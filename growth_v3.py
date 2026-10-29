"""LAWYGO v3 growth & operations.
No live advertising/transaction claims: all data is server-generated from events, explicit review, and subscription webhook.
"""
import hashlib, hmac, json, os, secrets, sqlite3, time, uuid
from datetime import datetime, timezone
from urllib.parse import urlparse
from fastapi import Depends, Request, Response, Query
from pydantic import BaseModel, Field, field_validator

PRODUCT_SET = {'channel','wiki','pan','note'}
EVENTS = {'impression','profile_open','consult_click','content_open','newsletter_click'}

def stamp(): return datetime.now(timezone.utc).isoformat()
def schema(db):
    db.executescript('''
    CREATE TABLE IF NOT EXISTS growth_campaigns(
      id TEXT PRIMARY KEY, tenant TEXT NOT NULL, product TEXT NOT NULL, name TEXT NOT NULL,
      post_id TEXT NOT NULL REFERENCES posts(id),status TEXT NOT NULL CHECK(status IN ('draft','active','paused','ended')),
      priority INTEGER NOT NULL DEFAULT 10, starts_at TEXT, ends_at TEXT,created_by TEXT NOT NULL,
      created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS ix_growth_campaigns ON growth_campaigns(tenant,product,status,priority);
    CREATE TABLE IF NOT EXISTS growth_events(
      id TEXT PRIMARY KEY,tenant TEXT NOT NULL,post_id TEXT NOT NULL REFERENCES posts(id),
      event_type TEXT NOT NULL, day TEXT NOT NULL,visitor_hash TEXT NOT NULL,created_at TEXT NOT NULL,
      UNIQUE(tenant,post_id,event_type,day,visitor_hash));
    CREATE INDEX IF NOT EXISTS ix_growth_events ON growth_events(tenant,day,event_type);
    CREATE TABLE IF NOT EXISTS lawyer_verifications(
      user_id TEXT NOT NULL REFERENCES users(id),tenant TEXT NOT NULL,
      professional_number TEXT NOT NULL,status TEXT NOT NULL CHECK(status IN ('pending','approved','rejected')),
      checked_by TEXT,checked_at TEXT,created_at TEXT NOT NULL,PRIMARY KEY(user_id,tenant));
    CREATE TABLE IF NOT EXISTS growth_entitlements(
      user_id TEXT NOT NULL REFERENCES users(id),tenant TEXT NOT NULL,plan TEXT NOT NULL,
      provider_subscription_id TEXT NOT NULL UNIQUE,expires_at TEXT,status TEXT NOT NULL,
      updated_at TEXT NOT NULL,PRIMARY KEY(user_id,tenant,plan));
    CREATE TABLE IF NOT EXISTS growth_webhook_receipts(
      event_id TEXT PRIMARY KEY,received_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS newsletter_subscribers(
      id TEXT PRIMARY KEY,tenant TEXT NOT NULL,email TEXT NOT NULL,email_hash TEXT NOT NULL,
      status TEXT NOT NULL,verify_token_hash TEXT,unsubscribe_token_hash TEXT,
      consent_at TEXT NOT NULL,verified_at TEXT,unsubscribed_at TEXT,
      UNIQUE(tenant,email_hash));
    CREATE TABLE IF NOT EXISTS newsletter_issues(
      id TEXT PRIMARY KEY,tenant TEXT NOT NULL,issue_month TEXT NOT NULL,subject TEXT NOT NULL,
      body TEXT NOT NULL,created_by TEXT NOT NULL,created_at TEXT NOT NULL);
    CREATE INDEX IF NOT EXISTS ix_newsletter_issues_month ON newsletter_issues(tenant,issue_month);
    CREATE TABLE IF NOT EXISTS newsletter_deliveries(
      id TEXT PRIMARY KEY,issue_id TEXT NOT NULL REFERENCES newsletter_issues(id),subscriber_id TEXT NOT NULL REFERENCES newsletter_subscribers(id),status TEXT NOT NULL,sent_at TEXT NOT NULL,
      UNIQUE(issue_id,subscriber_id));
    CREATE TABLE IF NOT EXISTS growth_diagnostics(
      id TEXT PRIMARY KEY,tenant TEXT NOT NULL,kind TEXT NOT NULL,summary TEXT NOT NULL,created_at TEXT NOT NULL);
    ''')

