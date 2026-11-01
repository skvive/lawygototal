"""LAWYGO Modular Operations Hub v4. Uses the existing local LAWYGO session/SQLite.
No arbitrary plugin execution. Readiness indicators are configuration, not third-party proof.
"""
import csv, io, json, os, sqlite3, uuid
from datetime import datetime, timezone, timedelta
from typing import Literal
from fastapi import Depends, Response, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

PRODUCTS={'channel':'채널','wiki':'위키','pan':'판','note':'노트','journal':'저널','pro':'프로'}
TYPES={'board','analytics','integration','newsletter','billing','workspace','dashboard'}
SERVICES={
 'channel':('/p/channel','공개 콘텐츠 발행·승인·영상 큐레이션'),
 'wiki':('/p/wiki','판례·법령·검수된 법률백과'),
 'pan':('/p/pan','변호사 콘텐츠·마케팅·상담 유입'),
 'note':('/p/note','비공개 문서와 법률 AI 노트'),
 'journal':('/','경제·법률 인사이트·뉴스레터'),
 'pro':('/','전문가 송무 관리·업무 협업'),
}
CORE = [
 ('channel','법률 채널 운영','board','news'),('wiki','법률백과 운영','board','encyclopedia'),
 ('pan','전문가 마케팅 운영','board','lawyers'),('note','비공개 연구 노트','board','projects'),
 ('journal','뉴스레터 편집·구독','newsletter',None),('pro','송무·법인 운영 연계','integration',None),
 ('pan','광고 운영·실적','analytics',None),('channel','Blogger · YouTube 연동','integration',None),
 ('note','법률 AI · 파일 분석','integration',None),('pan','Stripe 구독 권한','billing',None),
]
INTEGRATIONS={
 'google_oauth':('GOOGLE_CLIENT_ID','GOOGLE_CLIENT_SECRET'),
 'blogger':('GOOGLE_CLIENT_ID','GOOGLE_CLIENT_SECRET'),
 'youtube':('GOOGLE_CLIENT_ID','GOOGLE_CLIENT_SECRET'),
 'gemini':('GEMINI_API_KEY',),
 'lawygo_native':('LAWYGO_NATIVE_URL','LAWYGO_NATIVE_BRIDGE_SECRET'),
 'billing':('LAWYGO_BILLING_WEBHOOK_KEY',),
 'smtp':('SMTP_HOST','SMTP_USER','SMTP_PASSWORD'),
}

def stamp():return datetime.now(timezone.utc).isoformat()
def obj(r):return dict(r) if r else None

def schema(db):
 db.executescript('''
 CREATE TABLE IF NOT EXISTS hub_modules (
 id TEXT PRIMARY KEY,tenant TEXT NOT NULL, product TEXT NOT NULL,
 module_type TEXT NOT NULL,name TEXT NOT NULL,description TEXT NOT NULL DEFAULT '',
 board_id TEXT, config TEXT NOT NULL DEFAULT '{}',enabled INTEGER NOT NULL DEFAULT 1,
 sort_order INTEGER NOT NULL DEFAULT 0, version INTEGER NOT NULL DEFAULT 1,
 built_in INTEGER NOT NULL DEFAULT 0, created_by TEXT NOT NULL DEFAULT 'system',
 deleted_at TEXT,created_at TEXT NOT NULL,updated_at TEXT NOT NULL,
 FOREIGN KEY(board_id) REFERENCES boards(id));
 CREATE INDEX IF NOT EXISTS idx_hub_modules ON hub_modules(tenant,product,deleted_at,sort_order);
 CREATE TABLE IF NOT EXISTS hub_jobs (
 id TEXT PRIMARY KEY,tenant TEXT NOT NULL,kind TEXT NOT NULL,
 status TEXT NOT NULL CHECK(status IN ('queued','running','done','failed')),
 requested_by TEXT NOT NULL,payload TEXT NOT NULL DEFAULT '{}',result TEXT,
 created_at TEXT NOT NULL,started_at TEXT,finished_at TEXT);
 CREATE TABLE IF NOT EXISTS hub_snapshots (
 id TEXT PRIMARY KEY,tenant TEXT NOT NULL,month TEXT NOT NULL,metric TEXT NOT NULL,
 value INTEGER NOT NULL,created_at TEXT NOT NULL);
 CREATE INDEX IF NOT EXISTS idx_hub_snapshots ON hub_snapshots(tenant,month,metric);
 ''')
 for tenant in (db.execute('SELECT DISTINCT tenant FROM users').fetchall()):
  _seed_tenant(db,tenant['tenant'])

