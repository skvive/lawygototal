from pathlib import Path
import json,hashlib,collections,zipfile,datetime,subprocess,xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from PIL import Image
from docx import Document
import fitz
base=Path('/mnt/data/_lawygo_qa_work/LAWYGO_전체세션')
old=Path('/mnt/data/LAWYGO_ALL_SESSION_PROJECT_FILES_20261029.zip')
changed=collections.defaultdict(list); unchanged=0;missing=[]
with zipfile.ZipFile(old) as z:
 for name in z.namelist():
  rel=name.removeprefix('LAWYGO_전체세션/')
  f=base/rel
  if not f.exists(): missing.append(rel);continue
  if hashlib.sha256(z.read(name)).digest()!=hashlib.sha256(f.read_bytes()).digest():changed[f.suffix.lower()].append(rel)
  else:unchanged+=1
img=[];html=[];texts=[];broken=[];bad=[]; local_links=0; img_links=0
for f in base.rglob('*'):
 if not f.is_file():continue
 if f.suffix.lower() in ('.png','.jpg','.jpeg','.webp'):
  img.append(f)
  try:
   with Image.open(f) as im:im.verify()
  except Exception as e: bad.append((str(f.relative_to(base)),str(e)))
 if f.suffix=='.svg':
  img.append(f)
  try:ET.parse(f)
  except Exception as e:bad.append((str(f.relative_to(base)),str(e)))
 if f.suffix=='.html':
  html.append(f)
  soup=BeautifulSoup(f.read_text('utf-8'),'html.parser')
  for tag in soup.find_all(['a','img','script','link']):
   u=tag.get('src' if tag.name in ('img','script') else 'href','')
   if not u or u.startswith(('https://','http://','mailto:','tel:','#','javascript:','data:','//')):continue
   u=u.split('#')[0].split('?')[0]
   if not u:continue
   local_links+=1
   if tag.name=='img':img_links+=1
   if not (f.parent/u).exists():broken.append((str(f.relative_to(base)),u))
# PDF text check
pdfs=list(base.rglob('*.pdf'));docx=list(base.rglob('*.docx'))
pdf_pages=sum(fitz.open(f).page_count for f in pdfs)
version={'original_file_count':384,'all_files':len([f for f in base.rglob('*') if f.is_file()]),'html_files':len(html),'images':len(img),'pdf_files':len(pdfs),'pdf_pages':pdf_pages,'docx_files':len(docx),'html_relative_resources_checked':local_links,'html_relative_images_checked':img_links,'broken_references':len(broken),'invalid_images_or_svg':len(bad),'original_files_changed_by_type':{ext:len(fs) for ext,fs in sorted(changed.items())},'original_files_unchanged':unchanged,'original_files_missing':missing,'new_files':[str(f.relative_to(base)) for f in base.rglob('*') if f.is_file() and 'LAWYGO_전체세션/'+str(f.relative_to(base)) not in set()], 'sample_broken':broken[:12],'sample_invalid':bad[:12]}
# Don't include massive erroneous new_files list in output
version.pop('new_files')
print(json.dumps(version,ensure_ascii=False,indent=2))
Path('/mnt/data/_lawygo_audit_data.json').write_text(json.dumps(version,ensure_ascii=False,indent=2),'utf-8')
