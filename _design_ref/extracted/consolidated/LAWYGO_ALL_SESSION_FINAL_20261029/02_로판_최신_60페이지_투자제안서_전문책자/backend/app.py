"""LAWYGO PAN minimal production-integration *reference* API.
Email OTP verification, explicit marketing opt-in, salted token hashes, unsubscribe,
moderated URL submissions and private inquiries. Requires infrastructure review
before production deployment: reverse proxy, managed DB, WAF, audit log, backups,
external mail / authenticated lawyer verification.
"""
import os, hashlib, hmac, secrets, sqlite3, smtplib, json, time, html, re
from pathlib import Path
from email.message import EmailMessage
from urllib.parse import urlparse
from fastapi import FastAPI, Request, HTTPException, Response, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from datetime import datetime, timezone

ROOT=Path(__file__).resolve().parent.parent
SITE=ROOT/'site'
DB=Path(os.getenv('PAN_DB_PATH',str(ROOT/'private'/'pan.db')))
DB.parent.mkdir(parents=True,exist_ok=True)
BASE_URL=os.getenv('PAN_PUBLIC_URL','http://127.0.0.1:8765').rstrip('/')
DEMO_MAIL=os.getenv('PAN_DEMO_MAIL','0')=='1'
COOKIE_SECRET=os.getenv('PAN_COOKIE_SECRET','')
if len(COOKIE_SECRET)<32:
    if os.getenv('PAN_ENV')=='production':raise RuntimeError('PAN_COOKIE_SECRET must be >=32 chars in production')
    COOKIE_SECRET='dev-only-unsafe-cookie-secret-change-before-deploy'
FROM_EMAIL=os.getenv('PAN_FROM_EMAIL','')
ADMIN_EMAIL=os.getenv('PAN_ADMIN_EMAIL','')
app=FastAPI(title='LAWYGO PAN Example Membership API', docs_url=None,redoc_url=None)
RATE={}

def database():
    c=sqlite3.connect(DB)
    c.row_factory=sqlite3.Row
    c.execute('PRAGMA journal_mode=WAL')
    c.executescript('''CREATE TABLE IF NOT EXISTS members (email TEXT PRIMARY KEY,name TEXT NOT NULL,firm TEXT,region TEXT,practice TEXT,blog_url TEXT,youtube_url TEXT,verified INTEGER DEFAULT 0,lawyer_verified INTEGER DEFAULT 0,marketing_consent INTEGER DEFAULT 0,unsub_hash TEXT,created_at TEXT NOT NULL);CREATE TABLE IF NOT EXISTS pending_tokens(token_hash TEXT PRIMARY KEY,email TEXT NOT NULL,purpose TEXT NOT NULL,expires_at INTEGER NOT NULL);CREATE TABLE IF NOT EXISTS content_submissions(id INTEGER PRIMARY KEY AUTOINCREMENT,email TEXT NOT NULL,content_type TEXT NOT NULL,title TEXT NOT NULL,url TEXT NOT NULL,summary TEXT,approved INTEGER DEFAULT 0,created_at TEXT NOT NULL);CREATE TABLE IF NOT EXISTS campaigns(id INTEGER PRIMARY KEY AUTOINCREMENT,email TEXT NOT NULL,url TEXT NOT NULL,placement TEXT NOT NULL,budget INTEGER NOT NULL,status TEXT NOT NULL DEFAULT 'pending',created_at TEXT NOT NULL);CREATE TABLE IF NOT EXISTS inquiries(id INTEGER PRIMARY KEY AUTOINCREMENT,lawyer_id TEXT NOT NULL,contact_method TEXT NOT NULL,name TEXT NOT NULL,email TEXT NOT NULL,message TEXT NOT NULL,created_at TEXT NOT NULL,consent INTEGER NOT NULL DEFAULT 0);CREATE TABLE IF NOT EXISTS mail_sends(id INTEGER PRIMARY KEY AUTOINCREMENT,email TEXT,subject TEXT,status TEXT,created_at TEXT);''')
    return c

