from pathlib import Path
from PIL import Image,ImageOps
BASE=Path('/mnt/data/_lawygo_qa_work/LAWYGO_전체세션')
latest=BASE/'01_최종완성_웹사이트_Partnership_MOU'
other=BASE/'03_별도_AI_이미지_대표_미리보기'
def save_as(source,name):
 if not source.exists(): return False
 dest=other/name;im=Image.open(source).convert('RGB')
 if dest.exists():
  old=Image.open(dest)
  if old.width>0 and old.height>0:
   im.thumbnail((max(400,old.width),max(320,old.height)),Image.Resampling.LANCZOS)
 im.save(dest,format='JPEG' if dest.suffix.lower() in ('.jpg','.jpeg') else 'PNG',quality=90)
 return True
matches={
'LAWYGO_JOURNAL_desktop_preview.png':latest/'previews_wsj/JOURNAL--index--DESKTOP.png',
'LAWYGO_JOURNAL_mobile_preview.png':latest/'previews_wsj/JOURNAL--index--MOBILE.png',
'LAWYGO_JOURNAL_mobile_small.png':latest/'previews_wsj/JOURNAL--index--MOBILE.png',
'LAWYGO_JOURNAL_cover_preview.png':latest/'previews_wsj/JOURNAL--index--DESKTOP.png',
'LAWYGO_JOURNAL_hero_preview.png':latest/'previews_wsj/JOURNAL--index--DESKTOP.png',
'preview_small.png':latest/'previews_partnership/HOME--DESKTOP.png',
'partnership_hero_crop_test.png':latest/'previews_partnership/PARTNERSHIP--DESKTOP.png',
}
for n,src in matches.items():print(n,save_as(src,n))
# Correct all generated MOU render snapshots in the archive with the newly checked DOCX render.
p=BASE/'06_MOU_렌더검수'
for f in p.glob('*.png'):
 number=next((i for i in (1,2,3) if f'page-{i}' in f.name or f'page_{i}' in f.name),None)
 if number:
  raw=Path(f'/mnt/data/_mou_qa_final/page-{number}.png')
  f.write_bytes(raw.read_bytes());print('MOU updated',f.name)
