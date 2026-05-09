"""
Módulo do Agente de IA — renderiza o chat na sidebar do Streamlit.
Importado e chamado pelo app.py.
"""
import os
import re
import pandas as pd
import streamlit as st
from openai import OpenAI
from dotenv import load_dotenv
from sqlalchemy import text
import data_loader

load_dotenv(override=True)

# ── System Prompt ──────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """Você é o Assistente TechVendas, um analista de dados especializado da empresa TechVendas, uma empresa de tecnologia do Ceará.
Você responde perguntas sobre os dados da empresa de forma clara, objetiva e em português brasileiro.
Suas respostas devem ser CONCISAS (máximo 3-4 frases) pois serão exibidas em uma sidebar estreita.

## Regras OBRIGATÓRIAS:
1. Quando precisar consultar dados, gere APENAS queries SQL do tipo SELECT. NUNCA gere INSERT, UPDATE, DELETE, DROP, ALTER, TRUNCATE ou qualquer comando que modifique dados.
2. Retorne a query SQL dentro de um bloco ```sql ... ``` para que o sistema possa executá-la automaticamente.
3. Após receber os resultados, formate sua resposta de forma clara e profissional, usando formatação brasileira (R$ para moeda, vírgula para decimais, ponto para milhar).
4. Se não conseguir responder com os dados disponíveis, diga isso claramente.
5. Sempre limite queries a no máximo 100 linhas de resultado (use LIMIT 100).
6. Use os nomes de schema.tabela corretos conforme documentado abaixo.
7. **SEMPRE use comparações case-insensitive** ao filtrar campos de texto. Use LOWER() em ambos os lados da comparação ou use ILIKE. Exemplos corretos:
   - `WHERE LOWER(cat.descricao) = LOWER('informática')` ✅
   - `WHERE cat.descricao ILIKE '%informática%'` ✅
   - `WHERE cat.descricao = 'informática'` ❌ NUNCA faça isso
8. **Acentuação**: Os dados no banco podem ou não conter acentos. Para maior robustez, ao filtrar por nomes de categorias, produtos ou pessoas, use ILIKE com `%` para busca parcial. Exemplo: `WHERE cat.descricao ILIKE '%informatica%'` encontrará tanto "INFORMATICA" quanto "Informática".

## Estrutura do Banco de Dados (PostgreSQL):

### Schema `geral` — Cadastros Base
- `geral.pessoa` (id PK, data_cadastro) — Superclasse: todo cliente, vendedor e fornecedor é uma "pessoa"
- `geral.pessoa_fisica` (id PK/FK→pessoa, nome, cpf, nascimento)
- `geral.pessoa_juridica` (id PK/FK→pessoa, razao_social, cnpj)
- `geral.responsavel_juridico` (id_pessoa_fisica FK→pessoa, id_pessoa_juridica FK→pessoa)
- `geral.estado` (id PK, sigla, descricao)
- `geral.cidade` (id PK, id_estado FK→estado, descricao)
- `geral.bairro` (id PK, id_cidade FK→cidade, descricao)
- `geral.endereco` (id PK, id_pessoa FK→pessoa, id_bairro FK→bairro, rua, numero, cep, complemento)
- `geral.tipo_contato` (id PK, descricao, sigla)
- `geral.contato` (id PK, id_tipo_contato FK→tipo_contato, id_pessoa FK→pessoa, valor, principal)

### Schema `vendas` — Operações Comerciais
- `vendas.categoria` (id PK, descricao)
- `vendas.forma_pagamento` (id PK, descricao)
- `vendas.produto` (id PK, id_fornecedor FK→geral.pessoa, id_categoria FK→categoria, nome, valor_venda NUMERIC(18,2), valor_custo NUMERIC(18,2))
- `vendas.nota_fiscal` (id PK, id_vendedor FK→geral.pessoa, id_cliente FK→geral.pessoa, id_forma_pagto FK→forma_pagamento, data_venda TIMESTAMP, numero_nf, valor NUMERIC(18,2))
- `vendas.item_nota_fiscal` (id PK, id_produto FK→produto, id_nota_fiscal FK→nota_fiscal, quantidade INT, valor_venda_real NUMERIC(18,2), valor_unitario NUMERIC(18,2))
- `vendas.parcela` (id PK BIGINT, id_nota_fiscal FK→nota_fiscal, numero INT, vencimento DATE, valor NUMERIC(18,2))

