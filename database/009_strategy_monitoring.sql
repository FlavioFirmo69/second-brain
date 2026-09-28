-- Monitoraggio esplicito delle strategie.
-- Migrazione PostgreSQL / Supabase, idempotente.
-- Il backfill riguarda Rubicone e Peter, attraverso i rispettivi progetti.

alter table public.sb2_strategies
    add column if not exists start_date date,
    add column if not exists end_date date,
    add column if not exists baseline_value numeric(18,2),
    add column if not exists review_frequency varchar(20) not null default 'weekly',
    add column if not exists last_review_date date,
    add column if not exists next_review_date date;

alter table public.sb2_tasks
    add column if not exists strategy_id uuid references public.sb2_strategies(id);

alter table public.sb2_events
    add column if not exists strategy_id uuid references public.sb2_strategies(id);

alter table public.sb2_targets
    add column if not exists strategy_id uuid references public.sb2_strategies(id);

create index if not exists ix_sb2_tasks_strategy on public.sb2_tasks(strategy_id);
create index if not exists ix_sb2_events_strategy on public.sb2_events(strategy_id);
create index if not exists ix_sb2_targets_strategy on public.sb2_targets(strategy_id);

do $$
declare
    v_strategy_id uuid;
    v_project_id uuid;
    v_book_id uuid;
    v_author_id uuid;
    v_start_date date;
    v_end_date date;
    v_created_date date;
    v_strategy_code text;
    v_project_code text;
begin
    for v_strategy_code, v_project_code in
        select * from (values
            ('BOOK_RUBICONE'::text, 'RUBICONE'::text),
            ('BOOK_PETER'::text, 'PETER'::text)
        ) as mappings(strategy_code, project_code)
    loop
        v_strategy_id := null;
        v_project_id := null;
        v_book_id := null;
        v_author_id := null;
        v_start_date := null;
        v_end_date := null;
        v_created_date := null;

        select s.id, s.book_id, s.author_profile_id, s.created_at::date
          into v_strategy_id, v_book_id, v_author_id, v_created_date
          from public.sb2_strategies s
         where upper(s.code) = v_strategy_code
         order by s.version_number desc, s.created_at desc
         limit 1;

        select p.id
          into v_project_id
          from public.sb2_projects p
         where upper(p.code) = v_project_code
           and (v_book_id is null or p.book_id = v_book_id)
         order by p.created_at
         limit 1;

        if v_strategy_id is null then
            raise notice 'Strategia % non trovata: nessun backfill eseguito.', v_strategy_code;
            continue;
        end if;

        if v_project_id is null then
            raise notice 'Progetto % non trovato: nessuna attività collegata.', v_project_code;
            continue;
        end if;

        update public.sb2_tasks
       set strategy_id = v_strategy_id,
           book_id = coalesce(book_id, v_book_id),
           author_profile_id = coalesce(author_profile_id, v_author_id),
           updated_at = now()
     where project_id = v_project_id
       and strategy_id is null;

        update public.sb2_events
       set strategy_id = v_strategy_id,
           book_id = coalesce(book_id, v_book_id),
           author_profile_id = coalesce(author_profile_id, v_author_id),
           updated_at = now()
     where project_id = v_project_id
       and strategy_id is null;

        update public.sb2_targets
       set strategy_id = v_strategy_id
     where book_id = v_book_id
       and metric_code = 'copies_sold'
       and strategy_id is null;

        select min(action_date) into v_start_date
      from (
        select due_date as action_date from public.sb2_tasks where strategy_id = v_strategy_id and due_date is not null
        union all
        select event_date from public.sb2_events where strategy_id = v_strategy_id
      ) actions;

        select max(target_date) into v_end_date
      from public.sb2_targets
     where strategy_id = v_strategy_id
       and metric_code = 'copies_sold';

        update public.sb2_strategies
       set start_date = coalesce(start_date, v_start_date, v_created_date),
           end_date = coalesce(end_date, v_end_date),
           baseline_value = coalesce(
               baseline_value,
               (select coalesce(sum(quantity), 0)
                  from public.sb2_sales
                 where book_id = v_book_id
                   and sale_date < coalesce(v_start_date, v_created_date)),
               0
           ),
           next_review_date = coalesce(next_review_date, coalesce(v_start_date, v_created_date) + 7),
           updated_at = now()
         where id = v_strategy_id;
    end loop;
end $$;

select s.code,
       s.start_date,
       s.end_date,
       s.baseline_value,
       count(distinct t.id) as attivita_collegate,
       count(distinct e.id) as eventi_collegati,
       count(distinct g.id) as target_collegati
  from public.sb2_strategies s
  left join public.sb2_tasks t on t.strategy_id = s.id
  left join public.sb2_events e on e.strategy_id = s.id
  left join public.sb2_targets g on g.strategy_id = s.id
 where upper(s.code) in ('BOOK_RUBICONE', 'BOOK_PETER')
 group by s.id, s.code, s.start_date, s.end_date, s.baseline_value;
