from PIL import Image,ImageDraw,ImageFont,ImageFilter
from pathlib import Path
R=Path('/mnt/data/LAWYGO_PAN_CUSTOMER_SITE/assets');F='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc';B='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
font=lambda sz,b=False:ImageFont.truetype(B if b else F,sz,index=1)
photo=Image.open(R/'hero-attorney.webp').convert('RGB')
bg=Image.new('RGB',(1200,630),'#0c243b')
# right photo crop to 470x630, focussing on human subject
p=photo.crop((255,0,810,459));p=p.resize((520,630),Image.Resampling.LANCZOS)
bg.paste(p,(680,0))
layer=Image.new('RGBA',(1200,630),(0,0,0,0));d=ImageDraw.Draw(layer)
for x in range(570,870):
 a=int(255*(1-(x-570)/300)**1.3)
 d.line((x,0,x,629),fill=(10,31,50,a))
bg=Image.alpha_composite(bg.convert('RGBA'),layer)
d=ImageDraw.Draw(bg)
d.rounded_rectangle((62,64,136,138),radius=15,fill='#f7f5ef')
d.polygon([(79,78),(96,78),(96,113),(121,113),(121,129),(79,129)],fill='#102a43')
d.rounded_rectangle((103,91,119,107),radius=2,fill='#c83f56')
d.text((160,69),'LAWYGO',font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf',42),fill='white')
d.text((413,78),'PAN',font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',36),fill='#ec7389')
d.line((65,201,580,201),fill='#d3ab73',width=3)
d.text((64,232),'좋은 변호사를,',font=font(55,True),fill='#ffffff')
d.text((64,308),'더 가까이.',font=font(58,True),fill='#ddbb88')
d.text((65,419),'법률 콘텐츠 · 전문가 프로필',font=font(25),fill='#e5edf3')
d.text((65,463),'구글 블로그 · 유튜브 · 상담 연결',font=font(25),fill='#dbe5ee')
d.text((65,545),'pan.lawygo.com',font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',25),fill='#c8d4df')
bg.convert('RGB').save(R/'og-image.jpg',quality=93,subsampling=0)
print('OG recreated', (R/'og-image.jpg').stat().st_size)
