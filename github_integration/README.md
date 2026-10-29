# LAWYGO CMS ↔ 운영 Next.js 브리지 (ZIP5 / PR #37)

이 폴더는 `shinkangteam/lawygo` 기능 브랜치에 복사해 배포하는 참조 코드입니다.

| 파일 | 용도 |
| --- | --- |
| `identity_route.ts` | CMS Google 로그인 시 `site_users.google_id` 매칭 → `LAWYGO_NATIVE_IDENTITY_URL` |
| `native_route.ts` | 승인 콘텐츠 idempotent upsert/delete → `LAWYGO_NATIVE_BRIDGE_URL` |
| `LAWYGO_NATIVE_CMS_BRIDGE.sql` | Supabase `board_posts` external_source/revision 컬럼 |

운영 `master` 미병합. CMS 측 구현은 `integrations_v2.py` + `/dashboard` 연동 패널.
