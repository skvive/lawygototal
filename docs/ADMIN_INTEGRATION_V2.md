# 관리자 대시보드 · Google/AI V2 반영 (2026-10-29)

정본 ZIP: `LAWYGO_AI_GOOGLE_NATIVE_INTEGRATION_V2_20261029.zip`

## 기획 요약 (mockup → 구현)

| V2 기능 | 백엔드 | 대시보드 UI |
|--------|--------|-------------|
| Google OAuth · Blogger/YouTube | `integrations_v2.py` | 연동 패널 · 소유 채널 · 동기화 채널 |
| 승인 대기 워크플로 | sync → `posts.status=pending` | KPI · 승인 대기 필터 · 일괄 수집 후 안내 |
| Gemini 법률 AI | `/api/note/{id}/ai-analyze` + 동의 | NOTE 행 · AI 분석 버튼 |
| 운영 DB 브리지 | `/api/native/publish` | 공개 글 · 운영 게시판 발행 |
| 6시간 자동 수집 | `sync_worker.py` · `GET /api/cron/google-sync` | 상태 카드 · Cron env 안내 |
| 통합 허브 API | `GET /api/integrations/hub` | KPI 하단 스트립 + 연동 패널 카드/테이블 |

## 운영자 체크리스트

1. Vercel: `GOOGLE_*`, `LAWYGO_TOKEN_ENCRYPTION_KEY`, `GEMINI_API_KEY`(선택), `LAWYGO_NATIVE_BRIDGE_*`(선택)
2. Cron: `LAWYGO_CRON_SECRET` + Vercel Cron Authorization `Bearer <secret>`
3. `/dashboard` → **Google·AI·운영 게시판 연동** → Blogger/YouTube 연결 → 채널 등록 → **지금 수집**
4. **승인 대기**에서 검수 후 **승인** → PAN/채널 공개 → (선택) **운영 게시판 발행**

## 로컬 worker

```powershell
cd lawygototal
python sync_worker.py --once
python sync_worker.py --loop
```
