"""Static layout inspection ONLY. Actual API E2E is qa_v6_http_matrix.py.
All HTML, CSS and images from source; executable scripts intentionally removed since local
browser network navigation is blocked by execution policy."""
import base64,json,re
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
E=Path(__file__).resolve().parents[1];ST=E/'static';OUT=E.parent.parent/'V6_STATIC_VISUAL_QA';OUT.mkdir(exist_ok=True)
pages={'home':'index-v5.html','journal':'journal.html','channel':'channel-v5.html','pan':'pan-v5.html','wiki':'wiki-v5.html','note':'note-v5.html','pro':'pro-v5.html','editor':'editor-v5.html','dashboard':'dashboard.html','hub':'hub.html'}
css={'editorial.css','style.css','hub.css'}
styles='\n'.join((ST/name).read_text() for name in sorted(css))
def asset_data(m):
 name=m.group(1);f=ST/name
 if not f.is_file():return m.group(0)
 suff=f.suffix.lower();mime={'jpg':'image/jpeg','jpeg':'image/jpeg','png':'image/png','webp':'image/webp','svg':'image/svg+xml'}.get(suff.lstrip('.'))
 return "url('data:"+mime+";base64,"+base64.b64encode(f.read_bytes()).decode()+"')" if mime else m.group(0)
styles=re.sub(r'url\([\'\"]?/static/([^\)\'\"]+)[\'\"]?\)',asset_data,styles)
checks=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for screen,width,height in [('desktop',1440,900),('mobile',390,844)]:
  ctx=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1)
  pg=ctx.new_page()
  for name,src in pages.items():
   soup=BeautifulSoup((ST/src).read_text(),'html.parser')
   for tag in list(soup.find_all('script')):tag.decompose()
   for tag in list(soup.find_all('link')):
    if tag.get('rel') and any(x in tag['rel'] for x in ['stylesheet','icon']):tag.decompose()
   for tag in soup.find_all('img'):
    url=tag.get('src','')
    if url.startswith('/static/'):
     file=ST/url[len('/static/'):]
     mime={'jpg':'image/jpeg','jpeg':'image/jpeg','webp':'image/webp','png':'image/png','svg':'image/svg+xml'}.get(file.suffix.lower().lstrip('.'))
     if file.is_file() and mime:tag['src']=f'data:{mime};base64,'+base64.b64encode(file.read_bytes()).decode()
   style_node=soup.new_tag('style')
   style_node.string=styles
   (soup.head or soup).append(style_node)
   pg.set_content(str(soup),wait_until='load')
   pg.wait_for_timeout(90)
   overflow=pg.evaluate('document.documentElement.scrollWidth - document.documentElement.clientWidth')
   checked={'screen':screen,'page':name,'overflow_px':overflow,'pass':overflow<=2}
   checks.append(checked)
   pg.screenshot(path=str(OUT/f'{screen}-{name}.png'),full_page=True)
  ctx.close()
 browser.close()
(OUT/'STATIC_VISUAL_REPORT.json').write_text(json.dumps({'screenshots':len(checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,'note':'Offline static HTML, CSS, local images only. Not live browser E2E.'},ensure_ascii=False,indent=2))
print('visual renders',len(checks),'overflow failures',sum(not x['pass'] for x in checks))
