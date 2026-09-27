# Análise da Execução Orçamentária do Governo Federal — Portal da Transparência (2026)

Projeto completo de análise de dados em 4 etapas, do dado público bruto a um dashboard de BI interativo: seleção e engenharia da base, análise exploratória, tratamento/preparação e visualização.

**Stack:** Python, Pandas, Google BigQuery, Looker Studio

🔗 [Dashboard ao vivo](https://datastudio.google.com/reporting/12a3e0c7-f740-4e62-9580-958aa2e74560)

## Contexto

Pergunta de negócio: como está a execução orçamentária do Governo Federal em agosto de 2026 — quais órgãos e categorias de despesa concentram mais gastos, e qual o percentual de execução (liquidado/pago) entre eles?

Fonte dos dados: módulo de Despesas do [Portal da Transparência](https://portaldatransparencia.gov.br/download-de-dados/despesas), dados públicos oficiais do Governo Federal.

## Etapa 1 — Seleção e Engenharia da Base

Consolidação de mais de 205 mil empenhos e suas tabelas relacionadas (liquidação, pagamento) a partir de 31 arquivos diários do Portal da Transparência, concatenados em uma base relacional única via Python/Pandas e ligados pelo campo `Código Empenho`.

## Etapa 2 — Análise Exploratória

5 análises exploratórias (distribuição, outliers, ranking por órgão, correlação, série temporal). Principais achados:

- O Ministério da Fazenda lidera o ranking de órgãos com R$ 426,56 bilhões empenhados — mais do triplo do segundo colocado — dominado por operações de rolagem de dívida pública, não gasto corrente.
- 15,32% dos empenhos (31.472) são outliers estatísticos (método IQR).
- Correlação de Pearson de 0,6585 entre valor empenhado e valor pago.
- Cerca de 91% das "Despesas de Capital" do mês correspondem a amortização de dívida, não investimento.

## Etapa 3 — Tratamento e Preparação dos Dados

Remoção de duplicatas, padronização de texto e datas, e criação de 4 colunas derivadas (`% Liquidado`, `% Pago`, `Estorno ou Cancelamento`, `Situação da Execução`) preparando a base para BI.

## Etapa 4 — Dashboard Interativo (BigQuery + Looker Studio)

Carga da base tratada no BigQuery e construção de um dashboard interativo no Looker Studio, com 5 visualizações (barras, linha, dispersão, rosca, tabela dinâmica) e filtros cruzados por período, órgão e situação de execução.

## Estrutura do repositório

| Script | Função |
|---|---|
| `concatenar.py` | Concatena os 31 arquivos diários em bases mensais |
| `tratamento_fase3.py` | Tratamento, padronização e colunas derivadas |
| `eda.py` | As 5 análises exploratórias e gráficos |
| `subir_bigquery.py` | Carga da base tratada no BigQuery |

## Principal insight

A liderança do Ministério da Fazenda no ranking de gastos — e boa parte do pico de despesas de capital do mês — não reflete investimento público tradicional, e sim operações de rolagem da dívida pública. Uma distinção que só aparece quando se cruzam os dados de execução (empenho, liquidação e pagamento) com a classificação por elemento de despesa, reforçando a importância de ir além dos totais superficiais numa análise orçamentária.
