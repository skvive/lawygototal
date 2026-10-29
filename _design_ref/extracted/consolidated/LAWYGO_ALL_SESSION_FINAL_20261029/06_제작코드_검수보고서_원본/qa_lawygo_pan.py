from pathlib import Path
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import json,base64,mimetypes,re
root=Path('/mnt/data/LAWYGO_PAN_DELIVERY');screens=root/'previews';screens.mkdir(exist_ok=True)
issues=[];stats=[]
for p in sorted(root.glob('*.html')):
 soup=BeautifulSoup(p.read_text(encoding='utf-8'),'html.parser')
 for ele in soup.find_all(['img','script','link','a']):
  attr='src' if ele.name in ('img','script') else 'href'
  v=ele.get(attr,'').split('#')[0].split('?')[0]
  if not v or v.startswith(('http:','https:','mailto:','tel:','data:','#','javascript:')):continue
  if not (root/v).is_file():issues.append(f'{p.name}: missing {v}')
 for x in ['title','h1']:
  if not soup.find(x):issues.append(f'{p.name}: missing {x}')

def inline_file(file):
 soup=BeautifulSoup(file.read_text(encoding='utf-8'),'html.parser')
 for elem in soup.find_all('link',href=True):
  if 'stylesheet' not in elem.get('rel',[]):continue
  path=(file.parent/elem['href']).resolve()
  if path.exists():
   tag=soup.new_tag('style');tag.string=re.sub(r'@import[^;]+;','',path.read_text(encoding='utf-8'));elem.replace_with(tag)
 for elem in soup.find_all('script',src=True):
  path=(file.parent/elem['src']).resolve()
  if path.exists():
   elem.attrs.pop('src',None);elem.attrs.pop('defer',None);elem.string=path.read_text(encoding='utf-8')
  else:elem.decompose()
 for elem in soup.find_all('img',src=True):
  path=(file.parent/elem['src']).resolve()
  if path.exists():
   t=mimetypes.guess_type(path.name)[0] or 'image/png'
   elem['src']='data:'+t+';base64,'+base64.b64encode(path.read_bytes()).decode()
 return str(soup)

storage='''Object.defineProperty(window,'localStorage',{configurable:true,value:(()=>{const o={};return{getItem:k=>o[k]??null,setItem:(k,v)=>o[k]=String(v),removeItem:k=>delete o[k],clear:()=>Object.keys(o).forEach(k=>delete o[k])}})()})'''
with sync_playwright() as pw:
 browser=pw.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage','--disable-gpu'])
 for viewport,label in [({'width':1440,'height':900},'desktop'),({'width':390,'height':844},'mobile')]:
  ctx=browser.new_context(viewport=viewport,device_scale_factor=1)
  page=ctx.new_page();page.add_init_script(storage)
  for p in sorted(root.glob('*.html')):
   errors=[]
   try:
    # set_content follows previously tested PDF-style screenshot rendering workflow; browser network is intentionally disabled.
    page.set_content(inline_file(p),wait_until='domcontentloaded',timeout=7000)
    page.wait_for_timeout(90)
    details=page.evaluate('''() => ({width:document.documentElement.scrollWidth,inner:innerWidth,body:document.body.scrollHeight,images:[...document.images].filter(x=>x.loading!=='lazy' && (!x.complete || x.naturalWidth===0)).map(x=>x.src.slice(0,50))})''')
    if details['width']>viewport['width']+4:issues.append(f'{label}:{p.name}: horizontal overflow {details["width"]} > {viewport["width"]}')
    if details['images']:issues.append(f'{label}:{p.name}: {len(details["images"])} unloaded images')
    page.screenshot(path=str(screens/f'{p.stem}-{label}.png'),full_page=False,timeout=16000)
    stats.append((p.name,label,details['body']))
   except Exception as e:issues.append(f'{label}:{p.name}: {str(e)[:170]}')
  ctx.close()
 p=browser.new_page(viewport={'width':1400,'height':900});p.add_init_script(storage)
 p.set_content(inline_file(root/'lawyers.html'),wait_until='domcontentloaded');p.fill('#lawyerQuery','기업');val=p.locator('#lawyerCount').inner_text();print('filter',val)
 if '1개' not in val:issues.append('Filter expected 1, got '+val)
 p.set_content(inline_file(root/'index.html'),wait_until='domcontentloaded');p.click('[data-lang="en"]');v=p.locator('.home-copy h1').inner_text();print('EN',v[:120]);
 if 'Find' not in v:issues.append('EN toggle failed')
 p.set_content(inline_file(root/'blog-builder.html'),wait_until='domcontentloaded');p.fill('[name="blog"]','https://example.blogspot.com');p.fill('[name="youtube"]','https://www.youtube.com/watch?v=dQw4w9WgXcQ');p.click('#builderForm button[type=submit]');
 if not p.locator('#youtubeEmbed iframe').count():issues.append('YouTube preview embed missing')
 p.set_content(inline_file(root/'index.html'),wait_until='domcontentloaded');p.set_viewport_size({'width':390,'height':844});p.click('#menuButton')
 if not p.locator('#mainNav').evaluate('(e)=>e.classList.contains("open")'):issues.append('mobile menu failed')
 browser.close()
report={'pages':len(list(root.glob('*.html'))),'screenshots':len(list(screens.glob('*.png'))),'total_checks':len(stats),'issues':issues,'stats':stats}
(root/'QA_RESULTS.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print('REPORT',report['pages'],report['screenshots'],'issues',len(issues));print('\n'.join(issues[:35]))
