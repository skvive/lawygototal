BEGIN;
-- Literal names found in existing labels, not verified legal identifiers.
CREATE TABLE legal_wiki.reference_title_hints (title text PRIMARY KEY CHECK(length(btrim(title)) BETWEEN 2 AND 150), provenance text NOT NULL DEFAULT 'existing reference labels; search hint only');
INSERT INTO legal_wiki.reference_title_hints(title) VALUES ('가맹사업거래의 공정화에 관한 법률'),('가상자산 이용자 보호 등에 관한 법률'),('개발이익 환수에 관한 법률'),('공공기관의 정보공개에 관한 법률'),('공익사업을 위한 토지 등의 취득 및 보상에 관한 법률'),('공인중개사법'),('교원의 지위 향상 및 교육활동 보호를 위한 특별법'),('국가를 당사자로 하는 계약에 관한 법률'),('국가배상법'),('국제조세조정에 관한 법률'),('국토의 계획 및 이용에 관한 법률'),('근로자퇴직급여 보장법'),('금융소비자 보호에 관한 법률'),('기간제 및 단시간근로자 보호 등에 관한 법률'),('남녀고용평등과 일·가정 양립 지원에 관한 법률'),('노동조합 및 노동관계조정법'),('대규모유통업에서의 거래 공정화에 관한 법률'),('대부업 등의 등록 및 금융이용자 보호에 관한 법률'),('도시 및 주거환경정비법'),('독점규제 및 공정거래에 관한 법률'),('방문판매 등에 관한 법률'),('부동산 거래신고 등에 관한 법률'),('부동산 실권리자명의 등기에 관한 법률'),('부정경쟁방지 및 영업비밀보호에 관한 법률'),('부정청탁 및 금품등 수수의 금지에 관한 법률'),('상가건물 임대차보호법'),('상속세 및 증여세법'),('소음·진동관리법'),('스토킹범죄의 처벌 등에 관한 법률'),('신용정보의 이용 및 보호에 관한 법률'),('약관의 규제에 관한 법률'),('외국인근로자의 고용 등에 관한 법률'),('의료사고 피해구제 및 의료분쟁 조정 등에 관한 법률'),('인터넷주소자원에 관한 법률'),('자본시장과 금융투자업에 관한 법률'),('전자문서 및 전자거래 기본법'),('전자상거래 등에서의 소비자보호에 관한 법률'),('정보통신망 이용촉진 및 정보보호 등에 관한 법률'),('제조물 책임법'),('주식회사 등의 외부감사에 관한 법률'),('중대재해 처벌 등에 관한 법률'),('중재법'),('지방자치단체를 당사자로 하는 계약에 관한 법률'),('집합건물의 소유 및 관리에 관한 법률'),('채무자 회생 및 파산에 관한 법률'),('초·중등교육법'),('특정경제범죄 가중처벌 등에 관한 법률'),('파견근로자 보호 등에 관한 법률'),('표시·광고의 공정화에 관한 법률'),('하도급거래 공정화에 관한 법률'),('학교폭력예방 및 대책에 관한 법률'),('학원의 설립·운영 및 과외교습에 관한 법률'),('할부거래에 관한 법률'),('환경분쟁 조정 및 환경피해 구제 등에 관한 법률'),('환경오염피해 배상책임 및 구제에 관한 법률');
-- Candidate lookup plan only, not confirmed official IDs.
CREATE OR REPLACE VIEW legal_wiki.reference_lookup_plan WITH (security_invoker=true,security_barrier=true) AS
WITH labels AS (
 SELECT j.id AS job_id,j.source_id,substring(j.external_key from 11) AS reference_label
 FROM legal_wiki.ingestion_jobs j WHERE j.status='queued' AND j.external_key LIKE 'reference:%'
), titles AS (
 SELECT DISTINCT source_id,reference_label AS title FROM labels
 WHERE reference_label ~ '(법|헌법)$' AND reference_label !~ '( 및 |·| 관련 | 개별 | 특별법$| 준거법$)' AND length(reference_label)<=100
 UNION SELECT DISTINCT l.source_id,h.title FROM labels l CROSS JOIN legal_wiki.reference_title_hints h
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

COMMIT;
