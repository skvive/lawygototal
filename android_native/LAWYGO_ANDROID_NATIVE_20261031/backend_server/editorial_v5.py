"""LAWYGO v5 editorial RSS / daily digest module.
No AI calls required for collection or fact-preserving editorial draft.
All feeds are built-in allowlisted sources, not arbitrary URLs (SSRF prevention).
The scheduler is invoked outside web workers; an editor must approve and manually send.
"""
from __future__ import annotations
import hashlib, html, json, os, re, sqlite3, uuid
from datetime import datetime, timezone, timedelta, date
from zoneinfo import ZoneInfo
from urllib.parse import urlparse
from email.utils import parsedate_to_datetime
from defusedxml import ElementTree as ET
from pydantic import BaseModel, Field
from fastapi import Depends, HTTPException, Request
import httpx

KST=ZoneInfo('Asia/Seoul')
USER_AGENT='LAWYGO-Journal/5.0 (+https://lawygo.com; feed-summary-only)'
FEEDS=[
 ('fed-all','Federal Reserve · Press Releases','미국 정책','https://www.federalreserve.gov/feeds/press_all.xml','en'),
 ('sec-releases','SEC · Press Releases','미국 증권','https://www.sec.gov/news/pressreleases.rss','en'),
 ('fed-money','Federal Reserve · Monetary Policy','미국 정책','https://www.federalreserve.gov/feeds/press_monetary.xml','en'),
 ('bok-policy','한국은행 · 경제정책','한국 경제','https://www.bok.or.kr/portal/bbs/B0000552/news.rss?menuNo=200690','ko'),
 ('bok-markets','한국은행 · 금융시장 동향','한국 경제','https://www.bok.or.kr/portal/bbs/P0002017/news.rss?menuNo=200365','ko'),
 ('us-markets','미국 증권시장 뉴스 · Google News','미국 증권','https://news.google.com/rss/search?q=when:3d+site%3Areuters.com%2Fmarkets&ceid=US%3Aen&hl=en-US&gl=US','en'),
 ('us-business','미국 주요 경제 뉴스 · Google News','미국 경제','https://news.google.com/rss/search?q=when:3d+site%3Areuters.com%2Fbusiness&ceid=US%3Aen&hl=en-US&gl=US','en'),
 ('mk-economy','매일경제 · 경제','한국 경제','https://www.mk.co.kr/rss/30100041/','ko'),
 ('mk-stocks','매일경제 · 증권','한국 경제','https://www.mk.co.kr/rss/50200011/','ko'),
 ('mbn-stocks','매일경제TV · 증권','한국 경제','https://mbnmoney.com/rss/news/stock','ko'),
 ('korea-economy','한국 주요 경제 뉴스 · Google News','한국 경제','https://news.google.com/rss/search?q=%ED%95%9C%EA%B5%AD+%EA%B2%BD%EC%A0%9C+%EC%A6%9D%EA%B6%8C+%EC%A0%9C%EB%8F%84+when%3A3d&ceid=KR%3Ako&hl=ko&gl=KR','ko'),
]
ALLOWED_HOSTS={'www.federalreserve.gov','www.bok.or.kr','news.google.com','www.sec.gov','www.mk.co.kr','mbnmoney.com'}

def stamp():return datetime.now(timezone.utc).isoformat()
def today_kst():return datetime.now(KST).date().isoformat()
def sha(s):return hashlib.sha256(s.encode('utf-8')).hexdigest()
def textclean(s,maxlen=800):
 s=re.sub(r'(?is)<[^>]+>',' ',str(s or ''))
 return re.sub(r'\s+',' ',html.unescape(s)).strip()[:maxlen]
def inner(node,name):
 x=node.find(name) if node is not None else None
 return ''.join(x.itertext()).strip() if x is not None else ''
def parse_date(s):
 if not s:return None
 try:return parsedate_to_datetime(s).astimezone(timezone.utc).isoformat()
 except Exception:
  try:return datetime.fromisoformat(s.replace('Z','+00:00')).astimezone(timezone.utc).isoformat()
  except Exception:return None

