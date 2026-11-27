"""Optional local multilingual E5 worker. Model files are provisioned separately; no external API."""
import math
import os
import json
from functools import lru_cache
MODEL="intfloat/multilingual-e5-base"
DIM=768
def vector_literal(values):
    vals=[float(v) for v in values]
    if len(vals)!=DIM or not all(math.isfinite(v) for v in vals) or not any(vals):
        raise ValueError("invalid embedding")
    return "["+",".join(format(v,".9g") for v in vals)+"]"

def load_model():
    from sentence_transformers import SentenceTransformer
    path=os.environ.get("LAWYGO_E5_MODEL_DIR")
    if not path or not os.path.isdir(path): raise RuntimeError("local E5 model directory required")
    return SentenceTransformer(path,local_files_only=True,trust_remote_code=False)

@lru_cache(maxsize=1)
def cached_model():
    return load_model()

def encode(model,text,query=False):
    prefix="query: " if query else "passage: "
    return vector_literal(model.encode(prefix+text,normalize_embeddings=True).tolist())

def index_batch(model,limit=100):
    from db_engine import open_db, USE_POSTGRES
    if not USE_POSTGRES: raise RuntimeError("PostgreSQL required")
    limit=max(1,min(100,int(limit)))
    with open_db() as db:
        rows=db.execute("""SELECT p.id,p.holding,p.case_number,p.content_sha256
            FROM legal_wiki.precedents p JOIN legal_wiki.legal_sources s ON s.id=p.source_id
            WHERE p.verified_at IS NOT NULL AND s.verified_at IS NOT NULL AND s.enabled AND s.redistribution_allowed
            AND length(coalesce(p.holding,''))>0
            AND NOT EXISTS(SELECT 1 FROM legal_wiki.precedent_embeddings e WHERE e.precedent_id=p.id AND e.model=? AND e.content_sha256=p.content_sha256)
            ORDER BY p.id LIMIT ?""",(MODEL,limit)).fetchall()
    count=0
    for r in rows:
        vec=encode(model,r["case_number"]+" "+r["holding"])
        with open_db() as db:
            inserted=db.execute("""INSERT INTO legal_wiki.precedent_embeddings(precedent_id,model,content_sha256,embedding)
                SELECT p.id,?,p.content_sha256,CAST(? AS public.vector) FROM legal_wiki.precedents p JOIN legal_wiki.legal_sources s ON s.id=p.source_id
                WHERE p.id=? AND p.content_sha256=? AND p.verified_at IS NOT NULL AND s.verified_at IS NOT NULL AND s.enabled AND s.redistribution_allowed
                ON CONFLICT(precedent_id,model) DO UPDATE SET embedding=excluded.embedding,content_sha256=excluded.content_sha256,created_at=now() RETURNING precedent_id""",(MODEL,vec,r["id"],r["content_sha256"])).fetchone()
            count+=int(inserted is not None)
    return count

def search(db,model,query,limit=20):
    q=query.strip()
    if not 2<=len(q)<=100: raise ValueError("query length")
    vec=encode(model,q,query=True)
    rows=db.execute("""SELECT precedent_id,case_number,court,decided_on,holding,source_url,embedding OPERATOR(public.<=>) CAST(? AS public.vector) AS distance
        FROM legal_wiki.searchable_precedent_embeddings WHERE model=? ORDER BY distance,precedent_id LIMIT ?""",(vec,MODEL,max(1,min(50,int(limit))))).fetchall()
    return [dict(r) for r in rows]

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("action",choices=["index","search"])
    p.add_argument("--query",default="")
    a=p.parse_args()
    m=load_model()
    if a.action=="index": print(json.dumps({"indexed":index_batch(m)}))
    else:
        from db_engine import open_db, USE_POSTGRES
        if not USE_POSTGRES: raise RuntimeError("PostgreSQL required")
        with open_db() as db: print(json.dumps(search(db,m,a.query),ensure_ascii=False,default=str))
