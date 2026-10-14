BEGIN;
-- Cross-domain personal goals; author voices and project state keep their existing sources.
CREATE TABLE IF NOT EXISTS public.sb2_personal_profiles (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id uuid NOT NULL UNIQUE REFERENCES public.sb2_users(id),
 content_markdown text NOT NULL CHECK (length(trim(content_markdown)) > 0),
 revision integer NOT NULL DEFAULT 1 CHECK (revision > 0),
 updated_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.sb2_personal_profiles ENABLE ROW LEVEL SECURITY;
COMMIT;
