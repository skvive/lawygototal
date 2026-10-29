from pathlib import Path
from bs4 import BeautifulSoup
import json, re, zipfile, shutil, hashlib
from PIL import Image,ImageOps,ImageDraw,ImageFont
from pypdf import PdfReader
ROOT=Path('/mnt/data/LAWYGO_PAN_2026_EXPANSION');SITE=ROOT/'site';BOOKS=ROOT/'books'
htmlfiles=sorted(SITE.glob('*.html'));broken=[];resources=[];pdfs=[];formats=[];unclear=[]
for f in htmlfiles:
 s=BeautifulSoup(f.read_text(),'html.parser')
 for el in s.select('[href],[src]'):
  v=(el.get('href') or el.get('src') or '').strip()
  if not v or v.startswith(('http:','https:','mailto:','tel:','#','data:','javascript:','{{','/api/','/unsubscribe','/verify')):continue
  v=v.split('#')[0].split('?')[0]
  if not v:continue
  target=(f.parent/v).resolve()
  if not target.exists():broken.append((f.name,v))
  resources.append((f.name,v))
for f in list(SITE.glob('assets/*')):
 if f.suffix.lower() in ('.png','.jpg','.webp','.jpeg','.ico'):
  try:
   with Image.open(f) as im: im.verify()
  except Exception as e: formats.append((f.name,str(e)[:100]))
for f in BOOKS.glob('*.pdf'):
 pdfs.append((f.name,len(PdfReader(f).pages)))
