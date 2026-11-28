"""LW-05: explicit-ID official XML intake. Raw payloads are quarantined, not legal citations."""
import argparse
import hashlib
import os
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

BASE = "https://www.law.go.kr/DRF/lawService.do"
MAX_BYTES = 8 * 1024 * 1024

class IntakeError(Exception):
    pass

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise IntakeError("redirect refused")

def params(target, external_id, oc, master_id=None, effective_on=None):
    if target not in {"eflaw", "prec"} or not re.fullmatch(r"[0-9]{1,20}", external_id):
        raise IntakeError("explicit official numeric ID required")
    if not oc or oc.strip().lower() == "test":
        raise IntakeError("approved LAW_GO_OC required")
    result={"OC": oc.strip(), "target": target, "type": "XML"}
    if master_id is not None or effective_on is not None:
        if target!="eflaw" or not isinstance(master_id,str) or not re.fullmatch(r"[0-9]{1,20}",master_id) or int(master_id)<1:
            raise IntakeError("explicit statute master ID required")
        try:
            day=datetime.strptime(str(effective_on),"%Y-%m-%d").strftime("%Y%m%d")
        except ValueError: raise IntakeError("valid effective date required") from None
        return {**result,"MST":master_id,"efYd":day}
    return {**result,"ID":external_id}

def public_detail_url(target,external_id,master_id=None,effective_on=None):
    # Reuse the same identity validation and stable ordering as the intake request.
    p=params(target,external_id,"public-link-only",master_id,effective_on)
    p.pop("OC")
    p["type"]="HTML"
    return BASE+"?"+urllib.parse.urlencode(p)

def validate(raw, target, external_id, effective_on=None):
    if not raw or len(raw) > MAX_BYTES or b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise IntakeError("invalid XML payload")
    try:
        text = raw.decode("utf-8-sig")
        root = ET.fromstring(text)
    except (UnicodeError, ET.ParseError):
        raise IntakeError("invalid UTF-8 XML") from None
    fields = {}
    for e in root.iter():
        k = e.tag.rsplit("}", 1)[-1]
        if e.text and e.text.strip():
            fields.setdefault(k, []).append(e.text.strip())
    key = "법령ID" if target == "eflaw" else "판례정보일련번호"
    required = ("법령명_한글", "시행일자", "조문내용") if target == "eflaw" else ("사건번호", "선고일자", "법원명", "판례내용")
    if not any(x.isdigit() and int(x) == int(external_id) for x in fields.get(key, [])):
        raise IntakeError("official ID mismatch")
    if any(not fields.get(k) for k in required):
        raise IntakeError("required official fields missing")
    date_key = "시행일자" if target == "eflaw" else "선고일자"
    try:
        actual=datetime.strptime(fields[date_key][0], "%Y%m%d").date().isoformat()
    except ValueError:
        raise IntakeError("invalid official date") from None
    if effective_on is not None and (target!="eflaw" or actual!=str(effective_on)):
        raise IntakeError("official effective date mismatch")
    return text, hashlib.sha256(raw).hexdigest()

def collect(target, external_id, oc, master_id=None, effective_on=None):
    query = urllib.parse.urlencode(params(target, external_id, oc,master_id,effective_on))
    request = urllib.request.Request(BASE + "?" + query, headers={"Accept": "application/xml", "User-Agent": "LAWYGO-LegalWiki/1.0"})
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=25) as resp:
            raw = resp.read(MAX_BYTES + 1)
    except Exception:
        raise IntakeError("official API transport failed") from None
    return validate(raw, target, external_id,effective_on)

def run(target, external_id, master_id=None, effective_on=None):
    from db_engine import open_db, USE_POSTGRES
    if not USE_POSTGRES:
        raise IntakeError("PostgreSQL required")
    oc = os.getenv("LAW_GO_OC", "").strip()
    request_params=params(target, external_id, oc,master_id,effective_on)
    with open_db() as db:
        source = db.execute("SELECT id FROM legal_wiki.legal_sources WHERE code='kr-law-go' AND enabled AND verified_at IS NOT NULL AND redistribution_allowed").fetchone()
        if not source:
            raise IntakeError("official source approval required")
        source_id = source["id"]
    text, digest = collect(target, external_id, oc,master_id,effective_on)
    public_url = public_detail_url(target,external_id,master_id,effective_on)
    job_key=target+":"+external_id if master_id is None else target+":"+external_id+":mst:"+master_id+":"+str(effective_on)
    with open_db() as db:
        source = db.execute("SELECT id FROM legal_wiki.legal_sources WHERE id=? AND enabled AND verified_at IS NOT NULL AND redistribution_allowed FOR SHARE", (source_id,)).fetchone()
        if not source:
            raise IntakeError("source approval withdrawn")
        job = db.execute("INSERT INTO legal_wiki.ingestion_jobs(source_id,external_key,status,attempt) VALUES(?,?,'quarantined',1) ON CONFLICT(source_id,external_key) DO UPDATE SET status='quarantined',attempt=legal_wiki.ingestion_jobs.attempt+1 RETURNING id", (source_id, job_key)).fetchone()
        db.execute("INSERT INTO legal_wiki.raw_ingestion_payloads(job_id,target,external_id,content_sha256,source_url,raw_xml,master_id,requested_effective_on) VALUES(?,?,?,?,?,?,?,CAST(? AS date)) ON CONFLICT(job_id,content_sha256) DO NOTHING", (job["id"],target,external_id,digest,public_url,text,master_id,effective_on))
        db.execute("UPDATE legal_wiki.ingestion_jobs SET finished_at=now(),error_message=NULL WHERE id=?", (job["id"],))
    return {"job_id":job["id"],"sha256":digest,"status":"quarantined"}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("target", choices=["eflaw","prec"])
    parser.add_argument("external_id")
    parser.add_argument("--master-id")
    parser.add_argument("--effective-on")
    args = parser.parse_args()
    try:
        print(run(args.target,args.external_id,args.master_id,args.effective_on))
    except IntakeError as exc:
        parser.exit(1, str(exc)+"\n")
