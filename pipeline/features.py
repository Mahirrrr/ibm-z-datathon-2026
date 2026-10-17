"""Feature matrix for the cohort model, plus a split by disaster so the test set holds
disasters the model never saw.
"""

import numpy as np
import pandas as pd
from sklearn.model_selection import GroupShuffleSplit

from pipeline.config import BOOLEAN_FEATURES, CATEGORICAL_FEATURES, NUMERIC_FEATURES

FEATURES = CATEGORICAL_FEATURES + BOOLEAN_FEATURES + NUMERIC_FEATURES


def category_maps(df):
    """Stable category -> code mapping per categorical column, built once from the full data."""
    return {
        col: sorted(df[col].dropna().astype(str).unique().tolist())
        for col in CATEGORICAL_FEATURES
    }


def build_matrix(df, maps):
    """Encode df into a float32 matrix. Missing values stay NaN; unseen categories become NaN."""
    out = pd.DataFrame(index=df.index)
    for col in CATEGORICAL_FEATURES:
        lookup = {value: i for i, value in enumerate(maps[col])}
        out[col] = df[col].astype("string").map(lookup).astype("float32")
    for col in BOOLEAN_FEATURES:
        out[col] = df[col].astype("boolean").astype("float32")
    out["rpfvl"] = df["rpfvl"].astype("float32")
    out["ppfvl"] = df["ppfvl"].astype("float32")
    out["declarationYear"] = pd.to_datetime(df["declarationDate"]).dt.year.astype("float32")
    return out[FEATURES].to_numpy(dtype=np.float32)


def categorical_mask():
    return np.array([name in CATEGORICAL_FEATURES for name in FEATURES])


def disaster_split(df, test_size=0.2, seed=7):
    """Train/test row positions with whole disasters on one side only."""
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train_idx, test_idx = next(splitter.split(df, groups=df["disasterNumber"]))
    return train_idx, test_idx
