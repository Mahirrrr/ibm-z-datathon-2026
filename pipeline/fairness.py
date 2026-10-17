"""Fairness audit within verified-damage households.

For each group (renters vs owners, income, age, disability flag):
  * rate of landing in the Second Look cohort, with a 95% Wilson confidence interval
  * ratio vs a named reference category (how many times more likely)
  * adjusted odds ratio from a logistic regression controlling for damage and disaster type,
    so a gap is not just "this group had less damage"
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

from pipeline.config import ADJUSTED_ODDS, COHORT, FAIRNESS, FAIRNESS_GROUPS

Z = 1.959964


def wilson_interval(successes, n, z=Z):
    """95% Wilson score interval for a binomial proportion. Returns (low, high); (nan, nan) if n == 0."""
    successes = np.asarray(successes, dtype=float)
    n = np.asarray(n, dtype=float)
    with np.errstate(invalid="ignore", divide="ignore"):
        p = successes / n
        denom = 1 + z**2 / n
        center = (p + z**2 / (2 * n)) / denom
        half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return center - half, center + half


def group_rates(df, group, reference):
    """Cohort rate per category of `group`, with CI and ratio to the reference category."""
    keys = df[group].astype("object").where(df[group].notna(), "Unknown")
    table = (
        df.assign(_key=keys)
        .groupby("_key")["second_look"]
        .agg(cohort="sum", households="size")
        .reset_index()
        .rename(columns={"_key": "category"})
    )
    table["rate"] = table["cohort"] / table["households"]
    table["ci_low"], table["ci_high"] = wilson_interval(table["cohort"], table["households"])
    ref_rate = table.loc[table["category"] == reference, "rate"]
    table["ratio_vs_reference"] = table["rate"] / ref_rate.iloc[0] if len(ref_rate) else np.nan
    table.insert(0, "group", group)
    table["reference"] = str(reference)
    table["category"] = table["category"].astype(str)
    return table


def adjusted_odds(df, sample_size=1_500_000, seed=7):
    """Odds ratios for each group category vs its reference, controlling for verified loss,
    habitability, destroyed, incident type and declaration year."""
    sample = df.sample(n=min(sample_size, len(df)), random_state=seed)
    parts = []
    for group, reference in FAIRNESS_GROUPS.items():
        col = sample[group].astype("object").where(sample[group].notna(), "Unknown").astype(str)
        dummies = pd.get_dummies(col, prefix=group, dtype=np.float32)
        dummies = dummies.drop(columns=f"{group}_{reference}", errors="ignore")
        parts.append(dummies)
    controls = pd.DataFrame(
        {
            "log_loss": np.log1p(sample["verified_loss"].astype(float)),
            "habitability": sample["habitabilityRepairsRequired"].astype("boolean").fillna(False).astype(float),
            "destroyed": sample["destroyed"].astype("boolean").fillna(False).astype(float),
            "year": pd.to_datetime(sample["declarationDate"]).dt.year.astype(float) - 2000,
        },
        index=sample.index,
    )
    incident = pd.get_dummies(sample["incidentTypeCode"].fillna("NA"), prefix="incident", dtype=np.float32)
    X = pd.concat(parts + [controls, incident.iloc[:, 1:]], axis=1)
    model = LogisticRegression(max_iter=2000, C=1.0)
    model.fit(X.to_numpy(dtype=np.float64), sample["second_look"].astype(int))
    rows = []
    for name, coef in zip(X.columns, model.coef_[0]):
        for group in FAIRNESS_GROUPS:
            if name.startswith(f"{group}_"):
                rows.append(
                    {
                        "group": group,
                        "category": name[len(group) + 1 :],
                        "reference": str(FAIRNESS_GROUPS[group]),
                        "adjusted_odds_ratio": float(np.exp(coef)),
                    }
                )
    return pd.DataFrame(rows)


def main():
    cols = ["second_look", "verified_damage", "verified_loss", "habitabilityRepairsRequired",
            "destroyed", "incidentTypeCode", "declarationDate"] + list(FAIRNESS_GROUPS)
    df = pd.read_parquet(COHORT, columns=cols)
    df = df[df["verified_damage"]]
    rates = pd.concat([group_rates(df, g, ref) for g, ref in FAIRNESS_GROUPS.items()], ignore_index=True)
    rates.to_parquet(FAIRNESS, index=False)
    odds = adjusted_odds(df)
    odds.to_parquet(ADJUSTED_ODDS, index=False)
    pd.set_option("display.width", 160)
    print(rates[["group", "category", "households", "rate", "ci_low", "ci_high", "ratio_vs_reference"]]
          .to_string(index=False, float_format=lambda v: f"{v:.4f}"))
    print(odds.to_string(index=False, float_format=lambda v: f"{v:.2f}"))


if __name__ == "__main__":
    main()
