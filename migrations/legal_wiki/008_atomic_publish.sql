BEGIN;
CREATE OR REPLACE FUNCTION legal_wiki.approve_and_publish(p_tenant text,p_revision bigint,p_reviewer text,p_expected_digest text,p_notes text) RETURNS bigint LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $$
DECLARE r record; d text;
BEGIN
 IF p_tenant IS DISTINCT FROM nullif(current_setting('app.tenant',true),'') THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='tenant mismatch'; END IF;
 PERFORM 1 FROM public.lawyer_verifications l JOIN public.users u ON u.id=l.user_id AND u.tenant=l.tenant WHERE l.tenant=p_tenant AND l.user_id=p_reviewer AND l.status='approved' AND l.checked_at IS NOT NULL AND nullif(btrim(l.checked_by),'') IS NOT NULL AND u.role IN ('admin','editor') FOR SHARE OF l,u;
 IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='approved lawyer required'; END IF;
 SELECT * INTO r FROM legal_wiki.wiki_revisions WHERE tenant=p_tenant AND id=p_revision FOR UPDATE;
 IF NOT FOUND OR r.author_id=p_reviewer OR r.status NOT IN ('draft','pending','published') THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='revision not eligible'; END IF;
 d:=encode(sha256(convert_to(jsonb_build_array(r.title,r.summary,r.body_markdown,r.legal_as_of,r.version)::text,'UTF8')),'hex');
 IF d IS DISTINCT FROM p_expected_digest THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='revision changed'; END IF;
 IF EXISTS(SELECT 1 FROM legal_wiki.review_queue q WHERE q.tenant=p_tenant AND q.revision_id=p_revision AND q.status='queued' AND q.source_change_key NOT LIKE 'beta-publication:%') THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='unresolved non-beta review'; END IF;
 INSERT INTO legal_wiki.lawyer_reviews(tenant,revision_id,reviewer_id,credential_ref,decision,notes,approval_digest) VALUES(p_tenant,p_revision,p_reviewer,'lawyer-verification:'||p_reviewer,'approve',p_notes,d);
 UPDATE legal_wiki.wiki_revisions SET status='published' WHERE tenant=p_tenant AND id=p_revision;
 UPDATE legal_wiki.review_queue SET status='resolved' WHERE tenant=p_tenant AND revision_id=p_revision AND status='queued' AND source_change_key LIKE 'beta-publication:%';
 IF NOT EXISTS(SELECT 1 FROM legal_wiki.qualified_verified_revisions WHERE tenant=p_tenant AND id=p_revision) THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='verified sources, citations and effective dates required'; END IF;
 RETURN p_revision;
END $$;
REVOKE EXECUTE ON FUNCTION legal_wiki.approve_and_publish(text,bigint,text,text,text) FROM PUBLIC;
COMMIT;
