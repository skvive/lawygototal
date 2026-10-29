# LAWYGO CMS v3 엔진 (ZIP4 · LAWYGO_4 세션및 기타자료)

정본 아카이브: `LAWYGO_V3_FULL_RELEASE/LAWYGO_ENGINE/` (로컬 `_design_ref/extracted/LAWYGO_4_engine/`).

ZIP의 HTML·CSS 관리자 화면은 **디자인 검수용 예시 KPI**이며, `lawygototal` 배포본은 **FastAPI + Neon/SQLite API 실데이터**를 표시합니다.

## 제품별 핵심 기능 (ZIP4 표)

| 서비스 | 구현 |
| --- | --- |
| LAWYGO CHANNEL | 뉴스·칼럼·영상 게시글 작성·편집·공개 승인 · `/journal`·RSS 연동 |
| LAWYGO WIKI | 법률백과·판례·법령 게시판 · 승인 정보 검색 · `/api/wiki/search` |
| LAWYGO PAN | 프로필·블로그·YouTube · 광고 표시 · `/api/pan/inquiries` |
| LAWYGO NOTE | 비공개 노트 · 첨부 · PDF 발췌 · (동의 시) Gemini |

## 공통 엔진 (백엔드)

- 게시판 CRUD · soft delete · 복원
- 게시글 CRUD · revisions · 댓글 · media upload
- audit log · 역할(admin/editor/contributor/viewer) · CSRF 세션
- Growth v3 · Newsletter v3 · Integrations v2 (Google OAuth·네이티브 발행 브리지)

관리 UI: `/dashboard` — `static/dashboard.html` · `dashboard.js` · `style.css`

- KPI · 게시글 목록: `/api/stats` · `/api/posts`
- 편집 모달: 수정 이력(`/api/posts/{id}/revisions`) · 댓글 CRUD
- 제품 카드 그리드: ZIP4 기능 표 (`#engineProductGrid`)

## GitHub LAWYGO 운영 허브

- 매핑: `docs/GITHUB_ENGINE_MAPPING.md`
- PR: [shinkangteam/lawygo #37](https://github.com/shinkangteam/lawygo/pull/37) — Supabase 네이티브 게시판·세션·테넌트 재사용 (master 미병합)
- 브리지 참조: `integrations/lawygo_native_workspace.tsx` · `lawygo_native_product_api.ts`
- NOTE는 공개 게시판 대신 기존 비공개 노트 워크스페이스 연결 전제

## lawygototal vs ZIP4 엔진

로컬 `app.py`는 ZIP4 `LAWYGO_ENGINE/app.py`보다 **앞서 있음** (저널 feed, PAN API, cron, native publish 등). ZIP4는 독립 SQLite 데모·53 테스트 포함.

## 운영 전 검증 (미완)

1. Neon `DATABASE_URL` · Vercel env
2. Google OAuth (`/api/google/login`) · PR #37 세션 공유
3. Supabase `native_boards` 마이그레이션 · `/api/native/publish` 아웃박스
4. 법률 데이터 검수·테넌트 격리·감사 정책

## 로컬 실행

```bash
cd lawygototal
python bootstrap_admin.py --email admin@example.com --password 'your-12-char-pass'
uvicorn app:app --reload
# http://127.0.0.1:8000/dashboard
pytest -q
```

## 배포

- Repo: `skvive/lawygototal` → https://lawygo.lexid.site
- `.vercelignore`: `_design_ref/`, `_integration_v2_ref/`
