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
    "<h2 style='color: #007BFF; font-family: Inter, sans-serif;'>Recursos Humanos (People Analytics)</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "Visão consolidada do quadro de colaboradores, salários, turnover e demografia da equipe."
)
st.divider()

# ── Dados ──────────────────────────────────────────────────────────────────────
with st.spinner("Carregando base de colaboradores..."):
    df_rh = data_loader.carregar_dados_rh()

# ── Filtros ────────────────────────────────────────────────────────────────────
st.sidebar.header("Filtros de RH")

status_selecionado = st.sidebar.selectbox(
    "Status do Colaborador",
    ["Ativo", "Desligado", "Todos"],
    index=0
)

depto_selecionado = st.sidebar.selectbox(
    "Departamento",
    ["Todos"] + sorted(df_rh["departamento"].dropna().unique().tolist())
)

df = df_rh.copy()
if status_selecionado != "Todos":
    df = df[df["status"] == status_selecionado]
if depto_selecionado != "Todos":
    df = df[df["departamento"] == depto_selecionado]

# Evita erros se não houver dados no filtro
if df.empty:
    st.warning("Nenhum colaborador encontrado com os filtros selecionados.")
    st.stop()

# ── KPIs ───────────────────────────────────────────────────────────────────────
# Calcula turnover sobre toda a base (independente do filtro de Ativo/Desligado)
total_geral = len(df_rh)
total_desligados = len(df_rh[df_rh["status"] == "Desligado"])
taxa_turnover = (total_desligados / total_geral) * 100 if total_geral > 0 else 0

headcount = len(df)
salario_medio = df["salario"].mean()
tempo_casa_medio = df["tempo_casa_anos"].mean()

c1, c2, c3, c4 = st.columns(4)
c1.markdown(
    f"<div class='kpi-card'><div class='kpi-title'>Colaboradores</div><div class='kpi-value'>{u.num(headcount)}</div></div>",
    unsafe_allow_html=True,
)
c2.markdown(
    f"<div class='kpi-card'><div class='kpi-title'>Salário Médio</div><div class='kpi-value'>{u.brl(salario_medio)}</div></div>",
    unsafe_allow_html=True,
)
c3.markdown(
    f"<div class='kpi-card'><div class='kpi-title'>Tempo de Casa (Anos)</div><div class='kpi-value'>{tempo_casa_medio:.1f}</div></div>",
    unsafe_allow_html=True,
)
c4.markdown(
    f"<div class='kpi-card kpi-orange'><div class='kpi-title'>Turnover Global</div><div class='kpi-value'>{taxa_turnover:.1f}%</div></div>",
    unsafe_allow_html=True,
)

st.write("")
st.write("")

# ══════════════════════════════════════════════════════════════════════════════
# 1. DISTRIBUIÇÃO POR DEPARTAMENTO
# ══════════════════════════════════════════════════════════════════════════════
st.divider()

st.markdown("### Headcount por Departamento")
st.caption("Distribuição do quadro de funcionários por área.")

df_dept = df.groupby("departamento")["id_funcionario"].count().reset_index().rename(columns={"id_funcionario": "qtd"})
df_dept = df_dept.sort_values("qtd", ascending=True)

fig_dept = go.Figure()
fig_dept.add_trace(
    go.Bar(
        y=df_dept["departamento"],
        x=df_dept["qtd"],
        orientation="h",
        marker_color=C.VIOLET,
        text=df_dept["qtd"],
        textposition="auto",
        textfont=dict(size=13),
    )
)
fig_dept.update_layout(
    xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
    yaxis=dict(title=""),
    margin=dict(t=20, b=20, l=10, r=20),
    height=400,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig_dept, width="stretch")


# ══════════════════════════════════════════════════════════════════════════════
# 2. FAIXA SALARIAL E CUSTO POR DEPARTAMENTO
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown("### Salário Médio e Custo Total por Cargo")
st.caption("Mapeamento das remunerações da empresa.")

df_cargo = df.groupby("cargo").agg(
    salario_medio=("salario", "mean"),
    custo_total=("salario", "sum"),
    headcount=("id_funcionario", "count")
).reset_index().sort_values("salario_medio", ascending=True)

fig_salario = go.Figure()
fig_salario.add_trace(
    go.Bar(
        y=df_cargo["cargo"],
        x=df_cargo["salario_medio"],
        name="Salário Médio",
        orientation="h",
        marker=dict(
            color=df_cargo["salario_medio"],
            colorscale=C.SCALE_VIOLET,
            showscale=False,
        ),
        text=df_cargo["salario_medio"].apply(lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")),
        textposition="outside",
        cliponaxis=False,
        textfont=dict(size=12, color=C.VIOLET),
        customdata=np.stack((df_cargo["headcount"], df_cargo["custo_total"].apply(lambda v: f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))), axis=-1),
        hovertemplate=(
            "<b>%{y}</b><br>"
            "Salário Médio: %{text}<br>"
            "Colaboradores: %{customdata[0]}<br>"
            "Custo Total da Folha: %{customdata[1]}<extra></extra>"
        ),
    )
)
fig_salario.update_layout(
    xaxis=dict(showticklabels=False, showgrid=False, zeroline=False),
    yaxis=dict(title=""),
    margin=dict(t=20, b=20, l=10, r=100),
    height=450,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig_salario, width="stretch")

# ══════════════════════════════════════════════════════════════════════════════
# 3. TABELA DETALHADA
# ══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown("### Detalhamento da Equipe")

df_tabela = df[["nome", "departamento", "cargo", "salario", "tempo_casa_anos", "status"]].copy()
df_tabela.columns = ["Nome", "Departamento", "Cargo", "Salário (R$)", "Tempo de Casa (Anos)", "Status"]

# Formatações Visuais
st.dataframe(
    df_tabela.style.format({
        "Salário (R$)": u.fmt_brl,
        "Tempo de Casa (Anos)": "{:.1f}"
    }),
    hide_index=True,
    width="stretch"
)
