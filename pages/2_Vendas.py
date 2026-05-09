import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import data_loader
import utils as u

# ── Configuração ───────────────────────────────────────────────────────────────

st.markdown(
    "<h2 style='color: #007BFF; font-family: Inter, sans-serif;'>Análise Comercial e Performance</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "Sazonalidade, desempenho do time, mix de receita x margem e padrões de comportamento de vendas."
)
st.divider()

# ── Dados ──────────────────────────────────────────────────────────────────────
with st.spinner("Carregando base comercial..."):
    df_vendas = data_loader.carregar_dados_vendas()
    df_vendedores = data_loader.carregar_dados_vendedores()

# Feature engineering adicional para análise temporal
df_vendas["dia_semana"] = df_vendas["data_venda"].dt.day_name()
df_vendas["mes_num"] = df_vendas["data_venda"].dt.month
df_vendas["mes_nome"] = df_vendas["data_venda"].dt.strftime("%b")
df_vendas["trimestre"] = df_vendas["data_venda"].dt.quarter.map(
    {1: "Q1", 2: "Q2", 3: "Q3", 4: "Q4"}
)

# ── Filtros ────────────────────────────────────────────────────────────────────
st.sidebar.header("Filtros Comerciais (Específicos)")

tx_comissao = (
    st.sidebar.slider(
        "Taxa de Comissão (%)", min_value=1.0, max_value=10.0, value=2.5, step=0.5
    )
    / 100
)

ano_selecionado = st.session_state.get("global_ano", "Todos")
categoria_selecionada = st.session_state.get("global_categoria", "Todas")

df = df_vendas
if ano_selecionado != "Todos":
    df = df[df["ano"] == ano_selecionado]
if categoria_selecionada != "Todas":
    df = df[df["categoria"] == categoria_selecionada]

if df.empty:
    st.warning("Nenhum dado para os filtros selecionados.")
    st.stop()


# ── KPIs ───────────────────────────────────────────────────────────────────────
faturamento = df["receita"].sum()
margem_total = df["margem_lucro"].sum()
pct_margem = (margem_total / faturamento * 100) if faturamento > 0 else 0
qtd_notas = df["id_nota_fiscal"].nunique()
ticket_medio = faturamento / qtd_notas if qtd_notas > 0 else 0
qtd_itens = int(df["quantidade"].sum())


c1, c2, c3, c4, c5 = st.columns(5)
c1.markdown(
    f"<div class='kpi-card'><div class='kpi-title'>Faturamento</div><div class='kpi-value'>{u.brl(faturamento)}</div></div>",
    unsafe_allow_html=True,
)
c2.markdown(
    f"<div class='kpi-card kpi-green'><div class='kpi-title'>Lucro Bruto</div><div class='kpi-value'>{u.brl(margem_total)}</div></div>",
    unsafe_allow_html=True,
)
c3.markdown(
    f"<div class='kpi-card'><div class='kpi-title'>Margem Bruta</div><div class='kpi-value'>{u.pct(pct_margem)}</div></div>",
    unsafe_allow_html=True,
)
c4.markdown(
    f"<div class='kpi-card'><div class='kpi-title'>Ticket Médio (NF)</div><div class='kpi-value'>{u.brl(ticket_medio)}</div></div>",
    unsafe_allow_html=True,
)
c5.markdown(
    f"<div class='kpi-card'><div class='kpi-title'>Itens Vendidos</div><div class='kpi-value'>{u.num(qtd_itens)}</div></div>",
    unsafe_allow_html=True,
)

st.write("")
st.write("")

# ══════════════════════════════════════════════════════════════════════════════
# 1. RECEITA VS MARGEM — EVOLUÇÃO TEMPORAL COM ANOTAÇÕES
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("### Curva de Crescimento: Receita vs Margem Bruta")
st.caption(
    "Acompanha a evolução mensal de faturamento e lucratividade — afastamento entre as linhas indica aumento de custos."
)

evolucao = df.groupby("ano_mes")[["receita", "margem_lucro"]].sum().reset_index()

