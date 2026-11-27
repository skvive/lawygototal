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

    def test_long_passage_covers_tail(self):
        from legal_wiki_embeddings import encode_long
        class Tokenizer:
            def encode(self,text,**kw):return list(range(len(text.split())))
            def decode(self,ids,**kw):return " ".join(str(i) for i in ids)
        class LongModel(Model):
            tokenizer=Tokenizer()
            max_seq_length=512
            def __init__(self):self.calls=[]
            def encode(self,text,normalize_embeddings):
                self.calls.append(text);return Array()
        m=LongModel()
        vec,count=encode_long(m," ".join("word" for _ in range(900)))
        self.assertEqual(count,3)
        self.assertIn("899",m.calls[-1])
        self.assertEqual(len(vec[1:-1].split(",")),DIM)
    def test_manifest_rejects_changed_files(self):
        import tempfile,hashlib,json
        from pathlib import Path
        from legal_wiki_embeddings import verify_manifest,MODEL,REVISION
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);p=root/"model.safetensors";p.write_bytes(b"fixture")
            raw=json.dumps({"model":MODEL,"revision":REVISION,"files":{p.name:hashlib.sha256(p.read_bytes()).hexdigest()}}).encode()
            (root/"lawygo-model-manifest.json").write_bytes(raw)
            expected=hashlib.sha256(raw).hexdigest()
            self.assertEqual(len(verify_manifest(root,expected)),64)
            p.write_bytes(b"changed")
            with self.assertRaises(ValueError):verify_manifest(root,expected)
