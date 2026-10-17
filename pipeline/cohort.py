"""Rule-based Second Look cohort.

A household is in the cohort when all three hold:
  1. verified damage: an inspection was returned and FEMA verified real or personal property loss > $0
  2. denied: not eligible for IHP
  3. fixable: the denial reason is one a caseworker callback can resolve (see codebook.py)

Rules, not ML, on purpose: every flagged household can be explained in one sentence.
"""

import numpy as np
import pandas as pd

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


def main():
    df = pd.read_parquet(IHP_SLIM)
    labeled = label_cohort(df)
    labeled.to_parquet(COHORT, index=False)

    vd = labeled["verified_damage"]
    print(f"rows: {len(labeled):,}")
    print(f"verified damage: {vd.sum():,}")
    print(f"verified damage + denied: {(vd & labeled['denied']).sum():,}")
    print(f"second look cohort: {labeled['second_look'].sum():,}")
    print(labeled.loc[labeled["second_look"], "tier"].value_counts().to_string())


if __name__ == "__main__":
    main()
