import asyncio,json
from pathlib import Path
from playwright.async_api import async_playwright
BASE=Path('/mnt/data/LAWYGO_V3_BUILD/OFFLINE_QA')
OUT=Path('/mnt/data/LAWYGO_V3_BUILD/screenshots');OUT.mkdir(exist_ok=True)
MOCK="""(() => {
const b=[{id:'board-pan-one',name:'법률 블로그',slug:'blogs',product:'pan',description:'검수된 글'},{id:'board-pan-two',name:'영상·쇼츠',slug:'shorts',product:'pan',description:'법률 동영상'},{id:'board-channel',name:'경제 정책 저널',slug:'news',product:'channel',description:'정책'}];
const p=[{id:'11111111111111111111111111111111',title:'임대차 계약서 검토에서 자주 놓치는 사항',summary:'계약 및 법령을 검토하기 위한 공개 정보입니다.',status:'published',kind:'blog',product:'pan',board_id:'board-pan-one',is_sponsored:true,updated_at:'2026-10-29T00:00:00Z',version:1}];
const replies={'/api/me':{id:'admin',role:'admin',display_name:'검수 관리자'},'/api/boards':{items:b},'/api/dashboard/stats':{posts:[{product:'pan',status:'published',count:1}],boards:[]},'/api/posts':{items:p,total:1},'/api/growth/campaigns':{items:[{id:'cccccccccccccccccccccccccccccccc',product:'pan',name:'법률 칼럼 캠페인',title:p[0].title,status:'active',priority:1}]},'/api/growth/analytics':{events:[{event_type:'content_open',product:'pan',count:12},{event_type:'consult_click',product:'pan',count:3}]},'/api/growth/system':{database:'connected',google_oauth:false,gemini:false,native_bridge:false,billing_webhook:false},'/api/pan/verification':{items:[]},'/api/growth/entitlements':{items:[]}};
const orig=window.fetch;
window.fetch=async (url,opts) => {const key=String(url).split('?')[0];if(key in replies)return new Response(JSON.stringify(replies[key]),{status:200,headers:{'Content-Type':'application/json'}});if(key==='/api/growth/feed')return new Response(JSON.stringify({items:p.map(x=>({...x,placement:'광고'}))}),{status:200});if(String(url).startsWith('/api/'))return new Response(JSON.stringify({ok:true,items:[]}),{status:200});return orig(url,opts)};
})();"""
async def main():
 import base64,re
 css=(BASE/'style.css').read_text()
 css=re.sub(r"@import url\([^;]+;",'',css)
 def inline(path,product=None):
  html=(BASE/path).read_text()
  html=re.sub(r'<link rel="stylesheet"[^>]*>',lambda m:'<style>'+css+'</style>',html)
  html=re.sub(r'<link rel="icon"[^>]*>','',html)
  for ext in ['channel','wiki','pan','note']:
   dat=base64.b64encode((BASE/'img'/f'{ext}.webp').read_bytes()).decode()
   html=html.replace('/static/img/'+ext+'.webp','data:image/webp;base64,'+dat).replace('./img/'+ext+'.webp','data:image/webp;base64,'+dat)
  html=html.replace('/static/logo.svg','data:image/svg+xml;base64,'+base64.b64encode((BASE/'logo.svg').read_bytes()).decode()).replace('./logo.svg','data:image/svg+xml;base64,'+base64.b64encode((BASE/'logo.svg').read_bytes()).decode())
  html=re.sub(r'<script[^>]+src="[^"]+"[^>]*></script>','',html)
  return html
 rows=[]
 async with async_playwright() as p:
  browser=await p.chromium.launch(executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'],headless=True)
  for viewport in [(1440,900),(390,844)]:
   tag='mobile' if viewport[0]<500 else 'desktop'
   ctx=await browser.new_context(viewport={'width':viewport[0],'height':viewport[1]})
   for slug in ['home','channel','wiki','pan','note']:
    page=await ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
    await page.set_content(inline('index.html' if slug=='home' else 'product.html'))
    await page.evaluate(MOCK)
    js=(BASE/('marketing.js' if slug=='home' else 'product.js')).read_text()
    if slug!='home':js=js.replace("const product=location.pathname.split('/').pop();",f"const product='{slug}';")
    await page.add_script_tag(content=js)
    await page.wait_for_timeout(100)
    await page.screenshot(path=str(OUT/f'{slug}-{tag}.png'),full_page=slug=='home')
    width=await page.evaluate('({scroll:document.documentElement.scrollWidth,width:innerWidth})')
    rows.append({'page':slug,'viewport':tag,'overflow':width['scroll']>width['width']+2,'js_errors':errors.copy()});await page.close()
   page=await ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
   await page.set_content(inline('dashboard.html'))
   await page.evaluate(MOCK)
   await page.add_script_tag(content=(BASE/'dashboard.js').read_text())
   await page.add_script_tag(content=(BASE/'growth.js').read_text())
   await page.locator('#adminApp').wait_for(state='visible',timeout=5000)
   if tag=='mobile':await page.locator('.sidebar-toggle').click()
   await page.locator('[data-action="growth"]').click()
   await page.wait_for_timeout(300)
   await page.screenshot(path=str(OUT/f'growth-{tag}.png'),full_page=True)
   width=await page.evaluate('({scroll:document.documentElement.scrollWidth,width:innerWidth})')
   rows.append({'page':'growth','viewport':tag,'overflow':width['scroll']>width['width']+2,'js_errors':errors.copy()})
   cards=page.locator('#boardOrderCards .sort-card')
   if await cards.count()>1:
    before=await cards.first.get_attribute('data-id');await cards.first.drag_to(cards.nth(1))
    rows.append({'test':'drag-and-drop-board','viewport':tag,'changed':before!=await cards.first.get_attribute('data-id')})
   await ctx.close()
  await browser.close()
 (OUT/'browser_results.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
 print(json.dumps(rows,ensure_ascii=False,indent=2))
asyncio.run(main())
