import pandas as pd

from pipeline.codebook import UNVERIFIED_TIER, reason_label
from pipeline.cohort import label_cohort


def make(**overrides):
    row = {
        "inspnReturned": True,
        "rpfvl": 5000.0,
        "ppfvl": 0.0,
        "ihpEligible": False,
        "ineligibleReason": "4",
        "verifiedOwnership": True,
        "verifiedOccupancy": True,
    }
    row.update(overrides)
    return row


def run(*rows):
    df = pd.DataFrame(list(rows))
    for col in ["inspnReturned", "ihpEligible", "verifiedOwnership", "verifiedOccupancy"]:
        df[col] = df[col].astype("boolean")
    return label_cohort(df)


def test_missing_documents_with_verified_damage_is_in_cohort():
    out = run(make())
    assert out.loc[0, "second_look"]
    assert out.loc[0, "tier"] == "missing_documents"


def test_lost_contact_is_in_cohort():
    out = run(make(ineligibleReason="3"))
    assert out.loc[0, "tier"] == "lost_contact"


def test_eligible_household_is_excluded():
    out = run(make(ihpEligible=True, ineligibleReason=None))
    assert not out.loc[0, "second_look"]
    assert out.loc[0, "tier"] is None


def test_insured_or_no_damage_reasons_are_not_fixable():
    out = run(make(ineligibleReason="2"), make(ineligibleReason="1"), make(ineligibleReason="5"))
    assert not out["second_look"].any()


def test_zero_loss_is_not_verified_damage():
    out = run(make(rpfvl=0.0, ppfvl=0.0))
    assert not out.loc[0, "verified_damage"]
    assert not out.loc[0, "second_look"]


def test_personal_property_loss_alone_counts():
    out = run(make(rpfvl=0.0, ppfvl=800.0))
    assert out.loc[0, "second_look"]


def test_missing_inspection_is_not_verified():
    out = run(make(inspnReturned=None))
    assert not out.loc[0, "verified_damage"]


def test_null_money_is_treated_as_zero():
    out = run(make(rpfvl=None, ppfvl=None))
    assert not out.loc[0, "verified_damage"]
    assert out.loc[0, "verified_loss"] == 0


def test_other_reason_counts_only_when_unverified():
    out = run(
        make(ineligibleReason="7"),
        make(ineligibleReason="7", verifiedOwnership=False),
        make(ineligibleReason="9", verifiedOccupancy=False),
        make(ineligibleReason="7", verifiedOwnership=None, verifiedOccupancy=None),
    )
    assert list(out["second_look"]) == [False, True, True, False]
    assert out.loc[1, "tier"] == UNVERIFIED_TIER


def test_missing_reason_is_not_fixable():
    out = run(make(ineligibleReason=None))
    assert not out.loc[0, "second_look"]


def test_reason_labels():
    assert reason_label("4") == "Needs to submit documentation"
    assert reason_label(None) == "No reason recorded"
    assert reason_label("42") == "Unknown code"
