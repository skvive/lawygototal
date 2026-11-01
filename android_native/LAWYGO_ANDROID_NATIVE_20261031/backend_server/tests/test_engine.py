import os,sys,uuid
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
TEST_DIR=ROOT/'tests'/'_test_instance'
os.environ['LAWYGO_DB_PATH']=str(TEST_DIR/'test.db')
os.environ['LAWYGO_UPLOAD_PATH']=str(TEST_DIR/'uploads')
from app import app,init_db,connect,PH,now

@pytest.fixture(scope='module')
def c():
    TEST_DIR.mkdir(parents=True,exist_ok=True)
    p=TEST_DIR/'test.db'
    if p.exists():p.unlink()
    with TestClient(app) as client:
        with connect() as db:
            for role in ['admin','editor','contributor','viewer','other']:
                db.execute('INSERT INTO users(id,tenant,email,password_hash,display_name,role,created_at) VALUES(?,?,?,?,?,?,?)',(uuid.uuid4().hex,'demo',role+'@example.com',PH.hash('StrongTestingPass123!'),role,'contributor' if role=='other' else role,now()))
        yield client

def auth(c,role):
    c.cookies.clear()
    r=c.post('/api/auth/login',json={'email':role+'@example.com','password':'StrongTestingPass123!'})
    assert r.status_code==200,r.text
    return {'X-CSRF-Token':c.cookies.get('lawygo_cms_csrf')}

def board(c,product,slug=None):
    items=c.get('/api/boards?product='+product).json()['items']
    return next((x for x in items if slug is None or x['slug']==slug),None)['id']

def post(c,product,headers,status='draft',**kwargs):
    kind={'channel':'article','wiki':'encyclopedia','pan':'blog','note':'note'}[product]
    payload={'board_id':board(c,product),'kind':kind,'title':'제목 테스트','body':'한국어 설명을 포함한 실제 데이터입니다.','status':status,'visibility':'private' if product=='note' else 'public'}
    payload.update(kwargs)
    return c.post('/api/posts',headers=headers,json=payload)

def test_health_and_base_boards(c):
    assert c.get('/api/health').status_code==200
    assert len(c.get('/api/boards').json()['items'])==13
    assert c.get('/api/posts').json()['items']==[]

def test_unauthenticated_cannot_write(c):
    r=c.post('/api/posts',json={})
    assert r.status_code==401

def test_csrf(c):
    auth(c,'admin')
    assert c.post('/api/boards',json={'product':'pan','slug':'test-new','name':'새 게시판'}).status_code==403
    assert c.post('/api/boards',headers={'X-CSRF-Token':'bad'},json={'product':'pan','slug':'test-new','name':'새 게시판'}).status_code==403

def test_board_crud_and_recover(c):
    h=auth(c,'admin');r=c.post('/api/boards',headers=h,json={'product':'pan','slug':'test-new','name':'새 게시판','description':'최초 설명'})
    assert r.status_code==201,r.text;bid=r.json()['id']
    assert c.post('/api/boards',headers=h,json={'product':'pan','slug':'test-new','name':'새 게시판'}).status_code==409
    assert c.patch('/api/boards/'+bid,headers=h,json={'name':'수정한 게시판'}).status_code==200
    assert c.delete('/api/boards/'+bid,headers=h).status_code==200
    assert not any(b['id']==bid for b in c.get('/api/boards').json()['items'])
    assert c.post('/api/boards/'+bid+'/restore',headers=h).status_code==200
    assert any(b['id']==bid for b in c.get('/api/boards').json()['items'])

def test_contributor_moderation(c):
    h=auth(c,'contributor')
    assert post(c,'pan',h,status='published').status_code==403
    r=post(c,'pan',h,status='pending')
    assert r.status_code==201,r.text;pid=r.json()['id']
    assert c.get('/api/posts?product=pan').json()['total']==1
    assert c.patch('/api/posts/'+pid,headers=h,json={'version':1,'status':'published'}).status_code==403
    auth(c,'viewer')
    assert c.get('/api/posts?product=pan').json()['total']==0
    assert c.get('/api/posts/'+pid).status_code==404
    h=auth(c,'editor')
    d=c.get('/api/posts/'+pid).json()
    assert c.patch('/api/posts/'+pid,headers=h,json={'version':d['version'],'status':'published'}).status_code==200
    c.cookies.clear()
    assert c.get('/api/posts?product=pan').json()['total']==1
    assert c.get('/api/posts/'+pid).status_code==200

