"""Module hub & cross-feature beta tests, deterministic isolated sqlite database."""
import json,uuid,sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app as core

@pytest.fixture
def env(tmp_path,monkeypatch):
 monkeypatch.setattr(core,'DB_FILE',tmp_path/'test.db')
 monkeypatch.setattr(core,'FILES',tmp_path/'uploads')
 with TestClient(core.app) as client:
  with core.connect() as db:
   for tenant,role in [('demo','admin'),('demo','editor'),('demo','contributor'),('other','admin')]:
    db.execute('INSERT INTO users(id,tenant,email,password_hash,display_name,role,created_at) VALUES(?,?,?,?,?,?,?)',(uuid.uuid4().hex,tenant,f'{tenant}-{role}@test.com',core.PH.hash('longPassword82!'),role,role,core.now()))
  yield client

def login(c,role='admin',tenant='demo'):
 c.cookies.clear()
 assert c.post('/api/auth/login',json={'tenant':tenant,'email':f'{tenant}-{role}@test.com','password':'longPassword82!'}).status_code==200
 return {'X-CSRF-Token':c.cookies.get('lawygo_cms_csrf')}

def create(c,head,product='pan',kind='board',slug='lawygo-new'):
 return c.post('/api/hub/modules',json={'product':product,'module_type':kind,'name':'테스트 모듈','create_board_slug':slug if kind=='board' else None},headers=head)

def test_module_defaults_and_missing_auth(env):
 assert env.get('/api/hub/modules').status_code==401
 login(env);items=env.get('/api/hub/modules').json()['items']
 assert len(items)==10
 assert {m['product'] for m in items}=={'channel','wiki','pan','note','journal','pro'}
 assert all(m['built_in'] for m in items)

def test_admin_create_board_and_cross_product_link(env):
 h=login(env);r=create(env,h);assert r.status_code==201,r.text
 id=r.json()['id'];bid=r.json()['board_id'];items=env.get('/api/boards?product=pan').json()['items'];assert any(x['id']==bid for x in items)
 assert env.post('/api/hub/modules',headers=h,json={'name':'bad board','product':'wiki','module_type':'board','board_id':bid}).status_code==404
 assert env.post('/api/hub/modules',headers=h,json={'name':'bad board','product':'pro','module_type':'board','create_board_slug':'pro-board'}).status_code==422
 assert env.post('/api/hub/modules',headers=h,json={'name':'bad board','product':'pan','module_type':'board','create_board_slug':'lawygo-new'}).status_code==409

def test_module_edit_conflict_disable_and_restore(env):
 h=login(env);r=create(env,h);id=r.json()['id'];
 assert env.patch(f'/api/hub/modules/{id}',headers=h,json={'version':1,'enabled':False,'name':'변경된 모듈'}).status_code==200
 assert env.patch(f'/api/hub/modules/{id}',headers=h,json={'version':1,'name':'충돌'}).status_code==409
 assert env.delete(f'/api/hub/modules/{id}',headers=h).json()['board_preserved']
 assert all(m['id']!=id for m in env.get('/api/hub/modules').json()['items'])
 assert any(m['id']==id for m in env.get('/api/hub/trash').json()['items'])
 assert env.post(f'/api/hub/modules/{id}/restore',headers=h).status_code==200
 assert next(m for m in env.get('/api/hub/modules').json()['items'] if m['id']==id)['enabled'] is False

def test_core_module_delete_blocked(env):
 h=login(env);id=env.get('/api/hub/modules').json()['items'][0]['id']
 assert env.delete('/api/hub/modules/'+id,headers=h).status_code==409

def test_role_security_module_create_modify(env):
 h=login(env,'contributor')
 assert create(env,h).status_code==403
 assert env.get('/api/hub/health').status_code==403
 assert env.get('/api/hub/metrics.csv').status_code==403
 h=login(env,'editor');assert create(env,h).status_code==403
 assert env.post('/api/hub/jobs',headers=h,json={'kind':'snapshot_metrics'}).status_code==201

def test_no_csrf_and_logout(env):
 h=login(env)
 assert create(env,{}).status_code==403
 assert env.post('/api/hub/jobs',json={'kind':'check_dependencies'}).status_code==403
 assert env.post('/api/auth/logout',headers=h).status_code==200
 assert env.get('/api/hub/overview').status_code==401

def test_tenant_separation(env):
 h=login(env);r=create(env,h);id=r.json()['id']
 login(env,tenant='other')
 assert all(m['id']!=id for m in env.get('/api/hub/modules').json()['items'])
 h={'X-CSRF-Token':env.cookies.get('lawygo_cms_csrf')}
 assert env.patch(f'/api/hub/modules/{id}',headers=h,json={'version':1,'name':'침입'}).status_code==404
 assert env.delete('/api/hub/modules/'+id,headers=h).status_code==404

def test_sorting_all_scoped_immutable(env):
 h=login(env);items=[i for i in env.get('/api/hub/modules?product=pan').json()['items']];ids=[i['id'] for i in items];assert len(ids)>=2
 assert env.post('/api/hub/modules/reorder',headers=h,json={'product':'pan','ids':ids[::-1]}).status_code==200
 assert [m['id'] for m in env.get('/api/hub/modules?product=pan').json()['items']]==ids[::-1]
 assert env.post('/api/hub/modules/reorder',headers=h,json={'product':'pan','ids':[ids[0]]}).status_code==409
 assert env.post('/api/hub/modules/reorder',headers=h,json={'product':'pan','ids':[ids[0],ids[0]]}).status_code==422

def test_journal_pro_as_nonboard_modules(env):
 h=login(env)
 assert env.post('/api/hub/modules',headers=h,json={'product':'journal','module_type':'newsletter','name':'해외 정책 뉴스 편집'}).status_code==201
 assert env.post('/api/hub/modules',headers=h,json={'product':'pro','module_type':'integration','name':'법원 사건기일 상태조회'}).status_code==201

