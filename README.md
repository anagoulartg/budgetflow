# BudgetFlow

Central interna para formacao, aprovacao e exportacao do orcamento anual.

BudgetFlow e uma aplicacao web desenvolvida em Python com Streamlit para substituir o controle manual de solicitacoes orcamentarias em planilhas. O sistema organiza o fluxo entre Gestores, Diretoria, Controladoria e Conselho, mantendo historico de decisoes, metas por area, solicitacoes de ajuste e exportacao final para ERP.

## Visao Geral

O projeto simula um processo corporativo de planejamento orcamentario:

- Gestores cadastram despesas e investimentos por area, centro de custo, conta contabil e mes.
- Diretoria aprova, reprova ou solicita ajustes apenas para os itens da sua area.
- Gestores recebem os pedidos de ajuste, corrigem os itens e reenviam para aprovacao.
- Controladoria acompanha tudo de forma consolidada, define metas por area e analisa consistencia.
- Conselho delibera os itens aprovados pela Diretoria.
- A exportacao gera arquivos CSV e Excel no layout esperado pelo ERP.

## Principais Funcionalidades

- Login simulado por perfil
- Dashboard executivo com indicadores por perfil
- Cadastro manual de solicitacoes orcamentarias
- Recorrencia mensal para gastos fixos
- Importacao Excel/CSV
- Metas por area e tipo de gasto
- Aprovacao em lote pela Diretoria
- Deliberacao em lote pelo Conselho
- Mensagens de ajuste para o gestor responsavel
- Edicao e reenvio de itens em ajuste
- Exclusao de solicitacoes pendentes pelo gestor
- Historico de aprovacoes
- Exportacao CSV/Excel para ERP

## Perfis de Acesso

| Perfil | Acesso |
| --- | --- |
| Gestor | Cadastra itens, acompanha status, corrige ajustes e exclui itens pendentes |
| Diretoria | Aprova, reprova ou solicita ajustes apenas da sua area |
| Controladoria | Define metas e visualiza todas as areas de forma consolidada |
| Conselho | Delibera os itens aprovados pela Diretoria |
| Admin | Perfil de apoio para testes |

## Usuarios de Teste

Todos os usuarios usam a senha `123456`.

| Usuario | Perfil |
| --- | --- |
| gestor.demo | Gestor |
| diretoria.demo | Diretoria Comercial |
| diretoria.adm | Diretoria Administrativo |
| diretoria.industrial | Diretoria Industrial |
| controladoria.demo | Controladoria |
| conselho.demo | Conselho |
| admin.demo | Admin |

## Stack

- Python
- Streamlit
- Pandas
- SQLite
- SQLAlchemy
- Plotly
- Openpyxl

## Estrutura

```text
budgetflow/
├── app.py
├── assets/
├── database/
│   ├── db.py
│   └── models.py
├── pages/
│   ├── 1_Gestor.py
│   ├── 2_Diretoria.py
│   ├── 3_Conselho.py
│   ├── 4_Metas.py
│   ├── 5_Controladoria.py
│   ├── 6_Exportacao_ERP.py
│   └── 7_Historico_e_Mensagens.py
├── services/
│   ├── aprovacoes.py
│   ├── auth.py
│   ├── exportador_erp.py
│   ├── metas.py
│   ├── orcamentos.py
│   └── ui.py
├── exports/
├── templates/
├── requirements.txt
└── README.md
```

## Como Rodar

Clone o repositorio e instale as dependencias:

```bash
cd budgetflow
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

No Linux/macOS:

```bash
source .venv/bin/activate
```

Inicie a aplicacao:

```bash
streamlit run app.py
```

O banco SQLite sera criado automaticamente em `database/budgetflow.db` na primeira execucao.

## Fluxo Sugerido para Teste

1. Entre como `controladoria.demo`.
2. Acesse **4. Metas** e cadastre metas para Administrativo, Comercial e Industrial.
3. Entre como `gestor.demo`.
4. Cadastre uma despesa ou investimento em **1. Gestor**.
5. Entre como um diretor da area correspondente.
6. Aprove, reprove ou solicite ajuste em lote.
7. Volte como gestor para corrigir itens em ajuste.
8. Entre como Conselho para deliberar os itens aprovados pela Diretoria.
9. Use **6. Exportacao ERP** para baixar CSV/Excel.

## Layout ERP

O arquivo final possui as colunas:

```text
empresa;ano;centro_custo;conta_contabil;mes;valor_aprovado;historico;tipo
```

Exemplo:

```text
001;2026;ADM;3.1.01.001;01;15000;Orcamento aprovado Administrativo;Despesa
```

## Observacoes de Implementacao

- A autenticacao e simulada para fins de demonstracao.
- O SQLite foi escolhido para facilitar execucao local.
- A arquitetura separa telas, modelos e servicos de negocio.
- Arquivos gerados, cache Python e banco local nao sao versionados.

## Melhorias Futuras

- Autenticacao real com hash de senha
- Controle granular de permissoes
- Parametrizacao de areas, centros de custo e contas contabeis
- Workflow de revisao por rodada orcamentaria
- Integracao direta com ERP
- Auditoria com trilha de alteracoes por campo
