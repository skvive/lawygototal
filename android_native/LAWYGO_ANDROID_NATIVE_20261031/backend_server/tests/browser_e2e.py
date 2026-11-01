"""Browser smoke tests; expects the local development server and temporary QA login."""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright
OUT=Path(__file__).resolve().parents[2]/'screenshots';OUT.mkdir(exist_ok=True)
BASE='http://127.0.0.1:8018'
async def run():
 async with async_playwright() as p:
  browser=await p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
  page=await browser.new_page(viewport={'width':1440,'height':900},device_scale_factor=1)
  errors=[]
  page.on('pageerror',lambda e:errors.append(str(e)))
  await page.goto(BASE+'/',wait_until='networkidle')
  await page.screenshot(path=str(OUT/'01-home-desktop.png'),full_page=True)
  await page.goto(BASE+'/dashboard',wait_until='networkidle')
  await page.locator('#email').fill('qa-demo@example.com')
  await page.locator('#password').fill('ExampleQAOnly_StrongPass_7491')
  await page.locator('#loginForm button').click()
  await page.locator('#adminApp:not(.hidden)').wait_for()
  assert await page.locator('#kpiBoards').inner_text()=='13'
  await page.screenshot(path=str(OUT/'02-dashboard-desktop.png'),full_page=True)
  await page.locator('#newPostBtn').click()
  await page.locator('#postTitle').fill('로이고 채널 - 실제 동작 검증용 기사')
  await page.locator('#postSummary').fill('게시글 생성부터 승인까지 E2E 점검')
  await page.locator('#postBody').fill('채널에 기사를 등록합니다. 화면에서 안전하게 출력되는지 확인합니다.')
  await page.locator('#postStatus').select_option('published')
  await page.locator('#postForm button[type=submit]').click()
  await page.locator('#postModal:not(.open)').wait_for()
  await page.locator('td strong',has_text='로이고 채널 - 실제 동작 검증용 기사').wait_for()
  await page.screenshot(path=str(OUT/'03-dashboard-with-post.png'),full_page=True)
  await page.goto(BASE+'/p/channel',wait_until='networkidle')
  await page.get_by_text('로이고 채널 - 실제 동작 검증용 기사',exact=True).wait_for()
  await page.screenshot(path=str(OUT/'04-channel-desktop.png'),full_page=True)
  await page.get_by_role('button',name='자세히 보기 →').first.click()
  await page.locator('#reader.open').wait_for()
  await page.screenshot(path=str(OUT/'05-channel-post-detail.png'),full_page=False)
  mobile=await browser.new_page(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True)
  mobile.on('pageerror',lambda e:errors.append(str(e)))
  await mobile.goto(BASE+'/',wait_until='networkidle')
  horizontal=await mobile.evaluate('document.documentElement.scrollWidth > window.innerWidth + 2')
  assert not horizontal,'Mobile horizontal overflow'
  await mobile.screenshot(path=str(OUT/'06-home-mobile.png'),full_page=True)
  await mobile.goto(BASE+'/p/channel',wait_until='networkidle')
  assert not await mobile.evaluate('document.documentElement.scrollWidth > window.innerWidth + 2')
  await mobile.screenshot(path=str(OUT/'07-channel-mobile.png'),full_page=True)
  await browser.close()
  assert not errors,'Javascript errors: '+str(errors)
  print('BROWSER E2E PASS: homepage, login, dashboard, create+publish, public display, detail modal, mobile layouts, no console page errors')
asyncio.run(run())
