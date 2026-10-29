"""Deterministic integration tests. Google/Gemini/native external calls are mocked."""
import os, sys, uuid
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import pytest
from fastapi.testclient import TestClient
from cryptography.fernet import Fernet
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import app as core
import integrations_v2 as v2

@pytest.fixture
def c(tmp_path,monkeypatch):
    monkeypatch.delenv('DATABASE_URL', raising=False)
    monkeypatch.delenv('NEON_DATABASE_URL', raising=False)
    import db_engine
    monkeypatch.setattr(db_engine, 'DATABASE_URL', '')
    monkeypatch.setattr(db_engine, 'USE_POSTGRES', False)
    monkeypatch.setattr(core, 'USE_POSTGRES', False)
    monkeypatch.setattr(core,'DB_FILE',tmp_path/'cms.db')
    monkeypatch.setattr(core,'FILES',tmp_path/'uploads')
    monkeypatch.setenv('LAWYGO_TOKEN_ENCRYPTION_KEY',Fernet.generate_key().decode())
    monkeypatch.setenv('GOOGLE_CLIENT_ID','unit-test.apps.googleusercontent.com')
    monkeypatch.setenv('GOOGLE_CLIENT_SECRET','unused-test-only')
    monkeypatch.setenv('GOOGLE_REDIRECT_URI','http://localhost:8018/api/google/callback')
    monkeypatch.setattr(v2,'_verify_id_token',lambda token:{'sub':'google-test-123','email':'new-google@example.com','email_verified':True,'name':'구글 신규 사용자'})
    monkeypatch.setattr(v2,'_google_exchange',lambda code,verifier:{'access_token':'fake-access','refresh_token':'fake-refresh','scope':' '.join(v2.SCOPES['blogger']+v2.SCOPES['youtube']),'id_token':'test','expires_in':3600})
    with TestClient(core.app) as test:
        with core.connect() as db:
            for role in ['admin','editor','contributor','viewer']:
                db.execute('INSERT INTO users(id,tenant,email,password_hash,display_name,role,created_at) VALUES(?,?,?,?,?,?,?)',(
                    uuid.uuid4().hex,'demo',role+'@example.com',core.PH.hash('StrongPass123456'),role,role,core.now()))
        yield test

def login(c,role='admin'):
    c.cookies.clear()
    r=c.post('/api/auth/login',json={'email':f'{role}@example.com','password':'StrongPass123456'})
    assert r.status_code==200,r.text
    return {'X-CSRF-Token':c.cookies['lawygo_cms_csrf']}

def start(c,mode):
    route='/api/google/login' if mode=='login' else '/api/google/connect/'+mode
    r=c.get(route,follow_redirects=False)
    assert r.status_code==302,r.text
    q=parse_qs(urlparse(r.headers['location']).query)
    assert q['code_challenge_method']==['S256']
    return q['state'][0]

def callback(c,state):return c.get('/api/google/callback?state='+state+'&code=test-code',follow_redirects=False)

def add_source(c,provider,extid):
    h={'X-CSRF-Token':c.cookies['lawygo_cms_csrf']}
    r=c.post('/api/sync/sources',headers=h,json={'provider':provider,'external_id':extid,'title':'내 채널'})
    assert r.status_code==201,r.text
    return r.json()['id']

def mock_owned(url,token,params):
    if 'users/self/blogs' in url:return {'items':[{'id':'10001','name':'내 블로그','url':'https://site.blogspot.com/'}]}
    if '/channels' in url:return {'items':[{'id':'UC-my','snippet':{'title':'내 채널'},'contentDetails':{'relatedPlaylists':{'uploads':'UU-my-upload'}}}]}
    if '/blogs/10001/posts' in url:return {'items':[{'id':'blog-1','title':'민사소송 준비','content':'<b>법률 상담</b> 안내','url':'https://example.blogspot.com/2026/law.html'}]}
    if '/playlistItems' in url:return {'items':[{'contentDetails':{'videoId':'video-123'},'snippet':{'title':'소송 준비 팁','description':'증거 정리'}}]}
    raise AssertionError(url)

def test_google_requires_credentials(c,monkeypatch):
    monkeypatch.delenv('GOOGLE_CLIENT_SECRET')
    assert c.get('/api/google/login').status_code==503

def test_google_oidc_register_and_state_replay(c):
    state=start(c,'login');r=callback(c,state)
    assert r.status_code==302,r.text
    assert c.get('/api/me').json()['role']=='contributor'
    assert callback(c,state).status_code==400

def test_google_email_cannot_silently_hijack_password_account(c,monkeypatch):
    monkeypatch.setattr(v2,'_verify_id_token',lambda t:{'sub':'some-other-sub','email':'admin@example.com','email_verified':True})
    state=start(c,'login')
    assert callback(c,state).status_code==409
    assert c.get('/api/me').status_code==401

