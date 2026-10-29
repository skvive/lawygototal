from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import zipfile, json, os, hashlib, csv
R=Path('/mnt/data/LAWYGO_PAN_DELIVERY');prev=R/'previews';A=R/'assets'
name_map={'index':'메인','lawyers':'변호사 찾기','lawyer-jihye':'변호사 프로필 A','lawyer-hyunwoo':'변호사 프로필 B','lawyer-sujeong':'변호사 프로필 C','practice':'전문 분야','consult':'상담 문의','contents':'법률 콘텐츠','article-business':'기업 법률','article-lease':'부동산 법률','videos':'법률 영상','video-guide':'영상 상세','firms':'법무법인','for-lawyers':'전문가용','blog-builder':'블로그·영상 빌더','pricing':'요금제','partnership':'파트너십','faq':'FAQ','about':'서비스 소개','contact':'제휴 문의','terms':'약관 예시','privacy':'개인정보 안내'}
font_path='/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf'
if not os.path.exists(font_path):font_path='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
font=ImageFont.truetype(font_path,22);small=ImageFont.truetype(font_path,16)
for mode in ('desktop','mobile'):
 entries=list(name_map.items());columns=4 if mode=='desktop' else 6;thumbw=340 if mode=='desktop' else 176;thumbh=280 if mode=='desktop' else 300;gap=14;rows=(len(entries)+columns-1)//columns
 board=Image.new('RGB',(columns*(thumbw+gap)+gap,rows*(thumbh+gap)+gap+70),'#f4f4f0');d=ImageDraw.Draw(board)
 d.text((gap,13),f'LAWYGO PAN — {mode.upper()} · 22 PAGES',fill='#122941',font=font)
 for i,(slug,label) in enumerate(entries):
  src=prev/f'{slug}-{mode}.png';im=Image.open(src).convert('RGB');
  if mode=='desktop':im=im.crop((0,0,im.width,min(im.height,820)))
  # Keep aspect ratio using contain on ivory background, no stretching.
  im.thumbnail((thumbw,thumbh-40),Image.Resampling.LANCZOS)
  x=gap+(i%columns)*(thumbw+gap);y=70+gap+(i//columns)*(thumbh+gap)
  d.rounded_rectangle((x,y,x+thumbw,y+thumbh),radius=9,fill='white')
  board.paste(im,(x+(thumbw-im.width)//2,y+6))
  d.text((x+12,y+thumbh-30),f'{i+1:02d}  {label}',fill='#122941',font=small)
 board.save('/mnt/data/LAWYGO_PAN_'+mode.upper()+'_ALL_PAGES.jpg',quality=88)
# selected premium preview grid montage
selected=[('index','메인'),('lawyers','전문가 검색'),('lawyer-jihye','프로필'),('contents','콘텐츠'),('blog-builder','채널 연동'),('pricing','요금제')]
w,h=1500,930;board=Image.new('RGB',(w,h),'#f5f3ee');d=ImageDraw.Draw(board)
d.rectangle((0,0,w,85),fill='#10263f');d.text((35,20),'LAWYGO PAN · DESIGN SYSTEM',fill='white',font=ImageFont.truetype(font_path,30))
for i,(slug,label) in enumerate(selected):
 im=Image.open(prev/f'{slug}-desktop.png').convert('RGB');im.thumbnail((470,370),Image.Resampling.LANCZOS)
 x=25+(i%3)*495;y=105+(i//3)*407
 d.rounded_rectangle((x,y,x+470,y+375),radius=9,fill='white')
 board.paste(im,(x+(470-im.width)//2,y+7))
 d.text((x+16,y+347),f'{i+1:02d}  {label}',fill='#10263f',font=small)
board.save('/mnt/data/LAWYGO_PAN_DESIGN_PREVIEW.jpg',quality=92)
# Source evidence + QA report
(R/'LINKR_SOURCE_MAPPING.md').write_text('''# LAWYGO PAN — 소스 벤치마킹 및 통합 대응표

## 실제 조회 결과 (2026-10-29)
- 사용자 지정 `skvive/linkr`: 해당 경로의 GitHub 저장소 응답 404. 읽기 불가. **반영했다고 주장하지 않음.**
- `skvive/linkrcode`: 접근 가능. 실제 앱이 아닌 운영 스크립트·에이전트 설정 중심의 작은 저장소.
- `shinkangteam/linkr`: 연결된 GitHub에서 실제로 조회 가능한 대형 Next.js 앱(3,798 blob 파일). 해당 저장소의 아래 코드를 비교 분석.
- `live.lexid.site` 실배포는 Vercel 프로젝트 `live` / GitHub `shinkang888-code/srocks`로 확인. 소스는 브랜드북 iframe으로, 요청된 Blogger·YouTube 엔진의 존재는 확인하지 못함.

## 반영 경로
| 확인된 Linkr 구조 | LAWYGO PAN 적용 위치 | 상태 |
| --- | --- | --- |
| `lib/feed.ts` 피드 타입 분리 | `contents.html`, `videos.html` 카테고리 카드 | 화면 구조 참고 |
| `components/feed/FeedNlSearch.tsx` 키워드 검색·결과 | `contents.html` 검색·블로그/영상 필터 | JS 독립 재구현 |
| `lib/social.ts` 프로필/관심사/DM | `lawyers.html`, 가상 변호사 프로필, 관심 저장 | UI 패턴 참고 / DM 서버 미연결 |
| `components/social/SnsDiscover.tsx` 프로필 탐색 | 전문 분야·지역·이름 필터 | JS 독립 재구현 |
| `app/api/ads/campaign/route.ts` 광고 세션·가격·멱등성 검증 | 전문가 마케팅·광고 프로그램 미래 설계 | 실서버 미연결 |
| `docs/feed-vnext-poc.md` Editorial/Journal/Clip | 저널형 글·영상 콘텐츠 탐색 | 독자적인 레이아웃 |
| `lib/video.ts` 브라우저 영상 인코딩 | 채널 연동 단계의 원본 영상 업로드 정책 | 데모에 인코딩 이식 없음 |

## API 통합 계약(안)
1. `GET /api/pan/lawyers?practice=&region=&q=` — 검증된 변호사 프로필 목록.
2. `GET /api/pan/content?type=blog|video&q=` — Blogger/YouTube 수집된 콘텐츠.
3. `POST /api/pan/inquiries` — 로그인/비회원 동의 상태 확인, 연락처 보호·스팸 방지·감사 로그.
4. `POST /api/pan/creators/connect` — OAuth/채널 URL 검증 및 권한 확인.
5. `GET /api/pan/analytics` — 로그인 변호사 본인에게만 조회수/클릭수/문의수 제공.
6. `POST /api/pan/ads` — 인증, 서버 가격 확정, 중복결제 방지, 심사 후 게시.
7. Stripe는 `shinkangteam/lexid`의 LAWYGO 전용 결제 PR #14 설계와 연결하되 운영 승인 전 비활성화.

## 실운영 제약
- 본 패키지에 포함된 22페이지는 **정적 사이트 + 로컬 JS UI 시연**입니다.
- Linkr, LAWYGO, Blogger, YouTube의 운영 DB/API 키는 포함되지 않았습니다.
- 법률 광고 규정·변호사 신원 검증·개인정보처리 정책·상담 정보 보안이 우선 필요합니다.
''',encoding='utf-8')
q=json.loads((R/'QA_RESULTS.json').read_text());q['notes']=['22개 HTML 각각 화면 캡처(PC/모바일)하여 가로 넘침 검사','브라우저 모의 실행에서 검색·필터, KR/EN 토글, YouTube 임베드 미리보기, 모바일 메뉴 테스트 통과','실 API/Google 번역 위젯/실결제의 운영 통합 여부는 테스트하지 않음']
(R/'QA_RESULTS.json').write_text(json.dumps(q,ensure_ascii=False,indent=2),encoding='utf-8')
(R/'HANDOFF_CHECKLIST.md').write_text('''# 고객 검수 및 운영 인수인계

## 디자인 납품 항목
- 22개 HTML 상세 페이지 + 공통 CSS/JavaScript.
- AI 생성 이미지 재편집 8종, 로고 아이콘, favicon PNG/SVG, Apple touch icon, OG 이미지.
- PC 22장, 모바일 22장의 1차 화면 캡처 및 전체 모아보기 이미지.
- 한국어 문장 및 네비게이션 표기 교정, 반응형·검색·채널 URL 검사.

## 고객 관점 검수 후 변경한 사항
1. 전면 히어로의 복잡한 조작을 줄이고 바로 키워드를 입력할 수 있게 변경.
2. 콘텐츠와 변호사 프로필을 구분해 목록 정보가 한눈에 보이도록 변경.
3. 가상 전문직 이미지 중복을 줄이고 모든 시연 프로필에 가상임을 명시.
4. 콘텐츠 검색과 `전체/블로그/영상` 필터를 추가.
5. `메일 초안 열기`로 실제 상담 접수와 구분하여 오해를 방지.
6. 가입과 상담 관련 통계·후기·인증 수치를 임의로 제시하지 않음.
7. 주요 텍스트는 내장 영어 전환, 부가 텍스트는 Google Translate 가용 시 위젯으로 번역 시도.

## 사용자 수락 기준(정식 오픈 전)
- 검색 결과는 등록·자격확인을 통과한 실제 변호사만 표시.
- 상담 접수 건은 저장·전송이 되고 사용자에게 접수번호·응답 방법 안내.
- 개인정보 동의·처리 방침·국외 이전·전문직 광고규정 사전 검수.
- 블로그/YouTube 수집에 대한 작성자 동의, 저작권 표시 및 원문 링크.
- 법무법인·변호사 등록·수정 권한 검증 및 관리자 승인.
- 결제/광고 분리, 환불·해지·결제 실패·웹훅 중복 검증.
- Google Translate 운영 브라우저 호환성 및 영문 SEO 체크.
''',encoding='utf-8')
# Include full-page route listing and assets manifest.
files=[x for x in R.rglob('*') if x.is_file()];manifest=[{'file':str(p.relative_to(R)),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(files)]
(R/'FILES_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
zip_path=Path('/mnt/data/LAWYGO_PAN_22PAGES_LINKR_BENCHMARK_COMPLETE.zip')
with zipfile.ZipFile(zip_path,'w',zipfile.ZIP_DEFLATED,compresslevel=7) as z:
 for p in R.rglob('*'):
  if p.is_file():z.write(p,'LAWYGO_PAN/'+str(p.relative_to(R)))
 # top-level visual overview
 z.write('/mnt/data/LAWYGO_PAN_DESIGN_PREVIEW.jpg','LAWYGO_PAN/DESIGN_PREVIEW.jpg')
 z.write('/mnt/data/LAWYGO_PAN_DESKTOP_ALL_PAGES.jpg','LAWYGO_PAN/PC_ALL_PAGES.jpg')
 z.write('/mnt/data/LAWYGO_PAN_MOBILE_ALL_PAGES.jpg','LAWYGO_PAN/MOBILE_ALL_PAGES.jpg')
with zipfile.ZipFile(zip_path) as z:bad=z.testzip();print('ZIP',zip_path,'size_MB',round(zip_path.stat().st_size/1e6,2),'files',len(z.namelist()),'bad',bad)
print('QA',q['pages'],q['screenshots'],'issues',len(q['issues']))
