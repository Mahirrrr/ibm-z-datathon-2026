import json
import sqlite3

import pandas as pd
import pytest


@pytest.fixture
def sample_db(tmp_path):
    """A tiny secondlook.db with every table the API reads."""
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
    return db
