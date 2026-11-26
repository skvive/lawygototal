import unittest
from legal_wiki_drafts import key,validate,body
class DraftTests(unittest.TestCase):
    def test_unicode(self): self.assertEqual(key("계약 해제！"),key("계약해제"))
    def test_missing(self):
        with self.assertRaises(ValueError): validate({"title":"연구"})
    def test_draft(self):
        r=dict(category="civil",slug="valid-title",title="계약 검토 요점",issue="계약 체결 및 변경 과정 확인",evidence="계약서 원본과 회신 자료 확보",defense="상대방의 별도 합의 주장 확인",action="실제 이행 여부 시간순으로 정리")
        self.assertIn("미검수",body(validate(r)))