def test_jobs_run_once_and_snapshots(env):
 h=login(env);j=env.post('/api/hub/jobs',headers=h,json={'kind':'snapshot_metrics'}).json()['id']
 assert env.get('/api/hub/jobs').json()['items'][0]['status']=='queued'
 r=env.post('/api/hub/jobs/'+j+'/run',headers=h);assert r.status_code==200,r.text
 assert r.json()['result']['recorded']==8
 assert env.post('/api/hub/jobs/'+j+'/run',headers=h).status_code==409
 assert len(env.get('/api/hub/snapshots').json()['items'])==8

def test_jobs_config_and_pending(env):
 h=login(env)
 for kind in ['check_dependencies','count_pending_content']:
  j=env.post('/api/hub/jobs',headers=h,json={'kind':kind}).json()['id'];assert env.post('/api/hub/jobs/'+j+'/run',headers=h).status_code==200
 assert env.post('/api/hub/jobs',headers=h,json={'kind':'arbitrary_python'}).status_code==422

def test_analytics_cross_module_feed_and_snapshot(env):
 h=login(env);bid=env.get('/api/boards?product=pan').json()['items'][0]['id']
 r=env.post('/api/posts',headers=h,json={'board_id':bid,'kind':'profile','title':'광고 심사 검증용 가상 프로필','body':'가상 변호사로 표시된 검사 데이터','status':'published','visibility':'public','is_sponsored':True});assert r.status_code==201,r.text
 postid=r.json()['id'];campaign=env.post('/api/growth/campaigns',headers=h,json={'product':'pan','post_id':postid,'name':'검증용 광고 캠페인','status':'active'});assert campaign.status_code==201,campaign.text
 x=env.get('/api/hub/overview').json();assert x['campaigns_active']==1
 assert any(t['product']=='pan' and t['status']=='published' for t in x['posts'])
 assert env.get('/api/growth/feed?product=pan').status_code==200
 assert env.get('/api/hub/metrics.csv').status_code==200

def test_no_note_leak_in_overview(env):
 h=login(env,'contributor');board=env.get('/api/boards?product=note').json()['items'][0]['id']
 r=env.post('/api/posts',headers=h,json={'board_id':board,'kind':'note','title':'직원만 보는 변호인 노트','body':'수임인 개인정보 비공개','visibility':'private'});assert r.status_code==201
 assert any(m['product']=='note' for m in env.get('/api/hub/overview').json()['posts'])
 login(env,tenant='other');assert not any(m['product']=='note' for m in env.get('/api/hub/overview').json()['posts'])

def test_health_never_exposes_secret(env,monkeypatch):
 monkeypatch.setenv('GEMINI_API_KEY','this-secret-should-not-be-returned')
 login(env);r=env.get('/api/hub/health');assert r.status_code==200
 assert 'this-secret' not in r.text
 assert next(x for x in r.json()['integrations'] if x['id']=='gemini')['configured']
 assert all(x['live_verified'] is False for x in r.json()['integrations'])

def test_page_and_assets(env):
 r=env.get('/hub');assert r.status_code==200 and '모듈 빌더' in r.text
 for asset in ['hub.js','hub.css','logo.svg']:
  r=env.get('/static/'+asset);assert r.status_code==200


def test_invalid_types_and_content_safety(env):
 h=login(env)
 assert env.post('/api/hub/modules',headers=h,json={'product':'wiki','module_type':'exec','name':'임의 실행'}).status_code==422
 assert env.post('/api/hub/modules',headers=h,json={'product':'wiki','module_type':'board','name':'문자열','create_board_slug':'../../etc/passwd'}).status_code==422

def test_local_managed_board_post_crud_complete(env):
 h=login(env);r=create(env,h,slug='fresh-content');assert r.status_code==201
 board_id=r.json()['board_id'];p=env.post('/api/posts',headers=h,json={'board_id':board_id,'kind':'blog','title':'변호사 콘텐츠 입력','body':'구글 블로그 공개 컨텐츠 초안','status':'draft','visibility':'public'});assert p.status_code==201
 pid=p.json()['id'];v=env.get('/api/posts/'+pid).json()['version'];assert env.patch('/api/posts/'+pid,headers=h,json={'version':v,'status':'published'}).status_code==200
 assert env.delete('/api/posts/'+pid,headers=h).status_code==200
 assert env.post('/api/posts/'+pid+'/restore',headers=h).status_code==200


def test_database_integrity_error_rolls_back_created_board(env):
 h=login(env);before=len(env.get('/api/boards?product=pan').json()['items'])
 r=create(env,h,slug='duplicate-test');assert r.status_code==201
 r2=create(env,h,slug='duplicate-test');assert r2.status_code==409
 assert len(env.get('/api/boards?product=pan').json()['items'])==before+1

def test_disabled_module_blocks_new_posts_but_preserves_board(env):
 h=login(env);created=create(env,h,slug='temporary-disabling');assert created.status_code==201
 mid=created.json()['id'];bid=created.json()['board_id']
 assert env.patch('/api/hub/modules/'+mid,headers=h,json={'version':1,'enabled':False}).status_code==200
 body={'board_id':bid,'kind':'blog','title':'비활성 게시판', 'body':'사용할 수 없는 테스트'}
 assert env.post('/api/posts',headers=h,json=body).status_code==409
 assert any(b['id']==bid for b in env.get('/api/boards?product=pan').json()['items'])
 assert env.patch('/api/hub/modules/'+mid,headers=h,json={'version':2,'enabled':True}).status_code==200
 assert env.post('/api/posts',headers=h,json=body).status_code==201
