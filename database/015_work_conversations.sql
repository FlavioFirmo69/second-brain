BEGIN;
ALTER TABLE public.sb2_conversations ADD COLUMN IF NOT EXISTS book_id uuid REFERENCES public.sb2_books(id);
ALTER TABLE public.sb2_conversations ADD COLUMN IF NOT EXISTS case_id uuid REFERENCES public.sb2_cases(id);
CREATE UNIQUE INDEX IF NOT EXISTS ux_sb2_conversation_book ON public.sb2_conversations(user_id,book_id) WHERE book_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS ux_sb2_conversation_case ON public.sb2_conversations(user_id,case_id) WHERE case_id IS NOT NULL;
DO $$ BEGIN
 IF NOT EXISTS(SELECT 1 FROM pg_constraint WHERE conname='ck_sb2_conversation_context') THEN
 ALTER TABLE public.sb2_conversations ADD CONSTRAINT ck_sb2_conversation_context CHECK(num_nonnulls(book_id,case_id)<=1);
 END IF;
END $$;
COMMIT;
