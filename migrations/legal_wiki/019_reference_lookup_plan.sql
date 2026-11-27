-- Candidate lookup plan only, not confirmed official IDs.
CREATE OR REPLACE VIEW legal_wiki.reference_lookup_plan WITH (security_invoker=true,security_barrier=true) AS
WITH labels AS (
 SELECT j.id AS job_id,j.source_id,substring(j.external_key from 11) AS reference_label
 FROM legal_wiki.ingestion_jobs j WHERE j.status='queued' AND j.external_key LIKE 'reference:%'
), titles AS (
 SELECT DISTINCT source_id,reference_label AS title FROM labels
 WHERE reference_label ~ '(법|헌법)$' AND reference_label !~ '( 및 |·| 관련 | 개별 | 특별법$| 준거법$)' AND length(reference_label)<=100
), planned AS (
 SELECT l.*,t.title AS query FROM labels l LEFT JOIN LATERAL (
 SELECT title FROM titles t WHERE t.source_id=l.source_id AND
 (l.reference_label=t.title OR (left(l.reference_label,length(t.title)+2)=t.title||' 제'
 AND substring(l.reference_label from length(t.title)+2) ~ '^제[0-9]+조(의[0-9]+)?( 제[0-9]+항)?(([·~])제[0-9]+조(의[0-9]+)?( 제[0-9]+항)?)*( 이하)?$'))
 ORDER BY length(title) DESC LIMIT 1
 ) t ON true
)
SELECT p.job_id,p.source_id,p.reference_label,p.query,
 CASE WHEN m.job_id IS NOT NULL THEN 'mapped' WHEN p.query IS NOT NULL THEN 'candidate_lookup' ELSE 'manual_review' END AS plan_status
 FROM planned p LEFT JOIN legal_wiki.reference_job_mappings m ON m.job_id=p.job_id;
