"""Rule-based Second Look cohort.

A household is in the cohort when all three hold:
  1. verified damage: an inspection was returned and FEMA verified real or personal property loss > $0
  2. denied: not eligible for IHP
  3. fixable: the denial reason is one a caseworker callback can resolve (see codebook.py)

Rules, not ML, on purpose: every flagged household can be explained in one sentence.
"""

from collections import Counter

import numpy as np
import pandas as pd
import pyarrow as pa

from pipeline import frames
from pipeline.codebook import FIXABLE_TIERS, OTHER_REASONS, UNVERIFIED_TIER
from pipeline.config import COHORT, IHP_SLIM


def _flag(series):
    """Nullable boolean column to plain bool, treating missing as False."""
    return series.fillna(False).astype(bool)


def verified_damage(df):
    loss = (df["rpfvl"].fillna(0) > 0) | (df["ppfvl"].fillna(0) > 0)
    return _flag(df["inspnReturned"]) & loss


def denied(df):
    return ~_flag(df["ihpEligible"])


def fixable_tier(df):
    """Tier name per row, or None when the denial is not fixable."""
    reason = df["ineligibleReason"].astype("string")
    unverified = (df["verifiedOwnership"] == False) | (df["verifiedOccupancy"] == False)  # noqa: E712
    unverified = unverified.fillna(False).astype(bool)

    tier = pd.Series(None, index=df.index, dtype="object")
    for code, name in FIXABLE_TIERS.items():
        tier[reason == code] = name
    tier[reason.isin(OTHER_REASONS).fillna(False) & unverified] = UNVERIFIED_TIER
    return tier


def label_cohort(df):
    """Return a copy of df with verified_damage, denied, tier and second_look columns."""
    out = df.copy()
    out["verified_damage"] = verified_damage(out)
    out["denied"] = denied(out)
    out["tier"] = fixable_tier(out)
    out["second_look"] = out["verified_damage"] & out["denied"] & out["tier"].notna()
    out.loc[~out["second_look"], "tier"] = None
    out["verified_loss"] = (
        out["rpfvl"].fillna(0).astype(np.float64) + out["ppfvl"].fillna(0).astype(np.float64)
    )
    return out


LABEL_TYPES = {
    "verified_damage": pa.bool_(),
    "denied": pa.bool_(),
    "tier": pa.string(),
    "second_look": pa.bool_(),
    "verified_loss": pa.float64(),
}


def label_file(src, dst):
    """Label an Arrow IPC file one record batch at a time; peak memory is one batch.

    Source columns pass through as Arrow untouched (so their types never drift between
    batches); only the label columns are computed in pandas and appended with fixed types.
    """
    stats = {"rows": 0, "verified_damage": 0, "denied_verified": 0, "second_look": 0, "tiers": Counter()}
    reader = pa.ipc.open_file(src)
    rule_columns = ["inspnReturned", "rpfvl", "ppfvl", "ihpEligible", "ineligibleReason",
                    "verifiedOwnership", "verifiedOccupancy"]
    schema = reader.schema
    for name, kind in LABEL_TYPES.items():
        schema = schema.append(pa.field(name, kind))
    options = pa.ipc.IpcWriteOptions(compression=frames.COMPRESSION)
    with pa.ipc.new_file(dst, schema, options=options) as writer:
        for i in range(reader.num_record_batches):
            batch = reader.get_batch(i)
            labels = label_cohort(batch.select(rule_columns).to_pandas())
            arrays = batch.columns + [pa.array(labels[n], type=t, from_pandas=True) for n, t in LABEL_TYPES.items()]
            writer.write_batch(pa.record_batch(arrays, schema=schema))

            stats["rows"] += len(labels)
            stats["verified_damage"] += int(labels["verified_damage"].sum())
            stats["denied_verified"] += int((labels["verified_damage"] & labels["denied"]).sum())
            stats["second_look"] += int(labels["second_look"].sum())
            stats["tiers"].update(labels.loc[labels["second_look"], "tier"])
    stats["tiers"] = dict(stats["tiers"])
    return stats


def main():
    stats = label_file(IHP_SLIM, COHORT)
    print(f"rows: {stats['rows']:,}")
    print(f"verified damage: {stats['verified_damage']:,}")
    print(f"verified damage + denied: {stats['denied_verified']:,}")
    print(f"second look cohort: {stats['second_look']:,}")
    for tier, n in sorted(stats["tiers"].items(), key=lambda kv: -kv[1]):
        print(f"  {tier}: {n:,}")


if __name__ == "__main__":
    main()
