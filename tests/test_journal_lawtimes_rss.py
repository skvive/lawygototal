"""RSS headline-only LawTimes integration regression tests."""
from journal_feed import FEEDS, _parse_rss

LEGAL = next(feed for feed in FEEDS if feed["source"] == "법률신문")

def test_lawtimes_feed_is_registered():
    assert LEGAL["region"] == "legal"
    assert LEGAL["url"] == "https://cdn.lawtimes.co.kr/rss/gn_rss_allArticle.xml"

def test_lawtimes_headline_and_original_url_only():
    xml = """<rss><channel><item><title>주요 판례 &amp; 법조 소식</title>
        <link>https://www.lawtimes.co.kr/news/12345</link>
        <description>원문을 재게시하지 않는 요약</description>
        <pubDate>Tue, 03 Nov 2026 09:00:00 GMT</pubDate></item></channel></rss>"""
    items = _parse_rss(xml, LEGAL)
    assert len(items) == 1
    assert items[0]["title"] == "주요 판례 & 법조 소식"
    assert items[0]["source"] == "법률신문"
    assert items[0]["url"] == "https://www.lawtimes.co.kr/news/12345"
    assert items[0]["kind"] == "wire"
    assert "body" not in items[0]

def test_lawtimes_does_not_accept_untrusted_external_or_script_links():
    xml = """<rss><channel>
      <item><title>Bad site</title><link>https://example.com/news</link></item>
      <item><title>Bad scheme</title><link>javascript:alert(1)</link></item>
      <item><title>LawTimes article</title><link>https://m.lawtimes.co.kr/news/123</link></item>
    </channel></rss>"""
    items = _parse_rss(xml, LEGAL)
    assert [item["title"] for item in items] == ["LawTimes article"]
