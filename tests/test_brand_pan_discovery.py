"""Read-only PAN API integration and front-end design contract tests."""
import asyncio
import os
import re
from pathlib import Path

import pan_discovery_v2 as discovery

ROOT=Path(__file__).resolve().parents[1]

def test_discovery_disabled_without_keys(monkeypatch):
    monkeypatch.delenv("LAWYGO_PAN_YOUTUBE_API_KEY",raising=False)
    monkeypatch.delenv("LAWYGO_PAN_BLOGGER_API_KEY",raising=False)
    monkeypatch.delenv("LAWYGO_PAN_BLOGGER_IDS",raising=False)
    discovery._CACHE.clear()
    assert asyncio.run(discovery.public_search())==[]

def test_youtube_video_classification_is_conservative():
    sample={"id":{"videoId":"AbCdEf12345"},"snippet":{
        "title":"변호사 사건 분석 실무 설명","description":"법률 핵심 쟁점","publishedAt":"2026-11-01T10:00:00Z","channelTitle":"법률 실무 연구"}}
    video=discovery._youtube_item(sample)
    assert video["content_type"]=="video"
    assert video["url"]=="https://www.youtube.com/watch?v=AbCdEf12345"
    sample["snippet"]["title"]="#shorts 변호사 법률 상식"
    assert discovery._youtube_item(sample)["content_type"]=="shorts"
    sample["id"]["videoId"]="not-a-real-id"
    assert discovery._youtube_item(sample) is None

def test_blogger_whitelists_public_https_links(monkeypatch):
    monkeypatch.delenv("LAWYGO_PAN_BLOGGER_ALLOWED_HOSTS",raising=False)
    item={"id":"post-012","title":"변호사 판례 해설","content":"민사소송 절차",
        "url":"https://lawexample.blogspot.com/2026/11/post.html","published":"2026-11-02T00:00:00Z"}
    assert discovery._blogger_item(item)["content_type"]=="blog"
    item["url"]="https://lawexample.blogspot.com.evil.example/steal"
    assert discovery._blogger_item(item) is None
    item["url"]="http://lawexample.blogspot.com/post.html"
    assert discovery._blogger_item(item) is None
    item["url"]="https://lawexample.blogspot.com/post.html"
    item["title"]="일반요리레시피"
    item["content"]="비법 양념"
    assert discovery._blogger_item(item) is None

def test_service_routes_have_assets_and_layout():
    pages={
        "static/index.html":"ly-total-scene.svg",
        "static/journal.html":"ly-journal-scene.svg",
        "static/pan.html":"ly-pan-scene.svg",
        "static/note.html":"ly-note-scene.svg",
        "static/wiki.html":"ly-wiki-scene.svg",
        "static/pro.html":"ly-pro-scene.svg",
        "static/channel.html":"ly-journal-scene.svg",
        "static/pricing.html":"ly-total-scene.svg",
        "static/partnership.html":"ly-pan-scene.svg",
        "static/strategy.html":"ly-total-scene.svg",
        "static/payment.html":"ly-pro-scene.svg",
    }
    for page,asset in pages.items():
        content=(ROOT/page).read_text(encoding="utf-8")
        assert "lawygo-refined-20261103.css" in content,page
        assert asset in content,page
        assert (ROOT/"static/img/design"/asset).exists(),asset
    css=(ROOT/"static/lawygo-refined-20261103.css").read_text(encoding="utf-8")
    assert "@media(max-width:720px)" in css
    assert "prefers-reduced-motion" in css

def test_pan_ui_refresh_and_external_links_are_safe():
    js=(ROOT/"static/pan-platform.js").read_text(encoding="utf-8")
    html=(ROOT/"static/pan.html").read_text(encoding="utf-8")
    assert 'fetchContent("all", q)' in js
    assert 'pan-refresh-feed' in html and 'pan-feed-status' in html
    assert js.count('pan-refresh-feed')==1
    assert 'panTrack(L.id, "profile_open");\n    const end' not in js
    assert "target=\"_blank\"" not in js or "noopener noreferrer" in js
    assert 'LAWYGO_PAN_YOUTUBE_API_KEY' in (ROOT/"pan_discovery_v2.py").read_text(encoding="utf-8")