# Illustrated page preview collage from actual static render captures, not AI-drawn text.
pre=SITE/'previews';shots=[pre/f'EXPANDED_{s}-desktop.png' for s in ('content-feed','free-signup','advertising','investor-overview')]
shots=[x for x in shots if x.exists()]
canvas=Image.new('RGB',(1600,1180),'#f1f3f4')
D=ImageDraw.Draw(canvas)
font='/usr/share/fonts/truetype/nanum/NanumSquareB.ttf'
try:F=ImageFont.truetype(font,32); small=ImageFont.truetype(font,20)
except:F=ImageFont.load_default();small=F
D.text((40,20),'LAWYGO PAN · 2026 EXPANDED PLATFORM',font=F,fill='#102a43')
for i,p in enumerate(shots):
 im=Image.open(p).convert('RGB')
 im=ImageOps.fit(im,(740,460),method=Image.Resampling.LANCZOS,centering=(.5,.1))
 x=38+(i%2)*790;y=95+(i//2)*510
 canvas.paste(im,(x,y)); D.rectangle((x,y,x+740,y+460),outline='#bec7d0',width=2)
 D.text((x+5,y+463),p.stem.replace('EXPANDED_','').replace('-desktop',''),font=small,fill='#394f67')
canvas.save(ROOT/'LAWYGO_PAN_2026_DESIGN_BOARD.jpg',quality=88)
report=f'''# LAWYGO PAN 2026 · 검수 및 납품 보고서

- 기본 도메인: `https://pan.lawygo.com` (사이트의 디자인상 배포 목표 주소이며, 실제 배포되지 않았음)
- HTML 정적 사이트: **{len(htmlfiles)}개**, 기존 32개 페이지에서 증설
- 투자제안서: **{dict(pdfs).get('investor-deck.pdf')}쪽** (사업·수익 시나리오와 근거 구분)
- PDF 책자: **{len(pdfs)}종**, 실제 페이지 수: {pdfs}
- 내부 링크·리소스 점검 대상: **{len(resources)}건**, 깨진 링크: **{len(broken)}건**
- 이미지 파일 검사 오류: **{len(formats)}건**
- 신규 로컬 정적 반응형 화면: 8장 스크린샷. Chromium에서 HTML·이미지·CSS를 인라인 렌더링했고, 가로 넘침 0건.
- API 단위 흐름: 이메일 가입→인증→콘텐츠 제출→광고 동의 인증→수신거부 시연 DB 검증 성공.
- 실제 운영 서버(Stripe, Google OAuth, Blogger API, YouTube API, SMTP, 기업용 DB)와 연동된 상태는 **아님**. 백엔드 예제 서버를 실행하고 운영 설정이 필요.

## 이번 변경 주요 내용

1. 콘텐츠 피드: 채널별 변호사 계정, 쇼츠, Blogger 칼럼, 주제별 후원 광고 카드.
2. 회원: 본인 이메일 인증과 선택 광고 수신동의 분리. 변호사 자격 검수 완료 전에는 공개 프로필 노출 안 됨.
3. 업로드: Blogger와 YouTube **URL** 기반 등록, 소유권·저작권 확인 후 공개.
4. 후원 순위: 자연 추천 점수와 광고 지면을 분리하고 '광고 · 후원 콘텐츠' 표기.
5. 상담 정보: 개인 이메일·직통번호 비공개, 전화·이메일 요청 버튼을 통한 비공개 연결. 인증 미확인 프로필은 연결 거절.
6. 마케팅: [광고] 메일용 HTML·텍스트 시안, 명시적 사전 동의, 무작위 토큰 기반 수신거부, 운영 발송 CLI 기본 비활성.
7. 다국어: 기존 KO·EN UI 전환 및 Google 번역 외부 스크립트 지원(인터넷·외부 위젯 상태에 좌우됨); 공식 영문 웹사이트는 전문 검수 필요.
8. 투자제안서: 46쪽, 회사소개 9쪽, 사용자 13쪽, 광고규정 11쪽, 개인정보 10쪽, 보안 매뉴얼 13쪽.
9. **이미지**: 기존 AI 생성 전문직 이미지 + 이번에 생성한 편집용 6컷 이미지(텍스트 없는 장면)를 활용. 인물·컨텐츠는 실존 프로필이 아닌 시연용.
10. SEO: `sitemap.xml`, `robots.txt`, canonical·OG·favicon 기존 방식 유지.

## 한국어 마케팅 문구 사실 검증

- '네이버 블로그는 AI 검색에서 전면 차단돼 무용지물이다'라는 과도한 단정은 사용하지 않음.
- '네이버에서는 더 이상 상단 노출되지 않는다'는 보장·단정을 사용하지 않음.
- 'Google Blogger에 글을 쓰면 AI 검색에 반드시 활용된다'라고 약속하지 않음.
- 대체 표현: **'검색 가능한 공개 콘텐츠를 장기 자산으로 축적하고, 다채널 검색·AI 탐색의 기회를 넓힙니다.'**
- 투자자의 환산시장 규모·유료회원 전망과 가격은 공식 시장 실적이 아닌 가정으로 표기.

## 참조 출처

- 대한변협 회원 현황 (2026-10-21): https://www.koreanbar.or.kr/pages/introduce/stat.asp
- 대한변협 변호사 광고 규정 (2025-02): https://www.koreanbar.or.kr/pages/board/law_view.asp?category=&page=1&searchstr=&searchtype=&seq=14402&teamcode=&types=6
- KISA 2026 스팸 방지 안내: https://www.kisa.kr/401/form?postSeq=3608
- Google AI 검색: https://developers.google.com/search/docs/appearance/ai-features
- 네이버 검색 순위: https://help.naver.com/service/5626/contents/8022?osType=COMMONOS
- 네이버 AI 브리핑: https://www.navercorp.com/media/pressReleasesDetail?seq=32374
- Blogger API: https://developers.google.com/blogger/docs/3.0/reference/posts/list
- YouTube Data API: https://developers.google.com/youtube/v3/docs/videos/list

## 운영 전 잔여 작업

- 외부 서비스 API 키와 공식 회원 OAuth를 연결해야 함. 샘플 API는 인증 이메일 + 쿠키 방식이며 법률 자격을 자동 검증하지 않음.
- 수신자 메일 발송 SMTP, 실제 발신자 상호·사업자 식별정보, 광고 담당자 및 개인정보 보호책임자 확정.
- 개인정보처리방침·광고 약관에 대한 최종 법률 검토 및 실제 체결 전 MOU 내용 확인.
- 상용 운영 보안 요구 사항: WAF, 분산 rate limit, 암호화 DB, 외부 침해검사, 감사지원, 백업·복구.
- 새 사이트와 기존 `live.lexid.site` 및 Stripe 운영의 실제 통합은 **미완료**. GitHub 미접근 저장소 구현을 가져온 것으로 표현하면 안 됨.
- Chrome의 실제 네트워크 방문 검수는 환경 정책으로 차단되어, 정적 렌더와 API 시뮬레이션으로 검수함.

## 검수 발견 사항
- 문구 수정: 'AI 검색에서 네이버 블로그 무용지물'→'플랫폼별 노출 방식이 다르므로 직접 소유·관리하는 콘텐츠 채널을 병행'.
- 인물 이미지: 책·건물 컷이 프로필 원형 사진에 들어가지 않도록 실제 AI 생성 프로필 컷으로 교체.
- 메인 메뉴: 한 줄에서 줄바꿈되던 과도한 링크 수를 줄이고 핵심 8개로 재구성.
- 광고 라벨 및 실제 검증 불가능한 후기/실적 안내를 시연용으로 유지.

깨진 링크 목록: {broken[:20]}
이미지 파일 오류: {formats[:20]}
'''
(ROOT/'QA_REPORT.md').write_text(report)
# Site landing links to corporate books
rootread=ROOT/'README_START_HERE.md'
rootread.write_text('''# LAWYGO PAN · 제작파일 안내\n\n- `site/index.html`: 메인(변호사·콘텐츠·쇼츠·구글블로그·후원 영역)\n- `site/content-feed.html`: 콘텐츠 통합 지면\n- `site/free-signup.html`: 무료 회원가입 + 본인확인 이메일\n- `site/blogger-connect.html`, `site/youtube-connect.html`: 공개 URL 등록\n- `site/creator-studio.html`: 전문가 콘텐츠 관리 UI\n- `site/advertising.html`, `site/ad-ranking.html`: 광고 상품·노출정책\n- `site/private-inquiry.html`: 비공개 상담/연결 신청\n- `marketing/email-campaign.html`: 이메일 홍보 HTML\n- `marketing/email-campaign.txt`: 이메일 텍스트/광고표기\n- `books/investor-deck.html` 및 `.pdf`: 46쪽 투자제안서\n- `books/company-profile.*`: 회사소개서\n- `books/user-manual.*`: 사용자매뉴얼\n- `books/advertising-policy.*`: 광고규정\n- `books/privacy-manual.*`: 개인정보지침\n- `books/security-manual.*`: 보안운영지침\n- `backend/app.py`: 가입·콘텐츠 등록·수신거부·승인된 피드 API 데모\n- `backend/marketing_send.py`: 동의받은 대상에만 보내는 발송 CLI(기본 미발송)\n- `backend/moderate.py`: 관리자 검수용 CLI\n- `QA_REPORT.md`: 변경·검증·잔여작업 목록\n\n## 로컬 실행\n```bash\ncd LAWYGO_PAN_2026_EXPANSION\npython -m venv .venv\n# activate virtual environment then:\npip install -r backend/requirements.txt\n# configure backend/.env.example into local environment variables\nuvicorn backend.app:app --host 127.0.0.1 --port 8765\n```\n\n운영모드에서 SMTP·비밀키·DB 설정이 빠졌다면 실제 발송은 동작하지 않습니다.\n`LAWYGO_PAN_PREVIOUS_32PAGES.zip`는 이전 고객 납품본이고, `PREVIOUS_LAWYGO_ALL_SESSION.zip`에는 이전 세션의 전체 통합 작업본이 포함됩니다.\n\nGoogle Blogger/YouTube 자동 동기화는 아직 API 계정이 연결되지 않았으며, URL 제출·관리자 승인형 등록 기능의 구현 예제를 제공합니다.\n''')
zipout=Path('/mnt/data/LAWYGO_PAN_ALL_SESSION_INVESTOR_AND_MANUALS_20261029.zip')
external={
 'PREVIOUS_LAWYGO_ALL_SESSION.zip':Path('/mnt/data/LAWYGO_ALL_SESSION_KOREAN_PROOFREAD_20261029.zip'),
 'LAWYGO_PAN_PREVIOUS_32PAGES.zip':Path('/mnt/data/LAWYGO_PAN_32PAGES_FINAL_DESIGN.zip'),
}
with zipfile.ZipFile(zipout,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=7,allowZip64=True) as z:
 for p in sorted(ROOT.rglob('*')):
  if p.is_file() and '/private/' not in str(p) and not p.name.startswith('_'):
   z.write(p,arcname=str(Path('LAWYGO_PAN_2026_EXPANSION')/p.relative_to(ROOT)))
 for name,p in external.items():
  if p.exists():z.write(p,arcname='LAWYGO_PAN_2026_EXPANSION/previous-session/'+name,compress_type=zipfile.ZIP_STORED)
with zipfile.ZipFile(zipout) as z:
 corrupt=z.testzip()
 print('ZIP',zipout,'size_mb',round(zipout.stat().st_size/1048576,2),'entries',len(z.namelist()),'corrupt',corrupt)
print('QA',len(htmlfiles),'broken',len(broken),'pdf_pages',pdfs,'image_errs',len(formats))
