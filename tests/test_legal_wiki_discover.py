import unittest
from legal_wiki_discover import parse,search,IntakeError
class DiscoveryTests(unittest.TestCase):
    def test_law(self):
        xml="<LawSearch><target>eflaw</target><totalCnt>1</totalCnt><law><법령ID>001</법령ID><법령일련번호>002</법령일련번호><법령명한글>합성법</법령명한글><시행일자>20200101</시행일자></law></LawSearch>"
        r=parse(xml.encode(),"eflaw","합성법")
        self.assertEqual(r["items"][0]["external_id"],"1")
        self.assertTrue(r["items"][0]["exact_match"])
        self.assertFalse(r["items"][0]["confirmed"])
    def test_precedent(self):
        xml="<PrecSearch><target>prec</target><totalCnt>1</totalCnt><prec><판례일련번호>5</판례일련번호><사건번호>2020가합1</사건번호><사건명>합성</사건명><선고일자>20200101</선고일자></prec></PrecSearch>"
        self.assertTrue(parse(xml.encode(),"prec","2020가합1")["items"][0]["exact_match"])
    def test_invalid(self):
        for raw in (b"<!DOCTYPE x><x/>",b"<error/>"):
            with self.assertRaises(IntakeError): parse(raw,"eflaw","law")
    def test_no_key(self):
        with self.assertRaises(IntakeError):search("eflaw","민법","")
