from pathlib import Path
from bs4 import BeautifulSoup
import re,json
from playwright.sync_api import sync_playwright
ROOT=Path('/mnt/data/LAWYGO_PAN_2026_EXPANSION');SITE=ROOT/'site'
htmlfiles=sorted(SITE.glob('*.html'));broken=[];images=[];h1=[]
for f in htmlfiles:
 s=BeautifulSoup(f.read_text(),'html.parser')
 for el in s.select('[href],[src]'):
  v=el.get('href') or el.get('src')
  if not v or v.startswith(('http://','https://','mailto:','tel:','#','data:','javascript:','{{')):continue
  if v.startswith('/api/') or v.startswith('/unsubscribe') or v.startswith('/verify'):continue
  v=v.split('?')[0].split('#')[0]
  if not v:continue
  target=(f.parent/v).resolve()
  if not target.exists():broken.append(f'{f.name} -> {v}')
  if el.name=='img':images.append(str(target))
 h=s.select('main h1');
 if len(h)!=1:h1.append((f.name,len(h)))
print('htmlfiles',len(htmlfiles),'broken',len(broken),'h1 issue',h1[:10])
print('broken examples',broken[:35])
qa={'html_pages':len(htmlfiles),'broken_paths':broken,'h1_issues':h1,'images_count':len(images),'screenshots':[],'browser_errors':[]}
with sync_playwright() as p:
 b=p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox'])
 for slug in ['index','content-feed','shorts-feed','blogger-feed','free-signup','blogger-connect','advertising','ad-ranking','newsletter-optin','marketing-email-preview']:
  for typ,viewport in [('desktop',{'width':1365,'height':900}),('mobile',{'width':390,'height':844})]:
   pg=b.new_page(viewport=viewport,device_scale_factor=1)
   errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
   pg.goto('http://127.0.0.1:8766/'+slug+'.html',wait_until='load',timeout=20000)
   pg.wait_for_timeout(180)
   if slug in ['index','content-feed','free-signup','advertising','shorts-feed']:
    out=SITE/'previews'/f'NEW_{slug}-{typ}.png';pg.screenshot(path=str(out),full_page=False)
    qa['screenshots'].append(str(out.name))
   width=pg.evaluate('document.documentElement.scrollWidth'); v=viewport['width'];
   if width>v+2:errs.append(f'horizontal overflow {width} > {v}')
   if errs:qa['browser_errors'].append({'page':slug,'type':typ,'errors':errs[:6]})
   if slug=='index' and typ=='desktop':
    pg.locator('.lang').first.click();pg.wait_for_timeout(100);qa['english_toggle_text']=pg.locator('.nav').first.inner_text()[:160]
   pg.close()
 b.close()
(ROOT/'QA_REPORT.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2))
print('browser errors',qa['browser_errors'][:20],'preview count',len(qa['screenshots']))
