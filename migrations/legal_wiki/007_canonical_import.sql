BEGIN;
CREATE TABLE IF NOT EXISTS legal_wiki.canonical_imports(payload_id bigint PRIMARY KEY REFERENCES legal_wiki.normalized_payloads(payload_id), statute_version_id bigint REFERENCES legal_wiki.statute_versions(id), precedent_id bigint REFERENCES legal_wiki.precedents(id), imported_at timestamptz NOT NULL DEFAULT now(), CHECK(num_nonnulls(statute_version_id,precedent_id)=1));
CREATE OR REPLACE FUNCTION legal_wiki.import_normalized(p_payload bigint) RETURNS bigint LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $$
DECLARE r record; j jsonb; a jsonb; sid bigint; vid bigint; pid bigint; oldhash text;
BEGIN
  SELECT n.normalized_json,n.content_sha256,n.kind,p.source_url,p.external_id,p.content_sha256 AS raw_hash,s.id AS source_id,s.enabled,s.verified_at,s.redistribution_allowed
  INTO r FROM legal_wiki.normalized_payloads n JOIN legal_wiki.raw_ingestion_payloads p ON p.id=n.payload_id JOIN legal_wiki.ingestion_jobs k ON k.id=p.job_id JOIN legal_wiki.legal_sources s ON s.id=k.source_id WHERE n.payload_id=p_payload FOR UPDATE OF n FOR SHARE OF s;
  IF NOT FOUND THEN RAISE EXCEPTION 'normalized payload missing'; END IF;
  IF NOT r.enabled OR r.verified_at IS NULL OR NOT r.redistribution_allowed OR r.source_url !~ '^https://www[.]law[.]go[.]kr/' THEN RAISE EXCEPTION 'source approval required'; END IF;
  j:=r.normalized_json;
  IF r.raw_hash<>r.content_sha256 OR j->>'content_sha256' IS DISTINCT FROM r.raw_hash OR j->>'external_id' IS DISTINCT FROM ltrim(r.external_id,'0') OR j->>'verified' IS DISTINCT FROM 'false' THEN RAISE EXCEPTION 'payload identity mismatch'; END IF;
  SELECT COALESCE(statute_version_id,precedent_id) INTO vid FROM legal_wiki.canonical_imports WHERE payload_id=p_payload;
  IF FOUND THEN RETURN vid; END IF;
  IF r.kind='statute' THEN
    IF jsonb_typeof(j->'articles') IS DISTINCT FROM 'array' OR jsonb_array_length(j->'articles')=0 THEN RAISE EXCEPTION 'missing articles'; END IF;
    INSERT INTO legal_wiki.statutes(source_id,external_id,title,statute_type) VALUES(r.source_id,j->>'external_id',j->>'title',j->>'statute_type') ON CONFLICT(source_id,external_id) DO NOTHING;
    SELECT id INTO STRICT sid FROM legal_wiki.statutes WHERE source_id=r.source_id AND external_id=j->>'external_id';
    INSERT INTO legal_wiki.statute_versions(statute_id,external_version_id,promulgated_on,effective_from,effective_to,source_url,content_sha256) VALUES(sid,j->>'external_version_id',(j->>'promulgated_on')::date,(j->>'effective_from')::date,(j->>'effective_to')::date,r.source_url,r.content_sha256) ON CONFLICT(statute_id,external_version_id) DO NOTHING;
    SELECT id,content_sha256 INTO STRICT vid,oldhash FROM legal_wiki.statute_versions WHERE statute_id=sid AND external_version_id=j->>'external_version_id';
    IF oldhash<>r.content_sha256 THEN RAISE EXCEPTION 'statute version hash conflict'; END IF;
    FOR a IN SELECT value FROM jsonb_array_elements(j->'articles') LOOP
      INSERT INTO legal_wiki.article_versions(statute_version_id,article_key,heading,body,effective_from,effective_to,source_url,transitional_note) VALUES(vid,a->>'article_key',a->>'heading',a->>'body',(a->>'effective_from')::date,(a->>'effective_to')::date,r.source_url,(j->'transitional_notes')::text) ON CONFLICT(statute_version_id,article_key) DO NOTHING;
    END LOOP;
    INSERT INTO legal_wiki.canonical_imports(payload_id,statute_version_id) VALUES(p_payload,vid);
    RETURN vid;
  ELSIF r.kind='precedent' THEN
    INSERT INTO legal_wiki.precedents(source_id,external_id,court,case_number,decided_on,case_type,decision_type,original_text,holding,source_url,content_sha256) VALUES(r.source_id,j->>'external_id',j->>'court',j->>'case_number',(j->>'decided_on')::date,j->>'case_type',j->>'decision_type',j->>'original_text',j->>'holding',r.source_url,r.content_sha256) ON CONFLICT(source_id,external_id,content_sha256) DO NOTHING;
    SELECT id INTO STRICT pid FROM legal_wiki.precedents WHERE source_id=r.source_id AND external_id=j->>'external_id' AND content_sha256=r.content_sha256;
    INSERT INTO legal_wiki.canonical_imports(payload_id,precedent_id) VALUES(p_payload,pid);
    RETURN pid;
  ELSE RAISE EXCEPTION 'unknown normalized kind'; END IF;
END $$;
REVOKE EXECUTE ON FUNCTION legal_wiki.import_normalized(bigint) FROM PUBLIC;
COMMIT;
