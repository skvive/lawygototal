BEGIN;
CREATE OR REPLACE FUNCTION legal_wiki.invalidate_changed_source_text() RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $$
BEGIN
 IF (to_jsonb(NEW)-'verified_at'-'fetched_at') IS DISTINCT FROM (to_jsonb(OLD)-'verified_at'-'fetched_at') THEN
   NEW.verified_at:=NULL;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER lw_source_precedent_invalidate BEFORE UPDATE ON legal_wiki.precedents FOR EACH ROW EXECUTE FUNCTION legal_wiki.invalidate_changed_source_text();
CREATE TRIGGER lw_source_version_invalidate BEFORE UPDATE ON legal_wiki.statute_versions FOR EACH ROW EXECUTE FUNCTION legal_wiki.invalidate_changed_source_text();
CREATE OR REPLACE FUNCTION legal_wiki.invalidate_article_parent() RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $$
BEGIN
 IF TG_OP='UPDATE' AND to_jsonb(NEW) IS NOT DISTINCT FROM to_jsonb(OLD) THEN RETURN NEW; END IF;
 IF TG_OP IN ('UPDATE','DELETE') THEN
   UPDATE legal_wiki.statute_versions SET verified_at=NULL WHERE id=OLD.statute_version_id AND verified_at IS NOT NULL;
 END IF;
 IF TG_OP='INSERT' OR (TG_OP='UPDATE' AND NEW.statute_version_id IS DISTINCT FROM OLD.statute_version_id) THEN
   UPDATE legal_wiki.statute_versions SET verified_at=NULL WHERE id=NEW.statute_version_id AND verified_at IS NOT NULL;
 END IF;
 IF TG_OP='DELETE' THEN RETURN OLD; END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER lw_source_article_invalidate AFTER INSERT OR UPDATE OR DELETE ON legal_wiki.article_versions FOR EACH ROW EXECUTE FUNCTION legal_wiki.invalidate_article_parent();
CREATE OR REPLACE FUNCTION legal_wiki.invalidate_statute_metadata() RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $$
BEGIN
 IF to_jsonb(NEW) IS DISTINCT FROM to_jsonb(OLD) THEN
   UPDATE legal_wiki.statute_versions SET verified_at=NULL WHERE statute_id=NEW.id AND verified_at IS NOT NULL;
 END IF;
 RETURN NEW;
END $$;
CREATE TRIGGER lw_source_statute_invalidate AFTER UPDATE ON legal_wiki.statutes FOR EACH ROW EXECUTE FUNCTION legal_wiki.invalidate_statute_metadata();
COMMIT;