def now():return datetime.now(timezone.utc).isoformat()
def mail(to,subject,body,headers=None,html_body=None):
    if DEMO_MAIL:
        print('DEVELOPMENT MAIL',subject,to,body[:450]);return
    required=['PAN_SMTP_HOST','PAN_SMTP_USERNAME','PAN_SMTP_PASSWORD','PAN_FROM_EMAIL']
    if not all(os.getenv(k) for k in required):raise HTTPException(503,'이메일 발송 서버가 설정되지 않았습니다. 실제 등록은 처리되지 않았습니다.')
    msg=EmailMessage();msg['From']=FROM_EMAIL;msg['To']=to;msg['Subject']=subject;msg.set_content(body)
    if html_body: msg.add_alternative(html_body, subtype='html')
    for k,v in (headers or {}).items():msg[k]=v
    with smtplib.SMTP(os.getenv('PAN_SMTP_HOST'),int(os.getenv('PAN_SMTP_PORT','587')),timeout=15) as smtp:
        smtp.starttls();smtp.login(os.getenv('PAN_SMTP_USERNAME'),os.getenv('PAN_SMTP_PASSWORD'));smtp.send_message(msg)

def check_mail_ready():
    if DEMO_MAIL and os.getenv('PAN_ENV')!='production':return
    if not all(os.getenv(k) for k in ('PAN_SMTP_HOST','PAN_SMTP_USERNAME','PAN_SMTP_PASSWORD','PAN_FROM_EMAIL')):
        raise HTTPException(503,'실제 발송을 위한 이메일 서버 설정이 필요합니다.')

def throttled(request,tag,limit=6):
    ip=request.client.host if request.client else '?';k=(tag,ip)
    t=time.monotonic();x=[i for i in RATE.get(k,[]) if t-i<300]
    if len(x)>=limit:raise HTTPException(429,'요청이 너무 많습니다. 잠시 후 다시 시도해 주세요.')
    x.append(t); RATE[k]=x

def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def create_token(db,email,purpose,ttl=24*3600):
    token=secrets.token_urlsafe(36)
    db.execute('INSERT INTO pending_tokens(token_hash,email,purpose,expires_at) VALUES (?,?,?,?)',(digest(token),email,purpose,int(time.time()+ttl)))
    return token

def sign_session(email,ttl=86400*7):
    payload=f'{email}|{int(time.time()+ttl)}';signature=hmac.new(COOKIE_SECRET.encode(),payload.encode(),'sha256').hexdigest()
    return payload+'|'+signature

def user_email(request):
    cookie=request.cookies.get('pan_session','');parts=cookie.rsplit('|',2)
    if len(parts)!=3:raise HTTPException(401,'이메일 인증 후 다시 시도해 주세요.')
    email,exp,sig=parts
    if not exp.isdigit() or int(exp)<time.time() or not hmac.compare_digest(hmac.new(COOKIE_SECRET.encode(),f'{email}|{exp}'.encode(),'sha256').hexdigest(),sig):raise HTTPException(401,'로그인 유효기간이 종료됐습니다.')
    with database() as db:
        row=db.execute('SELECT verified FROM members WHERE email=?',(email,)).fetchone()
    if not row or not row['verified']:raise HTTPException(401,'이메일 인증이 필요합니다.')
    return email

def valid_url(x,kind=None):
    if not x:return ''
    try:u=urlparse(x)
    except Exception:raise HTTPException(400,'URL을 확인해 주세요.')
    if u.scheme!='https' or not u.hostname or '@' in u.netloc or len(x)>1200:raise HTTPException(400,'https URL만 입력할 수 있습니다.')
    host=u.hostname.lower()
    if kind=='video' and host not in {'youtube.com','www.youtube.com','youtu.be','m.youtube.com'}:raise HTTPException(400,'YouTube 영상 URL을 입력하세요.')
    if kind=='blog' and not (host.endswith('.blogspot.com') or host in {'blogger.com','www.blogger.com'}):raise HTTPException(400,'Blogger 블로그 주소를 입력하세요.')
    # URLs stored, never fetched server-side; prevent SSRF and unsafe redirects in other code.
    return x

