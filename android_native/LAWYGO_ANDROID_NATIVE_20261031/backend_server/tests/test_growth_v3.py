"""Business workflows and negative security cases for growth v3."""
import os,sys,uuid,time,hmac,hashlib,json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
ROOT_TEST=ROOT/'tests'/'_growth_instance'
os.environ['LAWYGO_DB_PATH']=str(ROOT_TEST/'test.db')
os.environ['LAWYGO_UPLOAD_PATH']=str(ROOT_TEST/'uploads')
from app import app,connect,PH,now

@pytest.fixture(scope='module')
def c():
    ROOT_TEST.mkdir(exist_ok=True)
    (ROOT_TEST/'test.db').unlink(missing_ok=True)
    with TestClient(app) as client:
        with connect() as db:
            for tenant,role in [('demo','admin'),('demo','contributor'),('demo','editor'),('other','admin')]:
                db.execute('INSERT INTO users(id,tenant,email,password_hash,display_name,role,created_at) VALUES(?,?,?,?,?,?,?)',
                   (uuid.uuid4().hex,tenant,f'{tenant}-{role}@test.com',PH.hash('StrongTest12345!'),role,role,now()))
        yield client

def login(c,role='admin',tenant='demo'):
    c.cookies.clear()
    r=c.post('/api/auth/login',json={'email':f'{tenant}-{role}@test.com','password':'StrongTest12345!','tenant':tenant})
    assert r.status_code==200,r.text
    return {'X-CSRF-Token':c.cookies.get('lawygo_cms_csrf')}

def make_post(c,h,product='pan',sponsored=True,kind='blog'):
    board=c.get('/api/boards?product='+product).json()['items'][0]
    r=c.post('/api/posts',headers=h,json={'board_id':board['id'],'kind':kind,'title':'테스트 콘텐츠','body':'한국어로 작성한 정확한 법률 콘텐츠입니다.','status':'published','visibility':'public','is_sponsored':sponsored})
    assert r.status_code==201,r.text
    return r.json()['id']

def test_growth_system_requires_login(c):
    assert c.get('/api/growth/system').status_code==401
    h=login(c)
    r=c.get('/api/growth/system');assert r.status_code==200
    assert r.json()['live_e2e']=='not_verified'

def test_campaign_create_edit_pause_and_public_feed(c):
    h=login(c)
    pid=make_post(c,h)
    bad=c.post('/api/growth/campaigns',headers=h,json={'product':'note','post_id':pid,'name':'광고로 바꿀 수 없음','status':'active'})
    assert bad.status_code==422
    r=c.post('/api/growth/campaigns',headers=h,json={'product':'pan','post_id':pid,'name':'파트너 광고','status':'active'})
    assert r.status_code==201,r.text
    cid=r.json()['id']
    feed=c.get('/api/growth/feed?product=pan').json()['items']
    assert next(x for x in feed if x['id']==pid)['placement']=='광고'
    assert c.patch(f'/api/growth/campaigns/{cid}',headers=h,json={'status':'paused'}).status_code==200
    assert c.patch(f'/api/growth/campaigns/{cid}',headers=h,json={'arbitrary_admin':True}).status_code==422
    assert c.post('/api/growth/campaigns',json={'product':'pan','post_id':pid,'name':'광고 작성','status':'active'}).status_code==403

def test_requires_sponsored_label_and_review(c):
    h=login(c)
    pid=make_post(c,h,sponsored=False)
    r=c.post('/api/growth/campaigns',headers=h,json={'product':'pan','post_id':pid,'name':'숨겨진 광고','status':'active'})
    assert r.status_code==409

def test_campaign_drag_order_scoped(c):
    h=login(c);ids=[]
    for i in range(3):
        pid=make_post(c,h)
        r=c.post('/api/growth/campaigns',headers=h,json={'product':'pan','post_id':pid,'name':f'후원 캠페인 {i}','status':'active'})
        ids.append(r.json()['id'])
    all_ids=[x['id'] for x in c.get('/api/growth/campaigns').json()['items'] if x['product']=='pan']
    r=c.post('/api/growth/campaigns/reorder',headers=h,json={'product':'pan','ids':list(reversed(all_ids))})
    assert r.status_code==200,r.text
    assert c.post('/api/growth/campaigns/reorder',headers=h,json={'product':'pan','ids':[ids[0],ids[0]]}).status_code==422
    assert c.post('/api/growth/campaigns/reorder',headers=h,json={'product':'pan','ids':['not-real']}).status_code==409

