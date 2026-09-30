# Second Brain 0.24.0 — aggiornamento cumulativo

Questo ZIP contiene i file nuovi/modificati rispetto alla base 0.22.0, incluse le funzioni della 0.23.0 e gli aggiornamenti concordati successivamente.

## Installazione

1. Copia i file nella radice del progetto mantenendo le cartelle e sostituisci gli omonimi. Credenziali e file `.env` non sono inclusi.
2. Se hai già eseguito con successo `database/013_planning_workflow.sql`, non ci sono nuove migrazioni da eseguire. Se provieni dalla 0.22.0 o non hai ancora eseguito la 013, eseguila nel SQL Editor di Supabase PRIMA dell'avvio.
3. Riavvia il backend. Per sviluppo/nuova pubblicazione, da `frontend` esegui `npm ci` e `npm run build`. È inclusa anche la build `frontend/dist` aggiornata.
4. Ricarica completamente il browser.

## Progetti e pratiche

La pagina **Piani e pratiche** torna a due pannelli affiancati: Progetti e Pratiche, con schede compatte, stato e conteggio degli elementi aperti. Le funzioni complete compaiono quando espandi una scheda e premi **Apri pratica** oppure **Apri libro e strategia**.

La pagina Progetti precedente conserva il suo layout e la creazione dei progetti/libri: nelle sue schede sono aggiunti gli stessi collegamenti per aprire il dettaglio. Il pulsante **Nuovo** del pannello Progetti nella pagina Piani e pratiche conduce alla creazione già esistente. Per una pratica usa **Nuova** nel pannello Pratiche.

Nel dettaglio rimangono disponibili contesto, elementi manuali, colloquio, bozze modificabili, approvazione, pulizia/rigenerazione e storico. Gli elementi manuali diventano operativi immediatamente; quelli proposti dall'agente solo dopo approvazione.

## Creazione dall'assistente

Scrivi ad esempio: **Apri una nuova pratica per regolarizzare la mia posizione contributiva**, seguito dalla situazione e dall'obiettivo.

L'assistente presenta titolo, riepilogo e massimo tre domande iniziali. Premi **Conferma creazione e apri pratica** per salvare e aprire la pratica. Nessuna attività viene calendarizzata da questa conferma. Se ignori la proposta, non viene creata una pratica.

Se il titolo coincide con una pratica esistente dell'utente, viene proposto il collegamento per aprirla. Anche ripetendo la conferma della stessa proposta non vengono creati duplicati. Non è implementato un riconoscimento semantico di titoli diversi: eventuali pratiche con nomi diversi ma stesso argomento vanno valutate dall'utente.

Il testo originale, il riepilogo e le domande vengono conservati nel contesto della pratica. Dopo la conferma rispondi alle domande/inserisci informazioni nel dettaglio e avvia il colloquio del piano. La proposta iniziale e il colloquio del piano sono fasi distinte; non viene ancora mantenuto un unico colloquio continuo fra la chat generale e il dettaglio.

Questa funzione richiede il provider LLM configurato già previsto dall'applicazione. La creazione manuale resta disponibile indipendentemente dal modello.

## Eventi finanziari nel calendario

Sono visibili i movimenti con stato **planned**, letti direttamente da `sb2_transactions`, appartenenti all'utente e al conto dello stesso utente, nell'intervallo visualizzato. Non vengono create copie in `sb2_events`.

- Visibili in Agenda, Giorno, Settimana e Mese.
- Etichetta € con descrizione, entrata/uscita e importo.
- Filtro **Finanziari**.
- Pulsante **Dettaglio €**: mostra data, conto, importo e stato, con collegamento a Finanze.
- Nessun pulsante Fatto o assegnazione a progetto/pratica per un movimento finanziario: non è un'attività.

Sono esclusi movimenti confermati/annullati e rilevazioni del saldo, che non rappresentano scadenze finanziarie pianificate. Le modifiche ai movimenti si riflettono al ricaricamento dei dati del calendario; questa versione non aggiunge una modifica dei movimenti dal calendario.

## Verifiche e limiti

Build TypeScript/Vite completata. 22 test backend superati, incluse prove di integrazione su PostgreSQL embedded compatibile (PGlite): approvazione e pulizia, conservazione del manuale e storico, monitoraggio, conferma idempotente delle pratiche, movimenti finanziari e conteggi dei progetti.

Il LLM è simulato nei test: non è stata effettuata una prova con il tuo provider reale o sulla tua istanza Supabase. Non è stata completata una verifica visiva nel browser in questo ambiente.

Rimangono i limiti della 0.23.0: nessuno scheduler per l'applicazione chiusa e nessuna ricerca web automatica. Il documento 0.23.0 nello ZIP descrive il flusso dei piani e il test del lancio; per layout, creazione dall'assistente e calendario finanziario prevale questo documento 0.24.0.
