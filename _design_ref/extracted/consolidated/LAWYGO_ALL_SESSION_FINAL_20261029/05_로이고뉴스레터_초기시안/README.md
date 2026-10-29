# LAWYGO JOURNAL — 디자인 제안 시안

## 파일
- `index.html` — PC / 모바일 대응 저널 메인, 분야별 검색·필터, 샘플 기사 상세 모달, 구독 데모, LawyGo·TerraBridge 외부 연결.
- `newsletter-email.html` — 인라인 스타일과 테이블 레이아웃을 사용한 뉴스레터 이메일 예시.

## 사용
`index.html`을 브라우저에서 열면 됩니다. 별도 프레임워크나 설치가 필요하지 않습니다. Google Fonts만 선택적 외부 의존성이고 차단 시 기본 서체로 표시됩니다.

## lawygo.com 서비스 통합 제안
1. 기존 홈페이지에 `Journal` 메뉴 추가.
2. 신규 라우트 `/journal` 또는 `/insights`에 이 시안의 구성 적용.
3. 기사 데이터는 실제 CMS(제목, 카테고리, 본문, 출처, 발행일, 검수자, 협찬 표시 등)로 교체.
4. 구독 폼은 개인정보 처리방침 및 광고성 정보 수신 동의 검토 뒤 공식 이메일 발송 API/DB와 연결. 현재 화면은 사용자 데이터를 서버로 보내거나 저장하지 **않는 데모**.
5. 실제 테라브릿지캐피탈과 법적·사업적 제휴 범위가 확정된 다음 명칭과 제휴 문구 확정.
6. 출처 확인 및 법률 검토를 거친 기사만 운영 환경에 공개.

## 화면 검수 가능한 상호작용
- 기사 제목 클릭 → 샘플 기사 전체 모달 (Esc / 닫기)
- 카테고리 칩 → 기사 필터
- 검색 버튼 / 입력 → 키워드 검색
- 구독 폼 → 필수 이메일·동의 확인. 실제 등록되지 않음.
- 모바일 내비게이션
- 실제 LawyGo·TerraBridge 홈페이지 링크

## 콘텐츠 주의
- 모든 기사·발행호·날짜는 디자인 예시입니다. 실제 뉴스나 발행 실적이 아닙니다.
- TerraBridge Capital 관련 페이지는 공개 사이트 https://terrabridge.us/ 를 참조했습니다. 유사한 다른 'TeraBridge Capital Partners'와 혼동하지 마세요.
- 본 디자인은 기존 로앤비/톰슨로이터 사이트를 복제하지 않고 편집형 레이아웃의 일반적인 디자인 패턴만 참고해 신규 제작했습니다.

## 참고 공개 사이트 (검토일 2026-10-29)
- https://www.lawygo.com/
- https://www.lawygo.com/ai
- https://www.lawygo.com/platform
- https://terrabridge.us/
- https://insight.thomsonreuters.co.kr/legal/
- https://legal.thomsonreuters.com/en/insights/newsletters/sign-up
- https://www.bkl.co.kr/law/insight/newsletter/subscribe