fig_ev = go.Figure()
fig_ev.add_trace(
    go.Scatter(
        x=evolucao["ano_mes"],
        y=evolucao["receita"],
        name="Receita Bruta",
        mode="lines+markers",
        line=dict(color="#007BFF", width=2.5),
        fill="tozeroy",
        fillcolor="rgba(0,2,77,0.07)",
    )
)
fig_ev.add_trace(
    go.Scatter(
        x=evolucao["ano_mes"],
        y=evolucao["margem_lucro"],
        name="Lucro Bruto",
        mode="lines+markers",
        line=dict(color="#39B54A", width=2.5),
        fill="tozeroy",
        fillcolor="rgba(116,169,207,0.15)",
    )
)
fig_ev.update_layout(
    yaxis_title="Valor (R$)",
    xaxis_title="Mês/Ano",
    legend=dict(orientation="h", y=-0.15),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=10, b=60),
)
st.plotly_chart(fig_ev, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# 2. SAZONALIDADE MENSAL + HEATMAP DIA DA SEMANA
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
col_saz, col_heat = st.columns(2)

with col_saz:
    st.markdown("#### Sazonalidade Mensal (Média Histórica)")
    st.caption(
        "Receita média por mês — identifica picos e vales recorrentes ao longo do ano."
    )

    ordem_meses = [
        "Jan",
        "Feb",
        "Mar",
        "Apr",
        "May",
        "Jun",
        "Jul",
        "Aug",
        "Sep",
        "Oct",
        "Nov",
        "Dec",
    ]
    sazon = df.groupby(["mes_num", "mes_nome"])["receita"].mean().reset_index()
    sazon = sazon.sort_values("mes_num")

    fig_saz = px.bar(
        sazon,
        x="mes_nome",
        y="receita",
        color="receita",
        color_continuous_scale=["#B3D9FF", "#007BFF"],
        labels={"mes_nome": "Mês", "receita": "Receita Média (R$)"},
        text=sazon["receita"].apply(lambda v: f"R$ {v:,.0f}"),
    )
    fig_saz.update_layout(
        coloraxis_showscale=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=10, b=10),
    )
    st.plotly_chart(fig_saz, width="stretch")

with col_heat:
    st.markdown("#### Heatmap: Dia da Semana × Trimestre")
    st.caption(
        "Intensidade de vendas por combinação de trimestre e dia — útil para planejamento tático."
    )

    ordem_dias = [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]
    nomes_dias = {
        "Monday": "Seg",
        "Tuesday": "Ter",
        "Wednesday": "Qua",
        "Thursday": "Qui",
        "Friday": "Sex",
        "Saturday": "Sáb",
        "Sunday": "Dom",
    }

    heat_df = df.groupby(["trimestre", "dia_semana"])["receita"].sum().reset_index()
    heat_pivot = heat_df.pivot(
        index="dia_semana", columns="trimestre", values="receita"
    ).fillna(0)
    # Reordenando os dias
    heat_pivot = heat_pivot.reindex([d for d in ordem_dias if d in heat_pivot.index])
    heat_pivot.index = [nomes_dias.get(d, d) for d in heat_pivot.index]

    fig_heat = px.imshow(
        heat_pivot,
        color_continuous_scale=["#F0FAF1", "#0056CC", "#007BFF"],
        labels=dict(x="Trimestre", y="Dia da Semana", color="Receita (R$)"),
        aspect="auto",
        text_auto=".2s",
    )
    fig_heat.update_layout(margin=dict(t=10, b=10))
    st.plotly_chart(fig_heat, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# 3. MIX DE CATEGORIAS — RECEITA E MARGEM POR TRIMESTRE
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown("### Mix de Receita por Categoria e Trimestre")
st.caption(
    "Composição trimestral do faturamento por categoria — identifica mudanças no mix ao longo do ano."
)

mix = df.groupby(["trimestre", "categoria"])["receita"].sum().reset_index()
fig_mix = px.bar(
    mix,
    x="trimestre",
    y="receita",
    color="categoria",
    barmode="stack",
    color_discrete_sequence=px.colors.qualitative.Set2,
    labels={
        "trimestre": "Trimestre",
        "receita": "Receita (R$)",
        "categoria": "Categoria",
    },
)
fig_mix.update_layout(
    legend=dict(orientation="h", y=-0.15),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=10, b=60),
)
st.plotly_chart(fig_mix, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# 4. PERFORMANCE DO TIME DE VENDAS
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown("### Performance do Time de Vendas")

vendedores = (
    df.groupby("id_vendedor")
    .agg(
        receita=("receita", "sum"),
        margem=("margem_lucro", "sum"),
        notas=("id_nota_fiscal", "nunique"),
        clientes=("id_cliente", "nunique"),
    )
    .reset_index()
)
vendedores["comissao"] = vendedores["receita"] * tx_comissao
vendedores["ticket_medio"] = vendedores["receita"] / vendedores["notas"]
vendedores["pct_margem"] = (vendedores["margem"] / vendedores["receita"] * 100).round(1)
# Substitui o ID pelo nome real do vendedor via join com RH
vendedores = pd.merge(vendedores, df_vendedores, on="id_vendedor", how="left")
vendedores["Vendedor"] = vendedores["nome_vendedor"].fillna(
    "Vendedor " + vendedores["id_vendedor"].astype(str)
)
vendedores = vendedores.sort_values("receita", ascending=False)

col_v1, col_v2 = st.columns(2)

with col_v1:
    st.markdown(f"#### Ranking por Faturamento (Comissão: {tx_comissao*100:.1f}%)")
    top10 = vendedores.head(10)
    fig_vend = go.Figure()
    fig_vend.add_trace(
        go.Bar(
            y=top10["Vendedor"],
            x=top10["receita"],
            name="Receita",
            orientation="h",
            marker_color="#007BFF",
            text=top10["receita"].apply(lambda v: f"R$ {v:,.0f}"),
            textposition="outside",
        )
    )
    fig_vend.add_trace(
        go.Bar(
            y=top10["Vendedor"],
            x=top10["comissao"],
            name=f"Comissão ({tx_comissao*100:.1f}%)",
            orientation="h",
            marker_color="#39B54A",
            text=top10["comissao"].apply(lambda v: f"R$ {v:,.0f}"),
            textposition="outside",
            xaxis="x2",
        )
    )
    fig_vend.update_layout(
        xaxis=dict(title="Receita (R$)", side="bottom"),
        xaxis2=dict(title="Comissão (R$)", overlaying="x", side="top", showgrid=False),
        yaxis=dict(categoryorder="total ascending"),
        legend=dict(orientation="h", y=-0.15),
        barmode="overlay",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=40, b=60, l=120),
    )
    fig_vend.update_traces(opacity=0.85)
    st.plotly_chart(fig_vend, width="stretch")



