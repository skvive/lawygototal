"""LAWYGO v2: Google OIDC, read-only Blogger/YouTube ingestion, grounded AI,
server-to-server native board publishing bridge. Credentials never leave server.

Operational integration requires real OAuth client credentials and service deployment.
External API requests are exercised by deterministic mocked HTTP tests; no live keys.
"""
from __future__ import annotations

import base64
import hashlib
import html
import json
import os
import re
import secrets
import time
import uuid
from datetime import datetime, timezone
from html.parser import HTMLParser
from urllib.parse import urlencode, urlparse

import httpx
from cryptography.fernet import Fernet, InvalidToken
from fastapi import Body, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field

GOOGLE_AUTH = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN = 'https://oauth2.googleapis.com/token'
BLOGGER_BASE = 'https://www.googleapis.com/blogger/v3'
YOUTUBE_BASE = 'https://www.googleapis.com/youtube/v3'
SCOPES = {
    'login': ['openid','email','profile'],
    'blogger': ['openid','email','https://www.googleapis.com/auth/blogger.readonly'],
    'youtube': ['openid','email','https://www.googleapis.com/auth/youtube.readonly'],
}
UA = 'LAWYGO/2.0 (server-side authorized integration)'

class _StripHTML(HTMLParser):
    def __init__(self):super().__init__(convert_charrefs=True);self.s=[]
    def handle_data(self,data):self.s.append(data)
    def get(self):return ' '.join(' '.join(self.s).split())

def plain_html(markup: str) -> str:
    x=_StripHTML();x.feed(markup or '');return x.get()[:20000]

def _now():return datetime.now(timezone.utc).isoformat()

def _hash(token):return hashlib.sha256(token.encode()).hexdigest()

def _require_config(*keys):
    if not all(os.getenv(k) for k in keys):
        raise HTTPException(503,'해당 외부 연동의 서버 환경변수가 아직 설정되지 않았습니다.')

def _cipher():
    key=os.getenv('LAWYGO_TOKEN_ENCRYPTION_KEY','')
    if not key:raise HTTPException(503,'외부 계정 암호화 키가 설정되지 않았습니다.')
    try:return Fernet(key.encode())
    except Exception:raise HTTPException(503,'외부 계정 암호화 키 형식이 올바르지 않습니다.')

def _oauth_cfg():
    _require_config('GOOGLE_CLIENT_ID','GOOGLE_CLIENT_SECRET','GOOGLE_REDIRECT_URI')
    redirect=os.environ['GOOGLE_REDIRECT_URI']
    p=urlparse(redirect)
    # The callback URI must be a configured HTTPS URL, except localhost development.
    if p.scheme!='https' and not (p.scheme=='http' and p.hostname in ('localhost','127.0.0.1')):
        raise HTTPException(503,'Google OAuth 콜백 주소에 HTTPS가 필요합니다.')
    return os.environ['GOOGLE_CLIENT_ID'],os.environ['GOOGLE_CLIENT_SECRET'],redirect

def _google_exchange(code, verifier):
    cid,secret,callback=_oauth_cfg()
    with httpx.Client(timeout=15) as c:
        res=c.post(GOOGLE_TOKEN,data={'client_id':cid,'client_secret':secret,'redirect_uri':callback,'grant_type':'authorization_code','code':code,'code_verifier':verifier})
        res.raise_for_status();return res.json()

def _google_refresh(refresh_token):
    cid,secret,_=_oauth_cfg()
    with httpx.Client(timeout=15) as c:
        res=c.post(GOOGLE_TOKEN,data={'client_id':cid,'client_secret':secret,'grant_type':'refresh_token','refresh_token':refresh_token})
        res.raise_for_status();return res.json()

def _verify_id_token(raw):
    if not raw:raise ValueError('Google 신원 토큰이 없습니다.')
    from google.oauth2 import id_token
    from google.auth.transport.requests import Request as GoogleRequest
    claims=id_token.verify_oauth2_token(raw,GoogleRequest(),os.getenv('GOOGLE_CLIENT_ID'))
    if claims.get('iss') not in ('https://accounts.google.com','accounts.google.com'):
        raise ValueError('Google 발급자가 일치하지 않습니다.')
    if not claims.get('email_verified') or not claims.get('sub'):
        raise ValueError('인증된 Google 이메일과 주체 식별자가 필요합니다.')
    return claims

def _google_get(url,access_token,params):
    # Server-controlled API base/paths only; never fetch a user-supplied URL.
    if not url.startswith((BLOGGER_BASE+'/',YOUTUBE_BASE+'/')):raise ValueError('허용되지 않은 Google API 경로')
    with httpx.Client(timeout=16) as c:
        r=c.get(url,params=params,headers={'Authorization':'Bearer '+access_token,'User-Agent':UA})
        r.raise_for_status();return r.json()