def parse_feed(xml:bytes,source:str):
 """RSS 2.0 & Atom. Limited output; external entities and DTD rejected by defusedxml."""
 if len(xml)>2_000_000:raise ValueError('RSS 크기 제한 초과')
 root=ET.fromstring(xml)
 items=[]
 for el in list(root.findall('.//item'))[:70]:
  title=textclean(inner(el,'title'),220);url=inner(el,'link').strip()
  descr=textclean(inner(el,'description'),320)
  if not title or not safe_article_url(url):continue
  guid=inner(el,'guid') or url
  published=parse_date(inner(el,'pubDate') or inner(el,'date'))
  items.append(dict(title=title,url=url,summary=descr,source=source,source_guid=guid,published_at=published))
 for el in list(root.findall('.//{http://www.w3.org/2005/Atom}entry'))[:70]:
  ns='{http://www.w3.org/2005/Atom}'
  title=textclean(inner(el,ns+'title'),220)
  x=el.find(ns+'link')
  url=x.attrib.get('href','') if x is not None else ''
  if not title or not safe_article_url(url):continue
  summary=textclean(inner(el,ns+'summary') or inner(el,ns+'content'),320)
  items.append(dict(title=title,url=url,summary=summary,source=source,source_guid=inner(el,ns+'id') or url,published_at=parse_date(inner(el,ns+'published') or inner(el,ns+'updated'))))
 return items

def safe_article_url(url):
 try:
  x=urlparse(url)
  return x.scheme=='https' and bool(x.hostname) and not x.username and not x.password and len(url)<2000 and x.hostname not in ('localhost','127.0.0.1')
 except Exception:return False

def ensure_schema(db):
 db.executescript('''
 CREATE TABLE IF NOT EXISTS journal_sources(id TEXT PRIMARY KEY,name TEXT NOT NULL,category TEXT NOT NULL,url TEXT NOT NULL,lang TEXT NOT NULL,enabled INTEGER NOT NULL DEFAULT 1,updated_at TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS journal_items(id TEXT PRIMARY KEY,source_id TEXT NOT NULL REFERENCES journal_sources(id),source_guid TEXT NOT NULL,url TEXT NOT NULL,title TEXT NOT NULL,summary TEXT NOT NULL,published_at TEXT,first_seen TEXT NOT NULL, UNIQUE(source_id,source_guid));
 CREATE INDEX IF NOT EXISTS journal_items_date ON journal_items(first_seen DESC);
 CREATE TABLE IF NOT EXISTS journal_fetches(id TEXT PRIMARY KEY,source_id TEXT NOT NULL,status TEXT NOT NULL,found INTEGER NOT NULL DEFAULT 0,added INTEGER NOT NULL DEFAULT 0,error TEXT,checked_at TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS journal_draft_history(id TEXT PRIMARY KEY,draft_id TEXT NOT NULL,editor_id TEXT NOT NULL,old_status TEXT NOT NULL,old_subject TEXT NOT NULL,old_body TEXT NOT NULL,changed_at TEXT NOT NULL);
 CREATE TABLE IF NOT EXISTS journal_drafts(id TEXT PRIMARY KEY,issue_day TEXT NOT NULL UNIQUE,subject TEXT NOT NULL,body TEXT NOT NULL,source_ids_json TEXT NOT NULL,source_count INTEGER NOT NULL,status TEXT NOT NULL CHECK(status IN ('draft','in_review','approved','archived')),generator TEXT NOT NULL,editor_id TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL);
 ''')
 for id,name,cat,url,lang in FEEDS:
  db.execute('INSERT OR IGNORE INTO journal_sources VALUES(?,?,?,?,?,?,?)',(id,name,cat,url,lang,1,stamp()))

def fetch_bytes(url:str):
 u=urlparse(url)
 if u.scheme!='https' or u.hostname not in ALLOWED_HOSTS or u.username or u.password:raise ValueError('허용되지 않은 RSS 출처')
 # redirects disabled; no user-controlled URLs; limit response bytes
 with httpx.Client(timeout=14,follow_redirects=False,headers={'User-Agent':USER_AGENT,'Accept':'application/rss+xml,application/atom+xml,application/xml,text/xml'}) as c:
  with c.stream('GET',url) as res:
   res.raise_for_status()
   raw=bytearray()
   for chunk in res.iter_bytes():
    raw.extend(chunk)
    if len(raw)>2_000_000:raise ValueError('RSS 용량 제한을 초과했습니다.')
   return bytes(raw)

def collect(db,fetcher=None):
 fetcher=fetcher or fetch_bytes
 sources=db.execute('SELECT * FROM journal_sources WHERE enabled=1').fetchall()
 output=[]
 for s in sources:
  count=added=0;error=None
  try:
   items=parse_feed(fetcher(s['url']),s['name'])
   count=len(items)
   for item in items:
    before=db.total_changes
    db.execute('''INSERT OR IGNORE INTO journal_items(id,source_id,source_guid,url,title,summary,published_at,first_seen) VALUES(?,?,?,?,?,?,?,?)''',
       (uuid.uuid4().hex,s['id'],sha(item['source_guid']),item['url'],item['title'],item['summary'],item['published_at'],stamp()))
    if db.total_changes>before:added+=1
   status='ok'
  except Exception as e:
   error=type(e).__name__+': '+str(e)[:220]
   status='failed'
  db.execute('INSERT INTO journal_fetches VALUES(?,?,?,?,?,?,?)',(uuid.uuid4().hex,s['id'],status,count,added,error,stamp()))
  output.append(dict(source=s['id'],status=status,found=count,added=added,error=error))
 return output

