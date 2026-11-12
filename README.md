# LAWYGO CMS v3 — 2026-10-29

## 설치 · 실행

1. Python 3.11+을 설치하고 `LAWYGO_ENGINE` 폴더에서 `pip install -r requirements.txt` 를 실행합니다.
2. `.env.example`을 `.env`로 복사하고 데이터 경로·API 환경변수를 설정합니다. 실제 고객 데이터가 담긴 기존 DB를 그대로 덮어쓰지 마세요.
3. `python bootstrap_admin.py --email admin@yourcompany.com --password "<직접 정한 12자 이상 비밀번호>"`로 최초 계정을 만듭니다.
4. Windows `RUN_WINDOWS.bat` 또는 macOS/Linux `RUN_LINUX_MAC.sh`를 실행하고 `http://127.0.0.1:8018/dashboard`를 엽니다.
5. 관리자 사이드바 **광고·마케팅·운영 분석**에서 캠페인, 변호사 인증 심사, 게시판 드래그앤드롭, 연동 상태를 확인합니다.
6. 테스트 종료 후에는 테스트 데이터베이스를 삭제하고 운영 전용 데이터베이스를 별도로 생성합니다.

## Android 네이티브 패키지

`android_native/LAWYGO_ANDROID_NATIVE_20261031/`에 첨부된 Android 네이티브 소스와 FastAPI 연동 패키지 전체를 보존했습니다. 패키지의 `README_FIRST_KO.md`는 빌드·실기기 검증에 필요한 납품 안내이며, Android SDK/JDK와 서명 키가 준비된 환경에서 별도로 빌드합니다.

## Neon DB · Neon Auth

운영 Vercel 환경은 `DATABASE_URL`에 Neon pooled PostgreSQL 연결 문자열을 주입해 사용합니다. Managed Neon Auth(Better Auth)는 `lawygototal-rerand` 기본 브랜치에 프로비저닝되어 있으며 `https://lawygo.lexid.site`가 trusted domain으로 등록되어 있습니다. 실제 연결 문자열과 비밀값은 Vercel 환경변수에만 저장하고 Git에는 넣지 않습니다.

## 현재 포함된 기능

- 4개 제품, 게시판/게시글/댓글 CRUD, 이력, 승인·복원, PDF·이미지 첨부, 비공개 노트 분리.
- 기존 v2: Google OAuth, Blogger 및 YouTube 읽기 동기화, Gemini 원문 동의형 분석, LAWYGO 네이티브 게시판 발행 어댑터.
- **v3 추가**: 광고 캠페인 CRUD·정렬, 공개 피드의 광고 분리, 마케팅 이벤트 집계, 변호사 등록 심사, 서버 간 구독 권한 이벤트 HMAC·중복방지, 게시판 순서 저장.
- **v5 운영 기준**: 월 1회 무료 뉴스레터의 이메일 확인·무료 수신거부, TLS SMTP HTML+텍스트 발송, 관리자 발행 승인, 100명/회 안전 상한.
- **v3 추가**: 뉴스레터 가입 폼·분야별 콘텐츠 피드, SNS OG 이미지·favicon, PC/모바일 반응형 드래그앤드롭 대시보드.

## 반드시 구분해야 할 검증 범위

- **검증됨**: 로컬 FastAPI + SQLite 실제 HTTP 요청/저장, 53개 Python 자동 테스트, 15개 서버 HTTP 업무 흐름, 브라우저로 렌더링한 정적/모의 API 화면과 클라이언트 DnD.
- **검증되지 않음**: `lawygo.com` 실제 운영 배포, 결제기관/Google API/Gemini 실제 계정 응답, Supabase/Neon 프로덕션 마이그레이션, 외부 Google 로그인·Blogger·YouTube 실제 토큰 발급, 실제 SMTP로 고객에게 발송, 실제 고객 개인정보 취급 E2E.
- Playwright의 localhost 및 file:// 네비게이션이 실행 환경에서 보안 차단되어 UI는 `page.set_content()` + 모의 API로 시각/동작 검증했습니다. 실제 운영 서버에서의 브라우저 E2E 테스트는 별도 수행해야 합니다.
- 기존 `shinkangteam/lawygo`의 통합 PR #37은 검토용이며 이 독립 CMS의 전체 DB/회원 상태가 실제 운영과 하나로 합쳐진 것은 아닙니다.

