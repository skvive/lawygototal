"""Delivery acceptance for current editorial release: actual assets, link safety, empty states."""
from pathlib import Path
import re
import json
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
PUBLIC=["static/"+p+".html" for p in ("index","journal","wiki","note","pan","pro","channel","pricing","partnership","strategy","payment","product")]
def read(path): return (ROOT/path).read_text(encoding="utf-8")

def test_delivery_styles_and_images_exist_on_all_pages():
    release=json.loads(read("static/design-release.json"))["release"]
    for page in PUBLIC:
        html=read(page)
        assert '<main' in html,page
        assets=re.findall(r'(?:href|src)="(/static/[^"]+\.(?:css|js))\?v=([^"]+)"',html)
        assert assets,page
        for path,version in assets:
            assert release in version and (ROOT/path.lstrip("/")).is_file(),(page,path)
        for src in re.findall(r'<img\b[^>]*\bsrc=["\'](/static/[^"\']+)["\']',html,re.I):
            assert (ROOT/src.split("?")[0].lstrip("/")).is_file(),(page,src)
    css=read("static/lawygo-delivery-20261103.css")
    for required in ("height:152px!important","aspect-ratio:5/3!important","min-height:44px","@media(max-width:480px)","prefers-reduced-motion:reduce","lyd-feed-empty"):
        assert required in css

def test_home_has_distinct_real_media_and_clickable_services():
    html=read("static/index.html")
    css=read("static/lawygo-editorial-portal-v8.css")
    for src in ("/static/img/design/lawygo-journal-courthouse-hero-20261121.webp","/static/img/design/lawygo-pro-v6.webp"):
        assert src in html
        assert (ROOT/src.lstrip("/")).is_file()
    assert "lawygo-journal-courthouse-hero-20261121.webp" in css
    links={urlsplit(x).path for x in re.findall(r'href="([^"]+)"',html)}
    assert {"/journal","/p/wiki","/p/pan","/p/note","/pro"}<=links

def test_journal_empty_feed_is_truthful_and_rss_safe():
    js=read("static/journal-editorial-live.js")
    assert "function showSourceSection(" in js
    assert "journal-wire-kr" in js and "journal-wire-us" in js
    assert "현재 표시할 검증된 대표 이미지가 포함된 뉴스와이어 기사가 없습니다" in js
    assert "function safeJournalUrl(" in js and "u.protocol==='https:'" in js
    assert ".filter(x=>x.image)" in js
    assert 'a.innerHTML = `<small>${item.source}' not in js
    assert 'wrap.innerHTML = `<div class="rubric">' not in js

def test_wiki_no_results_are_visual_but_no_private_docs():
    js=read("static/wiki-page.js")
    assert "function wikiEmptyState(" in js
    assert "공개 승인된" in js
    assert '"/static/img/wiki.webp"' in js
    assert "privateCase" not in js

def test_pro_link_opens_external_system_separately():
    html=read("static/pro.html")
    assert 'href="https://lawygo.com" target="_blank" rel="noopener noreferrer"' in html
    assert 'href="https://www.lawygo.com/" target="_blank" rel="noopener noreferrer"' in html

def test_pan_discovery_not_fake_live_when_keys_missing():
    html=read("static/pan.html")
    js=read("static/pan-published-v2-20261108.js")
    assert 'id="pan-real-post-count"' in html
    assert "실제 생방송 상태를 의미하지 않습니다" in html
    assert "연결된 실제 게시물이 없습니다." in js
    assert "공개 원문 연결에 실패했습니다." in js
    assert "소스 연결 확인 필요" in js