def ensure_schema(db):
    db.executescript('''
    CREATE TABLE IF NOT EXISTS native_identity_links (
      user_id TEXT PRIMARY KEY REFERENCES users(id),native_user_id TEXT NOT NULL UNIQUE,
      native_tenant TEXT NOT NULL,created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS google_identity (
      user_id TEXT PRIMARY KEY REFERENCES users(id),google_sub TEXT NOT NULL UNIQUE,
      email TEXT NOT NULL,connected_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS google_oauth_pending (
      state_hash TEXT PRIMARY KEY,mode TEXT NOT NULL,user_id TEXT,
      verifier TEXT NOT NULL,created_at INTEGER NOT NULL);
    CREATE TABLE IF NOT EXISTS google_tokens (
      user_id TEXT NOT NULL REFERENCES users(id),provider TEXT NOT NULL,
      access_enc TEXT NOT NULL,refresh_enc TEXT,expires_at INTEGER NOT NULL,
      scopes TEXT NOT NULL,updated_at TEXT NOT NULL,
      PRIMARY KEY(user_id,provider));
    CREATE TABLE IF NOT EXISTS sync_sources (
      id TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),tenant TEXT NOT NULL,
      provider TEXT NOT NULL,external_id TEXT NOT NULL,title TEXT NOT NULL,
      created_at TEXT NOT NULL,last_sync_at TEXT,
      UNIQUE(user_id,provider,external_id));
    CREATE TABLE IF NOT EXISTS synced_items (
      id TEXT PRIMARY KEY,source_id TEXT NOT NULL REFERENCES sync_sources(id),external_id TEXT NOT NULL,
      post_id TEXT NOT NULL REFERENCES posts(id),content_hash TEXT NOT NULL,
      updated_at TEXT NOT NULL,UNIQUE(source_id,external_id));
    CREATE TABLE IF NOT EXISTS sync_runs (
      id TEXT PRIMARY KEY,source_id TEXT NOT NULL REFERENCES sync_sources(id),
      status TEXT NOT NULL,created_count INTEGER NOT NULL DEFAULT 0,
      updated_count INTEGER NOT NULL DEFAULT 0,created_at TEXT NOT NULL,error TEXT);
    CREATE TABLE IF NOT EXISTS ai_analysis_runs (
      id TEXT PRIMARY KEY,post_id TEXT NOT NULL REFERENCES posts(id),user_id TEXT NOT NULL REFERENCES users(id),
      provider TEXT NOT NULL,status TEXT NOT NULL,created_at TEXT NOT NULL,
      result_json TEXT,consent_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS native_publish_outbox (
      id TEXT PRIMARY KEY,post_id TEXT NOT NULL UNIQUE REFERENCES posts(id),
      tenant TEXT NOT NULL,action TEXT NOT NULL,revision INTEGER NOT NULL,
      status TEXT NOT NULL DEFAULT 'queued',attempts INTEGER NOT NULL DEFAULT 0,
      last_error TEXT,updated_at TEXT NOT NULL);
    ''')


def _user_session(db,user,response):
    # Uses existing v1 session cookie format and database; rotates every login.
    raw=secrets.token_urlsafe(36);csrf=secrets.token_urlsafe(32)
    db.execute('INSERT INTO sessions(id_hash,user_id,csrf_hash,expires_at) VALUES(?,?,?,?)',(
        _hash(raw),user['id'],_hash(csrf),int(time.time())+8*3600))
    secure=os.getenv('LAWYGO_SECURE_COOKIES')=='true'
    response.set_cookie('lawygo_cms_session',raw,httponly=True,secure=secure,samesite='lax',max_age=8*3600)
    response.set_cookie('lawygo_cms_csrf',csrf,httponly=False,secure=secure,samesite='lax',max_age=8*3600)

def _store_oauth_state(db,mode,user_id=None):
    verifier=secrets.token_urlsafe(48)
    state=secrets.token_urlsafe(36)
    db.execute('DELETE FROM google_oauth_pending WHERE created_at<?',(int(time.time())-600,))
    db.execute('INSERT INTO google_oauth_pending VALUES(?,?,?,?,?)',(_hash(state),mode,user_id,verifier,int(time.time())))
    challenge=base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b'=').decode()
    return state,challenge

def _access_token(db,user_id,provider):
    row=db.execute('SELECT * FROM google_tokens WHERE user_id=? AND provider=?',(user_id,provider)).fetchone()
    if not row:raise HTTPException(409,'먼저 Google 계정을 연결해 주세요.')
    try:
        f=_cipher();access=f.decrypt(row['access_enc'].encode()).decode()
    except InvalidToken:raise HTTPException(503,'Google 토큰 복호화에 실패했습니다.')
    if row['expires_at']>int(time.time())+90:return access
    if not row['refresh_enc']:raise HTTPException(409,'자동 갱신 권한이 없어 Google 계정을 다시 연결해야 합니다.')
    try:refresh=f.decrypt(row['refresh_enc'].encode()).decode()
    except InvalidToken:raise HTTPException(503,'갱신 토큰 복호화에 실패했습니다.')
    try:data=_google_refresh(refresh)
    except Exception:raise HTTPException(502,'Google 토큰 자동 갱신에 실패했습니다. 다시 연결해 주세요.')
    access=data['access_token'];newrefresh=data.get('refresh_token') or refresh
    db.execute('UPDATE google_tokens SET access_enc=?,refresh_enc=?,expires_at=?,updated_at=? WHERE user_id=? AND provider=?',(
        f.encrypt(access.encode()).decode(),f.encrypt(newrefresh.encode()).decode(),int(time.time())+int(data.get('expires_in',3600)),_now(),user_id,provider))
    return access

def _store_tokens(db,user_id,provider,tokens):
    _cipher()
    scopes=set((tokens.get('scope') or '').split())
    needed=SCOPES[provider][2] if len(SCOPES[provider])>2 else None
    if needed and needed not in scopes:raise HTTPException(403,'Google에서 요청한 읽기 권한이 승인되지 않았습니다.')
    f=_cipher()
    previous=db.execute('SELECT refresh_enc FROM google_tokens WHERE user_id=? AND provider=?',(user_id,provider)).fetchone()
    refresh_enc=f.encrypt(tokens['refresh_token'].encode()).decode() if tokens.get('refresh_token') else (previous['refresh_enc'] if previous else None)
    db.execute('''INSERT INTO google_tokens VALUES(?,?,?,?,?,?,?) ON CONFLICT(user_id,provider)
      DO UPDATE SET access_enc=excluded.access_enc,refresh_enc=excluded.refresh_enc,
      expires_at=excluded.expires_at,scopes=excluded.scopes,updated_at=excluded.updated_at''',(
      user_id,provider,f.encrypt(tokens['access_token'].encode()).decode(),refresh_enc,
      int(time.time())+int(tokens.get('expires_in',3600)),json.dumps(sorted(scopes)),_now()))


