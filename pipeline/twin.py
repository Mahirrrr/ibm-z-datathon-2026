"""Keras/TensorFlow twin of the cohort model, to measure the Telum on-chip AI accelerator (NNPA).

Snap ML's tree engines do not reach the NNPA the way TensorFlow does: IBM's zDNN plugin for
TensorFlow sends MatMul, Dense, ReLU and Softmax ops to it. So we train a small MLP on the same
features and the same disaster split, then time inference with and without the plugin.

Two steps, because TensorFlow and the zDNN plugin live in IBM's jupyter-lab-ml image while the
data tools live in our conda env:

    python -m pipeline.twin export                    # conda env: encode features to .npy files
    NNPA_DEVICES=0 python -m pipeline.twin train      # TF container, CPU
    NNPA_DEVICES=0 python -m pipeline.twin bench      # TF container, plain CPU inference
    python -m pipeline.twin bench                     # TF container, zDNN plugin on the NNPA
    python -m pipeline.twin combine                   # writes data/processed/twin_benchmark.json
"""

import argparse
import json
import os
import platform
import time

import numpy as np

from pipeline.config import BOOLEAN_FEATURES, CATEGORICAL_FEATURES, PROCESSED_DIR

TWIN_DIR = PROCESSED_DIR / "twin"
TWIN_BENCHMARK = PROCESSED_DIR / "twin_benchmark.json"
TRAIN_ROWS = 1_000_000
SEED = 7


def one_hot(X, maps, features):
    """Categorical codes become one-hot columns (NaN -> all zero); booleans NaN -> 0; money -> log1p."""
    cols = []
    for j, name in enumerate(features):
        x = X[:, j]
        if name in CATEGORICAL_FEATURES:
            k = len(maps[name])
            block = np.zeros((len(x), k), dtype=np.float32)
            ok = ~np.isnan(x)
            block[np.flatnonzero(ok), x[ok].astype(np.int64)] = 1.0
            cols.append(block)
        elif name in BOOLEAN_FEATURES:
            cols.append(np.nan_to_num(x, nan=0.0)[:, None])
        elif name == "declarationYear":
            cols.append(((np.nan_to_num(x, nan=2010.0) - 2010.0) / 10.0)[:, None])
        else:
            cols.append(np.log1p(np.clip(np.nan_to_num(x, nan=0.0), 0, None))[:, None])
    return np.ascontiguousarray(np.hstack(cols), dtype=np.float32)


def export():
    from pipeline import frames
    from pipeline.config import COHORT
    from pipeline.features import FEATURES, build_matrix, category_maps, disaster_split
    from pipeline.train import LOAD_COLUMNS

    df = frames.read(COHORT, columns=LOAD_COLUMNS, where="verified_damage")
    maps = category_maps(df)
    X = build_matrix(df, maps)
    y = df["second_look"].to_numpy(dtype=np.float32)
    train_idx, test_idx = disaster_split(df)  # same disaster split as the Snap ML model
    rng = np.random.default_rng(SEED)
    train_idx = np.sort(rng.choice(train_idx, size=min(TRAIN_ROWS, len(train_idx)), replace=False))

    # One-hot only the rows we use: all 8.9M rows one-hot would not fit in 8 GB.
    TWIN_DIR.mkdir(parents=True, exist_ok=True)
    for name, idx in (("train", train_idx), ("test", test_idx)):
        np.save(TWIN_DIR / f"X_{name}.npy", one_hot(X[idx], maps, FEATURES))
        np.save(TWIN_DIR / f"y_{name}.npy", y[idx])
    print(f"exported train {len(train_idx):,} and test {len(test_idx):,} rows "
          f"({np.load(TWIN_DIR / 'X_test.npy', mmap_mode='r').shape[1]} inputs)")


def roc_auc(y, s):
    """Rank-based ROC AUC (Mann-Whitney), so the container needs no scikit-learn."""
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s))
    ranks[order] = np.arange(1, len(s) + 1)
    pos = y == 1
    n_pos, n_neg = pos.sum(), (~pos).sum()
    return float((ranks[pos].sum() - n_pos * (n_pos + 1) / 2) / (n_pos * n_neg))


def precision_at_k(y, s, k):
    return float(y[np.argsort(-s)[:k]].mean())