def select_for_day(db,issue_day):
 # last 36h of source publication relative to KST issue date, plus first-seen fallback for undated feeds.
 day=date.fromisoformat(issue_day);end=datetime.combine(day+timedelta(days=1),datetime.min.time(),KST).astimezone(timezone.utc)
 start=end-timedelta(hours=36)
 rows=db.execute('''SELECT i.*,s.category,s.name FROM journal_items i JOIN journal_sources s ON s.id=i.source_id
  WHERE COALESCE(i.published_at,i.first_seen)>=? AND COALESCE(i.published_at,i.first_seen)<?
  ORDER BY COALESCE(i.published_at,i.first_seen) DESC LIMIT 100''',(start.isoformat(),end.isoformat())).fetchall()
 # balanced by category, no repeated link/title; source original title preserved, no fabricated claim
 selected=[];percat={};seen=set()
 for r in rows:
  cat=r['category'];key=re.sub(r'\W+','',r['title']).lower()[:110]
  if percat.get(cat,0)>=4 or key in seen:continue
  selected.append(dict(r));percat[cat]=percat.get(cat,0)+1;seen.add(key)
  if len(selected)>=16:break
 return selected

def create_draft(db,issue_day=None,force=False):
 day=issue_day or today_kst()
 date.fromisoformat(day)
 old=db.execute('SELECT * FROM journal_drafts WHERE issue_day=?',(day,)).fetchone()
 if old and not force:return dict(old)
 if old and old['status'] in ('approved','in_review'):raise ValueError('검토 또는 승인 중인 초안은 덮어쓰지 않습니다.')
 items=select_for_day(db,day)
 subject=f'[LAWYGO DAILY BRIEF] {day} 경제·제도 브리핑 (편집 초안)'
 lines=[f'LAWYGO JOURNAL — {day}', '경제와 제도, 법률적 맥락을 함께 읽는 일일 브리핑', '', '※ 편집자 검토 전 초안입니다. 제목은 수집된 원문을 그대로 반영하며, 법률적 해석은 작성하지 않습니다.', '']
 if not items:
  lines.extend(['오늘 기준 신규 기사를 확인하지 못했습니다.', '편집자가 수집 상태를 점검한 뒤 발행 여부를 결정해야 합니다.'])
 else:
  group={}
  for x in items:group.setdefault(x['category'],[]).append(x)
  for cat,rows in group.items():
   lines.append('■ '+cat)
   for x in rows:
    lines.append('• '+x['title'])
    lines.append('  출처: '+x['name'])
    lines.append('  원문: '+x['url'])
    # feed summaries are not copied into draft beyond titles
   lines.append('')
  lines.extend(['편집자 검토 체크리스트', '□ 기사 내용·발행일·원문 링크 확인', '□ 경제 전망·법적 판단을 원문 사실과 분리', '□ 중복 기사·광고성 콘텐츠 검토', '□ 월 2회 무료 뉴스레터에 반영할 항목 선택'])
 record=(uuid.uuid4().hex,day,subject,'\n'.join(lines),json.dumps([r['id'] for r in items]),len(items),'draft','rule-based',None,stamp(),stamp())
 if old:
  db.execute('UPDATE journal_drafts SET subject=?,body=?,source_ids_json=?,source_count=?,status=?,generator=?,editor_id=NULL,updated_at=? WHERE issue_day=?',(
   subject,record[3],record[4],len(items),'draft','rule-based',stamp(),day))
 else:db.execute('INSERT INTO journal_drafts VALUES(?,?,?,?,?,?,?,?,?,?,?)',record)
 return dict(db.execute('SELECT * FROM journal_drafts WHERE issue_day=?',(day,)).fetchone())

