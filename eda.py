"""
Fase 2 - Analise Exploratoria (EDA)
5 analises sobre a base consolidada de execucao orcamentaria (ago/2026):
  1. Distribuicao do valor dos empenhos
  2. Outliers (metodo IQR + maiores empenhos individuais)
  3. Ranking por orgao (media/mediana/soma)
  4. Correlacao/dispersao: valor empenhado x valor pago
  5. Serie temporal: despesas por dia do mes

Cada analise imprime um resumo no terminal e salva um grafico em PNG
na pasta GRAFICOS_DIR, pra usar depois no relatorio/apresentacao.

Requisitos: pip install pandas matplotlib
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

BASE_DIR = Path(r"C:\Users\manoc\.vscode\Projeto EBAC\dados_agosto_completo")
GRAFICOS_DIR = BASE_DIR / "graficos_eda"
GRAFICOS_DIR.mkdir(exist_ok=True)

pd.options.display.float_format = "{:,.2f}".format


def carregar_dados() -> pd.DataFrame:
    # Agora le a base TRATADA (fase 3), nao mais a consolidada bruta
    df = pd.read_csv(BASE_DIR / "execucao_tratada_mes.csv", sep=";", encoding="utf-8", low_memory=False)
    # O tratamento (fase 3) ja salvou a data em formato ISO (aaaa-mm-dd),
    # entao o parse aqui muda de "%d/%m/%Y" para "%Y-%m-%d"
    df["Data Emissão"] = pd.to_datetime(df["Data Emissão"], format="%Y-%m-%d")
    return df


def salvar_grafico(fig, caminho: Path) -> None:
    """
    Salva o grafico sem derrubar o script se o arquivo estiver bloqueado
    (ex: aberto no visualizador de fotos, no preview do Explorer, etc.).
    Nesse caso, avisa no terminal e segue para a proxima analise.
    """
    try:
        fig.savefig(caminho, dpi=150)
        print(f"Grafico salvo: {caminho}")
    except OSError as erro:
        print(f"AVISO: nao consegui salvar '{caminho.name}' ({erro}).")
        print("       Provavelmente o arquivo esta aberto em outro programa. Feche-o e rode de novo.")
    finally:
        plt.close(fig)


# ---------------------------------------------------------------------------
# 1. Distribuicao do valor dos empenhos
# ---------------------------------------------------------------------------
def analise_distribuicao(df: pd.DataFrame) -> None:
    print("\n" + "=" * 80)
    print("1. DISTRIBUICAO - Valor Original do Empenho")
    print("=" * 80)

    valores = df["Valor Original do Empenho"]
    print(valores.describe())

    n_negativos_zero = (valores <= 0).sum()
    print(f"\nEmpenhos com valor <= 0 (estornos/cancelamentos): {n_negativos_zero}")

    # Para o histograma, usa apenas valores positivos em escala log
    # (a distribuicao de gastos publicos e extremamente assimetrica)
    positivos = valores[valores > 0]

    # bins em escala log: com bins lineares (padrao do hist), quase todo o
    # dado cai num unico bin gigante quando o eixo depois vira log na exibicao
    bins_log = np.logspace(np.log10(positivos.min()), np.log10(positivos.max()), 60)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.hist(positivos, bins=bins_log, color="#2E6F95", edgecolor="white")
    ax.set_xscale("log")
    ax.set_xlabel("Valor do Empenho (R$, escala log)")
    ax.set_ylabel("Quantidade de empenhos")
    ax.set_title("Distribuição do valor dos empenhos - Agosto/2026")
    fig.tight_layout()
    salvar_grafico(fig, GRAFICOS_DIR / "1_distribuicao_valor_empenho.png")


# ---------------------------------------------------------------------------
# 2. Outliers
# ---------------------------------------------------------------------------
def analise_outliers(df: pd.DataFrame) -> None:
    print("\n" + "=" * 80)
    print("2. OUTLIERS - metodo IQR")
    print("=" * 80)

    valores = df["Valor Original do Empenho"]
    q1, q3 = valores.quantile([0.25, 0.75])
    iqr = q3 - q1
    limite_superior = q3 + 1.5 * iqr

    outliers = df[valores > limite_superior]
    print(f"Q1: R$ {q1:,.2f} | Q3: R$ {q3:,.2f} | IQR: R$ {iqr:,.2f}")
    print(f"Limite superior (Q3 + 1.5*IQR): R$ {limite_superior:,.2f}")
    print(f"Empenhos classificados como outlier: {len(outliers)} de {len(df)} ({len(outliers)/len(df)*100:.2f}%)")

    print("\nTop 10 maiores empenhos individuais:")
    top10 = df.nlargest(10, "Valor Original do Empenho")[
        ["Órgão", "Favorecido", "Elemento de Despesa", "Valor Original do Empenho"]
    ]
    print(top10.to_string(index=False))

    # Os maiores outliers costumam ser rolagem/juros de divida publica, que e
    # uma operacao financeira, nao gasto corrente (saude, educacao etc.) --
    # vale conferir quanto disso pesa no total antes de comparar orgaos
    print("\nValor total por Categoria de Despesa (top 5):")
    por_categoria = (
        df.groupby("Categoria de Despesa")["Valor Original do Empenho"]
        .sum()
        .sort_values(ascending=False)
    )
    print(por_categoria.head(5).to_string())

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.boxplot(valores[valores > 0], vert=True, showfliers=True)
    ax.set_yscale("log")
    ax.set_ylabel("Valor do Empenho (R$, escala log)")
    ax.set_title("Boxplot - Valor dos empenhos (Agosto/2026)")
    fig.tight_layout()
    salvar_grafico(fig, GRAFICOS_DIR / "2_boxplot_outliers.png")


# ---------------------------------------------------------------------------
# 3. Ranking por orgao (soma / media / mediana)
# ---------------------------------------------------------------------------
def analise_ranking_orgao(df: pd.DataFrame) -> pd.DataFrame:
    print("\n" + "=" * 80)
    print("3. RANKING POR ORGAO - soma, media e mediana")
    print("=" * 80)

    ranking = (
        df.groupby("Órgão Superior")["Valor Original do Empenho"]
        .agg(total="sum", media="mean", mediana="median", qtd="count")
        .sort_values("total", ascending=False)
    )
    print(ranking.head(10).to_string())

    top10 = ranking.head(10)
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(top10.index[::-1], top10["total"][::-1], color="#2E6F95")
    ax.set_xlabel("Valor total empenhado (R$)")
    ax.set_title("Top 10 órgãos superiores por valor empenhado - Agosto/2026")
    fig.tight_layout()
    salvar_grafico(fig, GRAFICOS_DIR / "3_ranking_orgaos.png")

    return ranking


# ---------------------------------------------------------------------------
# 4. Correlacao / dispersao: empenhado x pago
# ---------------------------------------------------------------------------
def analise_correlacao(df: pd.DataFrame) -> None:
    print("\n" + "=" * 80)
    print("4. CORRELACAO/DISPERSAO - Valor Empenhado x Valor Pago")
    print("=" * 80)

    # Usa um limiar (1 centavo) em vez de > 0: quando pagamentos e estornos
    # quase se cancelam na soma, sobra um residuo de ponto flutuante
    # (ex: 1e-13) que tecnicamente e > 0 mas nao e um pagamento real
    EPSILON = 0.01
    com_pagamento = df[df["Valor Pago (R$)"] > EPSILON]
    correlacao = com_pagamento["Valor Original do Empenho"].corr(com_pagamento["Valor Pago (R$)"])
    print(f"Empenhos com pagamento > 0: {len(com_pagamento)} de {len(df)}")
    print(f"Correlacao de Pearson (empenhado x pago): {correlacao:.4f}")

    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(
        com_pagamento["Valor Original do Empenho"],
        com_pagamento["Valor Pago (R$)"],
        alpha=0.3, s=10, color="#2E6F95",
    )
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Valor Empenhado (R$, escala log)")
    ax.set_ylabel("Valor Pago (R$, escala log)")
    ax.set_title("Valor empenhado x valor pago (empenhos já pagos)")
    fig.tight_layout()
    salvar_grafico(fig, GRAFICOS_DIR / "4_dispersao_empenhado_pago.png")


# ---------------------------------------------------------------------------
# 5. Serie temporal: despesas por dia do mes
# ---------------------------------------------------------------------------
def analise_serie_temporal(df: pd.DataFrame) -> None:
    print("\n" + "=" * 80)
    print("5. SERIE TEMPORAL - Valor empenhado por dia")
    print("=" * 80)

    por_dia = df.groupby("Data Emissão")["Valor Original do Empenho"].sum().sort_index()
    print(por_dia.to_string())

    fig, ax = plt.subplots(figsize=(11, 5))
    cores = ["#C0392B" if d.weekday() >= 5 else "#2E6F95" for d in por_dia.index]
    ax.bar(por_dia.index, por_dia.values, color=cores, width=0.8)
    ax.set_xlabel("Data")
    ax.set_ylabel("Valor total empenhado (R$)")
    ax.set_title("Valor empenhado por dia - Agosto/2026 (vermelho = fim de semana)")
    fig.autofmt_xdate()
    fig.tight_layout()
    salvar_grafico(fig, GRAFICOS_DIR / "5_serie_temporal_diaria.png")


def main():
    df = carregar_dados()
    print(f"Base carregada: {df.shape[0]} empenhos, {df.shape[1]} colunas")

    analise_distribuicao(df)
    analise_outliers(df)
    analise_ranking_orgao(df)
    analise_correlacao(df)
    analise_serie_temporal(df)

    print("\n" + "=" * 80)
    print(f"Todos os graficos foram salvos em: {GRAFICOS_DIR}")
    print("=" * 80)


if __name__ == "__main__":
    main()