def _sanitize_item(title,body,url):
    title=html.unescape(str(title or '').strip())[:180]
    body=plain_html(str(body or ''))[:18000]
    url=str(url or '')
    p=urlparse(url)
    if p.scheme!='https' or not p.hostname or p.username or p.password:
        raise ValueError('외부 콘텐츠 URL이 HTTPS가 아닙니다.')
    return title if len(title)>1 else '제목 없는 원문',body or '외부 채널에서 불러온 콘텐츠입니다.',url

def _fetch_items(provider,ext_id,token):
    # Both APIs use minimal list operations. YouTube fetches upload playlist rather than costly search.list.
    if provider=='blogger':
        data=_google_get(f'{BLOGGER_BASE}/blogs/{ext_id}/posts',token,{'maxResults':25,'fetchBodies':'true','status':'live'})
        return [{'id':str(x['id']),'title':x.get('title'), 'body':x.get('content'),'url':x.get('url'),'kind':'blog'} for x in data.get('items',[])]
    data=_google_get(f'{YOUTUBE_BASE}/playlistItems',token,{'part':'snippet,contentDetails','playlistId':ext_id,'maxResults':25})
    return [{'id':str(x.get('contentDetails',{}).get('videoId') or x.get('snippet',{}).get('resourceId',{}).get('videoId') or ''),
             'title':x.get('snippet',{}).get('title'),'body':x.get('snippet',{}).get('description',''),
             'url':'https://www.youtube.com/watch?v='+str(x.get('contentDetails',{}).get('videoId') or ''),'kind':'video'}
            for x in data.get('items',[]) if x.get('contentDetails',{}).get('videoId')]


def _sync_source(db,source):
    token=_access_token(db,source['user_id'],source['provider'])
    items=_fetch_items(source['provider'],source['external_id'],token)
    board_slug='blogs' if source['provider']=='blogger' else 'shorts'
    board=db.execute('SELECT * FROM boards WHERE tenant=? AND product=? AND slug=? AND deleted_at IS NULL',(
      source['tenant'],'pan',board_slug)).fetchone()
    if not board:raise ValueError('LAWYGO PAN 게시판이 준비되지 않았습니다.')
    run=uuid.uuid4().hex;created=updated=0
    for item in items[:25]:
        try:title,body,url=_sanitize_item(item['title'],item['body'],item['url'])
        except (ValueError,TypeError):continue
        digest=hashlib.sha256(json.dumps([title,body,url],ensure_ascii=False).encode()).hexdigest()
        ext=str(item['id'])[:128]
        if not ext:continue
        prev=db.execute('SELECT * FROM synced_items WHERE source_id=? AND external_id=?',(source['id'],ext)).fetchone()
        if prev and prev['content_hash']==digest:continue
        ts=_now()
        # Content never becomes public automatically; a human editor must approve every change.
        if prev:
            p=db.execute('SELECT * FROM posts WHERE id=? AND tenant=?',(prev['post_id'],source['tenant'])).fetchone()
            if not p or p['deleted_at']:continue
            db.execute('''UPDATE posts SET title=?,body=?,summary=?,external_url=?,status='pending',
              version=version+1,updated_at=?,published_at=NULL WHERE id=?''',(
              title,body[:40000],body[:400],url,ts,p['id']))
            db.execute('UPDATE synced_items SET content_hash=?,updated_at=? WHERE id=?',(digest,ts,prev['id']))
            updated+=1
        else:
            post_id=uuid.uuid4().hex
            db.execute('''INSERT INTO posts(id,tenant,board_id,product,kind,title,body,summary,external_url,
              author_id,status,visibility,is_sponsored,created_at,updated_at)
              VALUES(?,?,?,?,?,?,?,?,?,?,?, ?,?,?,?)''',(
              post_id,source['tenant'],board['id'],'pan',item['kind'],title,body,body[:400],url,
              source['user_id'],'pending','public',0,ts,ts))
            db.execute('INSERT INTO synced_items VALUES(?,?,?,?,?,?)',(uuid.uuid4().hex,source['id'],ext,post_id,digest,ts));created+=1
    db.execute('UPDATE sync_sources SET last_sync_at=? WHERE id=?',(_now(),source['id']))
    db.execute('INSERT INTO sync_runs VALUES(?,?,?,?,?,?,?)',(run,source['id'],'ok',created,updated,_now(),None))
    return {'run_id':run,'created':created,'updated':updated,'fetched':len(items),'status':'ok'}

SYNC_INTERVAL_SEC = 6 * 3600


def run_scheduled_syncs(db, *, force: bool = False) -> dict:
    """Run Google sync for all registered sources (cron/worker). Respects 6h interval unless force."""
    summary = {'sources': 0, 'created': 0, 'updated': 0, 'skipped': 0, 'errors': 0, 'details': []}
    rows = db.execute('SELECT * FROM sync_sources ORDER BY created_at').fetchall()
    for row in rows:
        source = dict(row)
        if not force and source.get('last_sync_at'):
            try:
                elapsed = (datetime.now(timezone.utc) - datetime.fromisoformat(source['last_sync_at'])).total_seconds()
                if elapsed < SYNC_INTERVAL_SEC:
                    summary['skipped'] += 1
                    continue
            except ValueError:
                pass
        summary['sources'] += 1
        try:
            result = _sync_source(db, source)
            summary['created'] += result['created']
            summary['updated'] += result['updated']
            summary['details'].append({'source_id': source['id'], 'title': source['title'], **result})
        except Exception as exc:
            summary['errors'] += 1
            rid = uuid.uuid4().hex
            db.execute(
                'INSERT INTO sync_runs(id,source_id,status,created_count,updated_count,created_at,error) VALUES(?,?,?,?,?,?,?)',
                (rid, source['id'], 'error', 0, 0, _now(), type(exc).__name__),
            )
            summary['details'].append({'source_id': source['id'], 'status': 'error', 'error': type(exc).__name__})
    return summary


