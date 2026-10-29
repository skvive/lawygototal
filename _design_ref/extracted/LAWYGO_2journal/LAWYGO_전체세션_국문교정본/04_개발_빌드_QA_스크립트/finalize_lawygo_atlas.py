from pathlib import Path
from urllib.parse import urldefrag,unquote,urlsplit
from html.parser import HTMLParser
import json,os,zipfile,hashlib
from PIL import Image,ImageDraw,ImageFont,ImageOps
ROOT=Path('/mnt/data/LAWYGO_ATLAS_SITE')
rows=json.loads((ROOT/'PAGES.json').read_text())
files=[ROOT/x['path'] for x in rows]
class Extract(HTMLParser):
 def __init__(self):super().__init__();self.links=[];self.images=[]
 def handle_starttag(self,tag,attrs):
  d=dict(attrs)
  if tag=='a' and 'href' in d:self.links.append(d['href'])
  if tag=='img' and 'src' in d:self.images.append(d['src'])
issues=[];checked=0;pages=[]
for p in files:
 ex=Extract();ex.feed(p.read_text(encoding='utf8'))
 broken=[]
 for url in ex.links+ex.images:
  if url.startswith(('http:','https:','mailto:','tel:','data:','javascript:','#')):continue
  url=urlsplit(unquote(url)).path
  if not url:continue
  checked+=1
  target=(p.parent/url).resolve()
  if not target.exists():broken.append(url)
 if broken:issues.append(dict(page=str(p.relative_to(ROOT)),broken=broken))
 pages.append(dict(page=str(p.relative_to(ROOT)),links=len(ex.links),images=len(ex.images),broken=broken))
print('Static link checks',checked,'broken',len(issues));print(issues[:4])
previews=ROOT/'previews'; previews.mkdir(exist_ok=True)
W,H=375,290;cols=5;ct=len(rows); rcount=(ct+cols-1)//cols
sheet=Image.new('RGB',(W*cols,H*rcount),'#eeeae2');draw=ImageDraw.Draw(sheet)
f=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',12)
missing=[]
for i,row in enumerate(rows):
 path=row['path'];impath=previews/(path.replace('/','--').replace('.html','.png'))
 if not impath.exists():missing.append(path);continue
 im=Image.open(impath).convert('RGB');im=ImageOps.fit(im,(W-18,H-50),method=Image.Resampling.LANCZOS,centering=(.5,0))
 x=i%cols*W;y=i//cols*H;sheet.paste(im,(x+9,y+7));draw.text((x+9,y+H-32),f'{i+1:02d} · '+path,fill='#1a3349',font=f)
