# 로이고토탈 / 실제 브라우저·Android 독립 검수 보고서

- 기준일: 2026-11-01
- 운영주소: https://lawygo.lexid.site
- 운영 원본: master / dd8e839ce696770feee4dcefce54f38ab129c1d7
- QA 변경 브랜치: qa/lawygo-accessibility-android-20261101
- 이번 작업 원칙: 운영 인증/Neon DB, 실제 고객 데이터, 결제 거래를 변경하지 않음.

## 1. 실제 웹 브라우저 검증
Vercel Sandbox 환경에서 Chromium + Playwright를 실행하여 운영 화면 13개 경로를 PC(1440×900)와 모바일(390×844)에서 총 26회 렌더링함.

- 화면 페이지 HTTP: 26/26 정상
- 가로 넘침, 깨진 이미지, 스크립트 uncaught error: 검사 시점에 0건
- 모바일 메뉴 펼침/접힘, 뉴스레터 잘못된 이메일 검증, 로그인 필수 입력 검증: 통과
- 내부 상대경로 링크 확인: 13/13 HTTP 200
- HTML/CSS 배치 스크린샷 및 상태 JSON: GitHub Actions workflow `lawygo-web-qa.yml`, Run 41320328321 이상. 최신 성공 실행별 Artifacts에 26개 원본 JPG + result.json이 저장됨.
- 별도 브라우저 인증 계정 없이 관리자 로그인 이후 페이지 기능, 권한 분기, 고객 데이터 동작은 검증되지 않음.
- CI에서 사용하는 데이터베이스는 운영 Neon이 아닌 격리 SQLite이므로 저널 실콘텐츠·동적 데이터 유무/표시는 다를 수 있음.

## 2. 접근성 및 레이아웃 수정
- 기본 Atlas 페이지 10개에 `main` 랜드마크를 추가.
- JOURNAL에 스크린리더용 명시적 `h1` 추가.
- PAN 문의 입력 성함/이메일/문의 `label for`를 정확히 연결.
- 모든 주요 공개 페이지의 소형 문구, 링크, 다크 카드 CTA의 대비를 실제 axe-core WCAG 2.0/2.1 AA 자동감사 결과 기반으로 높임.
- 최초 axe 테스트: 다수 색상 대비 지적; 1차 수정 후 20/26 페이지에 일부 지적; 2차 수정 후 2/26 PAN 화면의 빈 상태·푸터만 남아 해당 부분도 수정.
- 최종 axe 완전 통과는 마지막 수정 버전의 재검사 결과로 판정해야 함.
- 자동화가 검출하지 못하는 실제 얼굴 크롭, 영상/동적 데이터, 모든 키보드/스크린리더 경로와 고객 경험은 인적 검수를 계속 필요로 함.

## 3. 격리 백엔드와 Android 소스 검증
- FastAPI 독립 회귀 pytest: 92 passed, 104 warnings (대부분 FastAPI/asyncio deprecation), SQLite.
- Android FastAPI 모바일 통합 테스트: 16/16 통과(실제 Google 토큰 대신 테스트용 모의).
- Android 네이티브 정적 계약 테스트: 18/18 통과.
- Android Suite Debug APK GitHub Actions 빌드: 성공 Run 41319410262. APK 아티팩트 이름 `lawygo-total-suite-debug-apk`.
- AGP 8.13.2/compileSdk36과 충돌한 Compose BOM 2026.09 → 2025.10, Activity Compose 1.13 → 1.11, Kotlin metadata가 2.4인 GoogleID 1.2.1 → 1.2.0으로 호환 버전을 고정.
- 빌드 완료/에뮬레이터 설치/실기기 설치/릴리스 서명/Google Play 업로드는 서로 별개의 QA 단계다. 실제 기기와 Google Play 출시 검증은 아직 승인하지 않음.

## 4. 운영 배포 게이트
- GitHub PR에 Android 및 Web QA 결과와 스크린샷을 보존.
- 프리뷰가 READY이고 Web smoke/접근성 검수가 통과하기 전까지 운영 master 병합·프로덕션 배포 금지.
- 병합 뒤 반드시 `lawygo.lexid.site` 와 `/api/health` 재검증하여 `storage:neon-postgres` 확인.
- 실제 구글 로그인/과금/발송 작업은 실계정·승인된 테스트용 계정/테스트 결제 환경 없이 무단 실행하지 않음.
