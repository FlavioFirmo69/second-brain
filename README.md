# Second Brain

Applicazione personale con frontend React, API FastAPI e PostgreSQL/Supabase. Ogni oggetto applicativo nel database usa il prefisso `sb2_`.

Per il passaggio da SQL Server a Supabase e la pubblicazione su Vercel vedere **`README_SUPABASE.md`**.

## Funzioni incluse

- home Assistente con conversazioni LLM persistenti;
- risposte operative in chat per `oggi`, `settimana` e `saldo`, con completamento rapido di attività ed eventi;
- dashboard Oggi e Settimana;
- calendario operativo e TODO;
- completamento delle attività;
- progetti e pratiche;
- profili autoriali Flavio/Cesare modificabili e versionati;
- strategie di autore e di libro;
- vendite e confronto con i target;
- saldo, riconciliazioni e proiezioni;
- inbox per note rapide;
- comando deterministico per `oggi`, `settimana`, `saldo`, `comandi`, note e vendite;
- gateway LLM opzionale per richieste non deterministiche;
- esportazione Markdown.

## Prerequisiti Windows

- Python 3.12 o successivo;
- Node.js 20 o successivo;
- progetto Supabase con le 19 tabelle `sb2_`;
- stringa Shared pooler Supabase;
- Microsoft ODBC Driver 17/18 e accesso al vecchio SQL Server soltanto per la migrazione iniziale.

## 1. Preparare Supabase

Aprire il SQL Editor di Supabase ed eseguire:

1. `database/005_create_supabase_tables.sql`

Lo script è rieseguibile, non elimina dati e abilita RLS senza policy pubbliche.

## 2. Installare il progetto

Da PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install-windows.ps1
```

Modificare quindi `backend/.env`:

```env
DATABASE_URL=postgresql://postgres.PROJECT:PASSWORD@HOST:6543/postgres?sslmode=require
```

La stringa deve essere quella **Shared pooler** di Supabase e non deve essere pubblicata su GitHub.

## 3. Avviare

```powershell
.\scripts\start-dev.ps1
```

- interfaccia: `http://localhost:5173`
- API: `http://127.0.0.1:8000`
- documentazione API: `http://127.0.0.1:8000/docs`
- test connessione: `http://127.0.0.1:8000/api/health`

L’API è vincolata a `127.0.0.1`: non è raggiungibile dal cellulare o da Internet. Per la futura pubblicazione serviranno autenticazione, HTTPS e hosting dedicato.

## LLM opzionale

I comandi semplici non chiamano alcun modello. Per abilitare un servizio compatibile con l’endpoint `/v1/chat/completions`:

```env
LLM_ENABLED=true
LLM_BASE_URL=https://provider.example/v1
LLM_API_KEY=...
LLM_MODEL=...
```

Se l’LLM non è configurato, una richiesta complessa viene salvata nell’inbox invece di essere persa.

La home **Assistente** conserva conversazioni e risposte nel database. Le pagine **Oggi**, **Calendario**, **Editoria** e **Finanze** restano deterministiche. Le bozze articolo sono mostrate con formattazione editoriale e il pulsante **Copia per Substack** inserisce negli appunti sia HTML formattato sia testo semplice.

## Modificare la voce degli autori

Aprire **Impostazioni → Profili autoriali**. Ogni salvataggio:

1. disattiva la versione precedente;
2. crea una nuova versione in `sb2_agent_prompt_versions`;
3. aggiorna il profilo attivo;
4. registra la modifica nel change log.

I file in `config/defaults` documentano i valori iniziali; la fonte ufficiale è Supabase.

## Esportazione Markdown

Con il backend configurato:

```powershell
.\backend\.venv\Scripts\python.exe .\scripts\export_markdown.py
```

I file vengono creati sotto `exports/<data>/`.

## Test

```powershell
Set-Location backend
.\.venv\Scripts\pytest.exe
```

## Passaggio futuro al cellulare

Il frontend è responsive. Database e chiavi restano accessibili esclusivamente al backend: nessuna credenziale viene inserita nel browser.
