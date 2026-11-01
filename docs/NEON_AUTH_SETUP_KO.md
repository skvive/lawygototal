# LAWYGO Neon DB · Neon Auth 운영 설정

현재 배포 대상은 Neon 프로젝트 `lawygototal-rerand`의 기본 브랜치입니다.

- DB: `DATABASE_URL`에 Neon pooled PostgreSQL URL을 Vercel Production/Preview 환경변수로 설정
- Auth: Managed Better Auth가 같은 브랜치에 프로비저닝됨
- Trusted domain: `https://lawygo.lexid.site`
- Auth base URL과 JWKS URL은 Neon Auth 응답값을 Vercel 환경변수 `NEON_AUTH_BASE_URL`, `NEON_AUTH_JWKS_URL`로 저장

연결 문자열·OAuth secret·bootstrap 비밀번호는 이 문서나 Git에 기록하지 않습니다. 이 저장소의 기존 대시보드 세션(`/api/auth/login`)은 호환성을 위해 유지되며, Neon Auth를 사용하는 새 클라이언트는 위 base URL의 Managed Better Auth API/SDK를 사용해야 합니다. 운영 전환 시 이메일 로그인, 세션 복원, 로그아웃, protected route를 실제 도메인에서 확인합니다.