def integration_flags():
    return {
        'google_oauth': bool(os.getenv('GOOGLE_CLIENT_ID') and os.getenv('GOOGLE_CLIENT_SECRET')),
        'token_encryption': bool(os.getenv('LAWYGO_TOKEN_ENCRYPTION_KEY')),
        'gemini': bool(os.getenv('GEMINI_API_KEY')),
        'native_bridge': bool(os.getenv('LAWYGO_NATIVE_BRIDGE_URL') and len(os.getenv('LAWYGO_NATIVE_BRIDGE_SECRET', '')) >= 32),
        'native_membership': bool(os.getenv('LAWYGO_NATIVE_IDENTITY_URL') or os.getenv('LAWYGO_REQUIRE_NATIVE_MEMBERSHIP') != 'true'),
        'cron_configured': bool(os.getenv('LAWYGO_CRON_SECRET')),
        'sync_interval_hours': SYNC_INTERVAL_SEC // 3600,
    }


def _gemini_analyze(source_text,refs):
    key=os.getenv('GEMINI_API_KEY','')
    if not key:raise HTTPException(503,'법률 AI API 키가 연결되지 않았습니다. 근거 없는 AI 결과를 표시하지 않습니다.')
    model=os.getenv('GEMINI_MODEL','gemini-2.5-flash')
    if not re.fullmatch(r'[a-zA-Z0-9.\-_]+',model):raise HTTPException(503,'모델 이름 설정을 확인해 주세요.')
    instruction=(
      '당신은 법률 문서의 근거 중심 분석 보조자입니다. 변호사 자문을 대체하지 않습니다. '
      '자료에 없는 법령 조항·판례 번호·인용문·사실을 절대 만들어내지 마세요. '
      '오직 제공된 [SOURCE] 텍스트에 기초하여 쟁점, 주요 사실, 부족한 증거, 확인할 질문을 추출하세요. '
      '모든 핵심 쟁점에는 source_ids 배열로 주어진 출처 식별자만 기재하세요. '
      '근거가 부족하면 명시적으로 불명확하다고 설명하세요. JSON만 출력하세요. '
      '출력 JSON 형식: {"summary":"...", "issues":[{"issue":"...","source_ids":["source-1"]}],'
      '"evidence_gaps":["..."],"questions":["..."],"disclaimer":"전문가 검토 필요"}.'
    )
    payload={'systemInstruction':{'parts':[{'text':instruction}]},'contents':[{'role':'user','parts':[{'text':'[SOURCE] '+json.dumps(refs,ensure_ascii=False)+'\n\n'+source_text[:30000]}]}],
      'generationConfig':{'temperature':0.1,'responseMimeType':'application/json','maxOutputTokens':3500}}
    try:
        with httpx.Client(timeout=55) as c:
            r=c.post(f'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent',
              headers={'x-goog-api-key':key,'Content-Type':'application/json'},json=payload)
            r.raise_for_status();data=r.json()
        raw=data['candidates'][0]['content']['parts'][0]['text'];obj=json.loads(raw)
        allowed={x['id'] for x in refs};issues=obj.get('issues',[])
        if not isinstance(issues,list):raise ValueError('issues 배열이 없습니다.')
        for i in issues:
            if not isinstance(i,dict) or not set(i.get('source_ids',[])).issubset(allowed):
                raise ValueError('유효하지 않은 출처 식별자입니다.')
        return {k:obj.get(k,[] if k in ('issues','evidence_gaps','questions') else '') for k in ('summary','issues','evidence_gaps','questions','disclaimer')}
    except (httpx.HTTPError,KeyError,IndexError,ValueError,TypeError,json.JSONDecodeError):
        raise HTTPException(502,'AI 분석 결과를 검증할 수 없습니다. 재시도하거나 원문을 확인해 주세요.')


def _ensure_member_boards(db,tenant):
    # Provision product boards for authenticated LAWYGO organization, never cross tenant.
    groups={
      'channel':[('news','경제·법률 뉴스'),('clips','법률 영상'),('insight','전문가 칼럼')],
      'wiki':[('encyclopedia','법률백과'),('precedents','판례'),('laws','법령·제도')],
      'pan':[('lawyers','변호사 프로필'),('blogs','Google 블로그'),('shorts','YouTube 쇼츠'),('sponsored','광고·프로모션')],
      'note':[('projects','개인 연구 노트'),('drafts','문서 초안'),('sources','업로드 자료')],
    }
    for product,boards in groups.items():
        for order,(slug,title) in enumerate(boards):
            db.execute('''INSERT OR IGNORE INTO boards(id,tenant,product,slug,name,sort_order,created_at,updated_at)
               VALUES(?,?,?,?,?,?,?,?)''',(uuid.uuid4().hex,tenant,product,slug,title,order,_now(),_now()))

def _native_identity_lookup(google_sub):
    """Optional approved member mapping from already verified Google subject."""
    url=os.getenv('LAWYGO_NATIVE_IDENTITY_URL','')
    if not url:
        if os.getenv('LAWYGO_REQUIRE_NATIVE_MEMBERSHIP')=='true':
            raise HTTPException(503,'LAWYGO 회원 확인 API가 아직 연결되지 않았습니다.')
        return None
    secret=os.getenv('LAWYGO_NATIVE_BRIDGE_SECRET','')
    if len(secret)<32:raise HTTPException(503,'LAWYGO 회원 연결 인증키가 필요합니다.')
    if urlparse(url).scheme!='https' and not url.startswith('http://127.0.0.1:'):
        raise HTTPException(503,'회원 확인 요청은 HTTPS로만 전송합니다.')
    try:
        with httpx.Client(timeout=15,follow_redirects=False) as client:
            r=client.post(url,headers={'Authorization':'Bearer '+secret},json={'googleSub':google_sub})
            if r.status_code==404:
                raise HTTPException(403,'기존 LAWYGO에서 가입·승인된 Google 회원이 아닙니다.')
            r.raise_for_status();data=r.json()
            if not data.get('active') or not data.get('id') or not data.get('tenant'):
                raise HTTPException(403,'LAWYGO 회원 상태가 승인되지 않았습니다.')
            return {'id':str(data['id']),'tenant':str(data['tenant'])}
    except HTTPException:raise
    except (httpx.HTTPError,KeyError,ValueError,TypeError):
        raise HTTPException(502,'LAWYGO 운영 회원 상태를 확인하지 못했습니다.')

