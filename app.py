import streamlit as st
import plotly.io as pio

# Separadores Plotly no padrão brasileiro para todos os gráficos da sessão
for _tmpl in ["plotly", "plotly_white", "ggplot2", "seaborn", "simple_white"]:
    try:
        pio.templates[_tmpl].layout.separators = ",."
    except Exception:
        pass

# ── Configuração Global ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="TechVendas | BI",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS Global ─────────────────────────────────────────────────────────────────
st.markdown(
    """
  <style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;800&display=swap');

  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
    background-color: #007BFF;
  }
  [data-testid="stSidebar"] * { color: #FFFFFF !important; }
  [data-testid="stSidebar"] .stSelectbox > div > div,
  [data-testid="stSidebar"] .stMultiSelect > div > div {
    background-color: rgba(255,255,255,0.15) !important;
    border-color: rgba(255,255,255,0.3) !important;
    color: white !important;
  }
  [data-testid="stSidebarNav"] { display: none; }

  /* ── Fundo geral branco ── */
  .main { background-color: #FFFFFF; }
  .block-container {
    padding-top: 3rem !important;
    background-color: #FFFFFF;
  }

  /* ── KPI Cards — design limpo, fundo branco com borda esquerda ── */
  .kpi-card {
    background-color: #FFFFFF;
    border-left: 5px solid #007BFF;
    padding: 16px 20px;
    border-radius: 8px;
    text-align: left;
    box-shadow: 0 2px 10px rgba(0,123,255,0.10);
  }
  .kpi-title {
    font-size: 0.85rem;
    font-weight: 600;
    color: #777777;
    margin-bottom: 6px;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }
  .kpi-value {
    font-size: 1.7rem;
    font-weight: 800;
    color: #007BFF;
  }
  .kpi-green { border-left-color: #39B54A; }
  .kpi-green .kpi-value { color: #39B54A; }
  .kpi-alert { border-left-color: #E63946; }
  .kpi-alert .kpi-value { color: #E63946; }

  /* ── Navegação horizontal ── */
  [data-testid="stPageLink"] a {
    display: flex !important;
    justify-content: center !important;
    align-items: center !important;
    min-height: 42px;
    padding: 8px 12px !important;
    border-radius: 8px !important;
    border: 2px solid #D0E8FF !important;
    background-color: #F4F8FF !important;
    color: #007BFF !important;
    font-weight: 600 !important;
    font-size: 0.92rem !important;
    text-decoration: none !important;
    transition: all 0.2s ease !important;
    white-space: nowrap !important;
  }
  [data-testid="stPageLink"] a:hover {
    background-color: #D0E8FF !important;
    border-color: #007BFF !important;
    color: #007BFF !important;
  }
  [data-testid="stPageLink"] a[aria-current="page"] {
    background-color: #007BFF !important;
    color: #FFFFFF !important;
    border-color: #007BFF !important;
  }

  /* ── Títulos de seção ── */
  h2 { color: #007BFF !important; }
  </style>
""",
    unsafe_allow_html=True,
)

# ── Navegação ──────────────────────────────────────────────────────────────────
pages = [
    st.Page("pages/2_Vendas.py", title="Vendas"),
    st.Page("pages/3_Financeiro.py", title="Financeiro"),
    st.Page("pages/4_Produtos.py", title="Produtos"),
    st.Page("pages/5_CRM.py", title="CRM"),
    st.Page("pages/6_Analise_Profunda.py", title="Previsão IA"),
]

pg = st.navigation(pages, position="hidden")

# ── Logo na sidebar ────────────────────────────────────────────────────────────
st.sidebar.image("logo_projeto.png", use_container_width=True)
st.sidebar.markdown("---")

# ── Barra de navegação horizontal ─────────────────────────────────────────────
nav_items = [
    ("pages/2_Vendas.py", " Vendas"),
    ("pages/3_Financeiro.py", " Financeiro"),
    ("pages/4_Produtos.py", " Produtos"),
    ("pages/5_CRM.py", " CRM"),
    ("pages/6_Analise_Profunda.py", " Previsão IA"),
]

cols = st.columns(len(nav_items))
for col, (path, label) in zip(cols, nav_items):
    with col:
        st.page_link(path, label=label, use_container_width=True)

st.divider()

# ── Renderiza a página atual ───────────────────────────────────────────────────
pg.run()
