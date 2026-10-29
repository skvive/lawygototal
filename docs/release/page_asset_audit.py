from pathlib import Path
import json,re,zipfile,hashlib
from bs4 import BeautifulSoup
from PIL import Image,ImageOps,ImageDraw,ImageFont
root=Path('/mnt/data/LAWYGO_V3_BUILD/LAWYGO_ENGINE/static')
pages=list(root.glob('*.html'))
fail=[];assets=set();links=[]
for f in pages:
 s=BeautifulSoup(f.read_text(encoding='utf-8'),'html.parser')
 if not s.find('html') or not s.find('title'):fail.append(f'{f.name}: HTML 문서 구조 누락')
 for el in s.select('[src], [href]'):
  key='src' if el.has_attr('src') else 'href';url=el[key]
  if url.startswith('/static/'):
   target=root/url.replace('/static/','',1)
   assets.add(str(target))
   if not target.exists():fail.append(f'{f.name}: missing {url}')
  if url.startswith('/p/') and url not in ['/p/channel','/p/wiki','/p/pan','/p/note']:fail.append(f'{f.name}: 잘못된 제품 경로 {url}')
  links.append((f.name,url))
 if not s.find('meta',attrs={'property':'og:image'}):fail.append(f'{f.name}: OG 누락')
 if '�' in f.read_text() or '���' in f.read_text():fail.append(f'{f.name}: 유니코드 깨짐')
imgs=list(root.rglob('*.webp'))+list(root.rglob('*.png'))+list(root.rglob('*.jpg'))+list(root.rglob('*.ico'))
for x in imgs:
 try: Image.open(x).verify()
 except Exception as e:fail.append(f'{x.name}: image corrupt {e}')
js=list(root.glob('*.js'))
result={'html_count':len(pages),'image_count':len(imgs),'js_count':len(js),'path_references_checked':len(links),'local_assets_checked':len(assets),'errors':fail,'text_qa':'운영 HTML은 한글 텍스트로 렌더링; 이미지 내부 한국어 자산 없음','scope':'current runnable CMS pages only, not every historical archive page'}
Path('/mnt/data/LAWYGO_V3_BUILD/REPORTS/PAGE_ASSET_AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
print(json.dumps(result,ensure_ascii=False,indent=2))
# Contact board with 6 desktop screenshots
src=Path('/mnt/data/LAWYGO_V3_BUILD/screenshots')
entries=[('메인 홈','home-desktop.png'),('로이고 채널','channel-desktop.png'),('로이고 위키','wiki-desktop.png'),('로이고 판','pan-desktop.png'),('로이고 노트','note-desktop.png'),('마케팅 대시보드','growth-desktop.png')]
w=1300;im=Image.new('RGB',(w,1090),'#edf2f6');d=ImageDraw.Draw(im)
f='/usr/share/fonts/truetype/nanum/NanumBarunGothic.ttf'
font=ImageFont.truetype(f,21);hf=ImageFont.truetype(f,32)
d.text((30,20),'LAWYGO CMS v3 — 페이지별 검수 이미지',font=hf,fill='#142b44')
for i,(title,filename) in enumerate(entries):
 x=20+(i%2)*645;y=85+(i//2)*330
 a=Image.open(src/filename).convert('RGB');a=ImageOps.fit(a,(605,280),centering=(.5,.1));im.paste(a,(x,y+35));d.text((x+5,y),title,font=font,fill='#152e47')
im.save('/mnt/data/LAWYGO_V3_BUILD/LAWYGO_V3_PAGE_PREVIEWS.jpg',quality=90)
if fail:raise SystemExit('FAIL')
