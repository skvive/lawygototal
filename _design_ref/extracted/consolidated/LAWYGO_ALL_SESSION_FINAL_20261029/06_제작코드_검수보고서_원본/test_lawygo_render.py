import asyncio,os
from pathlib import Path
from playwright.async_api import async_playwright
import threading
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

async def main():
 handler=partial(SimpleHTTPRequestHandler, directory="/mnt/data/lawygo_journal")
 server=ThreadingHTTPServer(("127.0.0.1", 8765),handler)
 threading.Thread(target=server.serve_forever,daemon=True).start()
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--disable-web-security'])
  d=await b.new_context(viewport={'width':1440,'height':900},device_scale_factor=1)
  page=await d.new_page(); errors=[]
  page.on('pageerror',lambda e: errors.append(str(e)))
  await page.set_content(Path('/mnt/data/lawygo_journal/index.html').read_text(),wait_until='domcontentloaded');await page.wait_for_timeout(1800)
  await page.screenshot(path='/mnt/data/LAWYGO_JOURNAL_desktop_preview.png',full_page=True)
  print('desktop title',await page.title(),'features',await page.locator('.feature').count(),'tiles',await page.locator('.article-tile').count())
  await page.locator('[data-filter="기업·투자"]').click()
  print('filtered',await page.locator('.article-tile').count())
  await page.locator('[data-filter="all"]').click()
  await page.locator('.article-tile').first.click();print('modal visible',await page.locator('#modalLayer').evaluate('(e)=>e.classList.contains("show")'))
  await page.keyboard.press('Escape');print('modal closed',await page.locator('#modalLayer').evaluate('(e)=>!e.classList.contains("show")'))
  print('errors',errors)
  m=await b.new_context(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True)
  pm=await m.new_page();e2=[];pm.on('pageerror',lambda e:e2.append(str(e)))
  await pm.set_content(Path('/mnt/data/lawygo_journal/index.html').read_text(),wait_until='domcontentloaded');await pm.wait_for_timeout(800)
  await pm.screenshot(path='/mnt/data/LAWYGO_JOURNAL_mobile_preview.png',full_page=True)
  print('mobile overflow',await pm.evaluate('document.documentElement.scrollWidth > window.innerWidth'), 'width',await pm.evaluate('[document.documentElement.scrollWidth,window.innerWidth]'))
  await pm.locator('#mobileMenu').click(); print('menu toggled',await pm.locator('#navlinks').evaluate('(e)=>e.classList.contains("open")'))
  print('mobile errors',e2)
  await b.close()
asyncio.run(main())
