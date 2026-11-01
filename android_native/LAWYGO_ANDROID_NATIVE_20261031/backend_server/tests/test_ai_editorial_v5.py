"""AI editorial opt-in and source-grounding checks (no external network)."""
import sys,uuid
from pathlib import Path
import pytest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import editorial_v5 as v5
import sqlite3

@pytest.fixture
def db(tmp_path):
    con=sqlite3.connect(tmp_path/'ai.db',isolation_level=None)
    con.row_factory=sqlite3.Row
    v5.ensure_schema(con)
    yield con
    con.close()

def put_draft(db):
    source=v5.FEEDS[0]
    item=uuid.uuid4().hex
    db.execute('INSERT INTO journal_items VALUES(?,?,?,?,?,?,?,?)', (item,source[0],'x','https://www.federalreserve.gov/test','Federal Reserve updates guidance','This is a guidance summary.',v5.stamp(),v5.stamp()))
    return v5.create_draft(db)

def test_ai_disabled_never_calls_network(db,monkeypatch):
    d=put_draft(db)
    monkeypatch.delenv('GEMINI_API_KEY',raising=False)
    monkeypatch.delenv('LAWYGO_EDITORIAL_AI_ENABLED',raising=False)
    with pytest.raises(ValueError):v5.enhance_draft_ai(db,d['id'],post=lambda *args,**kw: (_ for _ in ()).throw(RuntimeError('must not run')))

def test_ai_adds_immutable_source_links_and_editor_review(db,monkeypatch):
    d=put_draft(db)
    monkeypatch.setenv('GEMINI_API_KEY','mock-not-a-real-key')
    monkeypatch.setenv('LAWYGO_EDITORIAL_AI_ENABLED','true')
    class Resp:
        def raise_for_status(self):pass
        def json(self):return {'candidates':[{'content':{'parts':[{'text':'[1] This is a mock editorial interpretation, requiring human verification. '*3}]}}]}
    result=v5.enhance_draft_ai(db,d['id'],post=lambda *args,**kw: Resp())
    assert result['generator']=='gemini-assisted'
    assert 'https://www.federalreserve.gov/test' in result['body']
    assert '사실 검증 전' in result['body']
    assert '출처' in result['body']

def test_ai_rejects_reviewed_drafts(db,monkeypatch):
    d=put_draft(db)
    db.execute("UPDATE journal_drafts SET status='in_review' WHERE id=?",(d['id'],))
    monkeypatch.setenv('GEMINI_API_KEY','mock-not-a-real-key')
    monkeypatch.setenv('LAWYGO_EDITORIAL_AI_ENABLED','true')
    with pytest.raises(ValueError):v5.enhance_draft_ai(db,d['id'])
