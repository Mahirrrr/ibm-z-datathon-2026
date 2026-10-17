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


def test_label_file_streams_batches_with_stable_schema(tmp_path):
    import pyarrow as pa

    from pipeline import frames
    from pipeline.cohort import label_file

    schema = pa.schema([
        ("inspnReturned", pa.bool_()), ("rpfvl", pa.float32()), ("ppfvl", pa.float32()),
        ("ihpEligible", pa.bool_()), ("ineligibleReason", pa.string()),
        ("verifiedOwnership", pa.bool_()), ("verifiedOccupancy", pa.bool_()), ("county", pa.string()),
    ])
    in_cohort = pa.record_batch([[True], [5000.0], [0.0], [False], ["4"], [True], [True], ["Cameron"]], schema=schema)
    # Second batch: nobody qualifies and the string columns are all null.
    excluded = pa.record_batch([[True, None], [0.0, None], [0.0, None], [True, None], [None, None],
                                [True, None], [True, None], [None, None]], schema=schema)
    src, dst = tmp_path / "slim.arrow", tmp_path / "cohort.arrow"
    with pa.ipc.new_file(src, schema) as writer:
        writer.write_batch(in_cohort)
        writer.write_batch(excluded)

    stats = label_file(src, dst)

    out = frames.read(dst)
    assert stats == {"rows": 3, "verified_damage": 1, "denied_verified": 1, "second_look": 1,
                     "tiers": {"missing_documents": 1}}
    assert list(out["second_look"]) == [True, False, False]
    assert list(out["tier"].isna()) == [False, True, True]
    assert out.loc[0, "county"] == "Cameron"
