"""Smoke-test public HTML routes and critical static assets."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
import app as core

ROUTES = [
    "/",
    "/journal",
    "/channel",
    "/p/wiki",
    "/p/note",
    "/p/pan",
    "/p/channel",
    "/pro",
    "/pricing",
    "/payment",
    "/partnership",
    "/strategy",
    "/dashboard",
    "/nope-page-404",
]
ASSETS = [
    "/static/img/journal/hero-markets.jpg",
    "/static/img/editorial/journal-lead.jpg",
    "/static/logo.svg",
]

def main():
    c = TestClient(core.app)
    failed = []
    for path in ROUTES:
        r = c.get(path, headers={"Accept": "text/html"})
        if path.endswith("404") or path == "/nope-page-404":
            if r.status_code != 404:
                failed.append(f"{path} expected 404 got {r.status_code}")
        elif r.status_code != 200:
            failed.append(f"{path} {r.status_code}")
    for path in ASSETS:
        r = c.get(path)
        if r.status_code != 200:
            failed.append(f"asset {path} {r.status_code}")
    if failed:
        print("FAIL", *failed, sep="\n")
        sys.exit(1)
    print("OK", len(ROUTES), "routes,", len(ASSETS), "assets")

if __name__ == "__main__":
    main()
