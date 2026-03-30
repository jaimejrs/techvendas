import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import data_loader
import utils as u

# ── Configuração ───────────────────────────────────────────────────────────────

st.markdown(
    "<h2 style='color: #007BFF; font-family: Inter, sans-serif;'>Customer Relationship Management (CRM)</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "Segmentação RFM, lifecycle de clientes, risco de churn e distribuição geográfica da carteira."
)
st.divider()

# ── Dados ──────────────────────────────────────────────────────────────────────
with st.spinner("Carregando base de clientes..."):
    df_crm = data_loader.carregar_dados_crm()
    df_fin = data_loader.carregar_dados_financeiro()

# Enriquecer CRM com UF via dados financeiros (sem alterar a query SQL)
uf_por_cliente = (
    df_fin[["id_cliente", "uf"]].dropna().drop_duplicates(subset="id_cliente")
)
df_crm = pd.merge(df_crm, uf_por_cliente, on="id_cliente", how="left")

df_nomes = df_crm[["id_cliente", "nome_cliente"]].drop_duplicates()

# ── Filtros ────────────────────────────────────────────────────────────────────
st.sidebar.header("Filtros de Cliente")
anos_disponiveis = ["Todos"] + sorted(
    df_crm["ano"].dropna().unique().tolist(), reverse=True
)
ano_selecionado = st.sidebar.selectbox("Filtrar por Ano", anos_disponiveis)
tipo_selecionado = st.sidebar.selectbox(
    "Tipo de Cliente",
    ["Todos"] + sorted(df_crm["tipo_cliente"].dropna().unique().tolist()),
)

df = df_crm
if ano_selecionado != "Todos":
    df = df[df["ano"] == ano_selecionado]
if tipo_selecionado != "Todos":
    df = df[df["tipo_cliente"] == tipo_selecionado]

clientes_filtrados = df["id_cliente"].unique()
df_fin_filt = df_fin[df_fin["id_cliente"].isin(clientes_filtrados)]
df_atrasados = df_fin_filt[df_fin_filt["status_pagamento"] == "ATRASADA"]

# ── KPIs ───────────────────────────────────────────────────────────────────────
total_clientes = df["id_cliente"].nunique()
receita_total = df["receita"].sum()
ticket_medio = receita_total / total_clientes if total_clientes > 0 else 0
clientes_inadimplentes = df_atrasados["id_cliente"].nunique()
taxa_risco = (
    (clientes_inadimplentes / total_clientes * 100) if total_clientes > 0 else 0
)


c1, c2, c3, c4, c5 = st.columns(5)
c1.markdown(
    f"<div class='kpi-card'><div class='kpi-title'>Clientes Ativos</div><div class='kpi-value'>{u.num(total_clientes)}</div></div>",
    unsafe_allow_html=True,
)
c2.markdown(
    f"<div class='kpi-card'><div class='kpi-title'>Receita Total</div><div class='kpi-value'>{u.brl(receita_total)}</div></div>",
    unsafe_allow_html=True,
)
c3.markdown(
    f"<div class='kpi-card'><div class='kpi-title'>Ticket Médio (LTV)</div><div class='kpi-value'>{u.brl(ticket_medio)}</div></div>",
    unsafe_allow_html=True,
)
c4.markdown(
    f"<div class='kpi-card kpi-alert'><div class='kpi-title'>Clientes Inadimplentes</div><div class='kpi-value'>{u.num(clientes_inadimplentes)}</div></div>",
    unsafe_allow_html=True,
)
c5.markdown(
    f"<div class='kpi-card kpi-alert'><div class='kpi-title'>Taxa de Risco</div><div class='kpi-value'>{u.pct(taxa_risco)}</div></div>",
    unsafe_allow_html=True,
)

st.write("")
st.write("")

# ══════════════════════════════════════════════════════════════════════════════
# 1. MAPA GEOGRÁFICO DE CLIENTES POR ESTADO
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("### Distribuição Geográfica de Clientes")
st.caption(
    "Quantidade de clientes únicos por estado — intensidade da cor representa concentração."
)


@st.cache_data(ttl=86400, show_spinner=False)
def _get_brazil_geojson():
    import requests

    url = "https://raw.githubusercontent.com/giuliano-macedo/geodata-br-states/main/geojson/br_states.json"
    try:
        resp = requests.get(url, timeout=10)
        return resp.json()
    except Exception:
        return None


