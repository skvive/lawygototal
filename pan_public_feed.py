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
# Scope public syndicated videos/blogs to legal subjects regardless of provider.
# Channels alone are not evidence that every newly published item is legal content.
_LEGAL_TOPIC = re.compile(
    r"(법률|변호사|법무|법원|판례|법령|소송|민사|형사|계약|상속|이혼|부동산[ ]*분쟁|"
    r"손해배상|행정심판|노동법|지식재산|특허|개인정보[ ]*보호법|사기죄|고소|"
    r"중재|법률상담|재판|등기|조세|세무쟁송|유언|양육권|고용계약|"
    r"\blegal\b|\blawyer\b|\battorney\b|\blitigation\b|\bcourt\b|\bregulation\b)",
    re.I,
)


def _is_legal_topic(item: dict) -> bool:
    return bool(_LEGAL_TOPIC.search(" ".join(str(item.get(key) or "") for key in ("title", "summary"))))


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
                "id": "b-" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:20],
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


# LAWYGO PAN public sources (verified official video channels / public Blogger /
# Newswire category RSS). The fallback index below is real-source metadata only,
# never a fabricated video, quote or current live-broadcast status.
import asyncio
import hashlib

LEGAL_YOUTUBE_CHANNELS = (
    "UC7ilNDoKW1sxHqqIJj-DgKQ",  # 이돈호 변호사
    "UChRnJ6XdAANkCOJfmWSASgQ",  # 법률방송
    "UCA0AG-U7Tp9fDmzjqUmPLIw",  # 한변TV
    "UC1e5SzvZSDffEz32kP5J-1w", # 화요일 변호사
)
LEGAL_BLOGGER_SITES = ("2yourlawyer.blogspot.com", "kimmlaw.blogspot.com")
LEGAL_NEWSWIRE_FEEDS = (
    "https://api.newswire.co.kr/rss/industry/1902",  # 법률
    "https://api.newswire.co.kr/rss/theme/124",       # 소송
    "https://api.newswire.co.kr/rss/theme/129",       # 지식재산
)

# Source links individually verified at the original publishers on 2026-11-08.
# These are fallback reference entries only when a live source feed fails.
VERIFIED_SOURCE_STARTERS = (
    ("video",'"검사도 실수한다?" 폐지된 법으로 기소된 흥신소 사건, 재판 가기 전에 무조건 끝내야 하는 이유',
     "https://www.youtube.com/watch?v=73wWp3zXIB8","고호 법률사무소 · 내편박변","2026-06-28"),
    ("video","평택 강제추행 피해 여경의 계속 바뀌는 진술? 대법원은 다르게 봅니다",
     "https://www.youtube.com/watch?v=aFfWr20jG58","고호 법률사무소 · 내편박변","2026-06-07"),
    ("video","화장실 몰카범 잡았는데 폭행 전과자? 전직 부장검사가 분노한 기막힌 판결",
     "https://www.youtube.com/watch?v=f2d78wWhIsE","고호 법률사무소 · 내편박변","2026-06-24"),
    ("video","AVMOV 이어 '놀쟈' 수사 개시… 무조건 자수? 공포 마케팅에 절대 돈 쓰지 마세요!",
     "https://www.youtube.com/watch?v=Ptp-EqX-3h0","고호 법률사무소 · 내편박변","2026-06-04"),
    ("video","프로야구 선수가 야구를 제대로 못하면 직무유기죄? 부장검사 출신 변호사 해설",
     "https://www.youtube.com/watch?v=HaqImAlh4ic","고호 법률사무소 · 내편박변","2026-06-10"),
    ("shorts","검사의 충격적 실수 때문에 남편 외도 잡으려다 전과자 될 뻔?",
     "https://www.youtube.com/watch?v=FawkpE0aFeU","고호 법률사무소 · 내편박변","2026-07-07"),
    ("shorts","새벽 5시 몰카범 도주 막았는데 전과자? 부장검사 출신 변호사의 해설",
     "https://www.youtube.com/watch?v=_52mIFYx52o","고호 법률사무소 · 내편박변","2026-06-26"),
    ("shorts","놀쟈사이트 이용 전수조사? 경찰의 '진짜 타깃'은 따로 있습니다!",
     "https://www.youtube.com/watch?v=DBLMQtkTf1I","고호 법률사무소 · 내편박변","2026-06-14"),
    ("video","평택 여경 0.8초 강제추행 논란, 대법원에서 뒤집힐까?",
     "https://www.youtube.com/watch?v=p3yh_8rWdY0","고호 법률사무소 · 내편박변","2026-05-28"),
    ("blog","[회사법무 계약법] 병행수입상품 정품 감정업자의 책임이 문제된 사건",
     "https://2yourlawyer.blogspot.com/2026/09/blog-post_19.html",
     "변호사 정회목의 법률 스토리","2026-09-19"),
    ("blog","[행정소송 정보삭제] 공직선거법 제110조 제2항 해석 사건",
     "https://2yourlawyer.blogspot.com/2025/12/110-2.html",
     "변호사 정회목의 법률 스토리","2025-12-28"),
    ("newswire","로앤비 온주, ‘민사집행법’ 출간으로 주석서 100권 돌파",
     "https://www.newswire.co.kr/newsRead.php?no=1040726","뉴스와이어 · 보도자료","2026-08-19"),
    ("newswire","톰슨로이터코리아, 온라인 주석서 ‘온주’ 상법 회사편 ‘회사법’ 출간",
     "https://www.newswire.co.kr/newsRead.php?no=1030838","뉴스와이어 · 보도자료","2026-03-24"),
)

