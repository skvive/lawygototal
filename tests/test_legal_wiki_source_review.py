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

    def test_packet_reparses_original_and_rejects_modified_canonical_precedent(self):
        import hashlib
        from datetime import date
        from legal_wiki_normalize import normalize
        from legal_wiki_source_review import packet
        from test_legal_wiki_normalize import PREC
        data=normalize(PREC.encode(),"prec","1")
        r={"target":"prec","external_id":"1","raw_xml":PREC,"content_sha256":hashlib.sha256(PREC.encode()).hexdigest(),"master_id":None,"requested_effective_on":None,"source_url":"https://www.law.go.kr/fixture","normalized_json":data,"kind":"precedent","normalized_hash":data["content_sha256"],"statute_version_id":None,"precedent_id":7,"source_id":1,"code":"kr-law-go","agency":"fixture","base_url":"https://www.law.go.kr/","usage_terms":"fixture-only","source_verified_at":"2026-11-27"}
        canonical={**data,"source_id":1,"source_url":r["source_url"],"verified_at":None,"decided_on":date.fromisoformat(data["decided_on"])}
        db=Mock()
        db.execute.return_value.fetchone.side_effect=[r,canonical]
        p=packet(db,3)
        self.assertEqual(p["canonical_id"],7)
        self.assertFalse(p["verified"])
        self.assertEqual(len(p["digest"]),64)
        canonical["original_text"]="변조된 합성 원문"
        db.execute.return_value.fetchone.side_effect=[r,canonical]
        with self.assertRaises(ValueError):packet(db,3)
    def test_packet_source_permission_missing(self):
        from legal_wiki_source_review import packet
        db=Mock();db.execute.return_value.fetchone.return_value=None
        with self.assertRaises(LookupError):packet(db,3)
