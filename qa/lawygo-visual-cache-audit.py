"""Static contract for cached LAWYGO design releases. No network requests."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
pages=("index","journal","wiki","note","pro","pan","channel","pricing","partnership","payment","strategy","dashboard","product")
for name in pages:
    html=(root/"static"/(name+".html")).read_text(encoding="utf-8")
    assert html.count('lawygo-design-fix-20261104.css')==1, name
    assert "lawygo-design-fix-20261104.css?v=" in html, name
    assert "20261105-designrefresh3" in html, name
    assert 'name="lawygo-design-revision" content="20261105-designrefresh3"' in html, name
    assert r'\n</head>' not in html, "Literal escaped newline before head close: "+name
css=(root/"static/lawygo-design-fix-20261104.css").read_text(encoding="utf-8")
home=(root/"static/index.html").read_text(encoding="utf-8")
assert 'class="hero-bg hero-global"' in home and 'class="ly-catalog"' in home, "Compact homepage needs hero and one service catalogue."
assert home.count('class="ly-catalog-body"') == 5, "Exactly five service cards must remain."
assert 'class="product-grid"' not in home and 'class="home-bridge"' not in home, "Duplicate service sections must remain removed."
assert "lawygo-hero-premium-20261104.webp" in css, "Editorial image CSS fallback missing."
assert 'max-width:680px' in css
assert 'legal-knowledge-city.webp' in css
wiki=(root/"static/wiki.html").read_text(encoding="utf-8")
assert 'id="lawygo-wiki-dashboard"' in wiki
assert 'id="lw26-editor"' in wiki
assert 'id="lw26-searchform"' in wiki
assert 'data-brand-shell="header"' in wiki
assert '<section class="hero hero-dark">' not in wiki
assert 'id="wiki-native-workspace"' not in wiki
cfg=json.loads((root/"vercel.json").read_text(encoding="utf-8"))
pages_routes=[r for r in cfg["routes"] if r.get("dest","").endswith(".html")]
assert len(pages_routes)==13
assert all("no-store" in r["headers"]["Cache-Control"] for r in pages_routes)
assert all(r["headers"].get("X-Lawygo-Design-Release") == "20261105-designrefresh3" for r in pages_routes)
assets_route=next(r for r in cfg["routes"] if r["src"]=="/static/(.*)")
assert "s-maxage=0" in assets_route["headers"]["Cache-Control"]
assert "stale-while-revalidate" not in assets_route["headers"]["Cache-Control"]
assert assets_route["headers"].get("X-Lawygo-Design-Release") == "20261105-designrefresh3"
assert cfg["regions"]==["sin1"]
# Old unversioned styles and scripts can indefinitely survive inside mobile webviews.
import re
for name in pages:
    html=(root/"static"/(name+".html")).read_text(encoding="utf-8")
    refs=re.findall(r'(?:href|src)="(/static/[^"]+\.(?:css|js)(?:\?[^"]*)?)"', html)
    assert len(refs)>=5, (name, refs)
    assert all(("?v=" in url and "20261105-designrefresh3" in url) for url in refs), (name, refs)

assert cfg["routes"][-2]=={"src":"/api/(.*)","dest":"app.py"}
print("Design release contract pass: 13 pages + fresh CDN release + WIKI navigation")

# Final WIKI presentation: a technical knowledge graphic rather than repeated portrait.
assert "editorial-library-20261102.webp" not in wiki
assert 'css?v=wiki-ui2' in wiki
assert '/static/img/design/lawygo-wiki-study-20261110.svg' in wiki
assert "lawygo-wiki-editor-20261110.js" in wiki
assert "lawygo-wiki-editor-20261110.css" in wiki
assert (root/"static/img/design/lawygo-wiki-study-20261110.svg").exists()
assert (root/"static/lawygo-wiki-editor-20261110.js").exists()
pro=(root/"static/pro.html").read_text(encoding="utf-8")
assert pro.count('id="lawygoProStart"') == 1
assert 'href="https://www.lawygo.com/login" target="_blank" rel="noopener noreferrer"' in pro
assert (root/"static/img/design/lawygo-pro-hero-20261110.svg").exists()
