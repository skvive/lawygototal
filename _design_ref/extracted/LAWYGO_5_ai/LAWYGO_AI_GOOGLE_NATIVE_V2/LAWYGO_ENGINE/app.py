"""LAWYGO Content Engine v1 — runnable multi-product FastAPI + SQLite CMS.
Standalone deployment is tested; existing LAWYGO production authentication is NOT silently bypassed.
"""
from __future__ import annotations
import hashlib, os, re, secrets, sqlite3, time, uuid, json
from contextlib import contextmanager, asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal, Optional
from urllib.parse import urlparse

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from fastapi import FastAPI, Request, HTTPException, Depends, Response, UploadFile, File, Query
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

ROOT=Path(__file__).resolve().parent
from dotenv import load_dotenv
load_dotenv(ROOT/".env",override=False)
DB_FILE=Path(os.environ.get('LAWYGO_DB_PATH', str(ROOT/'data'/'lawygo.db')))
FILES=Path(os.environ.get('LAWYGO_UPLOAD_PATH', str(ROOT/'data'/'uploads')))
COOKIE='lawygo_cms_session'
CSRF_COOKIE='lawygo_cms_csrf'
DEFAULT_TENANT=os.environ.get('LAWYGO_DEFAULT_TENANT','demo')
PRODUCTS={'channel':'LAWYGO CHANNEL · 로이고 채널','wiki':'LAWYGO WIKI · 로이고 위키','pan':'LAWYGO PAN · 로이고 판','note':'LAWYGO NOTE · 로이고 노트'}
KINDS={'channel':{'article','blog','video','announcement'},'wiki':{'encyclopedia','precedent','statute','guide'},'pan':{'blog','video','profile','column','announcement'},'note':{'note','document','draft','research'}}
PH=PasswordHasher(time_cost=2,memory_cost=19456,parallelism=1)
ALLOWED_EXT={'image/jpeg':'.jpg','image/png':'.png','image/webp':'.webp','application/pdf':'.pdf'}
MAX_UPLOAD=6*1024*1024


def now(): return datetime.now(timezone.utc).isoformat()
def connect():
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    con=sqlite3.connect(DB_FILE,timeout=10,isolation_level=None,check_same_thread=False)
    con.row_factory=sqlite3.Row
    con.execute('PRAGMA foreign_keys=ON');con.execute('PRAGMA busy_timeout=10000');con.execute('PRAGMA journal_mode=WAL')
    return con

@contextmanager
def transaction(con):
    con.execute('BEGIN IMMEDIATE')
    try:
        yield
        con.commit()
    except BaseException:
        con.rollback();raise

