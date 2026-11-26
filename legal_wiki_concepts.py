"""Local Korean legal-concept retrieval. Explainable query expansion, not neural embeddings."""
import re
import unicodedata
CONCEPTS={
"채무불이행":("채무불이행","계약위반","이행지체","불완전이행","이행불능"),
"손해배상":("손해배상","손해액","일실수익","위자료","배상책임"),
"계약해제":("계약해제","계약해지","해제권","원상회복"),
"대금청구":("대금청구","잔금","중도금","물품대금","공사대금"),
"임대차":("임대차","임차인","임대인","보증금","차임"),
"집행":("강제집행","채권압류","가압류","추심명령","집행권원"),
"근로":("근로자성","근로계약","임금","부당해고","퇴직금"),
"개인정보":("개인정보","정보주체","처리위탁","개인정보유출"),
"입증":("입증책임","증명책임","요건사실","증거능력"),
"시효":("소멸시효","시효중단","시효완성","시효이익"),
"상계":("상계","자동채권","수동채권","상계적상"),
"동시이행":("동시이행","이행제공","반대급부","동시이행항변권"),
}
def compact(s): return re.sub(r"[^0-9a-z가-힣]","",unicodedata.normalize("NFKC",s).lower())
def expand(query):
    q=compact(query)
    if len(q)<2: return []
    result=[query.strip()]
    for terms in CONCEPTS.values():
        if any(compact(t) in q for t in terms):
            result.extend(terms)
    return list(dict.fromkeys(result))[:20]

def rerank(query,rows,limit=20):
    q=compact(query); terms=expand(query)
    scored=[]
    for row in rows:
        text=compact(" ".join(str(row.get(k) or "") for k in ("case_number","holding")))
        hits=[t for t in terms if compact(t) and compact(t) in text]
        score=(10 if q and q in text else 0)+sum(2 if t==query.strip() else 1 for t in hits)
        if score: scored.append({**row,"concept_score":score,"matched_terms":hits})
    return sorted(scored,key=lambda r:(-r["concept_score"],str(r.get("id",""))))[:limit]
