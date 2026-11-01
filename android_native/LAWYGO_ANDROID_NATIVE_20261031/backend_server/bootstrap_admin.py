"""Create admin / other user accounts locally; no hard-coded default credentials."""
import argparse, uuid
from app import init_db, connect, PH, now
parser=argparse.ArgumentParser()
parser.add_argument('--email',required=True)
parser.add_argument('--password',required=True)
parser.add_argument('--name',default='관리자')
parser.add_argument('--role',choices=['admin','editor','contributor','viewer'],default='admin')
parser.add_argument('--tenant',default='demo')
args=parser.parse_args()
if len(args.password)<12:parser.error('비밀번호는 12자 이상으로 설정하세요.')
init_db()
with connect() as db:
    db.execute('INSERT INTO users(id,tenant,email,password_hash,display_name,role,created_at) VALUES(?,?,?,?,?,?,?)', (uuid.uuid4().hex,args.tenant,args.email.strip().lower(),PH.hash(args.password),args.name,args.role,now()))
print('사용자 생성 성공: '+args.email+' / '+args.role)
