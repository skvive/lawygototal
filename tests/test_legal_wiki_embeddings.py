import unittest
from legal_wiki_embeddings import vector_literal,encode,DIM
class Array:
    def tolist(self): return [1.0]+[0.0]*(DIM-1)
class Model:
    def encode(self,text,normalize_embeddings):
        self.text=text
        assert normalize_embeddings
        return Array()
class EmbeddingsTests(unittest.TestCase):
    def test_vector(self):
        self.assertEqual(len(vector_literal([1]*DIM)[1:-1].split(",")),DIM)
    def test_invalid(self):
        for v in ([0]*DIM,[1], [float("nan")]*DIM):
            with self.assertRaises(ValueError): vector_literal(v)
    def test_query_prefix(self):
        m=Model();encode(m,"채무불이행",True);self.assertEqual(m.text,"query: 채무불이행")
    def test_passage_prefix(self):
        m=Model();encode(m,"판례",False);self.assertEqual(m.text,"passage: 판례")
