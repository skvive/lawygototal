-- Isolated dev-only transactional constraint probe. All fixture rows rolled back.
DO $probe$
DECLARE src bigint; job bigint;
BEGIN
 BEGIN
  SELECT id INTO src FROM legal_wiki.legal_sources WHERE code='kr-law-go';
  INSERT INTO legal_wiki.ingestion_jobs(source_id,external_key,status) VALUES(src,'fixture-effective-date-20261127','queued') RETURNING id INTO job;
  BEGIN
   INSERT INTO legal_wiki.reference_job_mappings(job_id,target,external_id,confirmed_by,evidence_url,master_id) VALUES(job,'eflaw','12','fixture-only','https://www.law.go.kr/fixture','123');
   RAISE EXCEPTION 'missing effective date accepted';
  EXCEPTION WHEN check_violation THEN NULL; END;
  BEGIN
   INSERT INTO legal_wiki.reference_job_mappings(job_id,target,external_id,confirmed_by,evidence_url,master_id,requested_effective_on) VALUES(job,'prec','12','fixture-only','https://www.law.go.kr/fixture','123','2020-01-01');
   RAISE EXCEPTION 'precedent accepted statute version';
  EXCEPTION WHEN check_violation THEN NULL; END;
  INSERT INTO legal_wiki.reference_job_mappings(job_id,target,external_id,confirmed_by,evidence_url,master_id,requested_effective_on) VALUES(job,'eflaw','12','fixture-only','https://www.law.go.kr/fixture','123','2020-01-01');
  IF NOT EXISTS(SELECT 1 FROM legal_wiki.reference_job_mappings WHERE job_id=job AND master_id='123' AND requested_effective_on='2020-01-01') THEN RAISE EXCEPTION 'valid historical pair missing'; END IF;
  RAISE EXCEPTION USING ERRCODE='ZX001',MESSAGE='rollback successful fixture';
 EXCEPTION WHEN SQLSTATE 'ZX001' THEN NULL; END;
END $probe$;
