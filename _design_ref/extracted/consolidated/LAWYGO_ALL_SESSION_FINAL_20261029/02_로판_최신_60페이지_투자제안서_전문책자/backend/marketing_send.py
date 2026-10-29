"""Permission-only opt-in email preview / small-batch CLI. Never called on startup.
Default dry run. --send requires explicit operator flag and SMTP configured.
"""
import argparse,sys,os,hashlib,secrets
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from app import database, BASE_URL, mail, now, check_mail_ready
ROOT=Path(__file__).resolve().parent.parent
p=argparse.ArgumentParser();p.add_argument('--send',action='store_true');p.add_argument('--limit',type=int,default=10)
a=p.parse_args()
if a.send and os.getenv('PAN_ENABLE_MARKETING_SEND')!='YES':raise SystemExit('PAN_ENABLE_MARKETING_SEND=YES required for live sending.')
with database() as db:
    rows=db.execute('SELECT email FROM members WHERE verified=1 AND marketing_consent=1 LIMIT ?', (max(1,min(a.limit,100)),)).fetchall()
print('Explicit verified opted-in recipients:',len(rows),'mode:', 'SEND' if a.send else 'DRY RUN')
if a.send:check_mail_ready()
for row in rows:
    email=row['email']
    if not a.send:print('Preview target:',email);continue
    token=secrets.token_urlsafe(36)
    url=BASE_URL+'/unsubscribe?token='+token
    text=(ROOT/'marketing'/'email-campaign.txt').read_text().replace('{{UNSUBSCRIBE_URL}}',url)
    email_html=(ROOT/'marketing'/'email-campaign.html').read_text().replace('{{UNSUBSCRIBE_URL}}',url)
    subj='[광고] 변호사를 위한 새로운 콘텐츠 채널, LAWYGO PAN 무료 가입 안내'
    try:
        mail(email,subj,text,{'List-Unsubscribe':f'<{url}>','List-Unsubscribe-Post':'List-Unsubscribe=One-Click'},html_body=email_html)
    except Exception as exc:
        print('Failed:',email,str(exc)[:150]);continue
    with database() as db:
        db.execute('UPDATE members SET unsub_hash=? WHERE email=?',(hashlib.sha256(token.encode()).hexdigest(),email))
        db.execute('INSERT INTO mail_sends(email,subject,status,created_at) VALUES (?,?,?,?)',(email,subj,'sent',now()));db.commit()
    print('Sent:',email)
