"""Aggregate licensed RSS headlines for LAWYGO Journal (title, summary, link, source)."""
from __future__ import annotations

import asyncio
import re
import time
import xml.etree.ElementTree as ET
from html import unescape
from typing import Any

import httpx

_CACHE: dict[str, Any] = {"at": 0.0, "items": []}
_TTL = 900  # 15 min on successful RSS load
_EMPTY_TTL = 60  # retry empty or upstream failures promptly

FEEDS = (
    # Official WeeklyNews RSS: headline and summary syndication only; never mirror full articles.
    {"source": "위클리뉴스", "region": "kr", "desk": "WEEKLYNEWS · 경제·법률", "url": "https://weeklynews.me/feed.xml"},
    {"source": "연합뉴스", "region": "kr", "desk": "한국 경제·정책", "url": "https://www.yna.co.kr/rss/economy.xml"},
    {"source": "연합뉴스", "region": "kr", "desk": "한국 종합", "url": "https://www.yna.co.kr/rss/news.xml"},
    {"source": "Federal Reserve", "region": "us", "desk": "미국 통화정책 · 연방준비제도", "url": "https://www.federalreserve.gov/feeds/press_monetary.xml"},
    {"source": "BBC", "region": "us", "desk": "U.S. & Americas", "url": "https://feeds.bbci.co.uk/news/world/us_and_canada/rss.xml"},
    {"source": "NPR", "region": "us", "desk": "U.S. Business", "url": "https://feeds.npr.org/1019/rss.xml"},
)

UA = {"User-Agent": "LAWYGO-Journal/1.0 (+https://lawygo.lexid.site/journal)"}

# JOURNAL is an economics-and-law publication, not a small-business grant
# directory. Filter only obvious recruitment/application notices. Reporting on
# law, litigation, penalties, and judicial reviews remains eligible.
_BUSINESS_PROGRAM = re.compile(
    r"(?:지원\s*사업|공모\s*사업|창업\s*기업|창업기업|입주기업|참여기업|"
    r"수혜기업|중소기업대상|중소기업\s*대상|연구개발특구|특구\s*육성|"
    r"창업\s*지원|소상공인|스타트업|보조금|지원금|바우처|"
    r"지원\s*프로그램|사업장|기업\s*모집|기업\s*대상|"
    r"R\s*&\s*D\s*사업|창업\s*도약)",
    re.IGNORECASE,
)
_APPLICATION_NOTICE = re.compile(
    r"(?:모집|공고|접수|신청|공모|참여\s*신청|추가\s*모집|"
    r"지원\s*대상|기업\s*선발|사업\s*참여)",
    re.IGNORECASE,
)
_LEGAL_PROCEEDING = re.compile(
    r"(?:소송|법원|판결|판례|위헌|위법|행정심판|조세심판|"
    r"대법원|헌법재판|기소|수사|사법심사|처분\s*취소)",
    re.IGNORECASE,
)


def is_business_announcement(item: dict) -> bool:
    """Whether the headline is a business-grant/recruitment announcement.

    Use the headline, not the summary or publisher; generic descriptions of
    funding or legal policy must not cause unrelated legal stories to vanish.
    """
    title = _strip_html(str(item.get("title") or ""))
    if not title or _LEGAL_PROCEEDING.search(title):
        return False
    return bool(_BUSINESS_PROGRAM.search(title) and _APPLICATION_NOTICE.search(title))


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
    for node in nodes[:36]:
        title = _strip_html(node.findtext("title") or "")
        link = (node.findtext("link") or "").strip()
        desc = _strip_html(node.findtext("description") or node.findtext("{http://purl.org/rss/1.0/modules/content/}encoded") or "")
        pub = (node.findtext("pubDate") or node.findtext("published") or "")[:31]
        if not title or not link or is_business_announcement({"title": title}):
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
        if len(items) >= 12:
            break
    return items


async def _fetch_one(client: httpx.AsyncClient, meta: dict) -> list[dict]:
    try:
        r = await client.get(meta["url"], headers=UA, timeout=4.0)
        r.raise_for_status()
        return _parse_rss(r.text, meta)
    except Exception:
        return []


async def load_wire_items() -> list[dict]:
    now = time.time()
    max_age = _TTL if _CACHE["items"] else _EMPTY_TTL
    if _CACHE["at"] and now - _CACHE["at"] < max_age:
        return _CACHE["items"]

    # RSS feeds were previously requested one-by-one with a 20-second timeout
    # each. Parallel fetching caps total waiting time at approximately 5 seconds
    # even when independent publishers are slow or unreachable.
    async with httpx.AsyncClient(follow_redirects=True, timeout=4.0) as client:
        try:
            batches = await asyncio.wait_for(
                asyncio.gather(*(_fetch_one(client, meta) for meta in FEEDS)), timeout=5.0
            )
        except asyncio.TimeoutError:
            # A publisher outage must never make every visitor wait.
            _CACHE["at"] = now
            return _CACHE["items"]

    merged = [item for batch in batches for item in batch]
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
        if is_business_announcement(r):
            continue
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
