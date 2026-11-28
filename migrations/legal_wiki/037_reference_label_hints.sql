BEGIN;
-- Explicit single-title lookup hints only; no inferred identifiers or multi-source completion.
CREATE TABLE legal_wiki.reference_label_hints(reference_label text PRIMARY KEY, title text NOT NULL CHECK(length(btrim(title)) BETWEEN 2 AND 150), provenance text NOT NULL DEFAULT 'single-title search hint; operator confirmation required');
INSERT INTO legal_wiki.reference_label_hints(reference_label,title) VALUES ('개인정보 보호법 국외 이전 규정','개인정보 보호법'),('공동주택관리법 하자담보 관련 규정','공동주택관리법'),('국세기본법 가산세 관련 규정','국세기본법'),('국세기본법 과세전적부심사 규정','국세기본법'),('국세기본법 납세자 권리 및 세무조사 규정','국세기본법'),('국세기본법 제2차 납세의무 관련 규정','국세기본법'),('국제사법 계약 준거법 규정','국제사법'),('국제사법 국제재판관할 규정','국제사법'),('노동조합 및 노동관계조정법 단체협약 규정','노동조합 및 노동관계조정법'),('노동조합 및 노동관계조정법 부당노동행위 규정','노동조합 및 노동관계조정법'),('도시 및 주거환경정비법 조합설립 규정','도시 및 주거환경정비법'),('도시 및 주거환경정비법 총회 규정','도시 및 주거환경정비법'),('독점규제 및 공정거래에 관한 법률 공동행위 규정','독점규제 및 공정거래에 관한 법률'),('독점규제 및 공정거래에 관한 법률 기업결합 규정','독점규제 및 공정거래에 관한 법률'),('독점규제 및 공정거래에 관한 법률 불공정거래 규정','독점규제 및 공정거래에 관한 법률'),('독점규제 및 공정거래에 관한 법률 시장지배 규정','독점규제 및 공정거래에 관한 법률'),('디자인보호법 디자인권 효력 및 침해금지 규정','디자인보호법'),('민법 계약 해석 법리','민법'),('민법 기한 및 채무불이행 규정','민법'),('민법 도급 규정','민법'),('민법 법률행위 및 의사능력 법리','민법'),('민법 보증인 구상권 규정','민법'),('민법 보증채무 규정','민법'),('민법 상속 승인 및 청산 규정','민법'),('민법 유언집행 관련 규정','민법'),('민법 임대차 규정','민법'),('민법 입양 규정','민법'),('민법 조합 관련 규정','민법'),('민법 지상권 관련 규정','민법'),('민법 채무인수 규정','민법'),('민법 친생관계 관련 규정','민법'),('민사소송법 가집행 관련 규정','민사소송법'),('민사소송법 감정 규정','민사소송법'),('민사소송법 당사자 관련 규정','민사소송법'),('민사소송법 보통·특별재판적 규정','민사소송법'),('민사소송법 소송비용 규정','민사소송법'),('민사소송법 이송 규정','민사소송법'),('민사소송법 제358조 등 문서 증거 규정','민사소송법'),('민사소송법 증인신문 규정','민사소송법'),('민사집행법 가압류·가처분 담보 관련 규정','민사집행법'),('민사집행법 배당이의 관련 규정','민사집행법'),('민사집행법 부동산 강제집행 규정','민사집행법'),('민사집행법 재산명시 및 재산조회 규정','민사집행법'),('민사집행법 집행문 관련 규정','민사집행법'),('발명진흥법 직무발명 규정','발명진흥법'),('부가가치세법 공급시기 규정','부가가치세법'),('부가가치세법 매입세액 공제 규정','부가가치세법'),('부정경쟁방지 및 영업비밀보호에 관한 법률 영업비밀 규정','부정경쟁방지 및 영업비밀보호에 관한 법률'),('산업재해보상보험법 심사·재심사 관련 규정','산업재해보상보험법'),('상법 자본금 감소 관련 규정','상법'),('상법 주식 양도 관련 규정','상법'),('상법 합병 관련 규정','상법'),('상속세 및 증여세법 재산평가 규정','상속세 및 증여세법'),('상표법 등록무효 규정','상표법'),('상표법 불사용취소 규정','상표법'),('소득세법 양도소득 필요경비 규정','소득세법'),('자본시장과 금융투자업에 관한 법률 공시 및 책임 규정','자본시장과 금융투자업에 관한 법률'),('저작권법 저작인격권 규정','저작권법'),('전자문서 및 전자거래 기본법 전자문서 송수신 규정','전자문서 및 전자거래 기본법'),('전자서명법 전자서명 효력 규정','전자서명법'),('채무자 회생 및 파산에 관한 법률 개인회생 규정','채무자 회생 및 파산에 관한 법률'),('채무자 회생 및 파산에 관한 법률 개인회생 면책 규정','채무자 회생 및 파산에 관한 법률'),('채무자 회생 및 파산에 관한 법률 파산·면책 규정','채무자 회생 및 파산에 관한 법률'),('채무자 회생 및 파산에 관한 법률 회생절차 규정','채무자 회생 및 파산에 관한 법률'),('채무자 회생 및 파산에 관한 법률 회생채권 규정','채무자 회생 및 파산에 관한 법률'),('최저임금법 최저임금 적용 규정','최저임금법'),('특허법 무효심판 규정','특허법'),('행정소송법 무효등확인소송 규정','행정소송법'),('행정소송법 부작위위법확인소송 규정','행정소송법'),('행정절차법 제22조 및 청문 규정','행정절차법'),('형법 강도 관련 규정','형법'),('형법 사기죄 관련 규정','형법'),('형법 사문서위조·행사 관련 규정','형법'),('형사소송법 고소·고발 규정','형사소송법'),('형사소송법 공소제기 관련 규정','형사소송법'),('형사소송법 압수·수색 관련 규정','형사소송법'),('형사소송법 약식절차 규정','형사소송법'),('형사소송법 항소 관련 규정','형사소송법');
CREATE OR REPLACE VIEW legal_wiki.reference_lookup_plan WITH (security_invoker=true,security_barrier=true) AS
WITH labels AS (
 SELECT j.id AS job_id,j.source_id,substring(j.external_key from 11) AS reference_label
 FROM legal_wiki.ingestion_jobs j WHERE j.status='queued' AND j.external_key LIKE 'reference:%'
), titles AS (
 SELECT DISTINCT source_id,reference_label AS title FROM labels
 WHERE reference_label ~ '(법|헌법)$' AND reference_label !~ '( 및 |·| 관련 | 개별 | 특별법$| 준거법$)' AND length(reference_label)<=100
 UNION SELECT DISTINCT l.source_id,h.title FROM labels l CROSS JOIN legal_wiki.reference_title_hints h
), planned AS (
 SELECT l.*,coalesce(t.title,h.title) AS query FROM labels l LEFT JOIN legal_wiki.reference_label_hints h ON h.reference_label=l.reference_label LEFT JOIN LATERAL (
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
