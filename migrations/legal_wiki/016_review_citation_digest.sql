BEGIN;
CREATE OR REPLACE FUNCTION legal_wiki.review_digest(p_tenant text,p_revision bigint) RETURNS text LANGUAGE sql STABLE SECURITY INVOKER SET search_path=pg_catalog AS $$
SELECT encode(sha256(convert_to(jsonb_build_array(r.title,r.summary,r.body_markdown,r.legal_as_of,r.version,
 coalesce((SELECT jsonb_agg(jsonb_build_array(c.id,c.proposition_key,c.article_version_id,c.precedent_id,c.pinpoint,c.relation,c.verified_by,c.verified_at,a.body,a.effective_from,a.effective_to,v.content_sha256,v.verified_at,p.content_sha256,p.verified_at) ORDER BY c.id) FROM legal_wiki.citations c LEFT JOIN legal_wiki.article_versions a ON a.id=c.article_version_id LEFT JOIN legal_wiki.statute_versions v ON v.id=a.statute_version_id LEFT JOIN legal_wiki.precedents p ON p.id=c.precedent_id WHERE c.tenant=r.tenant AND c.revision_id=r.id),'[]'::jsonb),
 coalesce((SELECT jsonb_agg(jsonb_build_array(c.id,c.reference_label,c.source_url,c.verification_status,c.verified_at,c.verified_by) ORDER BY c.id) FROM legal_wiki.legal_reference_candidates c WHERE c.tenant=r.tenant AND c.revision_id=r.id),'[]'::jsonb))::text,'UTF8')),'hex') FROM legal_wiki.wiki_revisions r WHERE r.tenant=p_tenant AND r.id=p_revision $$;
CREATE OR REPLACE FUNCTION legal_wiki.approve_and_publish(p_tenant text, p_revision bigint, p_reviewer text, p_expected_digest text, p_notes text)
 RETURNS bigint
 LANGUAGE plpgsql
 SET search_path TO 'pg_catalog'
AS $function$
DECLARE r record; d text;
BEGIN
 IF p_tenant IS DISTINCT FROM nullif(current_setting('app.tenant',true),'') THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='tenant mismatch'; END IF;
 PERFORM 1 FROM public.lawyer_verifications l JOIN public.users u ON u.id=l.user_id AND u.tenant=l.tenant WHERE l.tenant=p_tenant AND l.user_id=p_reviewer AND l.status='approved' AND l.checked_at IS NOT NULL AND nullif(btrim(l.checked_by),'') IS NOT NULL AND u.role IN ('admin','editor') FOR SHARE OF l,u;
 IF NOT FOUND THEN RAISE EXCEPTION USING ERRCODE='42501',MESSAGE='approved lawyer required'; END IF;
 SELECT * INTO r FROM legal_wiki.wiki_revisions WHERE tenant=p_tenant AND id=p_revision FOR UPDATE;
 IF NOT FOUND OR r.author_id=p_reviewer OR r.status NOT IN ('draft','pending','published') THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='revision not eligible'; END IF;
 d:=legal_wiki.review_digest(p_tenant,p_revision);
 IF d IS DISTINCT FROM p_expected_digest THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='revision changed'; END IF;
 IF EXISTS(SELECT 1 FROM legal_wiki.review_queue q WHERE q.tenant=p_tenant AND q.revision_id=p_revision AND q.status='queued' AND q.source_change_key NOT LIKE 'beta-publication:%') THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='unresolved non-beta review'; END IF;
 INSERT INTO legal_wiki.lawyer_reviews(tenant,revision_id,reviewer_id,credential_ref,decision,notes,approval_digest) VALUES(p_tenant,p_revision,p_reviewer,'lawyer-verification:'||p_reviewer,'approve',p_notes,d);
 UPDATE legal_wiki.wiki_revisions SET status='published' WHERE tenant=p_tenant AND id=p_revision;
 UPDATE legal_wiki.review_queue SET status='resolved' WHERE tenant=p_tenant AND revision_id=p_revision AND status='queued' AND source_change_key LIKE 'beta-publication:%';
 IF NOT EXISTS(SELECT 1 FROM legal_wiki.qualified_verified_revisions WHERE tenant=p_tenant AND id=p_revision) THEN RAISE EXCEPTION USING ERRCODE='23514',MESSAGE='verified sources, citations and effective dates required'; END IF;
 RETURN p_revision;
END $function$
;
CREATE OR REPLACE VIEW legal_wiki.qualified_verified_revisions WITH(security_invoker=true,security_barrier=true) AS  SELECT v.id,
    v.tenant,
    v.topic_id,
    v.version,
    v.title,
    v.summary,
    v.body_markdown,
    v.legal_as_of,
    v.published_at
   FROM legal_wiki.verified_revisions v
     JOIN legal_wiki.wiki_revisions r ON r.id = v.id AND r.tenant = v.tenant
     JOIN LATERAL ( SELECT lr_1.id,
            lr_1.tenant,
            lr_1.revision_id,
            lr_1.reviewer_id,
            lr_1.credential_ref,
            lr_1.decision,
            lr_1.notes,
            lr_1.reviewed_at,
            lr_1.approval_digest
           FROM legal_wiki.lawyer_reviews lr_1
          WHERE lr_1.tenant = r.tenant AND lr_1.revision_id = r.id
          ORDER BY lr_1.reviewed_at DESC, lr_1.id DESC
         LIMIT 1) lr ON true
     JOIN lawyer_verifications lv ON lv.tenant = r.tenant AND lv.user_id = lr.reviewer_id
     JOIN users u ON u.id = lv.user_id AND u.tenant = lv.tenant
  WHERE lv.status = 'approved'::text AND lv.checked_at IS NOT NULL AND NULLIF(btrim(lv.checked_by), ''::text) IS NOT NULL AND lr.credential_ref = ('lawyer-verification:'::text || lv.user_id) AND lr.reviewer_id <> r.author_id AND lr.approval_digest = legal_wiki.review_digest(r.tenant,r.id) AND u.role IN ('admin','editor');
COMMIT;
