-- Development-only synthetic transaction; no actual identity is confirmed.
DO $probe$
DECLARE src bigint; j bigint;
BEGIN
 BEGIN
  SELECT id INTO src FROM legal_wiki.legal_sources WHERE code='kr-law-go';
  INSERT INTO legal_wiki.ingestion_jobs(source_id,external_key,status) VALUES(src,'fixture-reference-audit','queued') RETURNING id INTO j;
  BEGIN
   INSERT INTO legal_wiki.reference_job_mappings(job_id,target,external_id,master_id,requested_effective_on,confirmed_by,evidence_url,confirmed_tenant)
    VALUES(j,'eflaw','1','2','2020-01-01','TEST','https://www.law.go.kr/test','fixture');
   RAISE EXCEPTION 'partial audit accepted';
  EXCEPTION WHEN check_violation THEN NULL; END;
  INSERT INTO legal_wiki.reference_job_mappings(job_id,target,external_id,master_id,requested_effective_on,confirmed_by,evidence_url,confirmed_tenant,lookup_query,lookup_candidate_sha256)
   VALUES(j,'eflaw','1','2','2020-01-01','TEST','https://www.law.go.kr/test','fixture','TEST',repeat('a',64));
  IF NOT EXISTS(SELECT 1 FROM legal_wiki.reference_job_mappings WHERE job_id=j AND lookup_candidate_sha256=repeat('a',64) AND confirmed_tenant='fixture') THEN RAISE EXCEPTION 'audit missing'; END IF;
  RAISE EXCEPTION USING ERRCODE='ZX001',MESSAGE='rollback synthetic mapping';
 EXCEPTION WHEN SQLSTATE 'ZX001' THEN NULL; END;
END $probe$;
