/*
  Second Brain - schema PostgreSQL per Supabase

  Eseguire nel SQL Editor del progetto Supabase.
  - Non crea o elimina il database.
  - Crea soltanto oggetti con prefisso sb2_.
  - E' rieseguibile: CREATE TABLE/INDEX usa IF NOT EXISTS.
  - Abilita RLS senza policy pubbliche: l'accesso avviene dal backend server-side.
*/

begin;

-- Mantiene i campi JSON come testo, compatibili con il backend attuale,
-- ma rifiuta valori che non contengono JSON valido.
create or replace function public.sb2_is_valid_json(value text)
returns boolean
language plpgsql
immutable
strict
as $function$
begin
    perform value::jsonb;
    return true;
exception when others then
    return false;
end
$function$;

create table if not exists public.sb2_users (
    id uuid primary key default gen_random_uuid(),
    email varchar(320) not null unique,
    display_name varchar(160) not null,
    timezone varchar(64) not null default 'Europe/Rome',
    is_active boolean not null default true,
    created_at timestamptz(0) not null default now(),
    updated_at timestamptz(0) not null default now()
);

create table if not exists public.sb2_author_profiles (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.sb2_users(id),
    code varchar(40) not null,
    display_name varchar(160) not null,
    is_pseudonym boolean not null default false,
    positioning varchar(1000),
    voice_markdown text not null default '',
    privacy_markdown text not null default '',
    is_active boolean not null default true,
    created_at timestamptz(0) not null default now(),
    updated_at timestamptz(0) not null default now(),
    constraint uq_sb2_profiles_code unique (user_id, code)
);

create table if not exists public.sb2_agent_prompt_versions (
    id uuid primary key default gen_random_uuid(),
    author_profile_id uuid not null references public.sb2_author_profiles(id),
    version_number integer not null,
    content_markdown text not null,
    change_reason varchar(500),
    is_active boolean not null default false,
    created_at timestamptz(0) not null default now(),
    constraint uq_sb2_prompt_version unique (author_profile_id, version_number)
);

create unique index if not exists ux_sb2_prompt_one_active
    on public.sb2_agent_prompt_versions(author_profile_id)
    where is_active = true;

create table if not exists public.sb2_channels (
    id uuid primary key default gen_random_uuid(),
    author_profile_id uuid not null references public.sb2_author_profiles(id),
    code varchar(40) not null,
    display_name varchar(100) not null,
    is_active boolean not null default true,
    created_at timestamptz(0) not null default now(),
    constraint uq_sb2_channels_code unique (author_profile_id, code)
);

create table if not exists public.sb2_books (
    id uuid primary key default gen_random_uuid(),
    author_profile_id uuid not null references public.sb2_author_profiles(id),
    code varchar(60) not null unique,
    title varchar(500) not null,
    status varchar(30) not null,
    publication_date date,
    format_notes varchar(500),
    created_at timestamptz(0) not null default now(),
    updated_at timestamptz(0) not null default now()
);

create table if not exists public.sb2_strategies (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.sb2_users(id),
    author_profile_id uuid references public.sb2_author_profiles(id),
    book_id uuid references public.sb2_books(id),
    code varchar(80) not null,
    title varchar(250) not null,
    content_markdown text not null,
    status varchar(30) not null default 'active',
    version_number integer not null default 1,
    created_at timestamptz(0) not null default now(),
    updated_at timestamptz(0) not null default now(),
    constraint uq_sb2_strategies_code unique (user_id, code)
);

create table if not exists public.sb2_projects (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.sb2_users(id),
    author_profile_id uuid references public.sb2_author_profiles(id),
    book_id uuid references public.sb2_books(id),
    code varchar(80) not null,
    title varchar(250) not null,
    status varchar(30) not null,
    objective text,
    notes_markdown text not null default '',
    created_at timestamptz(0) not null default now(),
    updated_at timestamptz(0) not null default now(),
    constraint uq_sb2_projects_code unique (user_id, code)
);

create table if not exists public.sb2_cases (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.sb2_users(id),
    code varchar(80) not null,
    title varchar(250) not null,
    status varchar(30) not null,
    context_markdown text not null default '',
    created_at timestamptz(0) not null default now(),
    updated_at timestamptz(0) not null default now(),
    constraint uq_sb2_cases_code unique (user_id, code)
);

create table if not exists public.sb2_tasks (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.sb2_users(id),
    project_id uuid references public.sb2_projects(id),
    case_id uuid references public.sb2_cases(id),
    author_profile_id uuid references public.sb2_author_profiles(id),
    book_id uuid references public.sb2_books(id),
    title varchar(500) not null,
    description text,
    status varchar(30) not null default 'open',
    priority smallint not null default 3,
    due_date date,
    due_time time(0),
    completed_at timestamptz(0),
    source varchar(50) not null default 'manual',
    created_at timestamptz(0) not null default now(),
    updated_at timestamptz(0) not null default now(),
    constraint ck_sb2_tasks_status check (
        status in ('open', 'planned', 'in_progress', 'blocked', 'to_verify', 'completed', 'cancelled')
    ),
    constraint ck_sb2_tasks_priority check (priority between 0 and 255)
);

create index if not exists ix_sb2_tasks_open_due
    on public.sb2_tasks(user_id, status, due_date);

create table if not exists public.sb2_events (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.sb2_users(id),
    project_id uuid references public.sb2_projects(id),
    author_profile_id uuid references public.sb2_author_profiles(id),
    book_id uuid references public.sb2_books(id),
    title varchar(500) not null,
    event_date date not null,
    start_time time(0),
    end_time time(0),
    location varchar(500),
    status varchar(30) not null default 'planned',
    event_type varchar(40) not null default 'personal',
    created_at timestamptz(0) not null default now(),
    updated_at timestamptz(0) not null default now()
);

