from pathlib import Path
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import base64,json,mimetypes
SITE=Path('/mnt/data/LAWYGO_PAN_2026_EXPANSION/site');out=SITE/'previews'
slugs=['content-feed','free-signup','advertising','investor-overview']
error=[];shots=[]
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-extensions'])
 for slug in slugs:
  s=BeautifulSoup((SITE/f'{slug}.html').read_text(),'html.parser')
  # Inline all assets to avoid browser network policy. This is a static visual check, not a full E2E browser API check.
  for link in s.select('link[rel="stylesheet"]'):
   target=SITE/link.get('href','')
   if target.exists():
    st=s.new_tag('style');st.string=__import__('re').sub(r'@import[^;]+;', '', target.read_text());link.replace_with(st)
  for img in s.select('img[src]'):
   val=img.get('src');target=SITE/val
   if target.exists() and target.stat().st_size<2000000:
    mt=mimetypes.guess_type(target.name)[0] or 'image/jpeg'
    img['src']='data:'+mt+';base64,'+base64.b64encode(target.read_bytes()).decode()
  for el in s.select('script[src]'):el.decompose()
  html=str(s)
  for typ,w,h in [('desktop',1365,900),('mobile',390,844)]:
   pg=browser.new_page(viewport={'width':w,'height':h},device_scale_factor=1)
   errors=[];pg.on('pageerror',lambda exc:errors.append(str(exc)))
   pg.route('**/*',lambda route:route.abort());pg.set_content(html,wait_until='domcontentloaded',timeout=6000)
   pg.wait_for_timeout(100)
   overflow=pg.evaluate('document.documentElement.scrollWidth')
   if overflow>w+2:errors.append('overflow:'+str(overflow)+' vs '+str(w))
   f=out/f'EXPANDED_{slug}-{typ}.png';pg.screenshot(path=str(f),full_page=False,timeout=8000)
   shots.append(f.name)
   if errors:error.append((slug,typ,errors))
   pg.close()
 browser.close()
print('screenshots',len(shots),'errors',error)
(Path('/mnt/data/LAWYGO_PAN_2026_EXPANSION')/'VISUAL_QA.json').write_text(json.dumps({'snapshots':shots,'errors':error,'notes':'External browser navigation was blocked; used local HTML with inline image/CSS for static responsive screenshot checks. Scripts excluded from these screenshots; API tested separately.'},ensure_ascii=False,indent=2))
