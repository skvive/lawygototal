"""First-party LAWYGO crawl discovery: robots, XML sitemaps, RSS and public editorials.

Only tenant-scoped, published, public CHANNEL posts appear in discovery.
Never re-publish syndicated external RSS as LAWYGO-owned content.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from email.utils import format_datetime
from html import escape as html_escape
from xml.sax.saxutils import escape as xml_escape

from fastapi import Depends, HTTPException, Response

BASE = "https://lawygo.lexid.site"
PUBLIC_PAGES = (
    "/", "/journal", "/channel", "/p/wiki", "/p/note", "/p/pan",
    "/p/channel", "/pro", "/pricing", "/payment", "/partnership", "/strategy",
)
_CACHE = {"Cache-Control": "public, max-age=0, s-maxage=300"}


def _xml(s: object) -> str:
    return xml_escape(str(s or ""), {'"': "&quot;", "'": "&apos;"})


def _date(value: object) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (ValueError, TypeError, OverflowError):
        return None


def _canonical(path: str) -> str:
    return BASE + path


def _public_rows(db, tenant: str, limit: int) -> list[dict]:
    # Deliberately mirror the approved editorial criteria of /api/journal/feed.
    rows = db.execute(
        """SELECT p.id,p.title,p.summary,p.body,p.updated_at,p.published_at,
                  p.is_sponsored
           FROM posts p JOIN boards b ON p.board_id=b.id
           WHERE p.tenant=? AND b.deleted_at IS NULL AND p.deleted_at IS NULL
             AND p.product='channel' AND p.status='published'
             AND p.visibility='public'
           ORDER BY p.updated_at DESC LIMIT ?""",
        (tenant, limit),
    ).fetchall()
    return [dict(row) for row in rows]


def _xml_response(data: str, media_type: str = "application/xml") -> Response:
    return Response(content=data, media_type=media_type, headers=_CACHE)


def register(app, database, tenant: str) -> None:
    @app.get("/robots.txt", include_in_schema=False)
    def robots_txt():
        text = (
            "User-agent: *\n"
            "Allow: /\n"
            "Disallow: /api/\n"
            "Disallow: /dashboard\n"
            "Sitemap: " + BASE + "/sitemap.xml\n"
        )
        # Robots is a crawl policy, not an access-control mechanism.
        return Response(text, media_type="text/plain", headers=_CACHE)

    @app.get("/sitemap.xml", include_in_schema=False)
    def sitemap_index():
        chunks = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ]
        for path in ("/sitemap-pages.xml", "/sitemap-articles.xml"):
            chunks.append("<sitemap><loc>" + _xml(_canonical(path)) + "</loc></sitemap>")
        chunks.append("</sitemapindex>")
        return _xml_response("\n".join(chunks))

    @app.get("/sitemap-pages.xml", include_in_schema=False)
    def sitemap_pages():
        chunks = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ]
        chunks.extend("<url><loc>" + _xml(_canonical(path)) + "</loc></url>" for path in PUBLIC_PAGES)
        chunks.append("</urlset>")
        # No fabricated lastmod for static HTML. Google ignores changefreq/priority.
        return _xml_response("\n".join(chunks))

    @app.get("/sitemap-articles.xml", include_in_schema=False)
    def sitemap_articles(db=Depends(database)):
        chunks = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
        ]
        for post in _public_rows(db, tenant, 1000):
            uri = _canonical("/journal/articles/" + str(post["id"]))
            when = _date(post.get("updated_at"))
            chunks.append("<url><loc>" + _xml(uri) + "</loc>"
                          + ("<lastmod>" + when.date().isoformat() + "</lastmod>" if when else "")
                          + "</url>")
        chunks.append("</urlset>")
        return _xml_response("\n".join(chunks))

    @app.get("/rss.xml", include_in_schema=False)
    def editorial_rss(db=Depends(database)):
        parts = [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">',
            '<channel>',
            '<title>LAWYGO JOURNAL | 법률·경제 인텔리전스</title>',
            '<link>' + BASE + '/journal</link>',
            '<description>LAWYGO 편집국에서 직접 승인·발행한 공개 콘텐츠만 제공하는 RSS입니다.</description>',
            '<language>ko-KR</language>',
            '<atom:link href="' + BASE + '/rss.xml" rel="self" type="application/rss+xml" />',
        ]
        for post in _public_rows(db, tenant, 50):
            uri = _canonical("/journal/articles/" + str(post["id"]))
            title = str(post["title"] or "LAWYGO 저널")
            if post.get("is_sponsored"):
                title = "[광고] " + title
            when = _date(post.get("published_at")) or _date(post.get("updated_at"))
            parts.extend([
                "<item>",
                "<title>" + _xml(title) + "</title>",
                "<link>" + _xml(uri) + "</link>",
                '<guid isPermaLink="true">' + _xml(uri) + "</guid>",
                "<description>" + _xml(post.get("summary") or title) + "</description>",
            ])
            if when:
                parts.append("<pubDate>" + format_datetime(when) + "</pubDate>")
            if post.get("is_sponsored"):
                parts.append("<category>광고</category>")
            parts.append("</item>")
        parts.extend(["</channel>", "</rss>"])
        return _xml_response("\n".join(parts), "application/rss+xml")

    @app.get("/journal/articles/{post_id}", include_in_schema=False)
    def public_article(post_id: str, db=Depends(database)):
        # The direct HTML permalink is needed before an item can enter an RSS or sitemap.
        if not re.fullmatch(r"[0-9a-f]{32}", post_id):
            raise HTTPException(status_code=404, detail="공개되지 않은 글입니다.")
        row = db.execute(
            """SELECT p.id,p.title,p.body,p.summary,p.updated_at,p.published_at,
                      p.is_sponsored
               FROM posts p JOIN boards b ON p.board_id=b.id
               WHERE p.id=? AND p.tenant=? AND b.deleted_at IS NULL
                 AND p.deleted_at IS NULL AND p.product='channel'
                 AND p.status='published' AND p.visibility='public'""",
            (post_id, tenant),
        ).fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="공개되지 않은 글입니다.")
        post = dict(row)
        title = html_escape(str(post["title"] or "LAWYGO JOURNAL"), quote=True)
        summary = html_escape(str(post.get("summary") or ""), quote=True)
        body = html_escape(str(post.get("body") or ""), quote=True)
        date = _date(post.get("published_at")) or _date(post.get("updated_at"))
        date_label = date.date().isoformat() if date else ""
        sponsored = '<span class="seo-article-ad">광고·후원 콘텐츠</span>' if post.get("is_sponsored") else ""
        canonical = _canonical("/journal/articles/" + post_id)
        html = f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title} | LAWYGO JOURNAL</title>
<meta name="description" content="{summary[:160]}">
<link rel="canonical" href="{canonical}">
<link rel="alternate" type="application/rss+xml" title="LAWYGO JOURNAL RSS" href="{BASE}/rss.xml">
<link rel="icon" href="/static/favicon.ico">
<link rel="stylesheet" href="/static/atlas/site.css">
<link rel="stylesheet" href="/static/lawygo-premium-20261101.css">
<link rel="stylesheet" href="/static/lawygo-delivery-20261103.css">
</head><body class="atlas-page"><div data-brand-shell="header"></div>
<main id="main-content" class="seo-article-main">
<article class="seo-article" lang="ko">
<p class="seo-article-kicker">LAWYGO / JOURNAL / ORIGINAL EDITORIAL</p>
<h1>{title}</h1>
<p class="seo-article-meta"><time>{date_label}</time>{sponsored}</p>
<p class="seo-article-lead">{summary}</p>
<div class="seo-article-body">{body}</div>
<p class="seo-article-disclaimer">본 자료는 일반 정보이며, 개별 사건에 관한 법률 자문이 아닙니다. 법령·판례 원문과 최신성을 확인해 주세요.</p>
<a class="btn btn-navy" href="/journal">저널로 돌아가기</a>
</article></main><div data-brand-shell="footer"></div>
<script src="/static/brand-shell.js" defer></script></body></html>"""
        return Response(content=html, media_type="text/html", headers=_CACHE)
