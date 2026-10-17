import pandas as pd

from pipeline import frames


def test_roundtrip_keeps_values_and_dtypes(tmp_path):
    df = pd.DataFrame({
        "id": pd.Series([1, 2, 3], dtype="int64"),
        "loss": pd.Series([1.5, None, 3.25], dtype="float32"),
        "flag": pd.Series([True, None, False], dtype="boolean"),
        "label": ["a", None, "c"],
    })
    path = tmp_path / "t.arrow"
    frames.write(df, path)
    pd.testing.assert_frame_equal(frames.read(path), df)


def test_non_default_index_is_dropped(tmp_path):
    df = pd.DataFrame({"x": [3, 1, 2]}).sort_values("x")
    path = tmp_path / "t.arrow"
    frames.write(df, path)
    out = frames.read(path)
    assert list(out["x"]) == [1, 2, 3]
    assert list(out.index) == [0, 1, 2]


def test_column_subset(tmp_path):
    path = tmp_path / "t.arrow"
    frames.write(pd.DataFrame({"a": [1], "b": [2]}), path)
    assert list(frames.read(path, columns=["b"]).columns) == ["b"]


def test_where_keeps_only_flagged_rows(tmp_path):
    path = tmp_path / "t.arrow"
    frames.write(pd.DataFrame({"keep": [True, False, True], "v": [1, 2, 3]}), path)
    out = frames.read(path, columns=["v"], where="keep")
    assert list(out["v"]) == [1, 3]
    assert list(out.columns) == ["v"]
