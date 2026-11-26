"""LW-07/08 pilot routes: separate beta and verified corpus; no private NOTE content leaves server."""
import os
from fastapi import Depends, HTTPException, Query
from db_engine import USE_POSTGRES
from legal_wiki_concepts import expand, rerank

def register(app, database, current_user, csrf):
    def guard(user, db):
        if not USE_POSTGRES or os.getenv("LAWYGO_LEGAL_WIKI_ENABLED") != "1":
            raise HTTPException(503, "전문 법률위키 준비 중")
        # Until professional-verification integration is tested, only staff may preview.
        if user["role"] not in ("admin", "editor"):
            raise HTTPException(403, "내부 검수 전용")
        if not db.execute("SELECT to_regclass('legal_wiki.qualified_verified_revisions') IS NOT NULL AS ready").fetchone()["ready"]:
            raise HTTPException(503, "법률 DB 준비 중")
        db.execute("SELECT set_config('app.tenant',?,true)", (user["tenant"],))
    def verified(db, tenant, q, limit):
        return [dict(r) for r in db.execute("""SELECT id,title,summary,legal_as_of
          FROM legal_wiki.qualified_verified_revisions WHERE tenant=? AND
          (strpos(lower(title),lower(?))>0 OR strpos(lower(summary),lower(?))>0)
          ORDER BY CASE WHEN lower(title)=lower(?) THEN 0 ELSE 1 END,id LIMIT ?""",
          (tenant,q,q,q,limit)).fetchall()]
    @app.get("/api/wiki/v2/search")
    def search(q: str=Query(min_length=2,max_length=100), limit: int=Query(20,ge=1,le=50), beta: bool=False, user=Depends(current_user), db=Depends(database)):
        guard(user,db)
        q=q.strip()
        if len(q)<2: raise HTTPException(400,"검색어 2자 이상")
        rows=[dict(r) for r in db.execute("SELECT * FROM legal_wiki.search_beta_topics(?,?,?)",(user["tenant"],q,limit)).fetchall()] if beta else verified(db,user["tenant"],q,limit)
        return {"items":rows,"verified":not beta,"notice":"미검수 베타 자료" if beta else "원문과 적용일을 재확인하세요"}
    @app.get("/api/wiki/v2/precedents")
    def precedents(q: str=Query(min_length=2,max_length=100), limit: int=Query(20,ge=1,le=50), user=Depends(current_user), db=Depends(database)):
        guard(user,db)
        q=q.strip()
        if len(q)<2: raise HTTPException(400,"검색어 2자 이상")
        rows=db.execute("""SELECT p.id,p.court,p.case_number,p.decided_on,p.holding,p.source_url,
          ts_rank(to_tsvector('simple',coalesce(p.holding,'')||' '||p.case_number),plainto_tsquery('simple',?)) AS score
          FROM legal_wiki.precedents p JOIN legal_wiki.legal_sources s ON s.id=p.source_id
          WHERE p.verified_at IS NOT NULL AND s.verified_at IS NOT NULL AND s.enabled AND s.redistribution_allowed
          AND (strpos(lower(p.case_number),lower(?))>0 OR strpos(lower(coalesce(p.holding,'')),lower(?))>0
          OR to_tsvector('simple',coalesce(p.holding,'')||' '||p.case_number) @@ plainto_tsquery('simple',?))
          ORDER BY score DESC,p.decided_on DESC,p.id LIMIT ?""",(q,q,q,q,limit)).fetchall()
        return {"items":[dict(r) for r in rows],"method":"keyword-ranked; not semantic similarity"}
    @app.get("/api/wiki/v2/precedents/concepts")
    def concept_precedents(q:str=Query(min_length=2,max_length=100),limit:int=Query(20,ge=1,le=50),user=Depends(current_user),db=Depends(database)):
        guard(user,db)
        terms=expand(q)
        if not terms: raise HTTPException(400,"검색어를 확인하세요")
        predicates=" OR ".join(["strpos(lower(coalesce(p.holding,'')||' '||p.case_number),lower(?))>0"]*len(terms))
        rows=db.execute("""SELECT p.id,p.court,p.case_number,p.decided_on,p.holding,p.source_url FROM legal_wiki.precedents p
            JOIN legal_wiki.legal_sources s ON s.id=p.source_id
            WHERE p.verified_at IS NOT NULL AND s.verified_at IS NOT NULL AND s.enabled AND s.redistribution_allowed
            AND ("""+predicates+") ORDER BY p.decided_on DESC,p.id LIMIT 500",tuple(terms)).fetchall()
        return {"items":rerank(q,[dict(r) for r in rows],limit),"method":"local legal concept expansion; not neural embedding","candidate_cap":500}
    @app.get("/api/wiki/v2/note/{note_id}/evidence")
    def note_evidence(note_id:str,q:str=Query(min_length=2,max_length=100),user=Depends(current_user),db=Depends(database)):
        guard(user,db)
        own=db.execute("SELECT id FROM posts WHERE id=? AND tenant=? AND author_id=? AND product='note' AND deleted_at IS NULL",(note_id,user["tenant"],user["id"])).fetchone()
        if not own: raise HTTPException(404,"본인의 노트를 찾을 수 없습니다")
        # Only the explicit search query is used; never read or forward NOTE body.
        items=verified(db,user["tenant"],q.strip(),10) if len(q.strip())>=2 else []
        return {"items":items,"ai_generated":False,"notice":"검증 자료 검색 결과; AI 법률 의견 아님"}

    @app.post("/api/wiki/v2/revisions/{revision_id}/review")
    def review(revision_id:int, decision:str=Query(pattern="^(approve|reject|revise)$"), notes:str=Query("",max_length=1000), user=Depends(csrf), db=Depends(database)):
        guard(user,db)
        lawyer=db.execute("SELECT user_id FROM lawyer_verifications WHERE tenant=? AND user_id=? AND status='approved' AND checked_at IS NOT NULL AND NULLIF(btrim(checked_by),'') IS NOT NULL FOR SHARE",(user["tenant"],user["id"])).fetchone()
        if not lawyer: raise HTTPException(403,"검증된 변호사만 검수할 수 있습니다")
        row=db.execute("""SELECT id,author_id,status,encode(sha256(convert_to(jsonb_build_array(title,summary,body_markdown,legal_as_of,version)::text,'UTF8')),'hex') AS digest
            FROM legal_wiki.wiki_revisions WHERE tenant=? AND id=? FOR UPDATE""",(user["tenant"],revision_id)).fetchone()
        if not row: raise HTTPException(404,"문서 없음")
        if row["author_id"]==user["id"]: raise HTTPException(403,"자기 작성 문서는 검수할 수 없습니다")
        if decision=="approve":
            # Keep the beta queue unresolved until the source/citation verification workflow is integrated.
            raise HTTPException(409,"공식 원문 및 인용 검증 완료 전 승인할 수 없습니다")
        db.execute("INSERT INTO legal_wiki.lawyer_reviews(tenant,revision_id,reviewer_id,credential_ref,decision,notes,approval_digest) VALUES(?,?,?,?,?,?,?)",(user["tenant"],revision_id,user["id"],"lawyer-verification:"+user["id"],decision,notes,row["digest"]))
        return {"revision_id":revision_id,"decision":decision,"published":False}
