-- Development-only synthetic transactional probe; all fixture rows rolled back.
DO $probe$
DECLARE s bigint; p bigint; st bigint; v bigint; a bigint; h text:=repeat('a',64);
BEGIN
 BEGIN
  INSERT INTO legal_wiki.legal_sources(code,agency,base_url,enabled,redistribution_allowed,verified_at) VALUES('fixture-source-invalidation','TEST ONLY','https://www.law.go.kr/',true,true,now()) RETURNING id INTO s;
  INSERT INTO legal_wiki.precedents(source_id,external_id,court,case_number,decided_on,original_text,holding,source_url,content_sha256,verified_at)
    VALUES(s,'1','TEST','TEST','2020-01-01','TEST ONLY','TEST ONLY','https://www.law.go.kr/test',h,now()) RETURNING id INTO p;
  INSERT INTO legal_wiki.precedent_embeddings(precedent_id,model,content_sha256,embedding)
    VALUES(p,'intfloat/multilingual-e5-base',h,('['||'1,'||repeat('0,',766)||'0]')::public.vector);
  IF NOT EXISTS(SELECT 1 FROM legal_wiki.searchable_precedent_embeddings WHERE precedent_id=p) THEN RAISE EXCEPTION 'fixture not searchable'; END IF;
  UPDATE legal_wiki.precedents SET fetched_at=now() WHERE id=p;
  IF NOT EXISTS(SELECT 1 FROM legal_wiki.searchable_precedent_embeddings WHERE precedent_id=p) THEN RAISE EXCEPTION 'non-substantive refresh invalidated'; END IF;
  UPDATE legal_wiki.precedents SET original_text='CHANGED',verified_at=now() WHERE id=p;
  IF EXISTS(SELECT 1 FROM legal_wiki.searchable_precedent_embeddings WHERE precedent_id=p) OR EXISTS(SELECT 1 FROM legal_wiki.precedents WHERE id=p AND verified_at IS NOT NULL) THEN RAISE EXCEPTION 'changed precedent still verified'; END IF;
  INSERT INTO legal_wiki.statutes(source_id,external_id,title,statute_type) VALUES(s,'2','TEST ONLY','법률') RETURNING id INTO st;
  INSERT INTO legal_wiki.statute_versions(statute_id,external_version_id,effective_from,source_url,content_sha256) VALUES(st,'fixture','2020-01-01','https://www.law.go.kr/test',h) RETURNING id INTO v;
  INSERT INTO legal_wiki.article_versions(statute_version_id,article_key,body,effective_from,source_url) VALUES(v,'1','TEST ONLY','2020-01-01','https://www.law.go.kr/test') RETURNING id INTO a;
  UPDATE legal_wiki.statute_versions SET verified_at=now() WHERE id=v;
  UPDATE legal_wiki.article_versions SET body=body WHERE id=a;
  IF NOT EXISTS(SELECT 1 FROM legal_wiki.statute_versions WHERE id=v AND verified_at IS NOT NULL) THEN RAISE EXCEPTION 'no-op invalidated'; END IF;
  UPDATE legal_wiki.article_versions SET body='CHANGED' WHERE id=a;
  IF EXISTS(SELECT 1 FROM legal_wiki.statute_versions WHERE id=v AND verified_at IS NOT NULL) THEN RAISE EXCEPTION 'changed article still verified'; END IF;
  UPDATE legal_wiki.statute_versions SET verified_at=now() WHERE id=v;
  UPDATE legal_wiki.statutes SET title='CHANGED' WHERE id=st;
  IF EXISTS(SELECT 1 FROM legal_wiki.statute_versions WHERE id=v AND verified_at IS NOT NULL) THEN RAISE EXCEPTION 'changed statute metadata still verified'; END IF;
  UPDATE legal_wiki.statute_versions SET verified_at=now() WHERE id=v;
  INSERT INTO legal_wiki.article_versions(statute_version_id,article_key,body,effective_from,source_url) VALUES(v,'2','TEST ONLY','2020-01-01','https://www.law.go.kr/test');
  IF EXISTS(SELECT 1 FROM legal_wiki.statute_versions WHERE id=v AND verified_at IS NOT NULL) THEN RAISE EXCEPTION 'added article still verified'; END IF;
  RAISE EXCEPTION USING ERRCODE='ZX001',MESSAGE='rollback successful synthetic probe';
 EXCEPTION WHEN SQLSTATE 'ZX001' THEN NULL; END;
END $probe$;
