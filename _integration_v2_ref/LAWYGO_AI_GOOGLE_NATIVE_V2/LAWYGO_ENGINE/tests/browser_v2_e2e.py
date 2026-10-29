"""Real Chromium UI smoke with temporary seeded runtime. No external API requests."""
import os,subprocess,sys,time,uuid,socket
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
QA_DIR=ROOT/'tests'/'_browser_v2_runtime';QA_DIR.mkdir(exist_ok=True)
for p in QA_DIR.glob('*.db*'):p.unlink()
env={**os.environ,'LAWYGO_DB_PATH':str(QA_DIR/'qa.db'),'LAWYGO_UPLOAD_PATH':str(QA_DIR/'uploads')}
os.environ.update({k:env[k] for k in ('LAWYGO_DB_PATH','LAWYGO_UPLOAD_PATH')})
sys.path.insert(0,str(ROOT));import app
app.init_db()
with app.connect() as db:
 db.execute('INSERT INTO users(id,tenant,email,password_hash,display_name,role,created_at) VALUES(?,?,?,?,?,?,?)',(
  uuid.uuid4().hex,'demo','qa-admin@example.test',app.PH.hash('QA-StrongPassword123!'),'테스트 관리자','admin',app.now()))
proc=subprocess.Popen([sys.executable,'-m','uvicorn','app:app','--host','127.0.0.1','--port','18018'],cwd=ROOT,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
try:
 for _ in range(60):
  with socket.socket() as sock:
   if sock.connect_ex(('127.0.0.1',18018))==0:break
  time.sleep(.25)
 else:raise RuntimeError('Uvicorn did not start')
 with sync_playwright() as p:
  b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
  for mode,vp in [('desktop',{'width':1440,'height':950}),('mobile',{'width':390,'height':844})]:
   page=b.new_page(viewport=vp,device_scale_factor=1)
   errors=[]
   page.on('pageerror',lambda e: errors.append(str(e)))
   page.goto('http://127.0.0.1:18018/dashboard',wait_until='domcontentloaded')
   page.wait_for_selector('#loginForm')
   page.fill('#email','qa-admin@example.test');page.fill('#password','QA-StrongPassword123!')
   page.locator('#loginForm button[type=submit]').click();page.wait_for_selector('#adminApp:not(.hidden)',timeout=15000)
   if mode=='mobile':page.locator('.sidebar-toggle').click()
   page.locator('[data-action="integrations"]').click()
   page.wait_for_selector('#integrationsPanel:not(.hidden)')
   page.screenshot(path=str(ROOT.parent/'preview'/f'integrations-{mode}.png'),full_page=False)
   x=page.evaluate('document.documentElement.scrollWidth - window.innerWidth')
   assert x<=1,(mode,'overflow',x)
   assert not errors,(mode,errors)
   print(mode,'OK integrations rendered; overflow',x,'js errors',len(errors))
   page.close()
  b.close()
finally:
 proc.terminate()
 try:proc.wait(timeout=8)
 except subprocess.TimeoutExpired:proc.kill()
 for p in QA_DIR.glob('*.db*'):p.unlink()
