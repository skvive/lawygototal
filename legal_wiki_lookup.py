"""Official law-name candidate lookup. Exact names only; candidates require human confirmation."""
import os,re,unicodedata,urllib.parse,urllib.request,xml.etree.ElementTree as ET
from legal_wiki_ingest import IntakeError,NoRedirect,MAX_BYTES
BASE="https://www.law.go.kr/DRF/lawSearch.do"
def norm(s): return " ".join(unicodedata.normalize("NFKC",s).split())
def parse(raw,title):
    if not raw or len(raw)>MAX_BYTES or b"<!DOCTYPE" in raw.upper() or b"<!ENTITY" in raw.upper(): raise IntakeError("unsafe response")
    try: root=ET.fromstring(raw.decode("utf-8-sig"))
    except (UnicodeError,ET.ParseError): raise IntakeError("invalid official response") from None
    found=[]
    for node in root.iter():
        if node.tag.rsplit("}",1)[-1]!="law":continue
        fields={e.tag.rsplit("}",1)[-1]:(e.text or "").strip() for e in node}
        name=fields.get("법령명한글") or fields.get("법령명_한글") or ""
        if norm(name)!=norm(title):continue
        identifier=fields.get("법령ID","");mst=fields.get("법령일련번호","")
        date=fields.get("시행일자","")
        if not re.fullmatch(r"[0-9]{1,20}",identifier) or not re.fullmatch(r"[0-9]{1,20}",mst) or not re.fullmatch(r"[0-9]{8}",date):continue
        from datetime import datetime
        try: datetime.strptime(date,"%Y%m%d")
        except ValueError:continue
        found.append({"title":name,"target":"eflaw","external_id":str(int(identifier)),"mst":mst,"effective_date":date,"evidence_url":"https://www.law.go.kr/법령/"+urllib.parse.quote(name,safe=""),"confirmed":False})
    return found
def lookup(title,oc):
    if not oc or oc.strip().lower()=="test":raise IntakeError("approved LAW_GO_OC required")
    if not 2<=len(title.strip())<=100:raise IntakeError("exact law title required")
    query=urllib.parse.urlencode({"OC":oc,"target":"eflaw","type":"XML","search":"1","query":title,"display":"100"})
    req=urllib.request.Request(BASE+"?"+query,headers={"Accept":"application/xml","User-Agent":"LAWYGO-LegalWiki/1.0"})
    try:
        with urllib.request.build_opener(NoRedirect()).open(req,timeout=25) as r:raw=r.read(MAX_BYTES+1)
    except Exception:raise IntakeError("official lookup failed") from None
    return parse(raw,title)
if __name__=="__main__":
    import argparse,json
    from db_engine import open_db,USE_POSTGRES
    p=argparse.ArgumentParser();p.add_argument("title");a=p.parse_args()
    if not USE_POSTGRES:raise SystemExit("PostgreSQL required")
    with open_db() as db:
        s=db.execute("SELECT id FROM legal_wiki.legal_sources WHERE code='kr-law-go' AND enabled AND verified_at IS NOT NULL AND redistribution_allowed").fetchone()
    if not s:raise SystemExit("source approval required")
    print(json.dumps(lookup(a.title,os.getenv("LAW_GO_OC","").strip()),ensure_ascii=False))
