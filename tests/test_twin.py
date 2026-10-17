import numpy as np

from pipeline import twin
from pipeline.features import FEATURES


def maps():
    from pipeline.config import CATEGORICAL_FEATURES
    return {c: ["a", "b", "c"] for c in CATEGORICAL_FEATURES}


def row(**values):
    x = np.full(len(FEATURES), np.nan, dtype=np.float32)
    for name, v in values.items():
        x[FEATURES.index(name)] = v
    return x


def test_one_hot_width_and_values():
    X = np.vstack([row(ownRent=1, rpfvl=np.e - 1, destroyed=1, declarationYear=2020), row()])
    out = twin.one_hot(X, maps(), FEATURES)
    from pipeline.config import BOOLEAN_FEATURES, CATEGORICAL_FEATURES
    assert out.shape == (2, 3 * len(CATEGORICAL_FEATURES) + len(BOOLEAN_FEATURES) + 3)
    assert out.dtype == np.float32
    assert np.isfinite(out).all()
    start = 3 * CATEGORICAL_FEATURES.index("ownRent")
    assert out[0, start:start + 3].tolist() == [0, 1, 0]
    assert out[1, start:start + 3].tolist() == [0, 0, 0], "missing category is all zeros"
    assert out[0, -1] == np.float32(1.0), "declaration year 2020 scales to 1.0"
    assert abs(out[0, -3] - 1.0) < 1e-6, "rpfvl log1p(e-1) = 1"
    assert out[1, -3] == 0.0, "missing money is 0"


def test_negative_money_clipped():
    out = twin.one_hot(np.vstack([row(rpfvl=-5)]), maps(), FEATURES)
    assert np.isfinite(out).all() and (out >= 0).all()


def test_roc_auc_matches_known_values():
    y = np.array([0, 0, 1, 1])
    assert twin.roc_auc(y, np.array([0.1, 0.2, 0.8, 0.9])) == 1.0
    assert twin.roc_auc(y, np.array([0.9, 0.8, 0.2, 0.1])) == 0.0
    assert twin.roc_auc(y, np.array([0.1, 0.4, 0.35, 0.8])) == 0.75


def test_device_from_env(monkeypatch):
    monkeypatch.delenv("NNPA_DEVICES", raising=False)
    assert twin.device() == "nnpa"
    for off in ("0", "false", "FALSE"):
        monkeypatch.setenv("NNPA_DEVICES", off)
        assert twin.device() == "cpu"


def test_precision_at_k():
    assert twin.precision_at_k(np.array([1, 0, 1, 0]), np.array([0.9, 0.8, 0.7, 0.1]), 2) == 0.5
