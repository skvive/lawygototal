-- LW-05/LW-07 follow-up. Requires existing LW-04 schema and verified view; apply on isolated branch.
BEGIN;
CREATE UNIQUE INDEX IF NOT EXISTS ix_ingestion_source_key ON legal_wiki.ingestion_jobs(source_id,external_key);
CREATE INDEX IF NOT EXISTS ix_ingestion_status_id ON legal_wiki.ingestion_jobs(status,id);
CREATE TABLE IF NOT EXISTS legal_wiki.raw_ingestion_payloads (id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,job_id bigint NOT NULL REFERENCES legal_wiki.ingestion_jobs(id),target text NOT NULL CHECK(target IN ('eflaw','prec')),external_id text NOT NULL,content_sha256 text NOT NULL CHECK(length(content_sha256)=64),source_url text NOT NULL,raw_xml text NOT NULL,fetched_at timestamptz NOT NULL DEFAULT now(),UNIQUE(job_id,content_sha256));
CREATE INDEX IF NOT EXISTS ix_precedent_search_fts ON legal_wiki.precedents USING gin(to_tsvector('simple',coalesce(holding,'')||' '||coalesce(case_number,'')));
INSERT INTO legal_wiki.ingestion_jobs(source_id,external_key,status) SELECT s.id,'reference:'||r.reference_label,'queued' FROM legal_wiki.legal_sources s CROSS JOIN (SELECT DISTINCT reference_label FROM legal_wiki.legal_reference_candidates WHERE verification_status='pending') r WHERE s.code='kr-law-go' ON CONFLICT(source_id,external_key) DO NOTHING;
CREATE OR REPLACE FUNCTION legal_wiki.search_beta_topics(p_tenant text, p_query text, p_limit integer DEFAULT 20)
 RETURNS TABLE(id bigint, title text, summary text, category text, score integer, review_notice text)
 LANGUAGE sql
 STABLE
 SET search_path TO 'pg_catalog'
AS $function$ SELECT r.id,r.title,r.summary,c.title,(CASE WHEN lower(r.title)=lower(btrim(p_query)) THEN 100 WHEN strpos(lower(r.title),lower(btrim(p_query)))>0 THEN 50 ELSE 0 END+CASE WHEN strpos(lower(r.summary),lower(btrim(p_query)))>0 THEN 10 ELSE 0 END)::integer,'미검수 베타 자료'::text FROM legal_wiki.wiki_revisions r JOIN legal_wiki.wiki_topics t ON t.id=r.topic_id AND t.tenant=r.tenant JOIN legal_wiki.categories c ON c.id=t.category_id WHERE r.tenant=p_tenant AND p_tenant=nullif(current_setting('app.tenant',true),'') AND r.status='published' AND length(btrim(p_query)) BETWEEN 2 AND 100 AND (strpos(lower(r.title),lower(btrim(p_query)))>0 OR strpos(lower(r.summary),lower(btrim(p_query)))>0) ORDER BY 5 DESC,r.id LIMIT least(greatest(p_limit,1),50) $function$
;
COMMIT;
