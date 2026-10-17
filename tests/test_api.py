import json
import sqlite3

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from api.app import create_app


@pytest.fixture
def client(tmp_path):
    db = tmp_path / "test.db"
    with sqlite3.connect(db) as con:
        pd.DataFrame([
            {"disasterNumber": 1, "declaration_date": "2020-08-28", "incident_type": "H", "applications": 100,
             "verified_damage": 50, "denied_verified": 10, "cohort": 3, "cohort_loss": 3000.0,
             "tier_missing_documents": 2, "tier_lost_contact": 1, "tier_unverified_ownership_or_occupancy": 0,
             "states": "LA"},
            {"disasterNumber": 2, "declaration_date": "2017-09-20", "incident_type": "W", "applications": 40,
             "verified_damage": 20, "denied_verified": 5, "cohort": 1, "cohort_loss": 500.0,
             "tier_missing_documents": 0, "tier_lost_contact": 0, "tier_unverified_ownership_or_occupancy": 1,
             "states": "PR"},
        ]).to_sql("disasters", con, index=False)
        pd.DataFrame([
            {"id": i, "disasterNumber": 1, "tier": t, "verified_loss": loss, "habitabilityRepairsRequired": hab,
             "factors": f, "priority": p, "why_flagged": f"why {i}", "rank_in_disaster": r, "risk_score": 0.5,
             "county": "Cameron (Parish)", "damagedStateAbbreviation": "LA"}
            for i, t, loss, hab, f, p, r in [
                (10, "missing_documents", 2000.0, 1, "renter", 1.5, 1),
                (11, "missing_documents", 600.0, 0, "", 0.6, 2),
                (12, "lost_contact", 400.0, 1, "age 65+, renter", 0.4, 3),
            ]
        ] + [{"id": 20, "disasterNumber": 2, "tier": "unverified_ownership_or_occupancy", "verified_loss": 500.0,
              "habitabilityRepairsRequired": 0, "factors": "", "priority": 0.9, "why_flagged": "why 20",
              "rank_in_disaster": 1, "risk_score": 0.2, "county": "San Juan", "damagedStateAbbreviation": "PR"}]
        ).to_sql("callbacks", con, index=False)
        pd.DataFrame([
            {"group": "ownRent", "category": "O", "cohort": 1, "households": 100, "rate": 0.01, "ci_low": 0.005,
             "ci_high": 0.02, "ratio_vs_reference": 1.0, "reference": "O"},
            {"group": "ownRent", "category": "R", "cohort": 3, "households": 100, "rate": 0.03, "ci_low": 0.02,
             "ci_high": 0.04, "ratio_vs_reference": 3.0, "reference": "O"},
            {"group": "ownRent", "category": "Unknown", "cohort": 1, "households": 2, "rate": 0.5, "ci_low": 0.1,
             "ci_high": 0.9, "ratio_vs_reference": 50.0, "reference": "O"},
        ]).to_sql("fairness", con, index=False)
        pd.DataFrame([
            {"group": "ownRent", "category": "R", "reference": "O", "adjusted_odds_ratio": 2.0},
            {"group": "ownRent", "category": "Unknown", "reference": "O", "adjusted_odds_ratio": 60.0},
        ]).to_sql("adjusted_odds", con, index=False)
        pd.DataFrame([{"feature": "rpfvl", "importance": 0.01}, {"feature": "ownRent", "importance": 0.02}]
                     ).to_sql("feature_importance", con, index=False)
        pd.DataFrame([{"key": "roc_auc", "value": "0.78"}, {"key": "backend", "value": '"sklearn"'}]
                     ).to_sql("model_metrics", con, index=False)
        pd.DataFrame([
            {"id": 10, "status": "ok", "reason": None, "why_flagged": "Granite why", "callback_script": "Granite script",
             "citations": json.dumps([{"ref": "P1", "label": "IAPPG 1.1, Ch. 3 §II.A.4 Occupancy, p. 51"}]),
             "model": "granite", "seconds": 40.0, "prompt_tokens": 700, "completion_tokens": 200},
            {"id": 11, "status": "rejected", "reason": "no citation", "why_flagged": None, "callback_script": None,
             "citations": "[]", "model": "granite", "seconds": 30.0, "prompt_tokens": 700, "completion_tokens": 150},
        ]).to_sql("callback_notes", con, index=False)
    return TestClient(create_app(db))


