"""Idempotent JSONL research draft importer. No publication or fabricated citations."""
import argparse
import json
import re
import unicodedata
def key(title):
    return "".join(c for c in unicodedata.normalize("NFKC",title).lower() if c.isalnum())
def validate(row):
    required=("category","slug","title","issue","evidence","defense","action")
    if not isinstance(row,dict) or any(not isinstance(row.get(k),str) or not row[k].strip() for k in required): raise ValueError("required research fields")
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{2,100}",row["slug"]) or not 5<=len(key(row["title"]))<=150: raise ValueError("invalid slug/title")
    if any(len(row[k])<12 for k in ("issue","evidence","defense","action")): raise ValueError("insufficient substantive fields")
    if len(set(row[k].strip() for k in ("issue","evidence","defense","action")))!=4: raise ValueError("repeated fields")
    return row
def body(r):
    return "> AI 연구 초안 · 공식 법령/판례 및 변호사 미검수.\n\n"+"\n\n".join("## "+h+"\n"+r[k] for h,k in (("핵심 쟁점","issue"),("증거 및 입증계획","evidence"),("예상 항변","defense"),("실무 대응","action")))+"\n\n## 검증 대기\n적용 조문·판례 원문·기한·입증책임 확인 필요."
def import_rows(db,rows,tenant,as_of):
    if not isinstance(tenant,str) or not tenant.strip(): raise ValueError("tenant required")
    db.execute("SELECT set_config('app.tenant',?,true)",(tenant,))
    count=0; seen=set()
    for row in rows:
        r=validate(row); k=key(r["title"])
        if k in seen: continue
        seen.add(k)
        c=db.execute("SELECT id FROM legal_wiki.categories WHERE slug=?",(r["category"],)).fetchone()
        if not c: raise ValueError("unknown category")
        t=db.execute("""INSERT INTO legal_wiki.wiki_topics(tenant,slug,category_id,title,audience) VALUES(?,?,?,?,'lawyer') ON CONFLICT DO NOTHING RETURNING id""",(tenant,r["slug"],c["id"],r["title"])).fetchone()
        if not t: continue
        db.execute("""INSERT INTO legal_wiki.wiki_revisions(tenant,topic_id,version,title,summary,body_markdown,author_id,status,legal_as_of) VALUES(?,?,1,?,?,?,'lw06-ai-draft','draft',CAST(? AS date))""",(tenant,t["id"],r["title"],r["issue"],body(r),as_of))
        count+=1
    return count
if __name__=="__main__":
    from datetime import date
    from db_engine import open_db,USE_POSTGRES
    p=argparse.ArgumentParser();p.add_argument("jsonl");p.add_argument("--tenant",required=True);p.add_argument("--as-of",required=True);a=p.parse_args()
    if not USE_POSTGRES: raise SystemExit("PostgreSQL required")
    date.fromisoformat(a.as_of)
    with open(a.jsonl,encoding="utf-8") as f: rows=[json.loads(s) for s in f if s.strip()]
    with open_db() as db: print(json.dumps({"inserted":import_rows(db,rows,a.tenant,a.as_of)}))