### Schema `financeiro` — Contas a Pagar/Receber
- `financeiro.situacao_titulo` (id PK, descricao) — ex: ABERTA, ATRASADA, PAGA
- `financeiro.conta_receber` (id PK, id_parcela FK→vendas.parcela, vencimento DATE, valor_original NUMERIC(18,2), valor_atual NUMERIC(18,2), id_situacao FK→situacao_titulo, criado_em, atualizado_em, data_recebimento DATE, id_forma_pagamento FK→vendas.forma_pagamento)
- `financeiro.conta_pagar` (id PK, documento, emissao DATE, vencimento DATE, valor_original NUMERIC(18,2), valor_atual NUMERIC(18,2), id_situacao FK→situacao_titulo, criado_em, atualizado_em, data_pagamento DATE, id_forma_pagamento FK→vendas.forma_pagamento, descricao)

### Schema `rh` — Recursos Humanos
- `rh.escolaridade` (id PK, descricao, codigo)
- `rh.funcionario` (id PK, id_pessoa FK→geral.pessoa, id_escolaridade FK→escolaridade, pretensao_salarial NUMERIC(18,2), pcd BOOLEAN)
- `rh.departamento` (id PK, descricao)
- `rh.cargo` (id PK, descricao)
- `rh.lotacao` (id PK, id_cargo FK→cargo, id_departamento FK→departamento, id_funcionario FK→funcionario, data_cadastro TIMESTAMP, data_desligamento TIMESTAMP, salario NUMERIC(18,2))

## Contexto de Negócio:
- Os dados de vendas são filtrados para o estado do Ceará (CE) e a partir de 2018.
- As categorias 'games', 'dvds', 'livros', 'passagens' são excluídas das análises de vendas por serem irrelevantes ao core business de tecnologia.
- Não existem tabelas separadas de "cliente" ou "vendedor": são papéis desempenhados por registros na tabela geral.pessoa.
- Para obter o nome de um vendedor: JOIN geral.pessoa_fisica ON id_vendedor = pessoa_fisica.id
- Para obter o nome de um cliente: LEFT JOIN geral.pessoa_fisica e LEFT JOIN geral.pessoa_juridica, usando COALESCE.

## Valores Reais das Tabelas de Domínio (use ILIKE para comparar):

### Categorias de Produtos (`vendas.categoria.descricao`):
CELULARES, DVDS, ELETRODOMESTICOS, GAMES, INFORMATICA, LIVROS, MOVEIS, PASSAGENS, TV E AUDIO

### Departamentos (`rh.departamento.descricao`):
FINANCEIRO, JURIDICO, TECNOLOGIA, VENDAS

### Cargos (`rh.cargo.descricao`):
ADVOGADO, ANALISTA DE DADOS, ANALISTA DE SISTEMAS, ANALISTA FINANCEIRO, PROGRAMADOR, VENDEDOR

### Formas de Pagamento (`vendas.forma_pagamento.descricao`):
Boleto, Cartão de crédito, Cartão de débito, Cheque, Crediário, Dinheiro, Pagamentos pelo celular, PIX, Vales

### Situação de Títulos Financeiros (`financeiro.situacao_titulo.descricao`):
ATRASADA, CANCELADA, EM_ABERTO, LIQUIDADA

