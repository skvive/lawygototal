from pathlib import Path
from bs4 import BeautifulSoup
from PIL import Image,ImageOps,ImageDraw,ImageFont
import json,collections,re,os
ROOT=Path('/mnt/data/LAWYGO_PAN_CUSTOMER_SITE');pages=sorted(ROOT.glob('*.html'));faults=[];links=0;imgs=0;tokens=[]
for p in pages:
 s=p.read_text();so=BeautifulSoup(s,'html.parser')
 h1=so.find_all('h1')
 if len(h1)!=1: faults.append(f'{p.name}: h1 count {len(h1)}')
 for t in ['title','meta','html','link']:
  if not so.find(t):faults.append(f'{p.name}: {t} missing')
 for a in so.select('a[href]'):
  href=a.get('href','').split('#')[0].split('?')[0]
  if href.endswith('.html'):
   links+=1
   if not (ROOT/href).is_file():faults.append(f'{p.name} broken href: {href}')
 for im in so.select('img[src]'):
  src=im['src'];imgs+=1
  if src.startswith('assets/') and not (ROOT/src).exists():faults.append(f'{p.name} broken image: {src}')
  if not im.get('alt'):faults.append(f'{p.name} missing image alt')
 for sc in so.select('script[src],link[rel=stylesheet]'):
  src=sc.get('src') or sc.get('href')
  if src and src.startswith('assets/') and not (ROOT/src).exists():faults.append(f'{p.name} broken script/css: {src}')
 txt=so.get_text(' ',strip=True)
 if '\ufffd' in txt: faults.append(f'{p.name}: replacement char U+FFFD')
 if '상담 문의 페이지에서 접수 완료' in txt:faults.append(f'{p.name}: misleading confirmation')
 tokens.append(len(re.findall(r'[가-힣]+',txt)))
for p in (ROOT/'assets').glob('*'):
 if p.suffix.lower() in ('.webp','.jpg','.png','.ico'):
  try:
   with Image.open(p) as im:im.verify()
  except Exception as e: faults.append(f'corrupted image {p.name}: {str(e)[:100]}')
if Image.open(ROOT/'assets'/'og-image.jpg').size != (1200,630):faults.append('OG size invalid')
# Basic auth/prototype disclosures
for p in ['lawyers.html','lawyer-kim.html','lawyer-lee.html','lawyer-park.html','lawyer-jung.html']:
 if '시연용' not in (ROOT/p).read_text():faults.append(f'{p}: no demo disclaimer')
report={'pages':len(pages),'internal_html_links':links,'image_usages':imgs,'korean_wordlike_tokens':sum(tokens),'assets':len(list((ROOT/'assets').iterdir())),'desktop_preview_count':len(list((ROOT/'previews').glob('*-desktop.png'))),'mobile_preview_count':len(list((ROOT/'previews').glob('*-mobile.png'))),'faults':faults}
(ROOT/'docs'/'STATIC_AUDIT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(report)
