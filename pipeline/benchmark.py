"""Time IBM Snap ML's inference engines on every verified-damage household.

Runs as its own step after training, so a crash inside Snap ML's native code can never
lose the pipeline outputs. Engines:
  cpu_default     plain predict_proba
  compress_trees  Snap ML's cache-friendly compressed trees on the CPU
  zdnn_tensors    tree ensemble as tensors on the Telum on-chip AI accelerator (NNPA)

Rankings always use the training step's scores; max_abs_diff_vs_cpu shows each engine
returns the same scores. A Snap ML model can be optimized only once (a second
optimize_trees call aborts), so each engine gets a freshly loaded copy.
"""

import json
import platform
import time

import joblib
import numpy as np

from pipeline import frames
from pipeline.config import BENCHMARK, COHORT, MODEL_PATH
from pipeline.features import build_matrix
from pipeline.train import LOAD_COLUMNS, model_matrix, predict_proba

COMPRESS_SAMPLE = 10_000  # rows Snap ML uses to plan node clustering for compress_trees


def timed_scores(model, X):
    start = time.perf_counter()
    scores = predict_proba(model, X)
    return scores, time.perf_counter() - start


def main():
    bundle = joblib.load(MODEL_PATH)
    if bundle["backend"] != "snapml":
        BENCHMARK.unlink(missing_ok=True)
        print(f"backend is {bundle['backend']}; Snap ML engine benchmark skipped")
        return

    df = frames.read(COHORT, columns=LOAD_COLUMNS, where="verified_damage")
    X = np.ascontiguousarray(model_matrix(build_matrix(df, bundle["maps"]), "snapml"))

    cpu_scores, cpu_seconds = timed_scores(bundle["model"], X)
    engines = {"cpu_default": {"seconds": round(cpu_seconds, 2), "records_per_second": round(len(X) / cpu_seconds)}}
    for tree_format in ("compress_trees", "zdnn_tensors"):
        model = joblib.load(MODEL_PATH)["model"]
        sample = {"X": X[:COMPRESS_SAMPLE]} if tree_format == "compress_trees" else {}
        model.optimize_trees(tree_format=tree_format, **sample)
        scores, seconds = timed_scores(model, X)
        engines[tree_format] = {
            "engine": model.booster_.optimized_tree_format_,
            "seconds": round(seconds, 2),
            "records_per_second": round(len(X) / seconds),
            "max_abs_diff_vs_cpu": float(np.max(np.abs(scores - cpu_scores))),
        }

    result = {"machine": platform.machine(), "rows": int(len(X)), "engines": engines}
    BENCHMARK.write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