def validate_email(email):
    s=(email or '').strip().lower()
    if len(s)>254 or not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',s):raise HTTPException(400,'올바른 이메일 주소를 입력하세요.')
    return s

def input_json(request): pass

class Signup(BaseModel):
    email:str;name:str=Field(min_length=1,max_length=60);firm:str='';region:str='';practice:str='';blog_url:str='';youtube_url:str='';terms:bool=False;marketing:bool=False

@app.middleware('http')
async def safety_headers(request,call_next):
    if request.method in {'POST','PUT','PATCH','DELETE'}:
        origin=request.headers.get('origin','')
        if origin and origin.rstrip('/') not in {BASE_URL,'http://127.0.0.1:8765','http://localhost:8765'}:return JSONResponse({'detail':'잘못된 요청 출처입니다.'},status_code=403)
    resp=await call_next(request)
    resp.headers['X-Content-Type-Options']='nosniff';resp.headers['Referrer-Policy']='strict-origin-when-cross-origin'
    resp.headers['X-Frame-Options']='DENY';resp.headers['Cache-Control']='no-store' if request.url.path.startswith('/api/') else 'no-cache'
    return resp

@app.post('/api/signup')
async def signup(data:Signup,request:Request):
    throttled(request,'signup');check_mail_ready()
    if not data.terms:raise HTTPException(400,'이용약관과 개인정보처리방침 확인이 필요합니다.')
    email=validate_email(data.email)
    blog=valid_url(data.blog_url) if data.blog_url else '';youtube=valid_url(data.youtube_url) if data.youtube_url else ''
    with database() as db:
        db.execute('''INSERT INTO members (email,name,firm,region,practice,blog_url,youtube_url,marketing_consent,created_at) VALUES (?,?,?,?,?,?,?,?,?) ON CONFLICT(email) DO UPDATE SET name=excluded.name,firm=excluded.firm,region=excluded.region,practice=excluded.practice,blog_url=excluded.blog_url,youtube_url=excluded.youtube_url,marketing_consent=0''',(email,data.name,data.firm[:100],data.region[:60],data.practice[:120],blog,youtube,0,now()))
        t=create_token(db,email,'signup')
        db.commit()
    mail(email,'[LAWYGO PAN] 이메일 인증 안내',f'계정 등록을 완료하려면 아래 주소로 이동하세요.\n{BASE_URL}/verify?token={t}\n유효기간은 24시간입니다.')
    return {'message':'입력한 이메일로 인증 주소를 발송했습니다. 인증 후 회원가입이 완료됩니다. 마케팅 수신동의는 별도로 확인합니다.'}

@app.get('/verify',response_class=HTMLResponse)
async def verify(token:str):
    with database() as db:
        row=db.execute('SELECT * FROM pending_tokens WHERE token_hash=?',(digest(token),)).fetchone()
        if not row or row['expires_at']<time.time():raise HTTPException(400,'만료되었거나 유효하지 않은 인증 주소입니다.')
        if row['purpose']=='signup':db.execute('UPDATE members SET verified=1 WHERE email=?',(row['email'],))
        elif row['purpose']=='marketing':db.execute('UPDATE members SET verified=1,marketing_consent=1 WHERE email=?',(row['email'],))
        else:raise HTTPException(400,'인증 목적이 올바르지 않습니다.')
        db.execute('DELETE FROM pending_tokens WHERE token_hash=?',(digest(token),));db.commit()
    resp=HTMLResponse('<meta charset="utf-8"><title>인증 완료</title><h2>인증이 완료되었습니다.</h2><p><a href="/creator-studio.html">LAWYGO PAN 콘텐츠 스튜디오로 이동</a></p>')
    resp.set_cookie('pan_session',sign_session(row['email']),max_age=7*86400,httponly=True,secure=BASE_URL.startswith('https://'),samesite='lax')
    return resp

