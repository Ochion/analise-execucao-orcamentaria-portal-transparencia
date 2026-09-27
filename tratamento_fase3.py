"""
Fase 3 - Tratamento e Preparacao dos Dados
Aplica e documenta os 4 requisitos minimos da fase:
  1. Tratar valores ausentes / inconsistencias
  2. Padronizar formatos (datas, texto, numerico)
  3. Criar colunas derivadas (pelo menos 2 -- aqui ficam 4)
  4. Deixar as tabelas prontas para analise/visualizacao (fase 4)

Le as tabelas mensais concatenadas (mes_*.csv) e gera as versoes tratadas,
alem da base final "execucao_tratada_mes.csv" para o dashboard.
"""

import numpy as np
import pandas as pd
from pathlib import Path

BASE_DIR = Path(r"C:\Users\manoc\.vscode\Projeto EBAC\dados_agosto_completo")


# ---------------------------------------------------------------------------
# Funcoes de padronizacao (reutilizaveis em qualquer tabela)
# ---------------------------------------------------------------------------
def padronizar_texto(df: pd.DataFrame) -> pd.DataFrame:
    """Remove espacos em branco nas pontas de todas as colunas de texto."""
    colunas_texto = df.select_dtypes(include="object").columns
    for col in colunas_texto:
        antes = df[col].copy()
        df[col] = df[col].astype(str).str.strip()
        alterados = (antes.astype(str) != df[col]).sum()
        if alterados > 0:
            print(f"  - '{col}': {alterados} valores com espacos extras removidos")
    return df


def padronizar_data(df: pd.DataFrame, coluna: str = "Data Emissão") -> pd.DataFrame:
    """Converte a coluna de data (formato dd/mm/aaaa) para datetime real."""
    if coluna in df.columns:
        df[coluna] = pd.to_datetime(df[coluna], format="%d/%m/%Y")
    return df


def tratar_processo_ausente(df: pd.DataFrame) -> pd.DataFrame:
    """A coluna 'Processo' pode vir vazia quando a despesa nao tem processo
    administrativo vinculado (ex: descontos em folha). Isso e um estado
    valido, entao preenchemos com um rotulo explicito em vez de deixar NaN."""
    if "Processo" in df.columns:
        n_nulos = df["Processo"].isna().sum()
        if n_nulos > 0:
            df["Processo"] = df["Processo"].fillna("Não se aplica")
            print(f"  - 'Processo': {n_nulos} valores ausentes preenchidos com 'Não se aplica'")
    return df


def carregar_e_tratar(nome_arquivo: str, nome_tabela: str) -> pd.DataFrame:
    print(f"\nTratando '{nome_tabela}'...")
    df = pd.read_csv(BASE_DIR / nome_arquivo, sep=";", encoding="utf-8", low_memory=False)
    df = padronizar_texto(df)
    df = padronizar_data(df)
    df = tratar_processo_ausente(df)
    return df


