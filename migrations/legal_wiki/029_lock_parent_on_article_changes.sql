-- Serialize article changes with source review, even when the parent is initially unverified.
CREATE OR REPLACE FUNCTION legal_wiki.invalidate_article_parent() RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path=pg_catalog AS $$
BEGIN
 IF TG_OP='UPDATE' AND to_jsonb(NEW) IS NOT DISTINCT FROM to_jsonb(OLD) THEN RETURN NEW; END IF;
 IF TG_OP IN ('UPDATE','DELETE') THEN
   UPDATE legal_wiki.statute_versions SET verified_at=NULL WHERE id=OLD.statute_version_id;
 END IF;
 IF TG_OP='INSERT' OR (TG_OP='UPDATE' AND NEW.statute_version_id IS DISTINCT FROM OLD.statute_version_id) THEN
   UPDATE legal_wiki.statute_versions SET verified_at=NULL WHERE id=NEW.statute_version_id;
 END IF;
 IF TG_OP='DELETE' THEN RETURN OLD; END IF;
 RETURN NEW;
END $$;
