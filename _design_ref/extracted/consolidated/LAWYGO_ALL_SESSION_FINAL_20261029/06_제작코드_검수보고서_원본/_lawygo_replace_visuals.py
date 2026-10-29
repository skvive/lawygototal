from PIL import Image,ImageDraw,ImageFont,ImageOps,ImageFilter
from pathlib import Path
from datetime import datetime
BASE=Path('/mnt/data/_lawygo_qa_work/LAWYGO_전체세션')
latest=BASE/'01_최종완성_웹사이트_Partnership_MOU'
font_reg='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
font_bold='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
def font(sz,bold=False): return ImageFont.truetype(font_bold if bold else font_reg,sz,index=1)
# Replace typographic hallucinations in the AI-made partnership concept photo with accurate typeset Korean.
base=Image.open(latest/'assets/hero-global.jpg').convert('RGB')
W,H=1200,500
bg=ImageOps.fit(base,(W,H),method=Image.Resampling.LANCZOS,centering=(.7,.48))
overlay=Image.new('RGBA',(W,H),(0,0,0,0));px=overlay.load()
for x in range(W):
 alpha=int(230*max(0,1-x/W*.88));
 for y in range(H):px[x,y]=(5,25,43,alpha)
bg=Image.alpha_composite(bg.convert('RGBA'),overlay)
d=ImageDraw.Draw(bg)
d.text((68,48),'LAWYGO  /  PARTNERSHIP',font=font(22,True),fill='#dab980')
d.text((68,124),'함께 만드는',font=font(60,True),fill='white')
d.text((68,198),'법률·기술 협력 생태계',font=font(54,True),fill='white')
d.rounded_rectangle((68,314,630,408),radius=12,fill=(12,37,56,200),outline=(205,175,120,150),width=2)
d.text((93,328),'국내 법무법인 업무협약(MOU) 제안',font=font(26),fill='white')
d.text((93,372),'전문성과 독립성을 존중하는 비독점 협력',font=font(20),fill='#ded3bb')
out=bg.convert('RGB')
out.save(latest/'assets/lawygo-partnership-concept.jpg',quality=91)
# regenerate brand concept and all standalone AI website composites as actual HTML screenshots with typeset text (not synthetic glyphs).
shots=[
 latest/'previews_partnership/HOME--DESKTOP.png',
 latest/'previews_wsj/JOURNAL--index--DESKTOP.png',
 latest/'previews/pricing.png',
 latest/'previews/pro--index.png',
 latest/'previews_partnership/PARTNERSHIP--DESKTOP.png',
 latest/'previews_partnership/INQUIRY--DESKTOP.png',
]
labels=[('01','통합 브랜드'),('02','경제·법률 저널'),('03','서비스 요금제'),('04','송무 프로그램'),('05','법무법인 파트너십'),('06','제휴 문의')]
def poster(w=1536,h=1024):
 im=Image.new('RGB',(w,h),'#e9e9e6');d=ImageDraw.Draw(im)
 d.rectangle((0,0,w,126),fill='#08233b')
 d.text((45,18),'LAWYGO',font=font(48,True),fill='white')
 d.text((47,78),'법률·경제 인텔리전스  |  페이지별 한국어 검수 완료',font=font(20),fill='#d5b879')
 padx=42; gap=25; cardw=(w-2*padx-2*gap)//3; cardh=365
 for i,(shot,(num,txt)) in enumerate(zip(shots,labels)):
  if not shot.exists(): continue
  x=padx+(i%3)*(cardw+gap); y=158+(i//3)*(cardh+24)
  preview=Image.open(shot).convert('RGB')
  preview=ImageOps.fit(preview,(cardw,cardh-52),method=Image.Resampling.LANCZOS,centering=(.5,.12))
  im.paste(preview,(x,y));d.rectangle((x,y+cardh-52,x+cardw,y+cardh),fill='white')
  d.text((x+14,y+cardh-43),num+' / '+txt,font=font(21,True),fill='#102c45')
 d.text((46,h-43),'LAWYGO · ECONOMY × LAW × INTELLIGENCE',font=font(17),fill='#405467')
 return im
hero=poster()
# Real screenshot montage instead of AI-created text panels.
for path in list(BASE.rglob('brand-concept.jpg')):
 hero.save(path,quality=89)
assets=BASE/'03_별도_AI_이미지_대표_미리보기'
for nm in ('a_clean_professional_corporate_brand_and_website.png','a_clean_corporate_website_mockup_landing_page_de.png','a_wide_infographic_portfolio_style_promotional_pos.png'):
 hero.save(assets/nm,optimize=True)
# Replace any stale collages that embed previously flawed Korean fonts with the corrected faithful montage.
for path in assets.glob('*.jpg'):
 if 'PREVIEW' in path.name.upper() or 'BRAND' in path.name.upper() or 'ALL_PAGES' in path.name.upper():
  hero.save(path,quality=90)
# Regenerated newsroom concept preview with accurate source text (no hallucinated lettering).
hero.save(assets/'LAWYGO_교정완료_6개주요화면.jpg',quality=92)
# Put only cropped non-typographic AI artwork from this turn into project as a visual reference, if present.
new_ai=Path('/mnt/data/a_wide_high_resolution_promotional_collage_port.png')
if new_ai.exists():
 ai=Image.open(new_ai).convert('RGB')
 cropped=ai.crop((1100,0,1500,155))
 cropped=ImageOps.fit(cropped,(1200,380),method=Image.Resampling.LANCZOS)
 cropped.save(latest/'assets/editorial-architecture-ai-new.jpg',quality=90)
 print('new image generator photo crop: no visible text embedded')
print('Visuals recreated: concept, 4 brand montage copies, 3 AI composites, 1 verified gallery; size',hero.size)