@app.post('/api/newsletter')
async def newsletter(request:Request):
    throttled(request,'newsletter');check_mail_ready()
    data=await request.json(); email=validate_email(data.get('email'))
    if not data.get('marketing'):raise HTTPException(400,'광고성 정보 수신에 대한 명시적 동의가 필요합니다.')
    with database() as db:
        db.execute('INSERT INTO members(email,name,marketing_consent,created_at) VALUES (?,?,0,?) ON CONFLICT(email) DO NOTHING',(email,'뉴스레터 구독자',now()))
        t=create_token(db,email,'marketing');db.commit()
    mail(email,'[LAWYGO PAN] 광고성 정보 수신동의 확인',f'광고성 정보 수신동의를 완료하려면 아래 링크를 눌러 주세요.\n{BASE_URL}/verify?token={t}')
    return {'message':'마케팅 수신동의 확인 메일을 발송했습니다. 링크를 누르면 동의가 완료됩니다.'}

@app.post('/api/content')
async def content(request:Request):
    throttled(request,'content',12);email=user_email(request);d=await request.json();kind=d.get('content_type')
    if kind not in ('blog','video'):raise HTTPException(400,'콘텐츠 유형이 올바르지 않습니다.')
    if not d.get('rights'):raise HTTPException(400,'콘텐츠 게시 권한 확인이 필요합니다.')
    title=str(d.get('title','')).strip()[:120]
    if len(title)<3:raise HTTPException(400,'콘텐츠 제목을 확인해 주세요.')
    url=valid_url(str(d.get('url','')),kind)
    with database() as db:
        db.execute('INSERT INTO content_submissions(email,content_type,title,url,summary,created_at) VALUES (?,?,?,?,?,?)',(email,kind,title,url,str(d.get('summary',''))[:1000],now()));db.commit()
    return {'message':'콘텐츠 등록 요청을 받았습니다. 관리자 검수 후 게시 여부를 안내합니다. 자동 게재되지 않습니다.'}

@app.post('/api/campaign')
async def campaign(request:Request):
    throttled(request,'campaign');email=user_email(request);d=await request.json()
    if not d.get('rights'):raise HTTPException(400,'광고심사 정책 동의가 필요합니다.')
    placement=d.get('placement','')
    if placement not in ('sponsored','shorts','topic'):raise HTTPException(400,'광고 영역이 올바르지 않습니다.')
    url=valid_url(str(d.get('url','')));budget=int(d.get('budget') or 0)
    if budget<0 or budget>100000000:raise HTTPException(400,'예산 입력을 확인해 주세요.')
    with database() as db:
        db.execute('INSERT INTO campaigns(email,url,placement,budget,created_at) VALUES (?,?,?,?,?)',(email,url,placement,budget,now()));db.commit()
    return {'message':'광고 검토 요청이 접수됐습니다. 과금과 게재는 시작되지 않았습니다.'}

@app.get('/unsubscribe',response_class=HTMLResponse)
async def unsubscribe_form(token:str=''):
    if not token:return '<meta charset="utf-8"><h2>개별 수신거부 링크가 필요합니다.</h2>'
    return '<meta charset="utf-8"><title>LAWYGO 수신거부</title><main style="max-width:600px;margin:10vh auto;font:18px sans-serif"><h1>LAWYGO PAN 광고 수신거부</h1><p>수신거부를 선택하면 추가 광고성 이메일을 보내지 않습니다.</p><form method="post" action="/api/unsubscribe"><input type="hidden" name="token" value="'+html.escape(token,quote=True)+'"><button style="padding:16px 28px;background:#102a43;color:white;border:0">수신거부 확정</button></form></main>'

