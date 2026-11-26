"""Actual model smoke on synthetic Korean phrases only. No legal corpus or private notes."""
import os, math
from sentence_transformers import SentenceTransformer
from legal_wiki_embeddings import DIM, MODEL
def main():
    model=SentenceTransformer(MODEL,revision="5c31b33181f6c6bfbbce758a5900f9407bbcff42",trust_remote_code=False,device="cpu")
    q="query: 임대차 종료 후 보증금을 돌려받는 방법"
    passages=["passage: 임차인이 계약 종료 이후 임대차보증금 반환을 청구하는 분쟁","passage: 회사 이사회 결의와 이사의 책임"]
    vectors=model.encode([q,*passages],normalize_embeddings=True)
    assert vectors.shape==(3,DIM)
    assert all(math.isfinite(float(x)) for row in vectors for x in row)
    scores=[float(vectors[0]@v) for v in vectors[1:]]
    assert scores[0]>scores[1],scores
    print({"model":MODEL,"dimension":DIM,"related":scores[0],"unrelated":scores[1],"synthetic_only":True})
if __name__=="__main__":main()
