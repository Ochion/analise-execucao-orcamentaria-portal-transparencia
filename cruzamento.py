"""
Fase 1 (fechamento) - Cruzamento das tabelas
Constroi uma visao consolidada de execucao orcamentaria por empenho:
    Valor Empenhado  x  Valor Liquidado  x  Valor Pago

Pressupoe que 'exploracao.py' ja rodou e os CSVs estao no mesmo BASE_DIR.
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(r"C:\Users\manoc\.vscode\Projeto EBAC")

empenho = pd.read_csv(BASE_DIR / "20260831_Despesas_Empenho.csv", sep=";", encoding="latin1", decimal=",", low_memory=False)
liquidacao_empenhos = pd.read_csv(BASE_DIR / "20260831_Despesas_Liquidacao_EmpenhosImpactados.csv", sep=";", encoding="latin1", decimal=",", low_memory=False)
pagamento_empenhos = pd.read_csv(BASE_DIR / "20260831_Despesas_Pagamento_EmpenhosImpactados.csv", sep=";", encoding="latin1", decimal=",", low_memory=False)

# ---------------------------------------------------------------------------
# 1. Agregar valores liquidados e pagos por empenho
#    (um empenho pode ter varias liquidacoes/pagamentos parciais)
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
# 2. Montar a tabela consolidada de execucao, partindo do Empenho
#    (traz as dimensoes: orgao, favorecido, funcao, elemento de despesa)
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

execucao["% Liquidado"] = (
    execucao["Valor Liquidado (R$)"] / execucao["Valor Original do Empenho"] * 100
)
execucao["% Pago"] = (
    execucao["Valor Pago (R$)"] / execucao["Valor Original do Empenho"] * 100
)

# ---------------------------------------------------------------------------
# 3. Conferencia rapida
# ---------------------------------------------------------------------------
print("Tabela de execucao orcamentaria consolidada:")
print(f"Shape: {execucao.shape}")
print(execucao.head(10))

print("\nQuantos empenhos ja tem liquidacao/pagamento registrado neste snapshot:")
print(f"  Com liquidacao: {(execucao['Valor Liquidado (R$)'] > 0).sum()} de {len(execucao)}")
print(f"  Com pagamento:  {(execucao['Valor Pago (R$)'] > 0).sum()} de {len(execucao)}")

# Salva para usar na fase 2 (EDA)
execucao.to_csv(BASE_DIR / "execucao_consolidada.csv", index=False, sep=";", encoding="utf-8")
print(f"\nSalvo em: {BASE_DIR / 'execucao_consolidada.csv'}")