def _seed_tenant(db,tenant):
 present=db.execute('SELECT count(*) n FROM hub_modules WHERE tenant=?',(tenant,)).fetchone()['n']
 if present:return
 for index,(product,name,typ,slug) in enumerate(CORE):
  board=(db.execute('SELECT id FROM boards WHERE tenant=? AND product=? AND slug=? AND deleted_at IS NULL',(tenant,product,slug)).fetchone() if slug else None)
  db.execute('INSERT INTO hub_modules(id,tenant,product,module_type,name,description,board_id,config,sort_order,built_in,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)',(
   uuid.uuid4().hex,tenant,product,typ,name,SERVICES[product][1],board['id'] if board else None,'{}',index,1,stamp(),stamp()))

def register(app,g):
 database=g['database'];current=g['current_user'];csrf=g['csrf'];audit=g['audit'];transaction=g['transaction'];err=g['err']
 def staff(u):
  if u['role'] not in ('admin','editor'):err(403,'운영자 권한이 필요합니다.')
 def admin(u):
  if u['role']!='admin':err(403,'관리자 권한이 필요합니다.')
 class ModuleCreate(BaseModel):
  product:Literal['channel','wiki','pan','note','journal','pro']
  module_type:Literal['board','analytics','integration','newsletter','billing','workspace','dashboard']
  name:str=Field(min_length=2,max_length=80)
  description:str=Field(default='',max_length=360)
  board_id:str|None=None
  create_board_slug:str|None=Field(default=None,pattern=r'^[a-z][a-z0-9-]{1,40}$')
  enabled:bool=True
 class ModuleEdit(BaseModel):
  version:int=Field(ge=1)
  name:str|None=Field(default=None,min_length=2,max_length=80)
  description:str|None=Field(default=None,max_length=360)
  enabled:bool|None=None
 class Reorder(BaseModel):
  product:Literal['channel','wiki','pan','note','journal','pro']
  ids:list[str]=Field(min_length=1,max_length=100)
 class JobCreate(BaseModel):
  kind:Literal['snapshot_metrics','check_dependencies','count_pending_content']

 def _one(db,id,tenant,deleted=False):
  row=db.execute('SELECT * FROM hub_modules WHERE id=? AND tenant=?'+('' if deleted else ' AND deleted_at IS NULL'),(id,tenant)).fetchone()
  if not row:err(404,'모듈을 찾을 수 없습니다.')
  return dict(row)
 def _format(row):
  d=dict(row);d['enabled']=bool(d['enabled']);d['built_in']=bool(d['built_in']);d['config']=json.loads(d['config']);return d

 @app.get('/api/hub/modules')
 def modules(product:str|None=None,user=Depends(current),db=Depends(database)):
  if product and product not in PRODUCTS:err(422,'서비스 종류가 유효하지 않습니다.')
  _seed_tenant(db,user['tenant'])
  rows=db.execute('SELECT * FROM hub_modules WHERE tenant=? AND deleted_at IS NULL'+(' AND product=?' if product else '')+' ORDER BY product,sort_order,created_at',([user['tenant'],product] if product else [user['tenant']])).fetchall()
  return {'items':[_format(r) for r in rows]}

 @app.post('/api/hub/modules',status_code=201)
 def create_module(data:ModuleCreate,user=Depends(csrf),db=Depends(database)):
  admin(user)
  if data.create_board_slug and (data.module_type!='board' or data.product in ('journal','pro')):err(422,'게시판 생성은 로이고 채널·위키·판·노트 모듈에서만 가능합니다.')
  if data.module_type=='board' and data.product in ('journal','pro'):err(422,'저널·프로의 기존 게시판 DB는 현재 별도 엔진입니다.')
  if data.module_type!='board' and (data.board_id or data.create_board_slug):err(422,'게시판 유형만 게시판을 연결할 수 있습니다.')
  board_id=data.board_id
  if data.module_type=='board' and not (board_id or data.create_board_slug):err(422,'연결할 게시판을 지정하거나 새 게시판을 생성하세요.')
  bid=uuid.uuid4().hex;mid=uuid.uuid4().hex
  with transaction(db):
   if board_id:
    board=db.execute('SELECT id FROM boards WHERE tenant=? AND product=? AND id=? AND deleted_at IS NULL',(user['tenant'],data.product,board_id)).fetchone()
    if not board:err(404,'선택한 서비스의 게시판이 없습니다.')
   if data.create_board_slug:
    existing=db.execute('SELECT id FROM boards WHERE tenant=? AND product=? AND slug=?',(user['tenant'],data.product,data.create_board_slug)).fetchone()
    if existing:err(409,'같은 게시판 식별자가 존재합니다.')
    db.execute('''INSERT INTO boards(id,tenant,product,slug,name,description,created_at,updated_at)
      VALUES(?,?,?,?,?,?,?,?)''',(bid,user['tenant'],data.product,data.create_board_slug,data.name.strip(),data.description.strip(),stamp(),stamp()))
    board_id=bid
   sort=(db.execute('SELECT COALESCE(max(sort_order),-1)+1 AS n FROM hub_modules WHERE tenant=? AND product=? AND deleted_at IS NULL',(user['tenant'],data.product)).fetchone()['n'])
   db.execute('''INSERT INTO hub_modules(id,tenant,product,module_type,name,description,board_id,enabled,sort_order,created_by,created_at,updated_at)
     VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',(mid,user['tenant'],data.product,data.module_type,data.name.strip(),data.description.strip(),board_id,int(data.enabled),sort,user['id'],stamp(),stamp()))
   audit(db,user,'create','hub_module',mid,{'product':data.product,'type':data.module_type})
  return {'id':mid,'board_id':board_id,'enabled':data.enabled}

 @app.patch('/api/hub/modules/{mid}')
 def update_module(mid:str,data:ModuleEdit,user=Depends(csrf),db=Depends(database)):
  admin(user);m=_one(db,mid,user['tenant']);
  if m['version']!=data.version:err(409,'동시 수정 충돌: 새로고침 후 다시 저장하세요.')
  values=data.model_dump(exclude_none=True,exclude={'version'})
  if not values:err(422,'변경할 항목이 없습니다.')
  if 'enabled' in values:values['enabled']=int(values['enabled'])
  values.update(version=m['version']+1,updated_at=stamp())
  with transaction(db):
   changed=db.execute('UPDATE hub_modules SET '+','.join(x+'=?' for x in values)+
     ' WHERE id=? AND tenant=? AND version=? AND deleted_at IS NULL',
     [*values.values(),mid,user['tenant'],data.version])
   if changed.rowcount != 1:err(409,'다른 운영자가 모듈을 변경했습니다. 새로고침 후 재시도하세요.')
   audit(db,user,'update','hub_module',mid,{'fields':list(values)})
  return {'ok':True,'version':m['version']+1}

 @app.delete('/api/hub/modules/{mid}')
 def remove_module(mid:str,user=Depends(csrf),db=Depends(database)):
  admin(user);m=_one(db,mid,user['tenant']);
  if m['built_in']:err(409,'기본 모듈은 삭제할 수 없습니다. 비활성화하세요.')
  with transaction(db):
   db.execute('UPDATE hub_modules SET deleted_at=?,enabled=0,updated_at=? WHERE id=? AND tenant=?',(stamp(),stamp(),mid,user['tenant']))
   audit(db,user,'delete','hub_module',mid)
  return {'ok':True,'board_preserved':True}

 @app.get('/api/hub/trash')
 def trash(user=Depends(current),db=Depends(database)):
  staff(user);return {'items':[_format(x) for x in db.execute('SELECT * FROM hub_modules WHERE tenant=? AND deleted_at IS NOT NULL ORDER BY deleted_at DESC LIMIT 100',(user['tenant'],))]}

 @app.post('/api/hub/modules/{mid}/restore')
 def restore(mid:str,user=Depends(csrf),db=Depends(database)):
  admin(user);m=_one(db,mid,user['tenant'],True)
  if not m['deleted_at']:err(409,'삭제된 모듈이 아닙니다.')
  with transaction(db):
   db.execute('UPDATE hub_modules SET deleted_at=NULL,enabled=0,version=version+1,updated_at=? WHERE id=? AND tenant=?',(stamp(),mid,user['tenant']));audit(db,user,'restore','hub_module',mid)
  return {'ok':True,'enabled':False}

 @app.post('/api/hub/modules/reorder')
 def reorder(data:Reorder,user=Depends(csrf),db=Depends(database)):
  admin(user)
  if len(data.ids)!=len(set(data.ids)):err(422,'중복된 모듈이 있습니다.')
  real={r['id'] for r in db.execute('SELECT id FROM hub_modules WHERE tenant=? AND product=? AND deleted_at IS NULL',(user['tenant'],data.product))}
  if real!=set(data.ids):err(409,'서비스별 전체 모듈을 정렬 목록에 포함해 주세요.')
  with transaction(db):
   for ix,mid in enumerate(data.ids):db.execute('UPDATE hub_modules SET sort_order=?,updated_at=? WHERE id=? AND tenant=?',(ix,stamp(),mid,user['tenant']))
   audit(db,user,'reorder','hub_modules',data.product)
  return {'ok':True,'count':len(data.ids)}

 def metrics(db,tenant,user_id,days=30):
  cutoff=(datetime.now(timezone.utc)-timedelta(days=days)).date().isoformat()
  posts=[dict(r) for r in db.execute("SELECT product,status,count(*) count FROM posts WHERE tenant=? AND deleted_at IS NULL AND (product!='note' OR author_id=?) GROUP BY product,status",(tenant,user_id))]
  boards=[dict(r) for r in db.execute('SELECT product,count(*) count FROM boards WHERE tenant=? AND deleted_at IS NULL GROUP BY product',(tenant,))]
  campaigns=db.execute("SELECT count(*) n FROM growth_campaigns WHERE tenant=? AND status='active'",(tenant,)).fetchone()['n']
  pending=db.execute("SELECT count(*) n FROM lawyer_verifications WHERE tenant=? AND status='pending'",(tenant,)).fetchone()['n']
  subscribers=db.execute("SELECT count(*) n FROM newsletter_subscribers WHERE tenant=? AND status='active'",(tenant,)).fetchone()['n']
  events=[dict(x) for x in db.execute('SELECT day,event_type,count(*) count FROM growth_events WHERE tenant=? AND day>=? GROUP BY day,event_type ORDER BY day',(tenant,cutoff))]
  jobs=[dict(r) for r in db.execute('SELECT status,count(*) count FROM hub_jobs WHERE tenant=? GROUP BY status',(tenant,))]
  mods=[dict(r) for r in db.execute('SELECT product,enabled,count(*) count FROM hub_modules WHERE tenant=? AND deleted_at IS NULL GROUP BY product,enabled',(tenant,))]
  return {'posts':posts,'boards':boards,'campaigns_active':campaigns,'lawyers_pending':pending,'newsletter_active':subscribers,'events':events,'jobs':jobs,'modules':mods,'period_days':days,'notice':'이벤트·게시글의 집계이며 매출·수임 성과를 뜻하지 않습니다.'}

 @app.get('/api/hub/overview')
 def overview(user=Depends(current),db=Depends(database)):
  _seed_tenant(db,user['tenant']);return metrics(db,user['tenant'],user['id'])

 @app.get('/api/hub/metrics')
 def trends(days:int=Query(default=30,ge=1,le=366),user=Depends(current),db=Depends(database)):
  return metrics(db,user['tenant'],user['id'],days)

 @app.get('/api/hub/metrics.csv')
 def export_csv(user=Depends(current),db=Depends(database)):
  staff(user)
  o=metrics(db,user['tenant'],user['id']);file=io.StringIO();w=csv.writer(file);w.writerow(['day','event','count'])
  for r in o['events']:w.writerow([r['day'],r['event_type'],r['count']]);
  return Response('\ufeff'+file.getvalue(),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="lawygo_metrics.csv"','Cache-Control':'private, no-store'})

 @app.get('/api/hub/health')
 def health(user=Depends(current),db=Depends(database)):
  staff(user)
  items=[]
  for key,required in INTEGRATIONS.items():
   configured=all(bool(os.environ.get(x)) for x in required)
   items.append({'id':key,'configured':configured,'live_verified':False,'status':'설정됨 · 실제 연결 미검증' if configured else '설정 필요'})
  return {'db':'local SQLite · 연결 확인','integrations':items,'note':'환경변수 존재는 실제 인증 또는 외부 API 가용성을 보증하지 않습니다.'}

 @app.post('/api/hub/jobs',status_code=201)
 def submit_job(data:JobCreate,user=Depends(csrf),db=Depends(database)):
  staff(user);jid=uuid.uuid4().hex
  with transaction(db):
   db.execute('INSERT INTO hub_jobs(id,tenant,kind,status,requested_by,created_at) VALUES(?,?,?,?,?,?)',(jid,user['tenant'],data.kind,'queued',user['id'],stamp()))
   audit(db,user,'queue','hub_job',jid,{'kind':data.kind})
  return {'id':jid,'status':'queued'}

 @app.get('/api/hub/jobs')
 def jobs(user=Depends(current),db=Depends(database)):
  staff(user);return {'items':[dict(r) for r in db.execute('SELECT * FROM hub_jobs WHERE tenant=? ORDER BY created_at DESC LIMIT 100',(user['tenant'],))]}

 @app.post('/api/hub/jobs/{jid}/run')
 def run_job(jid:str,user=Depends(csrf),db=Depends(database)):
  staff(user)
  with transaction(db):
   current_job=db.execute('SELECT * FROM hub_jobs WHERE tenant=? AND id=?',(user['tenant'],jid)).fetchone()
   if not current_job:err(404,'작업이 없습니다.')
   if current_job['status']!='queued':err(409,'이미 실행했거나 대기 중이 아닌 작업입니다.')
   db.execute("UPDATE hub_jobs SET status='running',started_at=? WHERE id=?",(stamp(),jid))
  try:
   if current_job['kind']=='snapshot_metrics':
    result=metrics(db,user['tenant'],user['id']);month=stamp()[:7];snap=[]
    for product in PRODUCTS:
     snap.append(('posts_'+product,sum(r['count'] for r in result['posts'] if r['product']==product)))
    snap.extend([('campaigns_active',result['campaigns_active']),('newsletter_active',result['newsletter_active'])])
    with transaction(db):
     for metric,value in snap:db.execute('INSERT INTO hub_snapshots VALUES(?,?,?,?,?,?)',(uuid.uuid4().hex,user['tenant'],month,metric,value,stamp()))
    value={'recorded':len(snap),'month':month}
   elif current_job['kind']=='check_dependencies':
    value={'configured':sum(all(os.environ.get(x) for x in req) for req in INTEGRATIONS.values()),'total':len(INTEGRATIONS),'external_calls_made':0}
   elif current_job['kind']=='count_pending_content':
    value={'pending':db.execute("SELECT count(*) n FROM posts WHERE tenant=? AND status='pending' AND deleted_at IS NULL AND product!='note'",(user['tenant'],)).fetchone()['n']}
   else:raise ValueError('허용되지 않은 작업')
   with transaction(db):
    db.execute("UPDATE hub_jobs SET status='done',result=?,finished_at=? WHERE tenant=? AND id=?",(json.dumps(value,ensure_ascii=False),stamp(),user['tenant'],jid));audit(db,user,'run','hub_job',jid,value)
   return {'ok':True,'result':value}
  except Exception:
   with transaction(db):db.execute("UPDATE hub_jobs SET status='failed',result=?,finished_at=? WHERE tenant=? AND id=?",(json.dumps({'error':'작업 실패'},ensure_ascii=False),stamp(),user['tenant'],jid))
   raise

 @app.get('/api/hub/snapshots')
 def snapshots(user=Depends(current),db=Depends(database)):
  staff(user);return {'items':[dict(r) for r in db.execute('SELECT month,metric,value,created_at FROM hub_snapshots WHERE tenant=? ORDER BY created_at DESC LIMIT 100',(user['tenant'],))]}

 @app.get('/hub')
 def hub_page():
  from fastapi.responses import FileResponse
  return FileResponse(g['ROOT']/'static'/'hub.html')
