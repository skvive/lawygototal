import unittest
from legal_wiki_concepts import expand,rerank
class ConceptsTests(unittest.TestCase):
    def test_expand(self):
        self.assertIn("이행지체",expand("채무 불이행"))
    def test_rank(self):
        rows=[{"id":1,"holding":"이행지체 손해배상"},{"id":2,"holding":"소유권"},{"id":3,"holding":"채무불이행"}]
        result=rerank("채무불이행",rows)
        self.assertEqual([r["id"] for r in result],[3,1])
    def test_blank(self):
        self.assertEqual(expand("  "),[])
