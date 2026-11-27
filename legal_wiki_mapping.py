"""Map only an explicitly selected exact official search result, never a guessed ID."""
import hashlib
import json
import os
import re
from datetime import date
from urllib.parse import urlencode
from legal_wiki_discover import search
from legal_wiki_ingest import IntakeError

def queue(db,limit=100,offset=0):
    return [dict(x) for x in db.execute("""SELECT job_id,reference_label,query,plan_status
      FROM legal_wiki.reference_lookup_plan ORDER BY CASE WHEN plan_status='candidate_lookup' THEN 0 WHEN plan_status='manual_review' THEN 1 ELSE 2 END,job_id LIMIT ? OFFSET ?""",(limit,offset)).fetchall()]

def plan(db,job_id,lock=False):
    if lock:
        row=db.execute("SELECT id FROM legal_wiki.ingestion_jobs WHERE id=? AND status='queued' FOR UPDATE",(job_id,)).fetchone()
        if not row:raise LookupError("queued job not found")
    row=db.execute("""SELECT p.job_id,p.reference_label,p.query,p.plan_status,p.source_id
      FROM legal_wiki.reference_lookup_plan p WHERE p.job_id=?""",(job_id,)).fetchone()
    if not row:raise LookupError("queued reference not found")
    if row["plan_status"]!="candidate_lookup" or not row["query"]:raise ValueError("manual review or existing mapping")
    approved=db.execute("""SELECT id FROM legal_wiki.legal_sources WHERE id=? AND code='kr-law-go'
      AND enabled AND redistribution_allowed AND verified_at IS NOT NULL"""+(" FOR SHARE" if lock else ""),(row["source_id"],)).fetchone()
    if not approved:raise PermissionError("source approval required")
    return row

def candidate(query,item):
    if item.get("target")!="eflaw" or item.get("title")!=query or item.get("exact_match") is not True:return None
    ids=[item.get("external_id"),item.get("master_id")]
    if any(not isinstance(x,str) or not re.fullmatch(r"[1-9][0-9]{0,19}",x) for x in ids):raise ValueError("invalid official identity")
    effective=date.fromisoformat(item["effective_from"]).isoformat()
    result={"query":query,"external_id":ids[0],"master_id":ids[1],"effective_from":effective}
    result["candidate_sha256"]=hashlib.sha256(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    # Link contains no OC or other credential. Actual detail response is checked later by intake.
    result["evidence_url"]="https://www.law.go.kr/DRF/lawService.do?"+urlencode({"target":"eflaw","MST":ids[1],"efYd":effective.replace("-",""),"type":"HTML"})
    return result

def candidates(db,job_id,page=1,lock=False):
    row=plan(db,job_id,lock)
    oc=os.getenv("LAW_GO_OC","").strip()
    if not oc or oc.lower()=="test":raise PermissionError("approved LAW_GO_OC required")
    result=search("eflaw",row["query"],oc,page)
    items=[]
    for item in result["items"]:
        c=candidate(row["query"],item)
        if c and c not in items:items.append(c)
    return {"job_id":job_id,"reference_label":row["reference_label"],"query":row["query"],"page":page,"total":result["total"],"items":items,"confirmed":False}

def confirm(db,job_id,page,digest,user,confirmed):
    if not confirmed:raise ValueError("explicit selection required")
    # Re-fetch the official result after locking this queued job. No user-supplied raw ID is accepted.
    results=candidates(db,job_id,page,True)
    chosen=[x for x in results["items"] if x["candidate_sha256"]==digest]
    if len(chosen)!=1:raise ValueError("candidate changed or not found")
    c=chosen[0]
    row=db.execute("""INSERT INTO legal_wiki.reference_job_mappings(job_id,target,external_id,master_id,requested_effective_on,confirmed_by,evidence_url,confirmed_tenant,lookup_query,lookup_candidate_sha256)
      VALUES(?,'eflaw',?,?,CAST(? AS date),?,?,?,?,?) ON CONFLICT(job_id) DO NOTHING RETURNING job_id""",
      (job_id,c["external_id"],c["master_id"],c["effective_from"],user["id"],c["evidence_url"],user["tenant"],c["query"],digest)).fetchone()
    if not row:raise ValueError("mapping already exists")
    return {"job_id":job_id,"mapped":True,"verified":False}
