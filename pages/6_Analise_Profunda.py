import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from sklearn.linear_model import LinearRegression
import data_loader
import utils as u

st.markdown(
    "<h2 style='color: #007BFF; font-family: Inter, sans-serif;'>Previsão de Demanda (Séries Temporais)</h2>",
    unsafe_allow_html=True,
)
st.markdown(
    "Projeção volumétrica de vendas para os próximos 3 meses baseada em regressão linear e sazonalidade histórica."
)
st.divider()

# 2. Carregamento dos Dados
with st.spinner("Analisando série histórica de vendas..."):
    df_vendas = data_loader.carregar_dados_vendas()

# 3. Barra Lateral: Seleção de Categoria
st.sidebar.header("Parâmetros de Projeção (Específicos)")
cat_selecionada = st.session_state.get("global_categoria", "Todas")

# Se for "Todas", a série temporal pode ficar misturada, mas o usuário deve escolher uma categoria específica
if cat_selecionada == "Todas":
    st.warning("Selecione uma categoria específica no Filtro Global para fazer a previsão.")
    st.stop()


# 4. Preparação da Série Temporal
# Agrupando por mês para suavizar ruídos diários
df_vendas["mes_ano"] = df_vendas["data_venda"].dt.to_period("M")
serie_cat = (
    df_vendas[df_vendas["categoria"] == cat_selecionada]
    .groupby("mes_ano")["quantidade"]
    .sum()
    .reset_index()
)
serie_cat["mes_ano_str"] = serie_cat["mes_ano"].astype(str)
serie_cat["ordinal"] = np.arange(
    len(serie_cat)
)  # Transformando data em número para a regressão

# 5. Motor de Machine Learning: Regressão Linear para Tendência
X = serie_cat[["ordinal"]]
y = serie_cat["quantidade"]

modelo = LinearRegression()
modelo.fit(X, y)

# Projeção para os próximos 3 meses (90 dias)
ult_ordinal = serie_cat["ordinal"].max()
futuro_ordinal = np.array([ult_ordinal + 1, ult_ordinal + 2, ult_ordinal + 3]).reshape(
    -1, 1
)
previsoes_futuras = modelo.predict(futuro_ordinal)

# Criando DataFrame de Projeção
datas_futuras = [serie_cat["mes_ano"].max() + i for i in range(1, 4)]
df_projecao = pd.DataFrame(
    {
        "mes_ano_str": [str(d) for d in datas_futuras],
        "quantidade": previsoes_futuras,
        "Tipo": "Projeção (IA)",
    }
)

serie_cat["Tipo"] = "Histórico Real"
df_final = pd.concat([serie_cat[["mes_ano_str", "quantidade", "Tipo"]], df_projecao])

# 6. Visualização do Forecast
st.markdown(f"### Forecast de Vendas: {cat_selecionada}")
fig_forecast = px.line(
    df_final,
    x="mes_ano_str",
    y="quantidade",
    color="Tipo",
    color_discrete_map={"Histórico Real": "#007BFF", "Projeção (IA)": "#39B54A"},
    markers=True,
    line_dash="Tipo",
    labels={"mes_ano_str": "Mês/Ano", "quantidade": "Volume de Itens"},
)

st.plotly_chart(fig_forecast, width="stretch")

# 7. Tabela de Suporte à Decisão (Estoque)
st.divider()
col1, col2 = st.columns([1, 2])

with col1:
    st.markdown("#### Necessidade de Estoque")
    total_projetado = sum(previsoes_futuras)
    st.metric("Total Previsto (Próx. Trimestre)", f"{total_projetado:,.0f} unidades")
    st.write(
        f"Com base na tendência de {cat_selecionada}, o setor de compras deve garantir este volume mínimo para evitar ruptura."
    )

with col2:
    st.markdown("#### Detalhamento dos Meses Futuros")
    st.table(
        df_projecao.rename(
            columns={"mes_ano_str": "Mês Projetado", "quantidade": "Previsão de Saída"}
        )
    )