@app.post('/unsubscribe',response_class=HTMLResponse)
@app.post('/api/unsubscribe',response_class=HTMLResponse)
async def unsubscribe(request:Request):
    # RFC 8058 one-click List-Unsubscribe-Post sends form-encoded body; token in query supported.
    data=await request.form()
    token=str(data.get('token') or request.query_params.get('token',''))
    if not token or len(token)>200:raise HTTPException(400,'유효하지 않은 수신거부 주소입니다.')
    with database() as db:
        row=db.execute('SELECT email FROM members WHERE unsub_hash=?',(digest(token),)).fetchone()
        if not row:raise HTTPException(404,'유효하지 않거나 이미 변경된 링크입니다.')
        db.execute('UPDATE members SET marketing_consent=0,unsub_hash=NULL WHERE email=?',(row['email'],));db.commit()
    return '<meta charset="utf-8"><h1>광고 메일 수신거부가 완료되었습니다.</h1><p>추가 광고 메일은 발송되지 않습니다.</p>'

@app.get('/api/health')
async def health():return {'ok':True,'billing':False,'mailConfigured':DEMO_MAIL or bool(os.getenv('PAN_SMTP_HOST'))}


@app.get('/api/feed')
async def approved_feed(kind:str='all'):
    if kind not in ('all','blog','video'):
        raise HTTPException(400,'올바르지 않은 콘텐츠 유형입니다.')
    with database() as db:
        rows=db.execute('SELECT id,content_type,title,url,summary,created_at FROM content_submissions WHERE approved=1 AND (?="all" OR content_type=?) ORDER BY id DESC LIMIT 50',(kind,kind)).fetchall()
    return {'contents':[dict(row) for row in rows]}

@app.post('/api/inquiry')
async def submit_inquiry(request:Request):
    throttled(request,'inquiry',6)
    d=await request.json()
    if not d.get('consent'):raise HTTPException(400,'상담정보 전송에 대한 동의가 필요합니다.')
    slug=str(d.get('profile','')).strip()[:60]
    if not re.fullmatch(r'[a-z0-9-]{3,60}',slug):raise HTTPException(400,'프로필 주소가 올바르지 않습니다.')
    name=str(d.get('name','')).strip()[:60]
    email=validate_email(d.get('email',''))
    message=str(d.get('message','')).strip()
    method=d.get('method','email')
    if method not in ('email','callback') or len(name)<2 or not (10<=len(message)<=1500):
        raise HTTPException(400,'신청 내용을 확인해 주세요.')
    check_mail_ready()
    with database() as db:
        db.execute('CREATE TABLE IF NOT EXISTS profile_routes (slug TEXT PRIMARY KEY,member_email TEXT NOT NULL,activated INTEGER DEFAULT 0)')
        profile=db.execute('SELECT member_email FROM profile_routes WHERE slug=? AND activated=1',(slug,)).fetchone()
        if not profile:raise HTTPException(409,'이 프로필의 연결 계정은 아직 운영 인증되지 않았습니다.')
        dest=profile['member_email']
        db.execute('INSERT INTO inquiries(lawyer_id,contact_method,name,email,message,created_at,consent) VALUES (?,?,?,?,?,?,1)',(slug,method,name,email,message,now()))
        db.commit()
    mail(dest,'[LAWYGO PAN] 새로운 비공개 상담 연결 요청',f'프로필: {slug}\n문의 방법: {method}\n신청자: {name}\n회신 이메일: {email}\n요약: {message}\n\n민감정보는 필요 최소한으로 다뤄 주세요.')
    return {'message':'인증된 변호사 계정으로 비공개 요청이 전달되었습니다. 실제 상담 수임은 별도 계약에 따릅니다.'}

# Static files mounted last: no mutable data, credentials or private DB is under this path.
app.mount('/',StaticFiles(directory=str(SITE),html=True),name='site')

# Public content and private professional-contact endpoints are registered by
# this integration module before StaticFiles is mounted in deployment.
