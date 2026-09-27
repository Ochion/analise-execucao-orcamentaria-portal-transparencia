"""
Fase 1 - Selecao dos dados
Carrega e inspeciona as tabelas de despesas publicas (Portal da Transparencia)
para validar os requisitos minimos do projeto:
  - 3+ tabelas cruzaveis
  - 1+ tabela com coluna de data
  - 2+ tabelas com mais de 5 colunas
  - 2+ tabelas com mais de 100 linhas
"""

import pandas as pd
from pathlib import Path

# ---------------------------------------------------------------------------
# 1. AJUSTE ESTE CAMINHO para a pasta onde estao os CSVs baixados
# ---------------------------------------------------------------------------
BASE_DIR = Path(r"C:\Users\manoc\.vscode\Projeto EBAC")

ARQUIVOS = {
    "empenho": "20260831_Despesas_Empenho.csv",
    "liquidacao": "20260831_Despesas_Liquidacao.csv",
    "pagamento": "20260831_Despesas_Pagamento.csv",
    "liquidacao_empenhos": "20260831_Despesas_Liquidacao_EmpenhosImpactados.csv",
    "pagamento_empenhos": "20260831_Despesas_Pagamento_EmpenhosImpactados.csv",
}


def carregar_csv(caminho: Path) -> pd.DataFrame:
    """
    Os CSVs do Portal da Transparencia costumam vir com ';' como separador,
    encoding latin-1 e numeros com virgula decimal. Se der erro de leitura
    ou os textos vierem com caracteres estranhos, ajuste os parametros abaixo.
    """
    return pd.read_csv(
        caminho,
        sep=";",
        encoding="latin1",
        decimal=",",
        low_memory=False,
    )


def inspecionar(nome: str, df: pd.DataFrame) -> None:
    print("=" * 80)
    print(f"TABELA: {nome}")
    print("=" * 80)
    print(f"Linhas x Colunas: {df.shape}")
    print("\nColunas:")
    for col in df.columns:
        print(f"  - {col}")
    print("\nTipos de dados:")
    print(df.dtypes)
    print("\nValores nulos por coluna:")
    print(df.isnull().sum())
    print("\nPrimeiras linhas:")
    print(df.head(3))
    print("\n")


def main():
    tabelas = {}
    for nome, arquivo in ARQUIVOS.items():
        caminho = BASE_DIR / arquivo
        print(f"Carregando {arquivo} ...")
        tabelas[nome] = carregar_csv(caminho)

    for nome, df in tabelas.items():
        inspecionar(nome, df)

    # -----------------------------------------------------------------
    # Checklist automatico dos requisitos minimos da fase 1
    # -----------------------------------------------------------------
    print("=" * 80)
    print("CHECKLIST - REQUISITOS MINIMOS DA FASE 1")
    print("=" * 80)

    n_tabelas = len(tabelas)
    print(f"Numero de tabelas carregadas: {n_tabelas} "
          f"({'OK' if n_tabelas >= 3 else 'FALTA'} - minimo 3 cruzaveis)")

    tabelas_com_data = []
    tabelas_5_colunas = []
    tabelas_100_linhas = []

    for nome, df in tabelas.items():
        colunas_data = [c for c in df.columns if "data" in c.lower()]
        if colunas_data:
            tabelas_com_data.append((nome, colunas_data))
        if df.shape[1] > 5:
            tabelas_5_colunas.append(nome)
        if df.shape[0] > 100:
            tabelas_100_linhas.append(nome)

    print(f"\nTabelas com coluna de data: {[t[0] for t in tabelas_com_data]} "
          f"({'OK' if tabelas_com_data else 'FALTA'})")
    print(f"Tabelas com mais de 5 colunas: {tabelas_5_colunas} "
          f"({'OK' if len(tabelas_5_colunas) >= 2 else 'FALTA'} - minimo 2)")
    print(f"Tabelas com mais de 100 linhas: {tabelas_100_linhas} "
          f"({'OK' if len(tabelas_100_linhas) >= 2 else 'FALTA'} - minimo 2)")


if __name__ == "__main__":
    main()