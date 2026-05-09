import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import data_loader
import utils as u
from utils import C

# Produtos — Inteligência de Catálogo

st.markdown(
    "<h2 style='color: #007BFF; font-family: Inter, sans-serif;'>Inteligência de Catálogo e Rentabilidade</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "Análise estratégica por categoria: classificação ABC, matriz de rentabilidade, sazonalidade e contribuição para o resultado."
)
st.divider()

# 2. Carregamento dos Dados
with st.spinner("Carregando base de produtos..."):
    df_vendas = data_loader.carregar_dados_vendas()

# 3. Filtros Avançados
st.sidebar.header("Filtros de Catálogo (Específicos)")

ano_selecionado = st.session_state.get("global_ano", "Todos")
categoria_selecionada = st.session_state.get("global_categoria", "Todas")

df = df_vendas
if ano_selecionado != "Todos":
    df = df[df["ano"] == ano_selecionado]
if categoria_selecionada != "Todas":
    df = df[df["categoria"] == categoria_selecionada]

if df.empty:
    st.warning("Nenhum dado encontrado para os filtros selecionados.")
    st.stop()


# 4. KPIs de Rentabilidade
receita_total = df["receita"].sum()
custo_total = df["valor_custo"].sum()
margem_total = df["margem_lucro"].sum()
pct_margem = (margem_total / receita_total * 100) if receita_total > 0 else 0
total_itens = int(df["quantidade"].sum())
produtos_unicos = df["id_produto"].nunique()


c1, c2, c3, c4, c5 = st.columns(5)
c1.markdown(
    f"<div class='kpi-card'><div class='kpi-title'>Receita Bruta</div><div class='kpi-value'>{u.brl(receita_total)}</div></div>",
    unsafe_allow_html=True,
)
c2.markdown(
    f"<div class='kpi-card kpi-alert'><div class='kpi-title'>Custo (CPV)</div><div class='kpi-value'>{u.brl(custo_total)}</div></div>",
    unsafe_allow_html=True,
)
c3.markdown(
    f"<div class='kpi-card kpi-green'><div class='kpi-title'>Lucro Bruto</div><div class='kpi-value'>{u.brl(margem_total)}</div></div>",
    unsafe_allow_html=True,
)
c4.markdown(
    f"<div class='kpi-card'><div class='kpi-title'>Margem (%)</div><div class='kpi-value'>{u.pct(pct_margem)}</div></div>",
    unsafe_allow_html=True,
)
c5.markdown(
    f"<div class='kpi-card'><div class='kpi-title'>SKUs Ativos</div><div class='kpi-value'>{u.num(produtos_unicos)}</div></div>",
    unsafe_allow_html=True,
)

st.write("")
st.write("")

# ══════════════════════════════════════════════════════════════════════════════
# 5. ANÁLISE ABC — CURVA DE PARETO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("### Classificação ABC — Curva de Pareto por Categoria")
st.caption(
    "Identifica quais categorias concentram a maior parcela da receita (A ≤ 80%, B ≤ 95%, C = restante)."
)

df_abc = (
    df.groupby("categoria")["receita"]
    .sum()
    .reset_index()
    .sort_values("receita", ascending=False)
)
df_abc["pct"] = df_abc["receita"] / df_abc["receita"].sum() * 100
df_abc["pct_acum"] = df_abc["pct"].cumsum()
df_abc["classe"] = df_abc["pct_acum"].apply(
    lambda x: "A" if x <= 80 else ("B" if x <= 95 else "C")
)

color_map_abc = C.abc_map()

fig_abc = go.Figure()
for classe, cor in color_map_abc.items():
    mask = df_abc["classe"] == classe
    if mask.any():
        fig_abc.add_trace(
            go.Bar(
                x=df_abc.loc[mask, "categoria"],
                y=df_abc.loc[mask, "receita"],
                name=f"Classe {classe}",
                marker_color=cor,
                text=df_abc.loc[mask, "pct"].apply(lambda v: f"{v:.1f}%"),
                textposition="outside",
            )
        )

