CREATE TABLE IF NOT EXISTS legal_wiki.reference_job_results (
 job_id bigint PRIMARY KEY REFERENCES legal_wiki.ingestion_jobs(id),
 payload_id bigint NOT NULL REFERENCES legal_wiki.canonical_imports(payload_id),
 collected_at timestamptz NOT NULL DEFAULT now()
);
