-- Aggiunge alle voci di calendario il collegamento alternativo a una pratica.
-- Eseguire una volta nel SQL Editor di Supabase prima di distribuire questa versione.

begin;

alter table public.sb2_events
    add column if not exists case_id uuid references public.sb2_cases(id);

create index if not exists ix_sb2_events_project_id
    on public.sb2_events(project_id);

create index if not exists ix_sb2_events_case_id
    on public.sb2_events(case_id);

create index if not exists ix_sb2_tasks_project_id
    on public.sb2_tasks(project_id);

create index if not exists ix_sb2_tasks_case_id
    on public.sb2_tasks(case_id);

do $$
begin
    if not exists (
        select 1 from pg_constraint where conname = 'ck_sb2_tasks_single_context'
    ) then
        alter table public.sb2_tasks
            add constraint ck_sb2_tasks_single_context
            check (num_nonnulls(project_id, case_id) <= 1);
    end if;

    if not exists (
        select 1 from pg_constraint where conname = 'ck_sb2_events_single_context'
    ) then
        alter table public.sb2_events
            add constraint ck_sb2_events_single_context
            check (num_nonnulls(project_id, case_id) <= 1);
    end if;
end $$;

commit;

select column_name, data_type
  from information_schema.columns
 where table_schema = 'public'
   and table_name = 'sb2_events'
   and column_name in ('project_id', 'case_id')
 order by column_name;
