# LAWYGO JOURNAL — WSJ형 인터넷 신문 기획 (2026-10-29)

## IA (메뉴)

| 메뉴 | URL | 역할 |
|------|-----|------|
| **저널** | `/journal` | WSJ형 편집면 · RSS+편집 콘텐츠 |
| **채널** | `/channel` | 미디어 데스크 허브 → `/p/channel` CMS |
| **위키** | `/p/wiki` | 백과·판례 |
| **판** | `/p/pan` | 변호사 블로그 |
| **노트** | `/p/note` | 비공개 연구 |
| **PRO** | `/pro` | 로이고 프로 송무(랜딩) |
| **관리자 로그인** | `/dashboard` | Neon DB 세션 · CMS |

## 디자인 토큰 (WSJ 벤치마크)

- Masthead: 검정 utility + 센터 로고 `LAWYGO` / `JOURNAL`
- Headline: Libre Baskerville + Noto Serif KR
- Body: Inter + Noto Sans KR
- Layout: Lead + 2-column (US | Korea) + rail (snapshot, newsletter)
- 이미지: `/static/img/journal/hero-markets.jpg`, `hero-korea.jpg` (AI 생성)

## 콘텐츠

- **API** `GET /api/journal/feed` — RSS(연합·한경·BBC·NPR 등) + channel 게시글
- 원문은 외부 링크 · 요약만 표시 (저작권)
- 뉴스와이어: 공식 RSS 확인 후 `journal_feed.FEEDS`에 추가

## 시안 파일

- `docs/siain/journal-home-mockup.jpg` — 전체 홈 WSJ comp
- 생성 소스 hero: `static/img/journal/*.jpg`

## 채널 vs 저널

- **저널**: 신문 · 와이어 헤드라인 · 편집국 tone
- **채널**: 영상/칼럼/승인 게시판 · `/p/channel` operational UI

## Phase 2

- Neon Auth SSO (현재: dashboard 자체 로그인)
- 게시글별 media 썸네일 on journal lead
- `/p/channel` → 저널 편집국 글 deep link modal
