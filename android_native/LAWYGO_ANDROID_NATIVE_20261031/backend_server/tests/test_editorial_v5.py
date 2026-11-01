"""Operational tests for the editorial addition, using mocked feed bytes only."""
import sys,uuid
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi.testclient import TestClient
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import editorial_v5 as mod
core=None

RSS=b'''<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>Sample</title>
<item><title>New securities rules &amp; disclosures</title><link>https://www.federalreserve.gov/a</link><description>Official policy update</description><guid>example-1</guid></item>
<item><title>Second item</title><link>https://www.federalreserve.gov/b</link><description>&lt;b&gt;Summary&lt;/b&gt;</description><guid>example-2</guid></item></channel></rss>'''
ATOM=b'''<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Market policy statement</title><link href="https://example.org/press"/><id>id-1</id><summary>Statement text</summary></entry></feed>'''

@pytest.fixture
def c(tmp_path,monkeypatch):
 global core
 import app as core
 monkeypatch.setattr(core,'DB_FILE',tmp_path/'db.sqlite')
 monkeypatch.setattr(core,'FILES',tmp_path/'uploads')
 with TestClient(core.app) as client:
  with core.connect() as db:
   for role in ('admin','editor','contributor'):
    db.execute('INSERT INTO users(id,tenant,email,password_hash,display_name,role,created_at) VALUES(?,?,?,?,?,?,?)',(uuid.uuid4().hex,'demo',role+'@v5.test',core.PH.hash('longPass888!'),role,role,core.now()))
  yield client

def login(c,role):
 c.cookies.clear()
 r=c.post('/api/auth/login',json={'email':role+'@v5.test','password':'longPass888!'})
 assert r.status_code==200,r.text
 return {'X-CSRF-Token':c.cookies['lawygo_cms_csrf']}

def test_sources_preseeded(c):
 with core.connect() as db:
  assert db.execute('SELECT COUNT(*) FROM journal_sources').fetchone()[0]==11
  assert db.execute('SELECT COUNT(*) FROM journal_drafts').fetchone()[0]==0

def test_rss_parser_and_dedup(c):
 with core.connect() as db:
  f=lambda _:RSS
  first=mod.collect(db,fetcher=f)
  assert all(x['status']=='ok' and x['added']==2 for x in first)
  again=mod.collect(db,fetcher=f)
  assert all(x['added']==0 for x in again)
  assert db.execute('SELECT COUNT(*) FROM journal_items').fetchone()[0]==22

def test_atom_parser():
 items=mod.parse_feed(ATOM,'test');assert len(items)==1
 assert items[0]['title']=='Market policy statement'

def test_unsafe_xml_raises():
 malicious=b'<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><rss><channel><item><title>&xxe;</title></item></channel></rss>'
 with pytest.raises(Exception):mod.parse_feed(malicious,'bad')

def test_url_restriction_and_feed_oversize():
 for bad in ['file:///tmp/a','http://localhost/private','https://evil.test@127.0.0.1/a']:
  assert not mod.safe_article_url(bad)
 with pytest.raises(ValueError):mod.fetch_bytes('https://169.254.169.254/latest/meta-data')
 with pytest.raises(ValueError):mod.parse_feed(b'x'*2000001,'src')

def test_errors_isolated_and_logged(c):
 with core.connect() as db:
  def run(url):
   if 'federalreserve' in url:raise TimeoutError('provider not reachable')
   return RSS
  rows=mod.collect(db,fetcher=run)
  assert len(rows)==11 and any(x['status']=='failed' for x in rows)
  assert db.execute("SELECT count(*) FROM journal_fetches WHERE status='failed'").fetchone()[0]>=1

def test_build_draft_day_and_no_auto_send(c):
 with core.connect() as db:
  mod.collect(db,fetcher=lambda _:RSS)
  d=mod.create_draft(db)
  assert d['source_count']>=1
  assert '[LAWYGO DAILY BRIEF]' in d['subject']
  assert 'https://www.federalreserve.gov/a' in d['body']
  assert mod.create_draft(db)['id']==d['id']
  assert db.execute('SELECT COUNT(*) FROM newsletter_issues').fetchone()[0]==0
  assert db.execute('SELECT COUNT(*) FROM newsletter_deliveries').fetchone()[0]==0

def test_unauthenticated_editor_forbidden(c):
 assert c.get('/api/journal/drafts').status_code==401
 assert c.post('/api/journal/collect').status_code==401
 assert c.get('/api/journal/news').status_code==200

def test_contributor_cannot_edit(c):
 h=login(c,'contributor')
 assert c.post('/api/journal/collect',headers=h).status_code==403
 assert c.get('/api/journal/drafts').status_code==403

def test_editor_and_admin_approval(c):
 h=login(c,'editor')
 r=c.post('/api/journal/drafts/today',headers=h)
 assert r.status_code==200
 d=r.json()['item'];id=d['id']
 assert c.patch('/api/journal/drafts/'+id,headers=h,json={'status':'approved'}).status_code==403
 assert c.patch('/api/journal/drafts/'+id,headers=h,json={'status':'in_review'}).status_code==200
 h=login(c,'admin')
 assert c.patch('/api/journal/drafts/'+id,headers=h,json={'status':'approved'}).status_code==409
 assert c.patch('/api/journal/drafts/'+id,headers=h,json={'status':'draft'}).status_code==200

def test_disable_source_and_csrf(c):
 h=login(c,'admin')
 assert c.patch('/api/journal/sources/fed-all',json={'enabled':False}).status_code==403
 assert c.patch('/api/journal/sources/fed-all',headers=h,json={'enabled':False}).status_code==200
 assert next(x for x in c.get('/api/journal/sources').json()['items'] if x['id']=='fed-all')['enabled']==0

def test_pages_served(c):
 for path in ['/journal','/channel','/pan','/wiki','/note','/pro','/editor']:
  r=c.get(path);assert r.status_code==200,(path,r.status_code)
  assert '<!doctype html>' in r.text.lower()

def test_draft_revision_and_concurrency(c):
 h=login(c,'admin')
 new=c.post('/api/journal/drafts/today',headers=h).json()['item'];key=new['id']
 ok=c.patch('/api/journal/drafts/'+key,headers=h,json={'status':'draft','subject':'수정된 브리핑 제목 테스트','expected_updated_at':new['updated_at']})
 assert ok.status_code==200,ok.text
 stale=c.patch('/api/journal/drafts/'+key,headers=h,json={'status':'draft','subject':'오래된 초안','expected_updated_at':new['updated_at']})
 assert stale.status_code==409,stale.text
 with core.connect() as db:
  assert db.execute('SELECT COUNT(*) FROM journal_draft_history WHERE draft_id=?',(key,)).fetchone()[0]==1
