# LAWYGO PAN — 반응형 브랜드·변호사 마케팅 UI 데모

## 시작
1. `index.html`을 Chrome/Edge로 열어 전체 기능을 둘러봅니다. 정적 호스팅(Vercel 등)에 배포할 수 있습니다.
2. 공개 전 `noindex` 제거, 사이트 주소 및 실제 사업자 정책 확인, 변호사 자격 증명, 데이터 연동이 필요합니다.
3. 모든 사진은 본 세션에서 AI로 생성한 가상 장면 및 인물입니다. 실제 변호사라고 소개하지 마세요.

## 기능
- 변호사 이름·분야·지역 클라이언트 필터, 관심 저장, 페이지 공유
- 상담·제휴 문의: 서버 저장 없이 이메일 클라이언트의 초안 열기(`mailto:`). **접수 성공과 동일하지 않음**
- Blogger 및 YouTube URL 연결·로컬 저장, 영상 ID가 있는 경우 `youtube-nocookie.com` 임베드 미리보기
- KR/EN 주요 문구 전환 + 구글 번역 위젯이 허용되는 브라우저에서 나머지 페이지 번역 시도. 외부 서비스 미지원 시 일부 문단은 한국어 유지
- 파비콘·Apple 아이콘·Open Graph 이미지 포함

## `live.lexid.site` 검증
Vercel `live` 프로젝트 배포의 연결 소스는 `shinkang888-code/srocks`입니다(2026-10-29 확인). 내용은 The Rocks Pie Company 브랜드북 iframe으로서 Blogger·YouTube 소셜 엔진이라는 증거가 없습니다. 이 프로젝트는 모듈을 이식했다고 주장하지 않습니다.

## Linkr 소스 반영
요청 경로 `skvive/linkr`는 연결된 GitHub에서 404로 반환됩니다. 접근 가능한 `shinkangteam/linkr`의 `lib/feed.ts`, `lib/social.ts`, `components/feed/FeedNlSearch.tsx`, `components/social/SnsDiscover.tsx`, `app/api/ads/campaign/route.ts`, `docs/feed-vnext-poc.md`를 읽고 피드·프로필·콘텐츠 검색·모듈 구분·광고 심사 구조를 **정보 설계에 참조**했습니다. 해당 비공개 소스 코드는 복사하거나 실서버에 연결하지 않았습니다. `skvive/linkrcode` 역시 발견되지만 앱 본체가 아니라 설치·도구 유틸리티입니다.

## 배포·실구현 체크리스트
- [ ] 운영 도메인 `pan.lawygo.com` DNS·Vercel 배포 및 SSL 확인
- [ ] 회원 인증·변호사 자격 확인과 데이터베이스
- [ ] Google Blogger 공개 RSS / Atom 서버 파서 및 갱신 캐시·원문 출처
- [ ] YouTube Data API / 허용된 임베드, 콘텐츠 권한 확인
- [ ] 상담 접수 API, 동의·암호화·보존 기한·스팸 방지·변호사별 할당
- [ ] 광고·구독 상품 Stripe 연동 및 정산(실결제 미구현)
- [ ] 프로필·상담의 사실적 검증, 광고 규정 및 개인정보처리방침 검토
- [ ] 실제 Google Translate 서비스 허용 여부 및 다국어 SEO 확인
- [ ] 샘플 프로필/성과 수치 제거, 메타 robots의 `noindex` 변경

## 출처 및 차별점
- 로톡 공개 사이트의 홈, 변호사, 로펌, 상담사례, 변호사포스트, 판례돋보기, 뉴스, FAQ를 정보 구조 참고(원문·이미지·코드 무단 복제 없음)
- LAWYGO의 독립 해석: **전문가가 만든 블로그·영상 콘텐츠 → 프로필 → 상담 문의** 흐름을 핵심 전략으로 설계
