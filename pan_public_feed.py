"""Public PAN wire: Blogger JSON + YouTube RSS (Linkr discover/feed.ts port). Server-only fetch."""
from __future__ import annotations

import json
import os
import re
import time
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from urllib.parse import urlparse

import httpx

UA = "LAWYGO-PAN/1.0 (+https://lawygo.lexid.site/p/pan)"
_CACHE: dict[str, tuple[float, list[dict]]] = {}
TTL = 900


class _Strip(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._p: list[str] = []

    def handle_data(self, data):
        self._p.append(data)

    def text(self) -> str:
        return " ".join(" ".join(self._p).split())


def _strip_html(html: str, n: int = 160) -> str:
    p = _Strip()
    p.feed(re.sub(r"(?is)<(script|style)[^>]*>.*?</\1>", " ", html or ""))
    t = p.text()
    return t if len(t) <= n else t[: n - 1] + "…"


def _upscale_thumb(url: str | None) -> str | None:
    if not url:
        return None
    return re.sub(r"/s\d+(-c)?/", "/s640/", url)


def _blogger_feed_url(site: str) -> str:
    raw = site.strip()
    if not raw.startswith("http"):
        raw = "https://" + raw
    u = urlparse(raw)
    base = f"{u.scheme}://{u.hostname}"
    return f"{base}/feeds/posts/default?alt=json&max-results=15"


def _parse_blogger_json(data: dict, source_label: str) -> list[dict]:
    feed = data.get("feed")
    if not feed or feed.get("generator", {}).get("$t") != "Blogger":
        return []
    entries = feed.get("entry") or []

    def alt_link(links):
        for link in links or []:
            if link.get("rel") == "alternate":
                return link.get("href", "")
        return ""

    site = alt_link(feed.get("link"))
    out: list[dict] = []
    for e in entries:
        html = (e.get("content") or e.get("summary") or {}).get("$t", "")
        url = alt_link(e.get("link"))
        if not url.startswith("https://"):
            continue
        if site and urlparse(url).hostname != urlparse(site).hostname:
            continue
        img = (e.get("media$thumbnail") or {}).get("url")
        if not img:
            m = re.search(r'<img[^>]+src="(https://[^"]+)"', html, re.I)
            img = m.group(1) if m else None
        title = _strip_html((e.get("title") or {}).get("$t", ""), 200) or "제목 없음"
        out.append(
            {
                "id": "b-" + re.sub(r"[^a-z0-9]", "", (e.get("id") or {}).get("$t", url))[:40],
                "content_type": "blog",
                "title": title,
                "summary": _strip_html(html),
                "url": url,
                "thumb_url": _upscale_thumb(img),
                "source": source_label or feed.get("title", {}).get("$t", "Blogger"),
                "published": (e.get("published") or e.get("updated") or {}).get("$t", ""),
            }
        )
    return out


def _parse_youtube_rss(xml_text: str, channel_label: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    ns = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015"}
    out: list[dict] = []
    for entry in root.findall("a:entry", ns):
        vid = entry.find("yt:videoId", ns)
        if vid is None or not vid.text:
            continue
        video_id = vid.text
        title_el = entry.find("a:title", ns)
        title = (title_el.text or "").strip() if title_el is not None else "영상"
        link_el = entry.find('a:link[@rel="alternate"]', ns)
        url = link_el.get("href") if link_el is not None else f"https://www.youtube.com/watch?v={video_id}"
        published_el = entry.find("a:published", ns)
        published = published_el.text if published_el is not None else ""
        desc_el = entry.find("a:summary", ns) or entry.find("a:content", ns)
        summary = _strip_html(desc_el.text if desc_el is not None else "")
        is_short = "/shorts/" in url or "#shorts" in title.lower() or "shorts" in title.lower()
        out.append(
            {
                "id": "y-" + video_id,
                "content_type": "shorts" if is_short else "video",
                "title": title,
                "summary": summary,
                "url": url if url.startswith("https://") else f"https://www.youtube.com/watch?v={video_id}",
                "thumb_url": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg",
                "source": channel_label or "YouTube",
                "published": published,
            }
        )
    return out


def _env_list(key: str) -> list[str]:
    raw = os.getenv(key, "").strip()
    if not raw:
        return []
    return [x.strip() for x in raw.split(",") if x.strip()]


async def _fetch_blogger(site: str) -> list[dict]:
    feed_url = _blogger_feed_url(site)
    async with httpx.AsyncClient(timeout=18, follow_redirects=True, headers={"User-Agent": UA}) as client:
        r = await client.get(feed_url, headers={"Accept": "application/json"})
        r.raise_for_status()
        data = r.json()
    label = urlparse(_blogger_feed_url(site)).hostname or site
    return _parse_blogger_json(data, label)


async def _fetch_youtube(channel_id: str) -> list[dict]:
    url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
    async with httpx.AsyncClient(timeout=18, follow_redirects=True, headers={"User-Agent": UA}) as client:
        r = await client.get(url)
        r.raise_for_status()
    return _parse_youtube_rss(r.text, f"YouTube · {channel_id[:8]}…")


async def load_wire_items(kind: str = "all") -> list[dict]:
    """kind: all | blog | video | shorts"""
    cache_key = f"wire:{kind}"
    now = time.time()
    if cache_key in _CACHE and now - _CACHE[cache_key][0] < TTL:
        return _CACHE[cache_key][1]

    blogs = _env_list("LAWYGO_PAN_BLOGGER_SITES")
    channels = _env_list("LAWYGO_PAN_YOUTUBE_CHANNEL_IDS")
    items: list[dict] = []

    if kind in ("all", "blog"):
        for site in blogs:
            try:
                items.extend(await _fetch_blogger(site))
            except (httpx.HTTPError, json.JSONDecodeError, KeyError, ValueError):
                continue

    if kind in ("all", "video", "shorts"):
        for cid in channels:
            try:
                vids = await _fetch_youtube(cid)
                if kind == "video":
                    items.extend([x for x in vids if x["content_type"] == "video"])
                elif kind == "shorts":
                    items.extend([x for x in vids if x["content_type"] == "shorts"])
                else:
                    items.extend(vids)
            except (httpx.HTTPError, ET.ParseError, ValueError):
                continue

    items.sort(key=lambda x: x.get("published") or "", reverse=True)
    _CACHE[cache_key] = (now, items[:60])
    return _CACHE[cache_key][1]
