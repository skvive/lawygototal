"""Render the actual dashboard HTML/CSS offline; visual check only, not API E2E."""
from pathlib import Path
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT.parent/'preview';OUT.mkdir(exist_ok=True)
html=(ROOT/'static/dashboard.html').read_text()
css=(ROOT/'static/style.css').read_text()
html=html.replace('<script src="/static/dashboard.js" defer></script>','')
html=html.replace('<link rel="stylesheet" href="/static/style.css">',f'<style>{css}</style>')
import base64
svg=(ROOT/'static/logo.svg').read_bytes()
html=html.replace('/static/logo.svg','data:image/svg+xml;base64,'+base64.b64encode(svg).decode())
html=html.replace('<div id="loginPanel" class="data-panel"','<div id="loginPanel" class="data-panel hidden"')
html=html.replace('<div id="adminApp" class="hidden">','<div id="adminApp">')
html=html.replace('<div id="integrationsPanel" class="data-panel hidden">','<div id="integrationsPanel" class="data-panel">')
html=html.replace('<div class="data-panel" id="postsPanel">','<div class="data-panel hidden" id="postsPanel">')
html=html.replace('<span id="accountName" class="role">방문자</span>','<span id="accountName" class="role">관리자 · 운영</span>')
html=html.replace('<div id="ownedChannels"></div>','<div id="ownedChannels"><div class="actions"><strong>Google Blogger</strong><span class="muted">읽기 전용 연결 · 사전 승인이 필요합니다</span></div><div class="actions"><strong>YouTube</strong><span class="muted">소유한 채널만 선택 가능</span></div></div>')
html=html.replace('<div id="syncSources"></div>','<div id="syncSources"><p class="muted">등록 후 원문을 수집하면 공개 전 승인 대기함에 저장됩니다.</p></div>')
html=html.replace('<div id="nativeOutbox"></div>','<div id="nativeOutbox"><p class="muted">기존 LAWYGO Supabase 게시판에 승인 콘텐츠만 발행합니다.</p></div>')
with sync_playwright() as p:
 b=p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox'])
 for mode,dim in [('desktop',{'width':1440,'height':900}),('mobile',{'width':390,'height':844})]:
  page=b.new_page(viewport=dim,device_scale_factor=1)
  page.set_content(html,wait_until='domcontentloaded')
  if mode=='mobile':page.evaluate("document.querySelector('.side').classList.remove('mobile-open')")
  page.screenshot(path=str(OUT/f'CMS_V2_{mode}.png'),full_page=True)
  overflow=page.evaluate('document.documentElement.scrollWidth-window.innerWidth')
  print(mode,'overflow:',overflow,'image:',str(OUT/f'CMS_V2_{mode}.png'))
  page.close()
 b.close()
