"""
Fase 1 (fechamento, mes completo) - Cruzamento das tabelas mensais
Constroi a visao consolidada de execucao orcamentaria por empenho:
    Valor Empenhado  x  Valor Liquidado  x  Valor Pago

Le as bases ja concatenadas por 'concatenar_mes.py' (mes_*.csv).
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(r"C:\Users\manoc\.vscode\Projeto EBAC\dados_agosto_completo")

empenho = pd.read_csv(BASE_DIR / "mes_empenho.csv", sep=";", encoding="utf-8", low_memory=False)
liquidacao_empenhos = pd.read_csv(BASE_DIR / "mes_liquidacao_empenhos.csv", sep=";", encoding="utf-8", low_memory=False)
pagamento_empenhos = pd.read_csv(BASE_DIR / "mes_pagamento_empenhos.csv", sep=";", encoding="utf-8", low_memory=False)

# ---------------------------------------------------------------------------
# 0. Tratamento: remover duplicatas de Codigo Empenho
#    Mantem a ocorrencia do arquivo mais recente (nome do arquivo comeca com
#    AAAAMMDD, entao ordenar como string funciona)
# ---------------------------------------------------------------------------
n_antes = len(empenho)
empenho = empenho.sort_values("Arquivo Origem").drop_duplicates(
    subset="Código Empenho", keep="last"
)
print(f"Duplicatas de Código Empenho removidas: {n_antes - len(empenho)}")

# ---------------------------------------------------------------------------
# 1. Agregar valores liquidados e pagos por empenho
# ---------------------------------------------------------------------------
liq_por_empenho = (
    liquidacao_empenhos.groupby("Código Empenho")["Valor Liquidado (R$)"]
    .sum()
    .reset_index()
)

pag_por_empenho = (
    pagamento_empenhos.groupby("Código Empenho")["Valor Pago (R$)"]
    .sum()
    .reset_index()
)

# ---------------------------------------------------------------------------
# 2. Montar a tabela consolidada de execucao
# ---------------------------------------------------------------------------
colunas_dimensao = [
    "Código Empenho",
    "Data Emissão",
    "Órgão Superior",
    "Órgão",
    "Favorecido",
    "Categoria de Despesa",
    "Elemento de Despesa",
    "Função",
    "Valor Original do Empenho",
]

execucao = (
    empenho[colunas_dimensao]
    .merge(liq_por_empenho, on="Código Empenho", how="left")
    .merge(pag_por_empenho, on="Código Empenho", how="left")
)

execucao["Valor Liquidado (R$)"] = execucao["Valor Liquidado (R$)"].fillna(0)
execucao["Valor Pago (R$)"] = execucao["Valor Pago (R$)"].fillna(0)

execucao["% Liquidado"] = execucao["Valor Liquidado (R$)"] / execucao["Valor Original do Empenho"] * 100
execucao["% Pago"] = execucao["Valor Pago (R$)"] / execucao["Valor Original do Empenho"] * 100

# ---------------------------------------------------------------------------
# 3. Conferencia
# ---------------------------------------------------------------------------
print(f"\nTabela de execucao consolidada: {execucao.shape}")
print(execucao.head(10))

print(f"\nCom liquidacao: {(execucao['Valor Liquidado (R$)'] > 0).sum()} de {len(execucao)}")
print(f"Com pagamento:  {(execucao['Valor Pago (R$)'] > 0).sum()} de {len(execucao)}")

print(f"\nValor total empenhado no mes: R$ {execucao['Valor Original do Empenho'].sum():,.2f}")
print(f"Valor total liquidado no mes: R$ {execucao['Valor Liquidado (R$)'].sum():,.2f}")
print(f"Valor total pago no mes:      R$ {execucao['Valor Pago (R$)'].sum():,.2f}")

execucao.to_csv(BASE_DIR / "execucao_consolidada_mes.csv", index=False, sep=";", encoding="utf-8")
print(f"\nSalvo em: {BASE_DIR / 'execucao_consolidada_mes.csv'}")