## 운영 투입 순서

1. Staging에 복제 DB 구성 → 마이그레이션 및 개인정보 접근권한 검수 → 독립 CMS의 테넌트/계정 식별자 대조.
2. 운영 Google OAuth 승인, Blogger API·YouTube API 사용량 및 갱신 토큰 암호화 검증.
3. Gemini API와 법률정보 처리 위탁·개인정보보호 조건, 비공개 원문 전송 동의 및 감사 기록 검증.
4. 결제 시스템의 고객/구독 식별자와 본 엔진 HMAC 이벤트를 서버 간 연결하고, 환불·만료·과금 실패·웹훅 역순 처리 시험.
5. 뉴스레터 SMTP 설정 및 발신 도메인 SPF/DKIM/DMARC, 사전 동의·수신거부 시험 후 발송 허용.
6. WAF, 익명 이벤트 레이트리밋, 스팸 방지, 백업/복원, 취약점 스캔, 접근성 검수 후 운영 릴리스.

## 중요한 규정

- 광고 콘텐츠는 `광고`로 표시합니다. 유료 노출은 변호사 전문성/상담 성과 순위가 아닙니다.
- 변호사 등록번호는 운영자가 실제 자료로 대조한 뒤 승인합니다. 자동 확인 결과로 오인시키지 마세요.
- 이용자의 상담 정보, 본인 파일, 법률 노트 등은 공개 피드로 보내지 않습니다.
- 운영 마케팅 효과 수치는 쿠키 기준 중복을 줄인 참고용 이벤트로, 확정 상담 건수·매출이 아닙니다.

## 데이터 보관

- 개발용 SQLite는 동작 검증용입니다. 다수 운영자·고트래픽 상용 운영에는 기존 LAWYGO Supabase/Neon과의 단일 원장·권한 통합이 필요합니다.
- 첨부파일과 백업에 대해 저장 시 암호화·수명 주기·삭제 요청·접근 기록을 적용하세요.
- `.env`, 업로드 디렉터리, 운영 DB는 반드시 Git 추적과 웹 공개 경로에서 제외하세요.

## LAWYGO JOURNAL 월간 뉴스레터 v5

- 편집자·관리자: `/newsletter/studio`에서 미국 경제/한국 법률정책 뉴스(각 최대 5건) 작성, 초안 저장, 출처 URL 검증, 반응형 HTML 이메일 미리보기.
- 관리자: 미리보기 및 수신 대상 확인 후 매달 단 1회 승인. 중복 등록 차단, 수신 확인 완료 주소만 대기열 편성.
- 발송: 서버에서 한국시간 10:00~14:45에 15분 간격으로 예약 대기열을 20건씩 처리. 보안 크론 인증 필요.
- 보안: 운영 `CRON_SECRET`, SMTP 계정 설정 및 `LAWYGO_NEWSLETTER_ALLOW_SEND=true` 세 조건 전에는 실제 메일 발송 안 함. 기본적으로 발송 잠김.
- 수신거부 및 결과 조회: `/static/newsletter-admin.html`. 저널 `/journal`에서 이메일 동의 구독 신청.
- 테스트: `python -m pytest -q tests/test_newsletter_monthly_v5.py tests/test_newsletter_v3.py`.
- 실 SMTP 발송, 실제 수신거부 메일클라이언트 UX, 대량 고객 구독자 운영 테스트는 운영 설정 후 별도 검증.
