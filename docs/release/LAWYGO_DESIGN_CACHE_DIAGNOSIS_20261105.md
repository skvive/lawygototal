# LAWYGO 디자인 업데이트 미반영 대응 — 2026-11-05 (Design Refresh 3)

## 원인과 검증 범위

1. GitHub `master`와 Vercel 운영 배포 SHA는 기존 조사에서 동일했고, `lawygo.lexid.site` 도메인은 해당 프로젝트에 연결되어 있다. 따라서 **GitHub 미배포로 단정하지 않는다**.
2. 최초 버전에서 HTML/CDN 캐시는 `s-maxage=30`, 정적파일은 `s-maxage=120, stale-while-revalidate=30`을 사용했다. `20261105-cachefix2`는 이를 0초 재검증으로 수정했다.
3. 그러나 13개 HTML의 대부분의 CSS/JS 링크는 여전히 `/static/x.css` 등 **고정된 URL**이었고, 다음 배포에서도 모바일 인앱 브라우저·중간 캐시가 이전 자산을 재사용할 여지가 있었다.
4. Atlas, Premium, Mobile Visual, Refined, Delivery, Design Fix 등의 CSS가 중첩돼 `!important` 규칙의 우선순위가 복잡하다. 이 문제는 시각적 오버라이드 검증 대상이며 네트워크 캐시 문제와 구분해야 한다.
5. 이 도구 환경에서는 실제 운영 URL의 HTTP 응답 헤더가 DNS/웹 접근 제한으로 확인되지 않았다. **코드 + Vercel 관리 API + CI 확인을 실제 HTTP 헤더 검증과 혼동하지 않는다**.

## 이번 조치 (20261105-designrefresh3)

- `static/design-release.json` 단일 버전 원천 생성.
- `scripts/bump_design_release.py --apply`: 13개 HTML 페이지에 존재하는 **모든 CSS/JS 링크**를 버전 표기로 갱신하고 `vercel.json`의 X-Lawygo-Design-Release 헤더를 동일한 버전으로 설정한다.
- `scripts/bump_design_release.py --check`: 최신 버전이 아닌 페이지/헤더가 남아 있으면 배포 전 실패한다.
- HTML 13개 라우트 `Cache-Control: private, no-store, max-age=0`으로 변경; 크로스 세션의 오래된 페이지 문서 캐시 방지. `/static/*`는 `s-maxage=0`, `must-revalidate` 유지.
- 인증 API, RSS, sitemap, robots, 데이터베이스, 원본 이미지 및 결제 로직은 수정하지 않는다.
- GitHub CI에 manifest-URL 일치 테스트를 추가하고 기존 52뷰포트 Playwright 검수 및 소스 계약 테스트 유지.

## 후속 디자인 배포 표준 절차

1. `static/design-release.json`의 `release`를 고유 버전(예: `20261106-refined4`)으로 증가.
2. `python scripts/bump_design_release.py --apply` 실행.
3. `python scripts/bump_design_release.py --check` 및 `python -m unittest discover -s tests -p 'test_design_release_contract.py' -v` 실행.
4. QA 52컷 및 통합 기능 테스트, PR CI 녹색, GitHub squash merge, Vercel production SHA 일치 확인.
5. 운영 도메인에서 `/static/design-release.json`, HTML의 `meta[name=lawygo-design-revision]`, 응답 `X-Lawygo-Design-Release`와 `Cache-Control`의 최종 값을 대조한다.
6. Android WebView/인앱 브라우저에서 기존 탭을 닫고 새 탭으로 재접속해 앱 내부 캐시 가능성을 분리 진단한다.

## 롤백

작업 직전 기준 SHA: `0158907e4726004a0a58ff71748f0ea246e66dc4`.
기존 스크립트/파일 삭제 없이 안전한 후속 병합으로 전환한다.
