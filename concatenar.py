"""
Fase 1 (mes completo) - Concatenar os arquivos diarios de Agosto/2026
Le todos os arquivos de cada tipo (Empenho, Liquidacao, Pagamento, pontes)
dentro de BASE_DIR e concatena em um unico DataFrame por tipo.
"""

import pandas as pd
from pathlib import Path

# Pasta onde TODOS os CSVs de TODOS os dias de agosto foram extraidos (mesmo nivel)
BASE_DIR = Path(r"C:\Users\manoc\.vscode\Projeto EBAC\dados_agosto_completo")

# Padroes de nome de arquivo (o "*" cobre o prefixo AAAAMMDD, que muda por dia)
PADROES = {
    "empenho": "*_Despesas_Empenho.csv",
    "liquidacao": "*_Despesas_Liquidacao.csv",
    "pagamento": "*_Despesas_Pagamento.csv",
    "liquidacao_empenhos": "*_Despesas_Liquidacao_EmpenhosImpactados.csv",
    "pagamento_empenhos": "*_Despesas_Pagamento_EmpenhosImpactados.csv",
}


def carregar_csv(caminho: Path) -> pd.DataFrame:
    return pd.read_csv(caminho, sep=";", encoding="latin1", decimal=",", low_memory=False)


def concatenar_tipo(nome: str, padrao: str) -> pd.DataFrame:
    arquivos = sorted(BASE_DIR.glob(padrao))
    print(f"[{nome}] {len(arquivos)} arquivos encontrados")
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo encontrado para o padrao: {padrao}")

    partes = []
    for arquivo in arquivos:
        df = carregar_csv(arquivo)
        # Guarda de qual arquivo/dia cada linha veio, util pra conferencia depois
        df["Arquivo Origem"] = arquivo.name
        partes.append(df)

    return pd.concat(partes, ignore_index=True)


def main():
    tabelas = {}
    for nome, padrao in PADROES.items():
        tabelas[nome] = concatenar_tipo(nome, padrao)

    print("\n" + "=" * 80)
    print("RESUMO APOS CONCATENACAO (mes completo)")
    print("=" * 80)
    for nome, df in tabelas.items():
        n_dias = df["Arquivo Origem"].nunique()
        print(f"{nome}: {df.shape[0]} linhas x {df.shape[1]} colunas  "
              f"(vindas de {n_dias} arquivos/dias)")

    # Checagem simples de duplicatas por chave (nao deveria haver, mas confirma)
    if "Código Empenho" in tabelas["empenho"].columns:
        duplicados = tabelas["empenho"]["Código Empenho"].duplicated().sum()
        print(f"\nEmpenhos com 'Código Empenho' duplicado entre os dias: {duplicados}")

    # Salva as bases consolidadas do mes pra usar nas proximas fases
    for nome, df in tabelas.items():
        destino = BASE_DIR / f"mes_{nome}.csv"
        df.to_csv(destino, index=False, sep=";", encoding="utf-8")
        print(f"Salvo: {destino}")


if __name__ == "__main__":
    main()