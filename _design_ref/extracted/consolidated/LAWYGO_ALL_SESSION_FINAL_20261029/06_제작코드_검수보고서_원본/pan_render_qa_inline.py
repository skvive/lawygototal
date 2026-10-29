from playwright.sync_api import sync_playwright
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageFont
import re,base64,mimetypes,json
root=Path('/mnt/data/LAWYGO_PAN_CUSTOMER_SITE');assets=root/'assets';pages=sorted(root.glob('*.html'))
css='\n'.join((assets/'site.css').read_text().splitlines()[1:])
data_hero='data:image/webp;base64,'+base64.b64encode((assets/'hero-attorney.webp').read_bytes()).decode()
css=css.replace("url('./hero-attorney.webp')","url('"+data_hero+"')")
js=(assets/'site.js').read_text()
def inline(path):
 t=path.read_text()
 t=t.replace('<link rel="stylesheet" href="assets/site.css">','<style>'+css+'</style>')
 t=t.replace('<script defer src="assets/integrations.js"></script>','').replace('<script defer src="assets/site.js"></script>','')
 def replace(m):
  p=assets/m.group(1)
  if not p.exists():return m.group(0)
  typ='image/'+('svg+xml' if p.suffix=='.svg' else 'webp' if p.suffix=='.webp' else 'jpeg' if p.suffix=='.jpg' else 'png')
  return 'src="data:'+typ+';base64,'+base64.b64encode(p.read_bytes()).decode()+'"'
 t=re.sub('src="assets/([\w\-\.]+)"',replace,t)
 return t
results=[]
with sync_playwright() as pw:
 browser=pw.chromium.launch(executable_path='/usr/bin/chromium',headless=True,args=['--no-sandbox','--disable-dev-shm-usage'])
 for width,mobile in [(1365,False),(390,True)]:
  ctx=browser.new_context(viewport={'width':width,'height':850 if not mobile else 844},device_scale_factor=1,locale='ko-KR')
  page=ctx.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
  for p in pages:
   try:
    page.set_content(inline(p),wait_until='domcontentloaded',timeout=20000)
    page.add_script_tag(content=js)
    page.evaluate("Array.from(document.images).forEach(i => i.loading='eager')")
    page.wait_for_timeout(150)
    dest=root/'previews'/(p.stem+('-mobile' if mobile else '-desktop')+'.png')
    page.screenshot(path=str(dest),timeout=10000)
    overflow=page.evaluate('document.documentElement.scrollWidth > window.innerWidth + 3')
    broken=page.evaluate('Array.from(document.images).filter(i=>!i.complete||i.naturalWidth===0).length')
    results.append({'page':p.name,'mode':'mobile' if mobile else 'desktop','overflow':overflow,'broken':broken,'errors':errors[:]})
    errors.clear()
   except Exception as e:results.append({'page':p.name,'mode':'mobile' if mobile else 'desktop','error':str(e)[:240]})
  ctx.close()
 browser.close()
(root/'docs'/'RENDER_QA.json').write_text(json.dumps(results,ensure_ascii=False,indent=2))
print('total',len(pages),'preview',len(list((root/'previews').glob('*.png'))),'errors',sum(bool(x.get('error')) for x in results),'overflows',sum(bool(x.get('overflow')) for x in results),'broken',sum(x.get('broken',0) for x in results),'js errors',sum(len(x.get('errors',[])) for x in results))
print('nonclean',*[x for x in results if x.get('error') or x.get('overflow') or x.get('broken') or x.get('errors')][:10],sep='\n')
