from pathlib import Path
from zipfile import ZipFile,ZIP_DEFLATED
import json,os,hashlib
root=Path('/mnt/data'); out=root/'LAWYGO_ALL_SESSION_PROJECT_FILES_20261029.zip'
latest=root/'LAWYGO_PARTNERSHIP_SITE'
prior=['LAWYGO_WSJ_EDITORIAL_SITE','LAWYGO_PAYMENT_COMPLETE_SITE','LAWYGO_ATLAS_SITE','lawygo_journal']
references=['1793206761151.jpeg','1793207959751.jpeg','1793210107739.jpeg','27939.jpg','27943.jpg']
selected_previews=['ALL_PAGES_CONTACT_SHEET.jpg','index.png','journal--index.png','pro--index.png','MOBILE--pro--index.png','payment.png','FULL--journal--index.png']
entries=[]
def add(file,arc):
 if file.is_file(): entries.append((file,'LAWYGO_전체세션/'+arc))
for p in latest.rglob('*'):
 if p.is_file():add(p,'01_최종완성_웹사이트_Partnership_MOU/'+p.relative_to(latest).as_posix())
for d in prior:
 base=root/d
 for p in base.rglob('*'):
  if not p.is_file():continue
  rel=p.relative_to(base)
  if any(part.startswith('previews') for part in rel.parts):
   if p.name not in selected_previews:continue
  add(p,'02_이전버전_원본소스/'+d+'/'+rel.as_posix())
for p in root.iterdir():
 if not p.is_file():continue
 if p.name in references:add(p,'05_사용자_원본_참고이미지/'+p.name)
 elif p.suffix.lower()=='.py' and p.name not in ('_bundle_all_lawygo.py','_bundle_compact_lawygo.py'):add(p,'04_개발_빌드_QA_스크립트/'+p.name)
 elif p.suffix.lower() in ['.png','.jpg','.jpeg'] and p.name not in references: add(p,'03_별도_AI_이미지_대표_미리보기/'+p.name)
for d in ['_lawygo_mou_render_updated']:
 for p in (root/d).rglob('*'):
  if p.is_file():add(p,'06_MOU_렌더검수/'+p.name)
extra='''# LAWYGO 전 세션 종합본 (2026-10-29)

이번 세션의 최종 사이트 전체, 이전 4개 버전의 HTML/CSS/JS/이미지 및 상세페이지, 대표 미리보기, AI 생성 이미지, 로고, 법무법인 MOU DOCX/PDF, 국내 영업소·도메인 정보, 파트너십 문의 페이지, 제작/검수 Python 스크립트, 사용자 참고 이미지가 포함됩니다.

**시작 파일** : `01_최종완성_웹사이트_Partnership_MOU/index.html`

**주요 개별 파일** :
- `01_최종완성_웹사이트_Partnership_MOU/partnership.html`
- `01_최종완성_웹사이트_Partnership_MOU/payment.html`
- `01_최종완성_웹사이트_Partnership_MOU/documents/LAWYGO_법무법인_MOU_약정서.docx`
- `01_최종완성_웹사이트_Partnership_MOU/documents/LAWYGO_법무법인_MOU_약정서.pdf`
- `01_최종완성_웹사이트_Partnership_MOU/DOMAIN_DEPLOYMENT_PLAN.md`

**별도 GitHub 작업** : `https://github.com/shinkangteam/lexid/pull/14`
Stripe 신규 구독 연동은 GitHub 비공개 저장소의 Draft PR에 남아 있습니다. 이 ZIP의 HTML Payment 페이지는 사이트 시안이며 실제 Stripe 운영 결제는 설정·배포되지 않았습니다.

**기존에 전달한 ZIP 원본** : 중복·용량 절감을 위해 ZIP을 ZIP에 다시 넣지는 않았습니다. 대신 이전 버전 웹 소스와 주요 대표 캡처를 이 압축본에 직접 담았습니다. 이전 ZIP 자체가 필요한 경우 기존 대화의 링크를 이용하세요.

법무법인 제휴 MOU는 계약 전 법률검토용 초안입니다. 도메인 및 전화는 고객 제공 정보입니다.
'''
manifest=[{'file':arc,'bytes':p.stat().st_size} for p,arc in entries]
with ZipFile(out,'w',ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
 z.writestr('LAWYGO_전체세션/00_읽어주세요.md',extra)
 z.writestr('LAWYGO_전체세션/파일목록.json',json.dumps(manifest,ensure_ascii=False,indent=1))
 for p,arc in entries:z.write(p,arc)
with ZipFile(out) as z:
 bad=z.testzip()
 print(json.dumps({'zip':str(out),'size':out.stat().st_size,'members':len(z.namelist()),'bad':bad,'final_html':any(x.endswith('01_최종완성_웹사이트_Partnership_MOU/index.html') for x in z.namelist()),'MOU_DOCX':any(x.endswith('LAWYGO_법무법인_MOU_약정서.docx') for x in z.namelist()),'MOU_PDF':any(x.endswith('LAWYGO_법무법인_MOU_약정서.pdf') for x in z.namelist())},ensure_ascii=False))
