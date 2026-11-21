"""LAWYGO v12 journal restoration and text-first wiki integrity audit."""
import json
import re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
release=json.loads((ROOT/"static/design-release.json").read_text(encoding="utf-8"))["release"]
pages=("index","journal","wiki","note","pro","pan","channel","pricing","partnership","payment","strategy","dashboard","product")
asset=re.compile(r"""(?:href|src)=["'](/static/[^"'\s<>]+\.(?:css|js)(?:\?[^"'\s<>]+)?)["']""")
for name in pages:
    html=(ROOT/"static"/f"{name}.html").read_text(encoding="utf-8")
    assert html.count('name="lawygo-design-revision"')==1,name
    assert f'name="lawygo-design-revision" content="{release}"' in html,name
    assets=asset.findall(html)
    assert len(assets)>=2,(name,len(assets))
    assert len(assets)==len(set(assets)),f"Duplicate CSS/JS: {name}"
    assert all("?v=" in a and release in a for a in assets),(name,assets)
    assert r"\n</head>" not in html, f"Literal escaped newline: {name}"
journal=(ROOT/"static/journal.html").read_text(encoding="utf-8")
assert all(f'id="{x}"' in journal for x in
    ("journal-front-left","journal-lead","journal-right","journal-wire-kr","journal-wire-us",
     "journal-row-editors","journal-row-law","newsletterSignupJournal","journal-issue-overlay"))
assert 'front-grid' in journal
assert 'class="navline"' in journal
assert "reference-search-form" not in journal
script=(ROOT/"static/journal-editorial-live.js").read_text(encoding="utf-8")
assert "/api/journal/feed" in script
assert "journal-front-left" in script and "openIssue" in script
assert "journal-issue-close" in script
wiki=(ROOT/"static/wiki.html").read_text(encoding="utf-8")
assert 'class="wiki-reference-v12"' in wiki
assert all(f'id="{x}"' in wiki for x in
       ("wikiHomeQuery","wikiLatestList","wikiResults","wikiStatPublished","wikiArticleTitle","wikiArticleBody"))
assert "wref-topic-index" in wiki
assert "wstats" not in wiki
assert 'data-article="lease"' in wiki
css=(ROOT/"static/lawygo-wiki-restored-20261111.css").read_text(encoding="utf-8")
assert "body.wiki-reference-v12" in css
pan_page=(ROOT/"static/pan.html").read_text(encoding="utf-8")
note_page=(ROOT/"static/note.html").read_text(encoding="utf-8")
portal_css=(ROOT/"static/lawygo-editorial-portal-v8.css").read_text(encoding="utf-8")
assert "법률 영상·전문가 콘텐츠" in pan_page
assert "법률자료 검색과 문서 정리" in note_page
assert note_page.index('id="note-editor"') < note_page.index('id="ly-note-ai"')
assert "Korean-first PAN / text-first NOTE" in portal_css
pan=(ROOT/"static/pan-published-v2-20261108.js").read_text(encoding="utf-8")
assert "summary_ko" in pan and "영문 원문 한국어 자동번역" in pan
pro=(ROOT/"static/pro.html").read_text(encoding="utf-8")
assert "한국어 사용 안내" in pro and "공식 PRO 프로그램에서 확인" in pro
config=json.loads((ROOT/"vercel.json").read_text(encoding="utf-8"))
routes=config["routes"]
assert len([x for x in routes if x.get("dest","").endswith(".html")])==13
for route in routes:
    if route.get("dest","").endswith(".html"):
        assert "no-store" in route["headers"]["Cache-Control"]
        assert route["headers"]["X-Lawygo-Design-Release"]==release
static=next(x for x in routes if x["src"]=="/static/(.*)")
assert "max-age=0" in static["headers"]["Cache-Control"]
assert static["headers"]["X-Lawygo-Design-Release"]==release
assert routes[-2:]==[{"src":"/api/(.*)","dest":"app.py"},{"src":"/(.*)","dest":"app.py"}]
print(f"PASS: {len(pages)} pages, restored editorial JOURNAL, text-first WIKI, Korean-first PAN and NOTE, CDN version {release}")
