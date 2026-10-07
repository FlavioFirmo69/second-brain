# Second Brain 0.27.0

## Installazione
1. Eseguire in Supabase `database/015_work_conversations.sql`. Servono già lo schema 005 e le migrazioni precedenti, in particolare 013 e 014.
2. Sostituire i sorgenti backend e frontend con questo pacchetto, conservando il proprio `backend/.env`.
3. Riavviare il backend. Il frontend compilato è incluso in `frontend/dist`. Per sviluppo: `npm ci`, `npm run dev` nella cartella frontend.

## Nuove funzioni
- Dashboard iniziale: solo libri con strategia editoriale o piano operativo attivo; tutte le pratiche aperte. Il numero di schede viene dal database.
- Criticità, revisioni, prossime azioni, attività scadute e agenda comune dei prossimi sette giorni.
- Vendite mensili registrate confrontate con il mese precedente completo. Il confronto non equivale a una previsione. Nessun dato mancante viene interpretato come zero vendite effettive.
- Monitoraggio target dei piani approvati con checkpoint e controllo della copertura dei dati. Le strategie editoriali precedenti restano visibili con accesso ai dettagli, senza inventare una valutazione di andamento.
- Una conversazione dedicata persistente per libro o pratica, con titolo stabile, riutilizzata dal pulsante “Parla di questo lavoro”. Il contesto viene riletto dal database ad ogni messaggio. La chat dedicata propone senza creare automaticamente attività o modificare strategie; per approvare usare Piani e pratiche.
- L’assistente generale risponde al conteggio delle strategie attive e dei piani attivi, anche con il refuso “uante”.
- Chiusura pratica: archivia conversazione, annulla attività ed eventi aperti e chiude i piani operativi; completati e storico restano consultabili. Le pratiche chiuse non compaiono più nella dashboard.
- Eliminazione definitiva disponibile nella sezione Pratiche chiuse, con conferma: elimina pratica, conversazione dedicata e messaggi, piani, attività ed eventi. Non elimina altre conversazioni generali o il registro di audit storico.

## Verifica e limiti
Build TypeScript/Vite verificata e test unitari eseguiti. Test PostgreSQL di integrazione richiedono TEST_DATABASE_URL su database separato e non sono stati eseguiti sul database dell’utente. Nessuna verifica visiva in browser o chiamata a provider LLM reale.
Il progetto mantiene l’accesso tramite utente predefinito: non introduce autenticazione per un servizio pubblico.
Questo archivio esclude credenziali, .git, ambienti Python e node_modules. Non sostituire la propria configurazione con valori di esempio.
