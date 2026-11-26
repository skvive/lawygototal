-- DEV ONLY. All synthetic rows rolled back in a subtransaction.
DO $test$
DECLARE s bigint; j bigint; p bigint; v bigint; t bigint; r bigint; d text; h text:=encode(sha256(convert_to('synthetic only','UTF8')),'hex'); approved bigint;
BEGIN
 BEGIN
  PERFORM set_config('app.tenant','lw09-synthetic',true);
  INSERT INTO legal_wiki.legal_sources(code,agency,base_url,enabled,redistribution_allowed,verified_at) VALUES('lw09-synthetic','TEST ONLY','https://www.law.go.kr',false,false,NULL) RETURNING id INTO s;
  INSERT INTO legal_wiki.ingestion_jobs(source_id,external_key,status) VALUES(s,'synthetic:123','quarantined') RETURNING id INTO j;
  INSERT INTO legal_wiki.raw_ingestion_payloads(job_id,target,external_id,content_sha256,source_url,raw_xml) VALUES(j,'prec','123',h,'https://www.law.go.kr/test','synthetic only') RETURNING id INTO p;
  INSERT INTO legal_wiki.normalized_payloads(payload_id,kind,normalized_json,content_sha256) VALUES(p,'precedent',jsonb_build_object('kind','precedent','external_id','123','court','TEST','case_number','TEST','decided_on','2020-01-01','original_text','TEST','holding','TEST','verified',false,'content_sha256',h),h);
  BEGIN PERFORM legal_wiki.import_normalized(p); RAISE EXCEPTION 'disabled source accepted'; EXCEPTION WHEN raise_exception THEN IF SQLERRM<>'source approval required' THEN RAISE; END IF; END;
  UPDATE legal_wiki.legal_sources SET enabled=true,redistribution_allowed=true,verified_at=now() WHERE id=s;
  v:=legal_wiki.import_normalized(p);
  IF v IS DISTINCT FROM legal_wiki.import_normalized(p) THEN RAISE EXCEPTION 'import not idempotent'; END IF;
  IF EXISTS(SELECT 1 FROM legal_wiki.precedents WHERE id=v AND verified_at IS NOT NULL) THEN RAISE EXCEPTION 'import auto-verified'; END IF;
  INSERT INTO public.users(id,tenant,email,password_hash,display_name,role,created_at) VALUES('lw09-fixture-reviewer','lw09-synthetic','lw09-fixture@example.invalid','not-a-password','TEST ONLY','editor',now()::text);
  INSERT INTO public.lawyer_verifications(user_id,tenant,professional_number,status,checked_by,checked_at,created_at) VALUES('lw09-fixture-reviewer','lw09-synthetic','TEST ONLY','approved','fixture',now()::text,now()::text);
  INSERT INTO legal_wiki.wiki_topics(tenant,slug,category_id,title,audience) VALUES('lw09-synthetic','synthetic',4,'TEST ONLY','lawyer') RETURNING id INTO t;
  INSERT INTO legal_wiki.wiki_revisions(tenant,topic_id,version,title,summary,body_markdown,author_id,status,legal_as_of) VALUES('lw09-synthetic',t,1,'TEST','TEST','TEST','fixture-author','draft','2021-01-01') RETURNING id INTO r;
  SELECT encode(sha256(convert_to(jsonb_build_array(title,summary,body_markdown,legal_as_of,version)::text,'UTF8')),'hex') INTO d FROM legal_wiki.wiki_revisions WHERE id=r;
  BEGIN PERFORM legal_wiki.approve_and_publish('lw09-synthetic',r,'lw09-fixture-reviewer',d,'fixture'); RAISE EXCEPTION 'missing citations accepted'; EXCEPTION WHEN check_violation THEN NULL; END;
  IF EXISTS(SELECT 1 FROM legal_wiki.lawyer_reviews WHERE revision_id=r) THEN RAISE EXCEPTION 'failed approval persisted'; END IF;
  UPDATE legal_wiki.precedents SET verified_at=now() WHERE id=v;
  INSERT INTO legal_wiki.citations(tenant,revision_id,proposition_key,precedent_id,pinpoint,relation,verified_by,verified_at) VALUES('lw09-synthetic',r,'test',v,'test','supports','fixture',now());
  approved:=legal_wiki.approve_and_publish('lw09-synthetic',r,'lw09-fixture-reviewer',d,'fixture');
  IF approved<>r OR NOT EXISTS(SELECT 1 FROM legal_wiki.qualified_verified_revisions WHERE id=r) THEN RAISE EXCEPTION 'valid synthetic approval failed'; END IF;
  RAISE EXCEPTION USING ERRCODE='ZX001',MESSAGE='rollback synthetic success';
 EXCEPTION WHEN SQLSTATE 'ZX001' THEN NULL; END;
END $test$;
