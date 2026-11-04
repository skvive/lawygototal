"""Read-only SEO discovery contract checks (no production credentials or network)."""
import unittest
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

import seo_discovery

POST_ID = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None


class FakeDB:
    def __init__(self, rows):
        self.rows = rows
        self.queries = []

    def execute(self, sql, params):
        self.queries.append((sql, params))
        for marker in ("p.tenant=?", "b.deleted_at IS NULL", "p.deleted_at IS NULL",
                       "p.product='channel'", "p.status='published'", "p.visibility='public'"):
            assert marker in sql, "Public-only filter missing: " + marker
        if "WHERE p.id=?" in sql:
            return FakeResult([r for r in self.rows if r["id"] == params[0]])
        return FakeResult(self.rows)


class SeoDiscoveryTest(unittest.TestCase):
    def setUp(self):
        self.post = dict(
            id=POST_ID, title="법률 & 금융 <검증>", summary="승인된 공개 뉴스",
            body="자체 편집 콘텐츠.\\n공식 법령 원문을 확인하세요.",
            updated_at="2026-11-04T00:05:00+00:00",
            published_at="2026-11-04T00:01:00+00:00",
            is_sponsored=0,
        )
        self.db = FakeDB([self.post])
        application = FastAPI()

        def database():
            yield self.db

        seo_discovery.register(application, database, "lawygo-demo")
        self.client = TestClient(application)

    def test_robots_contains_absolute_sitemap_and_excludes_api(self):
        r = self.client.get("/robots.txt")
        self.assertEqual(200, r.status_code)
        self.assertIn("text/plain", r.headers["content-type"])
        self.assertIn("Sitemap: https://lawygo.lexid.site/sitemap.xml", r.text)
        self.assertIn("Disallow: /api/", r.text)
        self.assertNotIn("Disallow: /static/", r.text)
        self.assertNotIn("Disallow: /dashboard", r.text)

    def test_sitemap_index_and_public_pages_are_valid_xml(self):
        parent = ET.fromstring(self.client.get("/sitemap.xml").content)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        children = [e.text for e in parent.findall("s:sitemap/s:loc", ns)]
        self.assertEqual([
            "https://lawygo.lexid.site/sitemap-pages.xml",
            "https://lawygo.lexid.site/sitemap-articles.xml",
        ], children)
        pages = ET.fromstring(self.client.get("/sitemap-pages.xml").content)
        urls = [e.text for e in pages.findall("s:url/s:loc", ns)]
        self.assertIn("https://lawygo.lexid.site/", urls)
        self.assertIn("https://lawygo.lexid.site/journal", urls)
        self.assertNotIn("https://lawygo.lexid.site/dashboard", urls)
        self.assertTrue(all(u.startswith("https://lawygo.lexid.site/") for u in urls))
        self.assertEqual(len(urls), len(set(urls)))
        self.assertEqual(len(urls), len(seo_discovery.PUBLIC_PAGES))

    def test_articles_sitemap_uses_real_modification_date(self):
        root = ET.fromstring(self.client.get("/sitemap-articles.xml").content)
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        self.assertEqual("https://lawygo.lexid.site/journal/articles/" + POST_ID,
                         root.find("s:url/s:loc", ns).text)
        self.assertEqual("2026-11-04", root.find("s:url/s:lastmod", ns).text)

    def test_rss_is_first_party_and_xml_safe(self):
        resp = self.client.get("/rss.xml")
        self.assertEqual(200, resp.status_code)
        self.assertIn("application/rss+xml", resp.headers["content-type"])
        feed = ET.fromstring(resp.content)
        self.assertEqual("rss", feed.tag)
        item = feed.find("channel/item")
        self.assertEqual(self.post["title"], item.findtext("title"))
        self.assertEqual("https://lawygo.lexid.site/journal/articles/" + POST_ID,
                         item.findtext("link"))
        self.assertIn("2026", item.findtext("pubDate"))
        self.assertEqual(1, len(feed.findall("channel/item")))

    def test_public_article_escape_and_404(self):
        resp = self.client.get("/journal/articles/" + POST_ID)
        self.assertEqual(200, resp.status_code)
        self.assertIn("법률 &amp; 금융 &lt;검증&gt;", resp.text)
        self.assertNotIn("<검증>", resp.text)
        self.assertIn('<link rel="canonical"', resp.text)
        self.assertEqual(404, self.client.get("/journal/articles/../../dashboard").status_code)
        self.assertEqual(404, self.client.get("/journal/articles/" + "b"*32).status_code)

    def test_empty_rss_contains_no_fabricated_items(self):
        self.db.rows = []
        feed = ET.fromstring(self.client.get("/rss.xml").content)
        self.assertEqual([], feed.findall("channel/item"))
        root = ET.fromstring(self.client.get("/sitemap-articles.xml").content)
        self.assertEqual([], list(root))


if __name__ == "__main__":
    unittest.main()
