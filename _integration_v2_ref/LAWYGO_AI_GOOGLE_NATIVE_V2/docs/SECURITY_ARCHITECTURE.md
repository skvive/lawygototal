# LAWYGO 신뢰 경계와 보안 설계

## 현재 구현
- `lawygo_cms_session`: HttpOnly/SameSite=Lax. HTTPS 배포 시 `LAWYGO_SECURE_COOKIES=true` 필수.
- 쓰기 API: CSRF 헤더/쿠키 확인. Google OAuth state DB 단일 사용·10분 만료·PKCE S256.
- OIDC: Google이 서명한 ID 토큰 검증, `iss`, `aud`, `email_verified`, `sub` 확인 (운영 테스트는 별도).
- 로컬 계정이 이미 동일 이메일을 점유한 경우 Google 로그인만으로 탈취 불가.
- Blogger `blogger.readonly`, YouTube `youtube.readonly` 최소 권한. 채널 등록 전에 `mine=true` / `users/self/blogs`로 소유관계 확인.
- refresh/access token은 Fernet으로 암호화한 형태만 저장. 환경변수 비밀키 필수, 연결 해제로 로컬 토큰 삭제.
- 수집한 콘텐츠는 자동 공개하지 않음. 관리자 승인·광고 표시 확인 후 게시.
- 법률 AI는 NOTE 소유자만, 동의 전 전송 차단. 원문에 없는 법령·판례를 만들지 말도록 프롬프트 설계 + 반환 출처 ID 검사. 결과 정확성은 보장할 수 없음.
- 원본 LAWYGO 회원 조회와 게시판 발행은 서버-서버 Bearer 비밀키(32자 이상), HTTPS, 고정 테넌트, 허용된 상품 유형만 처리.
- 기존 LAWYGO native bridge의 `cms_external_source` 고유 인덱스로 중복 등록 차단, revision을 통한 구버전 쓰기 방지.

## 운영 전 필수 확인
- 실제 OAuth 동의화면 검증과 권한 심사 및 이용자 데이터 정책.
- 법률문서·계약서·의뢰인 이름·연락처의 **서버 저장 데이터 암호화**, 유출 감사, 주기적 백업, 로그 최소화, 보관기한·삭제권 절차.
- 서명된 조회 토큰, 감사 로그, 누적 rate limit, 세션 관리, HTTPS, IP 제한, WAF.
- SQLite는 고가용성/다중 인스턴스 운영 저장소로 권장하지 않음. 현 브리지는 승인된 **공개 게시글만** 기존 Neon/Supabase 게시판으로 보내는 구조이며 CMS 내 모든 데이터를 동일 DB로 이관하는 작업은 별도 단계.
- AI를 법률 결론으로 자동 제공하거나 가짜 판례번호를 발행하지 않음. 법률 전문가 검수 전 사용자에 확정 조언 제공 금지.
- Google 콘텐츠 API 호출 Quota·429/5xx 재시도와 장애 복구, 운영자 권한 교체 시 연결 토큰 폐기 테스트.
