"""Prevent non-versioned styles/scripts and old release headers from shipping."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = (
    "index", "journal", "wiki", "note", "pro", "pan", "channel",
    "pricing", "partnership", "payment", "strategy", "dashboard", "product",
)
ASSET = re.compile(r'(?:href|src)="(/static/[^"]+\.(?:css|js)(?:\?[^"]*)?)"')


class DesignReleaseTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.release = json.loads((ROOT / "static/design-release.json").read_text(encoding="utf-8"))["release"]

    def test_all_public_assets_fingerprinted(self):
        for name in PUBLIC:
            with self.subTest(page=name):
                data = (ROOT / "static" / (name + ".html")).read_text(encoding="utf-8")
                self.assertIn(f'name="lawygo-design-revision" content="{self.release}"', data)
                assets = ASSET.findall(data)
                self.assertGreaterEqual(len(assets), 6, name)
                self.assertTrue(all("?v=" in url and self.release in url for url in assets), (name, assets))
                self.assertEqual(len(assets), len(set(assets)), "duplicate CSS/JS reference in " + name)

    def test_html_routes_no_store_but_apis_unchanged(self):
        config = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
        routes = config["routes"]
        pages = [item for item in routes if item.get("dest", "").endswith(".html")]
        self.assertEqual(len(pages), 13)
        for route in pages:
            self.assertIn("no-store", route["headers"]["Cache-Control"])
            self.assertEqual(route["headers"]["X-Lawygo-Design-Release"], self.release)
        static = next(item for item in routes if item["src"] == "/static/(.*)")
        self.assertEqual(static["headers"]["X-Lawygo-Design-Release"], self.release)
        self.assertIn("max-age=0", static["headers"]["Cache-Control"])
        self.assertEqual(routes[-2], {"src": "/api/(.*)", "dest": "app.py"})
        self.assertEqual(routes[-1], {"src": "/(.*)", "dest": "app.py"})

    def test_release_generator_is_idempotent(self):
        import sys
        sys.path.insert(0, str(ROOT / "scripts"))
        from bump_design_release import collect_changes
        changes = collect_changes()
        self.assertEqual(changes, [], "run python scripts/bump_design_release.py --apply")


if __name__ == "__main__":
    unittest.main()
