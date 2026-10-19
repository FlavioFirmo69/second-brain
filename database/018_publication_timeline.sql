BEGIN;
ALTER TABLE public.sb2_books ADD COLUMN IF NOT EXISTS planned_release_date date;
ALTER TABLE public.sb2_books ADD COLUMN IF NOT EXISTS release_plan_note text;
COMMENT ON COLUMN public.sb2_books.planned_release_date IS 'Independent target release date; never proof of actual publication.';
COMMIT;
