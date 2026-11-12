"""Durable opt-in + issue dispatch queue for LAWYGO JOURNAL.
Never email unverified users, and never auto-send an issue without admin approval.
All queue records are tenant-scoped; tokens are only stored as hashes.
"""
import os
import secrets
import uuid
from datetime import datetime, timezone
from fastapi import Depends
from pydantic import BaseModel, Field

def stamp():
    return datetime.now(timezone.utc).isoformat()

def enqueue_confirmation(db, tenant, subscriber_id):
    key='confirm:'+tenant+':'+subscriber_id
    t=stamp()
    db.execute("""INSERT INTO newsletter_jobs(job_key,tenant,job_type,subscriber_id,issue_id,status,attempts,created_at,updated_at)
       VALUES(?,?,?,?,?,'queued',0,?,?)
       ON CONFLICT(job_key) DO UPDATE SET status='queued',attempts=0,last_error=NULL,updated_at=excluded.updated_at""",
       (key,tenant,'confirmation',subscriber_id,None,t,t))
    return key

def dispatch_one(db, transaction, job_key, tenant, send_confirmation, send_issue_email, digest, allow_issues=False):
    job=db.execute("SELECT * FROM newsletter_jobs WHERE job_key=? AND tenant=? AND status='queued'",(job_key,tenant)).fetchone()
    if not job: return 'skipped'
    subscriber=db.execute("SELECT * FROM newsletter_subscribers WHERE id=? AND tenant=?",(job['subscriber_id'],tenant)).fetchone()
    expected='pending' if job['job_type']=='confirmation' else 'active'
    if not subscriber or subscriber['status']!=expected:
        db.execute("UPDATE newsletter_jobs SET status='cancelled',updated_at=? WHERE job_key=? AND status='queued'",(stamp(),job_key))
        return 'cancelled'
    if job['job_type']=='issue' and not allow_issues:
        return 'held'
    if job['job_type']=='issue':
        issue=db.execute("SELECT * FROM newsletter_issues WHERE id=? AND tenant=?",(job['issue_id'],tenant)).fetchone()
        if not issue:
            db.execute("UPDATE newsletter_jobs SET status='cancelled',updated_at=? WHERE job_key=?",(stamp(),job_key))
            return 'cancelled'
        from newsletter_monthly_v5 import unpack
        edition=unpack(issue['body'])
        if edition:
            from datetime import datetime
            planned=datetime.fromisoformat(edition.scheduled_at.replace('Z','+00:00'))
            if planned > datetime.now(timezone.utc):
                return 'held'
    else: issue=None
    # Atomic claim: concurrent dispatchers cannot send the same queued job.
    with transaction(db):
        claimed=db.execute("""UPDATE newsletter_jobs SET status='processing',attempts=attempts+1,updated_at=?
              WHERE job_key=? AND tenant=? AND status='queued' RETURNING job_key""",(stamp(),job_key,tenant)).fetchone()
        if not claimed:return 'skipped'
        token=secrets.token_urlsafe(32)
        unsub=secrets.token_urlsafe(32)
        if job['job_type']=='confirmation':
            db.execute("""UPDATE newsletter_subscribers SET verify_token_hash=?,unsubscribe_token_hash=?
                  WHERE id=? AND status='pending'""",(digest(token),digest(unsub),subscriber['id']))
        else:
            # Set the unsubscribe token *before* mailing to prevent broken unsubscribe links.
            db.execute("UPDATE newsletter_subscribers SET unsubscribe_token_hash=? WHERE id=? AND status='active'",(digest(unsub),subscriber['id']))
    try:
        if issue:
            send_issue_email(subscriber['email'],issue['subject'],issue['body'],unsub)
        else:
            send_confirmation(subscriber['email'],token,unsub)
    except Exception:
        # Do not automatically retry uncertain delivery; operator may explicitly requeue.
        with transaction(db):
            db.execute("""UPDATE newsletter_jobs SET status='failed',last_error='SMTP delivery failed',
                    updated_at=? WHERE job_key=? AND status='processing'""",(stamp(),job_key))
        return 'failed'
    with transaction(db):
        db.execute("""UPDATE newsletter_jobs SET status='sent',last_error=NULL,sent_at=?,updated_at=?
             WHERE job_key=? AND status='processing'""",(stamp(),stamp(),job_key))
        if issue:
            db.execute("""INSERT INTO newsletter_deliveries(id,issue_id,subscriber_id,status,sent_at)
                  VALUES(?,?,?,'sent',?)
                  ON CONFLICT(issue_id,subscriber_id) DO NOTHING""",
                  (uuid.uuid4().hex,issue['id'],subscriber['id'],stamp()))
    return 'sent'