def init_db():
    FILES.mkdir(parents=True, exist_ok=True)
    with connect() as db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS users(id TEXT PRIMARY KEY,tenant TEXT NOT NULL,email TEXT NOT NULL,password_hash TEXT NOT NULL,display_name TEXT NOT NULL,role TEXT NOT NULL CHECK(role IN ('admin','editor','contributor','viewer')),created_at TEXT NOT NULL,UNIQUE(tenant,email));
        CREATE TABLE IF NOT EXISTS sessions(id_hash TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES users(id),csrf_hash TEXT NOT NULL,expires_at INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS boards(id TEXT PRIMARY KEY,tenant TEXT NOT NULL,product TEXT NOT NULL CHECK(product IN ('channel','wiki','pan','note')),slug TEXT NOT NULL,name TEXT NOT NULL,description TEXT NOT NULL DEFAULT '',sort_order INTEGER NOT NULL DEFAULT 0,deleted_at TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,UNIQUE(tenant,product,slug));
        CREATE TABLE IF NOT EXISTS posts(id TEXT PRIMARY KEY,tenant TEXT NOT NULL,board_id TEXT NOT NULL REFERENCES boards(id),product TEXT NOT NULL,kind TEXT NOT NULL,title TEXT NOT NULL,body TEXT NOT NULL,summary TEXT NOT NULL DEFAULT '',external_url TEXT,author_id TEXT NOT NULL REFERENCES users(id),status TEXT NOT NULL CHECK(status IN ('draft','pending','published','archived','deleted')),visibility TEXT NOT NULL CHECK(visibility IN ('public','private')),is_sponsored INTEGER NOT NULL DEFAULT 0,version INTEGER NOT NULL DEFAULT 1,deleted_at TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,published_at TEXT);
        CREATE INDEX IF NOT EXISTS ix_posts_feed ON posts(tenant,product,status,updated_at);
        CREATE INDEX IF NOT EXISTS ix_posts_author ON posts(tenant,author_id,product);
        CREATE TABLE IF NOT EXISTS revisions(id TEXT PRIMARY KEY,post_id TEXT NOT NULL REFERENCES posts(id),editor_id TEXT NOT NULL REFERENCES users(id),version INTEGER NOT NULL,snapshot TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS comments(id TEXT PRIMARY KEY,post_id TEXT NOT NULL REFERENCES posts(id),tenant TEXT NOT NULL,author_id TEXT NOT NULL REFERENCES users(id),body TEXT NOT NULL,deleted_at TEXT,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS media(id TEXT PRIMARY KEY,tenant TEXT NOT NULL,owner_id TEXT NOT NULL REFERENCES users(id),post_id TEXT REFERENCES posts(id),safe_name TEXT NOT NULL,original_name TEXT NOT NULL,mime TEXT NOT NULL,size INTEGER NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS audit(id TEXT PRIMARY KEY,tenant TEXT NOT NULL,actor_id TEXT NOT NULL,action TEXT NOT NULL,object_type TEXT NOT NULL,object_id TEXT NOT NULL,details TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS publishing_queue(id TEXT PRIMARY KEY,post_id TEXT NOT NULL REFERENCES posts(id),tenant TEXT NOT NULL,target TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'queued',requested_by TEXT NOT NULL,created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS pan_inquiries(id TEXT PRIMARY KEY,tenant TEXT NOT NULL,profile_post_id TEXT NOT NULL REFERENCES posts(id),recipient_id TEXT NOT NULL REFERENCES users(id),sender_id TEXT NOT NULL REFERENCES users(id),sender_email TEXT NOT NULL,body TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'new',consented_at TEXT NOT NULL,created_at TEXT NOT NULL);
        ''')
        import integrations_v2
        integrations_v2.ensure_schema(db)
        for product,boards in {
            'channel':[('news','경제·법률 뉴스'),('clips','영상·쇼츠'),('insight','전문가 인사이트')],
            'wiki':[('encyclopedia','온라인 법률백과'),('precedents','판례 해설'),('laws','법령·제도')],
            'pan':[('lawyers','변호사 브랜딩'),('blogs','구글블로그 칼럼'),('shorts','변호사 쇼츠'),('sponsored','광고·프로모션')],
            'note':[('projects','개인 연구 노트'),('drafts','법률문서 초안'),('sources','분석 자료')],
        }.items():
            for ix,(slug,name) in enumerate(boards):
                db.execute('INSERT OR IGNORE INTO boards(id,tenant,product,slug,name,sort_order,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)',(
                    uuid.uuid4().hex,DEFAULT_TENANT,product,slug,name,ix,now(),now()))

@asynccontextmanager
async def lifespan(_app):
    init_db()
    yield

app=FastAPI(title='LAWYGO · Content Management Engine',version='1.0.0',docs_url='/api/docs',openapi_url='/api/openapi.json',lifespan=lifespan)
app.mount('/static',StaticFiles(directory=ROOT/'static'),name='static')


def database():
    con=connect()
    try:yield con
    finally:con.close()

def dictrow(row):return dict(row) if row else None

def err(status:int,message:str):raise HTTPException(status_code=status,detail=message)

def audit(db,user,action,object_type,obj,details=None):
    db.execute('INSERT INTO audit VALUES(?,?,?,?,?,?,?,?)',(
        uuid.uuid4().hex,user['tenant'],user['id'],action,object_type,obj,json.dumps(details or {},ensure_ascii=False),now()))

def current_user(req:Request,db=Depends(database)):
    token=req.cookies.get(COOKIE,'')
    if not token:err(401,'로그인이 필요합니다.')
    sh=hashlib.sha256(token.encode()).hexdigest()
    row=db.execute('''SELECT users.*,sessions.csrf_hash FROM sessions JOIN users ON users.id=sessions.user_id WHERE sessions.id_hash=? AND sessions.expires_at>?''',(sh,int(time.time()))).fetchone()
    if not row:err(401,'로그인이 만료됐습니다.')
    return dict(row)

def csrf(req:Request,user=Depends(current_user)):
    token=req.headers.get('X-CSRF-Token','')
    cookie=req.cookies.get(CSRF_COOKIE,'')
    if not token or not cookie or not secrets.compare_digest(token,cookie) or not secrets.compare_digest(hashlib.sha256(token.encode()).hexdigest(),user['csrf_hash']):
        err(403,'요청 검증(CSRF)에 실패했습니다.')
    origin=req.headers.get('origin','')
    if origin:
        p=urlparse(origin)
        if p.netloc.lower()!=req.url.netloc.lower():err(403,'허용되지 않은 요청 출처입니다.')
    return user

def require_staff(user):
    if user['role'] not in ('admin','editor'):err(403,'관리자 또는 편집자만 수행할 수 있습니다.')

def require_admin(user):
    if user['role']!='admin':err(403,'관리자만 수행할 수 있습니다.')

def get_board(db,board_id,tenant):
    b=db.execute('SELECT * FROM boards WHERE id=? AND tenant=? AND deleted_at IS NULL',(board_id,tenant)).fetchone()
    if not b:err(404,'게시판을 찾을 수 없습니다.')
    return dict(b)

def get_post(db,post_id,tenant):
    p=db.execute('SELECT * FROM posts WHERE id=? AND tenant=?',(post_id,tenant)).fetchone()
    if not p:err(404,'게시글을 찾을 수 없습니다.')
    return dict(p)

def can_read(post,user):
    if post['deleted_at'] or post['status']=='deleted':return False
    if post['product']=='note' or post['visibility']=='private':return bool(user and post['author_id']==user['id'])
    if post['status']=='published':return True
    return bool(user and (post['author_id']==user['id'] or (user['tenant']==post['tenant'] and user['role'] in ('admin','editor'))))

def can_edit(post,user):
    if user['tenant'] != post['tenant']:return False
    if post['product']=='note':return post['author_id']==user['id']
    return post['author_id']==user['id'] or user['role'] in ('admin','editor')

class Login(BaseModel):
    email:str
    password:str
    tenant:str=DEFAULT_TENANT

@app.post('/api/auth/login')
def login(data:Login,response:Response,db=Depends(database)):
    email=data.email.strip().lower()
    row=db.execute('SELECT * FROM users WHERE email=? AND tenant=?',(email,data.tenant)).fetchone()
    if not row:err(401,'로그인 정보가 올바르지 않습니다.')
    try: PH.verify(row['password_hash'],data.password)
    except (VerifyMismatchError,VerificationError):err(401,'로그인 정보가 올바르지 않습니다.')
    raw=secrets.token_urlsafe(36);token=secrets.token_urlsafe(32)
    with transaction(db):
        db.execute('DELETE FROM sessions WHERE expires_at<?',(int(time.time()),))
        db.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(raw.encode()).hexdigest(),row['id'],hashlib.sha256(token.encode()).hexdigest(),int(time.time())+3600*8))
    secure=os.environ.get('LAWYGO_SECURE_COOKIES')=='true'
    response.set_cookie(COOKIE,raw,httponly=True,secure=secure,samesite='lax',max_age=8*3600)
    response.set_cookie(CSRF_COOKIE,token,httponly=False,secure=secure,samesite='lax',max_age=8*3600)
    return {'id':row['id'],'name':row['display_name'],'role':row['role'],'tenant':row['tenant']}

@app.post('/api/auth/logout')
def logout(req:Request,response:Response,user=Depends(csrf),db=Depends(database)):
    # Delete current session, preserve security on concurrent sessions.
    token=req.cookies.get(COOKIE,'')
    db.execute('DELETE FROM sessions WHERE id_hash=?',(hashlib.sha256(token.encode()).hexdigest(),))
    response.delete_cookie(COOKIE);response.delete_cookie(CSRF_COOKIE)
    return {'ok':True}

@app.get('/api/me')
def me(user=Depends(current_user)):
    return {k:user[k] for k in ('id','tenant','email','display_name','role')}

class BoardIn(BaseModel):
    product:Literal['channel','wiki','pan','note']
    name:str=Field(min_length=2,max_length=80)
    slug:str=Field(min_length=2,max_length=42,pattern=r'^[a-z][a-z0-9-]*$')
    description:str=Field(default='',max_length=400)

class BoardEdit(BaseModel):
    name:Optional[str]=Field(default=None,min_length=2,max_length=80)
    description:Optional[str]=Field(default=None,max_length=400)
    sort_order:Optional[int]=Field(default=None,ge=0,le=500)

@app.get('/api/boards')
def boards(req:Request,product:Optional[str]=None,db=Depends(database)):
    if product and product not in PRODUCTS:err(400,'지원하지 않는 서비스입니다.')
    q='SELECT * FROM boards WHERE tenant=? AND deleted_at IS NULL'
    actor=optional_user(req,db)
    args=[actor['tenant'] if actor else DEFAULT_TENANT]
    if product:q+=' AND product=?';args.append(product)
    return {'items':[dict(x) for x in db.execute(q+' ORDER BY product,sort_order,name',args).fetchall()]}

@app.post('/api/boards',status_code=201)
def board_create(data:BoardIn,user=Depends(csrf),db=Depends(database)):
    require_admin(user)
    bid=uuid.uuid4().hex
    try:
        with transaction(db):
            db.execute('INSERT INTO boards(id,tenant,product,slug,name,description,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?)',(bid,user['tenant'],data.product,data.slug,data.name.strip(),data.description,now(),now()))
            audit(db,user,'create','board',bid)
    except sqlite3.IntegrityError:err(409,'동일한 게시판 식별자가 이미 존재합니다.')
    return {'id':bid}

@app.patch('/api/boards/{board_id}')
def board_update(board_id:str,data:BoardEdit,user=Depends(csrf),db=Depends(database)):
    require_admin(user);get_board(db,board_id,user['tenant'])
    fields=data.model_dump(exclude_none=True)
    if not fields:err(400,'변경할 항목이 없습니다.')
    with transaction(db):
        db.execute('UPDATE boards SET '+','.join(f'{k}=?' for k in fields)+',updated_at=? WHERE id=?',list(fields.values())+[now(),board_id]);audit(db,user,'update','board',board_id,fields)
    return {'ok':True}

@app.delete('/api/boards/{board_id}')
def board_delete(board_id:str,user=Depends(csrf),db=Depends(database)):
    require_admin(user);get_board(db,board_id,user['tenant'])
    with transaction(db):
        db.execute('UPDATE boards SET deleted_at=?,updated_at=? WHERE id=?',(now(),now(),board_id));audit(db,user,'delete','board',board_id)
    return {'ok':True}

@app.post('/api/boards/{board_id}/restore')
def board_restore(board_id:str,user=Depends(csrf),db=Depends(database)):
    require_admin(user)
    b=db.execute('SELECT id FROM boards WHERE id=? AND tenant=?',(board_id,user['tenant'])).fetchone()
    if not b:err(404,'게시판이 없습니다.')
    with transaction(db):
        db.execute('UPDATE boards SET deleted_at=NULL,updated_at=? WHERE id=?',(now(),board_id));audit(db,user,'restore','board',board_id)
    return {'ok':True}

class PostIn(BaseModel):
    board_id:str
    kind:str
    title:str=Field(min_length=2,max_length=180)
    body:str=Field(min_length=1,max_length=40000)
    summary:str=Field(default='',max_length=500)
    external_url:Optional[str]=Field(default=None,max_length=2000)
    visibility:Literal['public','private']='public'
    is_sponsored:bool=False
    status:Literal['draft','pending','published','archived']='draft'
    @field_validator('external_url')
    @classmethod
    def valid_url(cls,v):
        if v:
            url=urlparse(v)
            if url.scheme not in ('https',) or not url.netloc or url.username or url.password:raise ValueError('https 주소만 사용할 수 있습니다.')
        return v

class PostEdit(BaseModel):
    version:int=Field(ge=1)
    title:Optional[str]=Field(default=None,min_length=2,max_length=180)
    body:Optional[str]=Field(default=None,min_length=1,max_length=40000)
    summary:Optional[str]=Field(default=None,max_length=500)
    external_url:Optional[str]=Field(default=None,max_length=2000)
    is_sponsored:Optional[bool]=None
    status:Optional[Literal['draft','pending','published','archived']]=None
    visibility:Optional[Literal['public','private']]=None
    @field_validator('external_url')
    @classmethod
    def valid_url(cls,v):return PostIn.valid_url(v)

def validate_post(data:PostIn,board,user):
    product=board['product']
    if data.kind not in KINDS[product]:err(400,'서비스에 맞지 않는 콘텐츠 종류입니다.')
    if product=='note' and data.visibility!='private':err(400,'법률 노트는 비공개 자료만 허용합니다.')
    if product=='note' and data.is_sponsored:err(400,'비공개 노트에는 광고를 등록할 수 없습니다.')
    if product!='note' and data.visibility=='private' and data.status=='published':err(400,'비공개 게시글을 공개 발행할 수 없습니다.')
    if user['role']=='viewer':err(403,'읽기 전용 계정입니다.')
    if user['role']=='contributor' and product in ('wiki',):err(403,'위키는 검증된 편집자만 작성할 수 있습니다.')
    if user['role']=='contributor' and data.is_sponsored:err(403,'후원 광고 등록은 관리자 승인이 필요합니다.')

@app.post('/api/posts',status_code=201)
def create_post(data:PostIn,user=Depends(csrf),db=Depends(database)):
    board=get_board(db,data.board_id,user['tenant']);validate_post(data,board,user)
    if user['role']=='contributor' and data.status in ('published','archived'):err(403,'회원 콘텐츠는 검수 후 공개됩니다.')
    status=data.status
    if board['product']=='note':status='draft' if status=='published' else status
    pid=uuid.uuid4().hex
    with transaction(db):
        db.execute('''INSERT INTO posts(id,tenant,board_id,product,kind,title,body,summary,external_url,author_id,status,visibility,is_sponsored,created_at,updated_at,published_at)
             VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)''',(pid,user['tenant'],board['id'],board['product'],data.kind,data.title.strip(),data.body.strip(),data.summary,data.external_url,user['id'],status,'private' if board['product']=='note' else data.visibility,int(data.is_sponsored),now(),now(),now() if status=='published' else None))
        audit(db,user,'create','post',pid,{'status':status,'product':board['product']})
    return {'id':pid,'status':status}

def optional_user(req:Request,db):
    token=req.cookies.get(COOKIE,'')
    if not token:return None
    row=db.execute('SELECT users.* FROM sessions JOIN users ON users.id=sessions.user_id WHERE id_hash=? AND expires_at>?',(hashlib.sha256(token.encode()).hexdigest(),int(time.time()))).fetchone()
    return dict(row) if row else None

@app.get('/api/posts')
def list_posts(req:Request,product:Optional[str]=None,board_id:Optional[str]=None,q:str='',status:Optional[str]=None,limit:int=Query(30,ge=1,le=100),offset:int=Query(0,ge=0),db=Depends(database)):
    if product and product not in PRODUCTS:err(400,'지원하지 않는 서비스입니다.')
    user=optional_user(req,db)
    cond=['p.tenant=?','b.deleted_at IS NULL','p.deleted_at IS NULL'];args=[user['tenant'] if user else DEFAULT_TENANT]
    if product:cond.append('p.product=?');args.append(product)
    if board_id:cond.append('p.board_id=?');args.append(board_id)
    if q:cond.append('(p.title LIKE ? OR p.body LIKE ?)');args.extend(['%'+q[:100]+'%']*2)
    if user:
        # A private NOTE must never leak through unfiltered admin/editor queries.
        cond.append("(p.product!='note' OR p.author_id=?)");args.append(user['id'])
        cond.append("(p.visibility!='private' OR p.author_id=?)");args.append(user['id'])
        if product=='note':cond.append('p.product=? AND p.author_id=?');args.extend(['note',user['id']])
        elif user['role'] in ('admin','editor') and status:cond.append('p.status=?');args.append(status)
        else:cond.append("((p.status='published' AND p.visibility='public' AND p.product!='note') OR p.author_id=?)");args.append(user['id'])
    else:
        cond.append("p.status='published' AND p.visibility='public' AND p.product!='note'")
    sql='FROM posts p JOIN boards b ON p.board_id=b.id WHERE '+' AND '.join(cond)
    count=db.execute('SELECT count(*) '+sql,args).fetchone()[0]
    rows=db.execute('SELECT p.id,p.product,p.kind,p.title,p.summary,p.external_url,p.status,p.visibility,p.is_sponsored,p.author_id,p.version,p.created_at,p.updated_at,p.published_at '+sql+' ORDER BY p.is_sponsored DESC,p.updated_at DESC LIMIT ? OFFSET ?',args+[limit,offset]).fetchall()
    # Sponsored content always carries an explicit label; not ranked as impartial expertise.
    return {'total':count,'items':[dict(x) for x in rows]}

@app.get('/api/posts/{post_id}')
def read_post(post_id:str,req:Request,db=Depends(database)):
    p=get_post(db,post_id,optional_user(req,db)['tenant'] if optional_user(req,db) else DEFAULT_TENANT)
    if not can_read(p,optional_user(req,db)):err(404,'공개되지 않은 게시글입니다.')
    return p

@app.patch('/api/posts/{post_id}')
def edit_post(post_id:str,data:PostEdit,user=Depends(csrf),db=Depends(database)):
    p=get_post(db,post_id,user['tenant'])
    if not can_edit(p,user):err(403,'이 게시글을 수정할 수 없습니다.')
    if p['deleted_at']:err(409,'삭제된 게시글은 복구 후 수정하세요.')
    if data.version != p['version']:err(409,'다른 사용자가 수정했습니다. 새로고침 후 다시 시도하세요.')
    fields=data.model_dump(exclude_unset=True,exclude={'version'})
    if not fields:err(400,'변경사항이 없습니다.')
    if p['product']=='note':
        if fields.get('visibility','private')!='private':err(400,'노트는 공개할 수 없습니다.')
        if fields.get('is_sponsored'):err(400,'노트에 광고를 등록할 수 없습니다.')
        if fields.get('status')=='published':err(400,'노트는 공개할 수 없습니다.')
    if user['role']=='contributor':
        if fields.get('is_sponsored'):err(403,'광고는 관리자 승인이 필요합니다.')
        if fields.get('status') in ('published','archived'):err(403,'게시 승인 권한이 없습니다.')
        if p['status']=='published':fields['status']='pending'
    if fields.get('status')=='published' and user['role'] not in ('admin','editor'):err(403,'공개 승인 권한이 없습니다.')
    if fields.get('status')=='published' and fields.get('visibility',p['visibility'])!='public':err(400,'비공개 글을 발행할 수 없습니다.')
    fields['updated_at']=now();fields['version']=p['version']+1
    if fields.get('status')=='published':fields['published_at']=now()
    if 'is_sponsored' in fields:fields['is_sponsored']=int(fields['is_sponsored'])
    with transaction(db):
        db.execute('INSERT INTO revisions VALUES(?,?,?,?,?,?)',(uuid.uuid4().hex,post_id,user['id'],p['version'],json.dumps(p,ensure_ascii=False),now()))
        db.execute('UPDATE posts SET '+','.join(f'{k}=?' for k in fields)+' WHERE id=?',list(fields.values())+[post_id])
        audit(db,user,'update','post',post_id,{'fields':list(fields)})
    return {'ok':True,'version':p['version']+1}

@app.delete('/api/posts/{post_id}')
def delete_post(post_id:str,user=Depends(csrf),db=Depends(database)):
    p=get_post(db,post_id,user['tenant'])
    if not can_edit(p,user):err(403,'삭제할 권한이 없습니다.')
    if p['deleted_at']:err(409,'이미 삭제된 게시글입니다.')
    with transaction(db):
        db.execute('INSERT INTO revisions VALUES(?,?,?,?,?,?)',(uuid.uuid4().hex,post_id,user['id'],p['version'],json.dumps(p,ensure_ascii=False),now()))
        db.execute('UPDATE posts SET deleted_at=?,status=?,version=version+1,updated_at=? WHERE id=?',(now(),'deleted',now(),post_id))
        audit(db,user,'delete','post',post_id)
    return {'ok':True}

@app.post('/api/posts/{post_id}/restore')
def restore_post(post_id:str,user=Depends(csrf),db=Depends(database)):
    require_staff(user);p=get_post(db,post_id,user['tenant'])
    if p['product']=='note' and p['author_id']!=user['id']:err(403,'타인의 비공개 노트를 복구할 수 없습니다.')
    with transaction(db):
        db.execute('UPDATE posts SET deleted_at=NULL,status=?,version=version+1,updated_at=? WHERE id=?',('draft',now(),post_id))
        audit(db,user,'restore','post',post_id)
    return {'ok':True}

@app.get('/api/trash')
def list_trash(user=Depends(current_user),db=Depends(database)):
    require_staff(user)
    rows=db.execute('SELECT id,product,title,author_id,deleted_at FROM posts WHERE tenant=? AND deleted_at IS NOT NULL AND (product!=? OR author_id=?) ORDER BY deleted_at DESC LIMIT 100', (user['tenant'],'note',user['id'])).fetchall()
    return {'items':[dict(x) for x in rows]}

@app.get('/api/admin/boards/trash')
def list_board_trash(user=Depends(current_user),db=Depends(database)):
    require_admin(user)
    return {'items':[dict(x) for x in db.execute('SELECT * FROM boards WHERE tenant=? AND deleted_at IS NOT NULL ORDER BY deleted_at DESC LIMIT 100',(user['tenant'],))]}

@app.get('/api/posts/{post_id}/media')
def list_post_media(post_id:str,user=Depends(current_user),db=Depends(database)):
    p=get_post(db,post_id,user['tenant'])
    if not can_read(p,user):err(403,'첨부파일을 확인할 권한이 없습니다.')
    rows=db.execute('SELECT id,original_name,mime,size,created_at FROM media WHERE tenant=? AND post_id=? ORDER BY created_at DESC', (user['tenant'],post_id)).fetchall()
    return {'items':[dict(x) for x in rows]}

@app.get('/api/posts/{post_id}/revisions')
def post_revisions(post_id:str,user=Depends(current_user),db=Depends(database)):
    p=get_post(db,post_id,user['tenant'])
    if not can_edit(p,user):err(403,'이력 확인 권한이 없습니다.')
    return {'items':[dict(x) for x in db.execute('SELECT version,snapshot,created_at FROM revisions WHERE post_id=? ORDER BY created_at DESC LIMIT 50',(post_id,))]}

class CommentIn(BaseModel):body:str=Field(min_length=1,max_length=2000)

@app.get('/api/posts/{post_id}/comments')
def list_comments(post_id:str,req:Request,db=Depends(database)):
    p=get_post(db,post_id,optional_user(req,db)['tenant'] if optional_user(req,db) else DEFAULT_TENANT)
    if not can_read(p,optional_user(req,db)):err(404,'게시글을 찾을 수 없습니다.')
    return {'items':[dict(x) for x in db.execute('SELECT id,body,created_at FROM comments WHERE post_id=? AND deleted_at IS NULL ORDER BY created_at DESC LIMIT 100',(post_id,))]}

@app.post('/api/posts/{post_id}/comments',status_code=201)
def create_comment(post_id:str,data:CommentIn,user=Depends(csrf),db=Depends(database)):
    p=get_post(db,post_id,user['tenant'])
    if not can_read(p,user):err(403,'댓글 작성 권한이 없습니다.')
    cid=uuid.uuid4().hex
    with transaction(db):
        db.execute('INSERT INTO comments VALUES(?,?,?,?,?,?,?)',(cid,post_id,user['tenant'],user['id'],data.body.strip(),None,now()))
        audit(db,user,'create','comment',cid)
    return {'id':cid}

@app.delete('/api/comments/{comment_id}')
def delete_comment(comment_id:str,user=Depends(csrf),db=Depends(database)):
    c=db.execute('SELECT * FROM comments WHERE id=? AND tenant=?',(comment_id,user['tenant'])).fetchone()
    if not c:err(404,'댓글이 없습니다.')
    if c['author_id']!=user['id'] and user['role'] not in ('admin','editor'):err(403,'삭제 권한이 없습니다.')
    with transaction(db):
        db.execute('UPDATE comments SET deleted_at=? WHERE id=?',(now(),comment_id));audit(db,user,'delete','comment',comment_id)
    return {'ok':True}


def verify_content(mime,raw):
    if mime=='image/png':return raw[:8]==b'\x89PNG\r\n\x1a\n'
    if mime=='image/jpeg':return raw[:3]==b'\xff\xd8\xff'
    if mime=='image/webp':return raw[:4]==b'RIFF' and raw[8:12]==b'WEBP'
    if mime=='application/pdf':return raw[:5]==b'%PDF-'
    return False

@app.post('/api/media',status_code=201)
async def media_upload(post_id:str,file:UploadFile=File(...),user=Depends(csrf),db=Depends(database)):
    p=get_post(db,post_id,user['tenant'])
    if not can_edit(p,user):err(403,'첨부할 수 없습니다.')
    mime=file.content_type or ''
    if mime not in ALLOWED_EXT:err(415,'이미지 또는 PDF만 업로드할 수 있습니다.')
    raw=await file.read(MAX_UPLOAD+1)
    if len(raw)>MAX_UPLOAD:err(413,'6MB 이하 파일만 허용합니다.')
    if not verify_content(mime,raw):err(415,'파일 형식과 실제 내용이 일치하지 않습니다.')
    name=uuid.uuid4().hex+ALLOWED_EXT[mime]
    path=FILES/name;path.write_bytes(raw);os.chmod(path,0o600)
    mid=uuid.uuid4().hex
    with transaction(db):
        db.execute('INSERT INTO media VALUES(?,?,?,?,?,?,?,?,?)',(mid,user['tenant'],user['id'],post_id,name,Path(file.filename or '').name[:140],mime,len(raw),now()))
        audit(db,user,'upload','media',mid)
    return {'id':mid,'size':len(raw),'url':'/api/media/'+mid}

@app.get('/api/media/{media_id}')
def get_media(media_id:str,req:Request,db=Depends(database)):
    actor=optional_user(req,db)
    row=db.execute('SELECT * FROM media WHERE id=? AND tenant=?',(media_id,actor['tenant'] if actor else DEFAULT_TENANT)).fetchone()
    if not row:err(404,'첨부파일이 없습니다.')
    p=get_post(db,row['post_id'],actor['tenant'] if actor else DEFAULT_TENANT)
    if not can_read(p,optional_user(req,db)):err(404,'접근할 수 없는 첨부파일입니다.')
    path=FILES/row['safe_name']
    if not path.exists():err(404,'첨부파일이 손실됐습니다.')
    headers={'X-Content-Type-Options':'nosniff','Cache-Control':'private, no-store'}
    return FileResponse(path,media_type=row['mime'],headers=headers,filename=row['original_name'],content_disposition_type='attachment')

@app.get('/api/wiki/search')
def wiki_search(req:Request,q:str=Query(min_length=2,max_length=100),limit:int=Query(20,ge=1,le=50),db=Depends(database)):
    # Only curated, publicly approved encyclopedia records; no AI-generated legal findings.
    actor=optional_user(req,db)
    rows=db.execute("SELECT id,title,summary,external_url,updated_at FROM posts WHERE tenant=? AND product='wiki' AND visibility='public' AND status='published' AND deleted_at IS NULL AND (title LIKE ? OR body LIKE ?) ORDER BY updated_at DESC LIMIT ?",(actor['tenant'] if actor else DEFAULT_TENANT,'%'+q+'%','%'+q+'%',limit)).fetchall()
    return {'query':q,'items':[dict(x) for x in rows],'disclaimer':'법률 자료는 공신력 있는 원문과 최종 개정일을 확인하세요.'}

@app.get('/api/note/{post_id}/extract')
def note_extract(post_id:str,user=Depends(current_user),db=Depends(database)):
    p=get_post(db,post_id,user['tenant'])
    if p['product']!='note' or p['author_id']!=user['id'] or p['deleted_at']:err(404,'본인의 노트를 찾을 수 없습니다.')
    # No remote AI calls: deterministic extractive overview of user-owned sources only.
    text=p['body']
    attachments=[]
    for m in db.execute('SELECT * FROM media WHERE post_id=? AND tenant=? ORDER BY created_at',(post_id,user['tenant'])):
        if m['mime']!='application/pdf':continue
        try:
            from pypdf import PdfReader
            from io import BytesIO
            reader=PdfReader(BytesIO((FILES/m['safe_name']).read_bytes()))
            extracted='\n'.join((page.extract_text() or '') for page in reader.pages[:12])
            text+='\n'+extracted[:15000]
            attachments.append({'name':m['original_name'],'pages_analyzed':min(len(reader.pages),12),'text_chars':len(extracted)})
        except Exception:attachments.append({'name':m['original_name'],'error':'PDF 텍스트를 추출할 수 없습니다. OCR이 필요한 파일일 수 있습니다.'})
    pattern=r'(?<![가-힣A-Za-z])(?:소송|증거|계약|해지|채무|판례|법령|신청|절차|조항|보증|지급|통지|위반)(?![가-힣A-Za-z])'
    terms={t:len(re.findall(re.escape(t),text)) for t in re.findall(pattern,text)}
    summary='\n'.join(x.strip() for x in re.split(r'[\n.!?]',text[:5000]) if len(x.strip())>18)[:1600]
    return {'post_id':post_id,'title':p['title'],'source_documents':attachments,'extracted_chars':len(text),'keywords':terms,'extractive_preview':summary,'notice':'AI 법률판단·사실확인 결과가 아닌 업로드 원문 기반 단순 발췌입니다.'}

class InquiryIn(BaseModel):
    profile_post_id:str
    message:str=Field(min_length=10,max_length=2000)
    privacy_consent:bool

@app.post('/api/pan/inquiries',status_code=201)
def pan_inquiry(data:InquiryIn,user=Depends(csrf),db=Depends(database)):
    if not data.privacy_consent:err(400,'상담 요청 정보 처리 동의가 필요합니다.')
    profile=get_post(db,data.profile_post_id,user['tenant'])
    if profile['product']!='pan' or profile['kind']!='profile' or profile['status']!='published' or profile['deleted_at']:err(404,'상담 가능한 전문가 프로필이 없습니다.')
    recent=db.execute("SELECT count(*) FROM pan_inquiries WHERE sender_id=? AND created_at>?",(user['id'],datetime.fromtimestamp(time.time()-3600,timezone.utc).isoformat())).fetchone()[0]
    if recent>=5:err(429,'상담 요청은 시간당 최대 5회까지 가능합니다.')
    rid=uuid.uuid4().hex
    with transaction(db):
        db.execute('INSERT INTO pan_inquiries(id,tenant,profile_post_id,recipient_id,sender_id,sender_email,body,consented_at,created_at) VALUES(?,?,?,?,?,?,?,?,?)',(rid,user['tenant'],profile['id'],profile['author_id'],user['id'],user['email'],data.message,now(),now()))
        audit(db,user,'create','pan_inquiry',rid)
    return {'id':rid,'status':'received','notice':'연락처는 공개 프로필에 표시되지 않습니다. 실제 이메일 발송/안심전화는 별도 연동이 필요합니다.'}

@app.get('/api/pan/inquiries')
def list_pan_inquiries(user=Depends(current_user),db=Depends(database)):
    rows=db.execute('SELECT id,profile_post_id,sender_email,body,status,created_at FROM pan_inquiries WHERE tenant=? AND recipient_id=? ORDER BY created_at DESC LIMIT 100',(user['tenant'],user['id'])).fetchall()
    return {'items':[dict(x) for x in rows]}

@app.get('/api/dashboard/stats')
def dashboard(user=Depends(current_user),db=Depends(database)):
    cond="tenant=? AND deleted_at IS NULL AND (product!='note' OR author_id=?)"
    counts=[dict(x) for x in db.execute('SELECT product,status,count(*) AS count FROM posts WHERE '+cond+' GROUP BY product,status',(user['tenant'],user['id']))]
    board_counts=[dict(x) for x in db.execute('SELECT product,count(*) AS count FROM boards WHERE tenant=? AND deleted_at IS NULL GROUP BY product',(user['tenant'],))]
    return {'posts':counts,'boards':board_counts,'products':PRODUCTS}

@app.get('/api/audit')
def audit_list(user=Depends(current_user),db=Depends(database)):
    require_admin(user)
    return {'items':[dict(x) for x in db.execute('SELECT * FROM audit WHERE tenant=? ORDER BY created_at DESC LIMIT 100',(user['tenant'],))]}

@app.get('/api/health')
def health(db=Depends(database)):
    db.execute('SELECT 1').fetchone()
    return {'ok':True,'storage':'sqlite','engine':'LAWYGO CMS'}

@app.get('/')
def home():return FileResponse(ROOT/'static'/'index.html')
@app.get('/dashboard')
def dashboard_page():return FileResponse(ROOT/'static'/'dashboard.html')
@app.get('/p/{product}')
def product_page(product:str):
    if product not in PRODUCTS:err(404,'서비스가 없습니다.')
    return FileResponse(ROOT/'static'/'product.html')

import integrations_v2
integrations_v2.register(app, globals())

if __name__=='__main__':
    import uvicorn
    uvicorn.run('app:app',host='127.0.0.1',port=8018,reload=False)
