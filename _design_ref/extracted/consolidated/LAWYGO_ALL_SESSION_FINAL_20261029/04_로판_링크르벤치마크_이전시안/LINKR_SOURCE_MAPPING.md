# LAWYGO PAN — 소스 벤치마킹 및 통합 대응표

## 실제 조회 결과 (2026-10-29)
- 사용자 지정 `skvive/linkr`: 해당 경로의 GitHub 저장소 응답 404. 읽기 불가. **반영했다고 주장하지 않음.**
- `skvive/linkrcode`: 접근 가능. 실제 앱이 아닌 운영 스크립트·에이전트 설정 중심의 작은 저장소.
- `shinkangteam/linkr`: 연결된 GitHub에서 실제로 조회 가능한 대형 Next.js 앱(3,798 blob 파일). 해당 저장소의 아래 코드를 비교 분석.
- `live.lexid.site` 실배포는 Vercel 프로젝트 `live` / GitHub `shinkang888-code/srocks`로 확인. 소스는 브랜드북 iframe으로, 요청된 Blogger·YouTube 엔진의 존재는 확인하지 못함.

## 반영 경로
| 확인된 Linkr 구조 | LAWYGO PAN 적용 위치 | 상태 |
| --- | --- | --- |
| `lib/feed.ts` 피드 타입 분리 | `contents.html`, `videos.html` 카테고리 카드 | 화면 구조 참고 |
| `components/feed/FeedNlSearch.tsx` 키워드 검색·결과 | `contents.html` 검색·블로그/영상 필터 | JS 독립 재구현 |
| `lib/social.ts` 프로필/관심사/DM | `lawyers.html`, 가상 변호사 프로필, 관심 저장 | UI 패턴 참고 / DM 서버 미연결 |
| `components/social/SnsDiscover.tsx` 프로필 탐색 | 전문 분야·지역·이름 필터 | JS 독립 재구현 |
| `app/api/ads/campaign/route.ts` 광고 세션·가격·멱등성 검증 | 전문가 마케팅·광고 프로그램 미래 설계 | 실서버 미연결 |
| `docs/feed-vnext-poc.md` Editorial/Journal/Clip | 저널형 글·영상 콘텐츠 탐색 | 독자적인 레이아웃 |
| `lib/video.ts` 브라우저 영상 인코딩 | 채널 연동 단계의 원본 영상 업로드 정책 | 데모에 인코딩 이식 없음 |

## API 통합 계약(안)
1. `GET /api/pan/lawyers?practice=&region=&q=` — 검증된 변호사 프로필 목록.
2. `GET /api/pan/content?type=blog|video&q=` — Blogger/YouTube 수집된 콘텐츠.
3. `POST /api/pan/inquiries` — 로그인/비회원 동의 상태 확인, 연락처 보호·스팸 방지·감사 로그.
4. `POST /api/pan/creators/connect` — OAuth/채널 URL 검증 및 권한 확인.
5. `GET /api/pan/analytics` — 로그인 변호사 본인에게만 조회수/클릭수/문의수 제공.
6. `POST /api/pan/ads` — 인증, 서버 가격 확정, 중복결제 방지, 심사 후 게시.
7. Stripe는 `shinkangteam/lexid`의 LAWYGO 전용 결제 PR #14 설계와 연결하되 운영 승인 전 비활성화.

## 실운영 제약
- 본 패키지에 포함된 22페이지는 **정적 사이트 + 로컬 JS UI 시연**입니다.
- Linkr, LAWYGO, Blogger, YouTube의 운영 DB/API 키는 포함되지 않았습니다.
- 법률 광고 규정·변호사 신원 검증·개인정보처리 정책·상담 정보 보안이 우선 필요합니다.