def register(app,g,mail_config,send_confirmation,send_issue_email,digest):
    database=g['database']; transaction=g['transaction'];err=g['err']
    csrf=g['csrf'];current=g['current_user'];audit=g['audit']
    class IssueRequest(BaseModel):
        subject:str=Field(min_length=8,max_length=160)
        body:str=Field(min_length=30,max_length=10000)
        confirmed_preview:bool=False
    class DispatchRequest(BaseModel):
        limit:int=Field(default=20,ge=1,le=100)
    class RequeueRequest(BaseModel):
        job_key:str=Field(min_length=10,max_length=160)
    def admin_only(user):
        if user['role']!='admin':err(403,'관리자 전용 기능입니다.')
    @app.get('/api/growth/newsletter/admin/subscribers')
    def subscribers(status:str='all',limit:int=100,user=Depends(current),db=Depends(database)):
        admin_only(user)
        if status not in ('all','active','pending','unsubscribed'):err(422,'상태가 올바르지 않습니다.')
        limit=max(1,min(limit,100))
        if status=='all':
            rows=db.execute("SELECT id,email,status,consent_at,verified_at,unsubscribed_at FROM newsletter_subscribers WHERE tenant=? ORDER BY consent_at DESC LIMIT ?",(user['tenant'],limit)).fetchall()
        else:
            rows=db.execute("SELECT id,email,status,consent_at,verified_at,unsubscribed_at FROM newsletter_subscribers WHERE tenant=? AND status=? ORDER BY consent_at DESC LIMIT ?",(user['tenant'],status,limit)).fetchall()
        return {'items':[dict(r) for r in rows],'limit':limit}
    @app.get('/api/growth/newsletter/admin/queue')
    def queue_status(user=Depends(current),db=Depends(database)):
        admin_only(user)
        counts=db.execute("SELECT job_type,status,COUNT(*) AS n FROM newsletter_jobs WHERE tenant=? GROUP BY job_type,status",(user['tenant'],)).fetchall()
        entries=db.execute("""SELECT job_key,job_type,status,attempts,created_at,updated_at,
                 sent_at,last_error FROM newsletter_jobs WHERE tenant=?
                 ORDER BY created_at DESC LIMIT 100""",(user['tenant'],)).fetchall()
        return {'counts':[dict(x) for x in counts], 'jobs':[dict(x) for x in entries],
                'smtp_configured':smtp_ready(mail_config),
                'issue_send_enabled':os.getenv('LAWYGO_NEWSLETTER_ALLOW_SEND','').lower()=='true'}
    @app.post('/api/growth/newsletter/admin/queue-issue')
    def create_queued_issue(body:IssueRequest,user=Depends(csrf),db=Depends(database)):
        admin_only(user)
        if not body.confirmed_preview:err(409,'뉴스레터 발송 대상과 원고 미리보기 승인 후 등록하세요.')
        month=stamp()[:7]
        count=db.execute("SELECT COUNT(*) AS n FROM newsletter_issues WHERE tenant=? AND issue_month=?",(user['tenant'],month)).fetchone()[0]
        if count>=1:err(409,'이번 달 뉴스레터 발행 한도(1회)에 도달했습니다.')
        recipients=db.execute("SELECT id FROM newsletter_subscribers WHERE tenant=? AND status='active' ORDER BY id",(user['tenant'],)).fetchall()
        if not recipients:err(409,'이메일 확인을 완료한 구독자가 없습니다.')
        if len(recipients)>100:err(409,'구독자 100명 초과입니다. 전문 대량발송 서비스 연동 후 진행하세요.')
        issue_id=uuid.uuid4().hex;t=stamp()
        with transaction(db):
            db.execute("INSERT INTO newsletter_issues(id,tenant,issue_month,subject,body,created_by,created_at) VALUES(?,?,?,?,?,?,?)",
                       (issue_id,user['tenant'],month,body.subject.strip(),body.body.strip(),user['id'],t))
            for sub in recipients:
                db.execute("""INSERT INTO newsletter_jobs(job_key,tenant,job_type,subscriber_id,issue_id,status,attempts,created_at,updated_at)
                    VALUES(?,?,?,?,?,'queued',0,?,?)""",
                    ('issue:'+issue_id+':'+sub['id'],user['tenant'],'issue',sub['id'],issue_id,t,t))
            audit(db,user,'queue','newsletter_issue',issue_id,{'recipients':len(recipients)})
        return {'issue_id':issue_id,'queued':len(recipients),'status':'queued',
                'message':'승인한 원고를 발송 대기열에 등록했습니다. 자동 발송되지 않습니다.'}
    @app.post('/api/growth/newsletter/admin/dispatch')
    def dispatch(body:DispatchRequest,user=Depends(csrf),db=Depends(database)):
        admin_only(user)
        try:mail_config()
        except (RuntimeError,ValueError):err(503,'SMTP 이메일 서버 설정을 먼저 완료하세요. 대기열은 보존됩니다.')
        allow_issues=os.getenv('LAWYGO_NEWSLETTER_ALLOW_SEND','').lower()=='true'
        jobs=db.execute("""SELECT job_key FROM newsletter_jobs WHERE tenant=? AND status='queued'
             AND (job_type='confirmation' OR ?=1) ORDER BY created_at ASC LIMIT ?""",
            (user['tenant'],int(allow_issues),body.limit)).fetchall()
        result={'sent':0,'failed':0,'cancelled':0,'held':0,'skipped':0}
        for job in jobs:
            state=dispatch_one(db,transaction,job['job_key'],user['tenant'],send_confirmation,send_issue_email,digest,allow_issues)
            result[state]=result.get(state,0)+1
        result['remaining']=db.execute("SELECT count(*) FROM newsletter_jobs WHERE tenant=? AND status='queued'",(user['tenant'],)).fetchone()[0]
        return result
    @app.post('/api/growth/newsletter/admin/requeue')
    def retry(body:RequeueRequest,user=Depends(csrf),db=Depends(database)):
        admin_only(user)
        with transaction(db):
            row=db.execute("SELECT status,job_type FROM newsletter_jobs WHERE tenant=? AND job_key=?",(user['tenant'],body.job_key)).fetchone()
            if not row:err(404,'발송 작업을 찾을 수 없습니다.')
            if row['status']!='failed':err(409,'실패 처리된 작업만 수동 재등록할 수 있습니다.')
            db.execute("UPDATE newsletter_jobs SET status='queued',last_error=NULL,updated_at=? WHERE tenant=? AND job_key=?",
                       (stamp(),user['tenant'],body.job_key))
            audit(db,user,'retry','newsletter_job',body.job_key)
        return {'status':'queued','message':'발송 실패 기록을 수동 대기열로 돌렸습니다. 중복 수신 여부를 확인해 주세요.'}

def smtp_ready(mail_config):
    try:
        mail_config()
        return True
    except (RuntimeError,ValueError):
        return False
