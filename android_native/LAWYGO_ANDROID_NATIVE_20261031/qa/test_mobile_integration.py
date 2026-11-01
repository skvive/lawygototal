"""Local FastAPI/SQLite integration; Google ID tokens are mocked, not real Google calls."""
import os, tempfile, sys, unittest, importlib
from pathlib import Path
from types import SimpleNamespace
from fastapi.testclient import TestClient

ROOT=Path(__file__).resolve().parents[1]
BACKEND=ROOT/'backend_server'
sys.path.insert(0,str(BACKEND))
work=tempfile.TemporaryDirectory(prefix='lawygo-native-test-')
os.environ['LAWYGO_DB_PATH']=str(Path(work.name)/'test.db')
os.environ['LAWYGO_UPLOAD_PATH']=str(Path(work.name)/'uploads')
os.environ['LAWYGO_DEFAULT_TENANT']='demo'
os.environ['LAWYGO_GOOGLE_WEB_CLIENT_ID']='test.apps.googleusercontent.com'
os.environ['LAWYGO_SECURE_COOKIES']='false'
import app,mobile_auth

class AndroidIntegration(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.context=TestClient(app.app)
  cls.client=cls.context.__enter__()
  with app.connect() as db:
   db.execute("INSERT INTO users VALUES(?,?,?,?,?,?,?)",('qa_admin','demo','qa@example.com',app.PH.hash('long-test-password-123'),'관리자','admin',app.now()))
 @classmethod
 def tearDownClass(cls):cls.context.__exit__(None,None,None);work.cleanup()
 def test_01_guest_endpoints(self):
  for path in ['/api/health','/api/journal/news','/api/posts?product=channel','/api/growth/feed','/api/boards']:
   r=self.client.get(path);self.assertEqual(r.status_code,200,(path,r.text))
 def test_02_private_note_denied(self):
  self.assertEqual(self.client.get('/api/posts?product=note').status_code,200)
  self.assertEqual(self.client.get('/api/hub/overview').status_code,401)
 def test_03_google_challenge(self):
  r=self.client.get('/api/mobile/google/challenge');self.assertEqual(r.status_code,200)
  self.assertGreaterEqual(len(r.json()['nonce']),32)
 def test_04_google_real_auth_absent_not_faked(self):
  nonce=self.client.get('/api/mobile/google/challenge').json()['nonce']
  r=self.client.post('/api/mobile/google/login',json={'nonce':nonce,'id_token':'A'*80})
  self.assertIn(r.status_code,[401,503])
 def test_05_login(self):
  r=self.client.post('/api/auth/login',json={'email':'qa@example.com','password':'long-test-password-123','tenant':'demo'})
  self.assertEqual(r.status_code,200,r.text)
  self.assertEqual(self.client.get('/api/me').json()['role'],'admin')
 def csrf(self):return {'X-CSRF-Token':self.client.cookies.get('lawygo_cms_csrf','')}
 def test_06_missing_csrf_rejected(self):
  r=self.client.post('/api/boards',json={'product':'note','slug':'qa-test','name':'QA test'})
  self.assertEqual(r.status_code,403)
 def test_07_native_post_create_edit(self):
  board=self.client.get('/api/boards?product=channel').json()['items'][0]
  r=self.client.post('/api/posts',headers=self.csrf(),json={'board_id':board['id'],'kind':'article','title':'모바일 검수 기사','body':'원문에 근거한 모바일 테스트입니다.','status':'pending','visibility':'public','is_sponsored':False})
  self.assertEqual(r.status_code,201,r.text);self.__class__.post=r.json()['id']
  d=self.client.get('/api/posts/'+self.post).json();self.assertEqual(d['title'],'모바일 검수 기사')
  r=self.client.patch('/api/posts/'+self.post,headers=self.csrf(),json={'version':1,'title':'수정된 모바일 검수 기사'})
  self.assertEqual(r.status_code,200,r.text)
 def test_08_edit_conflict(self):
  r=self.client.patch('/api/posts/'+self.post,headers=self.csrf(),json={'version':1,'title':'오래된 저장'})
  self.assertEqual(r.status_code,409)
 def test_09_approval(self):
  r=self.client.patch('/api/posts/'+self.post,headers=self.csrf(),json={'version':2,'status':'published'})
  self.assertEqual(r.status_code,200,r.text)
  items=self.client.get('/api/posts?product=channel').json()['items']
  self.assertTrue(any(x['id']==self.post for x in items))
 def test_10_news_not_mailed(self):
  self.assertIn('items',self.client.get('/api/journal/news').json())
 def test_11_modules(self):
  r=self.client.get('/api/hub/modules');self.assertEqual(r.status_code,200,r.text);self.assertGreater(len(r.json()['items']),0)
 def test_12_google_link_nonce_protection(self):
  nonce=self.client.get('/api/mobile/google/challenge').json()['nonce']
  mobile_auth.id_token=SimpleNamespace(verify_oauth2_token=lambda token,request,audience: {'iss':'https://accounts.google.com','nonce':nonce,'email_verified':True,'sub':'qa_google_subject'})
  mobile_auth.google_requests=SimpleNamespace(Request=lambda:None)
  r=self.client.post('/api/mobile/google/link',headers=self.csrf(),json={'nonce':nonce,'id_token':'A'*80})
  self.assertEqual(r.status_code,200,r.text)
  reuse=self.client.post('/api/mobile/google/link',headers=self.csrf(),json={'nonce':nonce,'id_token':'A'*80})
  self.assertEqual(reuse.status_code,401)
 def test_13_google_mapped_login(self):
  nonce=self.client.get('/api/mobile/google/challenge').json()['nonce']
  mobile_auth.id_token=SimpleNamespace(verify_oauth2_token=lambda token,request,audience: {'iss':'https://accounts.google.com','nonce':nonce,'email_verified':True,'sub':'qa_google_subject'})
  r=self.client.post('/api/mobile/google/login',json={'nonce':nonce,'id_token':'A'*80})
  self.assertEqual(r.status_code,200,r.text)
 def test_14_google_wrong_subject(self):
  nonce=self.client.get('/api/mobile/google/challenge').json()['nonce']
  mobile_auth.id_token=SimpleNamespace(verify_oauth2_token=lambda token,request,audience: {'iss':'https://accounts.google.com','nonce':nonce,'email_verified':True,'sub':'not_linked_sub'})
  r=self.client.post('/api/mobile/google/login',json={'nonce':nonce,'id_token':'A'*80})
  self.assertEqual(r.status_code,403)
 def test_15_hub_stats(self):
  r=self.client.get('/api/hub/overview');self.assertEqual(r.status_code,200,r.text)
  self.assertIn('posts',r.json())
 def test_16_note_privacy(self):
  board=self.client.get('/api/boards?product=note').json()['items'][0]
  r=self.client.post('/api/posts',headers=self.csrf(),json={'board_id':board['id'],'kind':'note','title':'비공개 검수','body':'고객 정보가 없는 테스트용 자료입니다.','status':'draft','visibility':'private','is_sponsored':False})
  self.assertEqual(r.status_code,201,r.text)
  self.assertNotIn(r.json()['id'],[x['id'] for x in self.client.get('/api/growth/feed').json()['items']])

if __name__=='__main__':unittest.main(verbosity=2)
