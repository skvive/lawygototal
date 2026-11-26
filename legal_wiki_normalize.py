"""Strict normalization of quarantined official XML; never grants verified status."""
import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import datetime

def local(tag): return tag.rsplit("}",1)[-1]
def value(node,key,required=True):
    matches=[(e.text or "").strip() for e in node.iter() if local(e.tag)==key and (e.text or "").strip()]
    if not matches and required: raise ValueError("missing "+key)
    return matches[0] if matches else None
def date(s): return datetime.strptime(s,"%Y%m%d").date().isoformat()
def number(s):
    if not re.fullmatch(r"[0-9]{1,20}",s): raise ValueError("invalid ID")
    return str(int(s))
def normalize(raw,target,external_id,master_id=None):
    if not isinstance(raw,bytes) or not raw or len(raw)>8*1024*1024 or b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper(): raise ValueError("invalid XML")
    root=ET.fromstring(raw.decode("utf-8-sig"))
    digest=hashlib.sha256(raw).hexdigest()
    if target=="prec":
        if number(value(root,"판례정보일련번호"))!=number(external_id): raise ValueError("ID mismatch")
        return {"kind":"precedent","external_id":number(external_id),"court":value(root,"법원명"),"case_number":value(root,"사건번호"),"decided_on":date(value(root,"선고일자")),"case_type":value(root,"사건종류명",False),"decision_type":value(root,"판결유형",False),"holding":value(root,"판결요지",False),"original_text":value(root,"판례내용"),"content_sha256":digest,"verified":False}
    if target!="eflaw": raise ValueError("unsupported target")
    info=next((e for e in root.iter() if local(e.tag)=="기본정보"),None)
    if info is None: raise ValueError("missing statute metadata")
    if number(value(info,"법령ID"))!=number(external_id): raise ValueError("ID mismatch")
    effective=date(value(info,"시행일자")); promulgated=date(value(info,"공포일자"))
    # Explicit MST is required for historical identity. Current-ID responses remain digest-keyed.
    version="mst:"+number(master_id) if master_id else "sha256:"+digest
    articles=[]; seen=set()
    for unit in root.iter():
        if local(unit.tag)!="조문단위" or value(unit,"조문여부",False)!="조문": continue
        n=number(value(unit,"조문번호")); sub=number(value(unit,"조문가지번호",False) or "0")
        key=n+("-"+sub if sub!="0" else "")
        if key in seen: raise ValueError("duplicate article")
        seen.add(key)
        parts=[(e.text or "").strip() for e in unit.iter() if local(e.tag) in {"조문내용","항내용","호내용","목내용"} and (e.text or "").strip()]
        if not parts: raise ValueError("empty article")
        articles.append({"article_key":key,"heading":value(unit,"조문제목",False),"body":"\n".join(parts),"effective_from":date(value(unit,"조문시행일자",False)) if value(unit,"조문시행일자",False) else effective,"effective_to":None})
    if not articles: raise ValueError("no articles")
    transitional=[(e.text or "").strip() for e in root.iter() if local(e.tag)=="부칙내용" and (e.text or "").strip()]
    return {"kind":"statute","external_id":number(external_id),"external_version_id":version,"title":value(info,"법령명_한글"),"statute_type":value(info,"법종구분"),"promulgated_on":promulgated,"effective_from":effective,"effective_to":None,"articles":articles,"transitional_notes":transitional,"content_sha256":digest,"verified":False}

def stage(payload_id):
    import json
    from db_engine import open_db,USE_POSTGRES
    if not USE_POSTGRES: raise RuntimeError("PostgreSQL required")
    with open_db() as db:
        row=db.execute("SELECT id,target,external_id,raw_xml,content_sha256 FROM legal_wiki.raw_ingestion_payloads WHERE id=?",(payload_id,)).fetchone()
        if not row: raise ValueError("payload not found")
        # Intake hashes bytes including possible BOM; preserve byte-level check on decoded text too.
        raw=row["raw_xml"].encode("utf-8")
        if hashlib.sha256(raw).hexdigest()!=row["content_sha256"]:
            if hashlib.sha256(b"\xef\xbb\xbf"+raw).hexdigest()!=row["content_sha256"]: raise ValueError("raw hash mismatch")
            raw=b"\xef\xbb\xbf"+raw
        data=normalize(raw,row["target"],row["external_id"])
        db.execute("INSERT INTO legal_wiki.normalized_payloads(payload_id,kind,normalized_json,content_sha256) VALUES(?,?,CAST(? AS jsonb),?) ON CONFLICT(payload_id) DO NOTHING",(payload_id,data["kind"],json.dumps(data,ensure_ascii=False),data["content_sha256"]))
        return {"payload_id":payload_id,"kind":data["kind"],"verified":False}
