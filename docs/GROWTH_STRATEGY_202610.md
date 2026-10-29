# LAWYGO 성장 전략 및 개발 로드맵 (2026-10)

정본 입력: 시장조사·마케팅·서비스 기획·기술 고도화 제안 (2026년 10월).

## 포지셔닝

**LAWYGO — Legal Intelligence & Growth Platform**

법률 지식 → 콘텐츠 → 신뢰 → 비즈니스 연결. 단순 변호사 광고가 아닌 경제·법률 정보, 전문가 콘텐츠, 법률 AI 업무 도구, 고객 연결 통합.

공개 페이지: `/strategy` · 브랜드 홈 `/` hero 반영.

## P0–P2 ↔ 코드 매핑

| 우선 | 영역 | lawygototal 구현 | 남은 운영 과제 |
| --- | --- | --- | --- |
| P0 | 회원·DB·구독 통합 | Neon/SQLite CMS, `growth_entitlements`, billing webhook, PR #37 `github_integration/` | Supabase 단일 DB, Google SSO ↔ site_users |
| P0 | 변호사 인증·광고 심사 | `lawyer_verifications`, admin 수동 승인, `is_sponsored` + 캠페인 게이트 | 법률 검토된 광고 상품 문구 |
| P1 | Blogger·YouTube | `integrations_v2` sync → `pending`, `sync_worker.py` | 운영 OAuth·Cron |
| P1 | 전환 분석 | `growth_events`, `/api/growth/pan-dashboard`, PAN `pan-growth-events.js` | 자연/유료 유입 분리(UTM Phase 2) |
| P2 | 경제법률·영문 | Journal/Wiki 콘텐츠 구조 | EN locale, B2B |

## 서비스별 로드맵 (기획 → 구현 상태)

| 서비스 | 권장 기능 | 현재 |
| --- | --- | --- |
| CHANNEL / JOURNAL | 출처 검증, 편집 승인, 월 2회 뉴스레터 | `/journal`, `newsletter_v3`, CMS 승인 |
| WIKI | 개정 이력, 판례 그래프, 검수 | `/p/wiki`, CMS wiki boards — 그래프·이력 Phase 2 |
| NOTE | 사건별 격리, AI 근거, 버전 | `integrations_v2` Gemini+consent, revisions — Word/PDF export Phase 2 |
| PRO | 기일·결재 | `/pro` 베타 페이지 — PRO 엔진 별도 |
| PAN | 인증, 분석, 캠페인, 문의 | 인증 API, growth 캠페인, `pan_inquiries`, 퍼널 대시보드 |

## PAN 마케팅 퍼널 (실装)

| 이벤트 | 의미 |
| --- | --- |
| `impression` | 카드 노출(클라이언트 1회/세션) |
| `content_open` | 콘텐츠 클릭 |
| `profile_open` | 프로필 카드 노출/보기 |
| `consult_click` | 상담 CTA 클릭 |

API: `GET /api/growth/pan-dashboard` (본인 PAN 게시글 + `pan_inquiries`).

**LAWYGO Verified**: `lawyer_verifications.status=approved` → PAN 프로필 배지. 국가기관 인증 아님.

## 마케팅 4단계 (실행)

1. **MOU 파일럿** — `/partnership`, 목표 10~20 법무법인(실적 아님)
2. **콘텐츠 부담 최소화** — Google sync + 원문 링크·요약(중복 게시 지양)
3. **뉴스레터** — 매월 1·15일 제안, KISA 광고성 메일 동의·수신거부 (`newsletter_v3`)
4. **무료→유료** — Journal 무료, Wiki/Note/PAN 구독 (`/pricing`, Stripe PR #14 미배포)

## 수익·규정 (기획 원칙)

- 정액 프로필·콘텐츠·지면·분석 구독 권장
- 사건 소개·성사 건당 수수료 구조 지양 (변호사법·대한변협 규정 검토 필수)
- AI 생성물: AI기본법 투명성 — NOTE/Gemini UI에 동의·비자문 고지

## 90일 로드맵

| 기간 | 실행 | 완료 기준 |
| --- | --- | --- |
| 1~30일 | DB·Stripe·인증·보안 | 권한·결제·CRUD 운영 검증 |
| 31~60일 | Google sync·PAN 대시보드·MOU | 실채널·승인·이벤트 데이터 |
| 61~90일 | Wiki/Note 심화·뉴스레터·유료 실험 | 검수·전환 측정 |

KPI 파일럿: 법무법인 10~20, 프로필 30~60, 콘텐츠 120~200, 뉴스레터 6회 — **검증 목표치**.

## 아키텍처 (통합 계정)

```
Google OAuth + 회원 ID + 요금제 + 권한
  → CHANNEL/JOURNAL | WIKI | NOTE/PRO | PAN
  → 공통 감사·공개/비공개 검색 분리
```

- NOTE/비공개: `product=note`, `visibility=private`, AI `consent` — PAN/Wiki 공개 인덱스 제외
- CMS ↔ Supabase: `LAWYGO_NATIVE_*` 브리지

## 최우선 투자 3가지 (기획 = 개발 우선순위)

1. 통합 회원·DB·권한 안정화  
2. PAN 마케팅 자동화·성과 분석 (본 문서 + `/dashboard` growth)  
3. WIKI + NOTE 신뢰 AI (출처 검증·격리)

## 참고 URL (외부)

- Google 검색/AI Overview: developers.google.com 검색 중심 가이드  
- 변호사 광고: koreanbar.or.kr  
- AI 개인정보: pipc.go.kr  
- 광고성 이메일: spam.kisa.or.kr  