def _bridge_publish(message):
    url=os.getenv('LAWYGO_NATIVE_BRIDGE_URL','')
    secret=os.getenv('LAWYGO_NATIVE_BRIDGE_SECRET','')
    if not url or len(secret)<32:raise HTTPException(503,'네이티브 게시판 브리지 서버가 설정되지 않았습니다.')
    if urlparse(url).scheme!='https' and not url.startswith('http://127.0.0.1:'):
        raise HTTPException(503,'운영 브리지에는 HTTPS가 필요합니다.')
    # Do not send secrets to a redirect destination.
    with httpx.Client(timeout=20,follow_redirects=False) as c:
        r=c.post(url,headers={'Authorization':'Bearer '+secret,'Content-Type':'application/json'},json=message)
        r.raise_for_status();return r.json()

class SyncAdd(BaseModel):
    provider:str
    external_id:str=Field(min_length=2,max_length=150)
    title:str=Field(min_length=2,max_length=160)

class AiConsent(BaseModel):
    consent:bool


def register(app,g):
    database=g['database'];csrf=g['csrf'];current_user=g['current_user'];optional_user=g['optional_user']
    get_post=g['get_post'];err=g['err'];audit=g['audit'];connect=g['connect'];transaction=g['transaction'];FILES=g['FILES'];now=g['now']

    @app.get('/api/google/login')
    def google_login_start(db=Depends(database)):
        cid,_,callback=_oauth_cfg();state,challenge=_store_oauth_state(db,'login')
        url=GOOGLE_AUTH+'?'+urlencode({'client_id':cid,'redirect_uri':callback,'response_type':'code','scope':' '.join(SCOPES['login']),
          'state':state,'access_type':'online','code_challenge':challenge,'code_challenge_method':'S256','prompt':'select_account'})
        return RedirectResponse(url, status_code=302)

    @app.get('/api/google/connect/{provider}')
    def connect_google(provider:str,user=Depends(current_user),db=Depends(database)):
        if provider not in ('blogger','youtube'):err(400,'지원하지 않는 연결입니다.')
        cid,_,callback=_oauth_cfg();_cipher()
        state,challenge=_store_oauth_state(db,provider,user['id'])
        url=GOOGLE_AUTH+'?'+urlencode({'client_id':cid,'redirect_uri':callback,'response_type':'code','scope':' '.join(SCOPES[provider]),
           'state':state,'access_type':'offline','prompt':'consent','include_granted_scopes':'true',
           'code_challenge':challenge,'code_challenge_method':'S256'})
        return RedirectResponse(url,status_code=302)

    @app.get('/api/google/callback')
    def google_callback(req:Request,state:str='',code:str='',error:str='',db=Depends(database)):
        if error or not state or not code:err(400,'Google 인증이 취소되었거나 코드가 없습니다.')
        with transaction(db):
            row=db.execute('SELECT * FROM google_oauth_pending WHERE state_hash=? AND created_at>?',(_hash(state),int(time.time())-600)).fetchone()
            if not row:err(400,'만료되었거나 이미 사용한 인증 요청입니다.')
            db.execute('DELETE FROM google_oauth_pending WHERE state_hash=?',(_hash(state),))
        try:
            tokens=_google_exchange(code,row['verifier'])
            claims=_verify_id_token(tokens.get('id_token'))
        except (ValueError,KeyError,httpx.HTTPError):
            err(401,'Google 인증 정보 확인에 실패했습니다.')
        sub=str(claims['sub']);email=str(claims['email']).strip().lower()
        native_member=_native_identity_lookup(sub) if row['mode']=='login' else None
        if len(email)>254:err(400,'이메일이 너무 깁니다.')
        response=RedirectResponse('/dashboard?google=connected',status_code=302)
        with transaction(db):
            if row['mode']=='login':
                existing=db.execute('SELECT user_id FROM google_identity WHERE google_sub=?',(sub,)).fetchone()
                if existing:
                    user=db.execute('SELECT * FROM users WHERE id=?',(existing['user_id'],)).fetchone()
                else:
                    # Protect email-only legacy local accounts from silent account linking.
                    tenant=native_member['tenant'] if native_member else g['DEFAULT_TENANT']
                    taken=db.execute('SELECT 1 FROM users WHERE tenant=? AND email=?',(tenant,email)).fetchone()
                    if taken:err(409,'이메일을 사용 중인 계정이 있습니다. 기존 계정에서 Google 연결을 요청하세요.')
                    import uuid as _uuid
                    uid=_uuid.uuid4().hex
                    # Random unknown local password; Google accounts cannot password-login with a default credential.
                    db.execute('INSERT INTO users(id,tenant,email,password_hash,display_name,role,created_at) VALUES(?,?,?,?,?,?,?)',(
                        uid,tenant,email,g['PH'].hash(secrets.token_urlsafe(48)),str(claims.get('name') or email.split('@')[0])[:80],'contributor',_now()))
                    db.execute('INSERT INTO google_identity VALUES(?,?,?,?)',(uid,sub,email,_now()))
                    user=db.execute('SELECT * FROM users WHERE id=?',(uid,)).fetchone()
                if native_member:
                    if user['tenant']!=native_member['tenant']:
                        err(409,'기존 LAWYGO 회원 소속과 CMS 계정 소속이 다릅니다. 관리자에게 문의해 주세요.')
                    mapping=db.execute('SELECT native_user_id FROM native_identity_links WHERE user_id=?',(user['id'],)).fetchone()
                    if mapping and mapping['native_user_id']!=native_member['id']:
                        err(409,'다른 LAWYGO 계정으로 이미 연결돼 있습니다.')
                    if not mapping:db.execute('INSERT INTO native_identity_links VALUES(?,?,?,?)',(user['id'],native_member['id'],native_member['tenant'],_now()))
                    _ensure_member_boards(db,native_member['tenant'])
                _user_session(db,user,response)
            else:
                user=optional_user(req,db)
                if not user or user['id']!=row['user_id']:err(401,'연동 중 로그인 세션이 변경됐습니다.')
                bound=db.execute('SELECT user_id FROM google_identity WHERE google_sub=?',(sub,)).fetchone()
                if bound and bound['user_id']!=user['id']:err(409,'이미 다른 계정에 연결된 Google 계정입니다.')
                identity=db.execute('SELECT google_sub FROM google_identity WHERE user_id=?',(user['id'],)).fetchone()
                if identity and identity['google_sub']!=sub:err(403,'현재 계정과 다른 Google 계정은 연결할 수 없습니다.')
                if not identity:db.execute('INSERT INTO google_identity VALUES(?,?,?,?)',(user['id'],sub,email,_now()))
                _store_tokens(db,user['id'],row['mode'],tokens)
        return response

    @app.get('/api/google/connections')
    def google_connections(user=Depends(current_user),db=Depends(database)):
        rows=db.execute('SELECT provider,expires_at,updated_at FROM google_tokens WHERE user_id=?',(user['id'],)).fetchall()
        return {'items':[dict(x) for x in rows]}

    @app.delete('/api/google/connections/{provider}')
    def google_disconnect(provider:str,user=Depends(csrf),db=Depends(database)):
        if provider not in ('blogger','youtube'):err(400,'지원하지 않는 연결입니다.')
        with transaction(db):
            db.execute('DELETE FROM google_tokens WHERE user_id=? AND provider=?',(user['id'],provider))
            db.execute('DELETE FROM sync_sources WHERE user_id=? AND provider=? AND NOT EXISTS (SELECT 1 FROM synced_items WHERE synced_items.source_id=sync_sources.id)',(user['id'],provider))
            audit(db,user,'disconnect','google',provider)
        return {'ok':True,'notice':'로컬 연결 토큰 삭제. Google 계정에서 앱 액세스를 별도 취소할 수 있습니다.'}

    @app.get('/api/google/owned/{provider}')
    def google_owned(provider:str,user=Depends(current_user),db=Depends(database)):
        if provider not in ('blogger','youtube'):err(400,'지원하지 않는 서비스입니다.')
        token=_access_token(db,user['id'],provider)
        try:
            if provider=='blogger':
                d=_google_get(BLOGGER_BASE+'/users/self/blogs',token,{});
                return {'items':[{'id':str(x['id']),'name':x.get('name',''),'url':x.get('url','')} for x in d.get('items',[])]}
            d=_google_get(YOUTUBE_BASE+'/channels',token,{'part':'snippet,contentDetails','mine':'true','maxResults':50})
            return {'items':[{'id':x.get('contentDetails',{}).get('relatedPlaylists',{}).get('uploads',''),
                'name':x.get('snippet',{}).get('title',''),'channel_id':x['id']} for x in d.get('items',[]) if x.get('contentDetails',{}).get('relatedPlaylists',{}).get('uploads')]}
        except httpx.HTTPError:err(502,'Google 계정에서 채널 목록을 읽을 수 없습니다.')

    @app.get('/api/sync/sources')
    def sources(user=Depends(current_user),db=Depends(database)):
        return {'items':[dict(r) for r in db.execute('SELECT * FROM sync_sources WHERE user_id=? AND tenant=? ORDER BY created_at DESC',(user['id'],user['tenant']))]}

    @app.post('/api/sync/sources',status_code=201)
    def add_source(data:SyncAdd,user=Depends(csrf),db=Depends(database)):
        if data.provider not in ('blogger','youtube'):err(400,'Blogger와 YouTube만 연결할 수 있습니다.')
        if user['role']=='viewer':err(403,'읽기 전용 계정입니다.')
        token=_access_token(db,user['id'],data.provider)
        # Verify ownership by asking Google; supplied ID cannot select someone else's private channel.
        try:
            if data.provider=='blogger':d=_google_get(BLOGGER_BASE+'/users/self/blogs',token,{})
            else:d=_google_get(YOUTUBE_BASE+'/channels',token,{'part':'snippet,contentDetails','mine':'true','maxResults':50})
        except httpx.HTTPError:err(502,'Google 채널 소유권 조회에 실패했습니다.')
        ids=([str(x['id']) for x in d.get('items',[])] if data.provider=='blogger' else
             [str(x.get('contentDetails',{}).get('relatedPlaylists',{}).get('uploads','')) for x in d.get('items',[])])
        if data.external_id not in ids:err(403,'본인이 관리하는 Google 채널만 등록할 수 있습니다.')
        sid=uuid.uuid4().hex
        try:
            db.execute('INSERT INTO sync_sources(id,user_id,tenant,provider,external_id,title,created_at) VALUES(?,?,?,?,?,?,?)',(
                sid,user['id'],user['tenant'],data.provider,data.external_id,data.title,_now()))
        except Exception:err(409,'이미 등록된 채널입니다.')
        return {'id':sid,'status':'connected'}

    @app.post('/api/sync/sources/{source_id}/run')
    def run_source(source_id:str,user=Depends(csrf),db=Depends(database)):
        source=db.execute('SELECT * FROM sync_sources WHERE id=? AND user_id=? AND tenant=?',(source_id,user['id'],user['tenant'])).fetchone()
        if not source:err(404,'연결된 채널이 없습니다.')
        if source['last_sync_at'] and (datetime.now(timezone.utc)-datetime.fromisoformat(source['last_sync_at'])).total_seconds()<60:
            err(429,'동일 채널은 1분 간격으로 동기화할 수 있습니다.')
        try:
            with transaction(db):result=_sync_source(db,source)
            audit(db,user,'sync','source',source_id,{'created':result['created'],'updated':result['updated']})
            return result
        except HTTPException:raise
        except (httpx.HTTPError,ValueError,KeyError,TypeError):
            err(502,'Google 콘텐츠 동기화에 실패했습니다. 채널 및 API 권한을 확인해 주세요.')

    @app.get('/api/sync/runs')
    def sync_run_logs(user=Depends(current_user),db=Depends(database)):
        rows=db.execute('''SELECT r.* FROM sync_runs r JOIN sync_sources s ON s.id=r.source_id
            WHERE s.user_id=? AND s.tenant=? ORDER BY r.created_at DESC LIMIT 50''',(user['id'],user['tenant'])).fetchall()
        return {'items':[dict(x) for x in rows]}

    @app.post('/api/note/{post_id}/ai-analyze')
    def ai_analyze(post_id:str,data:AiConsent,user=Depends(csrf),db=Depends(database)):
        if not data.consent:err(400,'외부 AI 분석을 위한 문서 전송 동의가 필요합니다.')
        p=get_post(db,post_id,user['tenant'])
        if p['product']!='note' or p['author_id']!=user['id'] or p['deleted_at']:err(404,'본인의 비공개 법률 노트가 아닙니다.')
        source=p['body'];refs=[{'id':'source-note','title':p['title']}]
        for m in db.execute('SELECT * FROM media WHERE post_id=? AND tenant=? AND mime=? ORDER BY created_at LIMIT 3',(
             post_id,user['tenant'],'application/pdf')):
            try:
                from io import BytesIO
                from pypdf import PdfReader
                doc=PdfReader(BytesIO((FILES/m['safe_name']).read_bytes()))
                text='\n'.join(page.extract_text() or '' for page in doc.pages[:10])[:15000]
                if text:
                    source+='\n\n[SOURCE '+m['id']+'] '+text
                    refs.append({'id':m['id'],'title':m['original_name']})
            except Exception:pass
        if len(source.strip())<15:err(422,'분석 가능한 원문이 부족합니다. 텍스트 PDF 또는 본문을 입력해 주세요.')
        # No forwarding before explicit user consent, no secret in output, no false case cites.
        obj=_gemini_analyze(source,refs)
        rid=uuid.uuid4().hex
        db.execute('INSERT INTO ai_analysis_runs VALUES(?,?,?,?,?,?,?,?)',(
          rid,post_id,user['id'],'gemini','completed',_now(),json.dumps(obj,ensure_ascii=False),_now()))
        audit(db,user,'analyze','note',post_id,{'provider':'gemini','source_count':len(refs)})
        return {'id':rid,'result':obj,'sources':refs,'notice':'AI 생성 내용은 법률 자문이 아니며 원문·최신 법령·판례를 전문가가 검증해야 합니다.'}

    @app.get('/api/note/{post_id}/ai-runs')
    def ai_runs(post_id:str,user=Depends(current_user),db=Depends(database)):
        p=get_post(db,post_id,user['tenant'])
        if p['product']!='note' or p['author_id']!=user['id'] or p['deleted_at']:err(404,'본인의 노트가 아닙니다.')
        rows=db.execute('SELECT id,provider,status,created_at,result_json FROM ai_analysis_runs WHERE post_id=? AND user_id=? ORDER BY created_at DESC LIMIT 50',(post_id,user['id'])).fetchall()
        items=[]
        for row in rows:
            d={k:row[k] for k in ('id','provider','status','created_at')}
            if row['result_json']:
                try:
                    obj=json.loads(row['result_json'])
                    d['summary']=(obj.get('summary') or '')[:240]
                    d['issue_count']=len(obj.get('issues') or [])
                except json.JSONDecodeError:
                    d['summary']=''
            items.append(d)
        return {'items':items}

    @app.get('/api/note/{post_id}/ai-runs/{run_id}')
    def ai_run_detail(post_id:str,run_id:str,user=Depends(current_user),db=Depends(database)):
        p=get_post(db,post_id,user['tenant'])
        if p['product']!='note' or p['author_id']!=user['id'] or p['deleted_at']:err(404,'본인의 노트가 아닙니다.')
        row=db.execute('SELECT id,provider,status,created_at,result_json,consent_at FROM ai_analysis_runs WHERE id=? AND post_id=? AND user_id=?',(run_id,post_id,user['id'])).fetchone()
        if not row:err(404,'분석 기록이 없습니다.')
        result=None
        if row['result_json']:
            try:result=json.loads(row['result_json'])
            except json.JSONDecodeError:pass
        return {'id':row['id'],'provider':row['provider'],'status':row['status'],'created_at':row['created_at'],'consent_at':row['consent_at'],'result':result}

    @app.post('/api/native/queue/{post_id}')
    def queue_native(post_id:str,user=Depends(csrf),db=Depends(database)):
        if user['role'] not in ('admin','editor'):err(403,'공개 승인 권한이 필요합니다.')
        p=get_post(db,post_id,user['tenant'])
        if p['product'] not in ('channel','wiki','pan') or p['deleted_at'] or p['status']!='published' or p['visibility']!='public':
            err(400,'공개 승인된 콘텐츠만 기존 LAWYGO로 연동할 수 있습니다.')
        db.execute('''INSERT INTO native_publish_outbox(id,post_id,tenant,action,revision,status,updated_at)
        VALUES(?,?,?,?,?,'queued',?) ON CONFLICT(post_id) DO UPDATE SET action='upsert',revision=excluded.revision,status='queued',updated_at=excluded.updated_at''',(
          uuid.uuid4().hex,post_id,user['tenant'],'upsert',p['version'],_now()))
        return {'queued':True,'post_id':post_id}

    @app.post('/api/native/publish/{post_id}')
    def publish_native(post_id:str,user=Depends(csrf),db=Depends(database)):
        if user['role'] not in ('admin','editor'):err(403,'발행 권한이 필요합니다.')
        p=get_post(db,post_id,user['tenant'])
        if p['product'] not in ('channel','wiki','pan') or p['deleted_at'] or p['status']!='published' or p['visibility']!='public':
            err(400,'승인된 공개 콘텐츠만 LAWYGO 게시판에 전달할 수 있습니다.')
        msg={'source':'lawygo-cms','source_id':p['id'],'product':p['product'],'revision':p['version'],
           'title':p['title'],'body':p['body'],'author':'LAWYGO 콘텐츠 운영','sponsored':bool(p['is_sponsored']),'action':'upsert'}
        try:result=_bridge_publish(msg)
        except (httpx.HTTPError,ValueError):err(502,'기존 LAWYGO 서버에서 게시글을 수신하지 못했습니다.')
        with transaction(db):
            db.execute('''INSERT INTO native_publish_outbox(id,post_id,tenant,action,revision,status,updated_at)
                VALUES(?,?,?,?,?,'delivered',?) ON CONFLICT(post_id) DO UPDATE SET revision=excluded.revision,status='delivered',updated_at=excluded.updated_at,last_error=NULL''',(
              uuid.uuid4().hex,post_id,user['tenant'],'upsert',p['version'],_now()))
            audit(db,user,'publish','native',post_id,{'remote_id':result.get('postId')})
        return {'delivered':True,'remote':result}

    @app.post('/api/native/retract/{post_id}')
    def retract_native(post_id:str,user=Depends(csrf),db=Depends(database)):
        if user['role'] not in ('admin','editor'):err(403,'발행 취소 권한이 필요합니다.')
        p=get_post(db,post_id,user['tenant'])
        if p['product'] not in ('channel','wiki','pan'):err(400,'비공개 노트는 운영 게시판으로 전송할 수 없습니다.')
        msg={'source':'lawygo-cms','source_id':p['id'],'product':p['product'],
             'revision':p['version']+1,'title':p['title'],'body':'',
             'author':'LAWYGO 콘텐츠 운영','sponsored':bool(p['is_sponsored']),'action':'delete'}
        try:result=_bridge_publish(msg)
        except (httpx.HTTPError,ValueError):err(502,'LAWYGO 게시판에서 발행을 취소하지 못했습니다.')
        db.execute('''INSERT INTO native_publish_outbox(id,post_id,tenant,action,revision,status,updated_at)
            VALUES(?,?,?,?,?,'delivered',?) ON CONFLICT(post_id)
            DO UPDATE SET action='delete',revision=excluded.revision,status='delivered',updated_at=excluded.updated_at''',(
            uuid.uuid4().hex,post_id,user['tenant'],'delete',p['version']+1,_now()))
        return {'delivered':True,'remote':result}

    @app.get('/api/native/outbox')
    def native_outbox(user=Depends(current_user),db=Depends(database)):
        if user['role'] not in ('admin','editor'):err(403,'권한이 없습니다.')
        rows=db.execute('SELECT post_id,action,status,revision,attempts,updated_at FROM native_publish_outbox WHERE tenant=? ORDER BY updated_at DESC LIMIT 50',(user['tenant'],)).fetchall()
        return {'items':[dict(r) for r in rows]}

    @app.get('/api/integrations/hub')
    def integrations_hub(user=Depends(current_user),db=Depends(database)):
        flags=integration_flags()
        connections=db.execute(
            'SELECT provider,updated_at FROM google_tokens WHERE user_id=? ORDER BY provider',
            (user['id'],),
        ).fetchall()
        sources=db.execute(
            'SELECT id,provider,title,external_id,last_sync_at,created_at FROM sync_sources WHERE user_id=? AND tenant=? ORDER BY created_at DESC',
            (user['id'],user['tenant']),
        ).fetchall()
        pending_google=db.execute(
            '''SELECT count(*) FROM posts p
               WHERE p.tenant=? AND p.status='pending' AND p.deleted_at IS NULL
               AND p.external_url IS NOT NULL AND p.product IN ('pan','channel')''',
            (user['tenant'],),
        ).fetchone()[0]
        runs=db.execute(
            '''SELECT r.id,r.status,r.created_count,r.updated_count,r.created_at,r.error,s.title AS source_title
               FROM sync_runs r JOIN sync_sources s ON s.id=r.source_id
               WHERE s.user_id=? AND s.tenant=? ORDER BY r.created_at DESC LIMIT 20''',
            (user['id'],user['tenant']),
        ).fetchall()
        outbox=[]
        if user['role'] in ('admin','editor'):
            outbox=db.execute(
                'SELECT post_id,action,status,revision,attempts,updated_at FROM native_publish_outbox WHERE tenant=? ORDER BY updated_at DESC LIMIT 20',
                (user['tenant'],),
            ).fetchall()
        ai_runs=db.execute(
            'SELECT count(*) FROM ai_analysis_runs WHERE user_id=?',
            (user['id'],),
        ).fetchone()[0]
        return {
            'flags':flags,
            'connections':[dict(x) for x in connections],
            'sync_sources':[dict(x) for x in sources],
            'pending_from_sync':pending_google,
            'sync_runs':[dict(x) for x in runs],
            'native_outbox':[dict(x) for x in outbox],
            'ai_analysis_total':ai_runs,
        }

    @app.post('/api/sync/run-all')
    def sync_run_all(user=Depends(csrf),db=Depends(database)):
        if user['role'] not in ('admin','editor','contributor'):err(403,'동기화 권한이 없습니다.')
        with transaction(db):
            result=run_scheduled_syncs(db,force=True)
            audit(db,user,'sync','batch','all',{'created':result['created'],'updated':result['updated']})
        return result

    @app.get('/api/cron/google-sync')
    def cron_google_sync(req:Request,db=Depends(database)):
        secret=os.getenv('LAWYGO_CRON_SECRET','')
        auth=req.headers.get('Authorization','')
        if not secret or auth!=f'Bearer {secret}':
            err(401,'예약 작업 인증이 올바르지 않습니다.')
        with transaction(db):
            result=run_scheduled_syncs(db,force=False)
        return {'ok':True,**result}
