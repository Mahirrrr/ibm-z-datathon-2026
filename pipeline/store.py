"""Load the pipeline outputs into one SQLite file the API and dashboard read from."""

import json
import sqlite3

import pandas as pd

from pipeline import frames
from pipeline.codebook import INELIGIBLE_REASONS, TIER_LABELS
from pipeline.config import ADJUSTED_ODDS, BENCHMARK, CALLBACKS, COHORT, DB_PATH, FAIRNESS, METRICS, SCORES


def disaster_summary():
    cols = ["disasterNumber", "declarationDate", "damagedStateAbbreviation", "incidentTypeCode",
            "verified_damage", "denied", "second_look", "verified_loss", "tier"]
    df = frames.read(COHORT, columns=cols)
    df["denied_verified"] = df["verified_damage"] & df["denied"]
    df["cohort_loss"] = df["verified_loss"].where(df["second_look"], 0.0)
    for tier in TIER_LABELS:
        df[f"tier_{tier}"] = df["tier"] == tier
    grouped = df.groupby("disasterNumber")
    summary = grouped.agg(
        declaration_date=("declarationDate", "min"),
        incident_type=("incidentTypeCode", lambda s: s.mode().iat[0] if not s.mode().empty else None),
        applications=("second_look", "size"),
        verified_damage=("verified_damage", "sum"),
        denied_verified=("denied_verified", "sum"),
        cohort=("second_look", "sum"),
        cohort_loss=("cohort_loss", "sum"),
        **{f"tier_{t}": (f"tier_{t}", "sum") for t in TIER_LABELS},
    )
    states = grouped["damagedStateAbbreviation"].agg(lambda s: ",".join(sorted(s.dropna().unique())))
    summary["states"] = states
    summary["declaration_date"] = summary["declaration_date"].astype(str)
    return summary.reset_index()


def main():
    callbacks = frames.read(CALLBACKS).merge(frames.read(SCORES), on="id", how="left")
    callbacks["declarationDate"] = callbacks["declarationDate"].astype(str)
    metrics = json.loads(METRICS.read_text())
    if BENCHMARK.exists():
        metrics["inference_benchmark"] = json.loads(BENCHMARK.read_text())
    importance = pd.DataFrame(metrics.pop("feature_importance"))
    codes = pd.DataFrame(
        [{"code": k, "label": v} for k, v in INELIGIBLE_REASONS.items()]
    )

    DB_PATH.unlink(missing_ok=True)
    with sqlite3.connect(DB_PATH) as con:
        disaster_summary().to_sql("disasters", con, index=False)
        callbacks.to_sql("callbacks", con, index=False)
        frames.read(FAIRNESS).to_sql("fairness", con, index=False)
        frames.read(ADJUSTED_ODDS).to_sql("adjusted_odds", con, index=False)
        importance.to_sql("feature_importance", con, index=False)
        pd.DataFrame([{"key": k, "value": json.dumps(v)} for k, v in metrics.items()]).to_sql(
            "model_metrics", con, index=False
        )
        codes.to_sql("reason_codes", con, index=False)
        con.execute("CREATE INDEX idx_callbacks_disaster ON callbacks(disasterNumber, rank_in_disaster)")
    print(f"wrote {DB_PATH} ({DB_PATH.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
