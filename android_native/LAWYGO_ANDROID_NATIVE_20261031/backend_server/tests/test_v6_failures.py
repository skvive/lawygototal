"""Customer delivery gate: deterministic failing scenarios, auth, concurrency and regressions."""
import threading, uuid, sys
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from pathlib import Path
from fastapi.testclient import TestClient
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app as core

@pytest.fixture()
def c(tmp_path,monkeypatch):
 monkeypatch.setattr(core,'DB_FILE',tmp_path/'test.db')
 monkeypatch.setattr(core,'FILES',tmp_path/'uploads')
 with TestClient(core.app) as client:
  with core.connect() as db:
   db.execute('INSERT INTO users(id,tenant,email,password_hash,display_name,role,created_at) VALUES(?,?,?,?,?,?,?)',(uuid.uuid4().hex,'demo','admin@v6.test',core.PH.hash('Strong!V6Password'), 'QA admin','admin',core.now()))
  yield client

def auth(c):
 r=c.post('/api/auth/login',json={'email':'admin@v6.test','password':'Strong!V6Password'})
 assert r.status_code==200
 return {'X-CSRF-Token':c.cookies['lawygo_cms_csrf']}

def test_two_simultaneous_edits_do_not_overwrite(c,monkeypatch):
 h=auth(c)
 board=c.get('/api/boards?product=channel').json()['items'][0]['id']
 p=c.post('/api/posts',json={'board_id':board,'kind':'article','title':'동시 수정 테스트','body':'첫 내용'},headers=h).json()['id']
 originals=core.transaction
 gate=threading.Barrier(2,timeout=5)
 @contextmanager
 def gated_transaction(db):
  gate.wait()
  with originals(db):yield
 monkeypatch.setattr(core,'transaction',gated_transaction)
 cookies=dict(c.cookies)
 def do_update(n):
  with TestClient(core.app) as x:
   x.cookies.update(cookies)
   return x.patch('/api/posts/'+p,headers=h,json={'version':1,'title':'수정안 '+str(n)})
 with ThreadPoolExecutor(max_workers=2) as pool:
  a=pool.submit(do_update,1);b=pool.submit(do_update,2)
  results=[a.result(),b.result()]
 assert sorted(x.status_code for x in results)==[200,409],[(x.status_code,x.text[:160]) for x in results]
 with core.connect() as db:
  current=db.execute('SELECT version FROM posts WHERE id=?',(p,)).fetchone()['version']
  assert current==2

def test_old_newsletter_unsubscribe_link_survives_two_issues(c,monkeypatch):
 import newsletter_v3 as nl
 h=auth(c)
 env={'LAWYGO_NEWSLETTER_SMTP_HOST':'smtp.example.test','LAWYGO_NEWSLETTER_SMTP_USER':'sender',
 'LAWYGO_NEWSLETTER_SMTP_PASSWORD':'test','LAWYGO_NEWSLETTER_FROM':'newsletter@example.test',
 'LAWYGO_NEWSLETTER_BASE_URL':'https://pan.lawygo.com','LAWYGO_NEWSLETTER_SMTP_PORT':'465',
 'LAWYGO_NEWSLETTER_ALLOW_SEND':'true'}
 for k,v in env.items():monkeypatch.setenv(k,v)
 confirm=[];delivered=[]
 monkeypatch.setattr(nl,'send_confirmation',lambda email,tok,unsub:confirm.append((tok,unsub)))
 monkeypatch.setattr(nl,'send_issue_email',lambda email,subject,body,token:delivered.append(token))
 assert c.post('/api/growth/newsletter/request',json={'email':'recipient@v6.example.com','consent':True}).status_code==200
 assert c.get('/api/growth/newsletter/confirm?token='+confirm[0][0]).status_code==200
 body={'subject':'로이고 2026 경제 뉴스레터 테스트','body':'첫번째와 두번째 뉴스레터를 테스트하고 예전 수신거부 주소를 검증합니다.','confirmed_preview':True}
 assert c.post('/api/growth/newsletter/admin/send',headers=h,json=body).status_code==200
 assert c.post('/api/growth/newsletter/admin/send',headers=h,json=body).status_code==200
 assert len(delivered)==2
 assert c.get('/api/growth/newsletter/unsubscribe?token='+delivered[0]).status_code==200
 with core.connect() as db:
  assert db.execute("SELECT status FROM newsletter_subscribers WHERE email='recipient@v6.example.com'").fetchone()['status']=='unsubscribed'

def test_editor_has_only_one_send_and_ai_handler():
 path=Path(__file__).resolve().parents[1]/'static'/'editorial-site.js'
 js=path.read_text()
 assert js.count("$('#sendApproved').addEventListener")==1
 assert js.count("$('#aiEnhance').addEventListener")==1

def test_old_and_new_unsubscribe_tokens_revoke_together(c,monkeypatch):
 import newsletter_v3 as nl
 h=auth(c)
 config={'LAWYGO_NEWSLETTER_SMTP_HOST':'smtp.example.test','LAWYGO_NEWSLETTER_SMTP_USER':'sender',
 'LAWYGO_NEWSLETTER_SMTP_PASSWORD':'test','LAWYGO_NEWSLETTER_FROM':'newsletter@example.test',
 'LAWYGO_NEWSLETTER_BASE_URL':'https://pan.lawygo.com','LAWYGO_NEWSLETTER_SMTP_PORT':'465',
 'LAWYGO_NEWSLETTER_ALLOW_SEND':'true'}
 for k,v in config.items():monkeypatch.setenv(k,v)
 confirmation=[];tokens=[]
 monkeypatch.setattr(nl,'send_confirmation',lambda email,tok,unsub:confirmation.append((tok,unsub)))
 monkeypatch.setattr(nl,'send_issue_email',lambda email,subject,body,token:tokens.append(token))
 email='second@v6.example.com'
 assert c.post('/api/growth/newsletter/request',json={'email':email,'consent':True}).status_code==200
 assert c.get('/api/growth/newsletter/confirm?token='+confirmation[0][0]).status_code==200
 body={'subject':'구독 링크 안정성 점검입니다','body':'월 2회 발생되는 뉴스레터의 수신거부 링크 모두 검증합니다.','confirmed_preview':True}
 assert c.post('/api/growth/newsletter/admin/send',headers=h,json=body).status_code==200
 assert c.get('/api/growth/newsletter/unsubscribe?token='+confirmation[0][1]).status_code==200
 assert c.get('/api/growth/newsletter/unsubscribe?token='+tokens[0]).status_code==410
