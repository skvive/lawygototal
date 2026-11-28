"""Optional local multilingual E5 worker. Model files are provisioned separately; no external API."""
import math
import os
import json
import hashlib
from pathlib import Path
from functools import lru_cache
MODEL="intfloat/multilingual-e5-base"
DIM=768
REVISION="5c31b33181f6c6bfbbce758a5900f9407bbcff42"
ALGORITHM="e5-token-chunks-384-overlap-32-mean-v1"

def model_profile(manifest_digest):
    if len(manifest_digest)!=64 or any(c not in '0123456789abcdef' for c in manifest_digest):raise ValueError('invalid model manifest digest')
    return hashlib.sha256((MODEL+'|'+REVISION+'|'+ALGORITHM+'|'+manifest_digest).encode()).hexdigest()

def verify_manifest(path,expected):
    root=Path(path).resolve()
    manifest=root/'lawygo-model-manifest.json'
    raw=manifest.read_bytes()
    if hashlib.sha256(raw).hexdigest()!=expected:raise ValueError('untrusted model manifest')
    obj=json.loads(raw)
    if obj.get('model')!=MODEL or obj.get('revision')!=REVISION:raise ValueError('wrong model revision')
    files=obj.get('files')
    if not isinstance(files,dict) or not files:raise ValueError('empty model manifest')
    actual={p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file() and p!=manifest}
    if set(files)!=actual or not any(x.endswith('.safetensors') for x in files):raise ValueError('model file inventory mismatch')
    for name,digest in files.items():
        p=root/name
        if p.is_symlink() or not p.resolve().is_relative_to(root) or not p.is_file() or p.suffix in ('.bin','.pt','.pkl','.pickle'):raise ValueError('unsafe model file')
        with p.open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest()!=digest:raise ValueError('model file digest mismatch')
    return model_profile(expected)

def vector_literal(values):
    vals=[float(v) for v in values]
    if len(vals)!=DIM or not all(math.isfinite(v) for v in vals) or not any(vals):
        raise ValueError("invalid embedding")
    return "["+",".join(format(v,".9g") for v in vals)+"]"

def load_model():
    from sentence_transformers import SentenceTransformer
    path=os.environ.get("LAWYGO_E5_MODEL_DIR")
    if not path or not os.path.isdir(path): raise RuntimeError("local E5 model directory required")
    profile=verify_manifest(path,os.environ.get('LAWYGO_E5_MANIFEST_SHA256',''))
    model=SentenceTransformer(path,local_files_only=True,trust_remote_code=False,model_kwargs={'use_safetensors':True})
    if model.get_sentence_embedding_dimension()!=DIM:raise ValueError('wrong E5 dimension')
    model.lawygo_profile=profile
    return model

@lru_cache(maxsize=1)
def cached_model():
    return load_model()

def encode(model,text,query=False):
    prefix="query: " if query else "passage: "
    return vector_literal(model.encode(prefix+text,normalize_embeddings=True).tolist())

def encode_long(model,text):
    # Tokenize without silent truncation and include all token chunks.
    ids=model.tokenizer.encode(text,add_special_tokens=False,truncation=False)
    if not ids:raise ValueError('empty precedent text')
    window=min(384,int(model.max_seq_length)-16)
    if window<64:raise ValueError('model context too short')
    stride=window-32
    sums=[0.0]*DIM
    count=0
    for start in range(0,len(ids),stride):
        part=ids[start:start+window]
        passage=model.tokenizer.decode(part,skip_special_tokens=True)
        if len(model.tokenizer.encode('passage: '+passage,add_special_tokens=True,truncation=False))>model.max_seq_length:raise ValueError('chunk exceeds model context')
        values=model.encode('passage: '+passage,normalize_embeddings=True).tolist()
        vector_literal(values)
        weight=len(part) if start==0 else max(1,len(part)-32)
        for i,v in enumerate(values):sums[i]+=float(v)*weight
        count+=1
        if start+window>=len(ids):break
    norm=math.sqrt(sum(v*v for v in sums))
    if not norm or not math.isfinite(norm):raise ValueError('invalid aggregate vector')
    return vector_literal([v/norm for v in sums]),count

def index_batch(model,limit=100):
    from db_engine import open_db, USE_POSTGRES
    if not USE_POSTGRES: raise RuntimeError("PostgreSQL required")
    profile=model.lawygo_profile
    limit=max(1,min(100,int(limit)))
    with open_db() as db:
        rows=db.execute("""SELECT p.id,p.holding,p.original_text,p.case_number,p.content_sha256,p.verified_at
            FROM legal_wiki.precedents p JOIN legal_wiki.legal_sources s ON s.id=p.source_id
            WHERE p.verified_at IS NOT NULL AND s.verified_at IS NOT NULL AND s.enabled AND s.redistribution_allowed
            AND length(coalesce(p.holding,'')||coalesce(p.original_text,''))>0
            AND NOT EXISTS(SELECT 1 FROM legal_wiki.precedent_embeddings e WHERE e.precedent_id=p.id AND e.model=? AND e.content_sha256=p.content_sha256 AND e.model_profile=? AND e.indexed_verified_at=p.verified_at)
            ORDER BY p.id LIMIT ?""",(MODEL,profile,limit)).fetchall()
    count=0
    for r in rows:
        vec,_=encode_long(model,r["case_number"]+"\n"+(r["holding"] or "")+"\n"+(r["original_text"] or ""))
        with open_db() as db:
            inserted=db.execute("""INSERT INTO legal_wiki.precedent_embeddings(precedent_id,model,content_sha256,embedding,model_profile,indexed_verified_at)
                SELECT p.id,?,p.content_sha256,CAST(? AS public.vector),?,p.verified_at FROM legal_wiki.precedents p JOIN legal_wiki.legal_sources s ON s.id=p.source_id
                WHERE p.id=? AND p.content_sha256=? AND p.verified_at=? AND p.verified_at IS NOT NULL AND s.verified_at IS NOT NULL AND s.enabled AND s.redistribution_allowed
                ON CONFLICT(precedent_id,model) DO UPDATE SET embedding=excluded.embedding,content_sha256=excluded.content_sha256,model_profile=excluded.model_profile,indexed_verified_at=excluded.indexed_verified_at,created_at=now() RETURNING precedent_id""",(MODEL,vec,profile,r["id"],r["content_sha256"],r["verified_at"])).fetchone()
            count+=int(inserted is not None)
    return count

def search(db,model,query,limit=20):
    q=query.strip()
    if not 2<=len(q)<=100: raise ValueError("query length")
    vec=encode(model,q,query=True)
    rows=db.execute("""SELECT precedent_id,case_number,court,decided_on,holding,source_url,embedding OPERATOR(public.<=>) CAST(? AS public.vector) AS distance
        FROM legal_wiki.searchable_precedent_embeddings WHERE model=? AND model_profile=? ORDER BY distance,precedent_id LIMIT ?""",(vec,MODEL,model.lawygo_profile,max(1,min(50,int(limit))))).fetchall()
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
