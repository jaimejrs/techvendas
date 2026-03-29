import streamlit as st
import plotly.express as px
import data_loader

# 1. Configuração da Página
st.set_page_config(page_title="Vendas | TechVendas", page_icon="🛒", layout="wide")

st.markdown("<h2 style='color: #00024D;'>Análise Comercial e Performance</h2>", unsafe_allow_html=True)
st.markdown("Acompanhamento interativo de faturamento, sazonalidade e desempenho do time de vendas.")
st.divider()

# 2. Carregamento dos Dados
with st.spinner("Carregando base comercial..."):
    df_vendas = data_loader.carregar_dados_vendas()

# 3. Barra Lateral: Filtros Interativos
st.sidebar.header("Filtros Comerciais")

# Filtro de Ano
anos_disponiveis = ["Todos"] + sorted(df_vendas['ano'].dropna().unique().tolist(), reverse=True)
ano_selecionado = st.sidebar.selectbox("Selecione o Ano", anos_disponiveis)

# Filtro de Categoria
categorias_disponiveis = ["Todas"] + sorted(df_vendas['categoria'].dropna().unique().tolist())
categoria_selecionada = st.sidebar.selectbox("Selecione a Categoria", categorias_disponiveis)

# 4. Aplicando os Filtros no DataFrame
df_filtrado = df_vendas.copy()
if ano_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['ano'] == ano_selecionado]
if categoria_selecionada != "Todas":
    df_filtrado = df_filtrado[df_filtrado['categoria'] == categoria_selecionada]

# 5. Cálculo dos KPIs Dinâmicos 
faturamento = df_filtrado['receita'].sum()
qtd_itens = df_filtrado['quantidade'].sum()
ticket_medio = df_filtrado['receita'].mean() if not df_filtrado.empty else 0

# 6. Renderização dos Cards 
st.markdown("""
    <style>
    .kpi-card { background-color: #74A9CF; padding: 20px; border-radius: 10px; color: #00024D; text-align: center; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .kpi-title { font-size: 1.1rem; font-weight: 600; margin-bottom: 5px; }
    .kpi-value { font-size: 1.8rem; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
col1.markdown(f"<div class='kpi-card'><div class='kpi-title'>Faturamento Filtrado</div><div class='kpi-value'>R$ {faturamento:,.2f}</div></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='kpi-card'><div class='kpi-title'>Itens Vendidos</div><div class='kpi-value'>{qtd_itens:,.0f}</div></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='kpi-card'><div class='kpi-title'>Ticket Médio</div><div class='kpi-value'>R$ {ticket_medio:,.2f}</div></div>", unsafe_allow_html=True)

st.write("")
st.write("")

# 7. Gráficos de Vendas
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.markdown("#### Sazonalidade de Vendas")
    if not df_filtrado.empty:
        vendas_mes = df_filtrado.groupby('ano_mes')['receita'].sum().reset_index()
        fig_linha = px.line(
            vendas_mes, 
            x='ano_mes', 
            y='receita', 
            labels={'ano_mes': 'Mês/Ano', 'receita': 'Receita Bruta (R$)'}, 
            color_discrete_sequence=['#00024D'], 
            markers=True
        )
        st.plotly_chart(fig_linha, width='stretch')
    else:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")

with col_graf2:
    st.markdown("#### Top 5 Vendedores: Comissão Devida (2.5%)")
    if not df_filtrado.empty:
        top_vendedores = df_filtrado.groupby('id_vendedor')['receita'].sum().nlargest(5).reset_index()
        top_vendedores['comissao_devida'] = top_vendedores['receita'] * 0.025
        top_vendedores['id_vendedor'] = "Vendedor " + top_vendedores['id_vendedor'].astype(str) # Mascarando ID para ficar amigável
        
        fig_barras = px.bar(
            top_vendedores, 
            x='id_vendedor', 
            y='comissao_devida', 
            labels={'id_vendedor': 'Identificação', 'comissao_devida': 'Comissão (R$)'}, 
            text_auto='.2s', 
            color_discrete_sequence=['#74A9CF']
        )
        st.plotly_chart(fig_barras, width='stretch')
    else:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")