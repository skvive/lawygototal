import asyncio,json,base64,re,mimetypes
from pathlib import Path
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
root=Path('/mnt/data/LAWYGO_PARTNERSHIP_SITE');pv=root/'previews_partnership';pv.mkdir(exist_ok=True)
def inline(file):
 soup=BeautifulSoup(file.read_text('utf8'),'html.parser')
 for tag in soup.find_all('link',href=True):
  if tag.get('rel')==['stylesheet']:
   path=(file.parent/tag['href']).resolve()
   if path.is_file():
    style=soup.new_tag('style');style.string=path.read_text('utf8');tag.replace_with(style)
 for tag in soup.find_all('script',src=True):
  path=(file.parent/tag['src']).resolve()
  if path.is_file():
   tag.attrs.pop('src',None);tag.attrs.pop('defer',None);tag.string=path.read_text('utf8')
 for tag in soup.find_all(['img','source'],src=True):
  path=(file.parent/tag['src']).resolve()
  if path.is_file():tag['src']='data:'+ (mimetypes.guess_type(path.name)[0] or 'image/png')+';base64,'+base64.b64encode(path.read_bytes()).decode()
 for tag in soup.find_all(style=True):
  if 'url(' in tag['style']:pass
 for t in soup.select('style'):
  # inline CSS url images into data URIs
  def rep(m):
   raw=m.group(1).strip('"\' ')
   if raw.startswith(('http','data:','#')):return m.group(0)
   path=(file.parent/'assets'/raw).resolve()
   if path.is_file():return 'url("data:'+(mimetypes.guess_type(path.name)[0] or 'image/jpeg')+';base64,'+base64.b64encode(path.read_bytes()).decode()+'")'
   return m.group(0)
  t.string=re.sub(r'url\(([^)]+)\)',rep,t.string or '')
 return str(soup)
async def run():
 errors=[]; checks={}
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
  for file,nam in [('partnership.html','PARTNERSHIP'),('partnership-inquiry.html','INQUIRY'),('mou.html','MOU'),('index.html','HOME'),('contact.html','CONTACT')]:
   markup=inline(root/file)
   for mode,ww,hh in [('DESKTOP',1440,960),('MOBILE',390,844)]:
    pg=await b.new_page(viewport={'width':ww,'height':hh},device_scale_factor=1)
    await pg.set_content(markup,wait_until='load',timeout=30000)
    await pg.screenshot(path=str(pv/f'{nam}--{mode}.png'),full_page=False,timeout=30000)
    if nam=='PARTNERSHIP' and mode=='DESKTOP': await pg.screenshot(path=str(pv/f'{nam}--FULL.png'),full_page=True,timeout=30000)
    dims=await pg.evaluate('({scroll:document.documentElement.scrollWidth,inner:window.innerWidth,contact:document.body.innerText.includes("대한에이전트협회"),links:document.querySelectorAll("a").length})')
    checks[f'{nam}_{mode}']=dims
    if dims['scroll']>dims['inner']+3:errors.append(f'overflow {nam} {mode}: {dims}')
    await pg.close()
  checks['inquiry_to_correct_email']='sk@terrabridge.us' in (root/'assets'/'partnership.js').read_text('utf8')
  checks['mou_has_address']='서초중앙로22길 47' in (root/'mou.html').read_text('utf8')
  await b.close()
 (root/'PARTNERSHIP_QA.json').write_text(json.dumps({'checks':checks,'errors':errors},ensure_ascii=False,indent=2),'utf8')
 print(json.dumps({'checks':checks,'errors':errors},ensure_ascii=False,indent=2))
asyncio.run(run())
