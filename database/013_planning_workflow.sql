BEGIN;
CREATE TABLE IF NOT EXISTS public.sb2_plans (
 id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
 user_id uuid NOT NULL REFERENCES public.sb2_users(id),
 case_id uuid REFERENCES public.sb2_cases(id),
 book_id uuid REFERENCES public.sb2_books(id),
 parent_id uuid REFERENCES public.sb2_plans(id),
 status varchar(30) NOT NULL DEFAULT 'interview' CHECK(status IN ('interview','draft','active','discarded','cleaned')),
 brief text NOT NULL DEFAULT '',
 dialogue jsonb NOT NULL DEFAULT '[]',
 draft jsonb,
 source_snapshot jsonb,
 revision integer NOT NULL DEFAULT 0,
 sales_updated_through date,
 created_at timestamptz NOT NULL DEFAULT now(),
 updated_at timestamptz NOT NULL DEFAULT now(),
 CHECK(num_nonnulls(case_id,book_id)=1)
);
ALTER TABLE public.sb2_plans ADD COLUMN IF NOT EXISTS source_snapshot jsonb;
ALTER TABLE public.sb2_plans ENABLE ROW LEVEL SECURITY;
CREATE UNIQUE INDEX IF NOT EXISTS ux_sb2_plan_active_book ON public.sb2_plans(user_id,book_id) WHERE status='active' AND parent_id IS NULL;
CREATE UNIQUE INDEX IF NOT EXISTS ux_sb2_plan_active_case ON public.sb2_plans(user_id,case_id) WHERE status='active' AND parent_id IS NULL;
ALTER TABLE public.sb2_tasks ADD COLUMN IF NOT EXISTS plan_id uuid REFERENCES public.sb2_plans(id);
ALTER TABLE public.sb2_events ADD COLUMN IF NOT EXISTS plan_id uuid REFERENCES public.sb2_plans(id);
CREATE INDEX IF NOT EXISTS ix_sb2_task_plan ON public.sb2_tasks(plan_id);
CREATE INDEX IF NOT EXISTS ix_sb2_event_plan ON public.sb2_events(plan_id);
COMMIT;