def register(app, g):
    current=g['current_user'];csrf=g['csrf'];database=g['database'];get_post=g['get_post'];get_board=g['get_board'];err=g['err'];audit=g['audit'];transaction=g['transaction']
    class CampaignIn(BaseModel):
        product:str
        post_id:str
        name:str=Field(min_length=2,max_length=120)
        priority:int=Field(default=10,ge=1,le=100)
        status:str='draft'
        starts_at:str|None=None
        ends_at:str|None=None
    class ReorderIn(BaseModel):
        product:str
        ids:list[str]=Field(min_length=1,max_length=100)
    class VerifyIn(BaseModel):
        professional_number:str=Field(min_length=4,max_length=80)
    class VerifyDecision(BaseModel):
        approved:bool
    class EventIn(BaseModel):
        post_id:str
        event_type:str
    class SubscribeIn(BaseModel):
        email:str=Field(min_length=5,max_length=254)
        consent:bool
    class CheckToken(BaseModel):
        token:str=Field(min_length=20,max_length=128)
    class PaymentEvent(BaseModel):
        event_id:str=Field(min_length=8,max_length=128)
        user_id:str
        tenant:str
        plan:str
        subscription_id:str
        status:str
        expires_at:str|None=None

    def is_staff(user):
        if user['role'] not in ('admin','editor'):err(403,'승인된 운영자 권한이 필요합니다.')
    def is_admin(user):
        if user['role']!='admin':err(403,'관리자 권한이 필요합니다.')

    @app.get('/api/growth/campaigns')
    def campaign_list(user=Depends(current),db=Depends(database)):
        is_staff(user)
        rows=db.execute('''SELECT c.*,p.title FROM growth_campaigns c JOIN posts p ON c.post_id=p.id
          WHERE c.tenant=? ORDER BY c.priority ASC,c.updated_at DESC LIMIT 250''',(user['tenant'],)).fetchall()
        return {'items':[dict(r) for r in rows]}

    @app.post('/api/growth/campaigns',status_code=201)
    def campaign_create(body:CampaignIn,user=Depends(csrf),db=Depends(database)):
        is_staff(user)
        if body.product not in ('channel','wiki','pan'):err(422,'노트는 광고할 수 없습니다.')
        if body.status not in ('draft','active','paused','ended'):err(422,'상태가 올바르지 않습니다.')
        p=get_post(db,body.post_id,user['tenant'])
        if p['product']!=body.product or p['status']!='published' or p['visibility']!='public' or p['deleted_at']:
            err(409,'검수되어 공개된 콘텐츠만 캠페인에 등록할 수 있습니다.')
        if body.status=='active' and not p['is_sponsored']:err(409,'광고 표시가 없는 콘텐츠는 캠페인으로 활성화할 수 없습니다.')
        if body.starts_at and body.ends_at and body.ends_at<=body.starts_at:err(422,'시작·종료 시각을 확인해 주세요.')
        cid=uuid.uuid4().hex
        with transaction(db):
            db.execute('''INSERT INTO growth_campaigns(id,tenant,product,name,post_id,status,priority,starts_at,ends_at,created_by,created_at,updated_at)
              VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',(cid,user['tenant'],body.product,body.name,body.post_id,body.status,body.priority,body.starts_at,body.ends_at,user['id'],stamp(),stamp()))
            audit(db,user,'create','campaign',cid,{'status':body.status})
        return {'id':cid,'status':body.status}

    @app.patch('/api/growth/campaigns/{cid}')
    def campaign_change(cid:str,body:dict,user=Depends(csrf),db=Depends(database)):
        is_staff(user)
        item=db.execute('SELECT * FROM growth_campaigns WHERE tenant=? AND id=?',(user['tenant'],cid)).fetchone()
        if not item:err(404,'캠페인이 없습니다.')
        if set(body)-{'name','status','priority','starts_at','ends_at'}:err(422,'허용되지 않은 수정값입니다.')
        if 'status' in body and body['status'] not in ('draft','active','paused','ended'):err(422,'상태 값 오류')
        if 'name' in body and (not isinstance(body['name'],str) or not 2<=len(body['name'])<=120):err(422,'이름 값 오류')
        if 'priority' in body and (type(body['priority']) is not int or not 1<=body['priority']<=100):err(422,'순서 값 오류')
        if body.get('status')=='active':
            p=get_post(db,item['post_id'],user['tenant'])
            if p['status']!='published' or p['deleted_at'] or not p['is_sponsored']:err(409,'공개 승인·광고 표시를 먼저 완료하세요.')
        fields=dict(body);fields['updated_at']=stamp()
        with transaction(db):
            db.execute('UPDATE growth_campaigns SET '+','.join(f'{x}=?' for x in fields)+' WHERE tenant=? AND id=?',(*fields.values(),user['tenant'],cid))
            audit(db,user,'update','campaign',cid,body)
        return {'ok':True}

    @app.post('/api/growth/campaigns/reorder')
    def campaign_reorder(body:ReorderIn,user=Depends(csrf),db=Depends(database)):
        is_staff(user)
        if body.product not in ('channel','wiki','pan') or len(body.ids)!=len(set(body.ids)):err(422,'중복되거나 잘못된 정렬입니다.')
        with transaction(db):
            actual=db.execute('SELECT id FROM growth_campaigns WHERE tenant=? AND product=?',(user['tenant'],body.product)).fetchall()
            if set(body.ids)!={r['id'] for r in actual}:err(409,'동일 서비스의 캠페인 전체를 보내주세요.')
            for ix,cid in enumerate(body.ids):db.execute('UPDATE growth_campaigns SET priority=?,updated_at=? WHERE tenant=? AND id=?',(ix+1,stamp(),user['tenant'],cid))
            audit(db,user,'reorder','campaigns',body.product)
        return {'ok':True,'count':len(body.ids)}

    @app.post('/api/boards/reorder')
    def board_reorder(body:ReorderIn,user=Depends(csrf),db=Depends(database)):
        is_staff(user)
        if body.product not in PRODUCT_SET or len(body.ids)!=len(set(body.ids)):err(422,'정렬 요청이 올바르지 않습니다.')
        with transaction(db):
            current_ids={r['id'] for r in db.execute('SELECT id FROM boards WHERE tenant=? AND product=? AND deleted_at IS NULL',(user['tenant'],body.product))}
            if set(body.ids)!=current_ids:err(409,'이 서비스의 모든 활성 게시판을 정렬 목록에 포함해 주세요.')
            for ix,bid in enumerate(body.ids):db.execute('UPDATE boards SET sort_order=?,updated_at=? WHERE tenant=? AND id=?',(ix,stamp(),user['tenant'],bid))
            audit(db,user,'reorder','boards',body.product)
        return {'ok':True}

    @app.post('/api/pan/verification')
    def verification_submit(body:VerifyIn,user=Depends(csrf),db=Depends(database)):
        # Claim is not an approval; administrators must check official bar registration out-of-band.
        with transaction(db):
            db.execute('''INSERT INTO lawyer_verifications(user_id,tenant,professional_number,status,created_at)
             VALUES(?,?,?,?,?) ON CONFLICT(user_id,tenant) DO UPDATE SET professional_number=excluded.professional_number,status='pending',checked_by=NULL,checked_at=NULL''',
             (user['id'],user['tenant'],body.professional_number,'pending',stamp()))
            audit(db,user,'submit','lawyer_verification',user['id'])
        return {'status':'pending','notice':'대한변호사협회 등록 여부 확인 후 승인됩니다.'}

    @app.get('/api/pan/verification')
    def verification_list(user=Depends(current),db=Depends(database)):
        if user['role']=='admin':
            rows=db.execute('SELECT user_id,status,professional_number,created_at FROM lawyer_verifications WHERE tenant=? ORDER BY created_at DESC',(user['tenant'],))
        else:rows=db.execute('SELECT user_id,status,professional_number,created_at FROM lawyer_verifications WHERE tenant=? AND user_id=?',(user['tenant'],user['id']))
        return {'items':[dict(x) for x in rows]}

    @app.patch('/api/pan/verification/{uid}')
    def verification_decide(uid:str,body:VerifyDecision,user=Depends(csrf),db=Depends(database)):
        is_admin(user)
        v=db.execute('SELECT * FROM lawyer_verifications WHERE tenant=? AND user_id=?',(user['tenant'],uid)).fetchone()
        if not v:err(404,'요청이 없습니다.')
        with transaction(db):
            db.execute('UPDATE lawyer_verifications SET status=?,checked_by=?,checked_at=? WHERE tenant=? AND user_id=?',
                       ('approved' if body.approved else 'rejected',user['id'],stamp(),user['tenant'],uid))
            audit(db,user,'verify','lawyer_verification',uid,{'approved':body.approved})
        return {'ok':True}

    @app.post('/api/growth/events')
    def event_ingest(body:EventIn,req:Request,response:Response,db=Depends(database)):
        if body.event_type not in EVENTS:err(422,'지원하지 않는 집계 유형입니다.')
        # No request body supplied user identifier, email, IP address or fingerprint stored.
        p=get_post(db,body.post_id,g['DEFAULT_TENANT'])
        if p['status']!='published' or p['visibility']!='public' or p['deleted_at'] or p['product']=='note':err(404,'공개 콘텐츠가 아닙니다.')
        visit=req.cookies.get('lawygo_v3_visit','')
        if not 32<=len(visit)<=64 or not all(c in '0123456789abcdef' for c in visit):
            visit=secrets.token_hex(24)
            response.set_cookie('lawygo_v3_visit',visit,max_age=86400,httponly=True,secure=os.getenv('LAWYGO_SECURE_COOKIES','0')=='1',samesite='lax')
        day=stamp()[:10];hashed=hashlib.sha256((day+'|'+visit).encode()).hexdigest()
        db.execute('INSERT OR IGNORE INTO growth_events VALUES(?,?,?,?,?,?,?)',(uuid.uuid4().hex,p['tenant'],p['id'],body.event_type,day,hashed,stamp()))
        return {'ok':True}

    @app.get('/api/growth/analytics')
    def analytics(user=Depends(current),db=Depends(database)):
        is_staff(user)
        period=stamp()[:7]
        rows=db.execute('''SELECT p.product,e.event_type,count(*) count FROM growth_events e JOIN posts p ON p.id=e.post_id
            WHERE e.tenant=? AND e.day LIKE ? GROUP BY p.product,e.event_type''',(user['tenant'],period+'%')).fetchall()
        return {'month':period,'events':[dict(r) for r in rows],'disclaimer':'중복 축소된 참고용 웹 이벤트입니다. 확정 상담·매출 실적이 아닙니다.'}

    @app.get('/api/growth/feed')
    def feed(product:str='pan',db=Depends(database)):
        if product not in ('channel','wiki','pan'):err(422,'지원하지 않는 공개 서비스입니다.')
        tm=stamp()
        sponsored=db.execute('''SELECT p.id,p.product,p.title,p.summary,p.kind,p.external_url,p.updated_at,p.is_sponsored
         FROM growth_campaigns c JOIN posts p ON c.post_id=p.id WHERE c.tenant=? AND c.product=? AND c.status='active'
           AND (c.starts_at IS NULL OR c.starts_at<=?) AND (c.ends_at IS NULL OR c.ends_at>=?)
           AND p.status='published' AND p.visibility='public' AND p.deleted_at IS NULL AND p.is_sponsored=1
         ORDER BY c.priority ASC LIMIT 5''',(g['DEFAULT_TENANT'],product,tm,tm)).fetchall()
        regular=db.execute('''SELECT id,product,title,summary,kind,external_url,updated_at,is_sponsored FROM posts
          WHERE tenant=? AND product=? AND status='published' AND visibility='public' AND deleted_at IS NULL
          ORDER BY updated_at DESC LIMIT 30''',(g['DEFAULT_TENANT'],product)).fetchall()
        seen=set();out=[]
        for x in list(sponsored)+list(regular):
            if x['id'] in seen:continue
            seen.add(x['id']);rec=dict(x);rec['placement']='광고' if any(x['id']==a['id'] for a in sponsored) else ('광고' if x['is_sponsored'] else '일반');out.append(rec)
        return {'items':out,'note':'후원 우선 노출은 광고로 표시되며 전문성 순위를 뜻하지 않습니다.'}

    @app.get('/api/growth/entitlements')
    def entitlements(user=Depends(current),db=Depends(database)):
        rows=db.execute('''SELECT plan,status,expires_at,updated_at FROM growth_entitlements WHERE tenant=? AND user_id=?''',(user['tenant'],user['id'])).fetchall()
        current=[]
        for r in rows:
            v=dict(r);v['active']=v['status']=='active' and (not v['expires_at'] or v['expires_at']>stamp());current.append(v)
        return {'items':current,'notice':'가입·구독 상태는 서버가 검증한 결제 이벤트로만 변경됩니다.'}

    @app.post('/api/growth/billing/webhook')
    async def billing_webhook(req:Request,db=Depends(database)):
        key=os.getenv('LAWYGO_BILLING_WEBHOOK_KEY','')
        if len(key)<32:err(503,'결제 연동이 아직 설정되지 않았습니다.')
        raw=await req.body()
        if len(raw)>32768:err(413,'이벤트 용량 초과')
        try: ts=int(req.headers.get('x-lawygo-timestamp',''));signed=req.headers.get('x-lawygo-signature','')
        except ValueError:err(401,'서명 정보 오류')
        if abs(int(time.time())-ts)>300:err(401,'서명 만료')
        expect=hmac.new(key.encode(),str(ts).encode()+b'.'+raw,hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signed,expect):err(401,'결제 이벤트 서명 오류')
        try: data=PaymentEvent.model_validate_json(raw)
        except Exception:err(422,'결제 이벤트 형식 오류')
        if data.status not in ('active','canceled','past_due','unpaid') or data.plan not in ('journal_plus','wiki','note','pan','pro','suite'):
            err(422,'지원하지 않는 결제 이벤트입니다.')
        u=db.execute('SELECT 1 FROM users WHERE id=? AND tenant=?',(data.user_id,data.tenant)).fetchone()
        if not u:err(404,'존재하지 않는 회원')
        with transaction(db):
            if db.execute('SELECT 1 FROM growth_webhook_receipts WHERE event_id=?',(data.event_id,)).fetchone():return {'ok':True,'duplicate':True}
            db.execute('INSERT INTO growth_webhook_receipts VALUES(?,?)',(data.event_id,stamp()))
            db.execute('''INSERT INTO growth_entitlements(user_id,tenant,plan,provider_subscription_id,expires_at,status,updated_at)
              VALUES(?,?,?,?,?,?,?) ON CONFLICT(user_id,tenant,plan) DO UPDATE SET status=excluded.status,expires_at=excluded.expires_at,updated_at=excluded.updated_at''',
              (data.user_id,data.tenant,data.plan,data.subscription_id,data.expires_at,data.status,stamp()))
        return {'ok':True}

    @app.get('/api/growth/system')
    def system(user=Depends(current),db=Depends(database)):
        is_staff(user)
        return {'database':'connected','google_oauth':bool(os.getenv('GOOGLE_CLIENT_ID')),
           'gemini':bool(os.getenv('GEMINI_API_KEY')),'native_bridge':bool(os.getenv('LAWYGO_NATIVE_BRIDGE_URL')),
           'billing_webhook':len(os.getenv('LAWYGO_BILLING_WEBHOOK_KEY',''))>=32,
           'email':'pending_server_configuration','live_e2e':'not_verified'}
