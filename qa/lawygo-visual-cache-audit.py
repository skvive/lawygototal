"""LAWYGO v11 public page design release and reference search integrity audit."""
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
    ("reference-search-form","reference-query","reference-topics","reference-results","reference-items","reference-count","newsletterSignupJournal"))
assert 'front-grid' not in journal
assert 'class="navline"' not in journal
assert '<h1 id="reference-heading">경제·법률 자료 검색</h1>' in journal
script=(ROOT/"static/journal-editorial-live.js").read_text(encoding="utf-8")
assert "/api/journal/feed" in script
assert "reference-items" in script and "data-reference-topic" in script
assert "translate.google.com" in script
assert "textContent" in script
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
print(f"PASS: {len(pages)} pages, search-first library, PAN/PRO Korean copy, CDN version {release}")
