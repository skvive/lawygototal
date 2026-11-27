import unittest
from unittest.mock import Mock
from legal_wiki_readiness import credential_flags,inspect
class ReadinessTests(unittest.TestCase):
    def test_flags_do_not_return_secrets(self):
        env={"LAW_GO_OC":" test ","GEMINI_API_KEY":"fixture-secret"}
        flags=credential_flags(env)
        self.assertFalse(flags["law_go_configured"])
        self.assertTrue(flags["gemini_configured"])
        self.assertNotIn("fixture-secret",str(flags))
    def test_blocked_empty_database(self):
        db=Mock()
        db.execute.return_value.fetchone.return_value=dict(topics=1066,approved_sources=0,lookup_candidates=289,queued=488,mapped_queued=0,raw_payloads=0,canonical_imports=0,verified_precedents=0,searchable_vectors=0,qualified_reviewers=0,verified_revisions=0)
        r=inspect(db,{})
        self.assertFalse(r["preflight_passed"])
        self.assertFalse(r["live_provider_authentication_verified"])
        self.assertIn("SOURCE_APPROVAL_REQUIRED",r["blockers"])
        self.assertIn("OFFICIAL_ID_MAPPING_REQUIRED",r["blockers"])
        self.assertIn("QUALIFIED_REVIEWER_REQUIRED",r["blockers"])
