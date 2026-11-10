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

    def test_wiki_single_dashboard_and_editor(self):
        wiki = read("static/wiki.html")
        self.assertIn('id="lawygo-wiki-dashboard"', wiki)
        self.assertIn('id="lw26-editor"', wiki)
        self.assertIn('id="lw26-edit-toggle"', wiki)
        self.assertIn('id="lw26-searchform"', wiki)
        self.assertIn('lawygo-wiki-editor-20261110.js', wiki)
        self.assertNotIn('id="wiki-native-workspace"', wiki)
        self.assertNotIn('class="hero hero-dark"', wiki)
        self.assertIn('data-brand-shell="header"', wiki)
        editor = read("static/lawygo-wiki-editor-20261110.js")
        for marker in ("localStorage", "pointerdown", "dragstart", "maximized", "minimized", "lw26-editor-save"):
            self.assertIn(marker, editor)

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

    def test_pro_single_hero_official_login(self):
        pro = read("static/pro.html")
        self.assertIn('id="lawygoProHero"', pro)
        self.assertIn('id="lawygoProStart"', pro)
        self.assertIn('href="https://www.lawygo.com/login"', pro)
        self.assertIn('target="_blank" rel="noopener noreferrer"', pro)
        self.assertIn('/static/img/design/lawygo-pro-hero-20261110.svg', pro)
        self.assertNotIn('id="pro-program-map"', pro)
        self.assertNotIn('id="pro-features"', pro)
        self.assertNotIn("123-45-67890", pro)

    def test_note_removes_marketing_but_keeps_working_document_editor(self):
        note = read("static/note.html")
        self.assertNotIn('class="ly-premiere"', note)
        self.assertNotIn('id="note-ai-tools"', note)
        for marker in ('id="note-chat-workspace"', 'id="note-native-workspace"', 'id="note-editor"'):
            self.assertIn(marker, note)

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
            self.assertIn('href="/static/lawygo-service-integration-20261105.css?v=20261105-designrefresh3"', html)
        for path in ("pan", "note"):
            self.assertIn('src="/static/lawygo-service-integration-20261105.js?v=20261105-designrefresh3"', read(f"static/{path}.html"))
        self.assertIn("lawygo-wiki-editor-20261110.js", read("static/wiki.html"))


if __name__ == "__main__":
    unittest.main()
