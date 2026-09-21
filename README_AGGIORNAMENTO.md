# Aggiornamento Second Brain — Supabase

Questo archivio contiene il progetto completo predisposto per PostgreSQL/Supabase e Vercel.

## Sostituzione dei file

1. Arrestare backend e frontend.
2. Conservare una copia del proprio `backend\.env`: non è incluso nello ZIP.
3. Estrarre lo ZIP nella cartella che contiene il progetto.
4. Copiare i file della nuova cartella `second-brain` sopra `C:\Sorgenti\second-brain`.
5. Non cancellare il proprio `.env`.

## Ordine delle operazioni

Le 19 tabelle Supabase devono essere già presenti tramite
`database/005_create_supabase_tables.sql`. Poi seguire integralmente
`README_SUPABASE.md`:

1. aggiornare l'ambiente Python;
2. eseguire la simulazione della migrazione;
3. trasferire i dati da SQL Server;
4. avviare e collaudare l'app localmente;
5. solo dopo il collaudo pubblicare su Vercel.

## Contenuti principali

- backend convertito dalle query SQL Server a PostgreSQL;
- driver `psycopg` compatibile con Supabase e Vercel;
- importatore idempotente SQL Server → Supabase;
- configurazione Vercel per FastAPI e frontend Vite;
- tutte le funzioni applicative e grafiche della versione precedente.