**IMPORTANTE**: Todos os valores acima estão em MAIÚSCULAS no banco (exceto formas de pagamento). Quando o usuário perguntar sobre "informática", "celulares", "tv", etc., use ILIKE para correspondência flexível. Exemplo: `WHERE cat.descricao ILIKE '%informatica%'`
"""

FORBIDDEN_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|TRUNCATE|CREATE|GRANT|REVOKE|EXEC|EXECUTE)\b",
    re.IGNORECASE,
)


def _extract_sql(text_content: str) -> str | None:
    match = re.search(r"```sql\s*(.*?)```", text_content, re.DOTALL | re.IGNORECASE)
    return match.group(1).strip() if match else None


def _is_safe(sql: str) -> bool:
    return not FORBIDDEN_KEYWORDS.search(sql)


def _run_query(sql: str) -> pd.DataFrame | str:
    try:
        engine = data_loader._get_engine()
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn)
    except Exception as e:
        return f"Erro: {e}"


def _chat(messages: list) -> str:
    api_key = os.getenv("OPENAI_API_KEY") or st.secrets.get("openai", {}).get("api_key")
    if not api_key:
        return "⚠️ Chave da OpenAI não configurada. Configure OPENAI_API_KEY no .env ou no Streamlit Secrets."
    client = OpenAI(api_key=api_key)
    r = client.chat.completions.create(
        model="gpt-4o-mini", messages=messages, temperature=0.2, max_tokens=1024
    )
    return r.choices[0].message.content


def render_sidebar_agent():
    """Renderiza o agente de IA dentro da sidebar do Streamlit."""

    st.sidebar.markdown("### 🤖 Assistente IA")

    # Inicializa histórico
    if "ai_messages" not in st.session_state:
        st.session_state["ai_messages"] = []

    # Container de mensagens
    chat_container = st.sidebar.container(height=350)

    with chat_container:
        if not st.session_state["ai_messages"]:
            st.caption("Pergunte sobre vendas, produtos, clientes, financeiro ou RH.")
        for msg in st.session_state["ai_messages"]:
            with st.chat_message(msg["role"], avatar="👤" if msg["role"] == "user" else "🤖"):
                st.markdown(msg["content"], unsafe_allow_html=True)

    # Input via form para evitar rerun a cada digitação
    with st.sidebar.form("ai_form", clear_on_submit=True):
        user_input = st.text_input(
            "Pergunta",
            placeholder="Ex: Qual o faturamento de 2024?",
            label_visibility="collapsed",
        )
        submitted = st.form_submit_button("Enviar", use_container_width=True)

    if submitted and user_input.strip():
        pergunta = user_input.strip()
        st.session_state["ai_messages"].append({"role": "user", "content": pergunta})

        # Monta contexto para o GPT
        gpt_msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
        for m in st.session_state["ai_messages"]:
            gpt_msgs.append({"role": m["role"], "content": m["content"]})

        # 1ª chamada
        resposta_gpt = _chat(gpt_msgs)
        sql = _extract_sql(resposta_gpt)

        if sql:
            if not _is_safe(sql):
                resposta_final = "⛔ Operação bloqueada. Somente consultas SELECT."
            else:
                resultado = _run_query(sql)

                if isinstance(resultado, str):
                    # Tenta corrigir
                    gpt_msgs.append({"role": "assistant", "content": resposta_gpt})
                    gpt_msgs.append({"role": "user", "content": f"Erro: {resultado}. Corrija a query."})
                    resposta_corrigida = _chat(gpt_msgs)
                    sql_retry = _extract_sql(resposta_corrigida)
                    if sql_retry and _is_safe(sql_retry):
                        resultado = _run_query(sql_retry)
                        resposta_gpt = resposta_corrigida

                if isinstance(resultado, pd.DataFrame):
                    resultado_str = resultado.head(30).to_string(index=False)
                    gpt_msgs.append({"role": "assistant", "content": resposta_gpt})
                    gpt_msgs.append({
                        "role": "user",
                        "content": f"Dados retornados:\n{resultado_str}\n\nResponda minha pergunta de forma concisa em pt-BR. Formate valores em R$. NÃO inclua SQL.",
                    })
                    resposta_final = _chat(gpt_msgs)
                elif isinstance(resultado, str):
                    resposta_final = f"❌ Não consegui consultar. Tente reformular.\n\n`{resultado}`"
                else:
                    resposta_final = resposta_gpt
        else:
            resposta_final = resposta_gpt

        st.session_state["ai_messages"].append({"role": "assistant", "content": resposta_final})
        st.rerun()

    # Botão limpar
    if st.session_state["ai_messages"]:
        if st.sidebar.button("🗑️ Limpar Conversa", use_container_width=True, key="clear_ai"):
            st.session_state["ai_messages"] = []
            st.rerun()
