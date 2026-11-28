import unittest
from legal_wiki_lookup import parse,lookup
from legal_wiki_ingest import IntakeError
class LookupTests(unittest.TestCase):
    def test_exact(self):
        raw="<LawSearch><law><법령명한글>합성법</법령명한글><법령ID>00123</법령ID><법령일련번호>456</법령일련번호><시행일자>20261126</시행일자></law><law><법령명한글>합성법 시행령</법령명한글><법령ID>999</법령ID><법령일련번호>888</법령일련번호><시행일자>20261126</시행일자></law></LawSearch>".encode()
        rows=parse(raw,"합성법")
        self.assertEqual(len(rows),1);self.assertEqual(rows[0]["external_id"],"123");self.assertFalse(rows[0]["confirmed"])
    def test_doctype(self):
        with self.assertRaises(IntakeError):parse(b"<!DOCTYPE foo><law/>","test")
    def test_no_auth(self):
        with self.assertRaises(IntakeError):lookup("민법","test")
