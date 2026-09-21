-- Ripristino appuntamenti mancanti dopo la migrazione a Supabase.
-- PostgreSQL / Supabase. Lo script e' idempotente e puo' essere rieseguito.

begin;

do $$
declare
    v_user_id uuid;
    v_arona_project_id uuid;
begin
    select id
      into v_user_id
      from public.sb2_users
     where lower(email) = lower('owner@secondbrain.local')
       and is_active = true
     limit 1;

    if v_user_id is null then
        raise exception 'Utente owner@secondbrain.local non trovato in sb2_users';
    end if;

    select id
      into v_arona_project_id
      from public.sb2_projects
     where user_id = v_user_id
       and upper(code) = 'ARONA'
     limit 1;

    if v_arona_project_id is null then
        raise exception 'Progetto ARONA non trovato in sb2_projects';
    end if;

    -- Completa l'evento gia' presente senza crearne una seconda copia.
    update public.sb2_events
       set location = 'Teatro Grande',
           event_type = 'theatre',
           updated_at = now()
     where user_id = v_user_id
       and event_date = date '2026-09-27'
       and start_time = time '15:30'
       and lower(title) like '%morte a venezia%';

    -- Appuntamenti con e senza orario.
    with event_data(title, event_date, start_time, end_time, location, event_type) as (
        values
          ('Morte a Venezia', date '2026-09-27', time '15:30', null::time, 'Teatro Grande', 'theatre'),
          ('Festival Pianistico — Beatrice Rana', date '2026-10-01', time '21:00', null::time, 'Teatro Sociale', 'theatre'),
          ('Frecciarossa Brescia → Torino Porta Susa', date '2026-10-03', time '08:09', time '10:05', 'Brescia → Torino Porta Susa', 'personal'),
          ('Incontro con Daniele', date '2026-10-03', time '11:00', time '13:00', 'Via Fratelli Vasco 2C, Torino', 'personal'),
          ('Mostra Harry Gruyaert', date '2026-10-03', time '15:00', time '17:00', 'CAMERA, Via delle Rosine 18, Torino', 'personal'),
          ('Frecciarossa Torino Porta Susa → Brescia', date '2026-10-03', time '18:35', time '20:21', 'Torino Porta Susa → Brescia', 'personal'),
          ('Dentista Davo', date '2026-10-09', time '18:00', null::time, 'Davo', 'personal'),
          ('Storia Festival — Anna Foa — La distruzione del Tempio (con Paola)', date '2026-10-09', time '21:00', time '22:00', 'Teatro Grande', 'theatre'),
          ('Storia Festival — Luciano Canfora — La Dittatura giacobina (con Paola)', date '2026-10-10', time '21:00', time '22:00', 'Teatro Grande', 'theatre'),
          ('Storia Festival — Alessandra Bucossi — La Caduta di Costantinopoli', date '2026-10-11', time '11:00', time '12:00', 'Teatro Grande', 'theatre'),
          ('Storia Festival — Paola Rivetti — Teheran e la Repubblica Islamica', date '2026-10-11', time '15:30', time '16:30', 'Teatro Grande', 'theatre'),
          ('Storia Festival — Paolo Di Paolo — Giorni fatali nella grande Letteratura', date '2026-10-11', time '17:30', time '18:30', 'Teatro Grande', 'theatre'),
          ('Arrivato a questo punto', date '2026-10-23', time '20:30', null::time, 'Teatro Sociale', 'theatre'),
          ('Balletto (Paola)', date '2026-11-08', time '14:00', null::time, 'Teatro Grande', 'theatre'),
          ('Concerto Pappano', date '2026-11-11', time '21:00', null::time, 'Teatro Grande', 'theatre'),
          ('Non si sa come', date '2026-11-20', time '20:30', null::time, 'Teatro Sociale', 'theatre'),
          ('Emma B. vedova Giocasta', date '2026-11-27', time '20:30', null::time, 'Teatro Renato Borsoni', 'theatre'),
          ('Lirica', date '2026-11-28', time '15:30', null::time, 'Teatro Grande', 'theatre'),
          ('Cena dopo la lirica', date '2026-11-28', null::time, null::time, null::varchar, 'personal'),
          ('Prima del temporale', date '2026-12-04', time '20:30', null::time, 'Teatro Sociale', 'theatre'),
          ('Lirica', date '2026-12-13', time '15:30', null::time, 'Teatro Grande', 'theatre'),
          ('Network. Quinto potere', date '2027-01-15', time '20:30', null::time, 'Teatro Sociale', 'theatre'),
          ('Tre donne alte', date '2027-01-29', time '20:30', null::time, 'Teatro Mina Mezzadri', 'theatre'),
          ('La Mandragola', date '2027-02-05', time '20:30', null::time, 'Teatro Sociale', 'theatre'),
          ('Lo Zar', date '2027-02-19', time '20:30', null::time, 'Teatro Sociale', 'theatre'),
          ('Incendi', date '2027-02-26', time '20:30', null::time, 'Teatro Sociale', 'theatre'),
          ('Finale di partita', date '2027-03-05', time '20:30', null::time, 'Teatro Sociale', 'theatre'),
          ('Romeo e Giulietta', date '2027-03-19', time '20:30', null::time, 'Teatro Sociale', 'theatre'),
          ('La reginetta di Leenane', date '2027-04-09', time '20:30', null::time, 'Teatro Sociale', 'theatre'),
          ('La difficilissima storia della vita di Ciccio Speranza', date '2027-04-16', time '20:30', null::time, 'Teatro Renato Borsoni', 'theatre'),
          ('La rigenerazione', date '2027-04-23', time '20:30', null::time, 'Teatro Sociale', 'theatre'),
          ('Lisistrata', date '2027-05-14', time '20:30', null::time, 'Teatro Sociale', 'theatre')
    )
    insert into public.sb2_events
        (user_id, title, event_date, start_time, end_time, location, event_type)
    select
        v_user_id, d.title, d.event_date, d.start_time, d.end_time, d.location, d.event_type
      from event_data d
     where not exists (
        select 1
          from public.sb2_events e
         where e.user_id = v_user_id
           and e.event_date = d.event_date
           and e.start_time is not distinct from d.start_time
           and lower(e.title) = lower(d.title)
     );

    -- Allineamenti strategici: sono attivita' del progetto ARONA.
    with arona_tasks(title, due_date) as (
        values
          ('Allineamento team Arona', date '2026-09-22'),
          ('Allineamento team Arona', date '2026-09-29'),
          ('Allineamento team Arona', date '2026-10-06'),
          ('Allineamento team Arona', date '2026-10-13'),
          ('Allineamento team Arona', date '2026-10-20')
    )
    insert into public.sb2_tasks
        (user_id, project_id, title, status, priority, due_date, due_time, source)
    select
        v_user_id, v_arona_project_id, d.title, 'planned', 3, d.due_date, null, 'strategy'
      from arona_tasks d
     where not exists (
        select 1
          from public.sb2_tasks t
         where t.user_id = v_user_id
           and t.due_date = d.due_date
           and lower(t.title) = lower(d.title)
     );

    -- Promemoria e scadenze senza orario: dopo la scadenza diventeranno TODO.
    with deadline_tasks(title, due_date) as (
        values
          ('Bollo Audi', date '2027-04-15'),
          ('Verificare rinnovo tessera sanitaria — scadenza tra un mese', date '2027-04-17'),
          ('Scadenza tessera sanitaria', date '2027-05-17')
    )
    insert into public.sb2_tasks
        (user_id, title, status, priority, due_date, due_time, source)
    select
        v_user_id, d.title, 'planned', 3, d.due_date, null, 'manual'
      from deadline_tasks d
     where not exists (
        select 1
          from public.sb2_tasks t
         where t.user_id = v_user_id
           and t.due_date = d.due_date
           and lower(t.title) = lower(d.title)
     );
end $$;

commit;

-- Controllo finale. L'elenco da ripristinare comprende 40 elementi:
-- 32 eventi (uno dei quali era gia' presente) e 8 attivita'.
-- La query puo' mostrare ulteriori elementi gia' presenti nello stesso intervallo.
select event_date as data, start_time as ora, title, event_type as tipo
  from public.sb2_events
 where user_id = (
       select id from public.sb2_users
        where lower(email) = lower('owner@secondbrain.local')
        limit 1
   )
   and event_date between date '2026-09-22' and date '2027-05-17'
   and status not in ('completed', 'cancelled')
union all
select due_date as data, due_time as ora, title, source as tipo
  from public.sb2_tasks
 where user_id = (
       select id from public.sb2_users
        where lower(email) = lower('owner@secondbrain.local')
        limit 1
   )
   and due_date between date '2026-09-22' and date '2027-05-17'
   and status not in ('completed', 'cancelled')
order by data, ora nulls last, title;
