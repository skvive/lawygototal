"""LW-07/08 pilot routes: separate beta and verified corpus; no private NOTE content leaves server."""
import os
from fastapi import Depends, HTTPException, Query
from db_engine import USE_POSTGRES

def register(app, database, current_user):
    def guard(user, db):
        if not USE_POSTGRES or os.getenv("LAWYGO_LEGAL_WIKI_ENABLED") != "1":
            raise HTTPException(503, "전문 법률위키 준비 중")
        # Until professional-verification integration is tested, only staff may preview.
        if user["role"] not in ("admin", "editor"):
            raise HTTPException(403, "내부 검수 전용")
        if not db.execute("SELECT to_regclass('legal_wiki.verified_revisions') IS NOT NULL AS ready").fetchone()["ready"]:
            raise HTTPException(503, "법률 DB 준비 중")
        db.execute("SELECT set_config('app.tenant',?,true)", (user["tenant"],))
    def verified(db, tenant, q, limit):
        return [dict(r) for r in db.execute("""SELECT id,title,summary,legal_as_of
          FROM legal_wiki.verified_revisions WHERE tenant=? AND
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
    @app.get("/api/wiki/v2/note/{note_id}/evidence")
    def note_evidence(note_id:str,q:str=Query(min_length=2,max_length=100),user=Depends(current_user),db=Depends(database)):
        guard(user,db)
        own=db.execute("SELECT id FROM posts WHERE id=? AND tenant=? AND author_id=? AND product='note' AND deleted_at IS NULL",(note_id,user["tenant"],user["id"])).fetchone()
        if not own: raise HTTPException(404,"본인의 노트를 찾을 수 없습니다")
        # Only the explicit search query is used; never read or forward NOTE body.
        items=verified(db,user["tenant"],q.strip(),10) if len(q.strip())>=2 else []
        return {"items":items,"ai_generated":False,"notice":"검증 자료 검색 결과; AI 법률 의견 아님"}
