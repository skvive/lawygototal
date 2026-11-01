# LAWYGO TOTAL — 고객 납품 전 디자인·버튼 QA (2026-11-02)

## 기준과 보호 대상
- 운영: https://lawygo.lexid.site
- 기준 커밋: `master` / `7e863648eccceb9bef04df66d6062402158a54b7`.
- 변경 브랜치: `design/lawygo-delivery-qa-20261102`.
- 공식 로고: 기존 `static/logo.svg` 원본 유지. 고객 데이터, Neon/Auth 설정, 유료 결제 및 Android 소스 변경 금지.

## 실제 관찰한 기존 브라우저 증거
GitHub Actions 성공 실행 `41320328321`의 `lawygo-website-26-screenshots-and-qa` 아티팩트 내 desktop 13장, mobile 13장과 `result.json` 검토. 당시 26/26 HTML 200, 가로 넘침 0, 누락된 IMG 0. 이는 이전 코드 기준이며 금번 수정 완료 증거와 구분한다.
- WIKI 검색 결과·공개 카드의 `href="#"`는 클릭해도 본문이 열리지 않는 실제 UX 결함.
- NOTE 모바일의 워크플로 카드 4개가 과도하게 높고 하단 노트 영역의 밀도가 낮음.
- PRO/WIKI/CHANNEL 상세 페이지는 실무 기능 설명과 이미지 콘텐츠가 상대적으로 부족함.
- JOURNAL 데이터가 비어 있으면 주요 기사 칸이 공란으로 남을 수 있음.
- 공통 푸터의 '운영 배포가 아직 활성화되지 않음' 문구는 사이트 실제 운영 상태와 불일치.

## 이번 프런트 개선
1. WIKI: 빈 링크 삭제, 공개 글 상세 읽기 `dialog`(API `/api/posts/{id}`), 키보드 닫기, 원문 출처 링크 안전 프로토콜, 오류·빈 상태 안내; 검색·카드에 API 제공값을 DOM textContent로 삽입.
2. NOTE: 자료·리서치·비공개 영역 상세카드와 390px/360px 모바일 2열/1열 워크플로 밀도 최적화.
3. PRO: 사건·기일·문서/결재 화면에 개발 로드맵임을 명시한 기능별 상세 설명과 이미지.
4. CHANNEL: 출처 수집 → 편집·검수 → 공개 발행 3단계 콘텐츠 흐름의 자세한 카드.
5. 파트너십·요금·성장 전략·결제: 맞춤형 이미지 배경·카드·표·버튼 반응형 정돈.
6. JOURNAL: 승인 기사 없는 상태의 시각적 안내와 편집 데스크 이미지.
7. 신규 SVG 아트워크 3종: channel, partnership, subscription. 기존 original wiki/note/pro 이미지 유지.
8. 공식 로고·실제 구독 결제 상태 표시 원칙 유지.

## 검증 지침
- GitHub Actions `.github/workflows/lawygo-web-qa.yml`과 `qa/lawygo-browser-qa.cjs`에서 데스크톱(1440), 태블릿(768), 모바일(390), 소형 모바일(360) × 13경로 = **52장** 브라우저 캡처를 수집한다.
- 페이지 200, 가로 넘침, IMG 리소스, JS pageerror, main/h1, label, CTA 높이, 상세카드 3개 표시/미디어 규격, WIKI 모의 공개 본문 열기/닫기, PAN 탭 클릭, 메뉴, 유효성 검사.
- 실제 로그인·실제 고객 DB 쓰기·유료 결제·구글 OAuth는 실행하지 않는다.
- 최종 합격은 새 브랜치의 CI 성공, Vercel Preview READY, 주요 이미지/HTML/health 재조회 후에만 주장한다.
- 스크린샷은 GitHub Actions 아티팩트이며 브라우저 자동화가 확인하지 못한 모든 조합의 수작업 UX 검수는 별도.
