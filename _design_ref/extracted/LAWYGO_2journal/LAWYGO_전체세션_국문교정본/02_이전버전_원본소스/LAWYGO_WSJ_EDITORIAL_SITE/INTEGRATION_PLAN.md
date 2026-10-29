# LAWYGO 실제 개발 자산 연결 설계 — 구현 및 검증 핸드오프

이 파일은 2026-10-29에 연결된 비공개 GitHub 저장소에서 확인한 소스/개발문서 항목과 마케팅 HTML 사이트의 연결 표입니다. **정적 마케팅 산출물에서 실서비스 백엔드를 호출하지 않습니다.** 데이터베이스, OAuth, 법원 인증키, 운영 URL에 대한 별도 승인·배포 검증이 필요합니다.

## 1. 실제 저장소와 마케팅 페이지

| 원본 | 실제 소스·문서 검토 | 웹사이트 페이지 | 준비해야 할 연결 |
|---|---|---|---|
| `shinkangteam/lawygo` (master) | `src/app/page.tsx`, `src/app/cases`, `docs/planning/legal-encyclopedia-unified-architecture.md`, `docs/scourt-case-search-integration.md`, `docs/qa/final-qa-results.json` | `/pro`, `/wiki`, `/note`, `/pro/beta` | 기존 인증/테넌트/법원조회/백과 APIs를 내부 연동, 실 배포 확인 |
| `shinkangteam/wallpilotpro` (main) | `src/components/modules/dartlab-panel.tsx`, `src/lib/api/dart.functions.ts`, `src/lib/api/news-data.server.ts`, `docs/gtm/01_LANDING_COPY.md` | `/journal`, `/journal/market-intelligence` | OpenDART/뉴스 등 데이터 공급권·출처 정책·캐싱 적용, 편집 파이프라인 구성 |
| `shinkangteam/lonexus` (master) | `src/lib/module-registry.ts`, `docs/ARCHITECTURE-AUDIT.md`, `docs/MODULE-COMPLETION-PLAN.md`, `docs/SECURITY-AUDIT.md` | `/pro/hub`, `/pro/enterprise`, `/pro/work` | Google SSO, 조직 권한, 감사 로그, 사내 메시징·메일 서버 접속 테스트 |

## 2. 서비스 실행과 마케팅 분리

- 제안 구조: `lawygo.com` 마케팅(Next.js/Vercel)와 `app.lawygo.com` 업무 앱(기존 lawygo) 분리, 기업형 `hub`는 내부 인증 전용 경로. 실제 도메인/배포와 DNS는 미확정 예시.
- 마케팅에는 **서버 인증키, DB 키, 법원 조회정보, 의뢰인/사건 정보를 포함하지 않음**.
- Google 로그인: 기존 lawygo 인증 경로/실제 운영 OAuth 환경을 확인하고 메인 CTA만 공식 경로로 보냄. (현재 HTML은 lawygo.com으로 이동)
- Newsletter: 구독동의, 본인 이메일 확인, 구독 해지, 발송 기록, 이중 옵트인 검토 및 대량 발송 시스템 구축.
- PRO: 테넌트 분리, RBAC, 접근로그, 민감자료 암호화·백업, 사건별 분리 권한, 데이터 내보내기, 베타 종료 정책 구현.
- 대법원 연동: `docs/scourt-case-search-integration.md`에 공식 API(승인 필요) 및 웹 조회 링크 두 방식이 문서화됨. 사건번호만으로 자동 기일 조회를 일괄 보장하지 않음.
- Wiki & Note: 문서 OCR, 법령/판례 검색, 근거와 AI 생성 텍스트 구분, 원문 라이선스·업데이트 타임스탬프·출처 링크 필수.
- Journal: 공시(DART), SEC, 미 연준, 공식 정책자료, 데이터 공급업체(AlphaVantage·Yahoo)의 정책·캐시 제한 별도 검토. WallPilot의 투자 신호/매매 자동실행을 저널 기사에서 혼용 금지.
- Enterprise HUB: lonexus 문서에서 일부 iframe/서비스에 외부 URL/토큰 필요, 보안정책과 접근제어가 운영 준비 여부에 따라 다름.

## 3. 출시 전 QA 우선순위

1. 운영 GitHub의 실제 배포 커밋과 현재 Vercel 배포 SHA 대조
2. Google OAuth 신규 계정으로 가입/로그인/로그아웃 성공, 보호된 경로 접근 거부
3. 베타 사건번호 등록, 대법원 조회 링크/공식 API 경로, 기일 확인이 실제 가능한지 계정별 검증
4. 계정 A/B 간 조직/사건/문서 열람 불가 테스트와 보안 로깅
5. DART 뉴스 수집 원문 귀속·기사 업데이트·편집 승인·정정 요청 기능 테스트
6. 제품별 구독 권한, 청구/결제, 쿠키·메일 구독 동의·해지와 수신 거부 테스트
7. 모바일/접근성/Lighthouse/브라우저 호환과 이미지 최적화 수행
8. 개인 고객·법무법인 데이터 관련 이용약관/개인정보처리방침 검토
9. 특허 등록·권리 사용관계, LLC/Inc 법인명/델라웨어 등록, Google 경력 연구진 기술 기여 사실 확인

## 4. 베타 서비스 공식 카피 (사용자 제공 운영 정책)

> **LAWYGO PRO | 구글 계정으로 시작하는 전문 송무 관리**
>
> 누구나 구글 계정을 통해 무료 베타 서비스 이용을 시작할 수 있습니다. 사건번호 등을 등록하고 대법원 나의 사건 검색과 연결해 기일·사건 진행정보를 확인할 수 있습니다. 법원에 따라 당사자명·추가 인증 등이 필요할 수 있으며 자동 조회는 서비스 제공 범위에 따릅니다. 무료 베타는 3~6개월간 운영할 예정이고, 종료일 1개월 전에 별도 안내할 예정입니다. 종료 이후 정식 구독 조건은 사전에 공지합니다.

**문구 공개 전 확인:** 기존 lawygo.com의 공개 유료 요금표와 무료 베타 제공 여부가 충돌하지 않도록 판매조건과 약관을 조정해야 합니다.
