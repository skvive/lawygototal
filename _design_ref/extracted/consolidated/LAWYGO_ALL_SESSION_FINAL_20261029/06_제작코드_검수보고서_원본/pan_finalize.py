from pathlib import Path
from PIL import Image,ImageOps,ImageDraw,ImageFont
import json,zipfile,hashlib
ROOT=Path('/mnt/data/LAWYGO_PAN_CUSTOMER_SITE');P=ROOT/'previews';D=ROOT/'docs';
fn='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'; fb='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
if not Path(fn).exists():fn='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf';fb=fn
font=lambda z,b=False:ImageFont.truetype(fb if b else fn,z)
layout=[('index','메인'),('lawyers','변호사 검색'),('lawyer-kim','전문가 프로필'),('consultation','상담 신청'),('blog','전문 블로그'),('videos','유튜브 콘텐츠'),('pricing','마케팅 요금제'),('partnership','법무법인 제휴')]
CW,CH=524,360;out=Image.new('RGB',(CW*4+20,CH*2+80),'#edf1f5');draw=ImageDraw.Draw(out)
draw.text((27,18),'LAWYGO PAN  |  CUSTOMER EXPERIENCE · KEY SCREENS',font=font(29,True),fill='#132a42')
for i,(stem,name) in enumerate(layout):
 r,c=divmod(i,4);im=Image.open(P/f'{stem}-desktop.png').convert('RGB');im=ImageOps.fit(im,(CW-22,CH-53),method=Image.Resampling.LANCZOS,centering=(.5,.05));x=c*CW+10;y=r*CH+75
 out.paste(im,(x,y));draw.rounded_rectangle((x,y,x+CW-22,y+CH-53),radius=3,outline='#cad6df',width=3)
 draw.text((x+4,y+CH-47),f'{i+1:02d}  {name}',font=font(19,True),fill='#142d45')
path=Path('/mnt/data/LAWYGO_PAN_DESIGN_PREVIEW.jpg');out.save(path,quality=88)
# All pages: 32 desktop screenshots in a labelled matrix
files=sorted(P.glob('*-desktop.png'));cols=4;tw=330;th=270;head=72;rows=(len(files)+cols-1)//cols
sheet=Image.new('RGB',(cols*tw,head+rows*th),'#f2f5f8');d=ImageDraw.Draw(sheet);d.text((24,15),'LAWYGO PAN · 32 DESKTOP PAGE PREVIEWS',font=font(30,True),fill='#112c43')
for i,p in enumerate(files):
 r,c=divmod(i,cols);x=c*tw+8;y=head+r*th+8
 im=Image.open(p);im=ImageOps.fit(im,(tw-16,th-55),centering=(.5,.05));sheet.paste(im,(x,y))
 d.rectangle((x,y,x+tw-17,y+th-56),outline='#d6dfe5',width=1)
 d.text((x,y+th-46),f'{i+1:02d}  {p.stem.replace("-desktop", "")}',font=font(16,True),fill='#253b50')
sheet.save(P/'ALL_32_DESKTOP_PAGES.jpg',quality=85)
# mobile
files=sorted(P.glob('*-mobile.png'));cols=8;tw=177;th=350;head=65;rows=4
sheet=Image.new('RGB',(cols*tw,head+rows*th),'#f2f5f8');d=ImageDraw.Draw(sheet);d.text((24,10),'LAWYGO PAN · 32 MOBILE PAGE PREVIEWS',font=font(29,True),fill='#112c43')
for i,p in enumerate(files):
 r,c=divmod(i,cols);x=c*tw+6;y=head+r*th+7
 im=Image.open(p);im=ImageOps.fit(im,(tw-12,th-48),centering=(.5,.05));sheet.paste(im,(x,y))
 d.text((x,y+th-41),f'{i+1:02d} {p.stem.replace("-mobile", "")[:15]}',font=font(11,True),fill='#253b50')