def test_revision_conflict_deletion_restore(c):
    h=auth(c,'admin');r=post(c,'wiki',h,status='published');assert r.status_code==201,r.text;pid=r.json()['id']
    assert c.patch('/api/posts/'+pid,headers=h,json={'version':1,'title':'수정된 제목'}).json()['version']==2
    assert c.patch('/api/posts/'+pid,headers=h,json={'version':1,'title':'오래된 편집'}).status_code==409
    assert len(c.get('/api/posts/'+pid+'/revisions').json()['items'])==1
    assert c.delete('/api/posts/'+pid,headers=h).status_code==200
    assert c.get('/api/posts/'+pid).status_code==404
    assert c.post('/api/posts/'+pid+'/restore',headers=h).status_code==200
    assert c.get('/api/posts/'+pid).json()['status']=='draft'

def test_note_isolation_even_for_admin(c):
    h=auth(c,'contributor');r=post(c,'note',h);assert r.status_code==201;pid=r.json()['id']
    assert c.get('/api/posts?product=note').json()['total']==1
    assert c.get('/api/posts').json()['total']>=1
    auth(c,'other')
    assert c.get('/api/posts?product=note').json()['total']==0
    assert c.get('/api/posts/'+pid).status_code==404
    auth(c,'admin')
    assert c.get('/api/posts?product=note').json()['total']==0
    assert not any(x['id']==pid for x in c.get('/api/posts').json()['items'])
    assert c.get('/api/posts/'+pid).status_code==404

def test_note_public_and_sponsored_forbidden(c):
    h=auth(c,'admin')
    assert post(c,'note',h,visibility='public').status_code==400
    assert post(c,'note',h,is_sponsored=True).status_code==400

def test_roles(c):
    h=auth(c,'viewer')
    assert post(c,'channel',h).status_code==403
    assert c.post('/api/boards',headers=h,json={'product':'pan','slug':'viewer-test','name':'금지'}).status_code==403
    h=auth(c,'contributor')
    assert post(c,'wiki',h).status_code==403

def test_xss_storage_plain_text_and_url(c):
    h=auth(c,'admin')
    assert post(c,'pan',h,external_url='javascript:alert(1)').status_code==422
    r=post(c,'pan',h,body='<script>alert("xss")</script>')
    assert r.status_code==201
    assert '<script>' in c.get('/api/posts/'+r.json()['id']).json()['body']
    # UI uses textContent, not innerHTML; code data is not executed.

def test_comments_permissions(c):
    h=auth(c,'editor');r=post(c,'channel',h,status='published');pid=r.json()['id']
    res=c.post('/api/posts/'+pid+'/comments',headers=h,json={'body':'좋은 기사입니다.'})
    assert res.status_code==201
    assert len(c.get('/api/posts/'+pid+'/comments').json()['items'])==1
    cid=res.json()['id']
    h=auth(c,'other');assert c.delete('/api/comments/'+cid,headers=h).status_code==403
    h=auth(c,'admin');assert c.delete('/api/comments/'+cid,headers=h).status_code==200

def test_media_signature_and_access(c):
    h=auth(c,'admin');r=post(c,'note',h);pid=r.json()['id']
    bad=c.post('/api/media?post_id='+pid,headers=h,files={'file':('evil.png',b'this is not png','image/png')})
    assert bad.status_code==415
    good=c.post('/api/media?post_id='+pid,headers=h,files={'file':('a.pdf',b'%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n%%EOF','application/pdf')})
    assert good.status_code==201,good.text
    mid=good.json()['id'];res=c.get('/api/media/'+mid);assert res.status_code==200
    auth(c,'other');assert c.get('/api/media/'+mid).status_code==404

def test_dashboard_audit(c):
    h=auth(c,'admin');stats=c.get('/api/dashboard/stats').json();assert len(stats['boards'])>=4
    assert len(c.get('/api/audit').json()['items'])>0
    auth(c,'contributor');assert c.get('/api/audit').status_code==403

def test_html_and_assets(c):
    for path in ['/','/dashboard','/p/channel','/p/wiki','/p/pan','/p/note','/static/style.css','/static/dashboard.js']:
        r=c.get(path);assert r.status_code==200,(path,r.status_code)
