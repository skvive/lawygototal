import asyncio,os,json,re,base64
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageOps
from playwright.async_api import async_playwright
ROOT=Path('/mnt/data/LAWYGO_ATLAS_SITE')
PAGES=json.loads((ROOT/'PAGES.json').read_text())
PR=ROOT/'previews';PR.mkdir(exist_ok=True)
CSS=(ROOT/'assets/site.css').read_text();JS=(ROOT/'assets/site.js').read_text()
# inline asset urls for screenshot since network and filesystem navigation disabled in browser sandbox
cache={}
def imgdata(f):
 key=str(f)
 if key not in cache:
  if f.exists():cache[key]='data:image/jpeg;base64,'+base64.b64encode(f.read_bytes()).decode()
  else:cache[key]=''
 return cache[key]
def content(path):
 src=(ROOT/path).read_text()
 # inline css; place js at body end for event listeners (defer not supported on inline scripts)
 src=re.sub(r'<link rel="stylesheet" href="[^"]+">',lambda m:'<style>'+CSS+'</style>',src)
 src=re.sub(r'<script defer src="[^"]+"></script>','',src)
 src=src.replace('</body>','<script>'+JS+'</script></body>')
 folder=(ROOT/path).parent
 def convert(raw):
  if raw.startswith('data:') or raw.startswith('https://'):return raw
  return imgdata((folder/raw).resolve())
 src=re.sub(r'(<img\b[^>]*\bsrc=")([^"]+)(")',lambda m:m.group(1)+convert(m.group(2))+m.group(3),src)
 src=re.sub(r"(background-image:url\(')([^']+)('\))",lambda m:m.group(1)+convert(m.group(2))+m.group(3),src)
 return src
async def main():
 results=[]
 async with async_playwright() as pp:
  browser=await pp.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-web-security','--disable-dev-shm-usage'])
  d=await browser.new_context(viewport={'width':1440,'height':900},device_scale_factor=1)
  m=await browser.new_context(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True)
  page=await d.new_page();mpage=await m.new_page()
  pageerrors=[];page.on('pageerror',lambda e:pageerrors.append(str(e)))
  important=['index.html','journal/index.html','wiki/index.html','note/index.html','pro/index.html','pan/index.html','pro/beta.html','journal/market-intelligence.html','pro/enterprise.html','pricing.html']
  for item in PAGES:
   path=item['path'];html=content(path)
   await page.set_content(html,wait_until='load');await page.wait_for_timeout(35)
   broken=await page.locator('img').evaluate_all('es=>es.filter(x=>!x.complete||x.naturalWidth===0).map(x=>x.getAttribute("alt"))')
   width=await page.evaluate('document.documentElement.scrollWidth');inner=await page.evaluate('innerWidth')
   dest=PR/(path.replace('/','--').replace('.html','.png'))
   await page.screenshot(path=str(dest),full_page=False,animations='disabled')
   row={'path':path,'image':str(dest.relative_to(ROOT)),'imagesBroken':broken,'desktopOverflow':width>inner+2,'desktopWidth':[width,inner]}
   if path in important:
    await page.screenshot(path=str(PR/('FULL--'+path.replace('/','--').replace('.html','.png'))),full_page=True,animations='disabled')
   results.append(row)
  for path in ['index.html','journal/index.html','wiki/index.html','note/index.html','pro/index.html','pro/beta.html','pan/index.html','pricing.html']:
   await mpage.set_content(content(path),wait_until='load');await mpage.wait_for_timeout(30)
   width=await mpage.evaluate('document.documentElement.scrollWidth');inner=await mpage.evaluate('innerWidth')
   await mpage.screenshot(path=str(PR/('MOBILE--'+path.replace('/','--').replace('.html','.png'))),full_page=True,animations='disabled')
   row=next(x for x in results if x['path']==path);row['mobileOverflow']=width>inner+2;row['mobileWidth']=[width,inner]
  await page.set_content(content('pro/dashboard.html'));await page.locator('[data-dash="schedule"]').click();print('DASH CLICK',await page.locator('#dashTitle').inner_text())
  await mpage.set_content(content('pro/index.html'));await mpage.locator('.menu-toggle').click();print('MOBILE MENU',await mpage.locator('#mobileNav').evaluate('(e)=>getComputedStyle(e).display'))
  print('JS ERRORS',pageerrors[:10]);await browser.close()
 print('QA',len(results),'pages; issues',[(x['path'],x['imagesBroken'],x['desktopOverflow'],x.get('mobileOverflow')) for x in results if x['imagesBroken'] or x['desktopOverflow'] or x.get('mobileOverflow')])
 (ROOT/'QA_REPORT.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
 W,H=375,290;cols=5;rows=(len(results)+cols-1)//cols
 sheet=Image.new('RGB',(W*cols,H*rows),'#edeae3');draw=ImageDraw.Draw(sheet)
 fontpath='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';f=ImageFont.truetype(fontpath,12)
 for i,r in enumerate(results):
  im=Image.open(ROOT/r['image']).convert('RGB');im=ImageOps.fit(im,(W-18,H-50),method=Image.Resampling.LANCZOS,centering=(.5,0))
  x=i%cols*W;y=i//cols*H;sheet.paste(im,(x+9,y+7));draw.text((x+9,y+H-31),f'{i+1:02d}  '+r['path'],font=f,fill='#233d56')
 sheet.save(PR/'ALL_PAGES_CONTACT_SHEET.jpg',quality=90)
 print('CONTACT_SHEET',PR/'ALL_PAGES_CONTACT_SHEET.jpg')
asyncio.run(main())
