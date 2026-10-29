"""Explicit opt-in newsletter lifecycle. SMTP is fail-closed until configured.
Emails are never placed in public API output; confirmation/unsubscribe tokens are random one-time values.
"""
import hashlib, os, secrets, smtplib, ssl, uuid, json
from email.message import EmailMessage
from email.utils import parseaddr
from urllib.parse import urlencode, urlparse
from datetime import datetime,timezone
from fastapi import Depends, Request
from pydantic import BaseModel,Field

def now():return datetime.now(timezone.utc).isoformat()
def digest(x):return hashlib.sha256(x.encode()).hexdigest()
def mail_config():
    host=os.getenv('LAWYGO_NEWSLETTER_SMTP_HOST','').strip()
    user=os.getenv('LAWYGO_NEWSLETTER_SMTP_USER','').strip()
    pw=os.getenv('LAWYGO_NEWSLETTER_SMTP_PASSWORD','').strip()
    sender=os.getenv('LAWYGO_NEWSLETTER_FROM','').strip()
    base=os.getenv('LAWYGO_NEWSLETTER_BASE_URL','').strip()
    port=int(os.getenv('LAWYGO_NEWSLETTER_SMTP_PORT','465'))
    p=urlparse(base)
    if not host or not user or not pw or not sender or not p.hostname or (p.scheme!='https' and p.hostname not in ('127.0.0.1','localhost')):
        raise RuntimeError('SMTP 발신자, 비밀번호와 검증된 HTTPS 서비스 URL이 필요합니다.')
    if parseaddr(sender)[1]!=sender or '\n' in sender:raise RuntimeError('보낸사람 이메일 주소 오류')
    if port not in (465,587):raise RuntimeError('TLS 보안 포트(465/587)만 지원')
    return (host,user,pw,sender,base,port)

def send_confirmation(email,token,unsubscribe):
    host,user,pw,sender,base,port=mail_config()
    link=base.rstrip('/')+'/api/growth/newsletter/confirm?'+urlencode({'token':token})
    unsub=base.rstrip('/')+'/api/growth/newsletter/unsubscribe?'+urlencode({'token':unsubscribe})
    msg=EmailMessage();msg['From']=sender;msg['To']=email
    msg['Subject']='[LAWYGO] 월 2회 무료 뉴스레터 구독 확인'
    msg.set_content('LAWYGO 무료 뉴스레터(월 2회)에 신청하셨습니다.\n\n구독 확인: '+link+'\n\n원하지 않으시면 확인하지 않으셔도 됩니다. 수신거부: '+unsub+'\n')
    with (smtplib.SMTP_SSL(host,port,context=ssl.create_default_context(),timeout=12) if port==465 else smtplib.SMTP(host,port,timeout=12)) as client:
        if port==587:client.starttls(context=ssl.create_default_context())
        client.login(user,pw);client.send_message(msg)

def send_issue_email(email,subject,body,token):
    host,user,pw,sender,base,port=mail_config()
    unsub=base.rstrip('/')+'/api/growth/newsletter/unsubscribe?'+urlencode({'token':token})
    msg=EmailMessage();msg['From']=sender;msg['To']=email;msg['Subject']='[광고] '+subject
    msg['List-Unsubscribe']='<'+unsub+'>'
    msg.set_content(body+'\n\n---\n이 메일은 사전 수신 동의에 따라 발송되었습니다.\n무료 수신거부: '+unsub+'\nLAWYGO PAN | sk@terrabridge.us\n')
    with (smtplib.SMTP_SSL(host,port,context=ssl.create_default_context(),timeout=12) if port==465 else smtplib.SMTP(host,port,timeout=12)) as client:
        if port==587:client.starttls(context=ssl.create_default_context())
        client.login(user,pw);client.send_message(msg)

