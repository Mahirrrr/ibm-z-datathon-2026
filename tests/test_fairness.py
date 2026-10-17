import math

import pandas as pd

from pipeline.fairness import group_rates, wilson_interval


def test_wilson_matches_known_value():
    # 10 successes out of 100: textbook Wilson 95% interval is about (0.0552, 0.1744)
    low, high = wilson_interval(10, 100)
    assert math.isclose(float(low), 0.0552, abs_tol=1e-3)
    assert math.isclose(float(high), 0.1744, abs_tol=1e-3)


def test_wilson_zero_successes_has_zero_lower_bound():
    low, high = wilson_interval(0, 50)
    assert float(low) == 0 or abs(float(low)) < 1e-12
    assert 0 < float(high) < 0.1


def test_wilson_empty_group_is_nan():
    low, high = wilson_interval(0, 0)
    assert math.isnan(float(low)) and math.isnan(float(high))


def test_group_rates_ratio_and_unknown_bucket():
    df = pd.DataFrame(
        {
            "ownRent": ["O", "O", "O", "O", "R", "R", None, None],
            "second_look": [True, False, False, False, True, True, False, True],
        }
    )
    table = group_rates(df, "ownRent", "O").set_index("category")
    assert table.loc["O", "rate"] == 0.25
    assert table.loc["R", "rate"] == 1.0
    assert table.loc["R", "ratio_vs_reference"] == 4.0
    assert table.loc["Unknown", "households"] == 2


def test_group_rates_missing_reference_gives_nan_ratio():
    df = pd.DataFrame({"ownRent": ["R", "R"], "second_look": [True, False]})
    table = group_rates(df, "ownRent", "O")
    assert table["ratio_vs_reference"].isna().all()
