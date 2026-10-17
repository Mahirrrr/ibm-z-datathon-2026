import pandas as pd

from pipeline.rank import rank


def household(**overrides):
    row = {
        "id": 1,
        "disasterNumber": 100,
        "tier": "missing_documents",
        "verified_loss": 5000.0,
        "habitabilityRepairsRequired": False,
        "ownRent": "O",
        "grossIncome": "$60,001-$120,000",
        "applicantAge": "35-49",
        "accessFunctionalNeeds": False,
    }
    row.update(overrides)
    return row


def test_bigger_loss_ranks_first_within_disaster():
    out = rank(pd.DataFrame([household(id=1, verified_loss=500.0), household(id=2, verified_loss=9000.0)]))
    assert list(out["id"]) == [2, 1]
    assert list(out["rank_in_disaster"]) == [1, 2]


def test_vulnerability_and_livability_raise_priority():
    plain = household(id=1)
    vulnerable = household(id=2, ownRent="R", grossIncome="<$15,000", habitabilityRepairsRequired=True)
    out = rank(pd.DataFrame([plain, vulnerable])).set_index("id")
    assert out.loc[2, "priority"] > out.loc[1, "priority"]
    assert out.loc[2, "factors"] == "renter, lowest income band"


def test_ranks_restart_per_disaster():
    out = rank(pd.DataFrame([household(id=1, disasterNumber=1), household(id=2, disasterNumber=2)]))
    assert list(out["rank_in_disaster"]) == [1, 1]


def test_why_flagged_sentence():
    out = rank(pd.DataFrame([household(verified_loss=12345.0, habitabilityRepairsRequired=True, applicantAge="65+")]))
    sentence = out.iloc[0]["why_flagged"]
    assert sentence.startswith("FEMA verified $12,345 in damage")
    assert "home needs repairs to be livable" in sentence
    assert sentence.endswith("age 65+.")


def test_lost_contact_weighs_less_than_missing_documents():
    out = rank(pd.DataFrame([household(id=1, tier="lost_contact"), household(id=2, disasterNumber=2)])).set_index("id")
    assert out.loc[1, "priority"] < out.loc[2, "priority"]
