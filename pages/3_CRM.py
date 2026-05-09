import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import data_loader
import utils as u
from utils import C

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
st.sidebar.header("Filtros de Cliente (Específicos)")
tipo_selecionado = st.sidebar.selectbox(
    "Tipo de Cliente",
    ["Todos"] + sorted(df_crm["tipo_cliente"].dropna().unique().tolist()),
)

ano_selecionado = st.session_state.get("global_ano", "Todos")

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

df_clientes_unicos = df.drop_duplicates(subset=["id_cliente", "tipo_cliente"])
total_pf = df_clientes_unicos[df_clientes_unicos["tipo_cliente"].str.contains("Física", na=False)]["id_cliente"].count()
total_pj = df_clientes_unicos[df_clientes_unicos["tipo_cliente"].str.contains("Jurídica", na=False)]["id_cliente"].count()

total_compras = df["id_nota_fiscal"].nunique()
valor_total_compras = df["receita"].sum()

c1, c2, c3, c4, c5 = st.columns(5)
c1.markdown(
    f"<div class='kpi-card'><div class='kpi-title'>Total de Clientes</div><div class='kpi-value'>{u.num(total_clientes)}</div></div>",
    unsafe_allow_html=True,
)
c2.markdown(
    f"<div class='kpi-card'><div class='kpi-title'>Pessoas Físicas</div><div class='kpi-value'>{u.num(total_pf)}</div></div>",
    unsafe_allow_html=True,
)
c3.markdown(
    f"<div class='kpi-card'><div class='kpi-title'>Pessoas Jurídicas</div><div class='kpi-value'>{u.num(total_pj)}</div></div>",
    unsafe_allow_html=True,
)
c4.markdown(
    f"<div class='kpi-card'><div class='kpi-title'>Total de Compras</div><div class='kpi-value'>{u.num(total_compras)}</div></div>",
    unsafe_allow_html=True,
)
c5.markdown(
    f"<div class='kpi-card kpi-green'><div class='kpi-title'>Valor Total (R$)</div><div class='kpi-value'>{u.brl(valor_total_compras)}</div></div>",
    unsafe_allow_html=True,
)

st.write("")
st.write("")



# ══════════════════════════════════════════════════════════════════════════════
# 1. MAPA MICRO-GEOGRÁFICO: BAIRROS DE FORTALEZA
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown("### Densidade de Clientes em Fortaleza (Por Bairro)")
st.caption("Visão espacial da distribuição de faturamento e clientes dentro da capital.")

df_fortaleza = df[df["cidade"].str.upper() == "FORTALEZA"].dropna(subset=["bairro"]).copy()

if not df_fortaleza.empty:
    df_bairro = df_fortaleza.groupby("bairro").agg(
        clientes=("id_cliente", "nunique"),
        receita=("receita", "sum")
    ).reset_index()

    st.markdown("#### Top Bairros")
    top_bairros = df_bairro.sort_values("receita", ascending=False)
    st.dataframe(
        top_bairros.rename(columns={"bairro": "Bairro", "clientes": "Clientes", "receita": "Receita"}).style.format({"Receita": u.fmt_brl}),
        hide_index=True,
        width="stretch"
    )
else:
    st.info("Nenhum dado de bairro encontrado para a cidade de Fortaleza com os filtros atuais.")

# ══════════════════════════════════════════════════════════════════════════════
# 2. ANÁLISE B2B vs B2C (VALOR TOTAL E MIX DE PRODUTOS)
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
col_pizza, col_mix = st.columns(2)

with col_pizza:
    st.markdown("### Valor Total por Tipo de Pessoa")
    st.caption("Distribuição percentual da receita entre clientes B2B, B2C e não identificados.")
    
    df_pizza = df.groupby("tipo_cliente")["receita"].sum().reset_index()
    fig_pizza = px.pie(
        df_pizza,
        values="receita",
        names="tipo_cliente",
        color="tipo_cliente",
        color_discrete_sequence=C.QUAL,
        hole=0.4
    )
    fig_pizza.update_traces(
        textposition='inside', 
        textinfo='percent+label',
        hovertemplate="<b>%{label}</b><br>Receita: R$ %{value:,.2f}<extra></extra>".replace(",", "X").replace(".", ",").replace("X", ".")
    )
    fig_pizza.update_layout(
        margin=dict(t=20, b=20, l=20, r=20), 
        height=400,
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)"
    )
    st.plotly_chart(fig_pizza, width="stretch")

with col_mix:
    st.markdown("### Mix de Produtos Preferido")
    st.caption("Comparativo da representatividade das categorias de produto entre Pessoas Físicas e Jurídicas.")
    
    if "categoria" in df.columns:
        df_mix = df.groupby(["tipo_cliente", "categoria"])["receita"].sum().reset_index()
        df_mix["pct"] = df_mix.groupby("tipo_cliente")["receita"].transform(lambda x: x / x.sum() * 100)
        
        fig_mix = px.bar(
            df_mix,
            x="tipo_cliente",
            y="pct",
            color="categoria",
            text=df_mix["pct"].apply(lambda x: f"{x:.1f}%"),
            labels={"tipo_cliente": "Perfil", "pct": "Participação (%)", "categoria": "Categoria"},
            color_discrete_sequence=C.QUAL
        )
        fig_mix.update_traces(textposition="inside", textfont_size=12)
        fig_mix.update_layout(
            barmode="stack", 
            margin=dict(t=20, b=10),
            height=400,
        )
        st.plotly_chart(fig_mix, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# 3. FATURAMENTO POR CLIENTE
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown("### Faturamento por Cliente")
st.caption("Lista de faturamento dos clientes, considerando o vendedor responsável e a data da última compra.")

if "id_vendedor" in df.columns:
    df_vend = data_loader.carregar_dados_vendedores()

    # Agregar por cliente: última compra, receita total, e último vendedor
    faturamento = df.groupby("id_cliente").agg(
        ultima_data=("data_venda", "max"),
        receita_total=("receita", "sum"),
        id_vendedor=("id_vendedor", "last")
    ).reset_index()

    faturamento = pd.merge(faturamento, df_nomes, on="id_cliente")
    faturamento = pd.merge(faturamento, df_vend, on="id_vendedor", how="left")
    
    faturamento = faturamento.sort_values("receita_total", ascending=False)
    
    faturamento = faturamento[["nome_cliente", "nome_vendedor", "ultima_data", "receita_total"]]
    faturamento.columns = ["Cliente", "Vendedor", "Última Compra", "Faturamento Total"]
    faturamento["Última Compra"] = faturamento["Última Compra"].dt.strftime("%d/%m/%Y")
    
    st.dataframe(
        faturamento.style.format({"Faturamento Total": u.fmt_brl}),
        hide_index=True,
        width="stretch"
    )
else:
    st.info("Informações de vendedor não disponíveis nesta visão.")
