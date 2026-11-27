"""Bounded NOTE analysis source bundle and strict provider output validation."""
import json

def pack_sources(sources,max_chars=30000):
    """Include a manifest only for nonempty source text actually included."""
    chunks=[];refs=[];seen=set();remaining=max_chars
    for ref,raw in sources:
        sid=ref.get("id")
        if not isinstance(sid,str) or not sid or sid in seen: raise ValueError("invalid source identity")
        seen.add(sid)
        text=(raw or "").strip()
        if not text: continue
        prefix="\n\n[SOURCE "+sid+"]\n"
        if remaining<=len(prefix)+15: break
        excerpt=text[:remaining-len(prefix)]
        if not excerpt: continue
        chunks.append(prefix+excerpt);remaining-=len(prefix)+len(excerpt)
        refs.append({**{k:v for k,v in ref.items() if k!="pre_truncated"},"included_chars":len(excerpt),"truncated":bool(ref.get("pre_truncated")) or len(excerpt)<len(text)})
    return "".join(chunks),refs

def validate_result(obj,refs):
    if not isinstance(obj,dict) or not isinstance(obj.get("summary"),str) or not obj["summary"].strip(): raise ValueError("missing summary")
    allowed={r["id"] for r in refs}
    issues=obj.get("issues")
    if not isinstance(issues,list): raise ValueError("missing issues")
    for item in issues:
        if not isinstance(item,dict) or not isinstance(item.get("issue"),str) or not item["issue"].strip(): raise ValueError("invalid issue")
        ids=item.get("source_ids")
        if not isinstance(ids,list) or not ids or not all(isinstance(i,str) and i in allowed for i in ids): raise ValueError("issue lacks source evidence")
    for field in ("evidence_gaps","questions"):
        if not isinstance(obj.get(field),list) or not all(isinstance(v,str) for v in obj[field]): raise ValueError("invalid result field")
    return {"summary":obj["summary"],"issues":issues,"evidence_gaps":obj["evidence_gaps"],"questions":obj["questions"],"disclaimer":"AI 분석 보조 자료 · 변호사 검토 및 공식 원문 확인 필요"}
