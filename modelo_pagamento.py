"""
Modelagem: um empenho emitido em agosto/2026 será pago no mês?

Alvo: pago = valor_pago > 0
Features (só informação conhecida na emissão, para evitar vazamento):
  órgão superior, categoria de despesa, elemento de despesa, função,
  valor original (log), dia do mês e dia da semana da emissão.
NÃO usamos valor_liquidado, percentual_* nem situacao_execucao (vazariam o alvo).

Uso: python modelo_pagamento.py
"""
import json
import re
import unicodedata
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (ConfusionMatrixDisplay, RocCurveDisplay,
                             accuracy_score, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# ----------------------------- CONFIG ---------------------------------
CSV_PATH = "execucao_tratada_mes.csv"
SEP = ";"
OUT_DIR = Path("saidas_modelo")
SEED = 42

COL_DATA = "data_emissao"
COL_VALOR = "valor_original_do_empenho"
COL_PAGO = "valor_pago_r"
COLS_CAT = ["orgao_superior", "categoria_de_despesa", "elemento_de_despesa", "funcao"]
# -----------------------------------------------------------------------

OUT_DIR.mkdir(exist_ok=True)


def snake(txt: str) -> str:
    txt = unicodedata.normalize("NFKD", str(txt)).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", txt.lower()).strip("_")


# 1. Carga e preparação ---------------------------------------------------
df = pd.read_csv(CSV_PATH, sep=SEP, low_memory=False)
df.columns = [snake(c) for c in df.columns]

necessarias = [COL_DATA, COL_VALOR, COL_PAGO] + COLS_CAT
faltando = [c for c in necessarias if c not in df.columns]
if faltando:
    raise SystemExit(
        f"Colunas não encontradas: {faltando}\n"
        f"Colunas disponíveis: {list(df.columns)}\n"
        "Ajuste os nomes na seção CONFIG."
    )

df[COL_VALOR] = pd.to_numeric(df[COL_VALOR], errors="coerce")
df[COL_PAGO] = pd.to_numeric(df[COL_PAGO], errors="coerce").fillna(0)
df[COL_DATA] = pd.to_datetime(df[COL_DATA], errors="coerce")

# empenhos novos com valor positivo (exclui estornos/cancelamentos)
n0 = len(df)
df = df[df[COL_VALOR] > 0].copy()
print(f"Linhas: {n0} -> {len(df)} após remover valores <= 0 (estornos/cancelamentos)")

df["pago"] = (df[COL_PAGO] > 0).astype(int)
df["log_valor"] = np.log1p(df[COL_VALOR])
df["dia_emissao"] = df[COL_DATA].dt.day.fillna(df[COL_DATA].dt.day.median())
df["dia_semana"] = df[COL_DATA].dt.dayofweek.fillna(0)
for c in COLS_CAT:
    df[c] = df[c].fillna("NA").astype(str)

COLS_NUM = ["log_valor", "dia_emissao", "dia_semana"]
X = df[COLS_NUM + COLS_CAT]
y = df["pago"]
print(f"Taxa de empenhos pagos no mês: {y.mean():.2%}")

X_tr, X_te, y_tr, y_te = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=SEED
)
print(f"Treino: {len(X_tr)} | Teste: {len(X_te)}")

# 2. Modelos --------------------------------------------------------------
pre = ColumnTransformer([
    ("num", StandardScaler(), COLS_NUM),
    ("cat", OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=100), COLS_CAT),
])

modelos = {
    "Regressão Logística": LogisticRegression(max_iter=1000, class_weight="balanced"),
    "Random Forest": RandomForestClassifier(
        n_estimators=150, max_depth=14, min_samples_leaf=20,
        class_weight="balanced", n_jobs=-1, random_state=SEED),
}
pipes = {nome: Pipeline([("pre", pre), ("clf", m)]) for nome, m in modelos.items()}

print("\nValidação cruzada (ROC-AUC, 3 folds) — pode levar alguns minutos...")
cv = {}
for nome, pipe in pipes.items():
    scores = cross_val_score(pipe, X_tr, y_tr, cv=3, scoring="roc_auc")
    cv[nome] = float(scores.mean())
    print(f"  {nome}: {scores.mean():.4f} (+/- {scores.std():.4f})")

melhor = max(cv, key=cv.get)
print(f"\nMelhor modelo na validação: {melhor}")

# 3. Avaliação no teste ---------------------------------------------------
pipe = pipes[melhor].fit(X_tr, y_tr)
proba = pipe.predict_proba(X_te)[:, 1]
pred = (proba >= 0.5).astype(int)

metricas = {
    "modelo": melhor,
    "cv_roc_auc": cv,
    "baseline_acuracia_classe_majoritaria": float(max(y_te.mean(), 1 - y_te.mean())),
    "acuracia": float(accuracy_score(y_te, pred)),
    "roc_auc": float(roc_auc_score(y_te, proba)),
    "precisao": float(precision_score(y_te, pred)),
    "recall": float(recall_score(y_te, pred)),
    "f1": float(f1_score(y_te, pred)),
}
print("\nResultado no teste:")
for k, v in metricas.items():
    print(f"  {k}: {v}")
(OUT_DIR / "metricas.json").write_text(json.dumps(metricas, indent=2, ensure_ascii=False))

# 4. Gráficos -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(5, 5))
RocCurveDisplay.from_predictions(y_te, proba, ax=ax, name=melhor)
ax.plot([0, 1], [0, 1], "--", color="gray")
ax.set_title("Curva ROC — empenho será pago no mês?")
fig.tight_layout()
fig.savefig(OUT_DIR / "roc.png", dpi=150)
plt.close(fig)

fig, ax = plt.subplots(figsize=(5, 5))
ConfusionMatrixDisplay.from_predictions(
    y_te, pred, ax=ax, display_labels=["Não pago", "Pago"], cmap="Blues")
ax.set_title("Matriz de confusão (teste)")
fig.tight_layout()
fig.savefig(OUT_DIR / "matriz_confusao.png", dpi=150)
plt.close(fig)

# 5. Importância das variáveis -------------------------------------------
nomes = pipe.named_steps["pre"].get_feature_names_out()
clf = pipe.named_steps["clf"]
if hasattr(clf, "coef_"):
    valores = clf.coef_[0]          # sinal indica direção do efeito
    rotulo = "Coeficiente (log-odds)"
else:
    valores = clf.feature_importances_
    rotulo = "Importância"
imp = pd.DataFrame({"variavel": nomes, "valor": valores})
imp["abs"] = imp["valor"].abs()
imp = imp.sort_values("abs", ascending=False).head(15).drop(columns="abs")
imp.to_csv(OUT_DIR / "importancia_variaveis.csv", index=False)

fig, ax = plt.subplots(figsize=(8, 6))
imp.iloc[::-1].plot.barh(x="variavel", y="valor", ax=ax, legend=False, color="#4f1078")
ax.set_xlabel(rotulo)
ax.set_ylabel("")
ax.set_title("Top 15 variáveis do modelo")
fig.tight_layout()
fig.savefig(OUT_DIR / "importancia_variaveis.png", dpi=150)
plt.close(fig)

print(f"\nTop variáveis:\n{imp.to_string(index=False)}")
print(f"\nArquivos salvos em: {OUT_DIR.resolve()}")