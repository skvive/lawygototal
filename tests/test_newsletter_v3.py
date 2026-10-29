import os,sys,uuid
from pathlib import Path
from fastapi.testclient import TestClient
import pytest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
TD=ROOT/'tests'/'_newsletter_instance'
os.environ['LAWYGO_DB_PATH']=str(TD/'n.db')
os.environ['LAWYGO_UPLOAD_PATH']=str(TD/'files')
from app import app,connect,PH,now
import newsletter_v3

@pytest.fixture(scope='module')
def c():
 TD.mkdir(exist_ok=True);(TD/'n.db').unlink(missing_ok=True)
 with TestClient(app) as x:
  with connect() as db:
   db.execute('INSERT INTO users(id,tenant,email,password_hash,display_name,role,created_at) VALUES(?,?,?,?,?,?,?)',(uuid.uuid4().hex,'demo','editor@demo.test',PH.hash('ComplexTestPassword123!'),'editor','editor',now()))
  yield x

def test_newsletter_fail_closed_no_smtp(c):
 assert c.post('/api/growth/newsletter/request',json={'email':'abc@example.com','consent':True}).status_code==503
 assert c.post('/api/growth/newsletter/request',json={'email':'abc@example.com','consent':False}).status_code==422

def test_newsletter_real_flow_with_mocked_smtp(c,monkeypatch):
 creds={'LAWYGO_NEWSLETTER_SMTP_HOST':'smtp.example.test','LAWYGO_NEWSLETTER_SMTP_USER':'sender',
   'LAWYGO_NEWSLETTER_SMTP_PASSWORD':'password', 'LAWYGO_NEWSLETTER_FROM':'news@example.com',
   'LAWYGO_NEWSLETTER_BASE_URL':'https://pan.lawygo.com','LAWYGO_NEWSLETTER_SMTP_PORT':'465'}
 for k,v in creds.items():monkeypatch.setenv(k,v)
 called=[]
 monkeypatch.setattr(newsletter_v3,'send_confirmation',lambda email,tok,unsub:called.append((email,tok,unsub)))
 result=c.post('/api/growth/newsletter/request',json={'email':'abc@example.com','consent':True})
 assert result.status_code==200,result.text
 assert called[0][0]=='abc@example.com'
 assert c.get('/api/growth/newsletter/confirm?token=bad').status_code==400
 assert c.get('/api/growth/newsletter/confirm?token='+called[0][1]).json()['ok']
 assert c.get('/api/growth/newsletter/confirm?token='+called[0][1]).status_code==410
 assert c.get('/api/growth/newsletter/unsubscribe?token='+called[0][2]).json()['ok']
 assert c.get('/api/growth/newsletter/unsubscribe?token='+called[0][2]).status_code==410
 with connect() as db:
  assert db.execute('SELECT status FROM newsletter_subscribers').fetchone()['status']=='unsubscribed'

def test_newsletter_mail_failed_does_not_save(c,monkeypatch):
 for k,v in {'LAWYGO_NEWSLETTER_SMTP_HOST':'smtp.example.test','LAWYGO_NEWSLETTER_SMTP_USER':'sender','LAWYGO_NEWSLETTER_SMTP_PASSWORD':'password','LAWYGO_NEWSLETTER_FROM':'news@example.com','LAWYGO_NEWSLETTER_BASE_URL':'https://pan.lawygo.com','LAWYGO_NEWSLETTER_SMTP_PORT':'465'}.items():monkeypatch.setenv(k,v)
 import smtplib
 def fail(*args):raise smtplib.SMTPException('offline')
 monkeypatch.setattr(newsletter_v3,'send_confirmation',fail)
 assert c.post('/api/growth/newsletter/request',json={'email':'another@example.com','consent':True}).status_code==503
 with connect() as db:assert not db.execute("SELECT 1 FROM newsletter_subscribers WHERE email='another@example.com'").fetchone()

def test_admin_newsletter_send_with_approval_and_limits(c,monkeypatch):
 for k,v in {'LAWYGO_NEWSLETTER_SMTP_HOST':'smtp.example.test','LAWYGO_NEWSLETTER_SMTP_USER':'sender','LAWYGO_NEWSLETTER_SMTP_PASSWORD':'password','LAWYGO_NEWSLETTER_FROM':'news@example.com','LAWYGO_NEWSLETTER_BASE_URL':'https://pan.lawygo.com','LAWYGO_NEWSLETTER_SMTP_PORT':'465'}.items():monkeypatch.setenv(k,v)
 r=c.post('/api/auth/login',json={'email':'editor@demo.test','password':'ComplexTestPassword123!'})
 assert r.status_code==200
 hdr={'X-CSRF-Token':c.cookies.get('lawygo_cms_csrf')}
 body={'subject':'2026년 10월 경제정책 분석 뉴스레터','body':'경제와 법률 제도 변화를 검토한 뉴스레터 예시입니다. 이 내용은 테스트 발송 검증입니다.','confirmed_preview':True}
 assert c.post('/api/growth/newsletter/admin/send',headers=hdr,json=body).status_code==403
 with connect() as db:
  admin_id=uuid.uuid4().hex
  db.execute('INSERT INTO users(id,tenant,email,password_hash,display_name,role,created_at) VALUES(?,?,?,?,?,?,?)',(admin_id,'demo','admin@demo.test',PH.hash('ComplexTestPassword123!'),'admin','admin',now()))
 r=c.post('/api/auth/login',json={'email':'admin@demo.test','password':'ComplexTestPassword123!'})
 assert r.status_code==200
 hdr={'X-CSRF-Token':c.cookies.get('lawygo_cms_csrf')}
 assert c.post('/api/growth/newsletter/admin/send',headers=hdr,json=body).status_code==503
 monkeypatch.setenv('LAWYGO_NEWSLETTER_ALLOW_SEND','true')
 assert c.post('/api/growth/newsletter/admin/send',headers=hdr,json={**body,'confirmed_preview':False}).status_code==409
 # restore one verified recipient in this test DB
 with connect() as db:db.execute("UPDATE newsletter_subscribers SET status='active' WHERE email='abc@example.com'")
 sent=[];monkeypatch.setattr(newsletter_v3,'send_issue_email',lambda email,subject,body,token:sent.append(email))
 assert c.post('/api/growth/newsletter/admin/send',headers=hdr,json=body).status_code==200
 assert sent==['abc@example.com']
 assert c.post('/api/growth/newsletter/admin/send',headers=hdr,json=body).status_code==200
 assert c.post('/api/growth/newsletter/admin/send',headers=hdr,json=body).status_code==409
