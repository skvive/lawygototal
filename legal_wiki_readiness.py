"""Read-only preflight. No credentials, legal text, or private note data in output."""
import json
import os
from pathlib import Path

def credential_flags(env):
    return {
        "law_go_configured":bool(env.get("LAW_GO_OC","").strip()) and env.get("LAW_GO_OC","").strip().lower()!="test",
        "gemini_configured":bool(env.get("GEMINI_API_KEY","").strip()),
        "wiki_enabled":env.get("LAWYGO_LEGAL_WIKI_ENABLED")=="1",
        "e5_enabled":env.get("LAWYGO_E5_ENABLED")=="1",
        "e5_local_model_directory":bool(env.get("LAWYGO_E5_MODEL_DIR")) and Path(env["LAWYGO_E5_MODEL_DIR"]).is_dir()
    }

def inspect(db,env):
    flags=credential_flags(env)
    row=db.execute("""SELECT
      (SELECT count(*) FROM legal_wiki.wiki_topics) AS topics,
      (SELECT count(*) FROM legal_wiki.legal_sources WHERE code='kr-law-go' AND enabled AND verified_at IS NOT NULL AND redistribution_allowed) AS approved_sources,
      (SELECT count(*) FROM legal_wiki.reference_lookup_plan WHERE plan_status='candidate_lookup') AS lookup_candidates,
      (SELECT count(*) FROM legal_wiki.ingestion_jobs WHERE status='queued') AS queued,
      (SELECT count(*) FROM legal_wiki.reference_job_mappings m JOIN legal_wiki.ingestion_jobs j ON j.id=m.job_id WHERE j.status='queued') AS mapped_queued,
      (SELECT count(*) FROM legal_wiki.raw_ingestion_payloads) AS raw_payloads,
      (SELECT count(*) FROM legal_wiki.canonical_imports) AS canonical_imports,
      (SELECT count(*) FROM legal_wiki.precedents WHERE verified_at IS NOT NULL) AS verified_precedents,
      (SELECT count(*) FROM legal_wiki.searchable_precedent_embeddings) AS searchable_vectors,
      (SELECT count(*) FROM public.lawyer_verifications lv JOIN public.users u ON u.id=lv.user_id AND u.tenant=lv.tenant WHERE lv.status='approved' AND lv.checked_at IS NOT NULL AND NULLIF(btrim(lv.checked_by),'') IS NOT NULL AND u.role IN ('admin','editor')) AS qualified_reviewers,
      (SELECT count(*) FROM legal_wiki.qualified_verified_revisions) AS verified_revisions
    """).fetchone()
    counts={k:int(v) for k,v in dict(row).items()}
    blockers=[]
    if not flags["law_go_configured"]:blockers.append("LAW_GO_OC_NOT_CONFIGURED")
    if not counts["approved_sources"]:blockers.append("SOURCE_APPROVAL_REQUIRED")
    if counts["queued"] and not counts["mapped_queued"]:blockers.append("OFFICIAL_ID_MAPPING_REQUIRED")
    if not counts["verified_precedents"]:blockers.append("VERIFIED_PRECEDENTS_REQUIRED")
    if not flags["e5_local_model_directory"]:blockers.append("LOCAL_E5_MODEL_REQUIRED")
    if not counts["searchable_vectors"]:blockers.append("SEARCHABLE_E5_VECTORS_REQUIRED")
    if not counts["qualified_reviewers"]:blockers.append("QUALIFIED_REVIEWER_REQUIRED")
    if not counts["verified_revisions"]:blockers.append("REVIEWED_PUBLICATION_REQUIRED")
    if not flags["gemini_configured"]:blockers.append("GEMINI_API_KEY_NOT_CONFIGURED")
    if not flags["wiki_enabled"]:blockers.append("WIKI_FEATURE_DISABLED")
    if not flags["e5_enabled"]:blockers.append("E5_FEATURE_DISABLED")
    return {"environment":flags,"counts":counts,"blockers":blockers,"preflight_passed":not blockers,"live_provider_authentication_verified":False}

if __name__=="__main__":
    from db_engine import USE_POSTGRES,open_db
    if not USE_POSTGRES:raise SystemExit("PostgreSQL required")
    with open_db() as db:
        print(json.dumps(inspect(db,os.environ),ensure_ascii=False,indent=2))
