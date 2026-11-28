BEGIN;
ALTER TABLE legal_wiki.reference_job_mappings ADD COLUMN master_id text, ADD COLUMN requested_effective_on date, ADD CONSTRAINT reference_mapping_version_pair CHECK ((master_id IS NULL AND requested_effective_on IS NULL) OR (target='eflaw' AND master_id IS NOT NULL AND master_id ~ '^[0-9]{1,20}$' AND master_id::numeric>0 AND requested_effective_on IS NOT NULL));
ALTER TABLE legal_wiki.raw_ingestion_payloads ADD COLUMN master_id text, ADD COLUMN requested_effective_on date, ADD CONSTRAINT raw_payload_version_pair CHECK ((master_id IS NULL AND requested_effective_on IS NULL) OR (target='eflaw' AND master_id IS NOT NULL AND master_id ~ '^[0-9]{1,20}$' AND master_id::numeric>0 AND requested_effective_on IS NOT NULL));
COMMIT;
