"""Unit contracts for the monthly LAWYGO Journal email template and scheduling."""
from datetime import datetime, timedelta, timezone
import pytest
from newsletter_monthly_v5 import Edition, Story, serialize, unpack, plain_body, render_html

def edition():
    future=datetime.now(timezone.utc)+timedelta(days=1)
    month=future.strftime("%Y-%m")
    date=future.replace(microsecond=0).isoformat()
    return Edition(
        issue_month=month,
        subject="LAWYGO JOURNAL 미국 경제와 한국 정책 월간 브리핑",
        intro="이번 달 기업 경영과 법률 대응에 중요한 변화들을 편집국에서 검토했습니다.",
        scheduled_at=date,
        us=[Story(title="Federal Reserve 미국 경제 뉴스 정리",summary="연준 발표에 관한 핵심 사항과 적용 범위를 직접 확인할 필요가 있습니다.",
                  source="Federal Reserve",url="https://www.federalreserve.gov/")],
        kr=[Story(title="한국 법률정책 제도 변화 핵심 안내",summary="법률과 행정 제도는 공식 발표일과 시행일을 별도 확인해야 합니다.",
                  source="국가법령정보센터",url="https://www.law.go.kr/")])

def test_monthly_html_and_plaintext_are_both_available():
    e=edition()
    data=serialize(e)
    assert unpack(data).issue_month==e.issue_month
    html=render_html(e.subject,data,"https://lawygo.lexid.site/unsubscribe")
    assert "미국 주요 경제뉴스" in html
    assert "한국 법률·정책 뉴스" in html
    assert "https://www.law.go.kr/" in html
    assert "무료 수신거부" in html
    assert "출처: Federal Reserve" in plain_body(data)

def test_escaping_untrusted_editorial_text():
    e=edition()
    e.intro="<script>alert('x')</script>"+e.intro
    html=render_html(e.subject,serialize(e))
    assert "<script>" not in html
    assert "&lt;script&gt;" in html

def test_only_https_at_original_source():
    s=Story(title="잘못된 공식 출처 확인 테스트 항목",summary="원문 주소의 스킴은 HTTPS만 허용되어야 합니다.",
            source="테스트",url="http://example.org/article")
    with pytest.raises(ValueError):
        s.verified()

def test_schedule_checks_month_and_future():
    e=edition()
    assert e.checked_schedule() > datetime.now(timezone.utc)
    e.issue_month="2000-01"
    with pytest.raises(ValueError):
        e.checked_schedule()

def test_plain_legacy_email_gracefully_renders():
    body="기존 원고의 이메일 본문입니다."
    assert plain_body(body)==body
    assert "기존 원고" in render_html("LAWYGO 기존 뉴스레터",body)
