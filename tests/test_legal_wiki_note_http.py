"""Actual NOTE HTTP routes with isolated SQLite login and synthetic provider response."""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import HTTPException

class NoteAnalysisHttpTests(unittest.TestCase):
    def test_owner_consent_provider_failure_and_history(self):
        import app as a
        import integrations_v2 as v
        env={"LAWYGO_BOOTSTRAP_EMAIL":"note-test@example.invalid","LAWYGO_BOOTSTRAP_PASSWORD":"fixture-only-password-2026","LAWYGO_SECURE_COOKIES":"false","GEMINI_API_KEY":"","LAWYGO_LEGAL_WIKI_ENABLED":"0"}
        with tempfile.TemporaryDirectory() as tmp,patch.dict(os.environ,env),patch.object(a,"DB_FILE",Path(tmp)/"test.db"),patch.object(a,"FILES",Path(tmp)/"uploads"):
            with TestClient(a.app) as c:
                self.assertEqual(c.post("/api/note/unknown/ai-analyze",json={"consent":True}).status_code,401)
                self.assertEqual(c.post("/api/auth/login",json={"email":env["LAWYGO_BOOTSTRAP_EMAIL"],"password":env["LAWYGO_BOOTSTRAP_PASSWORD"],"tenant":"demo"}).status_code,200)
                headers={"X-CSRF-Token":c.cookies.get(a.CSRF_COOKIE)}
                boards=c.get("/api/boards?product=note").json()["items"]
                self.assertTrue(boards)
                r=c.post("/api/posts",headers=headers,json={"board_id":boards[0]["id"],"kind":"note","title":"합성 비공개 노트","body":"합성 계약 검토용 본문이며 실제 의뢰인 정보가 아닙니다.","visibility":"private"})
                self.assertEqual(r.status_code,201,r.text)
                pid=r.json()["id"];path="/api/note/"+pid+"/ai-analyze"
                with patch.object(v,"_gemini_analyze") as provider:
                    self.assertEqual(c.post(path,json={"consent":True}).status_code,403)
                    self.assertEqual(c.post(path,headers=headers,json={"consent":False}).status_code,400)
                    self.assertEqual(c.post("/api/note/unknown/ai-analyze",headers=headers,json={"consent":True}).status_code,404)
                    self.assertEqual(c.post(path,headers=headers,json={"consent":True,"wiki_query":"계약"}).status_code,503)
                    provider.assert_not_called()
                self.assertEqual(c.post(path,headers=headers,json={"consent":True}).status_code,503)
                self.assertEqual(c.get("/api/note/"+pid+"/ai-runs").json()["items"],[])
                result={"summary":"합성 분석 요약","issues":[{"issue":"합성 쟁점","source_ids":["source-note"]}],"evidence_gaps":[],"questions":[],"disclaimer":"테스트"}
                with patch.object(v,"_gemini_analyze",return_value=result) as provider:
                    r=c.post(path,headers=headers,json={"consent":True})
                    self.assertEqual(r.status_code,200,r.text)
                    self.assertEqual(r.json()["sources"][0]["id"],"source-note")
                    provider.assert_called_once()
                    args=provider.call_args.args
                    self.assertIn("합성 계약",args[0]);self.assertEqual(args[1][0]["id"],"source-note")
                rid=r.json()["id"]
                history=c.get("/api/note/"+pid+"/ai-runs").json()["items"]
                self.assertEqual(len(history),1)
                detail=c.get("/api/note/"+pid+"/ai-runs/"+rid).json()
                self.assertEqual(detail["result"]["sources"][0]["id"],"source-note")
