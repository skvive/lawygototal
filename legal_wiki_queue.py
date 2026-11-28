"""Bounded queue execution: confirmed official IDs only, never infer a reference ID."""
import os
import uuid
from legal_wiki_ingest import run,IntakeError
from legal_wiki_normalize import stage,import_checked
def batch(limit=10):
    from db_engine import open_db,USE_POSTGRES
    if not USE_POSTGRES: raise IntakeError("PostgreSQL required")
    if not os.getenv("LAW_GO_OC","").strip() or os.getenv("LAW_GO_OC","").strip().lower()=="test": raise IntakeError("approved LAW_GO_OC required")
    with open_db() as db:
        source=db.execute("SELECT id FROM legal_wiki.legal_sources WHERE code='kr-law-go' AND enabled AND verified_at IS NOT NULL AND redistribution_allowed").fetchone()
        if not source: raise IntakeError("source approval required")
        rows=db.execute("""SELECT j.id,m.target,m.external_id,m.master_id,m.requested_effective_on FROM legal_wiki.ingestion_jobs j JOIN legal_wiki.reference_job_mappings m ON m.job_id=j.id
        WHERE j.source_id=? AND j.status='queued' AND j.attempt<5 ORDER BY j.id LIMIT ?""",(source["id"],max(1,min(50,int(limit))))).fetchall()
    results=[]
    collected={}
    for r in rows:
        token=uuid.uuid4().hex
        with open_db() as db:
            claim=db.execute("UPDATE legal_wiki.ingestion_jobs SET status='running',attempt=attempt+1,claim_token=?,claimed_at=now(),finished_at=NULL WHERE id=? AND status='queued' AND attempt<5 RETURNING id",(token,r["id"])).fetchone()
        if not claim: continue
        try:
            key=(r["target"],r["external_id"],r.get("master_id"),str(r["requested_effective_on"]) if r.get("requested_effective_on") else None)
            if key not in collected:
                result=run(*key) if key[2] is not None else run(*key[:2])
                with open_db() as db:
                    p=db.execute("SELECT id FROM legal_wiki.raw_ingestion_payloads WHERE job_id=? AND content_sha256=?",(result["job_id"],result["sha256"])).fetchone()
                if not p: raise IntakeError("raw payload missing")
                stage(p["id"])
                with open_db() as db:
                    import_checked(db,p["id"])
                collected[key]=p["id"]
            payload_id=collected[key]
            with open_db() as db:
                owned=db.execute("SELECT id FROM legal_wiki.ingestion_jobs WHERE id=? AND status='running' AND claim_token=? FOR UPDATE",(r["id"],token)).fetchone()
                if not owned:raise IntakeError("worker claim expired")
                mapping=db.execute("SELECT target,external_id,master_id,requested_effective_on FROM legal_wiki.reference_job_mappings WHERE job_id=? FOR SHARE",(r["id"],)).fetchone()
                if not mapping or (mapping["target"],mapping["external_id"],mapping.get("master_id"),str(mapping["requested_effective_on"]) if mapping.get("requested_effective_on") else None)!=key:
                    raise IntakeError("confirmed mapping changed")
                source=db.execute("SELECT id FROM legal_wiki.legal_sources WHERE id=? AND enabled AND verified_at IS NOT NULL AND redistribution_allowed FOR SHARE",(source["id"],)).fetchone()
                if not source: raise IntakeError("source approval withdrawn")
                db.execute("INSERT INTO legal_wiki.reference_job_results(job_id,payload_id) VALUES(?,?) ON CONFLICT(job_id) DO UPDATE SET payload_id=excluded.payload_id,collected_at=now()",(r["id"],payload_id))
                db.execute("UPDATE legal_wiki.ingestion_jobs SET status='success',finished_at=now(),error_message=NULL,claim_token=NULL,claimed_at=NULL WHERE id=? AND claim_token=?",(r["id"],token))
            results.append({"id":r["id"],"status":"success","verified":False})
        except Exception:
            with open_db() as db:
                failed=db.execute("UPDATE legal_wiki.ingestion_jobs SET status='failed',finished_at=now(),error_message='intake or normalization failed; inspect approved source',claim_token=NULL,claimed_at=NULL WHERE id=? AND status='running' AND claim_token=? RETURNING id",(r["id"],token)).fetchone()
            results.append({"id":r["id"],"status":"failed" if failed else "claim_lost"})
            break
    return results
def requeue(job_id,confirm=False):
    """Operator-selected retry only. A stale worker can no longer commit a result."""
    from db_engine import open_db,USE_POSTGRES
    if not USE_POSTGRES or not confirm or int(job_id)<1:raise IntakeError("explicit operator retry required")
    with open_db() as db:
        row=db.execute("""UPDATE legal_wiki.ingestion_jobs j
            SET status='queued',claim_token=NULL,claimed_at=NULL,finished_at=NULL,error_message=NULL
            FROM legal_wiki.legal_sources s
            WHERE j.id=? AND j.source_id=s.id AND s.code='kr-law-go' AND s.enabled AND s.redistribution_allowed AND s.verified_at IS NOT NULL
              AND j.attempt<5 AND EXISTS(SELECT 1 FROM legal_wiki.reference_job_mappings m WHERE m.job_id=j.id)
              AND NOT EXISTS(SELECT 1 FROM legal_wiki.reference_job_results r WHERE r.job_id=j.id)
              AND (j.status='failed' OR (j.status='running' AND j.claim_token IS NOT NULL AND j.claimed_at<now()-interval '1 hour'))
            RETURNING j.id""",(int(job_id),)).fetchone()
        return {"job_id":int(job_id),"requeued":bool(row)}

if __name__=="__main__":
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument("--limit",type=int,default=10);p.add_argument("--requeue",type=int);p.add_argument("--confirm-retry",action="store_true");a=p.parse_args()
    print(json.dumps(requeue(a.requeue,a.confirm_retry) if a.requeue is not None else batch(a.limit)))
