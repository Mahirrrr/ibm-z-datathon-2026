"""Train the cohort model on verified-damage households: who ends up denied for a fixable reason?

Uses IBM Snap ML when installed (LinuxONE), scikit-learn otherwise. Scores the full
verified-damage population afterwards and times it (records/sec).
"""

import json
import platform
import time

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import average_precision_score, roc_auc_score

from pipeline.config import COHORT, METRICS, MODEL_PATH, MODELS_DIR, SCORES
from pipeline.features import (
    FEATURES,
    build_matrix,
    categorical_mask,
    category_maps,
    disaster_split,
)

LOAD_COLUMNS = [
    "id",
    "disasterNumber",
    "declarationDate",
    "rpfvl",
    "ppfvl",
    "second_look",
    "verified_damage",
] + [f for f in FEATURES if f not in ("rpfvl", "ppfvl", "declarationYear")]


def make_model():
    """Snap ML boosting if available (s390x / Telum path), else scikit-learn."""
    try:
        from snapml import BoostingMachineClassifier

        return "snapml", BoostingMachineClassifier(num_round=300, max_depth=6, n_jobs=-1)
    except ImportError:
        return "sklearn", HistGradientBoostingClassifier(
            max_iter=300,
            learning_rate=0.1,
            categorical_features=categorical_mask(),
            class_weight="balanced",
            random_state=7,
        )


def precision_at_k(y_true, scores, k):
    top = np.argsort(-scores)[:k]
    return float(y_true[top].mean())


def predict_proba(model, X):
    return model.predict_proba(X)[:, 1]


def main():
    df = pd.read_parquet(COHORT, columns=LOAD_COLUMNS)
    df = df[df["verified_damage"]].reset_index(drop=True)
    maps = category_maps(df)
    X = build_matrix(df, maps)
    y = df["second_look"].to_numpy(dtype=np.int8)

    train_idx, test_idx = disaster_split(df)
    backend, model = make_model()
    print(f"backend={backend} train={len(train_idx):,} test={len(test_idx):,} pos_rate={y.mean():.4f}")

    start = time.perf_counter()
    model.fit(X[train_idx], y[train_idx])
    fit_seconds = time.perf_counter() - start

    test_scores = predict_proba(model, X[test_idx])
    y_test = y[test_idx]
    metrics = {
        "backend": backend,
        "machine": platform.machine(),
        "population": "households with inspector-verified damage",
        "rows_train": int(len(train_idx)),
        "rows_test": int(len(test_idx)),
        "disasters_test": int(df.loc[test_idx, "disasterNumber"].nunique()),
        "positive_rate": float(y.mean()),
        "roc_auc": float(roc_auc_score(y_test, test_scores)),
        "average_precision": float(average_precision_score(y_test, test_scores)),
        "precision_at_1000": precision_at_k(y_test, test_scores, 1000),
        "precision_at_10000": precision_at_k(y_test, test_scores, 10000),
        "fit_seconds": round(fit_seconds, 1),
    }

    rng = np.random.default_rng(7)
    sample = rng.choice(test_idx, size=min(200_000, len(test_idx)), replace=False)
    importance = permutation_importance(
        model, X[sample], y[sample], scoring="average_precision", n_repeats=3, random_state=7
    )
    metrics["feature_importance"] = sorted(
        (
            {"feature": name, "importance": float(mean)}
            for name, mean in zip(FEATURES, importance.importances_mean)
        ),
        key=lambda item: -item["importance"],
    )

    start = time.perf_counter()
    all_scores = predict_proba(model, X)
    score_seconds = time.perf_counter() - start
    metrics["score_rows"] = int(len(X))
    metrics["score_seconds"] = round(score_seconds, 2)
    metrics["records_per_second"] = round(len(X) / score_seconds)

    MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump({"model": model, "maps": maps, "features": FEATURES, "backend": backend}, MODEL_PATH)
    pd.DataFrame({"id": df["id"], "risk_score": all_scores.astype("float32")}).to_parquet(SCORES, index=False)
    METRICS.write_text(json.dumps(metrics, indent=2))

    summary = {k: v for k, v in metrics.items() if k != "feature_importance"}
    print(json.dumps(summary, indent=2))
    print("top features:", [f["feature"] for f in metrics["feature_importance"][:8]])


if __name__ == "__main__":
    main()
