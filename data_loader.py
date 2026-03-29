import pandas as pd
import psycopg2
import streamlit as st

try:
    HOST = st.secrets["postgres"]["host"]
    DATABASE = st.secrets["postgres"]["database"]
    USER = st.secrets["postgres"]["user"]
    PASSWORD = st.secrets["postgres"]["password"]
except KeyError:
    st.error("Erro: Credenciais de banco de dados não encontradas no arquivo secrets.toml")
    st.stop()

def obter_conexao():
    """Cria e retorna a conexão com o banco de dados."""
    return psycopg2.connect(host=HOST, database=DATABASE, user=USER, password=PASSWORD)

@st.cache_data(ttl=3600) # Cache de 1 hora
def carregar_dados_vendas():
    """Extrai e trata a base analítica de Vendas e Produtos."""
    conn = obter_conexao()
    query = """
    SELECT 
        nf.id AS id_nota_fiscal, nf.data_venda, nf.id_vendedor, nf.id_cliente,
        inf.quantidade, inf.valor_venda_real AS receita, p.valor_custo, cat.descricao AS categoria
    FROM vendas.nota_fiscal nf
    INNER JOIN vendas.item_nota_fiscal inf ON nf.id = inf.id_nota_fiscal
    INNER JOIN vendas.produto p ON inf.id_produto = p.id
    INNER JOIN vendas.categoria cat ON p.id_categoria = cat.id;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Tratamento e Feature Engineering
    df.dropna(subset=['receita', 'valor_custo', 'categoria'], inplace=True)
    df['data_venda'] = pd.to_datetime(df['data_venda'])
    df['ano_mes'] = df['data_venda'].dt.to_period('M').astype(str)
    df['ano'] = df['data_venda'].dt.year
    df['margem_lucro'] = df['receita'] - df['valor_custo']
    
    return df

@st.cache_data(ttl=3600)
def carregar_dados_financeiro():
    """Extrai e trata a base analítica Financeira e Regional."""
    conn = obter_conexao()
    query = """
    SELECT 
        nf.id AS id_nota_fiscal, nf.id_cliente, cr.valor_atual AS valor_devido, 
        st.descricao AS status_pagamento, est.sigla AS uf, c.descricao AS cidade
    FROM vendas.nota_fiscal nf
    INNER JOIN vendas.parcela parc ON nf.id = parc.id_nota_fiscal
    INNER JOIN financeiro.conta_receber cr ON parc.id = cr.id_parcela
    INNER JOIN financeiro.situacao_titulo st ON cr.id_situacao = st.id
    LEFT JOIN geral.endereco ender ON nf.id_cliente = ender.id_pessoa
    LEFT JOIN geral.bairro b ON ender.id_bairro = b.id
    LEFT JOIN geral.cidade c ON b.id_cidade = c.id
    LEFT JOIN geral.estado est ON c.id_estado = est.id;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Tratamento
    df['uf'] = df['uf'].fillna('N/I')
    df['cidade'] = df['cidade'].fillna('N/I')
    
    return df
