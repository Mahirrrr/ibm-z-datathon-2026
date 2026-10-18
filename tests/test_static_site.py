import json

from pipeline import static_site


def build(sample_db, tmp_path, **kw):
    out = tmp_path / "site"
    static_site.build(sample_db, out, **kw)
    return out


def load(path):
    return json.loads(path.read_text())


def test_exports_every_api_response(sample_db, tmp_path):
    out = build(sample_db, tmp_path)
    data = out / "data"
    assert load(data / "summary.json")["cohort"] == 4
    assert [r["category"] for r in load(data / "fairness.json")] == ["O", "R"]
    assert load(data / "model.json")["metrics"]["roc_auc"] == 0.78
    assert [d["disasterNumber"] for d in load(data / "disasters.json")] == [1, 2]
    assert load(data / "disasters" / "1.json")["needs_repairs"] == 2
    assert [c["fips"] for c in load(data / "counties.json")] == ["22023", "72127"]
    assert load(data / "summary.json")["aid"]["total"] == 3600.0


def test_callbacks_exported_in_full_with_notes(sample_db, tmp_path):
    out = build(sample_db, tmp_path)
    rows = load(out / "data" / "callbacks" / "1.json")
    assert [r["rank_in_disaster"] for r in rows] == [1, 2, 3]
    assert rows[0]["note"]["why_flagged"] == "Granite why"
    assert rows[1]["note"] is None


def test_callbacks_paged_past_api_limit(sample_db, tmp_path, monkeypatch):
    monkeypatch.setattr(static_site, "PAGE", 2)
    rows = load(build(sample_db, tmp_path) / "data" / "callbacks" / "1.json")
    assert [r["id"] for r in rows] == [10, 11, 12]


def test_csv_matches_api_export(sample_db, tmp_path):
    out = build(sample_db, tmp_path)
    lines = (out / "data" / "csv" / "second_look_1.csv").read_text().strip().splitlines()
    assert lines[0].startswith("rank_in_disaster,")
    assert len(lines) == 4


def test_pages_flagged_static_and_assets_copied(sample_db, tmp_path):
    out = build(sample_db, tmp_path, live_url="https://live.example")
    for page in ("index.html", "disaster.html", "method.html"):
        html = (out / page).read_text()
        assert '<script src="static.js"></script>' in html
        assert html.index("static.js") < html.index("common.js"), "flag must load before the API helper"
    assert (out / "common.js").exists() and (out / "styles.css").exists()
    flag = (out / "static.js").read_text()
    assert "SECOND_LOOK_STATIC" in flag and "https://live.example" in flag
    assert (out / ".nojekyll").exists()


def test_rebuild_replaces_old_output(sample_db, tmp_path):
    out = build(sample_db, tmp_path)
    (out / "data" / "stale.json").write_text("{}")
    build(sample_db, tmp_path)
    assert not (out / "data" / "stale.json").exists()
