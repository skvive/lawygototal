"""Contract checks for integrated LAWYGO JOURNAL/WIKI/PAN/PRO/NOTE views.

Tests intentionally require no production credentials or external network.
Real API auth, AI providers, and publication rights must be checked independently.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class FiveServiceIntegrationTest(unittest.TestCase):
    def test_weeklynews_original_brand_and_rss_source(self):
        logo = read("static/img/weeklynews-w.svg")
        self.assertIn('aria-label="위클리뉴스 W 로고"', logo)
        self.assertIn("#B4232B", logo)
        self.assertIn("#22429F", logo)
        journal = read("static/journal.html")
        self.assertNotIn('class="weeklynews-partner"', journal)
        self.assertIn('class="journal-weeklynews-credit"', journal)
        self.assertIn('https://weeklynews.me/', journal)
        self.assertIn('aria-label="기사 제공: 위클리뉴스 공식 사이트 방문"', journal)
        self.assertIn('src="/static/img/weeklynews-w.svg"', journal)
        self.assertNotIn("위클리뉴스 RSS <span", journal)
        from journal_feed import FEEDS
        self.assertTrue(any(x["source"] == "위클리뉴스" and x["url"] == "https://weeklynews.me/feed.xml" for x in FEEDS))

    def test_wiki_native_reader_is_in_page(self):
        wiki = read("static/wiki.html")
        for ident in ("wiki-native-workspace", "lawygoWikiStudioForm", "lawygoWikiStudioResults",
                      "lawygoWikiStudioBody", "lawygoWikiStudioCopy", "lawygoWikiStudioSend"):
            self.assertIn(f'id="{ident}"', wiki)
        self.assertIn('href="#wiki-native-workspace"', wiki)
        self.assertNotIn('target="_blank" rel="noopener noreferrer">고급 법률백과', wiki)

    def test_note_native_editor_reuses_original_handlers(self):
        note = read("static/note.html")
        for ident in ("note-native-workspace", "note-editor", "lawygoNoteImportCitation",
                      "noteDraftTitle", "noteDraftContent"):
            self.assertIn(f'id="{ident}"', note)
        for key in ("blank", "case", "evidence", "research"):
            self.assertIn(f'data-note-start="{key}"', note)
            self.assertIn(f'data-note-template="{key}"', note)

    def test_pan_public_feed_is_legal_only(self):
        from pan_public_feed import _is_legal_topic
        self.assertTrue(_is_legal_topic({"title": "민사소송과 손해배상", "summary": ""}))
        self.assertTrue(_is_legal_topic({"title": "Legal research", "summary": "court proceedings"}))
        self.assertFalse(_is_legal_topic({"title": "패션 룩북과 쇼핑 신상품", "summary": "생활용품 할인과 이벤트"}))
        self.assertFalse(_is_legal_topic({"title": "", "summary": ""}))
        pan = read("static/pan.html")
        self.assertIn('id="pan-legal-live"', pan)
        self.assertIn('id="pan-legal-live-feed"', pan)
        self.assertIn('id="pan-legal-player"', pan)
        self.assertIn('id="pan-legal-player-close"', pan)

    def test_pro_mirrors_official_product_overview_not_private_app(self):
        pro = read("static/pro.html")
        for ident in ("pro-source-home", "pro-source-title", "pro-features", "pro-ai", "pro-login"):
            self.assertIn(f'id="{ident}"', pro)
        self.assertIn("대한민국 법원", pro)
        self.assertIn("https://www.lawygo.com/", pro)
        self.assertNotIn("123-45-67890", pro)

    def test_shared_static_assets_present_and_no_private_data_sync(self):
        css = read("static/lawygo-service-integration-20261105.css")
        script = read("static/lawygo-service-integration-20261105.js")
        self.assertIn(".journal-weeklynews-credit-link", css)
        self.assertNotIn(".weeklynews-partner{", css)
        self.assertIn(".lnw-grid", css)
        self.assertIn("@media(max-width:700px)", css)
        self.assertIn("lawygo_public_research_v1", script)
        self.assertIn("/api/wiki/search", script)
        self.assertIn("/api/pan/content", script)
        self.assertIn("youtube-nocookie.com/embed/", script)
        self.assertNotIn("innerHTML", script)
        for path in ("journal", "wiki", "pan", "note", "pro"):
            html = read(f"static/{path}.html")
            self.assertIn('href="/static/lawygo-service-integration-20261105.css"', html)
        for path in ("wiki", "pan", "note"):
            self.assertIn('src="/static/lawygo-service-integration-20261105.js"', read(f"static/{path}.html"))


if __name__ == "__main__":
    unittest.main()
