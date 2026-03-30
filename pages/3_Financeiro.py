import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import data_loader
import utils as u
import pandas as pd

st.markdown(
    "<h2 style='color: #007BFF; font-family: Inter, sans-serif;'>Gestão de Recebíveis e Risco de Crédito</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "Análise avançada: ageing de carteira, concentração de risco e listagem crítica para cobrança."
)
st.divider()

# ── Carregamento ──────────────────────────────────────────────────────────────
with st.spinner("Processando dados financeiros..."):
    df_fin = data_loader.carregar_dados_financeiro()
    df_vendas = data_loader.carregar_dados_vendas()

# Cross-data: categoria por nota fiscal
cat_por_nota = df_vendas[["id_nota_fiscal", "categoria"]].drop_duplicates(
    subset=["id_nota_fiscal"]
)
df_fin = pd.merge(df_fin, cat_por_nota, on="id_nota_fiscal", how="left")
df_fin["categoria"] = df_fin["categoria"].fillna("Diversos")
df_fin["ano"] = pd.to_datetime(df_fin["data_venda"]).dt.year

# ── Filtros ───────────────────────────────────────────────────────────────────
st.sidebar.header("Filtros Financeiros")

anos_fin = ["Todos"] + sorted(df_fin["ano"].dropna().unique().tolist(), reverse=True)
ano_fin_selecionado = st.sidebar.selectbox("Ano", anos_fin)

ufs_disponiveis = ["Todas"] + sorted(df_fin["uf"].dropna().unique().tolist())
uf_selecionada = st.sidebar.selectbox("Filtrar por UF", ufs_disponiveis)

status_disponiveis = sorted(df_fin["status_pagamento"].dropna().unique().tolist())
status_selecionado = st.sidebar.selectbox(
    "Status do Título", ["Todos"] + status_disponiveis
)

categorias_fin = ["Todas"] + sorted(df_fin["categoria"].dropna().unique().tolist())
cat_selecionada = st.sidebar.selectbox("Filtrar por Categoria", categorias_fin)

df = df_fin
if ano_fin_selecionado != "Todos":
    df = df[df["ano"] == ano_fin_selecionado]
if uf_selecionada != "Todas":
    df = df[df["uf"] == uf_selecionada]
if status_selecionado != "Todos":
    df = df[df["status_pagamento"] == status_selecionado]
if cat_selecionada != "Todas":
    df = df[df["categoria"] == cat_selecionada]

if df.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────
total_carteira = df["valor_devido"].sum()
df_atrasados = df[df["status_pagamento"] == "ATRASADA"]
atraso_total = df_atrasados["valor_devido"].sum()
taxa_inadimplencia = (atraso_total / total_carteira * 100) if total_carteira > 0 else 0
ticket_medio_atraso = (
    df_atrasados["valor_devido"].mean() if not df_atrasados.empty else 0
)
qtd_titulos_atraso = len(df_atrasados)


c1, c2, c3, c4, c5 = st.columns(5)
c1.markdown(
    f"<div class='kpi-card'><div class='kpi-title'>Carteira Total</div><div class='kpi-value'>{u.brl(total_carteira)}</div></div>",
    unsafe_allow_html=True,
)
c2.markdown(
    f"<div class='kpi-card kpi-alert'><div class='kpi-title'>Inadimplência</div><div class='kpi-value'>{u.brl(atraso_total)}</div></div>",
    unsafe_allow_html=True,
)
c3.markdown(
    f"<div class='kpi-card'><div class='kpi-title'>Taxa de Risco</div><div class='kpi-value'>{u.pct(taxa_inadimplencia, 2)}</div></div>",
    unsafe_allow_html=True,
)
c4.markdown(
    f"<div class='kpi-card'><div class='kpi-title'>Títulos Atrasados</div><div class='kpi-value'>{u.num(qtd_titulos_atraso)}</div></div>",
    unsafe_allow_html=True,
)
c5.markdown(
    f"<div class='kpi-card kpi-alert'><div class='kpi-title'>Ticket Médio Atraso</div><div class='kpi-value'>{u.brl(ticket_medio_atraso)}</div></div>",
    unsafe_allow_html=True,
)

