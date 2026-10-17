"""Static snapshot of the dashboard for GitHub Pages.

Every JSON file is the real API's response (through FastAPI's TestClient), so the snapshot
can't drift from what the LinuxONE container serves. The pages read these files when
static.js sets window.SECOND_LOOK_STATIC (see dashboard/common.js).

    python -m pipeline.static_site --out site --live-url https://<tunnel>
"""

import argparse
import json
import shutil
from datetime import date
from pathlib import Path

from fastapi.testclient import TestClient

from api.app import DASHBOARD_DIR, create_app
from pipeline.config import DB_PATH

PAGE = 500  # the API's maximum callbacks page size
PAGES = ("index.html", "disaster.html", "method.html")
FLAG_TAG = '<script src="static.js"></script>'


def _write(path, body):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body if isinstance(body, str) else json.dumps(body, separators=(",", ":")))


def build(db_path=DB_PATH, out=Path("site"), live_url=None):
    out = Path(out)
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(DASHBOARD_DIR, out)
    client = TestClient(create_app(db_path))
    get = lambda url: client.get(url).raise_for_status()  # noqa: E731
    data = out / "data"

    for name, url in (("summary", "/api/summary"), ("fairness", "/api/fairness"), ("model", "/api/model"),
                      ("disasters", "/api/disasters?limit=1000")):
        _write(data / f"{name}.json", get(url).json())

    for d in json.loads((data / "disasters.json").read_text()):
        n = d["disasterNumber"]
        _write(data / "disasters" / f"{n}.json", get(f"/api/disasters/{n}").json())
        rows, offset = [], 0
        while True:
            page = get(f"/api/disasters/{n}/callbacks?limit={PAGE}&offset={offset}").json()
            rows += page
            offset += PAGE
            if len(page) < PAGE:
                break
        _write(data / "callbacks" / f"{n}.json", rows)
        _write(data / "csv" / f"second_look_{n}.csv", get(f"/api/disasters/{n}/callbacks.csv").text)

    flag = {"snapshot": date.today().isoformat(), "live_url": live_url}
    _write(out / "static.js", f"window.SECOND_LOOK_STATIC = {json.dumps(flag)};\n")
    for page in PAGES:
        html = (out / page).read_text()
        (out / page).write_text(html.replace('<script src="common.js"></script>',
                                             f'{FLAG_TAG}\n  <script src="common.js"></script>', 1))
    (out / ".nojekyll").write_text("")  # serve files as-is
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="site")
    ap.add_argument("--live-url")
    args = ap.parse_args()
    out = build(DB_PATH, args.out, args.live_url)
    size = sum(f.stat().st_size for f in out.rglob("*") if f.is_file())
    print(f"wrote {out} ({size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
