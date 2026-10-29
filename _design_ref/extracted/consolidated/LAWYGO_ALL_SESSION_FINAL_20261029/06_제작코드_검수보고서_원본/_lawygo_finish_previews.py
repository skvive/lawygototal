from pathlib import Path
import asyncio
from playwright.async_api import async_playwright
scope={};exec(Path('/mnt/data/_lawygo_render_all_qa.py').read_text().split('async def main():')[0],scope)
inline_file=scope['inline_file']
base=Path('/mnt/data/_lawygo_qa_work/LAWYGO_전체세션')
latest=base/'01_최종완성_웹사이트_Partnership_MOU'
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
  jobs=[]
  for group in (base/'02_이전버전_원본소스').iterdir():
   if not group.is_dir():continue
   for png in (group/'previews').glob('*.png'):
    name=png.stem.replace('FULL--','').replace('MOBILE--','').replace('--','/')
    source=group/(name+'.html')
    if source.is_file(): jobs.append((source,png,'MOBILE' if 'MOBILE--' in png.name else 'DESKTOP',png.name.startswith('FULL--')))
  for nm,path in [('PARTNERSHIP--DESKTOP.png','partnership.html'),('PARTNERSHIP--MOBILE.png','partnership.html')]:
   jobs.append((latest/path,latest/'previews_partnership'/nm,'MOBILE' if 'MOBILE' in nm else 'DESKTOP',False))
  for n,(src,out,mode,full) in enumerate(jobs):
   pg=await b.new_page(viewport={'width':390 if mode=='MOBILE' else 1440,'height':844 if mode=='MOBILE' else 950},device_scale_factor=1)
   try:
    await pg.set_content(inline_file(src),wait_until='domcontentloaded',timeout=15000)
    await pg.screenshot(path=str(out),full_page=full,timeout=14000,animations='disabled')
    print(n+1,'OK',out.name,flush=True)
   except Exception as e:print(n+1,'FAIL',out.name,str(e)[:120],flush=True)
   finally:await pg.close()
  await b.close()
asyncio.run(main())
