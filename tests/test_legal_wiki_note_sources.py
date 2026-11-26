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