create index if not exists ix_sb2_events_date
    on public.sb2_events(user_id, event_date, start_time);

create table if not exists public.sb2_sales (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.sb2_users(id),
    book_id uuid not null references public.sb2_books(id),
    sale_date date not null,
    quantity integer not null,
    channel varchar(100),
    notes varchar(500),
    created_at timestamptz(0) not null default now(),
    constraint ck_sb2_sales_quantity check (quantity > 0)
);

create index if not exists ix_sb2_sales_book_date
    on public.sb2_sales(book_id, sale_date);

create table if not exists public.sb2_targets (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.sb2_users(id),
    author_profile_id uuid references public.sb2_author_profiles(id),
    book_id uuid references public.sb2_books(id),
    metric_code varchar(80) not null,
    target_value numeric(18,2) not null,
    warning_value numeric(18,2),
    target_date date not null,
    notes varchar(500),
    created_at timestamptz(0) not null default now()
);

create table if not exists public.sb2_accounts (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.sb2_users(id),
    code varchar(60) not null,
    display_name varchar(160) not null,
    account_type varchar(40) not null,
    currency char(3) not null default 'EUR',
    include_in_projection boolean not null default true,
    is_active boolean not null default true,
    created_at timestamptz(0) not null default now(),
    constraint uq_sb2_accounts_code unique (user_id, code)
);

create table if not exists public.sb2_transactions (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.sb2_users(id),
    account_id uuid not null references public.sb2_accounts(id),
    transaction_date date not null,
    description varchar(500) not null,
    amount numeric(18,2) not null,
    status varchar(20) not null,
    is_recurring boolean not null default false,
    created_at timestamptz(0) not null default now(),
    confirmed_at timestamptz(0),
    constraint ck_sb2_transactions_status check (status in ('planned', 'confirmed', 'cancelled'))
);

create index if not exists ix_sb2_transactions_date
    on public.sb2_transactions(account_id, status, transaction_date);

create table if not exists public.sb2_balance_checks (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.sb2_users(id),
    account_id uuid not null references public.sb2_accounts(id),
    balance_date date not null,
    balance numeric(18,2) not null,
    previous_balance numeric(18,2),
    reconciliation_amount numeric(18,2),
    notes varchar(500),
    created_at timestamptz(0) not null default now()
);

create index if not exists ix_sb2_balance_latest
    on public.sb2_balance_checks(account_id, balance_date desc, created_at desc);

create table if not exists public.sb2_inbox (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.sb2_users(id),
    source varchar(40) not null default 'desktop',
    text text not null,
    status varchar(30) not null default 'new',
    interpretation_json text,
    created_at timestamptz(0) not null default now(),
    processed_at timestamptz(0),
    constraint ck_sb2_inbox_status check (status in ('new', 'interpreted', 'confirmed', 'cancelled')),
    constraint ck_sb2_inbox_json check (
        interpretation_json is null or public.sb2_is_valid_json(interpretation_json)
    )
);

create table if not exists public.sb2_change_log (
    id bigint generated by default as identity primary key,
    user_id uuid references public.sb2_users(id),
    entity_type varchar(80) not null,
    entity_id uuid,
    action varchar(60) not null,
    before_json text,
    after_json text,
    source varchar(50) not null default 'api',
    created_at timestamptz(0) not null default now(),
    constraint ck_sb2_log_before_json check (
        before_json is null or public.sb2_is_valid_json(before_json)
    ),
    constraint ck_sb2_log_after_json check (
        after_json is null or public.sb2_is_valid_json(after_json)
    )
);

create index if not exists ix_sb2_log_entity
    on public.sb2_change_log(entity_type, entity_id, created_at desc);

create table if not exists public.sb2_conversations (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references public.sb2_users(id),
    title varchar(250) not null default 'Nuova conversazione',
    status varchar(20) not null default 'active',
    created_at timestamptz(0) not null default now(),
    updated_at timestamptz(0) not null default now(),
    constraint ck_sb2_conversations_status check (status in ('active', 'archived'))
);

create index if not exists ix_sb2_conversations_user_updated
    on public.sb2_conversations(user_id, updated_at desc);

create table if not exists public.sb2_messages (
    id uuid primary key default gen_random_uuid(),
    conversation_id uuid not null references public.sb2_conversations(id) on delete cascade,
    role varchar(20) not null,
    content_markdown text not null,
    message_kind varchar(40) not null default 'text',
    metadata_json text,
    created_at timestamptz(0) not null default now(),
    constraint ck_sb2_messages_role check (role in ('user', 'assistant', 'system')),
    constraint ck_sb2_messages_json check (
        metadata_json is null or public.sb2_is_valid_json(metadata_json)
    )
);

create index if not exists ix_sb2_messages_conversation_created
    on public.sb2_messages(conversation_id, created_at, id);

-- Nessuna policy pubblica: anon/authenticated non possono leggere o modificare i dati.
do $rls$
declare
    table_name text;
begin
    foreach table_name in array array[
        'sb2_users', 'sb2_author_profiles', 'sb2_agent_prompt_versions',
        'sb2_channels', 'sb2_books', 'sb2_strategies', 'sb2_projects',
        'sb2_cases', 'sb2_tasks', 'sb2_events', 'sb2_sales', 'sb2_targets',
        'sb2_accounts', 'sb2_transactions', 'sb2_balance_checks', 'sb2_inbox',
        'sb2_change_log', 'sb2_conversations', 'sb2_messages'
    ]
    loop
        execute format('alter table public.%I enable row level security', table_name);
    end loop;
end
$rls$;

commit;
