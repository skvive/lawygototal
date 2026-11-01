"""Non-destructive configuration and local-state check. Never print secret values."""
from __future__ import annotations
import json,os,sqlite3,sys
from pathlib import Path
from dotenv import load_dotenv
ROOT=Path(__file__).resolve().parent
load_dotenv(ROOT/'.env')
checks=[]
def add(name,ok,info=''):
    checks.append(dict(name=name,ok=bool(ok),info=info))
for page in ('index.html','hub.html','dashboard.html','journal.html','editor-v5.html','pan-v5.html','wiki-v5.html','note-v5.html','pro-v5.html'):
    add('static:'+page,(ROOT/'static'/page).is_file())
db=Path(os.environ.get('LAWYGO_DB_PATH',ROOT/'data'/'lawygo.db'))
add('database path available',db.parent.exists(),str(db.parent))
if db.exists():
    try:
        with sqlite3.connect(db) as conn:
            result=conn.execute('PRAGMA quick_check').fetchone()[0]
            add('database integrity',result=='ok',result)
    except Exception as exc:add('database integrity',False,type(exc).__name__)
else:add('database created on first run',True)
keys={
'Google login':['GOOGLE_CLIENT_ID','GOOGLE_CLIENT_SECRET','GOOGLE_REDIRECT_URI'],
'Blogger/YouTube':['GOOGLE_CLIENT_ID','GOOGLE_CLIENT_SECRET','LAWYGO_TOKEN_ENCRYPTION_KEY'],
'Gemini':['GEMINI_API_KEY'],
'Native LAWYGO bridge':['LAWYGO_NATIVE_BRIDGE_URL','LAWYGO_NATIVE_BRIDGE_SECRET'],
'SMTP':['LAWYGO_NEWSLETTER_SMTP_HOST','LAWYGO_NEWSLETTER_FROM'],
}
for label,requirements in keys.items():
    configured=all(os.environ.get(k) for k in requirements)
    checks.append({'name':'external:'+label,'ok':configured,'info':'configured' if configured else 'requires operator credentials'})
print(json.dumps(checks,ensure_ascii=False,indent=2))
# External integrations are optional; only local core readiness is a fatal check.
sys.exit(0 if all(x['ok'] for x in checks if not x['name'].startswith('external:')) else 1)
