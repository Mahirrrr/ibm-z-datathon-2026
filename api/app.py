"""Read-only API over secondlook.db, plus the static dashboard.

Run: .venv/bin/uvicorn api.app:app --port 8000
"""

import csv
import io
import json
import os
import sqlite3
from collections import Counter
from pathlib import Path
from statistics import median

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from pipeline.codebook import INCIDENT_NAMES, TIER_LABELS
from pipeline.config import DB_PATH, HABITABILITY_BONUS, TIER_WEIGHTS, VULNERABILITY_BONUS

DASHBOARD_DIR = Path(__file__).resolve().parent.parent / "dashboard"

GROUP_NAMES = {
    "ownRent": "Housing",
    "grossIncome": "Household income",
    "applicantAge": "Applicant age",
    "accessFunctionalNeeds": "Access or functional needs",
}

CATEGORY_LABELS = {
    ("ownRent", "O"): "Owners",
    ("ownRent", "R"): "Renters",
    ("grossIncome", "0"): "$0 reported",
    ("accessFunctionalNeeds", "True"): "Needs support",
    ("accessFunctionalNeeds", "False"): "No reported need",
}

# Display order inside each group; unlisted categories keep table order.
CATEGORY_ORDER = {
    "grossIncome": ["0", "<$15,000", "$15,000-$30,000", "$30,001-$60,000", "$60,001-$120,000",
                    "$120,001-$175,000", ">$175,000"],
    "applicantAge": ["<19", "19-34", "35-49", "50-64", "65+"],
}

CSV_COLUMNS = ["rank_in_disaster", "priority", "tier", "verified_loss", "county", "damagedStateAbbreviation",
               "habitabilityRepairsRequired", "factors", "why_flagged", "risk_score", "id"]


def create_app(db_path=DB_PATH):
    app = FastAPI(title="Second Look API")

    def query(sql, params=()):
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        try:
            return [dict(r) for r in con.execute(sql, params)]
        finally:
            con.close()

    def describe(d):
        d["incident_name"] = INCIDENT_NAMES.get(d["incident_type"], d["incident_type"])
        d["year"] = int(d["declaration_date"][:4])
        return d

    @app.get("/api/summary")
    def summary():
        totals = query(
            "SELECT SUM(applications) records, SUM(verified_damage) verified_damage,"
            " SUM(denied_verified) denied_verified, SUM(cohort) cohort, SUM(cohort_loss) cohort_loss,"
            " SUM(cohort > 0) disasters_with_cohort,"
            + ", ".join(f"SUM(tier_{t}) tier_{t}" for t in TIER_LABELS)
            + " FROM disasters"
        )[0]
        tiers = {t: totals.pop(f"tier_{t}") for t in TIER_LABELS}
        losses = [r["verified_loss"] for r in query("SELECT verified_loss FROM callbacks")]
        needs = query("SELECT COUNT(*) n FROM callbacks WHERE habitabilityRepairsRequired = 1")[0]["n"]
        return {**totals, "tiers": tiers, "median_loss": median(losses) if losses else None,
                "needs_repairs": needs}

    @app.get("/api/fairness")
    def fairness():
        rows = query(
            "SELECT f.*, a.adjusted_odds_ratio FROM fairness f LEFT JOIN adjusted_odds a"
            " ON a.\"group\" = f.\"group\" AND a.category = f.category WHERE f.category != 'Unknown'"
        )
        for r in rows:
            r["group_name"] = GROUP_NAMES.get(r["group"], r["group"])
            r["label"] = CATEGORY_LABELS.get((r["group"], r["category"]), r["category"])
            r["is_reference"] = r["category"] == r["reference"]
            if r["is_reference"]:
                r["adjusted_odds_ratio"] = 1.0

        def order(r):
            wanted = CATEGORY_ORDER.get(r["group"], [])
            pos = wanted.index(r["category"]) if r["category"] in wanted else len(wanted)
            return list(GROUP_NAMES).index(r["group"]) if r["group"] in GROUP_NAMES else 99, pos

        return sorted(rows, key=order)

    @app.get("/api/disasters")
    def disasters(limit: int = Query(20, ge=1, le=1000)):
        rows = query("SELECT * FROM disasters WHERE cohort > 0 ORDER BY cohort DESC LIMIT ?", (limit,))
        return [describe(r) for r in rows]

    @app.get("/api/disasters/{number}")
    def disaster(number: int):
        rows = query("SELECT * FROM disasters WHERE disasterNumber = ?", (number,))
        if not rows:
            raise HTTPException(404, "Disaster not found")
        d = describe(rows[0])
        cb = query("SELECT factors, habitabilityRepairsRequired FROM callbacks WHERE disasterNumber = ?", (number,))
        d["needs_repairs"] = sum(1 for r in cb if r["habitabilityRepairsRequired"] == 1)
        d["factor_counts"] = dict(Counter(f for r in cb for f in (r["factors"] or "").split(", ") if f))
        return d

    def has_notes():
        return bool(query("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'callback_notes'"))

    def callback_rows(number, limit=None, offset=0):
        sql = "SELECT * FROM callbacks WHERE disasterNumber = ? ORDER BY rank_in_disaster"
        params = (number,)
        if limit is not None:
            sql += " LIMIT ? OFFSET ?"
            params += (limit, offset)
        return query(sql, params)

    def attach_notes(rows):
        notes = {}
        if rows and has_notes():
            ids = [r["id"] for r in rows]
            notes = {n["id"]: n for n in query(
                f"SELECT * FROM callback_notes WHERE status = 'ok' AND id IN ({','.join('?' * len(ids))})", ids)}
        for r in rows:
            n = notes.get(r["id"])
            r["note"] = n and {"why_flagged": n["why_flagged"], "callback_script": n["callback_script"],
                               "citations": json.loads(n["citations"]), "model": n["model"]}
        return rows

    @app.get("/api/disasters/{number}/callbacks")
    def callbacks(number: int, limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)):
        return attach_notes(callback_rows(number, limit, offset))

    @app.get("/api/disasters/{number}/callbacks.csv")
    def callbacks_csv(number: int):
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=CSV_COLUMNS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(callback_rows(number))
        return Response(buf.getvalue(), media_type="text/csv",
                        headers={"Content-Disposition": f"attachment; filename=second_look_{number}.csv"})

    @app.get("/api/model")
    def model():
        metrics = {r["key"]: json.loads(r["value"]) for r in query("SELECT * FROM model_metrics")}
        importance = query("SELECT * FROM feature_importance ORDER BY importance DESC")
        policy = {"tier_weights": TIER_WEIGHTS, "tier_labels": TIER_LABELS,
                  "habitability_bonus": HABITABILITY_BONUS, "vulnerability_bonus": VULNERABILITY_BONUS}
        runtime = {"container": os.environ.get("SECOND_LOOK_CONTAINER")}
        return {"metrics": metrics, "feature_importance": importance, "policy": policy, "runtime": runtime,
                "genai": genai_stats()}

    def genai_stats():
        if not has_notes():
            return None
        rows = query("SELECT status, model, seconds, completion_tokens FROM callback_notes")
        if not rows:
            return None
        return {
            "model": rows[0]["model"],
            "notes": sum(r["status"] == "ok" for r in rows),
            "rejected": sum(r["status"] != "ok" for r in rows),
            "median_seconds": median(r["seconds"] for r in rows),
            "median_completion_tokens": median(r["completion_tokens"] for r in rows if r["completion_tokens"] is not None),
        }

    if DASHBOARD_DIR.exists():
        app.mount("/", StaticFiles(directory=DASHBOARD_DIR, html=True), name="dashboard")
    return app


app = create_app()
