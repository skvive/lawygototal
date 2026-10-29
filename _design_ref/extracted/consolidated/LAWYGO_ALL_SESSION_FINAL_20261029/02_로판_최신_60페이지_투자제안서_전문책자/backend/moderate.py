"""Operator-only CLI for verified-content approval and private contact routing.
Review identity and ownership OUTSIDE this script; the CLI cannot establish them.
"""
import argparse,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
from app import database
p=argparse.ArgumentParser()
p.add_argument('command',choices=['list','approve','assign-profile'])
p.add_argument('--id',type=int)
p.add_argument('--slug')
p.add_argument('--email')
a=p.parse_args()
with database() as db:
 if a.command=='list':
  for row in db.execute('SELECT id,email,content_type,title,url,approved FROM content_submissions ORDER BY id DESC LIMIT 100'):print(dict(row))
 if a.command=='approve':
  if not a.id:raise SystemExit('--id required')
  row=db.execute('SELECT id,email,url FROM content_submissions WHERE id=?',(a.id,)).fetchone()
  if not row:raise SystemExit('No record')
  print('Operator must manually confirm lawyer identity and URL content ownership:',dict(row))
  if input('Confirm approval by typing APPROVE: ')!='APPROVE':raise SystemExit('Canceled')
  db.execute('UPDATE content_submissions SET approved=1 WHERE id=?',(a.id,));db.commit();print('Approved')
 if a.command=='assign-profile':
  if not a.slug or not a.email:raise SystemExit('--slug and --email required')
  row=db.execute('SELECT email,verified,lawyer_verified FROM members WHERE email=?',(a.email,)).fetchone()
  if not row or not row['verified'] or not row['lawyer_verified']:
   raise SystemExit('Account has not passed both email and independent lawyer verification. Cannot activate.')
  print('Confirm identity-verified profile',a.slug,'=>',a.email)
  if input('Type APPROVE: ')!='APPROVE':raise SystemExit('Canceled')
  db.execute('CREATE TABLE IF NOT EXISTS profile_routes (slug TEXT PRIMARY KEY,member_email TEXT NOT NULL,activated INTEGER DEFAULT 0)')
  db.execute('INSERT INTO profile_routes(slug,member_email,activated) VALUES (?,?,1) ON CONFLICT(slug) DO UPDATE SET member_email=excluded.member_email,activated=1',(a.slug,a.email))
  db.commit();print('Profile route enabled')
