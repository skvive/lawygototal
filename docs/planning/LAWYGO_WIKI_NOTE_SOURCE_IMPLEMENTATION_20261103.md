# LAWYGO TOTAL — WIKI·NOTE 통합 플랫폼 디자인 및 원본 코드 대조 (2026-11-03)

## 원본과 구현 기준
- 통합 포털 저장소: `skvive/lawygototal` `master` 기준 `19c847d392cf6b5319d06713248991968e01f3cd`.
- 원본 고급 엔진: 비공개 `shinkangteam/lawygo` `master` 트리 `40cda21d7347217ec8674b5a4588534bc7af0473`.
- LAWYGO 공식 `static/logo.svg` 수정 금지, 기존 FastAPI/Neon/사용자·결제 데이터 보존.
- 원본 SaaS 확인: `https://lawygo.vercel.app/board/ai/legal_encyclopedia`, `legal_notebook`, `ai_search`, `doc_summary`, `doc_draft`, `law_search` 모두 HTTP 200 HTML 응답. **응답 200만으로 로그인 후 AI 기능 사용 가능 여부는 확인할 수 없다.**

## 원본 소스 분석
| 원본 구성요소 | 근거 코드 | 현황 |
|---|---|---|
| 법률백과 검색·온톨로지·벡터·순위·모범답안 | `src/components/board/ai/LegalEncyclopediaWorkspace.tsx`, `src/app/api/ai/legal-encyclopedia/route.ts` | 인증 필요, Supabase 테넌트와 프로젝트 기반 |
| 카테고리·메인 프레임·다중창·프로젝트 | `src/components/board/ai/encyclopedia/*` | React/Next 기반, FastAPI 단일 파일로 직접 복사 불가 |
| 법률 노트북 (업로드 PDF, 소스 선택, 소스 기반 Q&A) | `src/components/board/ai/LegalNotebookWorkspace.tsx` | OCR와 AI API, 브라우저 저장 데이터 사용 |
| AI 검색 | `src/components/board/ai/AiSearchWorkspace.tsx` | AI 프로바이더 설정 필요 |
| 판례 추천·법률검색·OCR 요약·서면 작성 | `src/lib/boardConfig.ts`, `src/app/board/ai/[featureId]/page.tsx` | 6+ 기능, 인증·서버 권한에 의존 |
| 백과 프로젝트·산출물 | `docs/planning/legal-encyclopedia-unified-architecture.md`, `src/app/api/encyclopedia/projects/route.ts` | 프로젝트/Drive 연계, 별도 DB와 테넌트 사용 |

## 이번 구현 범위(기능 오인 금지)
1. `static/platform-switcher.js/css`: 14개 공개·CMS HTML에 5개 플랫폼 공통 이동 버튼 추가. 홈 및 서로 다른 저널/PAN/CMS 스타일에 일관된 1단계 내비게이션 제공.
2. `static/wiki.html`: 법률백과 리서치 콘솔, 분야별 검색 단축, 공개 검색 결과(기존 FastAPI `/api/wiki/search`), 고급 백과 엔진의 **외부 새 탭 이동**. 실제 백과 AI 분석을 현 포털에서 수행한다는 뜻이 아님.
3. `static/note.html`: 3단 문서 작업 데스크; 사건 메모/증거 정리/법률 리서치 임시 템플릿, 글자 수·복사·TXT 다운로드·초기화 제공. 자동 저장이나 백엔드 전송 없음. 상단 5개 고급 AI 도구는 원본 SaaS 라우트로 링크하며 별도 로그인 필요.
4. `static/portal-workspaces.css`: 데스크톱·태블릿·모바일 디자인, 법률 문서 이미지, 독자적 카피, 키보드 포커스·터치 44px·가독성.
5. `static/note-page.js`: 개인노트 목록에서 타이틀 HTML 삽입을 제거하고 인증·빈 상태 안내 보강.
6. 새 이미지 생성 없이 기존 저장소의 법률백과/노트 AI 그래픽과 편집실 사진을 실제 페이지 배경·콘텐츠로 배치. 별도 AI 생성 디자인 콘셉트는 운영 원본 자산으로 자동 적용되지 않음.

## 원본 엔진 직접 이식 대신 단계별 통합을 택한 이유
- 원본은 Next.js + Supabase 기반 인증·테넌트와 별도 AI 프로바이더 권한·OCR 저장소를 사용함.
- 통합 포털은 FastAPI + Neon, CMS 권한 모델이 다름.
- 단순 CORS 프록시/공유 API 키/로그인 쿠키 복사로 이식하면 사용자 데이터·프롬프트·법률 원문이 누출될 수 있음.
- 현재 단계: **이동/탐색/임시 문서 편집** 기능은 구현; 고급 AI 작업은 **원본 엔진 새 탭 링크로 기존 인증 유지**.
- 다음 통합 단계(별도 명시적 설계 및 테스트): 신뢰 가능한 OIDC 인증 교환, 권한/테넌트 매핑, 사용자별 엔진 API 어댑터, 감사 로그, OCR 전송 동의, DB 분리 및 통합 테스트. 사용자 요청 없이 원본 인증/DB 변경 금지.

## 검수 게이트
- 13개 주요 라우트 × 데스크톱 1440, 태블릿 768, 모바일 390, 소형 모바일 360 = 52화면 Chromium screenshot.
- 공통 플랫폼 5개 버튼 표시, 위키 6개 검색 주제 클릭, NOTE 임시 템플릿과 초기화 및 원본 SaaS 링크.
- 페이지 HTTP 200, 이미지 로드, 가로 넘침 0, JS 예외 0, 입력 레이블, 접근성 기본 계약.
- 실제 로그인, AI 응답 정확도, PDF 업로드, 전자결제 및 프로덕션 개인정보 조회는 미실시.