def device():
    """IBM's plugin targets the NNPA unless NNPA_DEVICES is 0/false (then plain TensorFlow CPU)."""
    return "cpu" if os.environ.get("NNPA_DEVICES", "").lower() in ("0", "false") else "nnpa"


def load(name):
    return np.load(TWIN_DIR / f"X_{name}.npy"), np.load(TWIN_DIR / f"y_{name}.npy")


def train():
    """Train on the CPU (IBM recommends NNPA_DEVICES=0 for training); the NNPA is for inference."""
    import tensorflow as tf

    X, y = load("train")
    tf.keras.utils.set_random_seed(SEED)
    model = tf.keras.Sequential([
        tf.keras.Input(shape=(X.shape[1],)),
        tf.keras.layers.Dense(64, activation="relu"),
        tf.keras.layers.Dense(32, activation="relu"),
        tf.keras.layers.Dense(1, activation="sigmoid"),
    ])
    model.compile(optimizer=tf.keras.optimizers.Adam(1e-3), loss="binary_crossentropy")
    pos_rate = float(y.mean())
    start = time.perf_counter()
    model.fit(X, y, epochs=3, batch_size=2048, verbose=2, class_weight={0: 1.0, 1: (1 - pos_rate) / pos_rate})
    fit_seconds = time.perf_counter() - start
    model.save(TWIN_DIR / "twin.keras")
    (TWIN_DIR / "train.json").write_text(json.dumps({
        "framework": f"TensorFlow {tf.__version__} / Keras",
        "layers": "Dense 64 ReLU, Dense 32 ReLU, Dense 1 sigmoid",
        "inputs": int(X.shape[1]), "rows_train": int(len(X)), "fit_seconds": round(fit_seconds, 1),
    }))
    print(f"trained in {fit_seconds:.1f}s")


def bench(batch_size, repeats):
    """Score the held-out disasters with the saved model on this process's device; keep the best of N runs."""
    import tensorflow as tf

    X_test, y = load("test")
    model = tf.keras.models.load_model(TWIN_DIR / "twin.keras")
    scores = model.predict(X_test, batch_size=batch_size, verbose=0).ravel()  # also warms up
    timings = []
    for _ in range(repeats):
        start = time.perf_counter()
        model.predict(X_test, batch_size=batch_size, verbose=0)
        timings.append(time.perf_counter() - start)
    best = min(timings)
    dev = device()
    np.save(TWIN_DIR / f"scores_{dev}.npy", scores)
    result = {
        "device": dev, "machine": platform.machine(), "rows_scored": int(len(X_test)),
        "roc_auc": roc_auc(y, scores), "precision_at_1000": precision_at_k(y, scores, 1000),
        "batch_size": batch_size, "inference_seconds": round(best, 2),
        "inference_seconds_all": [round(t, 2) for t in timings], "records_per_second": round(len(X_test) / best),
    }
    (TWIN_DIR / f"bench_{dev}.json").write_text(json.dumps(result))
    print(json.dumps(result, indent=2))


def combine():
    """Merge the train and both bench runs; the score difference shows the NNPA path really ran."""
    result = json.loads((TWIN_DIR / "train.json").read_text())
    result["runs"] = {d: json.loads((TWIN_DIR / f"bench_{d}.json").read_text()) for d in ("cpu", "nnpa")}
    cpu, nnpa = (np.load(TWIN_DIR / f"scores_{d}.npy") for d in ("cpu", "nnpa"))
    result["max_abs_diff_nnpa_vs_cpu"] = float(np.max(np.abs(cpu - nnpa)))
    result["speedup_nnpa_vs_cpu"] = round(result["runs"]["nnpa"]["records_per_second"]
                                          / result["runs"]["cpu"]["records_per_second"], 2)
    TWIN_BENCHMARK.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("step", choices=["export", "train", "bench", "combine"])
    ap.add_argument("--batch-size", type=int, default=8192)
    ap.add_argument("--repeats", type=int, default=3)
    args = ap.parse_args()
    if args.step == "bench":
        bench(args.batch_size, args.repeats)
    else:
        {"export": export, "train": train, "combine": combine}[args.step]()


if __name__ == "__main__":
    main()
