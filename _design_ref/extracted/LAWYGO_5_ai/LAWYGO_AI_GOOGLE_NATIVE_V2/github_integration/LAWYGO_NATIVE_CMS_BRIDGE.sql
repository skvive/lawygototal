-- LAWYGO Native Board interoperability. Apply only after staging review.
-- This adds idempotent CMS metadata without changing existing native board content.
ALTER TABLE public.board_posts
  ADD COLUMN IF NOT EXISTS cms_external_source text,
  ADD COLUMN IF NOT EXISTS cms_external_revision integer NOT NULL DEFAULT 0;
CREATE UNIQUE INDEX IF NOT EXISTS ux_lawygo_cms_external_source
  ON public.board_posts (management_number, cms_external_source)
  WHERE cms_external_source IS NOT NULL;
