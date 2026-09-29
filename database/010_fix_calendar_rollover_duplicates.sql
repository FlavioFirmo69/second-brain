-- Corregge e previene i TODO duplicati generati dal rollover di eventi
-- scaduti senza orario. PostgreSQL / Supabase, idempotente.

-- Conserva una sola conversione per evento. Se esiste una copia ancora
-- attiva, mantiene quella; altrimenti conserva la più vecchia.
with ranked as (
    select id,
           row_number() over (
               partition by user_id, description
               order by
                   case when status not in ('completed','cancelled') then 0 else 1 end,
                   created_at,
                   id
           ) as duplicate_number
      from public.sb2_tasks
     where source = 'calendar_rollover'
       and description like 'calendar_event:%'
)
delete from public.sb2_tasks t
 using ranked r
 where t.id = r.id
   and r.duplicate_number > 1;

-- Protezione definitiva anche in presenza di richieste concorrenti.
create unique index if not exists ux_sb2_tasks_calendar_rollover
    on public.sb2_tasks(user_id, description)
    where source = 'calendar_rollover'
      and description like 'calendar_event:%';

select count(*) as todo_da_eventi_senza_orario
  from public.sb2_tasks
 where source = 'calendar_rollover'
   and description like 'calendar_event:%';
