import streamlit as st
import plotly.express as px
import data_loader

# 1. Configuração da Página
st.set_page_config(page_title="Visão Geral | TechVendas", page_icon="🌐", layout="wide")

st.markdown("<h2 style='color: #00024D;'>Visão Executiva Consolidada</h2>", unsafe_allow_html=True)
st.markdown("Acompanhamento dos principais indicadores de saúde financeira e comercial da empresa.")
st.divider()

# 2. Carregamento dos Dados
with st.spinner("Carregando base de dados..."):
    df_vendas = data_loader.carregar_dados_vendas()
    df_financeiro = data_loader.carregar_dados_financeiro()

# 3. Cálculo dos KPIs Principais
receita_total = df_vendas['receita'].sum()
margem_total = df_vendas['margem_lucro'].sum()
ticket_medio = df_vendas['receita'].mean()

# KPIs Financeiros
df_atrasados = df_financeiro[df_financeiro['status_pagamento'] == 'ATRASADA']
total_inadimplente = df_atrasados['valor_devido'].sum()
total_esperado = df_financeiro['valor_devido'].sum()
taxa_inadimplencia = (total_inadimplente / total_esperado) * 100 if total_esperado > 0 else 0

# 4. Renderização dos "Cards" de KPI com a Identidade Visual Corporativa
st.markdown("""
    <style>
    .kpi-card {
        background-color: #74A9CF;
        padding: 20px;
        border-radius: 10px;
        color: #00024D;
        text-align: center;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .kpi-title { font-size: 1.1rem; font-weight: 600; margin-bottom: 5px; }
    .kpi-value { font-size: 1.8rem; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Receita Bruta</div><div class='kpi-value'>R$ {receita_total:,.2f}</div></div>", unsafe_allow_html=True)
with col2:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Margem de Lucro</div><div class='kpi-value'>R$ {margem_total:,.2f}</div></div>", unsafe_allow_html=True)
with col3:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Total em Atraso</div><div class='kpi-value'>R$ {total_inadimplente:,.2f}</div></div>", unsafe_allow_html=True)
with col4:
    st.markdown(f"<div class='kpi-card'><div class='kpi-title'>Taxa de Risco</div><div class='kpi-value'>{taxa_inadimplencia:.2f}%</div></div>", unsafe_allow_html=True)

st.write("") 
st.write("")

# 5. Gráficos de Visão Geral
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.markdown("#### Curva de Crescimento (Receita vs Margem)")
    # Agrupando por data_venda (ano_mes)
    evolucao_vendas = df_vendas.groupby('ano_mes')[['receita', 'margem_lucro']].sum().reset_index()
    
    fig_linha = px.line(
        evolucao_vendas, 
        x='ano_mes', 
        y=['receita', 'margem_lucro'],
        labels={'value': 'Valor (R$)', 'ano_mes': 'Mês/Ano', 'variable': 'Indicador'},
        color_discrete_sequence=['#00024D', '#74A9CF'],
        markers=True
    )

    newnames = {'receita': 'Receita Bruta', 'margem_lucro': 'Margem de Lucro'}
    fig_linha.for_each_trace(lambda t: t.update(name = newnames[t.name],
                                      legendgroup = newnames[t.name],
                                      hovertemplate = t.hovertemplate.replace(t.name, newnames[t.name])
                                     ))
    
    st.plotly_chart(fig_linha, width='stretch')

with col_graf2:
    st.markdown("#### Saúde da Carteira de Recebimentos")
    saude_fin = df_financeiro.groupby('status_pagamento')['valor_devido'].sum().reset_index()
    
    color_map = {'ATRASADA': '#E63946', 'LIQUIDADA': '#00024D', 'EM_ABERTO': '#74A9CF', 'CANCELADA': '#8D99AE'}
    
    fig_pizza = px.pie(
        saude_fin, 
        names='status_pagamento', 
        values='valor_devido',
        hole=0.4, 
        color='status_pagamento',
        color_discrete_map=color_map
    )
    
    st.plotly_chart(fig_pizza, width='stretch')