# Passaggio a Supabase

## 1. Configurazione locale

In `backend/.env` mantenere le variabili LLM già configurate e aggiungere:

```env
DATABASE_URL=postgresql://postgres.PROJECT:PASSWORD@HOST:6543/postgres?sslmode=require
DEFAULT_USER_EMAIL=owner@secondbrain.local
```

Usare la stringa **Shared pooler** di Supabase, porta `6543`. Se la password contiene
caratteri riservati nelle URL, codificarli prima di inserirla nella stringa.

Per la sola migrazione iniziale aggiungere anche le vecchie credenziali, preferibilmente
con i nomi `SOURCE_DB_*` mostrati in `backend/.env.migration.example`.

## 2. Aggiornamento ambiente Python

Dalla radice del progetto, con l'ambiente virtuale attivo:

```powershell
cd backend
python -m pip install -r requirements-migration.txt
cd ..
```

## 3. Controllo preventivo della migrazione

```powershell
python .\scripts\migrate_sqlserver_to_supabase.py --dry-run
```

Il comando mostra, per ogni tabella, quanti record esistono in SQL Server e quanti
sono già presenti in Supabase. Non scrive alcun dato.

## 4. Trasferimento dati

Fermare temporaneamente backend e frontend, quindi eseguire:

```powershell
python .\scripts\migrate_sqlserver_to_supabase.py
```

Gli UUID vengono conservati. Il comando usa `ON CONFLICT DO NOTHING`: può essere
rieseguito senza duplicare record con la stessa chiave o lo stesso vincolo univoco.

## 5. Test locale

```powershell
.\scripts\start-dev.ps1
```

Verificare nell'ordine:

1. `http://127.0.0.1:8000/api/health` restituisce `database: connected`;
2. la home mostra le conversazioni;
3. Oggi e Calendario mostrano gli elementi attesi;
4. Progetti, Editoria, Finanze e Inbox contengono i dati migrati;
5. creare e completare un'attività di prova.

## 6. Variabili Vercel

Nel progetto Vercel configurare almeno:

```text
DATABASE_URL
DEFAULT_USER_EMAIL
APP_ENV=production
APP_TIMEZONE=Europe/Rome
LLM_ENABLED
LLM_BASE_URL
LLM_API_KEY
LLM_MODEL
```

Non caricare mai `backend/.env` nel repository.

Vercel usa l'entrypoint dichiarato in `pyproject.toml`; la build genera
`frontend/dist` e FastAPI pubblica il frontend insieme alle API `/api/*`.
