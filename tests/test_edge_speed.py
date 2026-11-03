"""Guard CDN-first routing and prevent regression to serialized public RSS.
No external requests or production database mutations.
"""
from __future__ import annotations

import asyncio
import json
from pathlib import Path

import journal_feed

ROOT=Path(__file__).resolve().parents[1]

PUBLIC={
  "/":"index.html","/journal":"journal.html","/channel":"channel.html",
  "/pro":"pro.html","/pricing":"pricing.html","/payment":"payment.html",
  "/partnership":"partnership.html","/strategy":"strategy.html",
  "/dashboard":"dashboard.html","/p/wiki":"wiki.html",
  "/p/pan":"pan.html","/p/note":"note.html","/p/channel":"product.html",
}

def test_static_public_routes_avoid_function_startup():
    cfg=json.loads((ROOT/"vercel.json").read_text(encoding="utf-8"))
    routes=cfg["routes"]
    resolved={r["src"]:r["dest"] for r in routes}
    for path,source in PUBLIC.items():
        assert resolved[path]=="/static/"+source
        assert (ROOT/"static"/source).exists()
    assert routes[0]["src"]=="/static/(.*)"
    assert routes[-2]=={"src":"/api/(.*)","dest":"app.py"}
    assert routes[-1]=={"src":"/(.*)","dest":"app.py"}
    assert all(r.get("headers",{}).get("Cache-Control","").startswith("public") for r in routes if r["src"] in PUBLIC)

def test_journal_sources_are_bounded_and_parallel(monkeypatch):
    journal_feed._CACHE.update(at=0.0,items=[])
    concurrent=0
    peak=0
    calls=0
    async def stub(_client,meta):
        nonlocal concurrent,peak,calls
        calls+=1
        concurrent+=1
        peak=max(peak,concurrent)
        await asyncio.sleep(.035)
        concurrent-=1
        return [{"title":meta["source"]+meta["desk"],"region":meta["region"],"source":meta["source"]}]
    monkeypatch.setattr(journal_feed,"_fetch_one",stub)
    results=asyncio.run(journal_feed.load_wire_items())
    assert peak>=2,"RSS must load concurrently to avoid N × timeout"
    assert calls==len(journal_feed.FEEDS)
    assert len(results)==len(journal_feed.FEEDS)
    assert asyncio.run(journal_feed.load_wire_items())==results
    assert calls==len(journal_feed.FEEDS),"Warm cache should avoid all upstream calls"

def test_journal_empty_feed_is_cached_for_short_period(monkeypatch):
    journal_feed._CACHE.update(at=0.0,items=[])
    count=0
    async def empty(_client,meta):
        nonlocal count
        count+=1
        return []
    monkeypatch.setattr(journal_feed,"_fetch_one",empty)
    assert asyncio.run(journal_feed.load_wire_items())==[]
    assert asyncio.run(journal_feed.load_wire_items())==[]
    assert count==len(journal_feed.FEEDS)

def test_hero_preload_matches_final_background():
    html=(ROOT/"static/index.html").read_text(encoding="utf-8")
    css=(ROOT/"static/lawygo-mobile-visual-20261102.css").read_text(encoding="utf-8")
    assert 'href="/static/img/design/hero-sunset-20261102.webp"' in html
    assert "hero-sunset-20261102.webp" in css
    assert (ROOT/"static/img/design/hero-sunset-20261102.webp").stat().st_size < 100*1024

def test_no_cdn_cache_for_authenticated_apis():
    cfg=json.loads((ROOT/"vercel.json").read_text(encoding="utf-8"))
    assert cfg["routes"][-2]["src"]=="/api/(.*)"
    for r in cfg["routes"]:
        if r["src"].startswith("/api/"):
            assert "s-maxage" not in r.get("headers",{}).get("Cache-Control","")
    import inspect,app
    src=inspect.getsource(app.journal_feed_api)
    assert 'response.headers["Cache-Control"]' in src
    assert "p.visibility='public'" in src
