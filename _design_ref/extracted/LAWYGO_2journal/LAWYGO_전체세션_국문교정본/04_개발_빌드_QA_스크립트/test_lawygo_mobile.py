import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
async def main():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
  context=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=1)
  page=await context.new_page();errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  import re
  html=Path('/mnt/data/lawygo_journal/index.html').read_text()
  html=re.sub(r'<link[^>]+fonts\.googleapis[^>]*>', '', html)
  html=re.sub(r'<link[^>]+fonts\.gstatic[^>]*>', '', html)
  await page.set_content(html,wait_until='domcontentloaded',timeout=10000)
  await page.wait_for_timeout(400)
  print('widths',await page.evaluate('[document.documentElement.scrollWidth,innerWidth]'),flush=True)
  print('errors',errors,flush=True)
  await page.screenshot(path='/mnt/data/LAWYGO_JOURNAL_mobile_preview.png',full_page=True,timeout=20000)
  print('mobile screen saved',flush=True)
  await b.close()
asyncio.run(main())
