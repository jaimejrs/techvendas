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
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');

  /* Global typography */
  html, body, [class*="css"] {
      font-family: 'Outfit', 'Inter', sans-serif !important;
  }
  
  /* ── Sidebar ── */
  [data-testid="stSidebar"] {
      background: linear-gradient(180deg, #1E1B4B 0%, #4C3D9E 50%, #7C5CBF 100%) !important;
      box-shadow: 4px 0 20px rgba(0, 0, 0, 0.15);
      border-right: 1px solid rgba(255,255,255,0.1);
  }
  [data-testid="stSidebar"] * { 
      color: #FFFFFF !important; 
  }
  [data-testid="stSidebar"] hr {
      border-color: rgba(255,255,255,0.2) !important;
  }
  [data-testid="stSidebar"] .stSelectbox > div > div,
  [data-testid="stSidebar"] .stMultiSelect > div > div {
      background-color: rgba(255,255,255,0.1) !important;
      border: 1px solid rgba(255,255,255,0.2) !important;
      border-radius: 12px !important;
      color: white !important;
      backdrop-filter: blur(12px);
      transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
      box-shadow: inset 0 2px 4px rgba(255,255,255,0.05);
  }
  [data-testid="stSidebar"] .stSelectbox > div > div:hover,
  [data-testid="stSidebar"] .stMultiSelect > div > div:hover {
      background-color: rgba(255,255,255,0.2) !important;
      border-color: rgba(255,255,255,0.4) !important;
      transform: translateY(-1px);
      box-shadow: 0 4px 10px rgba(0,0,0,0.1);
  }
  [data-testid="stSidebarNav"] { display: none; }

  /* ── Main Container ── */
  .block-container {
      padding-top: 2rem !important;
      max-width: 1400px;
  }

  /* ── Premium KPI Cards (Hover Animations) ── */
  .kpi-card {
      background-color: var(--secondary-background-color);
      border-left: 6px solid #4facfe;
      padding: 24px;
      border-radius: 16px;
      text-align: left;
      box-shadow: 0 4px 15px rgba(0,0,0,0.05);
      transition: transform 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275), box-shadow 0.3s ease;
      position: relative;
      overflow: hidden;
  }
  .kpi-card::before {
      content: '';
      position: absolute;
      top: 0; left: -100%;
      width: 50%; height: 100%;
      background: linear-gradient(to right, rgba(255,255,255,0) 0%, rgba(255,255,255,0.3) 50%, rgba(255,255,255,0) 100%);
      transform: skewX(-25deg);
      transition: all 0.7s ease;
  }
  .kpi-card:hover {
      transform: translateY(-8px);
      box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
  }
  .kpi-card:hover::before {
      left: 200%;
  }

  .kpi-title {
      font-size: 0.95rem;
      font-weight: 600;
      color: var(--text-color);
      opacity: 0.8;
      margin-bottom: 8px;
      text-transform: uppercase;
      letter-spacing: 1.5px;
  }
  .kpi-value {
      font-size: 1.45rem;
      font-weight: 800;
      background: linear-gradient(45deg, #C4B5FD 0%, #7C5CBF 100%);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      display: inline-block;
  }
  .kpi-green .kpi-value { background: linear-gradient(45deg, #2DD4BF 0%, #34D399 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
  .kpi-alert .kpi-value { background: linear-gradient(45deg, #F26B6B 0%, #FCA5A5 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }

  /* ── Horizontal Navigation Buttons ── */
  [data-testid="stPageLink"] a {
      display: flex !important;
      justify-content: center !important;
      align-items: center !important;
      min-height: 50px;
      padding: 10px 15px !important;
      border-radius: 12px !important;
      border: 1px solid rgba(200,200,200,0.5) !important;
      background-color: var(--secondary-background-color) !important;
      color: var(--text-color) !important;
      font-weight: 600 !important;
      font-size: 1rem !important;
      text-decoration: none !important;
      box-shadow: 0 4px 10px rgba(0,0,0,0.05) !important;
      transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1) !important;
      position: relative;
      overflow: hidden;
  }
  [data-testid="stPageLink"] a:hover {
      background-color: #7C5CBF !important;
      color: #ffffff !important;
      border-color: #7C5CBF !important;
      box-shadow: 0 8px 20px rgba(0, 123, 255, 0.3) !important;
      transform: translateY(-3px) !important;
  }
  [data-testid="stPageLink"] a[aria-current="page"] {
      background-color: #7C5CBF !important;
      color: #ffffff !important;
      border: none !important;
      box-shadow: 0 8px 20px rgba(0, 123, 255, 0.4) !important;
  }

  /* ── Section Titles ── */
  h1, h2, h3 {
      font-weight: 700 !important;
      letter-spacing: -0.5px;
  }
  h2 {
      color: #7C5CBF !important;
  }
  
  /* ── Metric Cards Native Streamlit Adjustments ── */
  [data-testid="stMetricValue"] {
      font-family: 'Outfit', sans-serif !important;
      font-weight: 800 !important;
      font-size: 1.45rem !important;
  }
  
  /* ── Dataframes / Tables ── */
  [data-testid="stDataFrame"] {
      border-radius: 12px;
      overflow: hidden;
      box-shadow: 0 5px 15px rgba(0,0,0,0.05);
      border: 1px solid rgba(200,200,200,0.3);
  }

  /* Dark mode overrides if user system is dark */
  @media (prefers-color-scheme: dark) {
      .kpi-card {
          border-color: rgba(255, 255, 255, 0.1);
      }
      [data-testid="stPageLink"] a {
          border-color: rgba(255,255,255,0.1) !important;
      }
      [data-testid="stPageLink"] a:hover {
          background-color: #7C5CBF !important;
          color: #fff !important;
      }
  }
  </style>
""",
    unsafe_allow_html=True,
)

# ── Navegação ──────────────────────────────────────────────────────────────────
pages = [
    st.Page("pages/1_Vendas.py", title="Vendas"),
    st.Page("pages/2_Produtos.py", title="Produtos"),
    st.Page("pages/3_CRM.py", title="CRM"),
    st.Page("pages/4_Recursos_Humanos.py", title="RH"),
]

pg = st.navigation(pages, position="hidden")

# ── Logo na sidebar ────────────────────────────────────────────────────────────
st.sidebar.image("logo_projeto.png", use_container_width=True)
st.sidebar.markdown("---")

# ── Filtros Globais ────────────────────────────────────────────────────────────
import data_loader
import pandas as pd

df_vendas_global = data_loader.carregar_dados_vendas()
anos_globais = ["Todos"] + sorted(df_vendas_global["ano"].dropna().unique().tolist(), reverse=True)
categorias_globais = ["Todas"] + sorted(df_vendas_global["categoria"].dropna().unique().tolist())

st.sidebar.header("Filtros Globais")
ano_global = st.sidebar.selectbox("Ano", anos_globais, key="global_ano_widget")
cat_global = st.sidebar.selectbox("Categoria", categorias_globais, key="global_cat_widget")

st.session_state["global_ano"] = ano_global
st.session_state["global_categoria"] = cat_global
st.sidebar.markdown("---")

# ── Agente de IA na Sidebar ───────────────────────────────────────────────────
import ai_agent
ai_agent.render_sidebar_agent()


# ── Barra de navegação horizontal ─────────────────────────────────────────────
nav_items = [
    ("pages/1_Vendas.py", " Vendas"),
    ("pages/2_Produtos.py", " Produtos"),
    ("pages/3_CRM.py", " CRM"),
    ("pages/4_Recursos_Humanos.py", " RH"),
]

cols = st.columns(len(nav_items))
for col, (path, label) in zip(cols, nav_items):
    with col:
        st.page_link(path, label=label, use_container_width=True)

st.divider()

# ── Renderiza a página atual ───────────────────────────────────────────────────
pg.run()
