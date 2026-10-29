import asyncio,re,json,base64,mimetypes
from pathlib import Path
from playwright.async_api import async_playwright
from bs4 import BeautifulSoup
import base64,mimetypes
BASE=Path('/mnt/data/_lawygo_qa_work/LAWYGO_전체세션')

# Render with original linked HTML rather than rasterized AI lettering; browser fonts preserve Korean glyphs.
def inline_file(file):
 soup=BeautifulSoup(file.read_text(encoding="utf-8"),"html.parser")
 for elem in soup.find_all("link",href=True):
  if "stylesheet" not in elem.get("rel",[]):continue
  path=(file.parent/elem["href"]).resolve()
  if not path.is_file():continue
  css=path.read_text(encoding="utf-8",errors="replace")
  def url_repl(match):
   raw=match.group(1).strip().strip('\"\'')
   if raw.startswith(("http:","https:","data:","#")):return match.group(0)
   loc=(path.parent/raw).resolve()
   if loc.is_file():return 'url("data:'+ (mimetypes.guess_type(loc.name)[0] or 'image/jpeg')+';base64,'+base64.b64encode(loc.read_bytes()).decode()+'")'
   return match.group(0)
  css=re.sub(r"url\(([^)]+)\)",url_repl,css)
  tag=soup.new_tag("style");tag.string=css;elem.replace_with(tag)
 for elem in soup.find_all("script",src=True):
  path=(file.parent/elem["src"]).resolve()
  if path.is_file():
   elem.attrs.pop("src",None);elem.attrs.pop("defer",None);elem.string=path.read_text(encoding="utf-8",errors="replace")
 for elem in soup.find_all(["img","source"],src=True):
  path=(file.parent/elem["src"]).resolve()
  if path.is_file():elem["src"]='data:'+(mimetypes.guess_type(path.name)[0] or 'image/jpeg')+';base64,'+base64.b64encode(path.read_bytes()).decode()
 return str(soup)

async def main():
 jobs=[]
 newest=BASE/'01_최종완성_웹사이트_Partnership_MOU'
 for png in newest.rglob('*.png'):
  if 'previews' not in str(png.parent):continue
  n=png.stem;pv=png.parent.name
  mode='MOBILE' if 'MOBILE' in n else 'DESKTOP'
  full=n.startswith('FULL--') or n.endswith('--FULL')
  if pv=='previews_partnership':
   section=n.split('--')[0].lower(); path={"home":"index","partnership":"partnership","mou":"mou","inquiry":"partnership-inquiry","contact":"contact"}.get(section)
  elif pv=='previews_wsj':
   section=n.split('--')[1];path='journal/'+section
  else:
   stem=n.replace('FULL--','').replace('MOBILE--','').replace('--','/');path=stem
  html=newest/(path+'.html') if path else None
  if html and html.exists():jobs.append((html,png,mode,full))
  else:print('SKIP-missing',png.name,path)
 for group in (BASE/'02_이전버전_원본소스').iterdir():
  if not group.is_dir():continue
  pv=group/'previews'
  if not pv.exists():continue
  for png in pv.glob('*.png'):
   stem=png.stem.replace('FULL--','').replace('MOBILE--','').replace('--','/')
   html=group/(stem+'.html')
   if html.exists():jobs.append((html,png,'MOBILE' if 'MOBILE' in png.stem else 'DESKTOP','FULL--' in png.stem))
 print('Rendering',len(jobs),'screenshots',flush=True)
 errs=[];count=0
 async with async_playwright() as p:
  b=await p.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
  sem=asyncio.Semaphore(4)
  async def worker(html,png,mode,full):
   nonlocal count
   async with sem:
    page=await b.new_page(viewport={'width':390 if mode=='MOBILE' else 1440,'height':844 if mode=='MOBILE' else 940},device_scale_factor=1)
    try:
     await page.set_content(inline_file(html),wait_until='load',timeout=24000)
     await page.evaluate('document.fonts.ready')
     await page.screenshot(path=str(png),full_page=full,animations='disabled',timeout=25000)
     dims=await page.evaluate('({w:document.documentElement.scrollWidth, v:window.innerWidth})')
     if dims['w']>dims['v']+3:errs.append({'file':str(png.relative_to(BASE)),'issue':'horizontal overflow','width':dims})
    except Exception as e: errs.append({'file':str(png.relative_to(BASE)),'issue':str(e)[:200]})
    finally: await page.close();count+=1
    if count%20==0:print('PROGRESS',count,'/',len(jobs),flush=True)
  await asyncio.gather(*(worker(*job) for job in jobs))
  await b.close()
 print('Screenshots rendered:',count,'issues:',len(errs),flush=True)
 (BASE/'01_최종완성_웹사이트_Partnership_MOU'/'TEXT_IMAGE_QA.json').write_text(json.dumps({'screenshots':count,'issues':errs},ensure_ascii=False,indent=2),encoding='utf-8')
 print('Errors:',errs[:8])
asyncio.run(main())
