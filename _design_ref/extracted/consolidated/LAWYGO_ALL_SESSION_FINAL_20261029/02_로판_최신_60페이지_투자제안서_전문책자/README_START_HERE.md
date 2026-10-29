# LAWYGO PAN · 제작파일 안내

- `site/index.html`: 메인(변호사·콘텐츠·쇼츠·구글블로그·후원 영역)
- `site/content-feed.html`: 콘텐츠 통합 지면
- `site/free-signup.html`: 무료 회원가입 + 본인확인 이메일
- `site/blogger-connect.html`, `site/youtube-connect.html`: 공개 URL 등록
- `site/creator-studio.html`: 전문가 콘텐츠 관리 UI
- `site/advertising.html`, `site/ad-ranking.html`: 광고 상품·노출정책
- `site/private-inquiry.html`: 비공개 상담/연결 신청
- `marketing/email-campaign.html`: 이메일 홍보 HTML
- `marketing/email-campaign.txt`: 이메일 텍스트/광고표기
- `books/investor-deck.html` 및 `.pdf`: 46쪽 투자제안서
- `books/company-profile.*`: 회사소개서
- `books/user-manual.*`: 사용자매뉴얼
- `books/advertising-policy.*`: 광고규정
- `books/privacy-manual.*`: 개인정보지침
- `books/security-manual.*`: 보안운영지침
- `backend/app.py`: 가입·콘텐츠 등록·수신거부·승인된 피드 API 데모
- `backend/marketing_send.py`: 동의받은 대상에만 보내는 발송 CLI(기본 미발송)
- `backend/moderate.py`: 관리자 검수용 CLI
- `QA_REPORT.md`: 변경·검증·잔여작업 목록

## 로컬 실행
```bash
cd LAWYGO_PAN_2026_EXPANSION
python -m venv .venv
# activate virtual environment then:
pip install -r backend/requirements.txt
# configure backend/.env.example into local environment variables
uvicorn backend.app:app --host 127.0.0.1 --port 8765
```

운영모드에서 SMTP·비밀키·DB 설정이 빠졌다면 실제 발송은 동작하지 않습니다.
`LAWYGO_PAN_PREVIOUS_32PAGES.zip`는 이전 고객 납품본이고, `PREVIOUS_LAWYGO_ALL_SESSION.zip`에는 이전 세션의 전체 통합 작업본이 포함됩니다.

Google Blogger/YouTube 자동 동기화는 아직 API 계정이 연결되지 않았으며, URL 제출·관리자 승인형 등록 기능의 구현 예제를 제공합니다.
