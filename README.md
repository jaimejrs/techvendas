<div align="center">

<img src="logo_projeto.png" alt="TechVendas BI" width="200"/>

# TechVendas BI — Dashboard de Inteligência Comercial

**Plataforma analítica completa para tomada de decisão baseada em dados**

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://techvendasdigital.streamlit.app)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.x-FF4B4B?logo=streamlit&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-5.x-3F4F75?logo=plotly&logoColor=white)

[Acesse o Dashboard ao vivo](https://techvendasdigital.streamlit.app)

</div>

---

## Sobre o Projeto

O **TechVendas BI** é um dashboard de Business Intelligence desenvolvido para a **TechVendas**, empresa de tecnologia do Ceará. A plataforma centraliza dados de vendas, produtos, clientes, financeiro e recursos humanos em uma interface moderna e interativa, com um assistente de IA integrado que responde perguntas em linguagem natural sobre os dados da empresa.

### Telas do Dashboard

**Visão Geral de Vendas e Performance**

![Dashboard de Vendas](dashboard_vendas.png)

**Módulo de CRM (Customer Relationship Management)**

![Dashboard de CRM](dashboard_crm.png)

---

## Funcionalidades

### Módulos do Dashboard

| Módulo | Descrição |
|--------|-----------|
| **Vendas** | Curva de crescimento receita vs margem, sazonalidade, heatmap dia/trimestre, performance do time de vendas e análise MoM |
| **Produtos** | Classificação ABC por Pareto, matriz estratégica volume × margem, treemap de rentabilidade, drill-down por SKU |
| **CRM** | Segmentação B2B vs B2C, densidade geográfica por bairro, mix de produtos por perfil e faturamento por cliente |
| **RH** | People Analytics — headcount por departamento, salário médio por cargo, turnover e tempo de casa |
| **Assistente IA** | Chatbot integrado na sidebar com GPT-4o-mini, que gera SQL automaticamente e responde em português |

### Design & UX
- Paleta de cores sofisticada e consistente em todos os gráficos (Violeta / Teal / Coral)
- KPI Cards com animações hover e gradiente
- Navegação horizontal entre módulos
- Filtros globais por Ano e Categoria (sidebar)
- Formatação pt-BR em todos os valores monetários e numéricos

---

## Stack Tecnológica

### Core
| Tecnologia | Versão | Uso |
|-----------|--------|-----|
| **Python** | 3.11+ | Linguagem principal |
| **Streamlit** | 1.x | Framework de UI e deploy |
| **PostgreSQL** | 15 | Banco de dados relacional |
| **SQLAlchemy** | 2.x | ORM e engine de conexão (singleton pattern) |

### Visualização
| Tecnologia | Uso |
|-----------|-----|
| **Plotly Express** | Gráficos interativos (barras, pizza, scatter, área, treemap) |
| **Plotly Graph Objects** | Gráficos customizados (dual-axis, heatmap, waterfall) |

### Inteligência Artificial
| Tecnologia | Uso |
|-----------|-----|
| **OpenAI GPT-4o-mini** | Geração de SQL e respostas em linguagem natural |
| **openai SDK** | Integração com a API da OpenAI |

### Dados & Utilitários
| Tecnologia | Uso |
|-----------|-----|
| **pandas** | Manipulação e feature engineering dos dados |
| **numpy** | Cálculos vetorizados (turnover, tempo de casa, idade) |
| **python-dotenv** | Gerenciamento de variáveis de ambiente |

---

## Estrutura do Projeto

```text
techvendas/
├── app.py                    # Entrypoint — navegação, CSS global, filtros, sidebar IA
├── data_loader.py            # Queries SQL e feature engineering (cache @st.cache_data)
├── ai_agent.py               # Módulo do Assistente IA (OpenAI + sidebar chat)
├── utils.py                  # Formatadores pt-BR + paleta de cores (class C)
├── requirements.txt          # Dependências do projeto
├── logo_projeto.png          # Logo da aplicação
├── .gitignore                # .env e venv excluídos do repositório
├── .streamlit/
│   └── secrets.toml          # Credenciais locais (ignorado pelo git)
└── pages/
    ├── 1_Vendas.py           # Análise Comercial e Performance
    ├── 2_Produtos.py         # Inteligência de Catálogo e Rentabilidade
    ├── 3_CRM.py              # Customer Relationship Management
    └── 4_Recursos_Humanos.py # People Analytics
```

---

## Rodando Localmente

### 1. Pré-requisitos
- Python 3.11+
- Acesso ao banco de dados PostgreSQL

### 2. Clone o repositório
```bash
git clone https://github.com/jaimejrs/techvendas.git
cd techvendas
```

### 3. Crie e ative um ambiente virtual
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```

### 4. Instale as dependências
```bash
pip install -r requirements.txt
```

### 5. Configure as credenciais
Crie um arquivo `.env` na raiz do projeto:
```env
DB_HOST=seu_host_postgres
DB_DATABASE=seu_banco
DB_USER=seu_usuario
DB_PASSWORD=sua_senha
OPENAI_API_KEY=sua_chave_openai
```

### 6. Inicie o dashboard
```bash
streamlit run app.py
```

Acesse em: **http://localhost:8501**

---

## Deploy — Streamlit Cloud

O projeto está disponível publicamente em:

> **https://techvendasdigital.streamlit.app**

As credenciais são configuradas via **Streamlit Secrets** (painel da plataforma), sem expor dados sensíveis no repositório.

---

## Segurança

- O arquivo `.env` está no `.gitignore` — credenciais nunca são commitadas
- O Assistente IA aceita apenas queries `SELECT` — operações destrutivas são bloqueadas por regex
- Pool de conexões singleton via `@st.cache_resource` — sem overhead de reconexões
- Cache de dados com `@st.cache_data(ttl=3600)` — reduz carga no banco

---

## Licença

Este projeto foi desenvolvido para fins acadêmicos e demonstrativos.

---

<div align="center">
  <sub>Desenvolvido usando Python, Streamlit e OpenAI</sub>
</div>