sheet.save(P/'ALL_32_MOBILE_PAGES.jpg',quality=85)
(ROOT/'robots.txt').write_text('''# 시연용 콘텐츠 공개 색인 방지. 실데이터 검증·권리 확인 후 변경하세요.\nUser-agent: *\nDisallow: /\n''')
(ROOT/'vercel.json').write_text(json.dumps({'version':2,'cleanUrls':False,'headers':[{'source':'/(.*)','headers':[{'key':'X-Content-Type-Options','value':'nosniff'},{'key':'Referrer-Policy','value':'strict-origin-when-cross-origin'},{'key':'X-Frame-Options','value':'DENY'}]}]},ensure_ascii=False,indent=2))
qa=json.loads((D/'STATIC_AUDIT.json').read_text());screens=json.loads((D/'RENDER_QA.json').read_text());stats={'screenshots':len(screens),'browser_errors':sum(bool(s.get('error')) for s in screens),'javascript_errors':sum(len(s.get('errors',[])) for s in screens),'overflows':sum(bool(s.get('overflow')) for s in screens),'broken_images':sum(s.get('broken',0) for s in screens)}
report=f'''# LAWYGO PAN 고객 납품·한국어 문법·이미지 QA 보고서

**검수일:** 2026-10-29  
**최종 결과:** {qa['pages']}개 HTML, PC·모바일 {stats['screenshots']}개 화면, 이미지 자산 {qa['assets']}개, 내부 HTML 링크 {qa['internal_html_links']}개 검사

## 검수 결과

| 항목 | 결과 |
|---|---|
| HTML 페이지 | {qa['pages']}개 |
| 검수한 한국어 어절(반복 포함) | 약 {qa['korean_wordlike_tokens']:,}개 |
| PC 미리보기 | 32개 |
| 모바일 미리보기 | 32개 |
| PC·모바일 화면 가로 넘침 | {stats['overflows']}개 |
| 브라우저 JavaScript 오류 | {stats['javascript_errors']}개 |
| 이미지 표시 오류(전체 지연 로드 후) | {stats['broken_images']}개 |
| 내부 HTML 링크 경로 검사 | {qa['internal_html_links']:,}개 |
| 누락 내부 파일 경로 | {len(qa['faults'])}개 |
| 인터랙션 테스트 | 변호사 검색·카테고리 필터·블로그 필터·모바일 메뉴·EN 전환·문의 모달 열기/닫기 동작 확인 |

## 한국어 문법·브랜드 표기 수정

- '구글블로그' → '구글 블로그'로 띄어쓰기를 통일하고 '구글 블로그·유튜브'로 병렬 항목 표기 개선
- '계약을 해지하고 싶습니다' 교육용 글에서 추상적인 계약 설명을 용역 계약 예시로 보완
- 변호사/의뢰인의 의사결정 주체를 분명히 밝히는 문장으로 법적 고지 개선
- '맞춤 견적/월'처럼 어색한 표기를 '맞춤 견적 · 협의'로 수정
- 메인 화면에서 존재하지 않는 `stories.html` 링크를 `cases.html`로 교체
- 상세페이지의 중복 H1 제목 6개를 H1/H2 올바른 구조로 수정
- 공개된 실제 변호사 실적처럼 오해하지 않도록 '시연용 가상 인물' 표기를 확인

## 이미지 검수

- 독창적으로 생성한 고해상도 사진형 비주얼을 8개 웹용 WebP로 분리하고 전체 페이지에 적용
- 이미지 자체에는 한글이 들어 있지 않아 AI 자동 글자 생성으로 인한 오타를 회피
- OG 이미지(1200×630)의 한글은 정식 한글 폰트로 직접 조판
- 기존 LAWYGO의 L 및 내부 사각형 모티프를 재해석하여 SVG/PNG/ICO 파비콘 제작
- 32개 전 페이지의 PC·모바일 화면을 실제 HTML 렌더링으로 캡처

## 고객 관점 2차 개선

1. 변호사 찾기에 검색어·분야·지역 필터와 결과 없음 안내 도입
2. 공개 시연임을 메인·프로필·법무법인·사례·영상에 반복 안내
3. 상담 문의가 실제 예약이나 발송 완료로 오해되지 않도록 버튼·메일 동작 및 정책 문구 수정
4. 휴대전화 390px에서 가로 넘침 0건으로 반응형 정리
5. 메인 → 변호사 상세 → 상담 신청, 블로그 → 관련 정보, 법무법인 → 제휴의 이동 동선 구성
6. 영어 토글은 주요 UI 직접 전환, 전체 자동 번역은 온라인 Google Translate 스크립트를 선택적으로 불러오도록 설계

## 확인하지 못한 내용 / 운영 전 필요한 작업

- 외부 로톡 사이트는 공개 페이지 내용을 기반으로 주요 페이지 유형을 조사했으나 브라우저 직접 스크린캡처는 환경의 접속 제한으로 수행하지 못했습니다. 따라서 '로톡의 모든 동적 URL을 일일이 캡처'했다는 의미는 아닙니다.
- `live.lexid.site` 현재 배포 소스의 Blogger·YouTube 연동 기능은 확인되지 않았습니다. 이 납품물에는 UI와 연동 가이드만 포함됩니다.
- 변호사 등록 실명·자격 검증, 개인정보 서버 저장, 실제 법률상담 예약, 운영 결제, YouTube 재생, Blogger 피드 동기화는 아직 연결되지 않았습니다.
- 무료 Google Translate 스크립트의 네트워크 접근과 자동 번역 품질은 외부 서비스 의존으로 실서비스 도메인에서 검증이 필요합니다. 정적 HTML의 KO/EN 토글은 확인했습니다.
- 약관/개인정보처리방침은 법무 검토용 초안으로 표시합니다.

## 인수인계 경로

- 메인 페이지: `index.html`
- 도메인 권장: `pan.lawygo.com`
- 주요 이미지: `assets/*.webp`
- OG: `assets/og-image.jpg`
- 로고: `assets/lawygo-mark.svg`, favicon 3종
- 메뉴 전수: `sitemap.html`, `docs/PAGE_INVENTORY.md`
- 소스 연구: `docs/SOURCE_AND_DESIGN_AUDIT.md`
- 연동 구현: `docs/INTEGRATION_GUIDE.md`
'''
(D/'QA_AND_CHANGELOG.md').write_text(report,encoding='utf-8')
manifest=[]
for p in sorted(ROOT.rglob('*')):
 if p.is_file():manifest.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
(D/'MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
out=Path('/mnt/data/LAWYGO_PAN_32PAGES_FINAL_DESIGN.zip')
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for p in sorted(ROOT.rglob('*')):
  if p.is_file():z.write(p,'LAWYGO_PAN_CUSTOMER_SITE/'+str(p.relative_to(ROOT)))
with zipfile.ZipFile(out) as z:
 bad=z.testzip();assert not bad
print('ZIP',out,'SIZE_MB',round(out.stat().st_size/1024**2,2),'ENTRY_COUNT',len(z.namelist()),'QA',stats)
