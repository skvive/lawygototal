# LAWYGO Atlas — 마케팅 사이트 납품 시안

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

## LAWYGO PAYMENT 추가
- payment.html 은 서비스별 결제 마케팅 UI. 유료 버튼은 https://lexid.site/lawygo/payment#lawygo-... 으로 이어짐.
- 백엔드 변경은 shinkangteam/lexid PR #14 (draft) 에 있음. 기존 /terra 운영 결제와 분리.
- LAWYGO_BILLING_ENABLED=true 가 설정되기 전까지 신규 결제 불가.
- LAWYGO PRO는 무료 베타 동안 결제 불가.
- 가격은 제안액이며 최종 가격·약관·판매자 검증 필요.