def _verified_source_starters() -> list[dict]:
    out = []
    for kind, title, url, source, published in VERIFIED_SOURCE_STARTERS:
        video_id = None
        if "youtube.com/watch?v=" in url:
            from urllib.parse import parse_qs
            video_id = parse_qs(urlparse(url).query).get("v", [None])[0]
        out.append({
            "id": "verified-" + hashlib.sha1(url.encode()).hexdigest()[:16],
            "content_type": kind, "title": title,
            "summary": ("법률사무소 고호가 공개한 변호사 법률 해설 영상." if kind in ("video", "shorts") else ""),
            "url": url,
            "thumb_url": f"https://img.youtube.com/vi/{video_id}/hqdefault.jpg" if video_id else None,
            "source": source, "published": published, "approved": False,
            "source_kind": "original-verified", "live": False
        })
    return out


def _parse_newswire_rss(xml_text: str, label: str = "뉴스와이어 · 보도자료") -> list[dict]:
    root = ET.fromstring(xml_text)
    items = root.findall(".//item")
    if not items:
        items = root.findall(".//{http://www.w3.org/2005/Atom}entry")
    result = []
    for node in items[:65]:
        def field(*names):
            for name in names:
                child = node.find(name)
                if child is not None and child.text:
                    return child.text.strip()
            return ""
        title = _strip_html(field("title", "{http://www.w3.org/2005/Atom}title"), 190)
        link = field("link", "{http://www.w3.org/2005/Atom}id")
        if not link:
            atom_link = node.find("{http://www.w3.org/2005/Atom}link")
            link = atom_link.get("href", "") if atom_link is not None else ""
        host = (urlparse(link).hostname or "").lower()
        if host not in ("www.newswire.co.kr", "newswire.co.kr") or not title:
            continue
        description = _strip_html(field("description", "{http://www.w3.org/2005/Atom}summary"), 155)
        pic = None
        # RSS explicitly provided images only; never scrape full articles for media.
        for child in node:
            if child.tag in ("{http://search.yahoo.com/mrss/}content",
                             "{http://search.yahoo.com/mrss/}thumbnail", "enclosure"):
                val = child.attrib.get("url", "")
                if val.startswith("https://") and (child.tag != "enclosure" or
                       child.attrib.get("type", "").startswith("image/")):
                    pic = val
                    break
        if pic and (pic.endswith("/thumb/.jpg") or pic.endswith("/thumb/.png")):
            pic = None
        if not pic:
            match = re.search(r'<img[^>]+src=["\'](https://[^"\']+)["\']',
                              field("description"), re.I)
            if match:
                pic = match.group(1)
        pub = field("pubDate", "{http://www.w3.org/2005/Atom}published")
        result.append({
            "id": "n-" + hashlib.sha1(link.encode()).hexdigest()[:20],
            "content_type": "newswire", "title": title,
            "summary": description, "url": link, "thumb_url": pic,
            "source": label, "published": pub, "approved": False,
            "source_kind": "press-release", "live": False
        })
    return result


