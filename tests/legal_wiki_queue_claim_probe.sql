-- Development-only transactional synthetic claim probe.
DO $probe$
DECLARE src bigint; j bigint; token text; p bigint;
BEGIN
 BEGIN
  SELECT id INTO src FROM legal_wiki.legal_sources WHERE code='kr-law-go';
  INSERT INTO legal_wiki.ingestion_jobs(source_id,external_key,status) VALUES(src,'fixture-queue-claim','queued') RETURNING id INTO j;
  BEGIN
   UPDATE legal_wiki.ingestion_jobs SET claim_token='invalid' WHERE id=j;
   RAISE EXCEPTION 'partial claim accepted';
  EXCEPTION WHEN check_violation THEN NULL; END;
  UPDATE legal_wiki.ingestion_jobs SET status='running',claim_token='old',claimed_at=now()-interval '2 hours' WHERE id=j;
  UPDATE legal_wiki.ingestion_jobs SET status='queued',claim_token=NULL,claimed_at=NULL WHERE id=j AND status='running' AND claimed_at<now()-interval '1 hour';
  UPDATE legal_wiki.ingestion_jobs SET status='running',claim_token='new',claimed_at=now() WHERE id=j AND status='queued';
  UPDATE legal_wiki.ingestion_jobs SET status='success',claim_token=NULL,claimed_at=NULL WHERE id=j AND claim_token='old';
  IF FOUND THEN RAISE EXCEPTION 'stale completion accepted'; END IF;
  SELECT claim_token INTO token FROM legal_wiki.ingestion_jobs WHERE id=j;
  IF token<>'new' THEN RAISE EXCEPTION 'new claim lost'; END IF;
  RAISE EXCEPTION USING ERRCODE='ZX001',MESSAGE='rollback fixture';
 EXCEPTION WHEN SQLSTATE 'ZX001' THEN NULL; END;
END $probe$;
