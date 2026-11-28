BEGIN;
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public;
CREATE TABLE IF NOT EXISTS legal_wiki.precedent_embeddings(precedent_id bigint REFERENCES legal_wiki.precedents(id),model text NOT NULL CHECK(model='intfloat/multilingual-e5-base'),content_sha256 text NOT NULL CHECK(length(content_sha256)=64),embedding public.vector(768) NOT NULL,created_at timestamptz NOT NULL DEFAULT now(),PRIMARY KEY(precedent_id,model));
CREATE INDEX IF NOT EXISTS ix_precedent_embedding_hnsw ON legal_wiki.precedent_embeddings USING hnsw (embedding public.vector_cosine_ops);
CREATE OR REPLACE VIEW legal_wiki.searchable_precedent_embeddings WITH(security_invoker=true,security_barrier=true) AS SELECT e.precedent_id,e.model,e.embedding,p.case_number,p.court,p.decided_on,p.holding,p.source_url FROM legal_wiki.precedent_embeddings e JOIN legal_wiki.precedents p ON p.id=e.precedent_id AND p.content_sha256=e.content_sha256 JOIN legal_wiki.legal_sources s ON s.id=p.source_id WHERE p.verified_at IS NOT NULL AND s.enabled AND s.verified_at IS NOT NULL AND s.redistribution_allowed;
COMMIT;
