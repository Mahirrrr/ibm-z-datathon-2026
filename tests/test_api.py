import sqlite3

import pytest
from fastapi.testclient import TestClient

from api.app import create_app


@pytest.fixture
def client(sample_db):
    return TestClient(create_app(sample_db))


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


def test_summary_reports_aid_estimate(client):
    aid = client.get("/api/summary").json()["aid"]
    assert aid == {"total": 3600.0, "median": 700.0, "households": 3,
                   "basis": {"disaster_band": 2, "disaster": 1, "none": 1}}


def test_counties_sorted_by_cohort_with_top_disaster_share(client):
    rows = client.get("/api/counties").json()
    assert [r["fips"] for r in rows] == ["22023", "72127"]
    assert rows[0]["top_disaster"] == 1
    assert rows[0]["top_share"] == 1.0
    assert rows[0]["rate"] == 0.075


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
