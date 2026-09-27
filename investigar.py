"""
Investigacao rapida:
  1. Quais datas nao tem registros de Pagamento (e se batem com fins de semana)
  2. Resolver os 4 'Codigo Empenho' duplicados (mantendo a ultima ocorrencia)
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(r"C:\Users\manoc\.vscode\Projeto EBAC\dados_agosto_completo")

empenho = pd.read_csv(BASE_DIR / "mes_empenho.csv", sep=";", encoding="utf-8", low_memory=False)
pagamento = pd.read_csv(BASE_DIR / "mes_pagamento.csv", sep=";", encoding="utf-8", low_memory=False)

# ---------------------------------------------------------------------------
# 1. Datas sem pagamento
# ---------------------------------------------------------------------------
# Extrai a data (AAAAMMDD) do nome do arquivo de origem
todas_as_datas = pd.date_range("2026-08-01", "2026-08-31")
datas_com_pagamento = pd.to_datetime(
    pagamento["Arquivo Origem"].str.slice(0, 8), format="%Y%m%d"
).unique()

datas_faltando = sorted(set(todas_as_datas) - set(datas_com_pagamento))

print("Datas SEM registros de pagamento:")
for data in datas_faltando:
    dia_semana = data.strftime("%A")  # nome do dia da semana em ingles
    print(f"  {data.strftime('%d/%m/%Y')} - {dia_semana}")

# ---------------------------------------------------------------------------
# 2. Resolver duplicatas de Codigo Empenho (mantem a ultima ocorrencia)
# ---------------------------------------------------------------------------
duplicados_antes = empenho["Código Empenho"].duplicated().sum()
print(f"\nDuplicados antes: {duplicados_antes}")

# Mostra quais sao, pra você dar uma conferida visual
if duplicados_antes > 0:
    codigos_duplicados = empenho.loc[
        empenho["Código Empenho"].duplicated(keep=False), "Código Empenho"
    ].unique()
    print("Códigos duplicados encontrados:")
    print(empenho[empenho["Código Empenho"].isin(codigos_duplicados)][
        ["Código Empenho", "Data Emissão", "Arquivo Origem"]
    ].sort_values("Código Empenho"))

# Mantem apenas a ultima ocorrencia (arquivo mais recente = dado mais atualizado)
empenho_sem_duplicata = empenho.drop_duplicates(subset="Código Empenho", keep="last")
duplicados_depois = empenho_sem_duplicata["Código Empenho"].duplicated().sum()
print(f"\nLinhas antes: {len(empenho)} | depois de remover duplicatas: {len(empenho_sem_duplicata)}")
print(f"Duplicados depois: {duplicados_depois}")

# Salva a versao limpa, que passa a ser a base oficial do projeto
empenho_sem_duplicata.to_csv(
    BASE_DIR / "mes_empenho.csv", index=False, sep=";", encoding="utf-8"
)
print(f"\nArquivo atualizado (sem duplicatas): {BASE_DIR / 'mes_empenho.csv'}")