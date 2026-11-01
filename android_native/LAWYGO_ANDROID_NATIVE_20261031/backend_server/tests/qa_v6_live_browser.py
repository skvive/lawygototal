"""Real Chromium + real uvicorn + isolated SQLite. Not a static HTML render."""
import json, os, socket, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
import httpx
from urllib.parse import urlsplit
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT.parent.parent/'V6_REAL_BROWSER_SCREENS'
OUT.mkdir(exist_ok=True)

def free_port():
 with socket.socket() as s:
  s.bind(('127.0.0.1',0));return s.getsockname()[1]

results=[]
def check(name,truth,detail=''):
 results.append({'name':name,'pass':bool(truth),'detail':str(detail)[:160]})
 if not truth:raise AssertionError(f'{name}: {detail}')

with tempfile.TemporaryDirectory(prefix='lawygo_v6_realbrowser_') as td:
 env=os.environ.copy();env['LAWYGO_DB_PATH']=str(Path(td)/'db.sqlite');env['LAWYGO_UPLOAD_PATH']=str(Path(td)/'uploads');env['LAWYGO_NEWSLETTER_ALLOW_SEND']='false'
 admin_email='qa-admin@lawygo.example.com';admin_password='BrowserE2E!2026Strong'
 subprocess.run([sys.executable,'bootstrap_admin.py','--email',admin_email,'--password',admin_password,'--name','품질검수 관리자'],cwd=ROOT,env=env,check=True,capture_output=True)
 port=free_port();base=f'http://127.0.0.1:{port}'
 proc=subprocess.Popen([sys.executable,'-m','uvicorn','app:app','--host','127.0.0.1','--port',str(port),'--log-level','warning'],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
 try:
  with httpx.Client(base_url=base,timeout=6) as http:
   for i in range(100):
    try:
     if http.get('/api/health').status_code==200:break
    except Exception: pass
    time.sleep(.1)
   else:raise RuntimeError('실제 HTTP 서버 시작 실패')
   check('실제 서버 상태',http.get('/api/health').status_code==200)
   check('비로그인 관리자 API 거부',http.get('/api/hub/modules').status_code==401)
   check('비로그인 작성 거부',http.post('/api/posts',json={}).status_code==401)
   for path in ['/','/journal','/channel','/pan','/wiki','/note','/pro','/dashboard','/editor','/hub']:
    check('페이지 HTTP '+path,http.get(path).status_code==200)
   check('실계정 인증 오류 재현',http.post('/api/auth/login',json={'email':admin_email,'password':'WRONG'}).status_code==401)
   auth=http.post('/api/auth/login',json={'email':admin_email,'password':admin_password})
   check('실제 로그인 API',auth.status_code==200)
   csrf=http.cookies.get('lawygo_cms_csrf');headers={'X-CSRF-Token':csrf}
   check('CSRF 거부 재현',http.post('/api/posts',json={}).status_code==403)
   boards=http.get('/api/boards').json()['items'];pan=next(b for b in boards if b['product']=='pan');wiki=next(b for b in boards if b['product']=='wiki')
   panpost=http.post('/api/posts',headers=headers,json={'board_id':pan['id'],'kind':'blog','title':'LAWYGO 실제 판 법률 칼럼 테스트','body':'표시와 검색이 가능한 게시물 테스트입니다.','status':'published','visibility':'public'})
   check('판 게시글 실제 저장',panpost.status_code==201,panpost.text);pan_id=panpost.json()['id']
   wikires=http.post('/api/posts',headers=headers,json={'board_id':wiki['id'],'kind':'encyclopedia','title':'법률백과 실제 동작 검증','body':'근로계약은 서면으로 주요 조건을 확인해야 합니다.','status':'published','visibility':'public'})
   check('위키 게시글 실제 저장',wikires.status_code==201,wikires.text)
   check('위키 검색 실제 반영',http.get('/api/wiki/search?q='+httpx.QueryParams({'q':'근로계약'})['q']).status_code==200 and http.get('/api/wiki/search',params={'q':'근로계약'}).json()['items']!=[])
   check('편집실 자동발송 기본 차단',http.post('/api/growth/newsletter/admin/send',headers=headers,json={'subject':'로이고 메일 발송 잠금 테스트','body':'뉴스레터 발송 잠금으로 실제 발송이 수행되지 않아야 합니다.','confirmed_preview':True}).status_code==503)
   edited=http.patch('/api/posts/'+pan_id,headers=headers,json={'version':1,'title':'LAWYGO 판 실제 수정 완료'})
   check('게시글 수정',edited.status_code==200)
   check('오래된 편집 버전 거부',http.patch('/api/posts/'+pan_id,headers=headers,json={'version':1,'title':'오래된 수정'}).status_code==409)
   check('기존 외부 API 키 없을 때 노트 AI fail-closed',http.get('/api/hub/health').status_code==200)
   check('Hub API 통계 집계',http.get('/api/hub/metrics').status_code==200)
  # Browser with its own session; verifies REAL UI navigation, not a data URI screenshot.
  with sync_playwright() as pw:
   browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
   front='https://qa.lawygo.example'
   proxy=httpx.Client(timeout=10,follow_redirects=False)
   def forward(route):
    req=route.request; u=urlsplit(req.url)
    if u.hostname!='qa.lawygo.example':
     return route.abort()
    headers={k:v for k,v in req.headers.items() if k.lower() not in ('content-length','connection','accept-encoding')}
    headers['host']='qa.lawygo.example'
    path=u.path+('?' + u.query if u.query else '')
    try:
     rr=proxy.request(req.method,base+path,headers=headers,content=req.post_data_buffer)
     hh={k:v for k,v in rr.headers.items() if k.lower() not in ('transfer-encoding','connection','content-encoding','content-length')}
     route.fulfill(status=rr.status_code,headers=hh,body=rr.content)
    except Exception as exc:
     route.fulfill(status=502,body='QA test proxy unavailable: '+type(exc).__name__)
   context=browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1)
   context.route('**/*',forward)
   page=context.new_page();errors=[];console_errors=[]
   page.on('pageerror',lambda e:errors.append(str(e)))
   page.on('console',lambda m:console_errors.append(m.text) if m.type=='error' else None)
   page.goto(front+'/journal',wait_until='networkidle')
   check('저널 실제 브라우저 열기',page.locator('body').inner_text().__contains__('LAWYGO'))
   page.screenshot(path=str(OUT/'01-journal-real-desktop.png'),full_page=True)
   page.goto(front+'/pan',wait_until='networkidle')
   check('로판 실제 기사 노출',page.get_by_text('LAWYGO 판 실제 수정 완료').count()>0)
   page.screenshot(path=str(OUT/'02-pan-live-content.png'),full_page=True)
   page.goto(front+'/wiki',wait_until='networkidle')
   page.locator('#wikiSearch').fill('근로계약');page.locator('#wikiGo').click()
   page.get_by_text('법률백과 실제 동작 검증').wait_for(timeout=7000)
   check('위키 실검색 브라우저',True)
   page.screenshot(path=str(OUT/'03-wiki-live-search.png'),full_page=True)
   page.goto(front+'/dashboard',wait_until='networkidle')
   page.locator('#email').fill(admin_email);page.locator('#password').fill(admin_password)
   page.locator('#loginForm button[type="submit"]').click()
   page.locator('#adminApp:not(.hidden)').wait_for(timeout=10000)
   check('관리자 실제 웹 로그인',page.locator('#kpiBoards').inner_text()=='13')
   page.screenshot(path=str(OUT/'04-admin-real-dashboard.png'),full_page=True)
   page.locator('#newPostBtn').click();page.locator('#postModal.open').wait_for()
   page.locator('#postTitle').fill('브라우저에서 직접 쓴 신규 콘텐츠')
   page.locator('#postBody').fill('UI 버튼과 저장 API의 종단간 연결을 검증합니다.')
   page.locator('#postStatus').select_option('published')
   page.locator('#postForm button[type="submit"]').click()
   page.locator('#postModal.open').wait_for(state='hidden',timeout=10000)
   page.get_by_text('브라우저에서 직접 쓴 신규 콘텐츠').wait_for(timeout=10000)
   check('브라우저 게시글 작성·저장',True)
   page.screenshot(path=str(OUT/'05-admin-created-post.png'),full_page=True)
   page.goto(front+'/hub',wait_until='networkidle')
   check('Hub 실제 브라우저 접근',page.locator('body').inner_text().__contains__('LAWYGO'))
   page.screenshot(path=str(OUT/'06-admin-hub-real.png'),full_page=True)
   mobile=browser.new_context(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True)
   mobile.route('**/*',forward)
   mp=mobile.new_page();mp.on('pageerror',lambda e:errors.append(str(e)))
   for index,path in enumerate(['/','/journal','/pan','/wiki','/note','/pro','/channel','/editor']):
    mp.goto(front+path,wait_until='networkidle');width=mp.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth')
    check('모바일 가로넘침 '+path,width<=2,f'overflow: {width}px')
    if path in ['/','/journal','/pan','/editor']:
     mp.screenshot(path=str(OUT/f'07-mobile-{path.strip("/") or "home"}.png'),full_page=True)
   check('브라우저 JavaScript 예외',not errors,errors)
   check('브라우저 콘솔 오류',not console_errors,console_errors[:5])
   browser.close();proxy.close()
 finally:
  proc.terminate()
  try:proc.wait(timeout=3)
  except subprocess.TimeoutExpired:proc.kill();proc.wait()
report={'passed':sum(x['pass'] for x in results),'failed':sum(not x['pass'] for x in results),'tests':results,'screenshots':len(list(OUT.glob('*.png')))}
(OUT/'BROWSER_HTTP_REAL_REPORT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps({'passed':report['passed'],'failed':report['failed'],'screenshots':report['screenshots']},ensure_ascii=False))
