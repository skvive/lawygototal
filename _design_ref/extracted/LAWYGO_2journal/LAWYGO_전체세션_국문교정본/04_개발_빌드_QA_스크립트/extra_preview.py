from pathlib import Path
import asyncio
from playwright.async_api import async_playwright
code=Path('/mnt/data/render_lawygo_inline.py').read_text().split('async def main():')[0]
exec(code)
async def go():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-web-security','--disable-dev-shm-usage'])
  pg=await b.new_page(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True)
  for file in ['index.html','journal/index.html','pro/index.html','pro/beta.html','wiki/index.html']:
   await pg.set_content(content(file),wait_until='domcontentloaded',timeout=20000)
   dest=PR/('MOBILE--'+file.replace('/','--').replace('.html','.png'))
   await pg.screenshot(path=str(dest),full_page=False,timeout=20000)
   print(file,'mobile dimensions',await pg.evaluate('[document.documentElement.scrollWidth,innerWidth]'),flush=True)
  d=await b.new_page(viewport={'width':1440,'height':900},device_scale_factor=1)
  await d.set_content(content('sitemap.html'),wait_until='domcontentloaded',timeout=20000)
  await d.screenshot(path=str(PR/'sitemap.png'),full_page=False,timeout=20000)
  await b.close()
asyncio.run(go())
