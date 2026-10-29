"""Real HTTP integration smoke; starts uvicorn on localhost and tests CRUD.
Uses an isolated temporary database, never touches production.
"""
import os,sys,tempfile,subprocess,time
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='lawygo_e2e_') as td:
 env=os.environ.copy()
 env['LAWYGO_DB_PATH']=str(Path(td)/'smoke.db')
 env['LAWYGO_UPLOAD_PATH']=str(Path(td)/'uploads')
 subprocess.run([sys.executable,'bootstrap_admin.py','--email','smoke@example.test','--password','TemporarySmokePass_2026!','--name','테스트 관리자'],cwd=ROOT,env=env,check=True,capture_output=True)
 proc=subprocess.Popen([sys.executable,'-m','uvicorn','app:app','--host','127.0.0.1','--port','8029'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 try:
  base='http://127.0.0.1:8029'
  with httpx.Client(base_url=base,timeout=5,follow_redirects=True) as c:
   for i in range(80):
    try:
     if c.get('/api/health').status_code==200:break
    except httpx.TransportError:pass
    time.sleep(.15)
   else:raise RuntimeError('Server failed to start')
   login=c.post('/api/auth/login',json={'email':'smoke@example.test','password':'TemporarySmokePass_2026!'})
   assert login.status_code==200,login.text
   h={'X-CSRF-Token':c.cookies.get('lawygo_cms_csrf')}
   b=c.get('/api/boards?product=channel').json()['items'][0]['id']
   r=c.post('/api/posts',headers=h,json={'board_id':b,'kind':'article','title':'로이고 실제 HTTP 저장 테스트','body':'HTTP를 통해 콘텐츠를 등록했습니다.','status':'draft'})
   assert r.status_code==201,r.text
   pid=r.json()['id']
   assert c.get('/api/posts/'+pid).status_code==200
   e=c.patch('/api/posts/'+pid,headers=h,json={'version':1,'title':'수정 완료','status':'published'})
   assert e.status_code==200,e.text
   assert c.get('/api/posts?product=channel').json()['total']==1
   assert c.delete('/api/posts/'+pid,headers=h).status_code==200
   assert c.get('/api/posts/'+pid).status_code==404
   assert c.post('/api/posts/'+pid+'/restore',headers=h).status_code==200
   assert c.get('/api/posts/'+pid).json()['status']=='draft'
   assert c.post('/api/auth/logout',headers=h).status_code==200
   assert c.get('/api/me').status_code==401
   print('REAL HTTP SMOKE PASS: health, login, board list, create, update, publish, delete, restore, logout.')
 finally:
  proc.terminate()
  try:proc.wait(timeout=3)
  except subprocess.TimeoutExpired:proc.kill();proc.wait()
