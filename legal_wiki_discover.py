"""Official law/precedent discovery: return candidates, never approve inferred IDs."""
import os
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from legal_wiki_ingest import NoRedirect, IntakeError, MAX_BYTES
from legal_wiki_normalize import date,number,local
BASE="https://www.law.go.kr/DRF/lawSearch.do"
def parse(raw,target,query):
    if not raw or len(raw)>MAX_BYTES or b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper():
        raise IntakeError("invalid list XML")
    try: root=ET.fromstring(raw.decode("utf-8-sig"))
    except (UnicodeError,ET.ParseError): raise IntakeError("invalid list XML") from None
    if target not in ("eflaw","prec"): raise IntakeError("unsupported list target")
    def get(node,key):
        return next(((c.text or "").strip() for c in node if local(c.tag)==key),"")
    if get(root,"target")!=target or not get(root,"totalCnt").isdigit(): raise IntakeError("unexpected API list response")
    out=[]
    for row in root:
        if local(row.tag)!=("law" if target=="eflaw" else "prec"): continue
        try:
            if target=="eflaw":
                title=get(row,"법령명한글")
                item={"target":target,"external_id":number(get(row,"법령ID")),"master_id":number(get(row,"법령일련번호")),"title":title,"effective_from":date(get(row,"시행일자")),"exact_match":title==query}
            else:
                case=get(row,"사건번호")
                item={"target":target,"external_id":number(get(row,"판례일련번호")),"case_number":case,"title":get(row,"사건명"),"decided_on":date(get(row,"선고일자")),"exact_match":case==query}
        except (ValueError,TypeError): raise IntakeError("malformed list item") from None
        item["confirmed"]=False
        out.append(item)
    return {"total":int(get(root,"totalCnt")),"items":out,"confirmed":False}
def search(target,query,oc,page=1):
    q=query.strip()
    if not 2<=len(q)<=150 or target not in ("eflaw","prec") or not 1<=page<=100: raise IntakeError("invalid query")
    if not oc or oc.strip()=="test": raise IntakeError("approved LAW_GO_OC required")
    params={"OC":oc,"target":target,"type":"XML","query":q,"display":50,"page":page}
    if target=="eflaw": params["nw"]="3"
    # Case-number parameter is reserved for explicit case identifiers.
    if target=="prec" and re.fullmatch(r"[0-9]{4}[가-힣]{1,4}[0-9]+",q):
        params.pop("query");params["nb"]=q
    req=urllib.request.Request(BASE+"?"+urllib.parse.urlencode(params),headers={"Accept":"application/xml","User-Agent":"LAWYGO-LegalWiki/1.0"})
    try:
        with urllib.request.build_opener(NoRedirect()).open(req,timeout=25) as res: raw=res.read(MAX_BYTES+1)
    except Exception: raise IntakeError("official list request failed") from None
    return parse(raw,target,q)
if __name__=="__main__":
    import argparse,json
    p=argparse.ArgumentParser();p.add_argument("target",choices=["eflaw","prec"]);p.add_argument("query");p.add_argument("--page",type=int,default=1);a=p.parse_args()
    from db_engine import open_db,USE_POSTGRES
    if not USE_POSTGRES: raise SystemExit("PostgreSQL required")
    with open_db() as db:
        if not db.execute("SELECT id FROM legal_wiki.legal_sources WHERE code='kr-law-go' AND enabled AND verified_at IS NOT NULL AND redistribution_allowed").fetchone(): raise SystemExit("source approval required")
    print(json.dumps(search(a.target,a.query,os.getenv("LAW_GO_OC","").strip(),a.page),ensure_ascii=False))