def enhance_draft_ai(db, draft_id, post=None):
    """Optional cost-bearing Gemini enhancement; preserves source links; editor-review only."""
    if os.getenv('LAWYGO_EDITORIAL_AI_ENABLED','').lower() != 'true' or not os.getenv('GEMINI_API_KEY'):
        raise ValueError('AI 초안 기능을 활성화하고 API 키를 등록해야 합니다.')
    draft = db.execute('SELECT * FROM journal_drafts WHERE id=?', (draft_id,)).fetchone()
    if not draft: raise ValueError('초안을 찾을 수 없습니다.')
    if draft['status'] != 'draft': raise ValueError('검토 중이거나 승인된 초안은 덮어쓰지 않습니다.')
    ids = json.loads(draft['source_ids_json'])
    if not ids: raise ValueError('검증 가능한 수집 기사가 없습니다.')
    placeholders = ','.join('?' for _ in ids)
    rows = db.execute('SELECT i.id,i.title,i.summary,i.url,s.name FROM journal_items i JOIN journal_sources s ON i.source_id=s.id WHERE i.id IN ('+placeholders+')', ids).fetchall()
    if not rows: raise ValueError('기사 출처를 확인할 수 없습니다.')
    sources = '\n'.join(f'[{i+1}] {r["title"]} | {r["name"]} | {r["summary"][:180]}' for i,r in enumerate(rows))
    prompt = (
        '당신은 경제·증권·법률 정보 저널의 편집 보조입니다. 제공한 RSS 제목·요약만 근거로 한국어로 600~1000자의 독자적인 초안을 작성하세요. '
        '검증되지 않은 수치·법조문·사건을 만들지 말고, 투자 추천과 법률 자문을 하지 마세요. '
        '문단마다 [숫자] 근거를 붙이고 원문 검증 전임을 표시하세요. 기사 본문은 복제하지 마세요.\n'
        + sources
    )
    api_post = post or httpx.post
    model = os.getenv('LAWYGO_EDITORIAL_GEMINI_MODEL', 'gemini-2.5-flash')
    if not re.fullmatch(r'gemini-[a-z0-9.-]{3,40}', model): raise ValueError('잘못된 Gemini 모델 설정')
    response = api_post(
        'https://generativelanguage.googleapis.com/v1beta/models/'+model+':generateContent',
        headers={'x-goog-api-key':os.environ['GEMINI_API_KEY'], 'Content-Type':'application/json'},
        json={'contents':[{'parts':[{'text':prompt}]}], 'generationConfig':{'temperature':0.2,'maxOutputTokens':1600}}, timeout=28)
    response.raise_for_status()
    result=response.json()
    try: generated='\n'.join(x.get('text','') for x in result['candidates'][0]['content']['parts']).strip()[:9500]
    except (KeyError, IndexError, TypeError): raise ValueError('AI 답변 형식을 확인할 수 없습니다.')
    if len(generated)<50: raise ValueError('AI 분석이 충분하지 않습니다.')
    links='\n'.join(f'[{i+1}] {r["name"]}: {r["url"]}' for i,r in enumerate(rows))
    body='LAWYGO JOURNAL / AI 편집 초안 — 사실 검증 전\n\n'+generated+'\n\n[원문 출처 — 자동 첨부, 편집자 검증 필요]\n'+links
    db.execute('UPDATE journal_drafts SET body=?,generator=?,updated_at=? WHERE id=?', (body,'gemini-assisted',stamp(),draft_id))
    return dict(db.execute('SELECT * FROM journal_drafts WHERE id=?',(draft_id,)).fetchone())

class DraftState(BaseModel):
 expected_updated_at:str|None=None
 status:str=Field(pattern='^(in_review|approved|archived|draft)$')
 body:str|None=Field(default=None,max_length=32000)
 subject:str|None=Field(default=None,max_length=200)

class SourceState(BaseModel):
 enabled:bool