@pytest.fixture
def client_without_notes(client, tmp_path):
    with sqlite3.connect(tmp_path / "test.db") as con:
        con.execute("DROP TABLE callback_notes")
    return client


def test_callbacks_include_granite_note_only_when_ok(client):
    rows = {r["id"]: r for r in client.get("/api/disasters/1/callbacks").json()}
    assert rows[10]["note"]["why_flagged"] == "Granite why"
    assert rows[10]["note"]["callback_script"] == "Granite script"
    assert rows[10]["note"]["citations"][0]["label"].startswith("IAPPG 1.1")
    assert rows[10]["note"]["model"] == "granite"
    assert rows[11]["note"] is None
    assert rows[12]["note"] is None


def test_callbacks_work_without_notes_table(client_without_notes):
    rows = client_without_notes.get("/api/disasters/1/callbacks").json()
    assert len(rows) == 3
    assert all(r["note"] is None for r in rows)
    assert client_without_notes.get("/api/model").json()["genai"] is None


def test_model_reports_genai_stats(client):
    genai = client.get("/api/model").json()["genai"]
    assert genai == {"model": "granite", "notes": 1, "rejected": 1, "median_seconds": 35.0,
                     "median_completion_tokens": 175.0}


def test_csv_has_no_note_column(client):
    header = client.get("/api/disasters/1/callbacks.csv").text.splitlines()[0]
    assert "note" not in header


def test_summary_totals(client):
    body = client.get("/api/summary").json()
    assert body["cohort"] == 4
    assert body["records"] == 140
    assert body["verified_damage"] == 70
    assert body["cohort_loss"] == 3500.0
    assert body["needs_repairs"] == 2
    assert body["median_loss"] == 550.0
    assert body["tiers"] == {"missing_documents": 2, "lost_contact": 1, "unverified_ownership_or_occupancy": 1}
    assert body["disasters_with_cohort"] == 2


def test_fairness_drops_unknown_and_joins_adjusted_odds(client):
    rows = client.get("/api/fairness").json()
    assert [r["category"] for r in rows] == ["O", "R"]
    renters = rows[1]
    assert renters["adjusted_odds_ratio"] == 2.0
    assert renters["label"] == "Renters"
    assert rows[0]["is_reference"] is True


def test_disasters_sorted_by_cohort_with_incident_name(client):
    rows = client.get("/api/disasters?limit=1").json()
    assert len(rows) == 1
    assert rows[0]["disasterNumber"] == 1
    assert rows[0]["incident_name"] == "Hurricane"
    assert rows[0]["year"] == 2020


def test_disaster_detail_and_missing(client):
    body = client.get("/api/disasters/1").json()
    assert body["cohort"] == 3
    assert body["needs_repairs"] == 2
    assert body["factor_counts"]["renter"] == 2
    assert client.get("/api/disasters/999").status_code == 404


def test_callbacks_paged_in_rank_order(client):
    rows = client.get("/api/disasters/1/callbacks?limit=2&offset=1").json()
    assert [r["rank_in_disaster"] for r in rows] == [2, 3]


def test_callbacks_csv_export(client):
    res = client.get("/api/disasters/1/callbacks.csv")
    assert res.headers["content-type"].startswith("text/csv")
    lines = res.text.strip().splitlines()
    assert lines[0].startswith("rank_in_disaster,")
    assert len(lines) == 4


def test_model_metrics_decoded(client):
    body = client.get("/api/model").json()
    assert body["metrics"]["roc_auc"] == 0.78
    assert body["metrics"]["backend"] == "sklearn"
    assert body["feature_importance"][0]["feature"] == "ownRent"
    assert body["policy"]["tier_weights"]["missing_documents"] == 1.0
    assert body["policy"]["tier_labels"]["lost_contact"] == "Denied after FEMA lost contact"
    assert body["policy"]["habitability_bonus"] > 0


def test_model_reports_container_runtime(client, monkeypatch):
    assert client.get("/api/model").json()["runtime"]["container"] is None
    monkeypatch.setenv("SECOND_LOOK_CONTAINER", "podman")
    assert client.get("/api/model").json()["runtime"]["container"] == "podman"


def test_bad_limit_rejected(client):
    assert client.get("/api/disasters?limit=0").status_code == 422
