import unittest,json
from unittest.mock import patch,MagicMock
from fastapi import HTTPException
import integrations_v2 as i

class GeminiGroundingTests(unittest.TestCase):
    def call(self,obj):
        response=MagicMock()
        response.json.return_value={"candidates":[{"content":{"parts":[{"text":json.dumps(obj)}]}}]}
        client=MagicMock()
        client.__enter__.return_value.post.return_value=response
        with patch.dict("os.environ",{"GEMINI_API_KEY":"fixture-not-real"}),patch.object(i.httpx,"Client",return_value=client):
            return i._gemini_analyze("[SOURCE source-note] 합성 문서 검토용 내용입니다.",[{"id":"source-note","title":"fixture"}])
    def result(self,ids):
        return {"summary":"검토 요약","issues":[{"issue":"검토 쟁점","source_ids":ids}],"evidence_gaps":[],"questions":[],"disclaimer":"검수 필요"}
    def test_valid(self): self.assertEqual(self.call(self.result(["source-note"]))["issues"][0]["source_ids"],["source-note"])
    def test_missing_sources(self):
        with self.assertRaises(HTTPException) as e: self.call(self.result([]))
        self.assertEqual(e.exception.status_code,502)
    def test_invented_source(self):
        with self.assertRaises(HTTPException) as e: self.call(self.result(["invented"]))
        self.assertEqual(e.exception.status_code,502)
    def test_wrong_shape(self):
        with self.assertRaises(HTTPException): self.call({"summary":123})
    def test_no_key(self):
        with patch.dict("os.environ",{"GEMINI_API_KEY":""}),patch.object(i.httpx,"Client") as client:
            with self.assertRaises(HTTPException) as e: i._gemini_analyze("fixture",[])
            self.assertEqual(e.exception.status_code,503);client.assert_not_called()
