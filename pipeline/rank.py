"""Ranked caseworker callback list per disaster.

priority = loss_percentile_within_disaster x tier_weight x (1 + bonuses)
Bonuses: home not livable without repairs, renter, lowest income band, age 65+, access/functional needs.
Weights live in config.py and are shown in the UI: a policy choice, not a learned one.
Each row gets a one-sentence "why flagged" a caseworker can read aloud.
"""

import pandas as pd

from pipeline import frames
from pipeline.codebook import TIER_LABELS
from pipeline.config import (
    CALLBACKS,
    COHORT,
    HABITABILITY_BONUS,
    TIER_WEIGHTS,
    VULNERABILITY_BONUS,
)

LOW_INCOME = {"0", "<$15,000"}


def vulnerability_factors(row):
    factors = []
    if row["ownRent"] == "R":
        factors.append("renter")
    if row["grossIncome"] in LOW_INCOME:
        factors.append("lowest income band")
    if row["applicantAge"] == "65+":
        factors.append("age 65+")
    if row["accessFunctionalNeeds"] is True:
        factors.append("needs accessibility support")
    return factors


def why_flagged(row):
    loss = f"${row['verified_loss']:,.0f}"
    parts = [f"FEMA verified {loss} in damage", TIER_LABELS[row["tier"]].lower()]
    if row["habitabilityRepairsRequired"] is True:
        parts.append("home needs repairs to be livable")
    if row["factors"]:
        parts.append(", ".join(row["factors"]))
    return "; ".join(parts) + "."


def rank(df):
    """Add priority, factors and why_flagged to cohort rows; sorted by disaster then priority."""
    out = df.copy()
    out["loss_pct"] = out.groupby("disasterNumber")["verified_loss"].rank(pct=True)
    out["factors"] = out.apply(vulnerability_factors, axis=1)
    livable_bonus = out["habitabilityRepairsRequired"].astype("boolean").fillna(False).astype(float)
    bonus = 1 + HABITABILITY_BONUS * livable_bonus + VULNERABILITY_BONUS * out["factors"].str.len()
    out["priority"] = out["loss_pct"] * out["tier"].map(TIER_WEIGHTS) * bonus
    out["why_flagged"] = out.apply(why_flagged, axis=1)
    out = out.sort_values(["disasterNumber", "priority"], ascending=[True, False])
    out["rank_in_disaster"] = out.groupby("disasterNumber").cumcount() + 1
    out["factors"] = out["factors"].str.join(", ")
    return out


def main():
    cols = ["id", "disasterNumber", "declarationDate", "damagedStateAbbreviation", "county",
            "incidentTypeCode", "tier", "second_look", "verified_loss", "habitabilityRepairsRequired",
            "ownRent", "grossIncome", "applicantAge", "accessFunctionalNeeds", "ineligibleReason"]
    df = frames.read(COHORT, columns=[c for c in cols if c != "second_look"], where="second_look")
    df["accessFunctionalNeeds"] = df["accessFunctionalNeeds"].astype(object)
    df["habitabilityRepairsRequired"] = df["habitabilityRepairsRequired"].astype(object)
    ranked = rank(df)
    frames.write(ranked, CALLBACKS)
    top = ranked[ranked["disasterNumber"] == ranked["disasterNumber"].value_counts().idxmax()].head(5)
    print(f"ranked {len(ranked):,} households across {ranked['disasterNumber'].nunique():,} disasters")
    for _, row in top.iterrows():
        print(f"#{row['rank_in_disaster']} ({row['priority']:.2f}) {row['why_flagged']}")


if __name__ == "__main__":
    main()
