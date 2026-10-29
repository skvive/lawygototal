# LAWYGO PAN 마케팅 이메일

- `email-campaign.html`는 고객이 확인하는 HTML 뉴스레터 디자인 샘플입니다. `{{UNSUBSCRIBE_URL}}` 자리에는 수신자별 토큰이 포함된 실제 링크를 넣어야 합니다.
- `email-campaign.txt`는 KISA 표기 원칙을 참조한 일반 텍스트 대체 본문입니다.
- **사전에 명시적으로 광고성 정보 수신에 동의한 수신자**에게만 발송해야 합니다. 가입 때 별도 마케팅 체크박스의 선택을 강요하지 않습니다.
- 실제 전송은 `backend/marketing_send.py --send`를 통해서만 개시되며 `PAN_ENABLE_MARKETING_SEND=YES` 설정이 필요합니다.
- 테스트는 `python backend/marketing_send.py`(기본 미발송)로 시작합니다.
- 수신거부는 실제 운영 서버 `/unsubscribe?token=...` 화면에서 확인, `/api/unsubscribe` POST에서 회원 DB의 마케팅 동의를 해제합니다.
- 광고성 이메일 마케팅 발송은 개인정보보호·광고법·변호사 광고 관련 최종 법률검토 후 운영하세요.
