# LAWYGO AI · Google 엔진 (ZIP5 · LAWYGO_5 AI엔진)

정본: `LAWYGO_AI_GOOGLE_NATIVE_V2/` (`_design_ref/extracted/LAWYGO_5_ai/`).

| 기능 | 구현 (lawygototal) |
| --- | --- |
| **법률 AI 분석** | `integrations_v2._gemini_analyze` · `POST /api/note/{id}/ai-analyze` (`consent:true` 필수) · PDF pypdf 발췌 · `source_ids` 서버 검증 · `ai_analysis_runs` 감사 |
| **Blogger 동기화** | `blogger.readonly` OAuth · `/api/google/connect/blogger` · 소유 블로그 검증 · `_sync_source` · SHA256 `content_hash` 중복 스킵 · 변경 시 `status=pending` |
| **YouTube 동기화** | `youtube.readonly` · 업로드 플레이리스트 ID · 영상 메타 수집 · 신규 글 `pending` · PAN `shorts` 게시판 |

## 관리 UI

- `/dashboard` → **Google · AI · DB 연동**: 기능 표(`#aiFeatureGrid`), OAuth 카드, 소유 채널 등록, **지금 수집** / **전체 채널 지금 수집**
- NOTE 편집: **원문 발췌**(로컬) · **AI 분석**(목록) · 모달 내 **Gemini 동의 체크** + 실행 · **최근 분석** 이력 버튼
- 승인: 사이드 **승인 대기** → 검수 후 **승인** (자동 공개 없음)

## API 요약

| Method | Path | 설명 |
| --- | --- | --- |
| GET | `/api/google/login` | Google OIDC 로그인 |
| GET | `/api/google/connect/{blogger\|youtube}` | 읽기 권한 연결 |
| GET | `/api/google/owned/{provider}` | 본인 블로그/플레이리스트 목록 |
| POST | `/api/sync/sources` | 동기화 채널 등록 (소유권 재검증) |
| POST | `/api/sync/sources/{id}/run` | 수동 수집 |
| POST | `/api/sync/run-all` | 전체 강제 수집 |
| GET | `/api/cron/google-sync` | Cron (Bearer `LAWYGO_CRON_SECRET`) |
| POST | `/api/note/{id}/ai-analyze` | Gemini (동의 body) |
| GET | `/api/note/{id}/ai-runs` | 분석 이력 (요약) |
| GET | `/api/note/{id}/ai-runs/{run_id}` | 분석 상세 JSON |
| GET | `/api/integrations/hub` | 연동 상태 통합 |

## 환경 변수

`.env.example` 참고: `GOOGLE_*`, `LAWYGO_TOKEN_ENCRYPTION_KEY`, `GEMINI_API_KEY`, `GEMINI_MODEL`, `LAWYGO_CRON_SECRET`, (선택) `LAWYGO_NATIVE_*`.

## GitHub 운영 허브 (PR #37)

- `github_integration/identity_route.ts` — Google `sub` → `site_users`
- `github_integration/native_route.ts` — 승인 콘�ents CMS upsert
- `github_integration/LAWYGO_NATIVE_CMS_BRIDGE.sql` — external_source/revision

CMS Neon/SQLite 엔진과 Supabase 허브는 **별 DB**. 브리지는 스테이징에서만 검증.

## 로컬

```powershell
cd lawygototal
python sync_worker.py --once
pytest tests/test_integrations_v2.py -q
```

## 배포

https://lawygo.lexid.site/dashboard — Vercel env 설정 후 Google Cloud Redirect URI에 `https://lawygo.lexid.site/api/google/callback` 등록.
