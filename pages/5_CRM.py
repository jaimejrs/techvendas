import streamlit as st
import plotly.express as px
import data_loader

# 1. Configuração da Página
st.set_page_config(page_title="CRM | TechVendas", page_icon="🤝", layout="wide")

st.markdown("<h2 style='color: #00024D;'>Customer Relationship Management (CRM)</h2>", unsafe_allow_html=True)
st.markdown("Análise do perfil da carteira de clientes, ticket médio por segmento e concentração de receita.")
st.divider()

# 2. Carregamento dos Dados
with st.spinner("Carregando base de clientes..."):
    df_crm = data_loader.carregar_dados_crm()

# 3. Barra Lateral: Filtros
st.sidebar.header("Filtros de Cliente")
anos_disponiveis = ["Todos"] + sorted(df_crm['ano'].dropna().unique().tolist(), reverse=True)
ano_selecionado = st.sidebar.selectbox("Filtrar por Ano da Compra", anos_disponiveis)

df_filtrado = df_crm.copy()
if ano_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['ano'] == ano_selecionado]

# 4. Cálculo dos KPIs de CRM
total_clientes_ativos = df_filtrado['id_cliente'].nunique()
receita_total = df_filtrado['receita'].sum()
ticket_medio_geral = receita_total / total_clientes_ativos if total_clientes_ativos > 0 else 0

# 5. Renderização dos Cards (Identidade Visual)
st.markdown("""
    <style>
    .kpi-card { background-color: #74A9CF; padding: 20px; border-radius: 10px; color: #00024D; text-align: center; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .kpi-title { font-size: 1.1rem; font-weight: 600; margin-bottom: 5px; }
    .kpi-value { font-size: 1.8rem; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
col1.markdown(f"<div class='kpi-card'><div class='kpi-title'>Clientes Ativos (Compradores)</div><div class='kpi-value'>{total_clientes_ativos:,.0f}</div></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='kpi-card'><div class='kpi-title'>Receita Total da Carteira</div><div class='kpi-value'>R$ {receita_total:,.2f}</div></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='kpi-card'><div class='kpi-title'>Valor Vitalício Médio (LTV)</div><div class='kpi-value'>R$ {ticket_medio_geral:,.2f}</div></div>", unsafe_allow_html=True)

st.write("")
st.write("")

# 6. Gráficos de CRM
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.markdown("#### Receita por Perfil de Cliente (B2B vs B2C)")
    if not df_filtrado.empty:
        receita_perfil = df_filtrado.groupby('tipo_cliente')['receita'].sum().reset_index()
        
        fig_perfil = px.pie(
            receita_perfil, 
            names='tipo_cliente', 
            values='receita',
            hole=0.4,
            color='tipo_cliente',
            color_discrete_map={'Pessoa Física (B2C)': '#74A9CF', 'Pessoa Jurídica (B2B)': '#00024D', 'Não Identificado': '#8D99AE'}
        )
        st.plotly_chart(fig_perfil, width='stretch')
    else:
        st.warning("Nenhum dado encontrado.")

with col_graf2:
    st.markdown("#### Top 10 Clientes por Faturamento (Curva ABC)")
    if not df_filtrado.empty:
        top_clientes = df_filtrado.groupby('id_cliente')['receita'].sum().nlargest(10).reset_index()
        top_clientes['id_cliente'] = "Cliente " + top_clientes['id_cliente'].astype(str)
        
        fig_top = px.bar(
            top_clientes, 
            x='id_cliente', 
            y='receita', 
            labels={'id_cliente': 'Identificação do Cliente', 'receita': 'Faturamento (R$)'},
            color_discrete_sequence=['#00024D'],
            text_auto='.2s'
        )
        st.plotly_chart(fig_top, width='stretch')
    else:
        st.warning("Nenhum dado encontrado.")

st.divider()

# 7. Insight de Segmentação
st.markdown("### Estratégia de Segmentação")
if not df_filtrado.empty:
    b2b = df_filtrado[df_filtrado['tipo_cliente'] == 'Pessoa Jurídica (B2B)']['receita'].sum()
    b2c = df_filtrado[df_filtrado['tipo_cliente'] == 'Pessoa Física (B2C)']['receita'].sum()
    
    if b2b > b2c:
        st.success(f"**Vocação Corporativa (B2B):** A maior parcela da receita (R$ {b2b:,.2f}) provém de Pessoas Jurídicas. O time de vendas deve focar em contratos de longo prazo, vendas em lote e réguas de relacionamento para contas corporativas (Key Accounts).")
    elif b2c > b2b:
        st.info(f"**Vocação Varejo (B2C):** A maior parcela da receita (R$ {b2c:,.2f}) provém de Pessoas Físicas. A estratégia deve focar em campanhas de marketing de massa, remarketing e aumento do volume de transações.")