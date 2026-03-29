import streamlit as st
import plotly.express as px
import data_loader

# 1. Configuração da Página
st.set_page_config(page_title="Financeiro | TechVendas", page_icon="💰", layout="wide")

st.markdown("<h2 style='color: #00024D;'>Controle Financeiro e Risco Regional</h2>", unsafe_allow_html=True)
st.markdown("Monitoramento de recebíveis, fluxo de caixa e mapeamento geográfico da inadimplência.")
st.divider()

# 2. Carregamento dos Dados
with st.spinner("Carregando base financeira..."):
    df_financeiro = data_loader.carregar_dados_financeiro()

# 3. Barra Lateral: Filtros Financeiros
st.sidebar.header("Filtros de Risco")

# Filtro de Estado (UF)
ufs_disponiveis = ["Todos"] + sorted(df_financeiro['uf'].unique().tolist())
uf_selecionada = st.sidebar.selectbox("Filtrar por Estado (UF)", ufs_disponiveis)

# Aplicação do Filtro
df_filtrado = df_financeiro.copy()
if uf_selecionada != "Todos":
    df_filtrado = df_filtrado[df_filtrado['uf'] == uf_selecionada]

# 4. Cálculo dos KPIs Financeiros
total_esperado = df_filtrado['valor_devido'].sum()
recebido = df_filtrado[df_filtrado['status_pagamento'] == 'LIQUIDADA']['valor_devido'].sum()
em_atraso = df_filtrado[df_filtrado['status_pagamento'] == 'ATRASADA']['valor_devido'].sum()
taxa_risco = (em_atraso / total_esperado) * 100 if total_esperado > 0 else 0

# 5. Renderização dos Cards 
st.markdown("""
    <style>
    .kpi-card { background-color: #74A9CF; padding: 20px; border-radius: 10px; color: #00024D; text-align: center; box-shadow: 2px 2px 5px rgba(0,0,0,0.1); }
    .kpi-title { font-size: 1.1rem; font-weight: 600; margin-bottom: 5px; }
    .kpi-value { font-size: 1.8rem; font-weight: 800; }
    </style>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
col1.markdown(f"<div class='kpi-card'><div class='kpi-title'>Total da Carteira</div><div class='kpi-value'>R$ {total_esperado:,.2f}</div></div>", unsafe_allow_html=True)
col2.markdown(f"<div class='kpi-card'><div class='kpi-title'>Valor Liquidado</div><div class='kpi-value'>R$ {recebido:,.2f}</div></div>", unsafe_allow_html=True)
col3.markdown(f"<div class='kpi-card'><div class='kpi-title'>Valor em Atraso</div><div class='kpi-value' style='color: #E63946;'>R$ {em_atraso:,.2f}</div></div>", unsafe_allow_html=True)
col4.markdown(f"<div class='kpi-card'><div class='kpi-title'>Taxa de Risco</div><div class='kpi-value'>{taxa_risco:.2f}%</div></div>", unsafe_allow_html=True)

st.write("")
st.write("")

# 6. Gráficos Financeiros
col_graf1, col_graf2 = st.columns(2)

with col_graf1:
    st.markdown("#### Status da Carteira de Recebíveis")
    if not df_filtrado.empty:
        status_carteira = df_filtrado.groupby('status_pagamento')['valor_devido'].sum().reset_index()
        color_map = {'ATRASADA': '#E63946', 'LIQUIDADA': '#00024D', 'EM_ABERTO': '#74A9CF', 'CANCELADA': '#8D99AE'}
        
        fig_status = px.bar(
            status_carteira, 
            x='status_pagamento', 
            y='valor_devido',
            labels={'status_pagamento': 'Status', 'valor_devido': 'Valor (R$)'},
            color='status_pagamento',
            color_discrete_map=color_map,
            text_auto='.2s'
        )

        fig_status.update_layout(showlegend=False)
        st.plotly_chart(fig_status, width='stretch')
    else:
        st.warning("Nenhum dado encontrado para os filtros selecionados.")

with col_graf2:
    st.markdown("#### Risco por Localidade (Top 10)")
    if not df_filtrado.empty:

        df_atraso_local = df_filtrado[df_filtrado['status_pagamento'] == 'ATRASADA']
        
        # Se filtramos por um UF específico, mostramos as Cidades. Se for "Todos", mostramos os UFs.
        if uf_selecionada == "Todos":
            risco_local = df_atraso_local.groupby('uf')['valor_devido'].sum().nlargest(10).reset_index()
            eixo_x = 'uf'
            label_x = 'Estado (UF)'
        else:
            risco_local = df_atraso_local.groupby('cidade')['valor_devido'].sum().nlargest(10).reset_index()
            eixo_x = 'cidade'
            label_x = f'Cidades em {uf_selecionada}'
            
        fig_local = px.bar(
            risco_local, 
            x=eixo_x, 
            y='valor_devido', 
            labels={eixo_x: label_x, 'valor_devido': 'Valor em Atraso (R$)'}, 
            color_discrete_sequence=['#74A9CF'],
            text_auto='.2s'
        )
        st.plotly_chart(fig_local, width='stretch')
    else:
        st.warning("Nenhum título em atraso encontrado para os filtros selecionados.")

st.divider()

# 7. Insight Estratégico 
st.markdown("### 💡 Insight de Governança Regional (Ofensores)")
if uf_selecionada in ["Todos", "CE"]:
    df_atraso_geral = df_financeiro[df_financeiro['status_pagamento'] == 'ATRASADA']
    atraso_ce = df_atraso_geral[df_atraso_geral['uf'] == 'CE']['valor_devido'].sum()
    atraso_fortaleza = df_atraso_geral[(df_atraso_geral['uf'] == 'CE') & (df_atraso_geral['cidade'] == 'FORTALEZA')]['valor_devido'].sum()
    
    perc_fortaleza = (atraso_fortaleza / atraso_ce) * 100 if atraso_ce > 0 else 0
    
    st.info(f"""
    **Concentração de Risco no Ceará:** Analisando a base completa, identificamos que dos **R$ {atraso_ce:,.2f}** inadimplentes no estado do Ceará, 
    **R$ {atraso_fortaleza:,.2f} ({perc_fortaleza:.2f}%)** concentram-se exclusivamente em clientes registrados em **Fortaleza**. 
    
    *Recomendação Operacional: Direcionar campanhas de renegociação específicas e auditoria de cadastros para a capital cearense.*
    """)
else:
    st.info("O insight estratégico focado no Ceará só é exibido quando a visão está em 'Todos' ou filtrada especificamente para 'CE'.")