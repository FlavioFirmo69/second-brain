BEGIN;
CREATE TABLE IF NOT EXISTS public.sb2_strategic_memories (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id uuid NOT NULL REFERENCES public.sb2_users(id),
 kind text NOT NULL CHECK (kind IN ('learning','constraint','decision','connection','correction')),
 content text NOT NULL,
 rationale text NOT NULL,
 source_refs jsonb NOT NULL DEFAULT '[]',
 created_at timestamptz NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_sb2_strategic_memories_user ON public.sb2_strategic_memories(user_id);
ALTER TABLE public.sb2_strategic_memories ENABLE ROW LEVEL SECURITY;
COMMIT;
