-- Second Brain - estensione anagrafica libri per Supabase/PostgreSQL
-- Script idempotente: può essere eseguito più volte nel SQL Editor di Supabase.

alter table public.sb2_books add column if not exists genre varchar(120);
alter table public.sb2_books add column if not exists synopsis text;
alter table public.sb2_books add column if not exists themes text;
alter table public.sb2_books add column if not exists target_reader text;
alter table public.sb2_books add column if not exists positioning text;
alter table public.sb2_books add column if not exists differentiators text;
alter table public.sb2_books add column if not exists tone_notes text;

comment on column public.sb2_books.synopsis is 'Sinossi operativa usata come contesto editoriale';
comment on column public.sb2_books.themes is 'Temi principali del libro';
comment on column public.sb2_books.target_reader is 'Lettore ideale e pubblico di riferimento';
comment on column public.sb2_books.positioning is 'Posizionamento editoriale del libro';
comment on column public.sb2_books.differentiators is 'Elementi distintivi e promessa del libro';
comment on column public.sb2_books.tone_notes is 'Indicazioni specifiche di tono e voce per il libro';
