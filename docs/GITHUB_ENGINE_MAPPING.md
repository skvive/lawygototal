# LAWYGO GitHub 연동 검증 및 반영표

조회 저장소: `shinkangteam/lawygo` (`master` 브랜치), 2026-10-29.

| 기존 LAWYGO 코드 | 확인한 기능 | 신규 콘텐츠 엔진 연결 |
| --- | --- | --- |
| `src/lib/boardService.ts` | Supabase boards / board_posts / board_comments CRUD | 채널·위키·판 3개 전용 게시판 식별자 추가 |
| `src/lib/boardBridge.ts` | 네이티브 boardService 변환 계층 | 기존 `/api/board/{slug}`로 게시물 목록·생성·편집·삭제 |
| `src/app/api/board/[boardId]/[postId]/route.ts` | 로그인 후 기존 게시글 CRUD | 변경하지 않고 그대로 사용 |
| `src/app/api/admin/boards/route.ts` | 관리자 게시판 생성·수정·삭제 | 기존 관리자 페이지 `/admin/settings/boards`로 이동 |
| `src/lib/authSession.ts` | HttpOnly HMAC 서명 세션 | 신규 제품 허브에서 기존 세션 재사용 |
| `src/lib/boardApiContext.ts` | 테넌트 관리번호 | 신규 제품 허브에서 기존 테넌트 범위 사용 |
| `src/app/api/ai/legal-encyclopedia/route.ts` | 법률백과 검색·문서 관리 | LAWYGO WIKI 고급 검색 탭 링크 |
| `src/components/board/ai/LegalNotebookWorkspace.tsx` | 비공개 문서/노트 워크스페이스 UI | NOTE는 별도 공개 게시판을 만들지 않고 본 컴포넌트를 사용 |
| `supabase/migrations/20260627000000_native_boards.sql` | 네이티브 게시판 초기 테이블 | 운영 환경 적용 여부 확인 필요 |

## 분리해 납품한 실행형 엔진
- `engine/app.py` FastAPI + SQLite, 13개 기본 게시판, 독립 CRUD·승인·권한·변경 기록·첨부·댓글
- PostgreSQL/Supabase 환경을 요구하지 않으며 개발 테스트에 적합함. LAWYGO 운영 DB와 자동 공유하지 않음.
- 실제 LAWYGO 안에 연동되는 코드는 `integrations/lawygo_native_workspace.tsx`와 `lawygo_native_product_api.ts`에 별도 제공.
- GitHub 기능 브랜치는 PR로 검토, 운영 `master` 변경 전 확인 필요.

## 특히 중요한 권한 경계
- 채널·판은 공개 발행 전 승인 흐름이 필요함. 기본 LAWYGO 네이티브 게시판에는 독립 Python 엔진의 공개 검수 워크플로와 동일한 승인 조건이 내장돼 있다고 단정할 수 없음.
- 위키는 외부에 공개 전 법률 전문가 검수 및 출처가 필요함.
- NOTE는 기밀 법률 문서가 들어가므로 일반 공개 게시판에 저장하지 않음.
- 법률백과 AI/판례 API는 인증·상업적 이용 정책·API 키·DB 설정에 따라 일부 기능이 제한될 수 있음.

## 실서비스 완료까지 남은 작업
1. 운영 Google OAuth 환경에서 제품 허브와 기존 회원 세션 경로 테스트.
2. Supabase `native_boards` 마이그레이션 확인 및 제품별 접근 권한 테스트.
3. PAN/CHANNEL 콘텐츠 승인 워크플로를 기존 게시판에 별도 구현하거나 신규 엔진의 API를 배포해 안전하게 연결.
4. 법률 문서 암호화·테넌트 격리·접근 감사, 법률 전문가 검수.
5. 운영 배포(현재 미배포), 관측 및 장애 대응, 데이터 마이그레이션 계획.
