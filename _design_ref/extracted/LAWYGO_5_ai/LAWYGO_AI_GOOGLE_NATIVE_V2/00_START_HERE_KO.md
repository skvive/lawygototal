# LAWYGO AI · Google · Native Board 통합 실행 패키지 v2

**수록 기능:** 로이고 채널 · 위키 · 판 · 노트 / 게시판 CRUD / Google 회원 로그인 / 기존 LAWYGO 회원 식별 / Blogger 동기화 / YouTube 동기화 / 법률 AI 분석 / LAWYGO 운영 DB 게시판 단방향 발행 브리지.

## 폴더
- `LAWYGO_ENGINE/`: FastAPI 기반 실제 실행형 CMS와 Google·AI·DB 동기화 코드.
- `LAWYGO_ENGINE/static/`: 관리자 대시보드, Google 연결·승인 대기·AI 동의 화면.
- `LAWYGO_ENGINE/tests/`: 38개 독립/모의 API 자동 테스트와 브라우저 정적 렌더링 테스트.
- `github_integration/`: 기존 LAWYGO Next.js의 `site_users` 조회/네이티브 게시판 수신 API와 SQL 마이그레이션 원본.
- `design_references/`: 기존 이 세션의 채널·위키·판·노트 HTML 시안 모음.
- `preview/`: 로컬 렌더링한 PC·모바일 관리자 페이지 캡처.
- `docs/`: 설정, 보안, QA 보고서.

## 로컬 Windows 실행
1. **Python 3.11 이상** 설치.
2. `LAWYGO_ENGINE/RUN_WINDOWS.bat` 실행. 최초 계정 생성 시 임의의 12자 이상 관리자 암호를 설정.
3. `http://127.0.0.1:8018/dashboard` 접속.
4. 새 관리자 → 게시글 등록·수정·삭제·복원 및 승인 기능 사용.

## Google·AI 활성화
1. Google Cloud 프로젝트를 만들고 **Blogger API v3, YouTube Data API v3**를 활성화.
2. OAuth 동의화면에 `openid`, `email`, `profile`, `blogger.readonly`, `youtube.readonly` 권한을 설정하고 승인·테스트 사용자 설정을 확인.
3. Google OAuth 웹 애플리케이션 `Client ID` / `Client Secret` 발급. Redirect URI를 `http://localhost:8018/api/google/callback`(로컬) 또는 배포된 HTTPS `/api/google/callback`으로 등록.
4. `.env.example` 값들을 안전한 서버 환경 변수로 등록. **파일에 실제 비밀키를 넣어 다시 공유하거나 GitHub에 커밋하지 말 것.** `LAWYGO_TOKEN_ENCRYPTION_KEY`는 Fernet 키를 생성해 보관.
5. Google 로그인을 한 뒤 관리자 화면 **Google·AI·운영 게시판 연동** → Blogger 또는 YouTube 연결 → 소유 채널 선택 → 게시글 수집. 수집 글은 `승인 대기`로 저장됨.
6. `sync_worker.py --once` 또는 작업 스케줄러의 **6시간 주기 실행**으로 자동 재수집. 명시적 읽기 권한을 가진 채널만 처리.
7. Gemini API 키 등록. NOTE 화면에서 사용자가 외부 AI 전송 동의를 확인해야 분석 기능 실행 가능.

## 기존 LAWYGO 운영 계정·DB 연결
- GitHub 기능 브랜치: `shinkangteam/lawygo` → `feature/lawygo-content-products-20261029`; 검토 PR: https://github.com/shinkangteam/lawygo/pull/37
- `src/app/api/integrations/cms/identity/route.ts`: 확인된 Google `sub`를 기존 `site_users.google_id`와 매칭해 승인된 LAWYGO 회원과 소속관리번호 반환. 고객의 이메일만으로 권한 승인하지 않음.
- `src/app/api/integrations/cms/route.ts`: **승인된 콘텐츠만** `board_posts`로 idempotent 발행/수정·삭제.
- `supabase/migrations/20261029000000_cms_native_sync.sql`: 브리지 `external_source/revision` 컬럼 추가 (운영 적용 전 백업 필수).
- CMS에 `LAWYGO_NATIVE_BRIDGE_URL`, `LAWYGO_NATIVE_IDENTITY_URL`, `LAWYGO_NATIVE_BRIDGE_SECRET`(32자 이상)을 설정하고, 원본 Next.js 서버에 동일한 `LAWYGO_NATIVE_BRIDGE_SECRET`, 고정된 `LAWYGO_NATIVE_MANAGEMENT_NUMBER`를 설정.
- **실서비스 회원만 허용**할 때 `LAWYGO_REQUIRE_NATIVE_MEMBERSHIP=true`로 설정. 다른 테넌트의 글은 현재 CMS 로그인 세션에서 노출되지 않음.

## 반드시 구분할 부분
- **실제 로컬 DB·CRUD 작동 및 요청 검증:** 실행·테스트 완료.
- **Google OAuth/Blogger/YouTube/Gemini/LAWYGO 원격 Supabase 실제 운영 연결:** 서버 자격증명 및 운영 배포가 제공되지 않아 **모의 API·로컬 계약 검증만 완료**. 프로덕션 성공으로 주장하지 않음.
- **운영 원본 DB 병합/스키마 변경:** 미수행. GitHub PR은 검토용 초안이며 `master`는 미변경.
- 이 패키지는 단일 인스턴스 SQLite 개발·스테이징용입니다. 고객 기밀 법률 문서를 운영하려면 서버 저장소 암호화·백업·삭제 정책·접근제어·법률 전문가의 결과 검수, 멀티인스턴스 관리형 DB 확장이 필요합니다.
