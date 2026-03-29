import streamlit as st
import plotly.graph_objects as go
import data_loader

# 1. Configuração da Página
st.set_page_config(page_title="Produtos | TechVendas", page_icon="📦", layout="wide")

st.markdown("<h2 style='color: #00024D;'>Rentabilidade e Análise de Catálogo</h2>", unsafe_allow_html=True)
st.markdown("Avaliação de performance por categoria: Comparação entre Margem de lucro e Volume de Saída.")
st.divider()

# 2. Carregamento dos Dados
with st.spinner("Carregando base de produtos..."):
    df_vendas = data_loader.carregar_dados_vendas()

# 3. Barra Lateral: Filtros de Tempo
st.sidebar.header("Filtros de Catálogo")
anos_disponiveis = ["Todos"] + sorted(df_vendas['ano'].dropna().unique().tolist(), reverse=True)
ano_selecionado = st.sidebar.selectbox("Analisar Ano Específico", anos_disponiveis)

df_filtrado = df_vendas.copy()
if ano_selecionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado['ano'] == ano_selecionado]

# 4. Cálculo dos KPIs de Rentabilidade
receita_total = df_filtrado['receita'].sum()
custo_total = df_filtrado['valor_custo'].sum()
margem_total = df_filtrado['margem_lucro'].sum()
percentual_margem = (margem_total / receita_total) * 100 if receita_total > 0 else 0

# 5. Renderização dos Cards (Identidade Visual)
st.markdown("""
    <style>
    .kpi-card { background-color: #74A9CF; padding: 20px; border-radius: 10px; color: #00024D; text-align: center; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .kpi-title { font-size: 1.1rem; font-weight: 600; margin-bottom: 5px; }
    .kpi-value { font-size: 1.8rem; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
col1.markdown(f"<div class='kpi-card'><div class='kpi-title'>Receita Gerada</div><div class='kpi-value'>R$ {receita_total:,.2f}</div></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='kpi-card'><div class='kpi-title'>Custo de Produto (CPV)</div><div class='kpi-value'>R$ {custo_total:,.2f}</div></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='kpi-card'><div class='kpi-title'>Lucro Bruto</div><div class='kpi-value'>R$ {margem_total:,.2f}</div></div>", unsafe_allow_html=True)
col4.markdown(f"<div class='kpi-card'><div class='kpi-title'>Margem (%)</div><div class='kpi-value'>{percentual_margem:.1f}%</div></div>", unsafe_allow_html=True)

st.write("")
st.write("")

# 6. Gráfico de Análise Comparativa 
st.markdown("#### Matriz de Performance: Lucro Bruto vs Volume de Saída por Categoria")
if not df_filtrado.empty:

    df_analise = df_filtrado.groupby('categoria').agg(
        margem_lucro=('margem_lucro', 'sum'),
        quantidade=('quantidade', 'sum')
    ).reset_index().sort_values('margem_lucro', ascending=True)

    fig_duo = go.Figure()

    fig_duo.add_trace(go.Bar(
        y=df_analise['categoria'],
        x=df_analise['quantidade'],
        name='Volume de Saída (Itens)',
        orientation='h',
        marker=dict(color='#74A9CF')
    ))

    fig_duo.add_trace(go.Bar(
        y=df_analise['categoria'],
        x=df_analise['margem_lucro'],
        name='Lucro Bruto (R$)',
        orientation='h',
        marker=dict(color='#00024D'),
        xaxis='x2'
    ))
# Configurando os layouts e os dois eixos X
    fig_duo.update_layout(
        xaxis=dict(
            title=dict(text='Volume de Saída (Itens)', font=dict(color='#74A9CF')), 
            tickfont=dict(color='#74A9CF')
        ),
        
        xaxis2=dict(
            title=dict(text='Lucro Bruto (R$)', font=dict(color='#00024D')), 
            tickfont=dict(color='#00024D'), 
            overlaying='x', 
            side='top'
        ),
        
        legend=dict(x=1, y=0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=200) 
    )
    
    st.plotly_chart(fig_duo, width='stretch')

else:
    st.warning("Nenhum dado encontrado para o ano selecionado.")

st.divider()

# 7. Tabela de Detalhamento Analítico
st.markdown("### 📋 Detalhamento de Performance das Categorias")
if not df_filtrado.empty:
    tabela_categorias = df_filtrado.groupby('categoria').agg(
        Itens_Vendidos=('quantidade', 'sum'),
        Receita_Total=('receita', 'sum'),
        Custo_Total=('valor_custo', 'sum'),
        Lucro_Bruto=('margem_lucro', 'sum')
    ).reset_index()
    
    tabela_categorias['Margem (%)'] = (tabela_categorias['Lucro_Bruto'] / tabela_categorias['Receita_Total']) * 100
    
    st.dataframe(
        tabela_categorias.style.format({
            'Itens_Vendidos': '{:,.0f}',
            'Receita_Total': 'R$ {:,.2f}',
            'Custo_Total': 'R$ {:,.2f}',
            'Lucro_Bruto': 'R$ {:,.2f}',
            'Margem (%)': '{:.1f}%'
        }),
        use_container_width=True,
        hide_index=True
    )