from pathlib import Path
import asyncio,zipfile, json,base64,re
from playwright.async_api import async_playwright
root=Path('/mnt/data/LAWYGO_WSJ_EDITORIAL_SITE'); pv=root/'previews_wsj';pv.mkdir(exist_ok=True)
cache={}
def content(file):
 s=file.read_text(encoding='utf8')
 for f in ['journal-editorial.css','journal-editorial.js']:
  raw=(root/'assets'/f).read_text(encoding='utf8')
  if f.endswith('css'): s=s.replace('<link rel="stylesheet" href="../assets/'+f+'">','<style>'+raw+'</style>')
  else: s=s.replace('<script defer src="../assets/'+f+'"></script>','').replace('</body>','<script>'+raw+'</script></body>')
 def rep(m):
  path=(file.parent/m.group(2)).resolve()
  if path not in cache:cache[path]='data:image/jpeg;base64,'+base64.b64encode(path.read_bytes()).decode() if path.exists() else ''
  return m.group(1)+cache[path]+m.group(3)
 return re.sub(r'(<img\b[^>]*\bsrc=")([^"]+)(")',rep,s)
async def run():
 async with async_playwright() as p:
  b=await p.chromium.launch(headless=True,executable_path='/usr/bin/chromium',args=['--no-sandbox','--disable-dev-shm-usage'])
  pc=await b.new_page(viewport={'width':1440,'height':950},device_scale_factor=1)
  mobile=await b.new_page(viewport={'width':390,'height':844},device_scale_factor=1,is_mobile=True,has_touch=True)
  failures=[]
  for file in sorted((root/'journal').glob('*.html')):
   name=file.stem; markup=content(file)
   try:
    await pc.set_content(markup,wait_until='load',timeout=25000)
    await pc.screenshot(path=str(pv/f'JOURNAL--{name}--DESKTOP.png'),full_page=False,timeout=25000)
    if name in ['index','us-markets','newsletter']:
     await pc.screenshot(path=str(pv/f'JOURNAL--{name}--FULL.png'),full_page=True,timeout=25000)
    await mobile.set_content(markup,wait_until='load',timeout=25000)
    await mobile.screenshot(path=str(pv/f'JOURNAL--{name}--MOBILE.png'),full_page=False,timeout=25000)
    sizes=await mobile.evaluate('({width:document.documentElement.scrollWidth,inner:innerWidth})')
    print(name,sizes,flush=True)
    if sizes['width']>sizes['inner']+3:failures.append((name,'horizontal overflow',sizes))
   except Exception as e:failures.append((name,str(e)[:200]))
  await b.close()
  (root/'WSJ_QA.json').write_text(json.dumps({'desktop_mobile_previews':len(list(pv.glob('*.png'))),'failures':failures},ensure_ascii=False,indent=2),encoding='utf8')
asyncio.run(run())
out=Path('/mnt/data/LAWYGO_JOURNAL_WSJ_REDESIGN_WITH_PAYMENT.zip')
with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
 for f in root.rglob('*'):
  if f.is_file():z.write(f,'LAWYGO_WSJ_SITE/'+str(f.relative_to(root)))
print('OUTPUT',out,'BYTES',out.stat().st_size)
