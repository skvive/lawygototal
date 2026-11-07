#!/usr/bin/env python3
"""Keep LAWYGO public HTML, CSS/JS URLs and CDN release headers in lockstep.

Usage:
  python scripts/bump_design_release.py --apply  # after editing static/design-release.json
  python scripts/bump_design_release.py --check  # non-mutating CI contract
Credentials, RSS, DB, user data and application logic are deliberately excluded.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAGES = (
    "index", "journal", "wiki", "note", "pro", "pan", "channel",
    "pricing", "partnership", "payment", "strategy", "dashboard", "product",
)
LINK = re.compile(r'(?P<attr>\b(?:href|src)=)(?P<quote>["\'])(?P<url>/static/[^"\'\s<>]+)(?P=quote)')
META = re.compile(r'(<meta name="lawygo-design-revision" content=")[^"]+(")')


def release() -> str:
    result = json.loads((ROOT / "static/design-release.json").read_text(encoding="utf-8"))["release"]
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{7,55}", result):
        raise ValueError("Unsafe design release identifier")
    return result


def replace_links(html: str, name: str, version: str) -> str:
    def rewrite(match: re.Match[str]) -> str:
        uri = match.group("url")
        basename = uri.split("?", 1)[0]
        if not basename.endswith((".css", ".js")):
            return match.group(0)
        # WIKI version prefix retained for historical QA and theme specificity.
        tag = ("wiki-ui2-r" + version) if (
            name == "wiki" and basename.endswith("/lawygo-design-fix-20261104.css")
        ) else version
        return match.group("attr") + match.group("quote") + basename + "?v=" + tag + match.group("quote")

    rewritten = LINK.sub(rewrite, html)
    if len(META.findall(rewritten)) != 1:
        raise ValueError(f"{name}: design-revision meta must appear exactly once")
    return META.sub(lambda m: m.group(1) + version + m.group(2), rewritten)


def transform_config(text: str, version: str) -> str:
    config = json.loads(text)
    for route in config["routes"]:
        src = route["src"]
        if route.get("dest", "").endswith(".html"):
            route.setdefault("headers", {})["Cache-Control"] = "private, no-store, max-age=0"
            route["headers"]["X-Lawygo-Design-Release"] = version
        elif src == "/static/(.*)":
            route.setdefault("headers", {})["Cache-Control"] = "public, max-age=0, s-maxage=0, must-revalidate"
            route["headers"]["X-Lawygo-Design-Release"] = version
        elif src == "/favicon.ico":
            route.setdefault("headers", {})["Cache-Control"] = "public, max-age=0, must-revalidate"
            route["headers"]["X-Lawygo-Design-Release"] = version
    return json.dumps(config, ensure_ascii=False, indent=2) + "\n"


def collect_changes() -> list[tuple[Path, bytes]]:
    ver = release()
    changes = []
    for name in PAGES:
        path = ROOT / "static" / (name + ".html")
        raw = path.read_bytes()
        updated = replace_links(raw.decode("utf-8"), name, ver).encode("utf-8")
        if updated != raw:
            changes.append((path, updated))
    config = ROOT / "vercel.json"
    raw = config.read_bytes()
    updated = transform_config(raw.decode("utf-8"), ver).encode("utf-8")
    if updated != raw:
        changes.append((config, updated))
    return changes


def main() -> None:
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--apply", action="store_true")
    modes.add_argument("--check", action="store_true")
    args = parser.parse_args()
    changes = collect_changes()
    if args.check:
        if changes:
            raise SystemExit("Outdated design release references: " + ", ".join(str(x.relative_to(ROOT)) for x, _ in changes))
        print("PASS: all public CSS/JS URLs and CDN release headers match static/design-release.json")
    else:
        for path, payload in changes:
            path.write_bytes(payload)
            print("UPDATED", path.relative_to(ROOT))
        print("Design release", release(), "updated files", len(changes))


if __name__ == "__main__":
    main()
