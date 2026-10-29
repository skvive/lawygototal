import asyncio, os, json, re, threading
from pathlib import Path
from functools import partial
from http.server import SimpleHTTPRequestHandler,ThreadingHTTPServer
from PIL import Image,ImageDraw,ImageFont,ImageOps
from playwright.async_api import async_playwright
ROOT=Path('/mnt/data/LAWYGO_ATLAS_SITE'); previews=ROOT/'previews'; previews.mkdir(exist_ok=True)
PAGES=json.loads((ROOT/'PAGES.json').read_text())
class QuietHandler(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass
async def main():
 server=ThreadingHTTPServer(('127.0.0.1',8899),partial(QuietHandler,directory=str(ROOT))); threading.Thread(target=server.serve_forever,daemon=True).start()
 results=[]
 async with async_playwright() as pp:
  browser=await pp.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
  desktop=await browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1)
  mobile=await browser.new_context(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True)
  page=await desktop.new_page(); mpage=await mobile.new_page()
  consoleerrors=[];page.on('pageerror',lambda e:consoleerrors.append(str(e)))
  important=['index.html','journal/index.html','wiki/index.html','note/index.html','pro/index.html','pan/index.html','pro/beta.html','journal/market-intelligence.html','pro/enterprise.html','pricing.html','pro/desk.html','pro/case.html','pro/flow.html','pro/work.html','pro/hub.html','pro/smart.html']
  for i,row in enumerate(PAGES):
   url='http://127.0.0.1:8899/'+row['path']
   resp=await page.goto(url,wait_until='domcontentloaded')
   await page.wait_for_timeout(100)
   errors=await page.evaluate('''()=>({brokenImages:[...document.images].filter(img=>!img.complete||img.naturalWidth===0).map(img=>img.getAttribute('src')),bodyWidth:document.body.scrollWidth,inner:innerWidth,links:[...document.querySelectorAll('a[href]')].filter(a=>a.getAttribute('href')?.endsWith('.html')).map(a=>a.getAttribute('href'))})''')
   imagepath=previews/(row['path'].replace('/','--').replace('.html','.png'))
   await page.screenshot(path=str(imagepath),full_page=False)
   rec=dict(path=row['path'],status=resp.status if resp else None,brokenImages=errors['brokenImages'],desktopOverflow=errors['bodyWidth']>errors['inner']+2,links=len(errors['links']),screenshot=str(imagepath.relative_to(ROOT)))
   if row['path'] in important:
    full=previews/('FULL--'+row['path'].replace('/','--').replace('.html','.png'))
    await page.screenshot(path=str(full),full_page=True)
   results.append(rec)
  # mobile selected
  for row in ['index.html','journal/index.html','wiki/index.html','note/index.html','pro/index.html','pro/beta.html','pan/index.html','pricing.html']:
   await mpage.goto('http://127.0.0.1:8899/'+row,wait_until='domcontentloaded');await mpage.wait_for_timeout(120)
   width=await mpage.evaluate('document.documentElement.scrollWidth'); inner=await mpage.evaluate('innerWidth')
   await mpage.screenshot(path=str(previews/('MOBILE--'+row.replace('/','--').replace('.html','.png'))),full_page=True)
   rec=next(x for x in results if x['path']==row);rec['mobileOverflow']=width>inner+2;rec['mobileWidth']=[width,inner]
  # buttons
  await page.goto('http://127.0.0.1:8899/pro/dashboard.html');await page.locator('button[data-dash="schedule"]').click();print('dashboard toggle',await page.locator('#dashTitle').inner_text())
  await page.goto('http://127.0.0.1:8899/wiki/search.html');print('wiki search input',await page.locator('#wikiSearchInput').count())
  await mpage.goto('http://127.0.0.1:8899/pro/index.html');await mpage.locator('.menu-toggle').click();print('mobile menu displayed',await mpage.locator('#mobileNav').evaluate('(e)=>getComputedStyle(e).display'))
  print('JS ERRORS',consoleerrors)
  await browser.close()
 server.shutdown()
 (ROOT/'QA_REPORT.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
 print('PAGE COUNT',len(results),'bad',[(x['path'],x['status'],x['brokenImages'],x['desktopOverflow'],x.get('mobileOverflow')) for x in results if x['status']!=200 or x['brokenImages'] or x['desktopOverflow'] or x.get('mobileOverflow')])
 # Contact sheet / 5 cols / 7 rows
 width,height=380,300; cols=5; rows=(len(results)+cols-1)//cols
 sheet=Image.new('RGB',(cols*width,rows*height),'#f3f0e9');draw=ImageDraw.Draw(sheet)
 fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
 f=ImageFont.truetype(fontpath,13)
 for i,r in enumerate(results):
  p=previews/r['screenshot']; im=Image.open(p).convert('RGB'); im=ImageOps.fit(im,(width-20,height-48),method=Image.Resampling.LANCZOS,centering=(.5,0));x=(i%cols)*width;y=(i//cols)*height
  sheet.paste(im,(x+10,y+7));draw.text((x+10,y+height-33),str(i+1).zfill(2)+'  '+r['path'],fill='#172b3b',font=f)
 sheet.save(previews/'ALL_PAGES_CONTACT_SHEET.jpg',quality=85)
asyncio.run(main())
