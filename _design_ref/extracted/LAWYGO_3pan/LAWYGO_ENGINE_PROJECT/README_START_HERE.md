# LAWYGO CHANNEL · WIKI · PAN · NOTE — 실행형 콘텐츠 운영 엔진

**납품일:** 2026년 10월 29일  
**버전:** 1.0.0 검증용 패키지  
**대상:** Windows / macOS / Linux (Python 3.11 이상)

## 1. 먼저 실행하기

Windows: `01_ENGINE/LAWYGO_ENGINE/RUN_WINDOWS.bat` 더블 클릭. Python 3.11 이상을 설치하고 처음 실행할 때 관리자 이메일과 12자 이상 비밀번호를 생성합니다. 설치에는 pip 인터넷 접속이 필요합니다. 실행 후 **http://127.0.0.1:8018** 에 접속합니다.

macOS·Linux: `cd 01_ENGINE/LAWYGO_ENGINE && bash RUN_LINUX_MAC.sh`.

기본 관리자 비밀번호나 실제 회원 데이터는 ZIP에 포함하지 않습니다. 초기 데이터베이스는 최초 실행 시 자동 생성됩니다.

- 홈: `/`
- 콘텐츠 대시보드: `/dashboard`
- 채널: `/p/channel`
- 위키: `/p/wiki`
- 판: `/p/pan`
- 노트: `/p/note`
- API 문서: `/api/docs`

## 2. ZIP 폴더 구성

| 폴더 | 내용 |
| --- | --- |
| `01_ENGINE/LAWYGO_ENGINE` | 실행형 FastAPI 서버, SQLite 저장, 관리자 대시보드, 게시판·게시글·댓글·첨부·버전 관리, 테스트 |
| `02_GITHUB_INTEGRATION` | 기존 shinkangteam/lawygo 모듈 대응표, native Next.js 연동 파일, PR 정보 |
| `03_DESIGN_REFERENCES` | 기존 세션의 LAWYGO 35페이지 및 LAWYGO PAN 60페이지 디자인·이미지 소스 (별도 정적 시안) |
| `04_QA_SCREENS` | 실제 HTML/CSS 기반 PC·모바일 시안 렌더 이미지. 데이터 표의 수치는 화면 검사용 예시 |
| `05_REPORTS` | 테스트 결과와 보안·운영 전 검증 항목 |

## 3. 실제로 구현한 기능

**공통 게시판 CMS**: 채널 3개, 위키 3개, 판 4개, 노트 3개 — 총 13개 기본 게시판 생성. 관리자 게시판 추가·편집·삭제·복원, 게시글 신규 생성·수정·삭제(소프트 삭제)·복원, 낙관적 버전 충돌 방지, 공개 승인, 검색, 댓글, 수정 이력, 파일 업로드/열람, 감사 기록, 통계.

**채널**: 기사·영상·칼럼 링크 콘텐츠, 공개 승인 후 게시.  
**위키**: 검증된 판례·법령·백과 콘텐츠의 공개 검색 API.  
**판**: 변호사 프로필·구글블로그·유튜브 주소 저장, 광고 명시, 로그인 계정의 동의형 상담 문의와 비공개 받은 편지함. **실제 YouTube/Blogger API 자동 수집은 없음.**  
**노트**: 사용자 전용 비공개 노트, PDF·이미지 첨부, 업로드 PDF/본문의 텍스트 발췌(스캔 OCR 아님), 법률 문구 빈도 표시. **생성형 법률 AI 분석은 기존 LAWYGO 엔진으로 별도 연결해야 함.**

**역할**: 관리자 / 편집자 / 기고자 / 열람자. 인증은 로컬 계정·비밀번호(Argon2)로 실행되며 **운영 LAWYGO의 Google 로그인과 자동 통합되지 않습니다.** 

## 4. 운영 LAWYGO GitHub 연결

- 소스 확인: `shinkangteam/lawygo` (기본 브랜치 `master`).
- 추가 기능 브랜치: `feature/lawygo-content-products-20261029`.
- PR: https://github.com/shinkangteam/lawygo/pull/37
- 변경: `src/lib/boardConfig.ts`에 채널·위키·판 신규 네이티브 게시판 추가, `/workspace/products` 기존 인증 기반 제품 허브, `/api/workspace/products` 접근상태 API.
- 기존 게시판 CRUD·법률백과·법률 노트북은 LAWYGO 원본 코드 자체를 재사용합니다.
- **PR은 초안이고 운영 master에 병합/배포되지 않았습니다.** 해당 브랜치의 운영 DB/권한/Google OAuth E2E는 검증하지 않았습니다.
- **독립 실행형 SQLite CMS와 LAWYGO 운영 Supabase DB 간 데이터 동기화는 포함하지 않았습니다.** 운영 서비스 단일 DB 구조를 결정한 후 데이터 마이그레이션 또는 API 브리지를 구현해야 합니다.

## 5. 검증 결과

- pytest 19건 통과 (사용자 인증, CSRF, 역할, 게시판/게시글 CRUD·복구, 승인/버전 충돌, 비공개 노트, 파일, 위키 검색, 판 문의함 포함).
- 실제 Uvicorn HTTP 테스트 통과: 로그인 → 등록 → 수정 → 공개 → 삭제 → 복구 → 로그아웃.
- 대시보드 JavaScript 구문 검사 통과.
- HTML/CSS 기반 정적 PC/모바일 렌더링에서 가로 넘침 0. 단, 관리 브라우저 정책이 localhost와 file URL을 차단하여 브라우저 E2E는 미수행. *시안의 관리자 수치는 예시값*.
- ZIP 압축 무결성 검사 및 SHA-256 매니페스트 생성.

## 6. 정식 운영 전 필수 작업

1. HTTPS, 안전한 세션 쿠키 옵션(`LAWYGO_SECURE_COOKIES=true`), reverse proxy 및 콘텐츠 보안 정책, 요청량 제한, CSRF/Origin 허용 정책 검증.
2. 독립형 SQLite 대신 조직 정책에 맞는 관리형 DB/백업/마이그레이션, 다중 인스턴스 및 멀티테넌트 설계.
3. 실제 Google OAuth·회원 권한·구독 권한 연동, 파일 바이러스 검사와 저장소 분리.
4. 변호사 등록 검증, 광고 심사, 민감 사건·의뢰인 정보 보호, 개인정보 보유기간/삭제 요청 대응.
5. Blogger/YouTube 동기화, 이메일·안심전화, 전문가 AI 문서 분석(법령·판례 출처 검증), 실제 결제.
6. staging 환경에서 GitHub PR #37 빌드/타입 검사, 원본 DB와 레거시 게시판 회귀 시험 후 승인/배포.

**보안 안내:** 소스와 테스트 샘플에는 실제 사용자 비밀번호, Stripe 키, Google OAuth 시크릿, Supabase 서비스 키가 없습니다. 테스트용 자료와 가상 이미지 인물은 실제 변호사를 뜻하지 않습니다.