def main():
    print("=" * 80)
    print("FASE 3 - TRATAMENTO E PREPARACAO DOS DADOS")
    print("=" * 80)

    # -----------------------------------------------------------------
    # 1 e 2. Padronizacao + tratamento de ausentes, tabela por tabela
    # -----------------------------------------------------------------
    empenho = carregar_e_tratar("mes_empenho.csv", "empenho")
    liquidacao_empenhos = carregar_e_tratar("mes_liquidacao_empenhos.csv", "liquidacao_empenhos")
    pagamento_empenhos = carregar_e_tratar("mes_pagamento_empenhos.csv", "pagamento_empenhos")

    # Duplicatas de Código Empenho: ja tratado em execucao anterior (0 restantes),
    # mas confere de novo aqui pra deixar documentado no log desta fase
    duplicados = empenho["Código Empenho"].duplicated().sum()
    print(f"\nConferencia de duplicatas em 'Código Empenho': {duplicados} (esperado: 0)")

    # -----------------------------------------------------------------
    # 3. Colunas derivadas
    # -----------------------------------------------------------------
    print("\nCriando colunas derivadas...")

    liq_por_empenho = (
        liquidacao_empenhos.groupby("Código Empenho")["Valor Liquidado (R$)"].sum().reset_index()
    )
    pag_por_empenho = (
        pagamento_empenhos.groupby("Código Empenho")["Valor Pago (R$)"].sum().reset_index()
    )

    colunas_dimensao = [
        "Código Empenho", "Data Emissão", "Órgão Superior", "Órgão", "Favorecido",
        "Categoria de Despesa", "Elemento de Despesa", "Função", "Valor Original do Empenho",
    ]
    execucao = (
        empenho[colunas_dimensao]
        .merge(liq_por_empenho, on="Código Empenho", how="left")
        .merge(pag_por_empenho, on="Código Empenho", how="left")
    )
    execucao["Valor Liquidado (R$)"] = execucao["Valor Liquidado (R$)"].fillna(0).round(2)
    execucao["Valor Pago (R$)"] = execucao["Valor Pago (R$)"].fillna(0).round(2)

    # Derivada 1 e 2 (ja existiam)
    execucao["% Liquidado"] = (
        execucao["Valor Liquidado (R$)"] / execucao["Valor Original do Empenho"] * 100
    ).round(2)
    execucao["% Pago"] = (
        execucao["Valor Pago (R$)"] / execucao["Valor Original do Empenho"] * 100
    ).round(2)
    print("  - '% Liquidado' e '% Pago' criadas")

    # Derivada 3: flag de estorno/cancelamento (valor original <= 0)
    execucao["Estorno ou Cancelamento"] = execucao["Valor Original do Empenho"] <= 0
    n_estornos = execucao["Estorno ou Cancelamento"].sum()
    print(f"  - 'Estorno ou Cancelamento' criada ({n_estornos} empenhos marcados)")

    # Derivada 4: situacao da execucao (categorica, otima pra filtro no dashboard)
    def classificar_situacao(row):
        if row["Estorno ou Cancelamento"]:
            return "Estorno/Cancelamento"
        if row["% Pago"] >= 99.5:
            return "Pago Integralmente"
        if row["% Pago"] > 0:
            return "Pago Parcialmente"
        if row["% Liquidado"] > 0:
            return "Liquidado, Aguardando Pagamento"
        return "Empenhado, Sem Execução"

    execucao["Situação da Execução"] = execucao.apply(classificar_situacao, axis=1)
    print("  - 'Situação da Execução' criada")
    print("\nDistribuição da Situação da Execução:")
    print(execucao["Situação da Execução"].value_counts().to_string())

    # -----------------------------------------------------------------
    # 4. Salvar tabelas tratadas, prontas para a fase 4
    # -----------------------------------------------------------------
    empenho.to_csv(BASE_DIR / "mes_empenho_tratado.csv", index=False, sep=";", encoding="utf-8")
    liquidacao_empenhos.to_csv(BASE_DIR / "mes_liquidacao_empenhos_tratado.csv", index=False, sep=";", encoding="utf-8")
    pagamento_empenhos.to_csv(BASE_DIR / "mes_pagamento_empenhos_tratado.csv", index=False, sep=";", encoding="utf-8")
    execucao.to_csv(BASE_DIR / "execucao_tratada_mes.csv", index=False, sep=";", encoding="utf-8")

    print("\n" + "=" * 80)
    print("Tabelas tratadas salvas:")
    print(f"  {BASE_DIR / 'mes_empenho_tratado.csv'}")
    print(f"  {BASE_DIR / 'mes_liquidacao_empenhos_tratado.csv'}")
    print(f"  {BASE_DIR / 'mes_pagamento_empenhos_tratado.csv'}")
    print(f"  {BASE_DIR / 'execucao_tratada_mes.csv'}  <- base final para o dashboard (fase 4)")
    print("=" * 80)


if __name__ == "__main__":
    main()