def test_google_token_encrypted_connection_scopes_and_revocation(c,monkeypatch):
    login(c)
    state=start(c,'blogger')
    assert callback(c,state).status_code==302
    with core.connect() as db:
        row=db.execute("SELECT * FROM google_tokens WHERE provider='blogger'").fetchone()
        assert row and row['access_enc']!='fake-access' and 'fake-access' not in row['access_enc']
    assert c.get('/api/google/connections').json()['items'][0]['provider']=='blogger'
    h={'X-CSRF-Token':c.cookies['lawygo_cms_csrf']}
    assert c.delete('/api/google/connections/blogger',headers=h).status_code==200
    assert c.get('/api/google/connections').json()['items']==[]

def test_google_account_mismatch_blocked(c,monkeypatch):
    login(c)
    s=start(c,'blogger');assert callback(c,s).status_code==302
    monkeypatch.setattr(v2,'_verify_id_token',lambda t:{'sub':'another-sub','email':'other@example.com','email_verified':True})
    s=start(c,'youtube');assert callback(c,s).status_code==403

def test_blogger_sync_approved_only_idempotence_update(c,monkeypatch):
    login(c);s=start(c,'blogger');assert callback(c,s).status_code==302
    monkeypatch.setattr(v2,'_google_get',mock_owned)
    assert c.get('/api/google/owned/blogger').json()['items'][0]['id']=='10001'
    wrong=c.post('/api/sync/sources',headers={'X-CSRF-Token':c.cookies['lawygo_cms_csrf']},json={'provider':'blogger','external_id':'not-owned','title':'남의 블로그'})
    assert wrong.status_code==403
    sid=add_source(c,'blogger','10001')
    h={'X-CSRF-Token':c.cookies['lawygo_cms_csrf']}
    r=c.post('/api/sync/sources/'+sid+'/run',headers=h);assert r.status_code==200,r.text
    assert r.json()['created']==1
    with core.connect() as db:
        item=db.execute("SELECT * FROM posts WHERE title='민사소송 준비'").fetchone()
        assert item['status']=='pending'
        postid=item['id']
        db.execute('UPDATE sync_sources SET last_sync_at=NULL WHERE id=?',(sid,))
    r=c.post('/api/sync/sources/'+sid+'/run',headers=h);assert r.status_code==200,r.text
    assert r.json()['created']==0 and r.json()['updated']==0
    # Publishing a remote item requires explicit editorial review.
    c.cookies.clear();assert c.get('/api/posts/'+postid).status_code==404
    h=login(c)
    with core.connect() as db:db.execute('UPDATE sync_sources SET last_sync_at=NULL WHERE id=?',(sid,))
    def changed(url,token,params):
        val=mock_owned(url,token,params)
        if '/posts' in url:val['items'][0]['title']='민사소송 최신 준비 체크리스트'
        return val
    monkeypatch.setattr(v2,'_google_get',changed)
    r=c.post('/api/sync/sources/'+sid+'/run',headers=h)
    assert r.status_code==200,r.text
    assert r.json()['updated']==1
    assert c.get('/api/posts/'+postid).json()['version']==2

def test_youtube_uploads_playlist_sync(c,monkeypatch):
    login(c);s=start(c,'youtube');assert callback(c,s).status_code==302
    monkeypatch.setattr(v2,'_google_get',mock_owned)
    assert c.get('/api/google/owned/youtube').json()['items'][0]['id']=='UU-my-upload'
    sid=add_source(c,'youtube','UU-my-upload');h={'X-CSRF-Token':c.cookies['lawygo_cms_csrf']}
    r=c.post('/api/sync/sources/'+sid+'/run',headers=h)
    assert r.status_code==200,r.text
    with core.connect() as db:
        post=db.execute("SELECT * FROM posts WHERE title='소송 준비 팁'").fetchone()
        assert post and post['kind']=='video' and post['external_url']=='https://www.youtube.com/watch?v=video-123'

def test_sync_requires_live_google_connection(c):
    h=login(c)
    r=c.post('/api/sync/sources',headers=h,json={'provider':'blogger','external_id':'10001','title':'블로그'})
    assert r.status_code==409

