"""HTTP-level checks, using real login/CSRF and isolated synthetic wiki database adapter."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import legal_wiki_api

class RealLoginTests(unittest.TestCase):
    def test_login_and_csrf_and_disabled_wiki(self):
        import app as a
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ,{"LAWYGO_BOOTSTRAP_EMAIL":"test-lawyer@example.invalid","LAWYGO_BOOTSTRAP_PASSWORD":"fixture-only-password-2026","LAWYGO_SECURE_COOKIES":"false","LAWYGO_LEGAL_WIKI_ENABLED":"0"}), patch.object(a,"DB_FILE",Path(tmp)/"test.db"), patch.object(a,"FILES",Path(tmp)/"uploads"):
            with TestClient(a.app) as client:
                self.assertEqual(client.get("/api/wiki/v2/review-queue").status_code,401)
                res=client.post("/api/auth/login",json={"email":"test-lawyer@example.invalid","password":"fixture-only-password-2026","tenant":"demo"})
                self.assertEqual(res.status_code,200,res.text)
                self.assertEqual(client.get("/api/wiki/v2/review-queue").status_code,503)
                path="/api/wiki/v2/revisions/1/review?decision=approve"
                self.assertEqual(client.post(path).status_code,403)
                token=client.cookies.get(a.CSRF_COOKIE)
                self.assertEqual(client.post(path,headers={"X-CSRF-Token":token}).status_code,503)
                self.assertEqual(client.post(path,headers={"X-CSRF-Token":token,"Origin":"https://invalid.example"}).status_code,403)

class Row:
    def __init__(self,one=None,all=None): self.one=one;self.all=all or []
    def fetchone(self): return self.one
    def fetchall(self): return self.all

class SyntheticDB:
    def __init__(self):
        self.qualified=True;self.author="writer";self.available=True;self.writes=0
    def execute(self,sql,args=()):
        if "to_regclass" in sql: return Row({"ready":True})
        if "set_config" in sql: return Row()
        if "lawyer_verifications" in sql: return Row({"user_id":"reviewer"} if self.qualified else None)
        if "FROM legal_wiki.wiki_revisions" in sql and "FOR UPDATE" in sql: return Row({"id":1,"author_id":self.author,"status":"draft","legal_as_of":"2020-01-01","digest":"a"*64})
        if "SELECT 1 FROM legal_wiki.qualified_verified_revisions" in sql: return Row()
        if "AS original" in sql: return Row({"original":"합성 테스트 원문 문장입니다","source_url":"https://www.law.go.kr/test"} if self.available else None)
        if "INSERT INTO legal_wiki.citations" in sql: self.writes+=1;return Row({"id":42})
        if "approve_and_publish" in sql: self.writes+=1;return Row({"id":1})
        if "FROM posts WHERE" in sql: return Row()
        raise AssertionError(sql)

class CitationHttpTests(unittest.TestCase):
    def setUp(self):
        self.db=SyntheticDB()
        self.user={"tenant":"fixture","id":"reviewer","role":"editor"}
        a=FastAPI()
        def database(): return self.db
        def user(): return self.user
        legal_wiki_api.register(a,database,user,user)
        self.client=TestClient(a)
        self.env=patch.dict(os.environ,{"LAWYGO_LEGAL_WIKI_ENABLED":"1"})
        self.flag=patch.object(legal_wiki_api,"USE_POSTGRES",True)
        self.env.start();self.flag.start()
        self.addCleanup(self.env.stop);self.addCleanup(self.flag.stop)
    def request(self,**kwargs):
        body=dict(kind="precedent",source_id=1,proposition_key="쟁점",pinpoint="합성 테스트 원문 문장",relation="supports",confirm=True)
        body.update(kwargs)
        return self.client.post("/api/wiki/v2/revisions/1/citations",json=body)
    def test_exact_quote(self):
        self.assertEqual(self.request().status_code,200)
        self.assertEqual(self.db.writes,1)
    def test_no_consent(self):
        self.assertEqual(self.request(confirm=False).status_code,400);self.assertEqual(self.db.writes,0)
    def test_whitespace(self):
        self.assertEqual(self.request(pinpoint=" "*10).status_code,400);self.assertEqual(self.db.writes,0)
    def test_mismatch(self):
        self.assertEqual(self.request(pinpoint="존재하지 않는 원문입니다").status_code,409)
    def test_wrong_date_or_unverified_source(self):
        self.db.available=False;self.assertEqual(self.request().status_code,409)
    def test_unqualified(self):
        self.db.qualified=False;self.assertEqual(self.request().status_code,403)
    def test_self_review(self):
        self.db.author="reviewer";self.assertEqual(self.request().status_code,403)
    def test_approval_digest(self):
        path="/api/wiki/v2/revisions/1/review?decision=approve"
        self.assertEqual(self.client.post(path).status_code,409)
        self.assertEqual(self.client.post(path+"&expected_digest="+"b"*64).status_code,409)
        self.assertEqual(self.client.post(path+"&expected_digest="+"a"*64).status_code,200)
    def test_private_note_missing(self):
        self.assertEqual(self.client.get("/api/wiki/v2/note/private/evidence?q=계약").status_code,404)

if __name__=="__main__":unittest.main()
