import streamlit as st

# Configuração da Página 
st.set_page_config(
    page_title="TechVendas | Inteligência de Negócios",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Injeção de CSS para a Identidade Visual Padronizada
st.markdown("""
    <style>
    /* Customização da Barra Lateral */
    [data-testid="stSidebar"] {
        background-color: #00024D;
    }
    [data-testid="stSidebar"] * {
        color: white !important;
    }
    
    /* Customização dos Títulos Principais */
    .main-header {
        color: #00024D;
        font-weight: 800;
        font-size: 3rem;
        margin-bottom: 0px;
    }
    .sub-header {
        color: #74A9CF;
        font-weight: 600;
        margin-top: -10px;
        margin-bottom: 30px;
    }
    </style>
""", unsafe_allow_html=True)

# Layout da Home Page
st.markdown("<h1 class='main-header'>Portal Corporativo</h1>", unsafe_allow_html=True)
st.markdown("<h3 class='sub-header'>TechVendas Solutions - Business Intelligence</h3>", unsafe_allow_html=True)

st.divider()

col1, col2 = st.columns([2, 1])

with col1:
    st.write("""
    ### Bem-vindo ao hub central de dados da empresa.
    
    Este ambiente integra informações dos setores operacional, comercial, recursos humanos e contábil para fornecer uma visão analítica completa e preditiva do negócio.
    
    **Módulos disponíveis no menu de navegação:**
    * **1. Visão Geral:** KPIs executivos consolidados.
    * **2. Vendas:** Performance comercial, sazonalidade e comissionamento.
    * **3. Financeiro:** Fluxo de caixa e rastreamento de inadimplência.
    * **4. Produtos:** Rentabilidade e margem de catálogo.
    * **5. CRM:** Comportamento e qualificação da base de clientes.
    * **6. RH:** Estrutura organizacional e indicadores de pessoal.
    * **7. Machine Learning:** Motor inteligente para previsão de inadimplência.
    """)

with col2:
    st.info("👈 Selecione um módulo no menu lateral à esquerda para iniciar as análises do painel.")
    st.image("https://cdn-icons-png.flaticon.com/512/2602/2602310.png", width=150) # Ícone Exemplo que será alterado