def register(app,g):
    database=g['database'];transaction=g['transaction'];err=g['err'];default_tenant=g['DEFAULT_TENANT'];current=g['current_user'];csrf=g['csrf'];audit=g['audit']
    class Signup(BaseModel):
        email:str=Field(min_length=5,max_length=254)
        consent:bool
    class NewsletterSend(BaseModel):
        subject:str=Field(min_length=8,max_length=160)
        body:str=Field(min_length=30,max_length=10000)
        confirmed_preview:bool=False
    @app.post('/api/growth/newsletter/request')
    def request_optin(data:Signup,db=Depends(database)):
        from email_validator import validate_email,EmailNotValidError
        if not data.consent:err(422,'이메일 뉴스레터 수신에 동의해야 합니다.')
        try:email=validate_email(data.email.strip(),check_deliverability=False).normalized.lower()
        except EmailNotValidError:err(422,'유효한 이메일을 입력하세요.')
        try:mail_config()
        except (RuntimeError,ValueError):err(503,'뉴스레터 이메일 발송 서비스가 설정되지 않았습니다.')
        email_hash=digest(email);token=secrets.token_urlsafe(32);unsub=secrets.token_urlsafe(32)
        old=db.execute('SELECT id,status FROM newsletter_subscribers WHERE tenant=? AND email_hash=?',(default_tenant,email_hash)).fetchone()
        if old and old['status']=='active':return {'ok':True,'message':'구독 확인 안내를 처리했습니다.'}
        try:send_confirmation(email,token,unsub)
        except (smtplib.SMTPException,OSError,TimeoutError):err(503,'메일 발송에 실패했습니다. 다시 시도해 주세요.')
        with transaction(db):
            db.execute('''INSERT INTO newsletter_subscribers(id,tenant,email,email_hash,status,verify_token_hash,unsubscribe_token_hash,consent_at)
              VALUES(?,?,?,?,?,?,?,?) ON CONFLICT(tenant,email_hash) DO UPDATE SET status='pending',verify_token_hash=excluded.verify_token_hash,
              unsubscribe_token_hash=excluded.unsubscribe_token_hash,consent_at=excluded.consent_at,verified_at=NULL,unsubscribed_at=NULL''',
              (old['id'] if old else uuid.uuid4().hex,default_tenant,email,email_hash,'pending',digest(token),digest(unsub),now()))
        return {'ok':True,'message':'이메일로 구독 확인 링크를 발송했습니다. 링크를 눌러야 구독이 시작됩니다.'}

    @app.get('/api/growth/newsletter/confirm')
    def confirm_optin(token:str,db=Depends(database)):
        if len(token)<25 or len(token)>128:err(400,'잘못된 확인 링크')
        item=db.execute('SELECT id,status FROM newsletter_subscribers WHERE tenant=? AND verify_token_hash=?',(default_tenant,digest(token))).fetchone()
        if not item or item['status']!='pending':err(410,'사용할 수 없는 확인 링크')
        db.execute('UPDATE newsletter_subscribers SET status=?,verified_at=?,verify_token_hash=NULL WHERE id=?',('active',now(),item['id']))
        return {'ok':True,'message':'무료 뉴스레터 구독이 완료됐습니다.'}

    @app.get('/api/growth/newsletter/unsubscribe')
    def unsubscribe(token:str,db=Depends(database)):
        if len(token)<25 or len(token)>128:err(400,'잘못된 수신거부 링크')
        item=db.execute('SELECT id FROM newsletter_subscribers WHERE tenant=? AND unsubscribe_token_hash=?',(default_tenant,digest(token))).fetchone()
        if not item:err(410,'사용할 수 없는 수신거부 링크')
        db.execute('UPDATE newsletter_subscribers SET status=?,unsubscribed_at=?,verify_token_hash=NULL,unsubscribe_token_hash=NULL WHERE id=?',('unsubscribed',now(),item['id']))
        return {'ok':True,'message':'수신거부가 정상적으로 처리됐습니다. 더 이상 뉴스레터를 발송하지 않습니다.'}

    @app.post('/api/growth/newsletter/admin/send')
    def newsletter_send(body:NewsletterSend,user=Depends(csrf),db=Depends(database)):
        if user['role']!='admin':err(403,'관리자 승인 후 발송할 수 있습니다.')
        if not body.confirmed_preview:err(409,'수신 대상과 내용 미리보기 승인이 필요합니다.')
        if os.getenv('LAWYGO_NEWSLETTER_ALLOW_SEND','').lower()!='true':err(503,'실제 발송이 잠겨 있습니다. 설정을 확인하세요.')
        try:mail_config()
        except (RuntimeError,ValueError):err(503,'이메일 서버가 준비되지 않았습니다.')
        month=now()[:7]
        issues=db.execute("SELECT COUNT(*) FROM newsletter_issues WHERE tenant=? AND issue_month=?",(user['tenant'],month)).fetchone()[0]
        if issues>=2:err(409,'이번 달 발행 한도(2회)에 도달했습니다.')
        recipients=db.execute("SELECT id,email FROM newsletter_subscribers WHERE tenant=? AND status='active' ORDER BY id",(user['tenant'],)).fetchall()
        if not recipients:err(409,'구독 확인을 마친 수신자가 없습니다.')
        if len(recipients)>100:err(409,'1회 발송 대상 100명 제한. 대량 발송은 전문 ESP로 연동하세요.')
        issue_id=uuid.uuid4().hex
        with transaction(db):
            db.execute('INSERT INTO newsletter_issues(id,tenant,issue_month,subject,body,created_by,created_at) VALUES(?,?,?,?,?,?,?)',
                (issue_id,user['tenant'],month,body.subject.strip(),body.body.strip(),user['id'],now()))
            audit(db,user,'create','newsletter_issue',issue_id)
        sent=0;failed=0
        for item in recipients:
            token=secrets.token_urlsafe(32)
            try:
                send_issue_email(item['email'],body.subject.strip(),body.body.strip(),token)
                with transaction(db):
                    db.execute('INSERT INTO newsletter_deliveries VALUES(?,?,?,?,?)',(uuid.uuid4().hex,issue_id,item['id'],'sent',now()))
                    db.execute('UPDATE newsletter_subscribers SET unsubscribe_token_hash=? WHERE id=?',(digest(token),item['id']))
                sent+=1
            except (smtplib.SMTPException,OSError,TimeoutError):
                with transaction(db):db.execute('INSERT INTO newsletter_deliveries VALUES(?,?,?,?,?)',(uuid.uuid4().hex,issue_id,item['id'],'failed',now()))
                failed+=1
        return {'issue_id':issue_id,'sent':sent,'failed':failed,'notice':'실제 SMTP 발송 결과입니다. 실패 수신자는 자동 재발송하지 않습니다.'}

    @app.get('/api/growth/newsletter/admin/stats')
    def stats(user=Depends(current),db=Depends(database)):
        if user['role']!='admin':err(403,'관리자 전용입니다.')
        rows=db.execute('SELECT status,count(*) n FROM newsletter_subscribers WHERE tenant=? GROUP BY status',(user['tenant'],)).fetchall()
        return {'counts':{r['status']:r['n'] for r in rows}}
