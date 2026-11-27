import unittest
from unittest.mock import Mock,patch
from legal_wiki_source_review import approve,require_fields
class SourceReviewTests(unittest.TestCase):
    def test_canonical_drift(self):
        with self.assertRaises(ValueError):require_fields({"body":"changed"},{"body":"original"},("body",))
    def test_explicit_confirmation_and_digest(self):
        db=Mock();user={"id":"fixture","tenant":"fixture"}
        with patch("legal_wiki_source_review.packet",return_value={"digest":"a"*64,"verified":False,"kind":"precedent","canonical_id":7}) as p:
            for digest,confirmed in [("a"*64,False),("b"*64,True)]:
                with self.assertRaises(ValueError):approve(db,1,user,digest,"합성 원문 검수 의견입니다",confirmed)
            db.execute.assert_not_called()
            approve(db,1,user,"a"*64,"합성 원문 검수 의견입니다",True)
            self.assertEqual(db.execute.call_count,2)
            self.assertIn("source_text_reviews",db.execute.call_args_list[0].args[0])
            self.assertIn("SET verified_at",db.execute.call_args_list[1].args[0])
            p.assert_called_with(db,1,True)
