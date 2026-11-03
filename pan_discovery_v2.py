"""Optional public, API-backed keyword discovery for LAWYGO PAN.
No HTML scraping, no fabricated items. Missing keys yield an empty discovery feed.
Uses public Google APIs, bounded to 15 minute freshness and strict host allow-lists.
"""
import asyncio
import os
import re
import time
from html import unescape
from urllib.parse import urlencode, urlparse

import httpx

_CACHE = {}
TTL = 900
_RELEVANT = re.compile(r"(법률|변호사|법무|판례|민사|형사|소송|계약|상속|이혼|legal|attorney|lawyer)",re.I)
_VIDEO_ID = re.compile(r"^[A-Za-z0-9_-]{11}$")
_BLOG_ID = re.compile(r"^[0-9]{5,30}$")

def _text(value,limit=200):
    value=re.sub(r"<[^>]*>"," ",str(value or ""))
    return unescape(" ".join(value.split()))[:limit]

def _safe_url(value,host):
    p=urlparse(str(value or ""))
    if p.scheme!="https" or not p.hostname:return None
    name=p.hostname.lower()
    if name!=host and not name.endswith("."+host):return None
    return p.geturl()

def _env_items(name,max_items=10):
    return [i.strip() for i in os.getenv(name,"").split(",") if i.strip()][:max_items]

def _youtube_item(item):
    ident=(item.get("id") or {}).get("videoId","")
    if not _VIDEO_ID.fullmatch(ident):return None
    sn=item.get("snippet") or {}
    title=_text(sn.get("title"),180);summary=_text(sn.get("description"),200)
    if not _RELEVANT.search(title+" "+summary):return None
    # A short-length video and YouTube's Shorts product are not synonymous.
    # Only explicitly tagged Shorts are classified as Shorts.
    is_short=bool(re.search(r"(#shorts\b|#쇼츠\b|\bshorts\b)",title+" "+summary,re.I))
    return {"id":"g-y-"+ident,"content_type":"shorts" if is_short else "video",
            "title":title,"summary":summary,"url":"https://www.youtube.com/watch?v="+ident,
            "thumb_url":"https://img.youtube.com/vi/"+ident+"/hqdefault.jpg",
            "source":_text(sn.get("channelTitle"),80) or "YouTube","published":str(sn.get("publishedAt") or ""),
            "approved":False,"discovery":"youtube-api"}

def _blogger_item(item):
    title=_text(item.get("title"),180)
    summary=_text(item.get("content"),200)
    if not _RELEVANT.search(title+" "+summary):return None
    url=_safe_url(item.get("url"),"blogspot.com")
    # Blogger may use connected custom domains. Those are admitted only when
    # explicitly configured in LAWYGO_PAN_BLOGGER_ALLOWED_HOSTS.
    if not url:
        for host in _env_items("LAWYGO_PAN_BLOGGER_ALLOWED_HOSTS",20):
            if host and re.fullmatch(r"[a-z0-9.-]{4,200}",host,re.I):
                url=_safe_url(item.get("url"),host)
                if url:break
    if not url:return None
    raw=str(item.get("id",""))[:80]
    return {"id":"g-b-"+re.sub("[^0-9a-zA-Z]","",raw)[:38],"content_type":"blog",
            "title":title,"summary":summary,"url":url,
            "thumb_url":None,"source":_text((item.get("author") or {}).get("displayName"),80) or urlparse(url).hostname,
            "published":str(item.get("published") or ""),"approved":False,"discovery":"blogger-api"}

async def public_search(kind="all"):
    """Public search only; requires explicitly provisioned API key."""
    youtube_key=os.getenv("LAWYGO_PAN_YOUTUBE_API_KEY","").strip()
    blogger_key=os.getenv("LAWYGO_PAN_BLOGGER_API_KEY","").strip()
    blog_ids=[i for i in _env_items("LAWYGO_PAN_BLOGGER_IDS") if _BLOG_ID.fullmatch(i)]
    if not (youtube_key or (blogger_key and blog_ids)):return []
    if kind not in ("all","blog","video","shorts"):kind="all"
    now=time.time()
    if kind in _CACHE and now-_CACHE[kind][0]<TTL:return list(_CACHE[kind][1])
    tasks=[]
    async with httpx.AsyncClient(timeout=9,follow_redirects=False) as client:
        if youtube_key and kind in ("all","video","shorts"):
            qs=["변호사 법률","#shorts 변호사"] if kind in ("all","shorts") else ["변호사 법률"]
            for q in qs:
                params={"part":"snippet","type":"video","q":q,"maxResults":15,"order":"date",
                        "regionCode":"KR","relevanceLanguage":"ko","safeSearch":"moderate","key":youtube_key}
                if kind=="shorts":params["videoDuration"]="short"
                tasks.append(("youtube",client.get("https://www.googleapis.com/youtube/v3/search",params=params)))
        if blogger_key and kind in ("all","blog"):
            for bid in blog_ids[:8]:
                for q in ("법률","변호사"):
                    tasks.append(("blogger",client.get(
                        "https://www.googleapis.com/blogger/v3/blogs/"+bid+"/posts/search",
                        params={"q":q,"key":blogger_key,"fetchBodies":"true"})))
        responses=await asyncio.gather(*(task for _,task in tasks),return_exceptions=True)
        items=[]
        for (source,_),response in zip(tasks,responses):
            if isinstance(response,Exception) or response.status_code!=200:continue
            try:
                data=response.json()
                for entry in data.get("items",[])[:30]:
                    v=_youtube_item(entry) if source=="youtube" else _blogger_item(entry)
                    if v and (kind=="all" or v["content_type"]==kind):items.append(v)
            except (ValueError,TypeError,KeyError):continue
    dedup={}
    for item in items:dedup.setdefault(item["url"],item)
    results=sorted(dedup.values(),key=lambda x:x.get("published") or "",reverse=True)[:60]
    _CACHE[kind]=(now,results)
    return list(results)
