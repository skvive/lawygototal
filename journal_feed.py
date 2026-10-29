"""Aggregate licensed RSS headlines for LAWYGO Journal (title, summary, link, source)."""
from __future__ import annotations

import re
import time
import xml.etree.ElementTree as ET
from html import unescape
from typing import Any

import httpx

_CACHE: dict[str, Any] = {"at": 0.0, "items": []}
_TTL = 900  # 15 min

FEEDS = (
    {"source": "연합뉴스", "region": "kr", "desk": "한국 경제·정책", "url": "https://www.yna.co.kr/rss/economy.xml"},
    {"source": "연합뉴스", "region": "kr", "desk": "한국 종합", "url": "https://www.yna.co.kr/rss/news.xml"},
    {"source": "한국경제", "region": "kr", "desk": "국내 증시·경제", "url": "https://www.hankyung.com/feed/economy"},
    {"source": "BBC", "region": "us", "desk": "U.S. & Americas", "url": "https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml"},
    {"source": "NPR", "region": "us", "desk": "U.S. Business", "url": "https://feeds.npr.org/1019/rss.xml"},
    {"source": "Reuters", "region": "us", "desk": "Global Markets", "url": "https://www.reutersagency.com/feed/?taxonomy=best-topics&post_type=best"},
)

UA = {"User-Agent": "LAWYGO-Journal/1.0 (+https://lawygo.lexid.site/journal)"}


def _strip_html(s: str) -> str:
    s = unescape(re.sub(r"<[^>]+>", " ", s or ""))
    return re.sub(r"\s+", " ", s).strip()[:480]


def _parse_rss(xml_text: str, meta: dict) -> list[dict]:
    items: list[dict] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return items
    channel = root.find("channel")
    nodes = channel.findall("item") if channel is not None else root.findall(".//item")
    for node in nodes[:12]:
        title = _strip_html(node.findtext("title") or "")
        link = (node.findtext("link") or "").strip()
        desc = _strip_html(node.findtext("description") or node.findtext("{http://purl.org/rss/1.0/modules/content/}encoded") or "")
        pub = (node.findtext("pubDate") or node.findtext("published") or "")[:31]
        if not title or not link:
            continue
        items.append(
            {
                "title": title,
                "summary": desc or title,
                "url": link,
                "published": pub,
                "source": meta["source"],
                "region": meta["region"],
                "desk": meta["desk"],
                "kind": "wire",
            }
        )
    return items


async def _fetch_one(client: httpx.AsyncClient, meta: dict) -> list[dict]:
    try:
        r = await client.get(meta["url"], headers=UA, timeout=20.0)
        r.raise_for_status()
        return _parse_rss(r.text, meta)
    except Exception:
        return []


async def load_wire_items() -> list[dict]:
    now = time.time()
    if _CACHE["items"] and now - _CACHE["at"] < _TTL:
        return _CACHE["items"]
    merged: list[dict] = []
    async with httpx.AsyncClient(follow_redirects=True) as client:
        for meta in FEEDS:
            merged.extend(await _fetch_one(client, meta))
    # de-dupe by title prefix
    seen: set[str] = set()
    out: list[dict] = []
    for it in merged:
        key = it["title"][:80].lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(it)
    _CACHE["at"] = now
    _CACHE["items"] = out
    return out


def editorial_from_posts(rows: list[dict]) -> list[dict]:
    out = []
    for r in rows:
        out.append(
            {
                "title": r.get("title") or "",
                "summary": r.get("summary") or "",
                "url": f"/api/posts/{r['id']}" if r.get("id") else "/p/channel",
                "published": (r.get("updated_at") or "")[:10],
                "source": "LAWYGO 편집국",
                "region": "editorial",
                "desk": r.get("kind") or "인사이트",
                "kind": "editorial",
                "post_id": r.get("id"),
            }
        )
    return out
