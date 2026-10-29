from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, ZIP_STORED
import os, json, hashlib, datetime

root=Path('/mnt/data')
out=root/'LAWYGO_20261029_ALL_SESSION_WORKFILES.zip'
version_dirs=['LAWYGO_PARTNERSHIP_SITE','LAWYGO_WSJ_EDITORIAL_SITE','LAWYGO_PAYMENT_COMPLETE_SITE','LAWYGO_ATLAS_SITE','lawygo_journal']
refs={'1793206761151.jpeg','1793207959751.jpeg','1793210107739.jpeg','27939.jpg','27943.jpg'}
exclude_dirs={'__pycache__','.git','.next','node_modules','user-juZbsnopn7J1MqkKq77BhiGg'}
exclude_files={out.name,'_bundle_all_lawygo.py'}
entries=[]
for folder in version_dirs:
  for p in sorted((root/folder).rglob('*')):
    if not p.is_file() or any(x in exclude_dirs for x in p.relative_to(root).parts): continue
    folder_alias={'LAWYGO_PARTNERSHIP_SITE':'01_최종_파트너십_MOU_도메인_반영', 'LAWYGO_WSJ_EDITORIAL_SITE':'02_WSJ_저널_개편_소스', 'LAWYGO_PAYMENT_COMPLETE_SITE':'03_Payment_반영_이전판', 'LAWYGO_ATLAS_SITE':'04_로이고PRO_35페이지_이전판','lawygo_journal':'05_초기_저널_HTML'}[folder]
    arc=f'LAWYGO_통합작업물/{folder_alias}/{p.relative_to(root/folder).as_posix()}'
    entries.append((p,arc))
for p in sorted(root.glob('LAWYGO_*.zip')):
  if p.name != out.name:
    entries.append((p,f'LAWYGO_통합작업물/06_이전_납품_ZIP/{p.name}'))
for p in sorted(root.glob('*')):
  if not p.is_file() or p.name in exclude_files or p.suffix.lower() not in ('.jpg','.jpeg','.png','.webp','.svg','.py'):
    continue
  if p.name in refs:
    group='09_사용자_제공_참고이미지'
  elif p.suffix.lower()=='.py':
    group='08_제작_검증_소스스크립트'
  else:
    group='07_대표_렌더_및_AI_이미지'
  entries.append((p,f'LAWYGO_통합작업물/{group}/{p.name}'))
for folder in ['_lawygo_mou_render','_lawygo_mou_render_updated']:
  for p in (root/folder).rglob('*'):
    if p.is_file(): entries.append((p,f'LAWYGO_통합작업물/10_MOU_출력_검수_이미지/{folder}/{p.relative_to(root/folder).as_posix()}'))

summary={
 'project':'LAWYGO JOURNAL · WIKI · NOTE · PRO · PAN — 2026-10-29 전체 세션 산출물',
 'files':len(entries),
 'sections': {
 '01':'최신 전체 웹사이트 소스·제휴 페이지·법무법인 MOU DOCX/PDF·도메인 안내·로고·이미지',
 '02':'WSJ 벤치마크 기반 LAWYGO JOURNAL 개선판',
 '03':'Payment/Stripe 연동 화면이 포함된 HTML 이전판',
 '04':'LAWYGO PRO 35페이지 시안과 이미지',
 '05':'초기 LAWYGO JOURNAL HTML',
 '06':'세션에서 제공했던 모든 이전 ZIP 납품물 원본',
 '07':'별도 제공한 대표 미리보기 및 AI 이미지',
 '08':'제작·검증 파이썬 소스와 자동화 스크립트',
 '09':'사용자가 제공한 브랜드 및 UI 참고 이미지',
 '10':'MOU PDF 페이지 출력 및 검수 이미지'},
 'github': {'repo':'https://github.com/shinkangteam/lexid','pr':'https://github.com/shinkangteam/lexid/pull/14','note':'Stripe 코드 변경은 GitHub 비공개 저장소의 PR #14에 있으며 운영 배포·판매 활성화된 상태가 아닙니다. ZIP 내부 HTML Payment 화면은 데모/프런트엔드 시안입니다.'},
 'deployment':'현재 패키지의 HTML을 로컬에서 볼 수 있으나, Stripe 실결제, Google 로그인, DB, 이메일 전송, 법원 API는 별도 서비스 설정과 배포 후 연동해야 합니다.',
 'source':'/mnt/data'
}
README='''# LAWYGO 전체 세션 작업파일 통합본\n\n- 기준: 2026-10-29\n- 포함: 저널, 위키, 노트, 프로 송무, 판, Payment 시안, Partnership, MOU, 로고, AI 이미지, PC/모바일 캡처, 이전 납품 ZIP, 제작 스크립트\n- 최종본 시작 파일: `01_최종_파트너십_MOU_도메인_반영/index.html`\n- 제휴 페이지: `01_최종_파트너십_MOU_도메인_반영/partnership.html`\n- 결제 페이지: `01_최종_파트너십_MOU_도메인_반영/payment.html`\n- MOU: `01_최종_파트너십_MOU_도메인_반영/documents/LAWYGO_법무법인_MOU_약정서.docx` 및 `.pdf`\n- 도메인 안내: `01_최종_파트너십_MOU_도메인_반영/DOMAIN_DEPLOYMENT_PLAN.md`\n- 전체 파일 목록: `파일목록_MANIFEST.json`\n\n## GitHub 결제 코드는 별도\n- `https://github.com/shinkangteam/lexid/pull/14` : LAWYGO Stripe 정기구독/권한 연동을 위한 Draft PR\n- Stripe 실제 계정의 결제상품 개설·운영 결제 활성화·배포는 진행되지 않았습니다.\n- ZIP 안의 독립 HTML 결제 페이지는 프런트엔드 시안이고 기존 GitHub 결제 API는 GitHub PR에서 관리됩니다.\n\n## 유의 사항\n- 다양한 시점의 이전 작업본이 포함돼 있습니다. 실제 공개용으로는 최신 폴더의 사실관계, 고지, 구독약관, 연락처를 검토해 배포해야 합니다.\n- MOU는 계약 전 검토용 초안입니다.\n- 원본 브랜드 레퍼런스 이미지 5장도 참고용으로 보관했습니다.\n'''
manifest=[{'file':arc,'bytes':p.stat().st_size} for p,arc in entries]
with ZipFile(out,'w',allowZip64=True,compression=ZIP_DEFLATED,compresslevel=6) as z:
  z.writestr('LAWYGO_통합작업물/00_먼저_읽어주세요.md',README)
  z.writestr('LAWYGO_통합작업물/파일목록_MANIFEST.json',json.dumps({'summary':summary,'files':manifest},ensure_ascii=False,indent=2))
  for i,(p,arc) in enumerate(entries,1):
    z.write(p,arc)
    if i%100==0:print('packed',i,'/',len(entries),flush=True)
with ZipFile(out) as z:
  invalid=z.testzip()
  namelist=z.namelist()
print(json.dumps({'path':str(out),'bytes':out.stat().st_size,'zip_files':len(namelist),'verified':invalid is None,'latest_index':any('01_최종' in n and n.endswith('/index.html') for n in namelist),'mou_pdf':any(n.endswith('LAWYGO_법무법인_MOU_약정서.pdf') for n in namelist),'mou_docx':any(n.endswith('LAWYGO_법무법인_MOU_약정서.docx') for n in namelist)},ensure_ascii=False,indent=2))
