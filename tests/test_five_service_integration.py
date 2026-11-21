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
        for ident in ("view-dashboard", "view-search", "view-article", "wikiResults",
                      "wikiSearchInput", "wikiArticleBody", "wikiArticleSource", "wikiArticleNotice"):
            self.assertIn(f'id="{ident}"', wiki)
        self.assertIn('data-view-link="search"', wiki)
        self.assertIn('https://law.go.kr/', wiki)
        self.assertNotIn("wiki-native-workspace", wiki)

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

    def test_pro_korean_guide_preserves_external_product_link(self):
        pro = read("static/pro.html")
        for ident in ("pro-title", "main-content", "pro-ko-guide-heading"):
            self.assertIn(f'id="{ident}"', pro)
        self.assertIn("한국어 사용 안내", pro)
        self.assertIn("송무관리 프로그램", pro)
        self.assertIn("https://www.lawygo.com/", pro)
        self.assertIn("https://lawygo.com", pro)
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
        for path in ("journal", "pan", "note"):
            html = read(f"static/{path}.html")
            self.assertIn('href="/static/lawygo-service-integration-20261105.css?v=20261121-pan-note-ko-v13"', html)
        for path in ("pan", "note"):
            self.assertIn('src="/static/lawygo-service-integration-20261105.js?v=20261121-pan-note-ko-v13"', read(f"static/{path}.html"))
        wiki = read("static/wiki.html")
        self.assertIn('src="/static/lawygo-wiki-restored-20261111.js?v=20261121-pan-note-ko-v13"', wiki)


    def test_journal_excludes_business_announcements_but_keeps_legal_news(self):
        from journal_feed import is_business_announcement, editorial_from_posts, _parse_rss

        blocked = [
            "[경기] 화성시 2026년 제4회 중소기업대상 추가모집 공고",
            "[경남] 함양군 2026년 소규모 사업장 방지시설 설치 지원사업 공고",
            "2026년 강원연구개발특구육성 R&D사업 창업기업 모집 공고",
            "서울시 소상공인 지원금 신청 안내",
            "스타트업 대상 입주기업 선발 공고",
            "중소기업 창업 바우처 사업 참여 신청 접수",
        ]
        kept = [
            "지원사업 보조금 환수처분 취소소송 대법원 판결",
            "소상공인 지원금 관련 헌법재판소 위헌 결정",
            "공정거래법 개정과 기업 준법감시 실무",
            "연방공개시장위원회 통화정책 회의록 공개",
            "중소기업 금융환경 분석 및 경제 전망",
        ]
        for title in blocked:
            with self.subTest(blocked=title):
                self.assertTrue(is_business_announcement({"title": title}))
        for title in kept:
            with self.subTest(kept=title):
                self.assertFalse(is_business_announcement({"title": title}))

        rows = [
            {"id": str(index), "title": title, "summary": title, "updated_at": "2026-11-21"}
            for index, title in enumerate(blocked + kept)
        ]
        filtered = editorial_from_posts(rows)
        self.assertEqual(len(filtered), len(kept))
        self.assertEqual([item["title"] for item in filtered], kept)

        # The first 20 RSS entries are announcements. A valid legal report
        # further down the feed must still reach the front page.
        from xml.sax.saxutils import escape
        xml = "<rss><channel>" + "".join(
            "<item><title>" + escape(title) + "</title>"
            "<link>https://example.org/story/" + str(i) + "</link>"
            "<description>Official publisher summary</description></item>"
            for i, title in enumerate(blocked * 4 + kept)
        ) + "</channel></rss>"
        wire = _parse_rss(xml, {"source": "검증 매체", "region": "kr", "desk": "법률"})
        self.assertEqual([item["title"] for item in wire], kept)
        self.assertFalse(any(is_business_announcement(item) for item in wire))


if __name__ == "__main__":
    unittest.main()