st.write("")
st.write("")

# ══════════════════════════════════════════════════════════════════════════════
# 1. AGEING — ENVELHECIMENTO DA CARTEIRA (DUAL AXIS)
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("### Ageing: Envelhecimento da Carteira em Atraso")
st.caption(
    "Distribuição dos títulos inadimplentes por faixa de atraso — valor acumulado e quantidade de títulos."
)

if not df_atrasados.empty:
    bins = [-1, 30, 60, 90, 180, 360, 9999]
    labels = [
        "0-30 dias",
        "31-60 dias",
        "61-90 dias",
        "91-180 dias",
        "181-360 dias",
        "+360 dias",
    ]
    df_age = df_atrasados.copy()
    df_age["faixa_atraso"] = pd.cut(df_age["dias_atraso"], bins=bins, labels=labels)

    ageing_sum = (
        df_age.groupby("faixa_atraso", observed=False)
        .agg(valor=("valor_devido", "sum"), qtd=("valor_devido", "count"))
        .reset_index()
    )

    # Gradiente de cores: quanto mais velho, mais vermelho
    colors_age = ["#C4D9E8", "#39B54A", "#3690C0", "#0570B0", "#034E7C", "#E63946"]

    fig_ageing = go.Figure()
    fig_ageing.add_trace(
        go.Bar(
            x=ageing_sum["faixa_atraso"],
            y=ageing_sum["valor"],
            marker_color=colors_age,
            name="Valor (R$)",
            text=ageing_sum["valor"].apply(lambda v: f"R$ {v:,.0f}"),
            textposition="outside",
        )
    )
    fig_ageing.add_trace(
        go.Scatter(
            x=ageing_sum["faixa_atraso"],
            y=ageing_sum["qtd"],
            mode="lines+markers+text",
            name="Qtd. Títulos",
            yaxis="y2",
            line=dict(color="#E63946", width=2.5),
            marker=dict(size=8),
            text=ageing_sum["qtd"],
            textposition="top center",
        )
    )
    fig_ageing.update_layout(
        yaxis=dict(title="Valor Acumulado (R$)"),
        yaxis2=dict(title="Qtd. Títulos", overlaying="y", side="right"),
        legend=dict(orientation="h", y=-0.15),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=60),
    )
    st.plotly_chart(fig_ageing, width="stretch")
else:
    st.success(" Nenhum título em atraso para os filtros selecionados!")

# ══════════════════════════════════════════════════════════════════════════════
# 2. EVOLUÇÃO TEMPORAL + DISTRIBUIÇÃO POR STATUS
# ══════════════════════════════════════════════════════════════════════════════
col_l, col_r = st.columns(2)

with col_l:
    st.markdown("#### Análise Vintage — Status por Mês de Originação")
    st.caption(
        "Para cada mês de venda, qual a proporção de títulos liquidados vs atrasados hoje."
    )
    df_temp = df.copy()
    df_temp["mes_ano"] = df_temp["data_venda"].dt.to_period("M").astype(str)
    evolucao = (
        df_temp.groupby(["mes_ano", "status_pagamento"])["valor_devido"]
        .sum()
        .reset_index()
    )

    color_map = {
        "ATRASADA": "#E63946",
        "LIQUIDADA": "#007BFF",
        "EM_ABERTO": "#39B54A",
        "CANCELADA": "#8D99AE",
    }
    fig_ev = px.bar(
        evolucao,
        x="mes_ano",
        y="valor_devido",
        color="status_pagamento",
        color_discrete_map=color_map,
        barmode="stack",
        labels={
            "mes_ano": "Mês/Ano de Venda",
            "valor_devido": "Valor (R$)",
            "status_pagamento": "Status",
        },
    )
    fig_ev.update_layout(legend=dict(orientation="h", y=-0.25), margin=dict(t=10, b=80))
    st.plotly_chart(fig_ev, width="stretch")

