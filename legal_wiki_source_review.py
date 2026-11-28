"""Explicit human review of imported official text. No automatic verification."""
import hashlib
import json
from legal_wiki_normalize import assert_staged

def json_value(x):
    return json.loads(x) if isinstance(x,str) else x

def scalar(x):
    return x.isoformat() if hasattr(x,"isoformat") else x

def require_fields(actual,expected,keys):
    for k in keys:
        if scalar(actual[k])!=expected[k]:raise ValueError("canonical content mismatch: "+k)

def packet(db,payload_id,lock=False):
    # Lock provenance and canonical rows before any decision. Source permissions stay independent.
    suffix=" FOR SHARE OF p,n,c,j,s" if lock else ""
    r=db.execute("""SELECT p.target,p.external_id,p.raw_xml,p.content_sha256,p.master_id,p.requested_effective_on,p.source_url,n.normalized_json,n.kind,n.content_sha256 AS normalized_hash,
        c.statute_version_id,c.precedent_id,s.id AS source_id,s.code,s.agency,s.base_url,s.usage_terms,s.verified_at AS source_verified_at
        FROM legal_wiki.canonical_imports c JOIN legal_wiki.normalized_payloads n ON n.payload_id=c.payload_id JOIN legal_wiki.raw_ingestion_payloads p ON p.id=c.payload_id JOIN legal_wiki.ingestion_jobs j ON j.id=p.job_id JOIN legal_wiki.legal_sources s ON s.id=j.source_id
        WHERE c.payload_id=? AND s.code='kr-law-go' AND s.enabled AND s.redistribution_allowed AND s.verified_at IS NOT NULL"""+suffix,(payload_id,)).fetchone()
    if not r:raise LookupError("approved imported source not found")
    data=assert_staged(r,r["normalized_json"])
    if data["kind"]!=r["kind"] or data["content_sha256"]!=r["normalized_hash"]:raise ValueError("normalized metadata mismatch")
    if data["kind"]=="precedent":
        if not r["precedent_id"] or r["statute_version_id"]:raise ValueError("import mapping mismatch")
        row=db.execute("SELECT * FROM legal_wiki.precedents WHERE id=?"+(" FOR UPDATE" if lock else ""),(r["precedent_id"],)).fetchone()
        if not row:raise ValueError("canonical precedent missing")
        require_fields(row,data,("external_id","court","case_number","decided_on","case_type","decision_type","original_text","holding","content_sha256"))
        kind="precedent";cid=r["precedent_id"];articles=[]
    else:
        if not r["statute_version_id"] or r["precedent_id"]:raise ValueError("import mapping mismatch")
        row=db.execute("""SELECT v.*,s.external_id,s.title,s.statute_type,s.source_id FROM legal_wiki.statute_versions v JOIN legal_wiki.statutes s ON s.id=v.statute_id WHERE v.id=?"""+(" FOR UPDATE OF v FOR SHARE OF s" if lock else ""),(r["statute_version_id"],)).fetchone()
        if not row:raise ValueError("canonical statute missing")
        require_fields(row,data,("external_id","title","statute_type","external_version_id","promulgated_on","effective_from","content_sha256"))
        articles=db.execute("SELECT * FROM legal_wiki.article_versions WHERE statute_version_id=? ORDER BY article_key"+(" FOR SHARE" if lock else ""),(r["statute_version_id"],)).fetchall()
        expected={x["article_key"]:x for x in data["articles"]}
        if len(articles)!=len(expected):raise ValueError("article count mismatch")
        for a in articles:
            if a["article_key"] not in expected:raise ValueError("unknown article")
            require_fields(a,expected[a["article_key"]],("article_key","heading","body","effective_from"))
            if a["source_url"]!=r["source_url"] or json_value(a["transitional_note"])!=data["transitional_notes"]:raise ValueError("article provenance mismatch")
            if a["effective_to"] is not None and a["effective_to"]<=a["effective_from"]:raise ValueError("invalid article end date")
        kind="statute";cid=r["statute_version_id"]
    if row["source_id"]!=r["source_id"] or row["source_url"]!=r["source_url"]:raise ValueError("canonical source mismatch")
    # Include the currently stored legal date limits, even when they were added by a separate chronology review.
    snapshot={"payload_id":payload_id,"canonical_id":cid,"kind":kind,"data":data,"source_url":r["source_url"],"source":{k:scalar(r[k]) for k in ("source_id","code","agency","base_url","usage_terms","source_verified_at")},"canonical_effective_to":scalar(row.get("effective_to")),"article_limits":[[a["article_key"],scalar(a["effective_to"])] for a in articles]}
    digest=hashlib.sha256(json.dumps(snapshot,ensure_ascii=False,sort_keys=True,separators=(",",":")).encode()).hexdigest()
    return {**snapshot,"digest":digest,"verified":row["verified_at"] is not None,"notice":"원문 대조 검수입니다. 특정 사건 적용 여부·개정 이력·효력 종료는 별도 검토가 필요합니다."}

def approve(db,payload_id,user,expected_digest,notes,confirmed):
    if not confirmed or len(notes.strip())<10:raise ValueError("explicit human source review required")
    p=packet(db,payload_id,True)
    if p["digest"]!=expected_digest:raise ValueError("source snapshot changed")
    if p["verified"]:raise ValueError("source already verified")
    db.execute("""INSERT INTO legal_wiki.source_text_reviews(payload_id,tenant,reviewer_id,snapshot_sha256,notes) VALUES(?,?,?,?,?)""",(payload_id,user["tenant"],user["id"],expected_digest,notes.strip()))
    table="precedents" if p["kind"]=="precedent" else "statute_versions"
    updated=db.execute("UPDATE legal_wiki."+table+" SET verified_at=now() WHERE id=? AND verified_at IS NULL RETURNING id",(p["canonical_id"],)).fetchone()
    if not updated:raise ValueError("source verification state changed")
    return {"payload_id":payload_id,"canonical_id":p["canonical_id"],"kind":p["kind"],"verified":True}
