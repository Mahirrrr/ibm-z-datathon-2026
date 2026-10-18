import math

import pandas as pd

from pipeline.aid import county_summary, estimate, loss_band, summarize


def household(id, disaster=1, loss=1500.0, approved=True, amount=1000.0, cohort=False, fips="22019",
              county="Calcasieu (Parish)", state="LA"):
    return {"id": id, "disasterNumber": disaster, "verified_loss": loss, "ihpEligible": approved,
            "ihpAmount": amount if approved else 0.0, "second_look": cohort, "fips": fips, "county": county,
            "damagedStateAbbreviation": state}


def approved(n, start, **kw):
    return [household(start + i, **kw) for i in range(n)]


def test_loss_bands_are_left_closed():
    assert list(loss_band(pd.Series([0.01, 999.99, 1000.0, 2500.0, 49999.0, 50000.0, 9e6]))) == [0, 0, 1, 2, 5, 6, 6]


def test_estimate_uses_disaster_and_band_median():
    rows = approved(30, 100, amount=1000.0) + approved(31, 200, amount=3000.0, loss=6000.0)
    rows.append(household(1, approved=False, cohort=True))
    out = estimate(pd.DataFrame(rows), min_cell=30).set_index("id")
    assert out.loc[1, "aid_estimate"] == 1000.0
    assert out.loc[1, "aid_basis"] == "disaster_band"


def test_small_cell_falls_back_to_disaster_median():
    rows = approved(29, 100, amount=1000.0) + approved(31, 200, amount=5000.0, loss=6000.0)
    rows.append(household(1, approved=False, cohort=True))
    out = estimate(pd.DataFrame(rows), min_cell=30).set_index("id")
    assert out.loc[1, "aid_basis"] == "disaster"
    assert out.loc[1, "aid_estimate"] == 5000.0  # median of 29 x 1000 and 31 x 5000


def test_small_disaster_falls_back_to_band_across_disasters():
    rows = approved(5, 100, disaster=2, amount=9000.0) + approved(30, 200, disaster=3, amount=800.0)
    rows.append(household(1, disaster=2, approved=False, cohort=True))
    out = estimate(pd.DataFrame(rows), min_cell=30).set_index("id")
    assert out.loc[1, "aid_basis"] == "band"
    assert out.loc[1, "aid_estimate"] == 800.0


def test_no_comparable_approvals_leaves_estimate_empty():
    rows = [household(1, approved=False, cohort=True, loss=80000.0)] + approved(3, 100)
    out = estimate(pd.DataFrame(rows), min_cell=30).set_index("id")
    assert math.isnan(out.loc[1, "aid_estimate"])
    assert out.loc[1, "aid_basis"] == "none"


def test_denied_households_never_count_as_comparables():
    rows = approved(30, 100, amount=1000.0) + [household(500 + i, approved=False) for i in range(100)]
    rows.append(household(1, approved=False, cohort=True))
    out = estimate(pd.DataFrame(rows), min_cell=30)
    assert list(out["id"]) == [1]
    assert out.iloc[0]["aid_estimate"] == 1000.0


def test_summarize_totals_and_basis_counts():
    est = pd.DataFrame({"id": [1, 2, 3], "aid_estimate": [100.0, 300.0, float("nan")],
                        "aid_basis": ["disaster_band", "disaster", "none"]})
    s = summarize(est)
    assert s == {"households": 3, "estimated": 2, "total": 400.0, "median": 200.0,
                 "basis": {"disaster_band": 1, "disaster": 1, "none": 1}}


def test_county_summary_counts_rate_and_top_disaster():
    rows = [household(1, disaster=1, cohort=True, approved=False), household(2, disaster=2, cohort=True, approved=False),
            household(3, disaster=2, cohort=True, approved=False), household(4), household(5, fips="72127",
            county="San Juan (Municipio)", state="PR"), household(6, fips=None)]
    out = county_summary(pd.DataFrame(rows)).set_index("fips")
    la = out.loc["22019"]
    assert (la.cohort, la.verified_damage, la.top_disaster, la.top_disaster_cohort) == (3, 4, 2, 2)
    assert la.rate == 0.75
    assert la.county == "Calcasieu (Parish)" and la.state == "LA"
    assert "72127" not in out.index, "counties with no cohort households are left out"
    assert None not in out.index