def test_board_reorder_and_role_security(c):
    h=login(c)
    b=c.get('/api/boards?product=pan').json()['items'];ids=[x['id'] for x in b]
    assert c.post('/api/boards/reorder',headers=h,json={'product':'pan','ids':list(reversed(ids))}).status_code==200
    assert [x['id'] for x in c.get('/api/boards?product=pan').json()['items']]==list(reversed(ids))
    h=login(c,'contributor');assert c.post('/api/boards/reorder',headers=h,json={'product':'pan','ids':ids}).status_code==403
    assert c.get('/api/growth/campaigns').status_code==403

def test_professional_verification_manual(c):
    h=login(c,'contributor')
    r=c.post('/api/pan/verification',headers=h,json={'professional_number':'등록번호 테스트1234'})
    assert r.status_code==200 and r.json()['status']=='pending'
    uid=c.get('/api/me').json()['id']
    assert c.patch('/api/pan/verification/'+uid,headers=h,json={'approved':True}).status_code==403
    h=login(c)
    assert c.patch('/api/pan/verification/'+uid,headers=h,json={'approved':True}).status_code==200
    assert any(x['status']=='approved' for x in c.get('/api/pan/verification').json()['items'])

def test_event_tracking_dedup_and_private_rejected(c):
    h=login(c);pid=make_post(c,h,sponsored=False)
    c.cookies.clear()
    p={'post_id':pid,'event_type':'profile_open'}
    assert c.post('/api/growth/events',json=p).status_code==200
    assert c.post('/api/growth/events',json=p).status_code==200
    h=login(c)
    agg=c.get('/api/growth/analytics').json()['events']
    assert any(x['event_type']=='profile_open' and x['count']==1 for x in agg)
    assert c.post('/api/growth/events',json={**p,'event_type':'fake_purchase'}).status_code==422
    h=login(c)
    note_board=c.get('/api/boards?product=note').json()['items'][0]['id']
    r=c.post('/api/posts',headers=h,json={'board_id':note_board,'kind':'note','title':'개인 비밀 노트','body':'비공개 정보','status':'draft','visibility':'private'})
    assert r.status_code==201
    assert c.post('/api/growth/events',json={'post_id':r.json()['id'],'event_type':'content_open'}).status_code==404

def test_subscription_webhook_reject_and_idempotence(c,monkeypatch):
    h=login(c);uid=c.get('/api/me').json()['id']
    body={'event_id':'evt_123456789','user_id':uid,'tenant':'demo','plan':'wiki','subscription_id':'sub_123456','status':'active','expires_at':None}
    payload=json.dumps(body).encode()
    assert c.post('/api/growth/billing/webhook',content=payload).status_code==503
    secret='Z'*48;monkeypatch.setenv('LAWYGO_BILLING_WEBHOOK_KEY',secret)
    ts=str(int(time.time()))
    sig=hmac.new(secret.encode(),ts.encode()+b'.'+payload,hashlib.sha256).hexdigest()
    headers={'x-lawygo-timestamp':ts,'x-lawygo-signature':sig}
    assert c.post('/api/growth/billing/webhook',content=payload,headers={**headers,'x-lawygo-signature':'0'*64}).status_code==401
    r=c.post('/api/growth/billing/webhook',content=payload,headers=headers)
    assert r.status_code==200,r.text
    assert c.post('/api/growth/billing/webhook',content=payload,headers=headers).json()['duplicate']
    assert c.get('/api/growth/entitlements').json()['items'][0]['active']
    assert c.post('/api/growth/billing/webhook',content=payload,headers={**headers,'x-lawygo-timestamp':str(int(time.time())-800)}).status_code==401

def test_strict_tenant_isolation(c):
    h=login(c,tenant='other')
    assert c.get('/api/growth/campaigns').json()['items']==[]
    assert c.get('/api/growth/analytics').json()['events']==[]
    assert c.get('/api/growth/entitlements').json()['items']==[]

def test_newsletter_does_not_fake_signup(c):
    c.cookies.clear()
    assert c.post('/api/growth/newsletter/request',json={'email':'x@y.com','consent':True}).status_code==503
    assert c.post('/api/growth/newsletter/request',json={'email':'x@y.com','consent':False}).status_code==422

def test_campaign_404_and_input_validation(c):
    h=login(c)
    assert c.patch('/api/growth/campaigns/na',headers=h,json={'status':'active'}).status_code==404
    assert c.get('/api/growth/feed?product=note').status_code==422
    assert c.get('/api/growth/analytics').status_code==200
