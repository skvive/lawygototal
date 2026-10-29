"""Secure interactive first user setup without printing/storing passwords."""
from getpass import getpass
from app import init_db,connect,now,PH
import uuid
init_db()
with connect() as db:
    n=db.execute('SELECT count(*) FROM users').fetchone()[0]
    if n:
        print('이미 사용자가 존재합니다. 계정 추가는 bootstrap_admin.py를 사용하세요.')
    else:
        email=input('관리자 이메일: ').strip().lower()
        name=input('표시 이름: ').strip() or '관리자'
        password=getpass('관리자 비밀번호 (12자 이상): ')
        if len(password)<12:raise SystemExit('비밀번호는 12자 이상이어야 합니다.')
        db.execute('INSERT INTO users(id,tenant,email,password_hash,display_name,role,created_at) VALUES(?,?,?,?,?,?,?)',(uuid.uuid4().hex,'demo',email,PH.hash(password),name,'admin',now()))
        print('관리자 계정을 생성했습니다.')