def test_ai_consent_no_api_key_and_citations(c,monkeypatch):
    h=login(c)
    board=c.get('/api/boards?product=note').json()['items'][0]['id']
    r=c.post('/api/posts',headers=h,json={'board_id':board,'kind':'note','title':'계약 검토','body':'계약 해지 시 서면 통지 여부가 쟁점이며 계약서 원문 검토가 필요합니다.','visibility':'private'})
    assert r.status_code==201,r.text
    pid=r.json()['id']
    assert c.post('/api/note/'+pid+'/ai-analyze',headers=h,json={'consent':False}).status_code==400
    monkeypatch.delenv('GEMINI_API_KEY',raising=False)
    assert c.post('/api/note/'+pid+'/ai-analyze',headers=h,json={'consent':True}).status_code==503
    monkeypatch.setattr(v2,'_gemini_analyze',lambda text,refs:{'summary':'자료 범위 내 분석','issues':[{'issue':'서면 통지','source_ids':['source-note']}], 'evidence_gaps':['계약 원문'],'questions':['통지 날짜는?'],'disclaimer':'전문가 검토 필요'})
    r=c.post('/api/note/'+pid+'/ai-analyze',headers=h,json={'consent':True})
    assert r.status_code==200,r.text
    assert r.json()['result']['issues'][0]['source_ids']==['source-note']
    assert c.get('/api/note/'+pid+'/ai-runs').json()['items'][0]['provider']=='gemini'
    c.cookies.clear();assert c.get('/api/note/'+pid+'/ai-runs').status_code==401

