"""Opt-in Google mobile ID-token bridge. Never link accounts by email alone."""
import hashlib,os,secrets,time
from datetime import datetime,timezone
from fastapi import Depends,Response
from pydantic import BaseModel,Field
try:
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
except ImportError:
    id_token = None
    google_requests = None

def register(app,g):
    db_dep=g['database']; csrf=g['csrf'];err=g['err'];txn=g['transaction']
    def schema(db):
        db.execute('CREATE TABLE IF NOT EXISTS google_links(sub TEXT PRIMARY KEY,user_id TEXT NOT NULL UNIQUE REFERENCES users(id))')
        db.execute('CREATE TABLE IF NOT EXISTS google_nonce(hash TEXT PRIMARY KEY,expires INTEGER NOT NULL)')
    def verify(body,db):
        audience=os.getenv('LAWYGO_GOOGLE_WEB_CLIENT_ID','')
        if not audience:err(503,'Google 클라이언트 ID 설정 필요')
        h=hashlib.sha256(body.nonce.encode()).hexdigest()
        with txn(db):
            row=db.execute('SELECT expires FROM google_nonce WHERE hash=?',(h,)).fetchone()
            if not row or row['expires']<time.time():err(401,'Google 로그인 요청 만료')
            db.execute('DELETE FROM google_nonce WHERE hash=?',(h,))
        if id_token is None:err(503,'Google 인증 모듈 설치 필요')
        try: claims=id_token.verify_oauth2_token(body.id_token,google_requests.Request(),audience=audience)
        except Exception:err(401,'Google 토큰 서명 또는 만료 검증 실패')
        if claims.get('iss') not in ('https://accounts.google.com','accounts.google.com') or claims.get('nonce')!=body.nonce or claims.get('email_verified') is not True:
            err(401,'Google 계정 검증 실패')
        sub=claims.get('sub','')
        if not sub or len(sub)>200:err(401,'Google 고유 ID 오류')
        return sub
    class Token(BaseModel):
        id_token:str=Field(min_length=40,max_length=16000)
        nonce:str=Field(min_length=32,max_length=256)
    @app.get('/api/mobile/google/challenge')
    def challenge(db=Depends(db_dep)):
        schema(db);nonce=secrets.token_urlsafe(48)
        with txn(db):
            db.execute('DELETE FROM google_nonce WHERE expires<?',(int(time.time()),))
            db.execute('INSERT INTO google_nonce VALUES(?,?)',(hashlib.sha256(nonce.encode()).hexdigest(),int(time.time())+300))
        return {'nonce':nonce,'expires_in':300}
    @app.post('/api/mobile/google/link')
    def link(body:Token,user=Depends(csrf),db=Depends(db_dep)):
        schema(db);sub=verify(body,db)
        with txn(db):
            other=db.execute('SELECT user_id FROM google_links WHERE sub=?',(sub,)).fetchone()
            linked=db.execute('SELECT sub FROM google_links WHERE user_id=?',(user['id'],)).fetchone()
            if (other and other['user_id']!=user['id']) or (linked and linked['sub']!=sub):err(409,'다른 회원 연결 또는 기존 연결 있음')
            db.execute('INSERT OR IGNORE INTO google_links VALUES(?,?)',(sub,user['id']))
        return {'linked':True}
    @app.post('/api/mobile/google/login')
    def login(body:Token,response:Response,db=Depends(db_dep)):
        schema(db);sub=verify(body,db)
        user=db.execute('SELECT u.* FROM users u JOIN google_links l ON l.user_id=u.id WHERE l.sub=?',(sub,)).fetchone()
        if not user:err(403,'기존 로이고 계정으로 로그인하여 최초 연결해 주세요.')
        session=secrets.token_urlsafe(36);csrf_val=secrets.token_urlsafe(32)
        with txn(db):db.execute('INSERT INTO sessions VALUES(?,?,?,?)',(hashlib.sha256(session.encode()).hexdigest(),user['id'],hashlib.sha256(csrf_val.encode()).hexdigest(),int(time.time())+8*3600))
        secure=os.getenv('LAWYGO_SECURE_COOKIES')=='true'
        response.set_cookie(g['COOKIE'],session,httponly=True,secure=secure,samesite='lax',max_age=8*3600)
        response.set_cookie(g['CSRF_COOKIE'],csrf_val,httponly=False,secure=secure,samesite='lax',max_age=8*3600)
        return {'id':user['id'],'name':user['display_name'],'role':user['role'],'tenant':user['tenant']}