geojson = _get_brazil_geojson()

clientes_por_uf = (
    df.dropna(subset=["uf"])
    .groupby("uf")["id_cliente"]
    .nunique()
    .reset_index()
    .rename(columns={"id_cliente": "clientes"})
)
receita_por_uf = (
    df.dropna(subset=["uf"])
    .groupby("uf")["receita"]
    .sum()
    .reset_index()
    .rename(columns={"receita": "receita_uf"})
)
mapa_df = pd.merge(clientes_por_uf, receita_por_uf, on="uf")

col_mapa, col_rank = st.columns([3, 1])

with col_mapa:
    if geojson:
        fig_mapa = px.choropleth(
            mapa_df,
            geojson=geojson,
            locations="uf",
            featureidkey="properties.sigla",
            color="clientes",
            color_continuous_scale=[
                "#F0FAF1",
                "#B3D9FF",
                "#66C177",
                "#0056CC",
                "#007BFF",
            ],
            labels={"clientes": "Clientes", "uf": "Estado"},
            hover_data={"uf": True, "clientes": True, "receita_uf": ":,.0f"},
        )
        fig_mapa.update_geos(
            fitbounds="locations", visible=False, bgcolor="rgba(0,0,0,0)"
        )
        fig_mapa.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            coloraxis_colorbar=dict(title="Clientes"),
            paper_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_mapa, width="stretch")
    else:
        st.warning("Não foi possível carregar o mapa. Exibindo ranking alternativo.")
        fig_alt = px.bar(
            mapa_df.sort_values("clientes", ascending=True),
            x="clientes",
            y="uf",
            orientation="h",
            color="clientes",
            color_continuous_scale=["#B3D9FF", "#007BFF"],
            labels={"clientes": "Clientes", "uf": ""},
        )
        st.plotly_chart(fig_alt, width="stretch")

with col_rank:
    st.markdown("#### Top Estados")
    st.dataframe(
        mapa_df.sort_values("clientes", ascending=False)
        .head(10)
        .rename(
            columns={"uf": "UF", "clientes": "Clientes", "receita_uf": "Receita (R$)"}
        )
        .style.format({"Receita (R$)": u.fmt_brl}),
        width="stretch",
        hide_index=True,
    )

# ══════════════════════════════════════════════════════════════════════════════
# 2. ANÁLISE RFM — SEGMENTAÇÃO DE CLIENTES
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown("### Segmentação RFM — Quem são seus melhores clientes?")
st.caption(
    "RFM = Recência (última compra) × Frequência (nº de compras) × Monetário (receita total). Calculado sobre toda a base histórica."
)

# Usa dados não filtrados para RFM ser comparável
df_rfm_base = df_crm.copy()
hoje_rfm = df_rfm_base["data_venda"].max()

rfm = (
    df_rfm_base.groupby("id_cliente")
    .agg(
        Recencia=("data_venda", lambda x: (hoje_rfm - x.max()).days),
        Frequencia=("id_nota_fiscal", "nunique"),
        Monetario=("receita", "sum"),
        nome_cliente=("nome_cliente", "first"),
        tipo_cliente=("tipo_cliente", "first"),
    )
    .reset_index()
)

# Scoring por quartis (1-4)
rfm["R_score"] = pd.qcut(
    rfm["Recencia"], 4, labels=[4, 3, 2, 1], duplicates="drop"
).astype(int)
rfm["F_score"] = pd.qcut(
    rfm["Frequencia"].rank(method="first"), 4, labels=[1, 2, 3, 4], duplicates="drop"
).astype(int)
rfm["M_score"] = pd.qcut(
    rfm["Monetario"].rank(method="first"), 4, labels=[1, 2, 3, 4], duplicates="drop"
).astype(int)
rfm["RFM_score"] = rfm["R_score"] + rfm["F_score"] + rfm["M_score"]


def segmentar(score):
    if score >= 10:
        return "Champions "
    elif score >= 8:
        return "Leais "
    elif score >= 6:
        return "Em Risco "
    elif score >= 4:
        return "Dormentes "
    else:
        return "Perdidos "


rfm["Segmento"] = rfm["RFM_score"].apply(segmentar)