def register(app,g):
 database=g['database'];csrf=g['csrf'];current=g['current_user'];err=g['err'];audit=g['audit'];transaction=g['transaction']
 @app.get('/api/journal/news')
 def news(limit:int=24,category:str='',db=Depends(database)):
  limit=min(max(limit,1),70)
  where='WHERE s.category=?' if category else ''
  rows=db.execute(f'''SELECT i.title,i.url,i.summary,i.published_at,i.first_seen,s.name AS source,s.category
    FROM journal_items i JOIN journal_sources s ON s.id=i.source_id {where}
    ORDER BY COALESCE(i.published_at,i.first_seen) DESC LIMIT ?''',((category,limit) if category else (limit,))).fetchall()
  return {'items':[dict(r) for r in rows],'note':'외부 RSS 제목·링크, 출처 원문에서 사실 확인 필요'}
 @app.get('/api/journal/sources')
 def sources(user=Depends(current),db=Depends(database)):
  if user['role'] not in ('admin','editor'):err(403,'편집자 권한 필요')
  return {'items':[dict(s) for s in db.execute('SELECT * FROM journal_sources ORDER BY category,id')],
   'recent':[dict(x) for x in db.execute('SELECT * FROM journal_fetches ORDER BY checked_at DESC LIMIT 20')]}
 @app.patch('/api/journal/sources/{sid}')
 def source_state(sid:str,body:SourceState,user=Depends(csrf),db=Depends(database)):
  if user['role']!='admin':err(403,'관리자만 변경 가능')
  if not db.execute('SELECT id FROM journal_sources WHERE id=?',(sid,)).fetchone():err(404,'RSS 미등록')
  db.execute('UPDATE journal_sources SET enabled=?,updated_at=? WHERE id=?',(int(body.enabled),stamp(),sid))
  audit(db,user,'toggle_source','journal_source',sid,{'enabled':body.enabled})
  return {'ok':True}
 @app.post('/api/journal/collect')
 def manual_collect(user=Depends(csrf),db=Depends(database)):
  if user['role'] not in ('admin','editor'):err(403,'편집자 권한 필요')
  result=collect(db)
  audit(db,user,'collect','journal_source','batch',{'ok':sum(r['status']=='ok' for r in result)})
  return {'items':result}
 @app.get('/api/journal/drafts')
 def drafts(user=Depends(current),db=Depends(database)):
  if user['role'] not in ('admin','editor'):err(403,'편집자 권한 필요')
  return {'items':[dict(x) for x in db.execute('SELECT * FROM journal_drafts ORDER BY issue_day DESC LIMIT 70')]}
 @app.post('/api/journal/drafts/today')
 def today(user=Depends(csrf),db=Depends(database)):
  if user['role'] not in ('admin','editor'):err(403,'편집자 권한 필요')
  try:r=create_draft(db)
  except ValueError as e:err(409,str(e))
  audit(db,user,'draft','journal_draft',r['id'])
  return {'item':r}
 @app.patch('/api/journal/drafts/{draft_id}')
 def edit_draft(draft_id:str,body:DraftState,user=Depends(csrf),db=Depends(database)):
  if user['role'] not in ('admin','editor'):err(403,'편집자 권한 필요')
  rec=db.execute('SELECT * FROM journal_drafts WHERE id=?',(draft_id,)).fetchone()
  if not rec:err(404,'초안이 없습니다.')
  if body.expected_updated_at and rec['updated_at']!=body.expected_updated_at:err(409,'다른 편집자가 먼저 수정했습니다. 새로고침 후 재검토하세요.')
  if body.status=='approved' and user['role']!='admin':err(403,'최종 승인 권한은 관리자에게 있습니다.')
  if body.status=='approved' and rec['source_count']<1:err(409,'근거 기사 없는 빈 초안은 승인할 수 없습니다.')
  with transaction(db):
   changed=db.execute('UPDATE journal_drafts SET status=?,body=?,subject=?,editor_id=?,updated_at=? WHERE id=? AND updated_at=?',(
    body.status,body.body if body.body is not None else rec['body'],body.subject if body.subject is not None else rec['subject'],user['id'],stamp(),draft_id,rec['updated_at']))
   if changed.rowcount != 1:err(409,'초안이 다른 편집자에 의해 변경됐습니다. 내용을 다시 불러오세요.')
   db.execute('INSERT INTO journal_draft_history VALUES(?,?,?,?,?,?,?)',(uuid.uuid4().hex,draft_id,user['id'],rec['status'],rec['subject'],rec['body'],stamp()))
   audit(db,user,'review','journal_draft',draft_id,{'status':body.status})
  return {'ok':True}
 @app.post('/api/journal/drafts/{draft_id}/ai')
 def ai_generate(draft_id:str,user=Depends(csrf),db=Depends(database)):
  if user['role'] not in ('admin','editor'):err(403,'편집자 권한 필요')
  try: result=enhance_draft_ai(db,draft_id)
  except ValueError as e:err(409,str(e))
  except (httpx.HTTPError,KeyError):err(502,'AI API 연결 또는 출력 형식 확인 실패')
  audit(db,user,'ai_draft','journal_draft',draft_id,{'generator':result['generator']})
  return {'item':result,'notice':'AI 초안은 자동 발송되지 않으며 편집자의 사실 검증이 필요합니다.'}
 @app.get('/api/journal/stats')
 def stats(user=Depends(current),db=Depends(database)):
  if user['role'] not in ('admin','editor'):err(403,'편집자 권한 필요')
  return {'articles':db.execute('SELECT COUNT(*) FROM journal_items').fetchone()[0],
   'drafts':db.execute('SELECT COUNT(*) FROM journal_drafts').fetchone()[0],
   'failed_sources':db.execute("SELECT COUNT(*) FROM journal_fetches WHERE status='failed'").fetchone()[0]}
