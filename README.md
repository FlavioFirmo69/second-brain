# Second Brain

Applicazione personale con frontend React, API FastAPI e SQL Server come fonte ufficiale. La prima versione gira sul PC e usa un database SQL Server già esistente. Ogni oggetto creato nel database usa il prefisso `sb2_`.

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
- Microsoft ODBC Driver 18 for SQL Server;
- accesso al database SQL Server esistente;
- un account SQL dedicato con permessi sulle sole tabelle `sb2_`.

## 1. Preparare il database

Aprire SQL Server Management Studio, selezionare esplicitamente il database esistente e, nell’ordine, eseguire:

1. `database/001_create_sb2_tables.sql`
2. `database/002_seed_initial_data.sql`
3. `database/004_add_llm_conversations.sql`

Il primo script non contiene `CREATE DATABASE` e non opera su tabelle senza prefisso `sb2_`. Il seed è rieseguibile e inserisce lo stato iniziale soltanto quando assente.

`database/003_create_login_example.sql` è un esempio commentato: adattarlo alla policy del server. Non assegnare `db_owner` all’applicazione.

Lo script `004` è idempotente e aggiunge soltanto le tabelle `sb2_conversations` e `sb2_messages`; non crea utenti o login SQL.

## 2. Installare il progetto

Da PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\install-windows.ps1
```

Modificare quindi `backend/.env`:

```env
DB_SERVER=server.example.com,1433
DB_NAME=NomeDatabaseEsistente
DB_USER=second_brain_app
DB_PASSWORD=...
DB_ENCRYPT=yes
DB_TRUST_SERVER_CERTIFICATE=no
```

Se il certificato del server non è verificabile, correggere la configurazione TLS del server. Usare `DB_TRUST_SERVER_CERTIFICATE=yes` soltanto come test temporaneo.

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

I file in `config/defaults` documentano i valori iniziali; dopo il seed, la fonte ufficiale è SQL Server.

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

Il frontend è già responsive. Per usarlo dal telefono sarà sufficiente distribuire API e build del frontend online e aggiungere autenticazione. Nessun accesso diretto a SQL Server verrà mai inserito nel browser.