# ══════════════════════════════════════════════════════════════════════════════
# 5. ANÁLISE DE CRESCIMENTO MoM (MÊS A MÊS)
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown("### Análise de Crescimento MoM (Mês a Mês)")
st.caption(
    "Variação percentual da receita em relação ao mês anterior — identifica aceleração ou desaceleração de crescimento."
)

crescimento = df.groupby("ano_mes")["receita"].sum().reset_index()
crescimento["variacao_pct"] = crescimento["receita"].pct_change() * 100
crescimento = crescimento.dropna()

cores_mom = ["#E63946" if v < 0 else "#007BFF" for v in crescimento["variacao_pct"]]

fig_mom = go.Figure()
fig_mom.add_trace(
    go.Bar(
        x=crescimento["ano_mes"],
        y=crescimento["variacao_pct"],
        marker_color=cores_mom,
        text=crescimento["variacao_pct"].apply(lambda v: f"{v:+.1f}%"),
        textposition="outside",
    )
)
fig_mom.add_hline(y=0, line_color="grey", line_width=1)
fig_mom.update_layout(
    yaxis_title="Variação % vs Mês Anterior",
    xaxis_title="Mês/Ano",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=10, b=10),
)
st.plotly_chart(fig_mom, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# 6. TABELA DETALHADA DO RANKING DE VENDEDORES
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown("### Detalhamento — Performance Individual dos Vendedores")

tabela_vend = vendedores[
    [
        "Vendedor",
        "notas",
        "clientes",
        "receita",
        "margem",
        "pct_margem",
        "ticket_medio",
        "comissao",
    ]
].copy()
tabela_vend.columns = [
    "Vendedor",
    "Nº Vendas",
    "Clientes",
    "Receita Total",
    "Lucro Bruto",
    "Margem (%)",
    "Ticket Médio",
    "Comissão Devida",
]
tabela_vend = tabela_vend.reset_index(drop=True)
tabela_vend.index = tabela_vend.index + 1
tabela_vend.index.name = "Rank"

st.dataframe(
    tabela_vend.style.format(
        {
            "Nº Vendas": u.fmt_num,
            "Clientes": u.fmt_num,
            "Receita Total": u.fmt_brl2,
            "Lucro Bruto": u.fmt_brl2,
            "Margem (%)": u.fmt_pct,
            "Ticket Médio": u.fmt_brl2,
            "Comissão Devida": u.fmt_brl2,
        }
    ),
    width="stretch",
)
