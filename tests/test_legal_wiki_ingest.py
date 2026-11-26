import unittest
from legal_wiki_ingest import params, validate, IntakeError

class IntakeTests(unittest.TestCase):
    def test_reject_test_key(self):
        with self.assertRaises(IntakeError): params("prec","123","test")
    def test_reject_non_numeric(self):
        with self.assertRaises(IntakeError): params("prec","../123","approved")
    def test_wrong_id(self):
        with self.assertRaises(IntakeError): validate("<r><판례정보일련번호>2</판례정보일련번호></r>".encode(),"prec","1")
    def test_dtd(self):
        with self.assertRaises(IntakeError): validate(b"<!DOCTYPE r><r/>","prec","1")
    def test_valid_fixture(self):
        raw="<r><판례정보일련번호>1</판례정보일련번호><사건번호>fixture</사건번호><선고일자>20200101</선고일자><법원명>fixture</법원명><판례내용>fixture only</판례내용></r>".encode()
        _,digest=validate(raw,"prec","1")
        self.assertEqual(len(digest),64)
if __name__=="__main__": unittest.main()
