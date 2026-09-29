-- STEP 1/2 - Adeguamento schema libreria, edizioni e vendite.
-- PostgreSQL / Supabase. Script idempotente.

begin;

alter table public.sb2_books
    add column if not exists promotion_status varchar(20) not null default 'none',
    add column if not exists source_system varchar(40) not null default 'manual',
    add column if not exists external_id varchar(120),
    add column if not exists publication_date_precision varchar(20) not null default 'unknown';

create unique index if not exists ux_sb2_books_external_source
    on public.sb2_books(source_system, external_id);

create table if not exists public.sb2_book_editions (
    id uuid primary key default gen_random_uuid(),
    book_id uuid not null references public.sb2_books(id) on delete cascade,
    format_code varchar(20) not null,
    status varchar(20) not null default 'unpublished',
    publication_date date,
    isbn varchar(32),
    notes varchar(500),
    source_system varchar(40) not null default 'manual',
    external_id varchar(120),
    created_at timestamptz(0) not null default now(),
    updated_at timestamptz(0) not null default now(),
    constraint ck_sb2_book_editions_format check (format_code in ('ebook','paperback')),
    constraint ck_sb2_book_editions_status check (status in ('unpublished','published','withdrawn')),
    constraint uq_sb2_book_editions_format unique (book_id,format_code)
);

create unique index if not exists ux_sb2_book_editions_external_source
    on public.sb2_book_editions(source_system, external_id);

alter table public.sb2_sales
    add column if not exists edition_id uuid references public.sb2_book_editions(id),
    add column if not exists source_system varchar(40) not null default 'manual',
    add column if not exists external_id varchar(160),
    add column if not exists imported_at timestamptz(0);

create index if not exists ix_sb2_sales_edition_date
    on public.sb2_sales(edition_id,sale_date);

create unique index if not exists ux_sb2_sales_external_source
    on public.sb2_sales(source_system,external_id);

-- Tabelle tecniche usate dal secondo script di importazione.
-- Vengono eliminate dal secondo script solo dopo un'importazione riuscita.
create table if not exists public.sb2_stage_legacy_books (
    external_id varchar(120) primary key,
    code varchar(80) not null,
    title varchar(500) not null,
    synopsis text,
    publication_date date,
    status varchar(30) not null,
    publication_date_precision varchar(20) not null
);

create table if not exists public.sb2_stage_legacy_ebook_sales (
    book_external_id varchar(120) not null,
    sale_date date not null,
    quantity integer not null,
    primary key(book_external_id,sale_date)
);

commit;

select
    to_regclass('public.sb2_book_editions') as tabella_edizioni,
    exists (
        select 1 from information_schema.columns
        where table_schema='public' and table_name='sb2_sales' and column_name='edition_id'
    ) as vendite_con_edizione,
    to_regclass('public.sb2_stage_legacy_books') as staging_libri,
    to_regclass('public.sb2_stage_legacy_ebook_sales') as staging_vendite;
