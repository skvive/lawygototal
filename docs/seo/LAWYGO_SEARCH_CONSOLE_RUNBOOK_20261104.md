# LAWYGO Search Discovery / Search Console 출고 대장
기준: 2026-11-04 KST
운영 URL: https://lawygo.lexid.site
소스: skvive/lawygototal
SEO 작업 브랜치: seo/lawygo-sitemap-rss-20261104

## 1. 경로·공개 정책
- 사이트맵 인덱스: https://lawygo.lexid.site/sitemap.xml
- 공개 페이지 12개: https://lawygo.lexid.site/sitemap-pages.xml
- 승인된 LAWYGO 편집 콘텐츠: https://lawygo.lexid.site/sitemap-articles.xml
- Googlebot 발견용 표준 규칙: https://lawygo.lexid.site/robots.txt
- RSS 구독: https://lawygo.lexid.site/rss.xml
- 편집국 자체 기사: https://lawygo.lexid.site/journal/articles/{public_post_id}
- 관리자, API, 미승인 글, 비공개 NOTE, 타사 RSS 원문은 사이트맵에 넣지 않음
- canonical 기준은 유일하게 lawygo.lexid.site; lawygo.com 도메인은 별도 운영 정책 결정 전까지 이 사이트맵에 넣지 않음

## 2. 운영 배포 전 자동 게이트
- [x] 기존 사이트맵·로봇·RSS 파일 미존재 확인 (2026-11-04, 작업 당시 master 코드)
- [x] 코드 작성 및 테스트 추가: 6개 SEO 계약 테스트
- [ ] 최신 브랜치 GitHub Actions 전체 성공 (결과 확인 후 완료 처리)
- [ ] PR 병합 후 Vercel production SHA 일치 확인
- [ ] 운영 5개 URL 요청 시 200 및 올바른 MIME type 확인
- [ ] 운영 12개 canonical 링크, RSS link, OG 정보, 모바일 가로 스크롤, 404 검수
- [ ] 루트/저널/공개 기사 응답에 인덱싱 방지 X-Robots-Tag가 없는지 확인
- [ ] RSS 항목의 실제 공개 글 URL 응답 200, 미공개 글은 404 확인

## 3. Google Search Console 등록 (실제 계정 권한 필요)
Google 공식 자료: https://developers.google.com/search/docs/crawling-indexing/sitemaps/build-sitemap
Search Console: https://search.google.com/search-console

- [ ] 소유권: 기존 `sc-domain:lexid.site` 속성 또는 `https://lawygo.lexid.site/` URL 접두어 속성의 사용자 권한 확인
- [ ] 기존 검증 토큰/DNS TXT와 충돌하지 않도록 소유권 인증 상태 검증
- [ ] 정확한 운영 sitemap URL `https://lawygo.lexid.site/sitemap.xml` 제출
- [ ] RSS `https://lawygo.lexid.site/rss.xml`은 자체 발행 글이 있을 때 피드로 추가 제출 고려 (선택)
- [ ] 색인 > 페이지: robots 차단, 발견됨/크롤링되지 않음, canonical 충돌, 404 상태 확인
- [ ] URL 검사: 홈, /journal, /p/wiki, /p/note, /p/pan, /pro와 실제 기사 1건 검사
- [ ] 사이트맵 보고서: 제출 URL, 최근 읽은 시각, 처리 상태, 발견된 URL 수 기록
- [ ] 데이터 기반 7일/28일 성과 검수: 검색 유입, CTR, 노출, 색인 제외 이유
- [ ] 등록 완료 증거(속성 ID, Search Console 상태/날짜/스크린샷)를 운영 대장에 추가

**중요:** robots.txt에 Sitemap을 두는 것은 Google에게 발견 경로를 알리는 것이며, Search Console에서 사이트맵 제출이 완료되었다는 뜻은 아니다. Google 색인 여부도 보증하지 않는다. 자체 Googlebot 유사 크롤러를 개발하거나 Google의 일반 웹페이지를 Indexing API에 강제 제출하지 않는다.

## 4. 개선 전략 / 장애 대응
1. 한 사이트당 canonical URL 한 개를 유지하고, 301/308 리다이렉트·실운영 앨리어스가 충돌하면 URL 통합 정책을 먼저 정한다.
2. 실제 공개 글이 늘어나면 `sitemap-articles.xml` 페이징을 도입한다. 초기 구현은 최신 공개 글 1,000건까지 노출한다.
3. 편집 콘텐츠는 사용자·개인정보 없는 승인된 본문만 외부 공개한다. 법률/금융 고위험 분야는 작성자·검수 일자·원문 출처를 검증하고, 광고는 명시한다.
4. 브라우저 렌더에서 링크가 JS 전용이면 크롤러가 발견하기 어려우므로 상세 문서로 향하는 HTML a 링크를 우선한다.
5. 뉴스레터 이메일 폼과 RSS 구독은 별개의 기능이다. RSS 등록은 메일 발송을 의미하지 않는다.
6. 보안은 robots.txt로 확보되지 않는다. 법률 노트·결제·고객 정보는 서버 인증/인가로 별도 보호한다.

## 5. 운영 소유자 확인 필요
- Google Search Console 소유권 인증·제출 권한: 확인 필요
- 네이버 서치어드바이저 등록: 별도 요청 범위
- lawygo.com / lawygo.lexid.site 중 영구 주도메인: 운영 정책 확인 필요
