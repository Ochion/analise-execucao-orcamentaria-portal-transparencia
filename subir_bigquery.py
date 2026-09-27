"""
Fase 4 - Sobe a base tratada (execucao_tratada_mes.csv) para o BigQuery,
com colunas renomeadas para nomes seguros (sem espaco/parenteses/simbolo/acento),
pronta pra conectar no Looker Studio.
"""

import pandas as pd
from pathlib import Path
from google.cloud import bigquery

# Ajuste para o seu projeto GCP (pode reaproveitar o mesmo do projeto de Londres)
PROJECT_ID = "london-crime-analysis-499415"
DATASET_ID = "gastos_publicos_agosto_2026"
TABLE_ID = "execucao_orcamentaria"

BASE_DIR = Path(r"C:\Users\manoc\.vscode\Projeto EBAC\dados_agosto_completo")
ARQUIVO_CSV = BASE_DIR / "execucao_tratada_mes.csv"

# Nomes de coluna seguros para o BigQuery: sem espaco, parenteses, simbolo ou acento
RENOMEAR_COLUNAS = {
    "Código Empenho": "codigo_empenho",
    "Data Emissão": "data_emissao",
    "Órgão Superior": "orgao_superior",
    "Órgão": "orgao",
    "Favorecido": "favorecido",
    "Categoria de Despesa": "categoria_despesa",
    "Elemento de Despesa": "elemento_despesa",
    "Função": "funcao",
    "Valor Original do Empenho": "valor_original_empenho",
    "Valor Liquidado (R$)": "valor_liquidado",
    "Valor Pago (R$)": "valor_pago",
    "% Liquidado": "percentual_liquidado",
    "% Pago": "percentual_pago",
    "Estorno ou Cancelamento": "estorno_cancelamento",
    "Situação da Execução": "situacao_execucao",
}


def main():
    client = bigquery.Client(project=PROJECT_ID)

    dataset_ref = bigquery.DatasetReference(PROJECT_ID, DATASET_ID)
    try:
        client.get_dataset(dataset_ref)
        print(f"Dataset '{DATASET_ID}' ja existe.")
    except Exception:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"
        client.create_dataset(dataset)
        print(f"Dataset '{DATASET_ID}' criado.")

    print(f"Lendo {ARQUIVO_CSV.name} ...")
    df = pd.read_csv(ARQUIVO_CSV, sep=";", encoding="utf-8", low_memory=False)
    df = df.rename(columns=RENOMEAR_COLUNAS)
    df["data_emissao"] = pd.to_datetime(df["data_emissao"]).dt.date

    job_config = bigquery.LoadJobConfig(write_disposition="WRITE_TRUNCATE")

    table_ref = f"{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}"

    print(f"Enviando para {table_ref} ...")
    job = client.load_table_from_dataframe(df, table_ref, job_config=job_config)
    job.result()  # espera o job terminar

    tabela = client.get_table(table_ref)
    print(f"\nPronto! Tabela criada: {table_ref}")
    print(f"Linhas: {tabela.num_rows} | Colunas: {len(tabela.schema)}")
    print("\nSchema detectado:")
    for campo in tabela.schema:
        print(f"  - {campo.name}: {campo.field_type}")


if __name__ == "__main__":
    main()