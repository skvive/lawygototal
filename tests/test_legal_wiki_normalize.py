import unittest
from legal_wiki_normalize import normalize

LAW="""<법령><기본정보><법령ID>12</법령ID><법령명_한글>테스트법</법령명_한글><법종구분>법률</법종구분><공포일자>20200101</공포일자><시행일자>20200201</시행일자></기본정보><조문><조문단위><조문번호>10</조문번호><조문가지번호>2</조문가지번호><조문여부>조문</조문여부><조문제목>테스트</조문제목><조문내용>본문</조문내용><항><항내용>제1항</항내용></항></조문단위></조문><부칙><부칙내용>부칙 샘플</부칙내용></부칙></법령>"""
PREC="""<r><판례정보일련번호>1</판례정보일련번호><사건번호>fixture</사건번호><선고일자>20200101</선고일자><법원명>fixture</법원명><판결요지>요지 샘플</판결요지><판례내용>본문 샘플</판례내용></r>"""
class NormalizationTests(unittest.TestCase):
    def test_articles(self):
        d=normalize(LAW.encode(),"eflaw","12","166520")
        self.assertEqual(d["external_version_id"],"mst:166520")
        self.assertEqual(d["articles"][0]["article_key"],"10-2")
        self.assertIn("제1항",d["articles"][0]["body"])
        self.assertEqual(d["articles"][0]["effective_from"],"2020-02-01")
        self.assertEqual(d["transitional_notes"],["부칙 샘플"])
        self.assertFalse(d["verified"])
    def test_historical_identity(self):
        d=normalize(LAW.encode(),"eflaw","12","166520","2020-02-01")
        self.assertEqual(d["external_version_id"],"mst:166520:2020-02-01")
        with self.assertRaises(ValueError):normalize(LAW.encode(),"eflaw","12","166520","2021-02-01")
    def test_current_id_has_no_invented_mst(self):
        self.assertTrue(normalize(LAW.encode(),"eflaw","12")["external_version_id"].startswith("sha256:"))
    def test_precedent(self):
        d=normalize(PREC.encode(),"prec","1")
        self.assertEqual(d["decided_on"],"2020-01-01")
        self.assertFalse(d["verified"])
    def test_mismatch(self):
        with self.assertRaises(ValueError): normalize(PREC.encode(),"prec","2")
    def test_bad_date(self):
        with self.assertRaises(ValueError): normalize(PREC.replace("20200101","20201399").encode(),"prec","1")
    def test_duplicate_article(self):
        fragment=LAW[LAW.index("<조문단위>"):LAW.index("</조문단위>")+len("</조문단위>")]
        with self.assertRaises(ValueError): normalize(LAW.replace("</조문>",fragment+"</조문>").encode(),"eflaw","12")
    def test_dtd(self):
        with self.assertRaises(ValueError): normalize(b"<!DOCTYPE r><r/>","prec","1")