fig_abc.add_trace(
    go.Scatter(
        x=df_abc["categoria"],
        y=df_abc["pct_acum"],
        mode="lines+markers",
        name="% Acumulado",
        yaxis="y2",
        line=dict(color=C.CORAL, width=2.5),
        marker=dict(size=7),
    )
)
fig_abc.add_hline(
    y=80,
    line_dash="dash",
    line_color=C.CORAL,
    opacity=0.5,
    annotation_text="80%",
    annotation_position="top right",
    yref="y2",
)

fig_abc.update_layout(
    yaxis=dict(title="Receita (R$)"),
    yaxis2=dict(title="% Acumulado", overlaying="y", side="right", range=[0, 105]),
    legend=dict(orientation="h", y=-0.2),
    barmode="stack",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=30, b=80),
    height=450,
)
st.plotly_chart(fig_abc, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# 6. MATRIZ ESTRATÉGICA + TREEMAP
# ══════════════════════════════════════════════════════════════════════════════
col_left, col_right = st.columns(2)

# Dados base para ambos os gráficos
df_matriz = (
    df.groupby("categoria")
    .agg(
        volume=("quantidade", "sum"),
        receita_cat=("receita", "sum"),
        margem_cat=("margem_lucro", "sum"),
    )
    .reset_index()
)
df_matriz["margem_pct"] = (
    df_matriz["margem_cat"] / df_matriz["receita_cat"] * 100
).round(1)

with col_left:
    st.markdown("#### Matriz Estratégica: Volume × Margem")
    st.caption(
        "Quadrante superior-direito = categorias 'estrela' (alto volume + alta margem)."
    )

    fig_scatter = px.scatter(
        df_matriz,
        x="volume",
        y="margem_pct",
        size="receita_cat",
        color="categoria",
        text="categoria",
        labels={
            "volume": "Volume de Itens",
            "margem_pct": "Margem (%)",
            "receita_cat": "Receita",
        },
        size_max=50,
    )
    fig_scatter.update_traces(textposition="top center", textfont_size=9)
    fig_scatter.update_layout(
        showlegend=False, 
        margin=dict(t=20, b=10),
        height=400,
    )

    media_vol = df_matriz["volume"].mean()
    media_margem = df_matriz["margem_pct"].mean()
    fig_scatter.add_vline(x=media_vol, line_dash="dot", line_color="grey", opacity=0.5)
    fig_scatter.add_hline(
        y=media_margem, line_dash="dot", line_color="grey", opacity=0.5
    )

    st.plotly_chart(fig_scatter, width="stretch")

with col_right:
    st.markdown("#### Composição de Receita — Treemap")
    st.caption(
        "Tamanho = faturamento; cor = margem percentual (azul = alta, vermelho = baixa)."
    )

    fig_tree = px.treemap(
        df_matriz,
        path=["categoria"],
        values="receita_cat",
        color="margem_pct",
        color_continuous_scale=C.SCALE_DIVERG,
        labels={"receita_cat": "Receita", "margem_pct": "Margem (%)"},
    )
    fig_tree.update_layout(
        margin=dict(t=20, b=10, l=10, r=10),
        height=400,
    )
    st.plotly_chart(fig_tree, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# 7. EVOLUÇÃO TEMPORAL POR CATEGORIA
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown("### Tendência de Receita por Categoria ao Longo do Tempo")

df_tempo = df.groupby(["ano_mes", "categoria"])["receita"].sum().reset_index()

fig_tempo = px.area(
    df_tempo,
    x="ano_mes",
    y="receita",
    color="categoria",
    labels={"ano_mes": "Mês/Ano", "receita": "Receita (R$)", "categoria": "Categoria"},
    color_discrete_sequence=C.QUAL,
)
fig_tempo.update_layout(
    legend=dict(orientation="h", y=-0.2),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=20, b=80),
    height=450,
)
st.plotly_chart(fig_tempo, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# 9. TABELA DETALHADA COM RANKING E CLASSE ABC
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown("### Ranking de Performance por Categoria")

tabela = (
    df.groupby("categoria")
    .agg(
        Itens_Vendidos=("quantidade", "sum"),
        Produtos_Unicos=("id_produto", "nunique"),
        Transacoes=("id_nota_fiscal", "nunique"),
        Receita_Total=("receita", "sum"),
        Custo_Total=("valor_custo", "sum"),
        Lucro_Bruto=("margem_lucro", "sum"),
    )
    .reset_index()
)

tabela["Margem (%)"] = (tabela["Lucro_Bruto"] / tabela["Receita_Total"] * 100).round(1)
tabela["Ticket Médio"] = (tabela["Receita_Total"] / tabela["Transacoes"]).round(2)
tabela = tabela.sort_values("Receita_Total", ascending=False).reset_index(drop=True)
tabela.index = tabela.index + 1
tabela.index.name = "Rank"

# Merge com classe ABC
tabela = pd.merge(
    tabela,
    df_abc[["categoria", "classe"]].rename(columns={"classe": "ABC"}),
    on="categoria",
    how="left",
)

st.dataframe(
    tabela.style.format(
        {
            "Itens_Vendidos": u.fmt_num,
            "Produtos_Unicos": u.fmt_num,
            "Transacoes": u.fmt_num,
            "Receita_Total": u.fmt_brl2,
            "Custo_Total": u.fmt_brl2,
            "Lucro_Bruto": u.fmt_brl2,
            "Margem (%)": u.fmt_pct,
            "Ticket Médio": u.fmt_brl2,
        }
    ),
    width="stretch",
)

# ══════════════════════════════════════════════════════════════════════════════
# 10. ANÁLISE EM GRANULARIDADE DE PRODUTO (SKU)
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown("## Análise em Granularidade de Produto (SKU)")
st.caption(
    "Drill-down da categoria para o produto individual — identifique os itens que mais impactam o resultado."
)

# Filtro de categoria para o drill-down
cats_disponiveis = ["Todas"] + sorted(df["categoria"].dropna().unique().tolist())
cat_drill = st.selectbox(
    " Filtrar por Categoria (drill-down)", cats_disponiveis, key="cat_drill"
)

df_sku = df if cat_drill == "Todas" else df[df["categoria"] == cat_drill]

# Agregação por produto
produtos_agg = (
    df_sku.groupby(["id_produto", "produto", "categoria"])
    .agg(
        itens=("quantidade", "sum"),
        receita=("receita", "sum"),
        custo=("valor_custo", "sum"),
        lucro=("margem_lucro", "sum"),
        transacoes=("id_nota_fiscal", "nunique"),
        clientes=("id_cliente", "nunique"),
    )
    .reset_index()
)

produtos_agg["margem_pct"] = (
    produtos_agg["lucro"] / produtos_agg["receita"] * 100
).round(1)
produtos_agg["ticket_medio"] = (
    produtos_agg["receita"] / produtos_agg["transacoes"]
).round(2)

# ── ABC por Produto ────────────────────────────────────────────────────────────
st.markdown("### Análise ABC — Concentração de Receita por Produto")
st.caption("Produtos que sozinhos geram 80% da receita total do segmento selecionado.")

abc_prod = produtos_agg.sort_values("receita", ascending=False).reset_index(drop=True)
abc_prod["receita_acum"] = abc_prod["receita"].cumsum()
abc_prod["pct_acum"] = abc_prod["receita_acum"] / abc_prod["receita"].sum() * 100


def _classe_abc(pct):
    if pct <= 80:
        return "A"
    elif pct <= 95:
        return "B"
    else:
        return "C"


abc_prod["classe"] = abc_prod["pct_acum"].apply(_classe_abc)

# Exibe top 30 no gráfico para não sobrecarregar
top30 = abc_prod.head(30)
cor_abc = C.abc_map()

fig_abc_prod = go.Figure()
fig_abc_prod.add_trace(
    go.Bar(
        x=top30["produto"],
        y=top30["receita"],
        marker_color=[cor_abc[c] for c in top30["classe"]],
        name="Receita",
        customdata=list(zip(
            top30["receita"].apply(lambda v: f"R$ {v:,.0f}".replace(",", ".")),
            top30["classe"],
        )),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Receita: %{customdata[0]}<br>"
            "Classe ABC: %{customdata[1]}<extra></extra>"
        ),
        yaxis="y1",
    )
)
fig_abc_prod.add_trace(
    go.Scatter(
        x=top30["produto"],
        y=top30["pct_acum"],
        mode="lines+markers",
        name="% Acumulado",
        line=dict(color=C.CORAL, width=2),
        yaxis="y2",
    )
)
fig_abc_prod.add_hline(
    y=80,
    line_dash="dash",
    line_color=C.CORAL,
    opacity=0.6,
    annotation_text="80%",
    yref="y2",
)
fig_abc_prod.update_layout(
    yaxis=dict(title="Receita (R$)"),
    yaxis2=dict(
        title="% Acumulado",
        overlaying="y",
        side="right",
        range=[0, 105],
        ticksuffix="%",
    ),
    xaxis=dict(tickangle=-40),
    legend=dict(orientation="h", y=-0.25),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    margin=dict(t=20, b=100),
    height=550,
)
st.plotly_chart(fig_abc_prod, width="stretch")

# ── Top Produtos: Receita vs Margem ───────────────────────────────────────────
st.divider()
col_p1, col_p2 = st.columns(2)

with col_p1:
    st.markdown("#### Top 15 Produtos por Receita")
    top_rec = abc_prod.head(15)
    fig_tr = px.bar(
        top_rec,
        x="receita",
        y="produto",
        orientation="h",
        color="classe",
        color_discrete_map=cor_abc,
        text=top_rec["receita"].apply(lambda v: f"R$ {v:,.0f}"),
        labels={"classe": "Classe ABC", "receita": "Receita (R$)", "produto": ""},
    )
    fig_tr.update_layout(
        yaxis=dict(categoryorder="total ascending"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=10),
        height=600,
    )
    st.plotly_chart(fig_tr, width="stretch")

with col_p2:
    st.markdown("#### Top 15 Produtos por Lucro Bruto")
    top_luc = produtos_agg.nlargest(15, "lucro")
    fig_tl = px.bar(
        top_luc,
        x="lucro",
        y="produto",
        orientation="h",
        color="margem_pct",
        color_continuous_scale=C.SCALE_VIOLET,
        text=top_luc["lucro"].apply(lambda v: f"R$ {v:,.0f}"),
        labels={"lucro": "Lucro Bruto (R$)", "produto": "", "margem_pct": "Margem %"},
    )
    fig_tl.update_layout(
        yaxis=dict(categoryorder="total ascending"),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=10),
        height=600,
    )
    st.plotly_chart(fig_tl, width="stretch")

# ── Tabela Completa de SKUs ────────────────────────────────────────────────────
st.divider()
st.markdown("### Tabela Completa de Produtos")

tabela_sku = abc_prod[
    [
        "produto",
        "categoria",
        "classe",
        "itens",
        "transacoes",
        "clientes",
        "receita",
        "lucro",
        "margem_pct",
        "ticket_medio",
    ]
].copy()
tabela_sku.columns = [
    "Produto",
    "Categoria",
    "ABC",
    "Itens Vendidos",
    "Nº Transações",
    "Clientes",
    "Receita Total",
    "Lucro Bruto",
    "Margem (%)",
    "Ticket Médio",
]
tabela_sku = tabela_sku.reset_index(drop=True)
tabela_sku.index = tabela_sku.index + 1
tabela_sku.index.name = "Rank"

st.dataframe(
    tabela_sku.style.format(
        {
            "Itens Vendidos": u.fmt_num,
            "Nº Transações": u.fmt_num,
            "Clientes": u.fmt_num,
            "Receita Total": u.fmt_brl2,
            "Lucro Bruto": u.fmt_brl2,
            "Margem (%)": u.fmt_pct,
            "Ticket Médio": u.fmt_brl2,
        }
    ),
    width="stretch",
)
