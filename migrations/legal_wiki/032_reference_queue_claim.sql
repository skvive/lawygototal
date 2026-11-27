-- Explicit worker ownership; abandoned jobs must be requeued by an operator.
ALTER TABLE legal_wiki.ingestion_jobs ADD COLUMN claim_token text, ADD COLUMN claimed_at timestamptz, ADD CONSTRAINT ingestion_claim_pair CHECK ((claim_token IS NULL AND claimed_at IS NULL) OR (claim_token IS NOT NULL AND claimed_at IS NOT NULL AND status='running'));
