"""Static contract for cached LAWYGO design releases. No network requests."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
pages=("index","journal","wiki","note","pro","pan","channel","pricing","partnership","payment","strategy","dashboard","product")
for name in pages:
    html=(root/"static"/(name+".html")).read_text(encoding="utf-8")
    assert html.count('lawygo-design-fix-20261104.css')==1, name
    assert 'name="lawygo-design-revision" content="20261104-ui1"' in html, name
    assert r'\n</head>' not in html, "Literal escaped newline before head close: "+name
css=(root/"static/lawygo-design-fix-20261104.css").read_text(encoding="utf-8")
home=(root/"static/index.html").read_text(encoding="utf-8")
assert 'height="800" loading="eager"' in home, "Editorial artwork must load before showing empty space."
assert "lawygo-hero-premium-20261104.webp" in css, "Editorial image CSS fallback missing."
assert 'max-width:680px' in css
assert 'legal-knowledge-city.webp' in css
wiki=(root/"static/wiki.html").read_text(encoding="utf-8")
assert wiki.index('wiki-knowledge-section')<wiki.index('class="ly-premiere"')
assert 'href="#wiki-search-form"' in wiki
cfg=json.loads((root/"vercel.json").read_text(encoding="utf-8"))
pages_routes=[r for r in cfg["routes"] if r.get("dest","").endswith(".html")]
assert len(pages_routes)==13
assert all("s-maxage=30" in r["headers"]["Cache-Control"] for r in pages_routes)
assets_route=next(r for r in cfg["routes"] if r["src"]=="/static/(.*)")
assert "s-maxage=120" in assets_route["headers"]["Cache-Control"]
assert cfg["regions"]==["sin1"]
assert cfg["routes"][-2]=={"src":"/api/(.*)","dest":"app.py"}
print("Design release contract pass: 13 pages + cache/region + WIKI navigation")

# Final WIKI presentation: a technical knowledge graphic rather than repeated portrait.
assert "editorial-library-20261102.webp" not in wiki
assert 'css?v=wiki-ui2' in wiki
assert '/static/img/design/ly-wiki-scene.svg' in wiki
assert "media-wiki-links" in css and "media-wiki-review" in css
assert (root/"static/img/design/ly-wiki-scene.svg").exists()
