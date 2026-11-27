import unittest
from unittest.mock import Mock,patch
from legal_wiki_mapping import candidate,candidates,confirm

class MappingTests(unittest.TestCase):
    def setUp(self):
        self.item={"target":"eflaw","title":"합성법","exact_match":True,"external_id":"1","master_id":"2","effective_from":"2020-01-01"}
        self.user={"id":"fixture","tenant":"operator"}
    def test_exact_identity_and_secret_free_link(self):
        c=candidate("합성법",self.item)
        self.assertIn("MST=2",c["evidence_url"])
        self.assertNotIn("OC=",c["evidence_url"])
        self.assertEqual(len(c["candidate_sha256"]),64)
        self.assertIsNone(candidate("다른법",self.item))
        with self.assertRaises(ValueError):candidate("합성법",{**self.item,"external_id":"0"})
    def test_approval_gate_precedes_network(self):
        db=Mock()
        db.execute.return_value.fetchone.side_effect=[{"job_id":1,"query":"합성법","plan_status":"candidate_lookup","source_id":7},None]
        with patch("legal_wiki_mapping.search") as s:
            with self.assertRaises(PermissionError):candidates(db,1)
            s.assert_not_called()
    def test_recheck_selection_and_provenance(self):
        db=Mock()
        c=candidate("합성법",self.item)
        with patch("legal_wiki_mapping.candidates",return_value={"items":[c]}) as fetch:
            with self.assertRaises(ValueError):confirm(db,1,1,c["candidate_sha256"],self.user,False)
            fetch.assert_not_called()
            with self.assertRaises(ValueError):confirm(db,1,1,"b"*64,self.user,True)
            db.execute.assert_not_called()
            db.execute.return_value.fetchone.return_value={"job_id":1}
            self.assertTrue(confirm(db,1,1,c["candidate_sha256"],self.user,True)["mapped"])
            fetch.assert_called_with(db,1,1,True)
            self.assertEqual(db.execute.call_args.args[1][1:4],("1","2","2020-01-01"))
            self.assertIn("operator",db.execute.call_args.args[1])
    def test_existing_mapping_cannot_overwrite(self):
        db=Mock();db.execute.return_value.fetchone.return_value=None
        c=candidate("합성법",self.item)
        with patch("legal_wiki_mapping.candidates",return_value={"items":[c]}):
            with self.assertRaises(ValueError):confirm(db,1,1,c["candidate_sha256"],self.user,True)
