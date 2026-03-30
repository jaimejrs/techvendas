import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import streamlit as st

# Recuperando as credenciais via Streamlit Secrets
try:
    HOST = st.secrets["postgres"]["host"]
    DATABASE = st.secrets["postgres"]["database"]
    USER = st.secrets["postgres"]["user"]
    PASSWORD = st.secrets["postgres"]["password"]
except KeyError:
    st.error("Erro: Credenciais de banco de dados não encontradas.")
    st.stop()

DATABASE_URL = f"postgresql://{USER}:{PASSWORD}@{HOST}/{DATABASE}"


# ── Engine Singleton ──────────────────────────────────────────────────────────
# Criada uma única vez e reutilizada por todas as funções/abas.
# @st.cache_resource garante que o pool de conexões é compartilhado,
# eliminando o overhead de create_engine() a cada chamada.
@st.cache_resource
def _get_engine():
    return create_engine(DATABASE_URL)


# ── Dados de Vendas ───────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def carregar_dados_vendas():
    engine = _get_engine()
    query = """
  SELECT 
    nf.id AS id_nota_fiscal, nf.data_venda, nf.id_vendedor, nf.id_cliente,
    inf.quantidade, inf.valor_venda_real AS receita,
    p.id AS id_produto, p.nome AS produto, p.valor_custo,
    cat.descricao AS categoria
  FROM vendas.nota_fiscal nf
  INNER JOIN vendas.item_nota_fiscal inf ON nf.id = inf.id_nota_fiscal
  INNER JOIN vendas.produto p ON inf.id_produto = p.id
  INNER JOIN vendas.categoria cat ON p.id_categoria = cat.id;
  """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    # Tratamento e Feature Engineering
    df.dropna(subset=["receita", "valor_custo", "categoria"], inplace=True)
    df["data_venda"] = pd.to_datetime(df["data_venda"]).dt.tz_localize(None)
    df["ano_mes"] = df["data_venda"].dt.to_period("M").astype(str)
    df["ano"] = df["data_venda"].dt.year
    df["margem_lucro"] = df["receita"] - df["valor_custo"]

    return df


# ── Dados Financeiros ─────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def carregar_dados_financeiro():
    engine = _get_engine()
    # Query limpa e performática (Sem o Produto Cartesiano)
    query = """
  SELECT 
    nf.id AS id_nota_fiscal, 
    nf.id_cliente,
    nf.data_venda,
    cr.valor_atual AS valor_devido, 
    st.descricao AS status_pagamento, 
    est.sigla AS uf, 
    c.descricao AS cidade
  FROM vendas.nota_fiscal nf
  INNER JOIN vendas.parcela parc ON nf.id = parc.id_nota_fiscal
  INNER JOIN financeiro.conta_receber cr ON parc.id = cr.id_parcela
  INNER JOIN financeiro.situacao_titulo st ON cr.id_situacao = st.id
  LEFT JOIN geral.endereco ender ON nf.id_cliente = ender.id_pessoa
  LEFT JOIN geral.bairro b ON ender.id_bairro = b.id
  LEFT JOIN geral.cidade c ON b.id_cidade = c.id
  LEFT JOIN geral.estado est ON c.id_estado = est.id;
  """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    # Tratamentos de Data e Ageing
    df["data_venda"] = pd.to_datetime(df["data_venda"]).dt.tz_localize(None)
    data_hoje = df["data_venda"].max()

    # ── Cálculo vetorizado de dias de atraso ──────────────────────────────────
    # Substituímos o df.apply(lambda, axis=1) — que itera linha-a-linha em
    # Python puro — por operações vetorizadas do NumPy/Pandas (C nativo).
    # Speedup médio: 10-100x dependendo do volume de registros.
    df["dias_atraso"] = np.where(
        df["status_pagamento"] == "ATRASADA", (data_hoje - df["data_venda"]).dt.days, 0
    )

    return df


# ── Dados de CRM ──────────────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def carregar_dados_crm():
    engine = _get_engine()
    query = """
  SELECT 
    nf.id AS id_nota_fiscal,
    nf.id_cliente,
    COALESCE(pf.nome, pj.razao_social, 'Nome Não Identificado') AS nome_cliente,
    nf.data_venda,
    inf.valor_venda_real AS receita,
    CASE 
      WHEN pf.id IS NOT NULL THEN 'Pessoa Física (B2C)'
      WHEN pj.id IS NOT NULL THEN 'Pessoa Jurídica (B2B)'
      ELSE 'Não Identificado'
    END as tipo_cliente
  FROM vendas.nota_fiscal nf
  INNER JOIN vendas.item_nota_fiscal inf ON nf.id = inf.id_nota_fiscal
  INNER JOIN geral.pessoa p ON nf.id_cliente = p.id
  LEFT JOIN geral.pessoa_fisica pf ON p.id = pf.id
  LEFT JOIN geral.pessoa_juridica pj ON p.id = pj.id;
  """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)

    # Tratamento de Data
    df["data_venda"] = pd.to_datetime(df["data_venda"]).dt.tz_localize(None)
    df["ano"] = df["data_venda"].dt.year
    return df


# ── Nomes de Vendedores ───────────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def carregar_dados_vendedores():
    """Retorna mapeamento id_vendedor → nome_vendedor via join com RH."""
    engine = _get_engine()
    query = """
  SELECT
    func.id AS id_vendedor,
    COALESCE(pf.nome, pj.razao_social, 'Vendedor ' || func.id::text) AS nome_vendedor
  FROM rh.funcionario func
  INNER JOIN geral.pessoa p  ON func.id = p.id
  LEFT JOIN geral.pessoa_fisica pf ON p.id = pf.id
  LEFT JOIN geral.pessoa_juridica pj ON p.id = pj.id;
  """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df
