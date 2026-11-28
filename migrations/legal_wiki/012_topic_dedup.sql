CREATE UNIQUE INDEX IF NOT EXISTS ix_wiki_topic_title_normalized ON legal_wiki.wiki_topics(tenant,(regexp_replace(lower(normalize(title,NFKC)),'[^[:alnum:]가-힣]','','g')));