def test_ai_rejects_invalid_citations(c,monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY','mocked-key')
    class FakeResponse:
        def raise_for_status(self):pass
        def json(self):return {'candidates':[{'content':{'parts':[{'text':'{"summary":"a","issues":[{"issue":"fake","source_ids":["invented-case"]}]}' }]}}]}
    class FakeHttp:
        def __init__(self,*a,**kw):pass
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def post(self,*a,**kw):return FakeResponse()
    monkeypatch.setattr(v2.httpx,'Client',FakeHttp)
    with pytest.raises(Exception) as ex:v2._gemini_analyze('text',[{'id':'source-note','title':'note'}])
    assert getattr(ex.value,'status_code',None)==502

def test_native_bridge_publish_after_moderation(c,monkeypatch):
    h=login(c)
    b=c.get('/api/boards?product=channel').json()['items'][0]['id']
    r=c.post('/api/posts',headers=h,json={'board_id':b,'kind':'article','title':'기업 법률 칼럼','body':'기업 공시 변화','status':'draft'})
    assert r.status_code==201,r.text;pid=r.json()['id']
    assert c.post('/api/native/publish/'+pid,headers=h).status_code==400
    assert c.patch('/api/posts/'+pid,headers=h,json={'version':1,'status':'published'}).status_code==200
    assert c.post('/api/native/publish/'+pid,headers=h).status_code==503
    monkeypatch.setattr(v2,'_bridge_publish',lambda msg: {'ok':True,'postId':17,'same':msg['source_id']})
    assert c.post('/api/native/queue/'+pid,headers=h).status_code==200
    result=c.post('/api/native/publish/'+pid,headers=h)
    assert result.status_code==200,result.text
    assert result.json()['remote']['postId']==17
    assert c.get('/api/native/outbox').json()['items'][0]['status']=='delivered'

def test_bridge_requires_secure_destination(monkeypatch):
    monkeypatch.setenv('LAWYGO_NATIVE_BRIDGE_URL','http://external.example/api')
    monkeypatch.setenv('LAWYGO_NATIVE_BRIDGE_SECRET','x'*40)
    with pytest.raises(Exception) as ex:v2._bridge_publish({})
    assert getattr(ex.value,'status_code',None)==503

def test_refresh_token_rotation(c,monkeypatch):
    login(c);assert callback(c,start(c,'youtube')).status_code==302
    with core.connect() as db:
        db.execute("UPDATE google_tokens SET expires_at=0 WHERE provider='youtube'")
    monkeypatch.setattr(v2,'_google_refresh',lambda previous:{'access_token':'updated-access','refresh_token':'new-refresh','expires_in':3600})
    with core.connect() as db:
        user=db.execute("SELECT id FROM users WHERE email='admin@example.com'").fetchone()
        assert v2._access_token(db,user['id'],'youtube')=='updated-access'
        assert 'new-refresh' not in db.execute("SELECT refresh_enc FROM google_tokens WHERE provider='youtube'").fetchone()['refresh_enc']

def test_sync_source_permission_and_cooldown(c,monkeypatch):
    login(c);assert callback(c,start(c,'blogger')).status_code==302
    monkeypatch.setattr(v2,'_google_get',mock_owned)
    sid=add_source(c,'blogger','10001')
    h={'X-CSRF-Token':c.cookies['lawygo_cms_csrf']}
    assert c.post('/api/sync/sources/'+sid+'/run',headers=h).status_code==200
    assert c.post('/api/sync/sources/'+sid+'/run',headers=h).status_code==429
    login(c,'contributor')
    h={'X-CSRF-Token':c.cookies['lawygo_cms_csrf']}
    assert c.post('/api/sync/sources/'+sid+'/run',headers=h).status_code==404

def test_note_ai_private_from_other_authenticated_user(c,monkeypatch):
    h=login(c,'contributor')
    b=c.get('/api/boards?product=note').json()['items'][0]['id']
    pid=c.post('/api/posts',headers=h,json={'board_id':b,'kind':'note','title':'기밀 소송 문서','body':'의뢰인 자료는 외부에 공개할 수 없으며 비공개로 저장해야 합니다.','visibility':'private'}).json()['id']
    h=login(c,'admin')
    assert c.post('/api/note/'+pid+'/ai-analyze',headers=h,json={'consent':True}).status_code==404

def test_native_retract_handles_deleted_post(c,monkeypatch):
    h=login(c)
    b=c.get('/api/boards?product=wiki').json()['items'][0]['id']
    pid=c.post('/api/posts',headers=h,json={'board_id':b,'kind':'encyclopedia','title':'대법원 판례 요약','body':'판례 번호 및 사건 사실은 반드시 원문으로 확인해야 합니다.','status':'published','visibility':'public'}).json()['id']
    monkeypatch.setattr(v2,'_bridge_publish',lambda payload:{'ok':True,'action':payload['action']})
    assert c.post('/api/native/publish/'+pid,headers=h).status_code==200
    assert c.delete('/api/posts/'+pid,headers=h).status_code==200
    r=c.post('/api/native/retract/'+pid,headers=h)
    assert r.status_code==200,r.text
    assert r.json()['remote']['action']=='delete'
    assert c.get('/api/native/outbox').json()['items'][0]['action']=='delete'

def test_native_membership_required_missing_bridge_fails_closed(c,monkeypatch):
    monkeypatch.setenv('LAWYGO_REQUIRE_NATIVE_MEMBERSHIP','true')
    monkeypatch.delenv('LAWYGO_NATIVE_IDENTITY_URL',raising=False)
    state=start(c,'login')
    assert callback(c,state).status_code==503
    assert c.get('/api/me').status_code==401

def test_existing_lawygo_membership_tenant_isolation(c,monkeypatch):
    monkeypatch.setattr(v2,'_native_identity_lookup',lambda sub:{'id':'native-user-123','tenant':'firm-001'})
    state=start(c,'login');r=callback(c,state)
    assert r.status_code==302,r.text
    assert c.get('/api/me').json()['tenant']=='firm-001'
    assert len(c.get('/api/boards?product=pan').json()['items'])==4
    with core.connect() as db:
        mapped=db.execute('SELECT * FROM native_identity_links WHERE native_user_id=?',('native-user-123',)).fetchone()
        assert mapped and mapped['native_tenant']=='firm-001'
    # An unrelated default-tenant post is never visible to tenant firm-001.
    h={'X-CSRF-Token':c.cookies['lawygo_cms_csrf']}
    b=c.get('/api/boards?product=pan').json()['items'][0]['id']
    new=c.post('/api/posts',headers=h,json={'board_id':b,'kind':'profile','title':'기존 LAWYGO 회원 프로필','body':'공개 승인 전 프로필 초안입니다.','visibility':'public','status':'pending'})
    assert new.status_code==201,new.text
    assert c.get('/api/posts?product=pan').json()['total']==1
    c.cookies.clear()
    assert c.get('/api/posts?product=pan').json()['total']==0

def test_gemini_json_generation_schema_success(c,monkeypatch):
    monkeypatch.setenv('GEMINI_API_KEY','fake-api-key-for-local-mock')
    class Response:
        def raise_for_status(self):pass
        def json(self):return {'candidates':[{'content':{'parts':[{'text':'{"summary":"계약서 검토", "issues":[{"issue":"해지 통지", "source_ids":["source-note"]}],"evidence_gaps":["통지 증거"],"questions":["언제 발송했습니까?"],"disclaimer":"전문가 검토 필요"}'}]}}]}
    class Client:
        def __init__(self,**kw):pass
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def post(self,url,headers,json):
            assert 'generativelanguage.googleapis.com' in url
            assert headers['x-goog-api-key']=='fake-api-key-for-local-mock'
            assert 'SOURCE' in json['contents'][0]['parts'][0]['text']
            return Response()
    monkeypatch.setattr(v2.httpx,'Client',Client)
    obj=v2._gemini_analyze('계약 해지 전 통지를 해야 한다는 조항이 포함됩니다.',[{'id':'source-note','title':'계약서'}])
    assert obj['issues'][0]['source_ids']==['source-note']
    assert '전문가' in obj['disclaimer']
