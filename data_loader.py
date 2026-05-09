import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import streamlit as st
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# Recuperando as credenciais (tenta .env primeiro, depois st.secrets como fallback)
HOST = os.getenv("DB_HOST") or st.secrets.get("postgres", {}).get("host")
DATABASE = os.getenv("DB_DATABASE") or st.secrets.get("postgres", {}).get("database")
USER = os.getenv("DB_USER") or st.secrets.get("postgres", {}).get("user")
PASSWORD = os.getenv("DB_PASSWORD") or st.secrets.get("postgres", {}).get("password")

if not all([HOST, DATABASE, USER, PASSWORD]):
    st.error("Erro: Credenciais de banco de dados não encontradas no .env ou Streamlit Secrets.")
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
  INNER JOIN vendas.categoria cat ON p.id_categoria = cat.id
  INNER JOIN geral.endereco ender ON nf.id_cliente = ender.id_pessoa
  INNER JOIN geral.bairro b ON ender.id_bairro = b.id
  INNER JOIN geral.cidade c ON b.id_cidade = c.id
  INNER JOIN geral.estado est ON c.id_estado = est.id
  WHERE nf.data_venda >= '2018-01-01'
    AND lower(cat.descricao) NOT IN ('games', 'dvds', 'livros', 'passagens')
    AND est.sigla = 'CE';
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
  INNER JOIN geral.endereco ender ON nf.id_cliente = ender.id_pessoa
  INNER JOIN geral.bairro b ON ender.id_bairro = b.id
  INNER JOIN geral.cidade c ON b.id_cidade = c.id
  INNER JOIN geral.estado est ON c.id_estado = est.id
  WHERE nf.data_venda >= '2018-01-01'
    AND est.sigla = 'CE';
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
    END as tipo_cliente,
    c.descricao AS cidade,
    b.descricao AS bairro,
    cat.descricao AS categoria,
    nf.id_vendedor
  FROM vendas.nota_fiscal nf
  INNER JOIN vendas.item_nota_fiscal inf ON nf.id = inf.id_nota_fiscal
  INNER JOIN vendas.produto p ON inf.id_produto = p.id
  INNER JOIN vendas.categoria cat ON p.id_categoria = cat.id
  INNER JOIN geral.pessoa pessoa ON nf.id_cliente = pessoa.id
  LEFT JOIN geral.pessoa_fisica pf ON pessoa.id = pf.id
  LEFT JOIN geral.pessoa_juridica pj ON pessoa.id = pj.id
  INNER JOIN geral.endereco ender ON nf.id_cliente = ender.id_pessoa
  INNER JOIN geral.bairro b ON ender.id_bairro = b.id
  INNER JOIN geral.cidade c ON b.id_cidade = c.id
  INNER JOIN geral.estado est ON c.id_estado = est.id
  WHERE nf.data_venda >= '2018-01-01'
    AND lower(cat.descricao) NOT IN ('games', 'dvds', 'livros', 'passagens')
    AND est.sigla = 'CE';
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
    """Retorna mapeamento id_vendedor → nome_vendedor consultando a tabela pessoa."""
    engine = _get_engine()
    query = """
  SELECT DISTINCT
    nf.id_vendedor,
    COALESCE(pf.nome, pj.razao_social, 'Vendedor ' || nf.id_vendedor::text) AS nome_vendedor
  FROM vendas.nota_fiscal nf
  LEFT JOIN geral.pessoa_fisica pf ON nf.id_vendedor = pf.id
  LEFT JOIN geral.pessoa_juridica pj ON nf.id_vendedor = pj.id;
  """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df


# ── Dados de Recursos Humanos ──────────────────────────────────────────────────
@st.cache_data(ttl=3600)
def carregar_dados_rh():
    engine = _get_engine()
    query = """
    -- BUST CACHE 3
    SELECT 
        f.id AS id_funcionario,
        pf.nome AS nome,
        pf.nascimento,
        f.pcd,
        e.descricao AS escolaridade,
        l.data_cadastro AS data_admissao,
        l.data_desligamento,
        l.salario,
        c.descricao AS cargo,
        d.descricao AS departamento
    FROM rh.funcionario f
    INNER JOIN geral.pessoa_fisica pf ON f.id_pessoa = pf.id
    LEFT JOIN rh.escolaridade e ON f.id_escolaridade = e.id
    LEFT JOIN rh.lotacao l ON f.id = l.id_funcionario
    LEFT JOIN rh.cargo c ON l.id_cargo = c.id
    LEFT JOIN rh.departamento d ON l.id_departamento = d.id
    """
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
        
    # Feature Engineering
    df["data_admissao"] = pd.to_datetime(df["data_admissao"]).dt.tz_localize(None)
    df["data_desligamento"] = pd.to_datetime(df["data_desligamento"]).dt.tz_localize(None)
    df["nascimento"] = pd.to_datetime(df["nascimento"]).dt.tz_localize(None)
    
    data_ref = pd.Timestamp.today()
    
    # Status
    df["status"] = np.where(df["data_desligamento"].isnull(), "Ativo", "Desligado")
    
    # Idade e Tempo de Casa (anos)
    df["idade"] = (data_ref - df["nascimento"]).dt.days / 365.25
    df["tempo_casa_anos"] = (
        np.where(
            df["status"] == "Ativo",
            (data_ref - df["data_admissao"]).dt.days,
            (df["data_desligamento"] - df["data_admissao"]).dt.days
        )
    ) / 365.25
    
    # Pega apenas a lotação mais recente de cada funcionário
    df = df.sort_values(by=["id_funcionario", "data_admissao"], ascending=[True, False]).drop_duplicates(subset=["id_funcionario"], keep="first")
    
    # Tratamento de dados Nulos
    df["escolaridade"] = df["escolaridade"].fillna("Não Informada")
    
    return df
