"""LAWYGO 2026 delivery acceptance — responsive media and safe empty states."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
PUBLIC = [
    "static/index.html","static/journal.html","static/wiki.html","static/note.html",
    "static/pan.html","static/pro.html","static/channel.html","static/pricing.html",
    "static/partnership.html","static/payment.html","static/strategy.html",
    "static/product.html",
]

def read(path):
    return (ROOT / path).read_text(encoding="utf-8")

def test_delivery_styles_and_images_exist_on_all_pages():
    for page in PUBLIC:
        html=read(page)
        assert 'href="/static/lawygo-delivery-20261103.css?v=20261105-designrefresh3"' in html, page
        assert '<main' in html, page
        for src in re.findall(r'<img\b[^>]*\bsrc=["\'](/static/[^"\']+)["\']', html, re.I):
            assert (ROOT / src.lstrip("/")).is_file(), (page, src)
    css=read("static/lawygo-delivery-20261103.css")
    for required in ("height:152px!important","aspect-ratio:5/3!important",
                     "min-height:44px","@media(max-width:480px)",
                     "prefers-reduced-motion:reduce","lyd-feed-empty"):
        assert required in css

def test_home_has_distinct_real_media_and_clickable_services():
    html=read("static/index.html")
    for src in ("/static/img/channel.webp","/static/img/wiki.webp","/static/img/pan.webp",
                "/static/img/note.webp","/static/img/design/legal-knowledge-city.webp"):
        assert src in html
    for path in ('/journal','/p/wiki','/p/pan','/p/note','/pro'):
        assert f'href="{path}"' in html

def test_journal_empty_feed_is_truthful_and_rss_safe():
    js=read("static/journal-editorial-live.js")
    assert "function journalEmpty(" in js
    assert "journal-wire-kr" in js and "journal-wire-us" in js
    assert "공개된" in js
    assert "function safeJournalUrl(" in js
    assert 'a.innerHTML = `<small>${item.source}' not in js
    assert 'wrap.innerHTML = `<div class="rubric">' not in js
    assert 'source.target="_blank"' not in js

def test_wiki_no_results_are_visual_but_no_private_docs():
    js=read("static/wiki-page.js")
    assert "function wikiEmptyState(" in js
    assert "공개 승인된" in js
    assert '"/static/img/wiki.webp"' in js
    assert "privateCase" not in js

def test_pro_link_opens_external_system_separately():
    html=read("static/pro.html")
    assert 'id="lawygoProStart"' in html
    assert 'href="https://www.lawygo.com/login"' in html
    assert 'target="_blank" rel="noopener noreferrer"' in html

def test_pan_discovery_not_fake_live_when_keys_missing():
    html=read("static/pan.html")
    js=read("static/pan-platform.js")
    assert "pan-feed-status" in html
    assert "실제 게시물" in js or "연결된" in js
    assert "showSourceEmpty" in js
