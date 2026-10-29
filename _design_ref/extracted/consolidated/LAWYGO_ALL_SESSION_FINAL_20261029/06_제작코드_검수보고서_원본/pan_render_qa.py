from playwright.sync_api import sync_playwright
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,time
root=Path('/mnt/data/LAWYGO_PAN_CUSTOMER_SITE'); pages=sorted([p for p in root.glob('*.html')]);results=[]
with sync_playwright() as pw:
 b=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--disable-features=TranslateUI'])
 for width,mobile in [(1365,False),(390,True)]:
  ctx=b.new_context(viewport={'width':width,'height':900 if not mobile else 844},device_scale_factor=1,locale='ko-KR')
  page=ctx.new_page()
  errs=[];page.on('pageerror',lambda ex: errs.append(str(ex)))
  for i,p in enumerate(pages):
   try:
    page.goto("http://127.0.0.1:18744/"+p.name,wait_until='load',timeout=15000)
    page.wait_for_timeout(100)
    path=root/'previews'/(p.stem+('-mobile' if mobile else '-desktop')+'.png')
    page.screenshot(path=str(path),full_page=False,timeout=7000)
    overflow=page.evaluate('document.documentElement.scrollWidth > window.innerWidth + 3')
    broken=page.evaluate('Array.from(document.images).filter(i => !i.complete || i.naturalWidth===0).map(i=>i.getAttribute("src"))')
    results.append({'page':p.name,'mode':'mobile' if mobile else 'desktop','overflow':overflow,'images':broken,'errors':list(errs)})
    errs.clear()
   except Exception as e:results.append({'page':p.name,'mode':'mobile' if mobile else 'desktop','error':str(e)[:180]})
  ctx.close()
 b.close()
(root/'docs'/'RENDER_QA.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print('pages',len(pages),'screenshots',len(list((root/'previews').glob('*.png'))),'failed',sum(1 for x in results if x.get('error')),'overflow',sum(1 for x in results if x.get('overflow')),'broken images',sum(len(x.get('images',[])) for x in results),'js errors',sum(len(x.get('errors',[])) for x in results))
for x in results:
 if x.get('error') or x.get('overflow') or x.get('images') or x.get('errors'):
  print(x)
