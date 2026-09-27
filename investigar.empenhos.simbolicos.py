"""
Diagnostico: empenhos com "Valor Original do Empenho" simbolico (<=R$100)
mas "Valor Pago" bem maior -- possivel indicio de empenho estimativo/global
que foi reforcado depois (valor original nao reflete o total executado).
"""

import pandas as pd
from pathlib import Path

BASE_DIR = Path(r"C:\Users\manoc\.vscode\Projeto EBAC\dados_agosto_completo")

df = pd.read_csv(BASE_DIR / "execucao_consolidada_mes.csv", sep=";", encoding="utf-8", low_memory=False)

suspeitos = df[
    (df["Valor Original do Empenho"] <= 100) & (df["Valor Pago (R$)"] > 10_000)
].sort_values("Valor Pago (R$)", ascending=False)

print(f"Empenhos com valor original <= R$100 mas pago > R$10.000: {len(suspeitos)} de {len(df)}")
print(
    suspeitos[
        [
            "Código Empenho",
            "Órgão",
            "Favorecido",
            "Elemento de Despesa",
            "Valor Original do Empenho",
            "Valor Pago (R$)",
        ]
    ].head(20).to_string(index=False)
)

print(f"\nValor total pago nesses casos suspeitos: R$ {suspeitos['Valor Pago (R$)'].sum():,.2f}")
print(f"Isso representa {suspeitos['Valor Pago (R$)'].sum() / df['Valor Pago (R$)'].sum() * 100:.2f}% do total pago no mes")