fullsheet=previews/'ALL_PAGES_CONTACT_SHEET.jpg';sheet.save(fullsheet,quality=87)
print('missing screenshots',missing,'sheet size',fullsheet.stat().st_size)
(ROOT/'QA_REPORT.json').write_text(json.dumps({'checked_page_count':len(rows),'checked_internal_links_and_images':checked,'broken_paths':issues,'desktop_1440x900_preview_count':len(rows)-len(missing),'note':'정적 링크·이미지 존재 검사를 완료. 화면 이미지는 브라우저 set_content 렌더링으로 생성; 실제 서비스 백엔드/API 연동 시험은 포함하지 않음.','pages':pages},ensure_ascii=False,indent=2),encoding='utf8')
(ROOT/'README.md').write_text('''# LAWYGO Atlas — 마케팅 사이트 납품 시안

## 이번 반영
- **LAWYGO PRO (로이고 프로)** — 기존 LAWYGO LITIGATION(송무 프로그램) 명칭 변경
- 다섯 제품: LAWYGO JOURNAL / WIKI / NOTE / PRO / PAN
- PRO 하위 모듈: DESK / CASE / FLOW / WORK / HUB / SMART
- PRO 무료 베타: 구글 계정 로그인, 3~6개월 무료 운영 *예정*, 종료 1개월 전 안내 *예정*
- LAWYGO JOURNAL: 미국·한국 경제, 증권정책, OpenDART, 제도 변화 해설 / 월 2회 무료 뉴스레터
- 기술 출처: shinkangteam/lawygo, shinkangteam/wallpilotpro, shinkangteam/lonexus

## 시작
1. ZIP을 풀고 `index.html`을 브라우저에서 엽니다.
2. `sitemap.html`은 전체 35페이지 안내입니다.
3. `previews/ALL_PAGES_CONTACT_SHEET.jpg`는 모든 페이지 미리보기입니다.
4. `previews/`에 페이지별 첫 화면 PNG가 있습니다. 주요 9개 페이지는 FULL 길이 캡처도 포함됩니다.
5. 정적 HTML/CSS/JS로 제작했고, 실제 데이터/API·Google OAuth·구독 DB·결제·뉴스레터 발송은 **연결되지 않았습니다**.

## 독립 저널과 위키
브랜드 UI/컨텐츠 저작물을 로앤비 사이트에서 복사하지 않고, 법률·경제 리서치 편집구조만 벤치마킹해 제작했습니다. 제시된 기사·판례·변호사 인물은 별도 표시된 목업입니다. AI가 생성한 Hero 이미지를 사용했습니다.

## 기술적 구현/이관 가이드
`INTEGRATION_PLAN.md` 및 `BRAND_ARCHITECTURE.md` 참고.

## 법률 및 브랜드 리스크
- **대법원 사건번호만으로 전체 정보 자동 조회**를 보장하지 않습니다. 검색 시 법원·사건번호·당사자명·인증 절차가 더 필요할 수 있습니다.
- TerraBridge Capital LLC의 델라웨어 등록과 Google 경력 연구원 참여는 사용자 제공 내용입니다. 공식 사이트는 미국 회사 소개를 게시하지만 명칭·주 등록 및 고용관계의 서류 검토 전 확정 문구로 외부 공표하지 마세요.
- 특히 `wallpilotpro` 공개 마케팅 초안은 `Terrabridge Capital Inc.`로 표기하며, 다른 사이트의 `TerraBridge Capital LLC` 표기와 상충합니다. 법인명이 확정되어야 합니다.
- 특허 공개번호 10-2019-0015797과 등록특허 10-2054514는 별개이며 현재 보유·사용 권리와 라이선스 확인이 필요합니다.
- 정식 판매가·구독기간·자동 갱신·환불·베타 데이터 삭제 정책 등 확정 전에는 가정/안내로만 사용합니다.
''',encoding='utf8')
(ROOT/'BRAND_ARCHITECTURE.md').write_text('''# LAWYGO 제품군 네이밍·콘텐츠 정보 구조

## 최상위 제품 (별도 구독과 고객 획득 목적)

| 이름 | 한글 | 문장 | 사업적 역할 |
|---|---|---|---|
| LAWYGO JOURNAL | 로이고 저널 | 경제를 읽는 법률, 제도의 흐름을 보다 | 월 2회 무료 뉴스레터. 미국 경제·증권·정책 변화 및 국내 경제 트렌드를 리걸 마인드로 해석 |
| LAWYGO WIKI | 로이고 위키 | 판례에서 법령까지 이어지는 지식의 지도 | 법률 정보 백과/판례 정보 유료 월 구독 |
| LAWYGO NOTE | 로이고 노트 | 전문지식을 문서로 완성하다 | 판결문/자료 분석, 변호인의견서·전문 서식 초안 월 구독 |
| LAWYGO PRO | 로이고 프로 | 구글 계정으로 시작하는 전문 송무 관리 | 3~6개월 무료 베타, 구독형 전환 예정. 별도 송무 운영 제품 |
| LAWYGO PAN | 로이고 판 | 전문가가 콘텐츠로 신뢰를 만들다 | 구글블로그 변호사 채널 큐레이션 및 상담 연결 (광고 규정 검토) |

## PRO 제품 내부 기능 (독립 서브브랜드 아님)

| 제품 모듈 | 핵심 기능 | 코드 자산 |
|---|---|---|
| LAWYGO DESK | 대시보드/기일/결재 현황 | lawygo 대시보드·stats·deadlines |
| LAWYGO CASE | 사건번호/사건 관리/의뢰인 | lawygo cases·clients |
| LAWYGO FLOW | 기일·일정·전자결재 흐름 | lawygo calendar·approval |
| LAWYGO WORK | 문서·업무·직원·회계 | lawygo staff·finance·document |
| LAWYGO HUB | 사내 메신저/메일/드라이브/보안 ERP | lonexus module-registry / 보안 거버넌스 |
| LAWYGO SMART | 판례 추천/법령·AI 검색/사건 정보 보조 | lawygo AI 법률백과·case_search·doc_summary |

## 콘텐츠 세분류는 별도 유료 브랜드가 아닌 저널 카테고리
- U.S. ECONOMY & MARKETS · SEC/연준·증권제도
- KOREA ECONOMY & DART · 국내 산업·공시·지배구조
- CASE & POLICY REVIEW · 판례·법제도 변화
- THE LEGAL VIEW · 시장 정보의 제도적 해석

## 권장 공개 사이트 메뉴
저널 / 위키 / 노트 / 로이고 PRO / 판 / 구독 안내

**원칙**: `LAWYGO LITIGATION`은 사용하지 않음. 기존 레거시 URL은 `pro/`로 전달. NOTE의 문서 AI와 PRO의 SMART는 문서 작성 주체가 다르므로 제품 설명에 구별해 표시.
''',encoding='utf8')
(ROOT/'INTEGRATION_PLAN.md').write_text('''# LAWYGO 실제 개발 자산 연결 설계 — 구현 및 검증 핸드오프

이 파일은 2026-10-29에 연결된 비공개 GitHub 저장소에서 확인한 소스/개발문서 항목과 마케팅 HTML 사이트의 연결 표입니다. **정적 마케팅 산출물에서 실서비스 백엔드를 호출하지 않습니다.** 데이터베이스, OAuth, 법원 인증키, 운영 URL에 대한 별도 승인·배포 검증이 필요합니다.

## 1. 실제 저장소와 마케팅 페이지

| 원본 | 실제 소스·문서 검토 | 웹사이트 페이지 | 준비해야 할 연결 |
|---|---|---|---|
| `shinkangteam/lawygo` (master) | `src/app/page.tsx`, `src/app/cases`, `docs/planning/legal-encyclopedia-unified-architecture.md`, `docs/scourt-case-search-integration.md`, `docs/qa/final-qa-results.json` | `/pro`, `/wiki`, `/note`, `/pro/beta` | 기존 인증/테넌트/법원조회/백과 APIs를 내부 연동, 실 배포 확인 |
| `shinkangteam/wallpilotpro` (main) | `src/components/modules/dartlab-panel.tsx`, `src/lib/api/dart.functions.ts`, `src/lib/api/news-data.server.ts`, `docs/gtm/01_LANDING_COPY.md` | `/journal`, `/journal/market-intelligence` | OpenDART/뉴스 등 데이터 공급권·출처 정책·캐싱 적용, 편집 파이프라인 구성 |
| `shinkangteam/lonexus` (master) | `src/lib/module-registry.ts`, `docs/ARCHITECTURE-AUDIT.md`, `docs/MODULE-COMPLETION-PLAN.md`, `docs/SECURITY-AUDIT.md` | `/pro/hub`, `/pro/enterprise`, `/pro/work` | Google SSO, 조직 권한, 감사 로그, 사내 메시징·메일 서버 접속 테스트 |

## 2. 서비스 실행과 마케팅 분리

- 제안 구조: `lawygo.com` 마케팅(Next.js/Vercel)와 `app.lawygo.com` 업무 앱(기존 lawygo) 분리, 기업형 `hub`는 내부 인증 전용 경로. 실제 도메인/배포와 DNS는 미확정 예시.
- 마케팅에는 **서버 인증키, DB 키, 법원 조회정보, 의뢰인/사건 정보를 포함하지 않음**.
- Google 로그인: 기존 lawygo 인증 경로/실제 운영 OAuth 환경을 확인하고 메인 CTA만 공식 경로로 보냄. (현재 HTML은 lawygo.com으로 이동)
- Newsletter: 구독동의, 본인 이메일 확인, 구독 해지, 발송 기록, 이중 옵트인 검토 및 대량 발송 시스템 구축.
- PRO: 테넌트 분리, RBAC, 접근로그, 민감자료 암호화·백업, 사건별 분리 권한, 데이터 내보내기, 베타 종료 정책 구현.
- 대법원 연동: `docs/scourt-case-search-integration.md`에 공식 API(승인 필요) 및 웹 조회 링크 두 방식이 문서화됨. 사건번호만으로 자동 기일 조회를 일괄 보장하지 않음.
- Wiki & Note: 문서 OCR, 법령/판례 검색, 근거와 AI 생성 텍스트 구분, 원문 라이선스·업데이트 타임스탬프·출처 링크 필수.
- Journal: 공시(DART), SEC, 미 연준, 공식 정책자료, 데이터 공급업체(AlphaVantage·Yahoo)의 정책·캐시 제한 별도 검토. WallPilot의 투자 신호/매매 자동실행을 저널 기사에서 혼용 금지.
- Enterprise HUB: lonexus 문서에서 일부 iframe/서비스에 외부 URL/토큰 필요, 보안정책과 접근제어가 운영 준비 여부에 따라 다름.

## 3. 출시 전 QA 우선순위

1. 운영 GitHub의 실제 배포 커밋과 현재 Vercel 배포 SHA 대조
2. Google OAuth 신규 계정으로 가입/로그인/로그아웃 성공, 보호된 경로 접근 거부
3. 베타 사건번호 등록, 대법원 조회 링크/공식 API 경로, 기일 확인이 실제 가능한지 계정별 검증
4. 계정 A/B 간 조직/사건/문서 열람 불가 테스트와 보안 로깅
5. DART 뉴스 수집 원문 귀속·기사 업데이트·편집 승인·정정 요청 기능 테스트
6. 제품별 구독 권한, 청구/결제, 쿠키·메일 구독 동의·해지와 수신 거부 테스트
7. 모바일/접근성/Lighthouse/브라우저 호환과 이미지 최적화 수행
8. 개인 고객·법무법인 데이터 관련 이용약관/개인정보처리방침 검토
9. 특허 등록·권리 사용관계, LLC/Inc 법인명/델라웨어 등록, Google 경력 연구진 기술 기여 사실 확인

## 4. 베타 서비스 공식 카피 (사용자 제공 운영 정책)

> **LAWYGO PRO | 구글 계정으로 시작하는 전문 송무 관리**
>
> 누구나 구글 계정을 통해 무료 베타 서비스 이용을 시작할 수 있습니다. 사건번호 등을 등록하고 대법원 나의 사건 검색과 연결해 기일·사건 진행정보를 확인할 수 있습니다. 법원에 따라 당사자명·추가 인증 등이 필요할 수 있으며 자동 조회는 서비스 제공 범위에 따릅니다. 무료 베타는 3~6개월간 운영할 예정이고, 종료일 1개월 전에 별도 안내할 예정입니다. 종료 이후 정식 구독 조건은 사전에 공지합니다.

**문구 공개 전 확인:** 기존 lawygo.com의 공개 유료 요금표와 무료 베타 제공 여부가 충돌하지 않도록 판매조건과 약관을 조정해야 합니다.
''',encoding='utf8')
# Create ZIP with all pages and assets, including page-by-page previews
ZIP=Path('/mnt/data/LAWYGO_PRO_FULL_MARKETING_35PAGES.zip')
with zipfile.ZipFile(ZIP,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for q in sorted(ROOT.rglob('*')):
  if q.is_file():z.write(q,'LAWYGO_PRO_SITE/'+q.relative_to(ROOT).as_posix())
print('ZIP',ZIP,ZIP.stat().st_size)
