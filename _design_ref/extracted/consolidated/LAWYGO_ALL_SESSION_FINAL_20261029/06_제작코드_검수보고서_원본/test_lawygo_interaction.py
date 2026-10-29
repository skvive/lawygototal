import asyncio,re
from pathlib import Path
from playwright.async_api import async_playwright
async def main():
 html=Path('/mnt/data/lawygo_journal/index.html').read_text()
 html=re.sub(r'<link[^>]+fonts\.googleapis[^>]*>','',html)
 html=re.sub(r'<link[^>]+fonts\.gstatic[^>]*>','',html)
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
  page=await browser.new_page(viewport={'width':1280,'height':800})
  errors=[]
  page.on('pageerror', lambda e:errors.append(str(e)))
  await page.set_content(html,wait_until='domcontentloaded',timeout=15000)
  print('initial',await page.locator('.article-tile').count(),flush=True)
  await page.locator('[data-filter="기업·투자"]').evaluate('(e)=>e.click()')
  print('category result',await page.locator('.article-tile').count(),flush=True)
  await page.locator('[data-filter="all"]').evaluate('(e)=>e.click()')
  await page.locator('#articleSearch').evaluate('(e)=>{e.value="글로벌";e.dispatchEvent(new Event("input",{bubbles:true}))}')
  print('keyword result',await page.locator('.article-tile').count(),flush=True)
  await page.locator('#articleSearch').evaluate('(e)=>{e.value="";e.dispatchEvent(new Event("input",{bubbles:true}))}')
  await page.locator('.article-tile').first.evaluate('(e)=>e.click()')
  print('modal',await page.locator('.modal-layer.show').count(),flush=True)
  await page.evaluate('document.dispatchEvent(new KeyboardEvent("keydown",{key:"Escape",bubbles:true}))');print('closed',await page.locator('.modal-layer.show').count(),flush=True)
  await page.locator('#subscriberEmail').evaluate('(e)=>{e.value="user@example.com";e.dispatchEvent(new Event("input",{bubbles:true}))}')
  await page.locator('#privacyConsent').evaluate('(e)=>{e.checked=true;e.dispatchEvent(new Event("change",{bubbles:true}))}')
  await page.locator('#subscribeForm button[type=submit]').evaluate('(e)=>e.click()')
  print('submit demo',await page.locator('#formResult').inner_text(),flush=True)
  print('page errors',errors,flush=True)
  await browser.close()
asyncio.run(main())