async def _fetch_newswire(feed_url: str) -> list[dict]:
    async with httpx.AsyncClient(timeout=9, follow_redirects=True,
                                 headers={"User-Agent": UA, "Accept": "application/rss+xml, application/xml, text/xml"}) as client:
        r = await client.get(feed_url)
        r.raise_for_status()
    return _parse_newswire_rss(r.text)


async def load_wire_items(kind: str = "all") -> list[dict]:
    """Public source metadata only. Prefer RSS and use verified original URLs as fallback."""
    cache_key = f"wire:v2:{kind}"
    now = time.time()
    if cache_key in _CACHE and now - _CACHE[cache_key][0] < TTL:
        return _CACHE[cache_key][1]
    # Honor explicitly configured sources; known verified public defaults prevent
    # an empty production feed when an operator has not entered custom sources.
    blogs = _env_list("LAWYGO_PAN_BLOGGER_SITES") or list(LEGAL_BLOGGER_SITES)
    channels = _env_list("LAWYGO_PAN_YOUTUBE_CHANNEL_IDS") or list(LEGAL_YOUTUBE_CHANNELS)
    feeds = _env_list("LAWYGO_PAN_NEWSWIRE_RSS_URLS") or list(LEGAL_NEWSWIRE_FEEDS)
    jobs = []
    if kind in ("all", "blog"):
        jobs.extend((_fetch_blogger(site) for site in blogs[:6]))
    if kind in ("all", "video", "shorts"):
        jobs.extend((_fetch_youtube(cid) for cid in channels[:10]))
    if kind in ("all", "newswire"):
        jobs.extend((_fetch_newswire(feed) for feed in feeds[:5]))
    batches = await asyncio.gather(*jobs, return_exceptions=True)
    items: list[dict] = []
    for batch in batches:
        if not isinstance(batch, BaseException):
            items.extend(batch)
    # Existing official search integration (disabled when no API credentials).
    if kind in ("all", "video", "shorts"):
        import pan_discovery_v2
        try:
            items.extend(await asyncio.wait_for(pan_discovery_v2.public_search(kind), timeout=8))
        except (httpx.HTTPError, ValueError, KeyError, asyncio.TimeoutError):
            pass
    present_kinds = {x.get("content_type") for x in items if _is_legal_topic(x)}
    # Only verified real publisher metadata, not stock/fake posts.
    for starter in _verified_source_starters():
        if starter["content_type"] not in present_kinds:
            items.append(starter)
    dedup: dict[str, dict] = {}
    for item in items:
        if not item.get("url") or not item.get("title") or not _is_legal_topic(item):
            continue
        ctype = item.get("content_type")
        if kind != "all" and ctype != kind:
            continue
        dedup.setdefault(item["url"], item)
    items = list(dedup.values())
    # ISO and RSS dates both allowed; put valid modern ISO first via parser.
    from email.utils import parsedate_to_datetime
    def sort_date(item):
        raw = item.get("published") or ""
        if not raw:
            return ""
        try:
            if re.match(r"^\d{4}-", raw):
                return raw[:10]
            return parsedate_to_datetime(raw).date().isoformat()
        except (TypeError, ValueError, OverflowError):
            return ""
    items.sort(key=sort_date, reverse=True)
    _CACHE[cache_key] = (now, items[:95])
    return _CACHE[cache_key][1]
