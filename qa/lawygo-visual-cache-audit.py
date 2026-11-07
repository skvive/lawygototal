"""LAWYGO release check: all public assets, no-store headers and workspace-first IA."""
import json,re
from pathlib import Path
root=Path(__file__).resolve().parents[1]
rel=json.loads((root/"static/design-release.json").read_text())["release"]
pages=("index","journal","wiki","note","pro","pan","channel","pricing","partnership","payment","strategy","dashboard","product")
for n in pages:
    src=(root/f"static/{n}.html").read_text(encoding="utf-8")
    assert f'name="lawygo-design-revision" content="{rel}"' in src,n
    refs=re.findall(r'(?:href|src)="(/static/[^"]+\.(?:css|js)(?:\?[^"]*)?)"',src)
    assert len(refs)>=4,(n,refs)
    assert all(f"?v={rel}" in r for r in refs),(n,refs)
cfg=json.loads((root/"vercel.json").read_text(encoding="utf-8"))
routes=[r for r in cfg["routes"] if r.get("dest","").endswith(".html")]
assert len(routes)==13
assert all("no-store" in r["headers"]["Cache-Control"] and r["headers"]["X-Lawygo-Design-Release"]==rel for r in routes)
assert cfg["routes"][-2]=={"src":"/api/(.*)","dest":"app.py"}
assert cfg["routes"][-1]=={"src":"/(.*)","dest":"app.py"}
assert cfg["regions"]==["sin1"]
home=(root/"static/index.html").read_text(encoding="utf-8")
wiki=(root/"static/wiki.html").read_text(encoding="utf-8")
note=(root/"static/note.html").read_text(encoding="utf-8")
nav=(root/"static/brand-shell.js").read_text(encoding="utf-8")
assert home.count('class="lx-feature"')==4
assert "/journal" not in home and "/journal" not in nav
assert 'lawygo-hero-premium-20261104.webp' in home
assert wiki.index('id="wiki-native-workspace"')<wiki.index('id="wiki-results"')
assert note.index('id="note-native-workspace"')<note.index('id="note-editor"')
assert "lawygoWikiStudioForm" in wiki and "noteDraftContent" in note
print("PASS: 13 public routes, cache control, assets, direct WIKI and NOTE workspaces")
