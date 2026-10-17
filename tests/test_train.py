import numpy as np

from pipeline.train import SNAPML_MISSING, model_matrix


def test_snapml_matrix_has_no_nan():
    X = np.array([[1.0, np.nan], [np.nan, 0.0]], dtype=np.float32)
    out = model_matrix(X, "snapml")
    assert not np.isnan(out).any()
    assert out[0, 1] == SNAPML_MISSING and out[1, 0] == SNAPML_MISSING
    assert out[0, 0] == 1.0 and out[1, 1] == 0.0


def test_sklearn_matrix_keeps_nan():
    X = np.array([[np.nan]], dtype=np.float32)
    assert np.isnan(model_matrix(X, "sklearn")).all()