with col_r:
    st.markdown("#### Distribuição da Carteira por Status")
    status_sum = df.groupby("status_pagamento")["valor_devido"].sum().reset_index()
    color_map = {
        "ATRASADA": "#E63946",
        "LIQUIDADA": "#007BFF",
        "EM_ABERTO": "#39B54A",
        "CANCELADA": "#8D99AE",
    }

    fig_donut = px.pie(
        status_sum,
        names="status_pagamento",
        values="valor_devido",
        hole=0.45,
        color="status_pagamento",
        color_discrete_map=color_map,
    )
    fig_donut.update_traces(textposition="inside", textinfo="percent+label")
    fig_donut.update_layout(showlegend=False, margin=dict(t=10, b=10))
    st.plotly_chart(fig_donut, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# 3. RISCO GEOGRÁFICO + RISCO POR CATEGORIA
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
col_l2, col_r2 = st.columns(2)

with col_l2:
    st.markdown("#### Top 10 Estados — Exposição ao Risco")
    if not df_atrasados.empty:
        risco_uf = (
            df_atrasados.groupby("uf")
            .agg(valor_atraso=("valor_devido", "sum"), qtd=("valor_devido", "count"))
            .reset_index()
            .sort_values("valor_atraso", ascending=True)
            .tail(10)
        )

        fig_uf = px.bar(
            risco_uf,
            x="valor_atraso",
            y="uf",
            orientation="h",
            text=risco_uf["valor_atraso"].apply(lambda v: f"R$ {v:,.0f}"),
            color="valor_atraso",
            color_continuous_scale=["#39B54A", "#E63946"],
            labels={"valor_atraso": "Valor em Atraso (R$)", "uf": ""},
        )
        fig_uf.update_layout(
            showlegend=False, coloraxis_showscale=False, margin=dict(t=10, b=10)
        )
        st.plotly_chart(fig_uf, width="stretch")
    else:
        st.success("Sem inadimplência geográfica.")

with col_r2:
    st.markdown("#### Inadimplência por Categoria de Produto")
    if not df_atrasados.empty:
        df_atr_cat = df[df["status_pagamento"] == "ATRASADA"]
        risco_cat = (
            df_atr_cat.groupby("categoria")["valor_devido"]
            .sum()
            .reset_index()
            .sort_values("valor_devido", ascending=True)
        )

        fig_cat = px.bar(
            risco_cat,
            y="categoria",
            x="valor_devido",
            orientation="h",
            color_discrete_sequence=["#007BFF"],
            labels={"valor_devido": "Valor em Atraso (R$)", "categoria": ""},
            text=risco_cat["valor_devido"].apply(lambda v: f"R$ {v:,.0f}"),
        )
        fig_cat.update_layout(margin=dict(t=10, b=10))
        st.plotly_chart(fig_cat, width="stretch")
    else:
        st.success("Sem inadimplência por categoria.")


# ══════════════════════════════════════════════════════════════════════════════
# 5. TABELA DE AUDITORIA PARA COBRANÇA
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown("### Listagem Crítica para Cobrança")
st.write("Os 50 títulos com maior tempo de atraso que requerem ação imediata:")

if not df_atrasados.empty:
    df_critico = df_atrasados.sort_values("dias_atraso", ascending=False).head(50)
    st.dataframe(
        df_critico[
            [
                "id_nota_fiscal",
                "uf",
                "cidade",
                "categoria",
                "valor_devido",
                "dias_atraso",
            ]
        ].style.format({"valor_devido": u.fmt_brl2, "dias_atraso": u.fmt_dias}),
        width="stretch",
        hide_index=True,
    )
else:
    st.success("Nenhum título em atraso — parabéns!")
