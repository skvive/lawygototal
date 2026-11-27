import unittest
from legal_wiki_note_sources import pack_sources,validate_result
class NoteSourceTests(unittest.TestCase):
    def test_truncation_excludes_untransmitted_sources(self):
        source,refs=pack_sources([({"id":"n"},"a"*100),({"id":"pdf"},"b"*100)],60)
        self.assertLessEqual(len(source),60)
        self.assertEqual([x["id"] for x in refs],["n"])
        self.assertTrue(refs[0]["truncated"])
    def test_blank_source(self):
        source,refs=pack_sources([({"id":"n"},"  "),({"id":"p"},"자료 본문")])
        self.assertEqual([x["id"] for x in refs],["p"])
    def test_good(self):
        obj={"summary":"검토","issues":[{"issue":"쟁점","source_ids":["n"]}],"evidence_gaps":[],"questions":[]}
        self.assertEqual(validate_result(obj,[{"id":"n"}])["summary"],"검토")
    def test_missing_invalid_refs(self):
        for ids in ([],["fake"],"n",None):
            with self.assertRaises(ValueError):validate_result({"summary":"검토","issues":[{"issue":"쟁점","source_ids":ids}],"evidence_gaps":[],"questions":[]},[{"id":"n"}])

    def test_upstream_truncation_not_hidden(self):
        _,refs=pack_sources([({"id":"n","source_chars":20000,"pre_truncated":True},"a"*12000)],30000)
        self.assertTrue(refs[0]["truncated"])
        self.assertEqual(refs[0]["included_chars"],12000)
        self.assertEqual(refs[0]["source_chars"],20000)
        self.assertNotIn("pre_truncated",refs[0])
    def test_pdf_page_limit_disclosed(self):
        _,refs=pack_sources([({"id":"pdf","pages_total":20,"pages_examined":10,"pre_truncated":True},"합성 원문 테스트")])
        self.assertTrue(refs[0]["truncated"])
        self.assertEqual(refs[0]["pages_examined"],10)