col_rfm1, col_rfm2 = st.columns([2, 1])

with col_rfm1:
    color_seg = {
        "Champions ": "#39B54A",
        "Leais ": "#007BFF",
        "Em Risco ": "#F4A261",
        "Dormentes ": "#8D99AE",
        "Perdidos ": "#E63946",
    }
    fig_rfm = px.scatter(
        rfm,
        x="Frequencia",
        y="Monetario",
        size="Recencia",
        color="Segmento",
        color_discrete_map=color_seg,
        hover_data=["nome_cliente", "tipo_cliente", "RFM_score"],
        labels={"Frequencia": "Frequência (Nº Compras)", "Monetario": "Monetário (R$)"},
        size_max=30,
    )
    fig_rfm.update_layout(legend=dict(orientation="h", y=-0.2), margin=dict(t=10, b=60))
    st.plotly_chart(fig_rfm, width="stretch")

with col_rfm2:
    seg_count = rfm["Segmento"].value_counts().reset_index()
    seg_count.columns = ["Segmento", "Clientes"]
    fig_seg = px.pie(
        seg_count,
        names="Segmento",
        values="Clientes",
        hole=0.4,
        color="Segmento",
        color_discrete_map=color_seg,
    )
    fig_seg.update_traces(textposition="inside", textinfo="percent+label")
    fig_seg.update_layout(showlegend=False, margin=dict(t=10, b=10))
    st.plotly_chart(fig_seg, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# 3. LIFECYCLE — NOVOS vs RECORRENTES
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown("### Lifecycle: Clientes Novos vs Recorrentes por Mês")
st.caption(
    "'Novo' = primeira compra registrada. 'Recorrente' = já tinha comprado anteriormente."
)

primeira_compra = df_crm.groupby("id_cliente")["data_venda"].min().reset_index()
primeira_compra.columns = ["id_cliente", "primeira_compra"]
primeira_compra["mes_entrada"] = (
    primeira_compra["primeira_compra"].dt.to_period("M").astype(str)
)

df_life = pd.merge(df[["id_cliente", "data_venda"]], primeira_compra, on="id_cliente")
df_life["ano_mes"] = df_life["data_venda"].dt.to_period("M").astype(str)
df_life["tipo_compra"] = np.where(
    df_life["data_venda"].dt.to_period("M")
    == df_life["primeira_compra"].dt.to_period("M"),
    "Novo",
    "Recorrente",
)

lifecycle = (
    df_life.groupby(["ano_mes", "tipo_compra"])["id_cliente"].nunique().reset_index()
)
lifecycle.columns = ["Mês/Ano", "Tipo", "Clientes"]

fig_life = px.bar(
    lifecycle,
    x="Mês/Ano",
    y="Clientes",
    color="Tipo",
    barmode="stack",
    color_discrete_map={"Novo": "#39B54A", "Recorrente": "#007BFF"},
    labels={"Mês/Ano": "Mês/Ano", "Clientes": "Nº de Clientes"},
)
fig_life.update_layout(legend=dict(orientation="h", y=-0.15), margin=dict(t=10, b=60))
st.plotly_chart(fig_life, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# 4. CHURN RISK + B2B vs B2C
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
col_churn, col_tipo = st.columns(2)

with col_churn:
    st.markdown("#### Radar de Churn (Clientes em Silêncio)")
    st.caption("Clientes sem compra nos últimos 90, 180 e 360 dias.")

    data_ref = df_crm["data_venda"].max()
    ultima_compra = df_crm.groupby("id_cliente")["data_venda"].max().reset_index()
    ultima_compra["dias_sem_compra"] = (data_ref - ultima_compra["data_venda"]).dt.days
    ultima_compra = pd.merge(ultima_compra, df_nomes, on="id_cliente")

    churn_90 = (ultima_compra["dias_sem_compra"] > 90).sum()
    churn_180 = (ultima_compra["dias_sem_compra"] > 180).sum()
    churn_360 = (ultima_compra["dias_sem_compra"] > 360).sum()

    fig_churn = go.Figure(
        go.Bar(
            x=["> 90 dias", "> 180 dias", "> 360 dias"],
            y=[churn_90, churn_180, churn_360],
            marker_color=["#F4A261", "#E76F51", "#E63946"],
            text=[churn_90, churn_180, churn_360],
            textposition="outside",
        )
    )
    fig_churn.update_layout(
        yaxis_title="Clientes",
        xaxis_title="Período Sem Compra",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(t=20, b=20),
    )
    st.plotly_chart(fig_churn, width="stretch")

with col_tipo:
    st.markdown("#### Receita: B2B vs B2C por Período")
    st.caption("Evolução da participação de cada perfil no faturamento total.")

    df_bxb = df.groupby(["ano", "tipo_cliente"])["receita"].sum().reset_index()
    df_bxb["ano"] = df_bxb["ano"].astype(str)

    fig_bxb = px.bar(
        df_bxb,
        x="ano",
        y="receita",
        color="tipo_cliente",
        barmode="group",
        color_discrete_map={
            "Pessoa Física (B2C)": "#39B54A",
            "Pessoa Jurídica (B2B)": "#007BFF",
            "Não Identificado": "#8D99AE",
        },
        labels={"ano": "Ano", "receita": "Receita (R$)", "tipo_cliente": "Perfil"},
    )
    fig_bxb.update_layout(legend=dict(orientation="h", y=-0.2), margin=dict(t=10, b=60))
    st.plotly_chart(fig_bxb, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# 5. TOP CLIENTES — FATURAMENTO E DÍVIDA
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown("### Ranking de Clientes")
col_top1, col_top2 = st.columns(2)

with col_top1:
    st.markdown("##### Top 10 por Faturamento")
    top_fat = (
        df.groupby("id_cliente")["receita"]
        .sum()
        .reset_index()
        .pipe(lambda x: pd.merge(x, df_nomes, on="id_cliente"))
        .nlargest(10, "receita")
    )
    fig_top = px.bar(
        top_fat,
        x="receita",
        y="nome_cliente",
        orientation="h",
        text=top_fat["receita"].apply(lambda v: f"R$ {v:,.0f}"),
        color_discrete_sequence=["#007BFF"],
        labels={"nome_cliente": "", "receita": "Receita Total (R$)"},
    )
    fig_top.update_layout(
        yaxis={"categoryorder": "total ascending"}, margin=dict(t=10, b=10, l=0)
    )
    st.plotly_chart(fig_top, width="stretch")

with col_top2:
    st.markdown("##### Top 10 por Dívida em Aberto")
    if not df_atrasados.empty:
        top_divida = (
            df_atrasados.groupby("id_cliente")["valor_devido"]
            .sum()
            .reset_index()
            .pipe(lambda x: pd.merge(x, df_nomes, on="id_cliente"))
            .nlargest(10, "valor_devido")
        )
        top_divida["nome_cliente"] = top_divida["nome_cliente"].fillna("Sem Nome")
        fig_div = px.bar(
            top_divida,
            x="valor_devido",
            y="nome_cliente",
            orientation="h",
            text=top_divida["valor_devido"].apply(lambda v: f"R$ {v:,.0f}"),
            color_discrete_sequence=["#E63946"],
            labels={"nome_cliente": "", "valor_devido": "Dívida (R$)"},
        )
        fig_div.update_layout(
            yaxis={"categoryorder": "total ascending"}, margin=dict(t=10, b=10, l=0)
        )
        st.plotly_chart(fig_div, width="stretch")
    else:
        st.success(" Nenhum cliente inadimplente nos filtros selecionados!")

# ══════════════════════════════════════════════════════════════════════════════
# 6. TABELA RFM DETALHADA
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown("### Tabela de Segmentação RFM — Detalhamento")
st.caption(
    "Ordenada por score RFM decrescente. Champions são os clientes de maior valor estratégico."
)

rfm_tabela = rfm[
    [
        "nome_cliente",
        "tipo_cliente",
        "Recencia",
        "Frequencia",
        "Monetario",
        "RFM_score",
        "Segmento",
    ]
].copy()
rfm_tabela = rfm_tabela.sort_values("RFM_score", ascending=False)

st.dataframe(
    rfm_tabela.style.format(
        {
            "Recencia": u.fmt_dias,
            "Frequencia": "{:.0f} compras",
            "Monetario": u.fmt_brl2,
            "RFM_score": "{:.0f}",
        }
    ),
    width="stretch",
    hide_index=True,
)
