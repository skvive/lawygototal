# LAWYGO 브랜드 도메인 및 배포설계 (2026-10-29)

**공식 기준 도메인:** `lawygo.com` (기존 사이트 기반). 아래 세부 서비스 주소는 **배포 제안**이며 실제 DNS/SSL/라우팅 연결을 확인한 상태는 아닙니다.

|서비스|권장 URL|동봉된 HTML 시안 위치|
|---|---|---|
|ROOT|`https://lawygo.com`|`index.html`|
|JOURNAL|`https://journal.lawygo.com`|`journal/index.html`|
|WIKI|`https://wiki.lawygo.com`|`wiki/index.html`|
|NOTE|`https://note.lawygo.com`|`note/index.html`|
|PRO|`https://pro.lawygo.com`|`pro/index.html`|
|PAN|`https://pan.lawygo.com`|`pan/index.html`|
|PARTNER|`https://lawygo.com/partnership`|`partnership.html`|
|PAYMENT|`https://lawygo.com/payment`|`payment.html`|


## 배포 체크리스트
1. 호스팅(Vercel 또는 기존 lawygo.com 서버)에 `lawygo.com`, `journal.lawygo.com`, `wiki.lawygo.com`, `note.lawygo.com`, `pro.lawygo.com`, `pan.lawygo.com` 도메인을 하나씩 등록하고 DNS CNAME/A 검증 후 SSL을 활성화합니다.
2. **각 도메인이 연결되기 전까지 임의의 subdomain 외부 링크로 즉시 치환하지 않습니다.** ZIP은 파일 상대경로로 모든 페이지 간 이동이 가능하도록 유지했습니다.
3. 기존 lawygo 프로젝트로 실제 송무를 제공하는 `pro.lawygo.com`은 기존 Google OAuth callback 허용목록, 세션 쿠키 Domain·SameSite·Secure 설정, 프로젝트별 DB/멀티테넌트 권한을 검수한 후 연결합니다.
4. LAWYGO 결제는 기존 `shinkangteam/lexid`의 PR #14 (`/lawygo/payment`)로 설계됐지만 **운영 병합·키 검증·판매 승인 전**입니다. 새로운 `lawygo.com/payment`를 공개할 때에는 결제 서버와 로그인을 보안 경계 내에서 연결하고 CORS/CSRF/Stripe Webhook URL·성공/취소/계정 접근을 교차 도메인 기준 재검증합니다.
5. Partnership: `lawygo.com/partnership` (정적 `partnership.html`을 rewrite), MOU는 `lawygo.com/mou`, 간편 문의창은 `lawygo.com/partnership-inquiry` rewrite를 권장합니다. 현재 폼은 메일 앱 `mailto:`를 열 뿐 자동 접수/DB 저장 기능이 아닙니다.
6. 개인정보처리방침 및 서비스 약관을 각 결제·회원가입·데이터 수집처리 범위에 맞게 확정하고 제휴 폼의 수신·보관 기간을 고지합니다.

## 대외 명칭·국내 창구
- 한국 협력·영업 창구: **대한에이전트협회 (Korea Agent Association)**
- 주소: 서울특별시 서초구 서초중앙로22길 47, INS-154 (명함 영문: `INS-154, 47, Seochojungang-ro 22-gil, Seocho-gu, Seoul, Republic of Korea`)
- 전화: 0505-248-2468 / 팩스: 0505-284-2468
- 국내 문의: shinkang888@gmail.com
- 미국 제휴 이메일: sk@terrabridge.us
- **법적 주의:** 국내 창구 표기는 TERRABRIDGE CAPITAL LLC의 등록된 한국 지점·계약 대리권을 증명하지 않습니다. MOU 서명법인과 권한은 서명 시 검증합니다.
