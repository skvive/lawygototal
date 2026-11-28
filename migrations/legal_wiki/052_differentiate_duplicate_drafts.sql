-- Preserve version 1 as archived; version 2 is a distinct unverified draft. Stable topic IDs and slugs retained.
WITH seed(slug,old_title,title,summary,body) AS (VALUES ('lw06-privacy-access-request-redaction-log','개인정보 열람 요구와 제삼자 정보 가림처리','개인정보 제공용 PDF의 가림처리 복원 가능성과 메타데이터 점검','제공본의 시각적 가림과 실제 텍스트·주석·첨부·메타데이터 제거를 구분하고 제삼자 정보 노출 여부를 확인한다.','> AI 실무 연구 초안 · 공식 원문 및 변호사 미검수. 법률 결론이나 인용으로 사용하지 않음.

## 핵심 쟁점
제공본의 시각적 가림과 실제 텍스트·주석·첨부·메타데이터 제거를 구분하고 제삼자 정보 노출 여부를 확인한다.

## 증거 및 입증계획
원본과 승인된 제공본의 해시, 가림 작업기록, 문서 속성·첨부 목록, 권한 있는 환경에서의 복사·검색 검사 결과, 제공 로그.

## 예상 항변
실제 정보 삭제 완료, 메타데이터에 개인정보 없음, 제공 전 재생성, 별도 자료에서의 노출.

## 실무 대응
공개 대상과 제외 대상을 목록화하고 별도 검사본을 생성한다. 승인된 로컬 환경에서 숨은 텍스트·주석·첨부·문서 속성을 확인하여 제공본의 안전성을 검수한다. 실제 정보는 추가 유출하지 않으며 법정 제공·제한 근거와 사고 대응 절차를 확인한다.

## 검증 대기
공식 원문, 적용 시점, 예외 요건, 입증책임 및 구제절차 확인 필요.'),
('lw06-insurance-policy-beneficiary-change-record','보험수익자 변경 신청과 보험사 접수 기록','법인 보험수익자의 합병 이후 보험금 청구권과 승계 증빙','합병 효력일과 보험사고 발생일, 법인 수익자의 권리승계 여부 및 변경 등록과 청구권 귀속의 관계를 구분한다.','> AI 실무 연구 초안 · 공식 원문 및 변호사 미검수. 법률 결론이나 인용으로 사용하지 않음.

## 핵심 쟁점
합병 효력일과 보험사고 발생일, 법인 수익자의 권리승계 여부 및 변경 등록과 청구권 귀속의 관계를 구분한다.

## 증거 및 입증계획
보험증권과 수익자 지정서, 합병계약·등기, 승계 자료, 사고 자료, 보험금 청구서와 회신.

## 예상 항변
합병 전 보험사고, 수익권 비승계 특약, 별도 수익자 지정, 법인 동일성 오류.

## 실무 대응
합병으로 승계되는 법적 권리와 계약상 수익자 변경 절차를 구분한다. 사고일 및 합병일의 법인 지위와 계약 문언을 대조하고 보험금 지급 상대방 및 필요한 증빙을 확인한다.

## 검증 대기
공식 원문, 적용 시점, 예외 요건, 입증책임 및 구제절차 확인 필요.'),
('lw06-redevelopment-member-address-notice','정비사업 조합원 주소 변경과 주요 통지 수령','정비조합 전자통지 동의 철회 이후 통지수단 전환','전자통지에 관한 동의의 범위와 철회 시점, 철회 후 사용된 통지 채널 및 정관과 법령상 개별 통지 요건을 확인한다.','> AI 실무 연구 초안 · 공식 원문 및 변호사 미검수. 법률 결론이나 인용으로 사용하지 않음.

## 핵심 쟁점
전자통지에 관한 동의의 범위와 철회 시점, 철회 후 사용된 통지 채널 및 정관과 법령상 개별 통지 요건을 확인한다.

## 증거 및 입증계획
전자통지 동의서와 버전, 철회 신청·접수 기록, 정관, 채널별 발송 결과, 총회 자료.

## 예상 항변
철회 미도달, 전자통지가 아닌 참고 안내, 적법한 다른 채널 통지, 동의 범위 다툼.

## 실무 대응
통지 유형별 공식 요건과 동의 상태를 기준으로 철회 전후의 발송 기록을 구분한다. 단순 열람 여부와 적법한 통지수단 사용 여부를 별개로 검토한다.

## 검증 대기
공식 원문, 적용 시점, 예외 요건, 입증책임 및 구제절차 확인 필요.')), eligible AS (
 SELECT t.id AS topic_id,t.tenant,t.slug,r.id AS revision_id FROM legal_wiki.wiki_topics t JOIN seed s ON t.slug=s.slug AND t.title=s.old_title JOIN legal_wiki.wiki_revisions r ON r.topic_id=t.id AND r.tenant=t.tenant AND r.version=1 AND r.title=s.old_title AND r.status='draft' AND r.author_id='lw06-ai-draft'
 WHERE t.tenant='demo' AND NOT EXISTS(SELECT 1 FROM legal_wiki.wiki_revisions v WHERE v.topic_id=t.id AND v.tenant=t.tenant AND v.version>1)
 AND NOT EXISTS(SELECT 1 FROM legal_wiki.legal_reference_candidates c WHERE c.revision_id=r.id) AND NOT EXISTS(SELECT 1 FROM legal_wiki.citations c WHERE c.revision_id=r.id)
 AND NOT EXISTS(SELECT 1 FROM legal_wiki.review_queue q WHERE q.revision_id=r.id) AND NOT EXISTS(SELECT 1 FROM legal_wiki.lawyer_reviews l WHERE l.revision_id=r.id)
 FOR UPDATE OF t,r
), archived AS (UPDATE legal_wiki.wiki_revisions r SET status='archived' FROM eligible e WHERE r.id=e.revision_id RETURNING r.topic_id,r.tenant), renamed AS (UPDATE legal_wiki.wiki_topics t SET title=s.title FROM eligible e JOIN seed s ON s.slug=e.slug JOIN archived a ON a.topic_id=e.topic_id AND a.tenant=e.tenant WHERE t.id=e.topic_id AND t.tenant=e.tenant RETURNING t.id,t.tenant,t.slug)
INSERT INTO legal_wiki.wiki_revisions(tenant,topic_id,version,title,summary,body_markdown,author_id,status,legal_as_of) SELECT t.tenant,t.id,2,s.title,s.summary,s.body,'lw06-ai-draft','draft',DATE '2026-11-28' FROM renamed t JOIN seed s ON s.slug=t.slug RETURNING topic_id,version,title;
