"""Live socket HTTP matrix for LAWYGO V6. No production credentials, isolated DB."""
import json,os,socket,subprocess,sys,tempfile,time
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent.parent/'V6_REAL_HTTP_EVIDENCE';OUT.mkdir(exist_ok=True)
checks=[]
def verify(label,response,expected):
 ok=response.status_code==expected
 checks.append({'case':label,'expected':expected,'actual':response.status_code,'pass':ok})
 if not ok:raise AssertionError(f'{label}: {response.status_code} != {expected}; {response.text[:230]}')
 return response
with tempfile.TemporaryDirectory(prefix='lawygo_v6_http_') as tmp:
 env=os.environ.copy();env.update({'LAWYGO_DB_PATH':str(Path(tmp)/'db.sqlite'),'LAWYGO_UPLOAD_PATH':str(Path(tmp)/'uploads'),'LAWYGO_NEWSLETTER_ALLOW_SEND':'false'})
 proc0=subprocess.run([sys.executable,'bootstrap_admin.py','--email','qa-admin@lawygo.example.com','--password','V6Quality!2026Strong','--name','v6 관리자'],cwd=ROOT,env=env,capture_output=True,text=True)
 assert proc0.returncode==0,proc0.stderr
 with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
 server=subprocess.Popen([sys.executable,'-m','uvicorn','app:app','--host','127.0.0.1','--port',str(port),'--log-level','error'],cwd=ROOT,env=env,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
 try:
  with httpx.Client(base_url=f'http://127.0.0.1:{port}',timeout=15) as c:
   for _ in range(80):
    try:
     if c.get('/api/health').status_code==200:break
    except Exception:pass
    time.sleep(.15)
   verify('health',c.get('/api/health'),200)
   for url in ['/','/journal','/channel','/wiki','/note','/pan','/pro','/editor','/dashboard','/hub']:
    verify('page '+url,c.get(url),200)
   verify('anonymous hub denied',c.get('/api/hub/modules'),401)
   verify('anonymous post denied',c.post('/api/posts',json={}),401)
   verify('invalid login blocked',c.post('/api/auth/login',json={'email':'qa-admin@lawygo.example.com','password':'Incorrect!'}),401)
   verify('real login',c.post('/api/auth/login',json={'email':'qa-admin@lawygo.example.com','password':'V6Quality!2026Strong'}),200)
   h={'X-CSRF-Token':c.cookies.get('lawygo_cms_csrf')}
   verify('missing csrf blocked',c.post('/api/posts',json={}),403)
   br=c.get('/api/boards');verify('board read',br,200);boards=br.json()['items']
   w=next(x for x in boards if x['product']=='wiki');p=next(x for x in boards if x['product']=='pan');n=next(x for x in boards if x['product']=='note')
   wdata={'board_id':w['id'],'kind':'encyclopedia','title':'실제 HTTP 근로계약 법률백과','body':'근로계약서와 근로기준법을 함께 확인합니다.','status':'published'}
   wid=verify('wiki post created',c.post('/api/posts',headers=h,json=wdata),201).json()['id']
   verify('wiki search contains saved data',c.get('/api/wiki/search',params={'q':'근로계약'}),200)
   assert any(x['id']==wid for x in c.get('/api/wiki/search',params={'q':'근로계약'}).json()['items'])
   pdata={'board_id':p['id'],'kind':'blog','title':'실제 공개 변호사 칼럼','body':'공개 칼럼입니다.','status':'published','is_sponsored':False}
   pid=verify('pan article created',c.post('/api/posts',headers=h,json=pdata),201).json()['id']
   verify('invalid sponsored campaign activation',c.post('/api/growth/campaigns',headers=h,json={'product':'pan','post_id':pid,'name':'테스트 광고','status':'active'}),409)
   verify('content version update',c.patch('/api/posts/'+pid,headers=h,json={'version':1,'is_sponsored':True}),200)
   camp=verify('approved ad campaign',c.post('/api/growth/campaigns',headers=h,json={'product':'pan','post_id':pid,'name':'검수 광고','status':'active'}),201).json()['id']
   feed=verify('ad feed',c.get('/api/growth/feed?product=pan'),200).json()['items'];assert any(x['id']==pid and x['placement']=='광고' for x in feed)
   verify('stale version rejected',c.patch('/api/posts/'+pid,headers=h,json={'version':1,'title':'오래된 편집'}),409)
   verify('pan consultation without consent denied',c.post('/api/pan/inquiries',headers=h,json={'profile_post_id':pid,'message':'무료 상담 신청입니다, 문장 길이 확인','privacy_consent':False}),400)
   note={'board_id':n['id'],'kind':'note','title':'실제 비공개 노트','body':'기밀 개인 노트','visibility':'private','status':'draft'}
   nid=verify('private note created',c.post('/api/posts',headers=h,json=note),201).json()['id']
   verify('private note cannot publish',c.patch('/api/posts/'+nid,headers=h,json={'version':1,'status':'published'}),400)
   verify('invalid upload signature',c.post('/api/media',params={'post_id':nid},headers=h,files={'file':('bad.pdf',b'not_pdf','application/pdf')}),415)
   media=verify('valid pdf media stored',c.post('/api/media',params={'post_id':nid},headers=h,files={'file':('qa.pdf',b'%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF','application/pdf')}),201).json()['id']
   verify('note media retrieved',c.get('/api/media/'+media),200)
   verify('note extraction',c.get('/api/note/'+nid+'/extract'),200)
   verify('no newsletter sending without approval/config',c.post('/api/growth/newsletter/admin/send',headers=h,json={'subject':'뉴스레터 발송 금지 테스트','body':'뉴스레터 발송은 관리자와 SMTP가 승인해야 작동합니다.','confirmed_preview':True}),503)
   verify('journal sources read',c.get('/api/journal/sources'),200)
   draft=verify('daily draft generated',c.post('/api/journal/drafts/today',headers=h),200).json()['item']
   verify('empty draft cannot be approved',c.patch('/api/journal/drafts/'+draft['id'],headers=h,json={'status':'approved','expected_updated_at':draft['updated_at']}),409)
   verify('disabled external AI refused',c.post('/api/journal/drafts/'+draft['id']+'/ai',headers=h),409)
   verify('hub list',c.get('/api/hub/modules'),200)
   mod=verify('new hub module',c.post('/api/hub/modules',headers=h,json={'product':'channel','module_type':'analytics','name':'QA 모듈','enabled':True}),201).json()['id']
   verify('hub module edit',c.patch('/api/hub/modules/'+mod,headers=h,json={'version':1,'name':'검수 모듈'}),200)
   verify('hub stale edit rejected',c.patch('/api/hub/modules/'+mod,headers=h,json={'version':1,'name':'오래된 버전'}),409)
   jid=verify('hub job queued',c.post('/api/hub/jobs',headers=h,json={'kind':'count_pending_content'}),201).json()['id']
   verify('hub job run',c.post('/api/hub/jobs/'+jid+'/run',headers=h),200)
   verify('hub duplicate job rejected',c.post('/api/hub/jobs/'+jid+'/run',headers=h),409)
   verify('hub metrics',c.get('/api/hub/metrics'),200)
   verify('audit log',c.get('/api/audit'),200)
   verify('delete PAN article',c.delete('/api/posts/'+pid,headers=h),200)
   verify('deleted article not found',c.get('/api/posts/'+pid),404)
   verify('restore PAN article',c.post('/api/posts/'+pid+'/restore',headers=h),200)
   verify('logout',c.post('/api/auth/logout',headers=h),200)
   verify('postlogout protected api denied',c.get('/api/me'),401)
 finally:
  server.terminate()
  try:server.wait(timeout=3)
  except subprocess.TimeoutExpired:server.kill();server.wait()
result={'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'cases':checks,
'execution':'Actual uvicorn process and HTTP socket; SQLite isolated temporary DB; external provider keys absent; no real emails sent'}
(OUT/'V6_REAL_HTTP_MATRIX.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print('LIVE HTTP:',result['passed'],'passed',result['failed'],'failed')
