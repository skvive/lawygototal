"""LAWYGO Journal monthly briefing v5. Reuses the existing verified-opt-in queue.
One edition per tenant/month, editor drafts, admin approval, safe HTML and cron dispatch.
"""
import html
import hmac
import json
import os
import re
import uuid
from datetime import datetime, timezone
from urllib.parse import urlsplit

from fastapi import Depends, Request
from pydantic import BaseModel, Field

PREFIX = "LJMONTHLY5:"
MONTH_PATTERN = re.compile(r"^\d{4}-(0[1-9]|1[0-2])$")


def stamp():
    return datetime.now(timezone.utc).isoformat()


class Story(BaseModel):
    title: str = Field(min_length=8, max_length=160)
    summary: str = Field(min_length=15, max_length=350)
    source: str = Field(min_length=2, max_length=80)
    url: str = Field(min_length=12, max_length=600)

    def verified(self):
        p = urlsplit(self.url)
        if p.scheme != "https" or not p.hostname or p.username or p.password:
            raise ValueError("기사 원문 링크는 HTTPS 주소여야 합니다.")


class Edition(BaseModel):
    issue_month: str = Field(min_length=7, max_length=7)
    subject: str = Field(min_length=8, max_length=160)
    intro: str = Field(min_length=30, max_length=1200)
    us: list[Story] = Field(min_length=1, max_length=5)
    kr: list[Story] = Field(min_length=1, max_length=5)
    editorial_note: str = Field(default="", max_length=900)
    scheduled_at: str = Field(min_length=20, max_length=40)

    def checked_schedule(self):
        if not MONTH_PATTERN.fullmatch(self.issue_month):
            raise ValueError("발행월은 YYYY-MM 형식이어야 합니다.")
        for story in self.us + self.kr:
            story.verified()
        try:
            dt = datetime.fromisoformat(self.scheduled_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError("예약발송 시각이 잘못됐습니다.") from exc
        if not dt.tzinfo:
            raise ValueError("예약발송에는 시간대가 필요합니다.")
        dt = dt.astimezone(timezone.utc)
        if dt < datetime.now(timezone.utc):
            raise ValueError("예약발송 시각은 미래여야 합니다.")
        if dt.strftime("%Y-%m") != self.issue_month:
            raise ValueError("예약 발송일과 발행월이 일치해야 합니다.")
        return dt


class ApprovedEdition(Edition):
    confirmed_preview: bool = False


def serialize(edition):
    result = PREFIX + json.dumps(edition.model_dump(exclude={"confirmed_preview"}), ensure_ascii=False, separators=(",", ":"))
    if len(result) > 10000:
        raise ValueError("뉴스레터 원고가 최대 길이를 초과했습니다.")
    return result


def unpack(body):
    if not isinstance(body, str) or not body.startswith(PREFIX):
        return None
    try:
        return Edition.model_validate(json.loads(body[len(PREFIX):]))
    except (ValueError, TypeError, json.JSONDecodeError):
        return None


def plain_body(body):
    edition = unpack(body)
    if not edition:
        return body
    lines = [edition.intro, "", "미국 경제 | U.S. ECONOMY"]
    for s in edition.us:
        lines += ["", s.title, s.summary, "출처: " + s.source, "원문: " + s.url]
    lines += ["", "한국 법률·정책 | KOREA LEGAL & POLICY"]
    for s in edition.kr:
        lines += ["", s.title, s.summary, "출처: " + s.source, "원문: " + s.url]
    if edition.editorial_note:
        lines += ["", "편집자 코멘트", edition.editorial_note]
    return "\n".join(lines)


def render_html(subject, body, unsub_url="#", base_url="https://lawygo.lexid.site"):
    esc = lambda x: html.escape(str(x), quote=True)
    edition = unpack(body)
    if edition:
        intro = '<p style="font-size:16px;line-height:1.85;color:#35485a;">' + esc(edition.intro) + '</p>'
        sections = ""
        for heading, marker, stories in (("미국 주요 경제뉴스", "01 / U.S. ECONOMY", edition.us), ("한국 법률·정책 뉴스", "02 / KOREA POLICY", edition.kr)):
            sections += '<tr><td style="padding:30px 35px 12px;"><div style="color:#ac8650;font-size:11px;font-weight:bold;letter-spacing:2px;">'+marker+'</div><h2 style="font-size:24px;color:#142b40;margin:8px 0 8px;">'+heading+'</h2></td></tr>'
            for s in stories:
                sections += '<tr><td style="padding:10px 35px 22px;border-bottom:1px solid #e8edf0;">'
                sections += '<h3 style="font-size:18px;line-height:1.45;color:#15354d;margin:0 0 9px;">'+esc(s.title)+'</h3>'
                sections += '<p style="color:#44586a;font-size:14px;line-height:1.8;margin:0 0 10px;">'+esc(s.summary)+'</p>'
                sections += '<span style="font-size:12px;color:#647788;">'+esc(s.source)+'</span>'
                sections += ' &nbsp; <a style="font-size:12px;color:#126096;text-decoration:underline;" href="'+esc(s.url)+'">원문 보기</a></td></tr>'
        if edition.editorial_note:
            sections += '<tr><td style="padding:25px 35px;"><div style="background:#f0f4f5;padding:20px;border-left:3px solid #c5a470;"><strong style="color:#203e50;">편집자 코멘트</strong><p style="line-height:1.7;color:#44586a;">'+esc(edition.editorial_note)+'</p></div></td></tr>'
        month = esc(edition.issue_month)
    else:
        intro = '<p style="white-space:pre-line;font-size:15px;line-height:1.8;color:#35485a;">'+esc(body)+'</p>'
        sections = ""
        month = "MONTHLY JOURNAL"
    safe_unsub = esc(unsub_url) if urlsplit(unsub_url).scheme == "https" else "#"
    base = base_url.rstrip("/")
    if urlsplit(base).scheme != "https":
        base = "https://lawygo.lexid.site"
    safe_home = esc(base + "/journal")
    return (
        '<!doctype html><html lang="ko"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1"></head>'
        '<body style="padding:0;margin:0;background:#f3f6f7;font-family:Arial,Apple SD Gothic Neo,Malgun Gothic,sans-serif;">'
        '<div style="display:none;max-height:0;overflow:hidden;">'+esc(subject)+'</div>'
        '<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="background:#f3f6f7;"><tr><td align="center" style="padding:28px 12px;">'
        '<table role="presentation" cellpadding="0" cellspacing="0" width="100%" style="width:100%;max-width:620px;background:#ffffff;border-collapse:collapse;">'
        '<tr><td style="background:#102a3f;padding:35px;color:white;border-top:5px solid #c5a470;">'
        '<div style="font-size:13px;letter-spacing:3px;color:#e1bf89;">LAWYGO JOURNAL</div>'
        '<h1 style="font-size:34px;line-height:1.2;margin:18px 0 10px;">MONTHLY<br>BRIEFING</h1>'
        '<div style="font-size:13px;color:#d6e1e7;">U.S. ECONOMY × KOREA LAW & POLICY</div>'
        '<div style="font-size:12px;margin-top:19px;color:#c9d7df;">'+month+'</div></td></tr>'
        '<tr><td style="padding:32px 35px 10px;"><h2 style="font-size:23px;color:#152e42;margin:0 0 16px;">'+esc(subject)+'</h2>'+intro+'</td></tr>'
        + sections +
        '<tr><td style="padding:25px 35px;text-align:center;"><a href="'+safe_home+'" style="display:inline-block;padding:13px 25px;background:#163b54;color:white;text-decoration:none;font-weight:bold;">로이고저널 전체 보기</a></td></tr>'
        '<tr><td style="background:#edf1f3;padding:22px 35px;color:#60717d;font-size:11px;line-height:1.8;">'
        '이 뉴스레터는 직접 구독을 확인한 수신자에게 월 1회 제공됩니다. 제휴·광고 콘텐츠는 별도로 표시합니다.'
        '<br>외부 기사 저작권은 원 발행사에 있으며, 원문 링크를 통해 확인할 수 있습니다.'
        '<br>법률·경제 동향 정보로서 개별 법률·투자 자문이 아닙니다.'
        '<br>LAWYGO JOURNAL · sk@terrabridge.us'
        '<br><a href="'+safe_unsub+'" style="color:#235e80;">무료 수신거부</a></td></tr>'
        '</table></td></tr></table></body></html>'
    )


def ensure_schema(db):
    db.executescript("""
      CREATE TABLE IF NOT EXISTS newsletter_monthly_drafts(
        tenant TEXT NOT NULL, issue_month TEXT NOT NULL, payload TEXT NOT NULL,
        updated_by TEXT NOT NULL, updated_at TEXT NOT NULL,
        PRIMARY KEY(tenant,issue_month));
      CREATE TABLE IF NOT EXISTS newsletter_monthly_claims(
        tenant TEXT NOT NULL, issue_month TEXT NOT NULL, issue_id TEXT NOT NULL,
        PRIMARY KEY(tenant,issue_month));
    """)


def register(app, g):
    from newsletter_queue_v4 import dispatch_one
    import newsletter_v3
    database = g["database"]
    transaction = g["transaction"]
    current = g["current_user"]
    csrf = g["csrf"]
    err = g["err"]
    audit = g["audit"]

    def staff(user):
        if user["role"] not in ("admin", "editor"):
            err(403, "편집 권한이 필요합니다.")

    @app.get("/api/growth/newsletter/monthly/draft")
    def get_draft(month: str, user=Depends(current), db=Depends(database)):
        staff(user)
        if not MONTH_PATTERN.fullmatch(month):
            err(422, "발행월이 잘못됐습니다.")
        row = db.execute("SELECT payload,updated_at FROM newsletter_monthly_drafts WHERE tenant=? AND issue_month=?",
                         (user["tenant"], month)).fetchone()
        return {"draft": json.loads(row["payload"]) if row else None, "updated_at": row["updated_at"] if row else None}

    @app.post("/api/growth/newsletter/monthly/draft")
    def save_draft(edition: Edition, user=Depends(csrf), db=Depends(database)):
        staff(user)
        try: edition.checked_schedule()
        except ValueError as exc: err(422, str(exc))
        with transaction(db):
            db.execute("""INSERT INTO newsletter_monthly_drafts(tenant,issue_month,payload,updated_by,updated_at)
                VALUES(?,?,?,?,?) ON CONFLICT(tenant,issue_month) DO UPDATE SET
                payload=excluded.payload,updated_by=excluded.updated_by,updated_at=excluded.updated_at""",
                (user["tenant"],edition.issue_month,edition.model_dump_json(),user["id"],stamp()))
        return {"ok": True, "saved_at": stamp()}

    @app.post("/api/growth/newsletter/monthly/preview")
    def preview(edition: Edition, user=Depends(csrf)):
        staff(user)
        try: edition.checked_schedule()
        except ValueError as exc: err(422, str(exc))
        return {"html": render_html(edition.subject,serialize(edition)),
                "text":plain_body(serialize(edition))}

    @app.get("/api/growth/newsletter/monthly/issues")
    def history(user=Depends(current), db=Depends(database)):
        staff(user)
        rows = db.execute("""SELECT i.id,i.issue_month,i.subject,i.created_at,
            (SELECT count(*) FROM newsletter_jobs j WHERE j.issue_id=i.id AND j.status='sent') AS sent,
            (SELECT count(*) FROM newsletter_jobs j WHERE j.issue_id=i.id AND j.status='queued') AS queued
            FROM newsletter_issues i WHERE i.tenant=? ORDER BY i.created_at DESC LIMIT 24""",
            (user["tenant"],)).fetchall()
        return {"items": [dict(r) for r in rows]}

    @app.post("/api/growth/newsletter/monthly/queue")
    def queue_monthly(edition: ApprovedEdition, user=Depends(csrf), db=Depends(database)):
        if user["role"] != "admin":
            err(403, "관리자 승인만 발송 대기열을 생성할 수 있습니다.")
        if not edition.confirmed_preview:
            err(409, "원고 미리보기와 수신 대상 확인이 필요합니다.")
        try: edition.checked_schedule()
        except ValueError as exc: err(422, str(exc))
        recipients = db.execute("SELECT id FROM newsletter_subscribers WHERE tenant=? AND status='active' ORDER BY id",
                                (user["tenant"],)).fetchall()
        if not recipients: err(409, "인증된 구독자가 없습니다.")
        if len(recipients)>100: err(409, "회당 최대 100명입니다. 발송 서비스 연동이 필요합니다.")
        issue_id=uuid.uuid4().hex
        t=stamp()
        content=serialize(edition)
        with transaction(db):
            exists=db.execute("SELECT 1 FROM newsletter_issues WHERE tenant=? AND issue_month=?",
                              (user["tenant"],edition.issue_month)).fetchone()
            if exists: err(409, "해당 월의 뉴스레터가 이미 등록돼 있습니다.")
            claimed=db.execute("""INSERT INTO newsletter_monthly_claims(tenant,issue_month,issue_id)
                VALUES(?,?,?) ON CONFLICT(tenant,issue_month) DO NOTHING RETURNING issue_id""",
                (user["tenant"],edition.issue_month,issue_id)).fetchone()
            if not claimed: err(409, "이미 승인된 월간호가 있습니다.")
            db.execute("""INSERT INTO newsletter_issues(id,tenant,issue_month,subject,body,created_by,created_at)
                VALUES(?,?,?,?,?,?,?)""",
                (issue_id,user["tenant"],edition.issue_month,edition.subject.strip(),content,user["id"],t))
            for sub in recipients:
                db.execute("""INSERT INTO newsletter_jobs(job_key,tenant,job_type,subscriber_id,issue_id,status,attempts,created_at,updated_at)
                    VALUES(?,?,?,?,?,'queued',0,?,?)""",
                    ("issue:"+issue_id+":"+sub["id"],user["tenant"],"issue",sub["id"],issue_id,t,t))
            audit(db,user,"approve","newsletter_monthly",issue_id,{"recipients":len(recipients),"scheduled_at":edition.scheduled_at})
        return {"issue_id": issue_id,"queued":len(recipients),"scheduled_at":edition.scheduled_at,
                "status":"scheduled","message":"승인된 월간호를 예약 대기열에 등록했습니다. 설정 전까지 발송되지 않습니다."}

    @app.get("/api/cron/newsletter-monthly")
    def cron_monthly(req: Request, db=Depends(database)):
        secret=os.getenv("LAWYGO_CRON_SECRET","") or os.getenv("CRON_SECRET","")
        auth=req.headers.get("authorization","")
        if not secret or not hmac.compare_digest(auth, "Bearer "+secret):
            err(401,"허가되지 않은 요청입니다.")
        if os.getenv("LAWYGO_NEWSLETTER_ALLOW_SEND","").lower() != "true":
            return {"ok":True,"status":"locked","sent":0}
        try: newsletter_v3.mail_config()
        except (RuntimeError,ValueError):
            return {"ok":True,"status":"smtp_not_configured","sent":0}
        # Ordered, bounded daily batch; processing is only possible after admin approval.
        rows=db.execute("""SELECT j.job_key,j.tenant,i.body FROM newsletter_jobs j
            JOIN newsletter_issues i ON i.id=j.issue_id
            WHERE j.job_type='issue' AND j.status='queued'
            ORDER BY j.created_at,j.job_key LIMIT 120""").fetchall()
        totals={"sent":0,"failed":0,"cancelled":0,"held":0,"skipped":0}
        processed=0
        for row in rows:
            e=unpack(row["body"])
            if not e: continue
            scheduled=datetime.fromisoformat(e.scheduled_at.replace("Z","+00:00"))
            if scheduled > datetime.now(timezone.utc): continue
            if processed>=20: break
            state=dispatch_one(db,transaction,row["job_key"],row["tenant"],
                               newsletter_v3.send_confirmation,newsletter_v3.send_issue_email,
                               newsletter_v3.digest,allow_issues=True)
            totals[state]=totals.get(state,0)+1
            processed+=1
        return {"ok":True,"status":"processed","counts":totals,"processed":processed}
