# LAWYGO 디자인 캐시 교정 (20261105-cachefix2)

## 원인
- GitHub master SHA와 Vercel 운영 배포 SHA는 일치하므로 배포 누락으로 단정할 수 없음.
- 기존 vercel.json /static/* 자산은 CDN s-maxage=120 + stale-while-revalidate=30, 13개 HTML은 s-maxage=30.
- 전 페이지 디자인 revision 메타가 20261104-ui1에 고정되어 새 버전 식별이 어려움.
- 과거 Premium/Refined/Delivery CSS와 최종 DesignFix/Integration CSS가 공존해 !important 우선순위 별도 검수 필요.

## 수정
- 13개 HTML과 /static/* 모두 public, max-age=0, s-maxage=0, must-revalidate로 revalidate, stale-while-revalidate 제거.
- 13개 HTML와 정적 자산에 X-Lawygo-Design-Release 응답 헤더 20261105-cachefix2 추가.
- 13개 HTML의 메타 및 마지막 디자인 CSS/통합 CSS URL에 버전 쿼리 적용. WIKI wiki-ui2 식별자는 보존.
- robots.txt, sitemap, rss, 로그인, 데이터베이스, 파일 저장 API 수정 없음.

## 검증
- CI: qa/lawygo-visual-cache-audit.py, tests/test_edge_speed.py, tests/test_five_service_integration.py, 52개 Playwright 캡처.
- 배포 후 /journal 응답 Cache-Control 및 X-Lawygo-Design-Release, CSS 응답 헤더를 확인.
- 사용자 기기의 브라우저 캐시/웹뷰 장기 캐시는 도구에서 확인 불가. 최신 CSS URL은 버전 변경으로 새 리소스 요청됨.
- 롤백 기준 master SHA 0d18ee43e26133f3996dad092d7be718ee46a9d0.
