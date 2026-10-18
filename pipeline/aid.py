"""Aid left on the table: a modeled estimate of what each Second Look household would likely
have received had it been approved, plus the county view behind the Story page map.

Estimate per cohort household = median ihpAmount among APPROVED verified-damage households in
the same disaster and the same verified-loss band. Cells with fewer than MIN_CELL approvals fall
back to the whole disaster, then to the loss band across all disasters. The same disaster keeps
the year's grant caps and local costs. Medians make the total a conservative floor: approved
awards are right-skewed (median $2,000, mean about $4,355).

A modeled estimate, not a promise of eligibility: a callback can still end in a denial.
"""

import numpy as np
import pandas as pd

from pipeline import frames
from pipeline.config import AID, COHORT, COUNTIES

LOSS_BANDS = [0, 1_000, 2_500, 5_000, 10_000, 25_000, 50_000, np.inf]
MIN_CELL = 30
BASES = ("disaster_band", "disaster", "band", "none")


def loss_band(loss):
    """Index into LOSS_BANDS, left-closed: $1,000 falls in the $1,000-$2,500 band."""
    return pd.Series(np.searchsorted(LOSS_BANDS, loss.to_numpy(), side="right") - 1, index=loss.index)


def _cell_median(approved, cohort, keys, min_cell):
    stats = approved.groupby(keys)["ihpAmount"].agg(["size", "median"])
    stats = stats[stats["size"] >= min_cell]["median"]
    index = pd.MultiIndex.from_frame(cohort[keys]) if len(keys) > 1 else pd.Index(cohort[keys[0]])
    return pd.Series(stats.reindex(index).to_numpy(), index=cohort.index)


def estimate(df, min_cell=MIN_CELL):
    """One row per cohort household: id, disasterNumber, aid_estimate, aid_basis.

    df holds verified-damage households with disasterNumber, verified_loss, ihpEligible,
    ihpAmount and second_look.
    """
    df = df.assign(band=loss_band(df["verified_loss"]))
    approved = df[df["ihpEligible"].fillna(False).astype(bool)]
    cohort = df[df["second_look"].fillna(False).astype(bool)]

    out = cohort[["id", "disasterNumber"]].copy()
    out["aid_estimate"] = np.nan
    out["aid_basis"] = "none"
    for basis, keys in (("disaster_band", ["disasterNumber", "band"]), ("disaster", ["disasterNumber"]),
                        ("band", ["band"])):
        median = _cell_median(approved, cohort, keys, min_cell)
        fill = out["aid_estimate"].isna() & median.notna()
        out.loc[fill, "aid_estimate"] = median[fill]
        out.loc[fill, "aid_basis"] = basis
    return out.reset_index(drop=True)


def summarize(est):
    values = est["aid_estimate"].dropna()
    counts = est["aid_basis"].value_counts()
    return {"households": len(est), "estimated": len(values), "total": float(values.sum()),
            "median": float(values.median()) if len(values) else None,
            "basis": {b: int(counts.get(b, 0)) for b in BASES if counts.get(b, 0)}}


def county_summary(df):
    """Counties (5-digit FIPS) with at least one cohort household: cohort count, verified-damage
    households, cohort rate, and the disaster that contributed the most cohort households."""
    df = df[df["fips"].notna()]
    flag = df["second_look"].fillna(False).astype(bool)
    base = df.groupby("fips").agg(verified_damage=("id", "size"),
                                  county=("county", lambda s: s.mode().iat[0] if s.notna().any() else None),
                                  state=("damagedStateAbbreviation",
                                         lambda s: s.mode().iat[0] if s.notna().any() else None))
    cohort = df[flag]
    by_disaster = cohort.groupby(["fips", "disasterNumber"]).size().rename("n").reset_index()
    top = by_disaster.sort_values(["fips", "n", "disasterNumber"], ascending=[True, False, True]).drop_duplicates("fips")
    top = top.set_index("fips").rename(columns={"disasterNumber": "top_disaster", "n": "top_disaster_cohort"})
    out = base.join(cohort.groupby("fips").size().rename("cohort"), how="inner").join(top)
    out["rate"] = out["cohort"] / out["verified_damage"]
    cols = ["county", "state", "cohort", "verified_damage", "rate", "top_disaster", "top_disaster_cohort"]
    return out[cols].reset_index()


def main():
    cols = ["id", "disasterNumber", "verified_loss", "ihpEligible", "ihpAmount", "second_look", "fips", "county",
            "damagedStateAbbreviation"]
    df = frames.read(COHORT, columns=cols, where="verified_damage")
    df["ihpAmount"] = df["ihpAmount"].astype(np.float64)
    est = estimate(df)
    frames.write(est, AID)
    summary = summarize(est)
    counties = county_summary(df)
    frames.write(counties, COUNTIES)

    print(f"aid estimate: {summary['estimated']:,} of {summary['households']:,} cohort households")
    print(f"  total ${summary['total']:,.0f}, median ${summary['median']:,.0f}")
    for basis, n in summary["basis"].items():
        print(f"  {basis}: {n:,}")
    print(f"counties with cohort households: {len(counties):,} "
          f"({int(counties['cohort'].sum()):,} households; {int(df.loc[df['fips'].isna(), 'second_look'].sum()):,} "
          f"have no county)")


if __name__ == "__main__":
    main()
