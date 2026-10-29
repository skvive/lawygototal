# 신규 API 엔드포인트

| 경로 | 방법 | 목적 |
|---|---|---|
| `/api/google/login` | GET | Google OIDC 로그인 시작 (PKCE) |
| `/api/google/callback` | GET | OAuth state 1회 사용 후 코드 교환 · ID 토큰 검증 |
| `/api/google/connect/blogger` | GET | 로그인 회원이 Blogger 읽기 권한 연결 |
| `/api/google/connect/youtube` | GET | 로그인 회원이 YouTube 읽기 권한 연결 |
| `/api/google/connections` | GET | 연결 상태(토큰 값은 비공개) |
| `/api/google/connections/{provider}` | DELETE | 연결 해제(원본 Google 계정에서 별도 권한 철회 가능) |
| `/api/google/owned/{provider}` | GET | 본인 소유 Google 블로그/업로드 채널 조회 |
| `/api/sync/sources` | GET/POST | 본인 소유 채널 동기화 목록·등록 |
| `/api/sync/sources/{source_id}/run` | POST | 수집 작업 수동 실행 (1분 내 반복 제한) |
| `/api/sync/runs` | GET | 동기화 결과 기록 |
| `/api/note/{post_id}/ai-analyze` | POST | 기밀 문서 전송 동의 후 Gemini 분석 |
| `/api/note/{post_id}/ai-runs` | GET | 본인 노트 분석 기록 열람 |
| `/api/native/queue/{post_id}` | POST | 승인된 게시글 발행 큐 등록 |
| `/api/native/publish/{post_id}` | POST | 기존 LAWYGO 네이티브 게시판에 발행 |
| `/api/native/retract/{post_id}` | POST | 기존 게시판에 발행 취소 전달 |
| `/api/native/outbox` | GET | 관리자 발행 현황 확인 |

요청 헤더: 모든 변경 API에는 v1과 동일하게 브라우저의 `X-CSRF-Token`이 필요합니다. Google OAuth 콜백에는 검증 가능한 `state` 및 PKCE verifier가 필요합니다.

## 참고 URL 및 권한
- Google OAuth: `openid email profile`.
- Blogger: `https://www.googleapis.com/auth/blogger.readonly`.
- YouTube: `https://www.googleapis.com/auth/youtube.readonly`.
- Gemini: `generateContent` 서버 API + 사용자의 명시적 전송 동의.

모든 동기화된 블로그·영상은 우선 **승인 대기**입니다. 관리자 공개 승인 후에도 기존 LAWYGO 네이티브 게시판 발행은 별도 버튼으로 수행합니다.
