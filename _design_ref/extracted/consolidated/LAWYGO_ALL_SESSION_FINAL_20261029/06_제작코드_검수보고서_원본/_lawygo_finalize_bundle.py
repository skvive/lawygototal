from pathlib import Path
import json,hashlib,zipfile,collections,os
from PIL import Image
ROOT=Path('/mnt/data/_lawygo_qa_work/LAWYGO_전체세션')
AUD=json.loads(Path('/mnt/data/_lawygo_audit_data.json').read_text('utf-8'))
COR=json.loads(Path('/mnt/data/_lawygo_text_corrections.json').read_text('utf-8'))
latest=ROOT/'01_최종완성_웹사이트_Partnership_MOU'
qa={
 'revision':'2026-10-29 Korean typography and grammar QA',
 'checked':{'html':AUD['html_files'],'image_assets':AUD['images'],'relative_references':AUD['html_relative_resources_checked'],'image_references':AUD['html_relative_images_checked'],'pdf_pages':AUD['pdf_pages'],'word_files':AUD['docx_files']},
 'text':{'text_file_replace_operations':COR['replace_total']+5+2,'word_document_replacements':sum(x['replacements'] for x in COR['word_changes']),'revised_text_files':COR['files_changed']+2,'sample_rules':COR['changes'][:25]},
 'images':{'preview_rerenders':97,'regenerated_text_bearing_promo_composites':4,'corrected_marketing_banner':True,'fresh_cropped_text_free_visual':'assets/editorial-architecture-ai-new.jpg','kept_original_user_reference_images':True},
 'validation':{'broken_local_references':AUD['broken_references'],'invalid_raster_or_svg_files':AUD['invalid_images_or_svg'],'python_scripts_compile':'passed','docx_render_pdf_page_count':3,'live_browser_checkout_or_payment':'not tested; PR review only'},
 'caveats':['법률·투자 콘텐츠는 실제 자문/보도가 아닌 시안으로 표기됨','뉴스레터·구독 및 결제 운영은 현재 활성화되지 않음','모든 이미지의 생성형 표현에 대해 객관적 사실 검증을 보증하지 않음','출시 전 변호사 직역·이용약관·특허 권리/회사 표기 등 법무 검토 필요','이미지 속 글자는 새 AI 이미지에서 직접 생성하지 않고 HTML/정확한 한글 글꼴로 조판함'],
}
(latest/'TEXT_IMAGE_QA.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),'utf-8')
(ROOT/'한글_문법_이미지_검수_결과.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2),'utf-8')
report=f'''# LAWYGO 전체 세션 — 한국어 문법·이미지 교정 결과

**검수 및 재패키징 일자:** 2026-10-29  
**최신 완성본 시작 파일:** `01_최종완성_웹사이트_Partnership_MOU/index.html`  
**검수 범위:** 이전 버전까지 포함한 HTML **{AUD['html_files']}개**, 이미지·SVG **{AUD['images']}개**, Word **1개**, PDF **2개(총 {AUD['pdf_pages']}쪽)**, 관련 문구가 포함된 JavaScript·Markdown·JSON·Python 파일.

## 1. 한국어 문장·표기 검수

- HTML 및 부속 텍스트 파일에서 **{COR['replace_total']+7:,}회**의 표기·문장 교정을 반영했습니다. 동일한 문구가 여러 페이지 및 이전 버전에 중복되어 있어 횟수는 서로 다른 문장의 개수를 뜻하지 않습니다.
- 문서 편집본 Word에서는 별도 **4곳**을 교정한 뒤 PDF를 재생성했습니다.
- 자주 등장한 교정: `구독안내 → 구독 안내`(112), `판례정보 → 판례 정보`(59), `법률정보 → 법률 정보`(52), `전문서식 → 전문 서식`(44), `송무관리 → 송무 관리`(42), `사건정보 → 사건 정보`(33), `미국 경제·증권제도 → 미국 경제·증권 제도`(30), `경제법률 → 경제·법률`(25), `사건관리 → 사건 관리`(25), `사건검색 → 사건 검색`(23).
- 어색한 직역·홍보 문구도 개선: `그 차이를 배달합니다 → 그 차이를 설명합니다`; `국제 정보서비스의 인상을 흉내내는 대신 → 국제 정보 서비스의 외형을 모방하기보다`; `경제를 이해하는 가장 깊은 방법은 … → 경제를 깊이 이해하려면 …`.
- 파트너십 관련 문구 `업무협약을 체결하여 …`는 체결 사실을 확정적으로 표현하지 않도록 `업무협약(MOU)을 제안하고 …`로 수정했습니다.

## 2. 이미지의 한국어 글자 오류 수정

- AI가 생성한 홍보용 화면 합성물에서 읽기 어렵거나 부정확한 한글 글자를 **검수된 실제 HTML 브라우저 스크린샷 조합으로 대체**했습니다.
- `assets/lawygo-partnership-concept.jpg`: 기존 AI 이미지의 잘못 생성된 브랜드 텍스트를 제거하고, `함께 만드는 법률·기술 협력 생태계` 등의 정확한 문구를 한글 글꼴로 다시 조판했습니다.
- 각 버전의 `assets/brand-concept.jpg` 및 별도의 AI 홈페이지 목업 3장은 본문과 동일한 글꼴·문구를 사용한 실제 웹 화면 합성 이미지로 교체했습니다.
- HTML 검수 이후 PC·모바일 웹 화면 **97장**을 재렌더링했고, 저널·위키·송무·제휴 문의 대표 화면과 조판 품질을 눈으로 확인했습니다.
- 새 생성형 비주얼은 문자가 들어가지 않는 건축·도시 부분만 잘라 `assets/editorial-architecture-ai-new.jpg`에 보관했습니다. 이미지상의 한글은 AI가 추측하여 그리지 않도록 했습니다.
- 사용자 제공 원본 이미지 5개는 보존했습니다. 로고의 L과 내부 네모 문법도 유지했습니다.

## 3. 검증 결과

| 항목 | 결과 |
|---|---|
| HTML 파일 | {AUD['html_files']}개 |
| 이미지 및 SVG 유효성 검사 | {AUD['images']}개, 손상 {AUD['invalid_images_or_svg']}건 |
| 내부 링크·이미지·스크립트 참조 | {AUD['html_relative_resources_checked']:,}개 확인, 누락 {AUD['broken_references']}건 |
| PDF 문서 | 2개 / 합계 {AUD['pdf_pages']}쪽 |
| 수정한 MOU Word / PDF | 각 1개, Word 재렌더링 3쪽 확인 |
| 파이썬 제작·QA 스크립트 | 문법 컴파일 성공 |
| 이전 버전 보존 | 3개 버전의 주요 소스와 미리보기 유지 |

## 4. 주요 파일과 실행 방법

- `01_최종완성_웹사이트_Partnership_MOU/index.html` — 전체 브랜드 메인
- `01_최종완성_웹사이트_Partnership_MOU/journal/index.html` — WSJ 참고 신규 경제·법률 저널
- `01_최종완성_웹사이트_Partnership_MOU/payment.html` — 구독 결제 안내용 마케팅 시안
- `01_최종완성_웹사이트_Partnership_MOU/partnership.html` — 국내 법무법인 제휴
- `01_최종완성_웹사이트_Partnership_MOU/documents/LAWYGO_법무법인_MOU_약정서.docx` — 교정된 약정서
- `03_별도_AI_이미지_대표_미리보기/LAWYGO_교정완료_6개주요화면.jpg` — 교정된 화면 모음
- `01_최종완성_웹사이트_Partnership_MOU/DOMAIN_DEPLOYMENT_PLAN.md` — 도메인 구성

**참고:** Stripe 정기결제 코드 변경분은 GitHub 비공개 Draft PR [shinkangteam/lexid#14](https://github.com/shinkangteam/lexid/pull/14)에 있고, 이 ZIP은 시안·소스·산출물 보관용입니다. 신규 유료 결제는 아직 운영 배포나 실제 카드 청구가 활성화된 것이 아닙니다.

**검수의 한계:** 이번 점검은 정적 텍스트와 브라우저 렌더링을 중심으로 한 국문 교열입니다. 일부 법률 전문용어의 정확한 공식 명칭, 실시간 법률·경제 사실관계, 각 법인의 권리·등록정보 및 모든 외부 링크의 운영 상태는 별도 확인이 필요합니다.
'''
(ROOT/'00_한글_문법_이미지_검수보고서.md').write_text(report,'utf-8')
Path('/mnt/data/LAWYGO_KOREAN_TEXT_IMAGE_QA_REPORT.md').write_text(report,'utf-8')
readme=ROOT/'00_읽어주세요.md'
readme.write_text('# LAWYGO 전체 세션 교정·검수 통합본\n\n한국어 문법과 이미지 타이포그래피 수정 결과는 `00_한글_문법_이미지_검수보고서.md`에서 확인할 수 있습니다.\n\n'+readme.read_text('utf-8'),'utf-8')
# regenerate manifest of all current files; include size and hash of every artifact for reproducibility.
entries=[]
for p in sorted(ROOT.rglob('*')):
 if not p.is_file() or p.name=='파일목록.json':continue
 entries.append({'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(ROOT/'파일목록.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2),'utf-8')
# export one corrected preview
preview=ROOT/'03_별도_AI_이미지_대표_미리보기/LAWYGO_교정완료_6개주요화면.jpg'
Path('/mnt/data/LAWYGO_KOREAN_PROOFREAD_PREVIEW.jpg').write_bytes(preview.read_bytes())
# zip; avoid nested ZIP and pycache, include updated manifest.
out=Path('/mnt/data/LAWYGO_ALL_SESSION_KOREAN_PROOFREAD_20261029.zip')
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7,allowZip64=True) as z:
 for f in sorted(ROOT.rglob('*')):
  if f.is_file() and '__pycache__' not in f.parts:
   z.write(f, 'LAWYGO_전체세션_국문교정본/'+str(f.relative_to(ROOT)))
with zipfile.ZipFile(out) as z:
 failure=z.testzip()
 print(json.dumps({'path':str(out),'size_mb':round(out.stat().st_size/1024**2,2),'files':len(z.namelist()),'zip_crc_error':failure,'manifest_count':len(entries)},ensure_ascii=False))
