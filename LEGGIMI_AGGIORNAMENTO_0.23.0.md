# Second Brain — aggiornamento 0.23.0 per la base 0.22.0

## Installazione

1. Conserva una copia del progetto e del database prima dell'aggiornamento.
2. Copia il contenuto di questo ZIP nella radice del progetto 0.22.0, mantenendo i percorsi e sovrascrivendo i file omonimi. Non modifica file `.env` o credenziali. Sono inclusi soltanto i file nuovi/modificati e la build frontend aggiornata.
3. Nel SQL Editor di Supabase esegui **database/013_planning_workflow.sql**. È una migrazione aggiuntiva e rieseguibile: non elimina o riscrive le strategie già presenti. Eseguila PRIMA di avviare il nuovo backend, anche perché le regole del calendario usano la nuova colonna `plan_id`.
4. Usa le dipendenze backend già previste in `backend/requirements.txt`. Se necessario: `python -m pip install -r backend/requirements.txt` nel relativo ambiente virtuale.
5. Per sviluppo o pubblicazione ricostruisci il frontend: da `frontend`, esegui `npm ci` e `npm run build`. Lo ZIP contiene anche `frontend/dist` già compilato. Riavvia backend e frontend o ripubblica con il tuo flusso abituale.
6. Apri **Piani e pratiche** dal menu. Se vedi la vecchia interfaccia, ricarica la pagina completamente.

Non eseguire di nuovo gli script di importazione o di seed delle vecchie vendite.

## Percorso per il nuovo libro

- Completa o modifica la scheda del libro in Editoria e seleziona l'autore corretto.
- In Piani e pratiche seleziona il libro. Scrivi obiettivo, quarter, target, budget, tempo disponibile e vincoli, quindi premi **Avvia bozza**.
- Il sistema conserva la richiesta e avvia il colloquio con l'agente. Rispondi alle domande. Puoi integrare o correggere le informazioni tramite nuovi messaggi.
- Premi **Genera / rigenera bozza**. La strategia presenta motivazioni, ipotesi da verificare, attività proposte, dipendenze, periodo e aspettative cumulative settimanali. Nessuna attività operativa viene creata.
- **Modifica bozza** consente di correggere tutti questi elementi tramite campi normali. Salva le modifiche prima di approvare. Per le strategie editoriali, l'ultimo checkpoint deve cadere alla fine del periodo e coincidere con il target; i checkpoint devono essere ordinati e le copie cumulative non possono diminuire.
- **Scarta bozza** non tocca il calendario. Puoi modificare la scheda del libro e ricominciare con una nuova bozza. Il sistema impedisce l'approvazione di una bozza basata su una scheda successivamente modificata.
- **Approva esplicitamente e calendarizza** crea gli elementi in una sola transazione. Una seconda approvazione dello stesso piano non genera duplicati. Per lo stesso libro o pratica può esistere un solo piano principale attivo.
- **Pulisci piano completamente** richiede una conferma nella schermata e annulla gli elementi aperti del piano e delle sue correzioni. Conserva le attività completate, le vendite e gli elementi manuali. Il monitoraggio del piano pulito non è più disponibile.
- **Ricomincia con una nuova bozza** conserva richiesta e colloquio precedenti, ma legge la scheda aggiornata quando genera il nuovo piano. Puoi aggiungere un messaggio per modificare l'obiettivo o i vincoli.

Le strategie storiche importate nella pagina Editoria restano separate: questo nuovo flusso opera sui nuovi piani creati in **Piani e pratiche**, senza convertire le vecchie strategie o ricostruire attività già eseguite.

## Vendite e correzioni

- Inserisci le vendite con la pagina Editoria esistente. Se registri un totale settimanale usa una sola registrazione per quel totale, senza aggiungerla alle righe giornaliere già incluse: questo aggiornamento non aggiunge un importatore o una riconciliazione automatica di aggregati settimanali.
- Nella strategia attiva conferma **Dati completi fino al**, anche per periodi senza vendite.
- Il controllo confronta vendite effettive e attese al più recente checkpoint raggiunto, soltanto se i dati sono confermati fino a quel checkpoint. Non interpreta un dato mancante come zero.
- Scostamento = `(copie effettive - copie attese) / copie attese × 100`. La soglia predefinita è 30%, modificabile e motivata dall'agente nella bozza; l'approvazione della bozza approva anche questa soglia. Un minimo di copie attese (predefinito 20) evita valutazioni premature su piccoli volumi.
- Lo stato viene ricalcolato quando apri un piano attivo, ogni 60 secondi mentre la pagina è aperta e con **Controlla andamento / Conferma dati e controlla**. Le nuove vendite vengono quindi considerate al prossimo controllo.
- Quando lo scostamento negativo raggiunge o supera la soglia, compare **Apri proposta di correzione**. Il sistema apre un piano correttivo con strategia originale, vendite, checkpoint e attività svolte/aperte come contesto. Prosegui con colloquio e generazione della bozza. Anche le correzioni richiedono approvazione esplicita.
- Il medesimo checkpoint non produce più proposte mediante ripetuti clic. Il target e le aspettative originali non vengono riscritti dalle correzioni; le loro azioni sono comprese nello storico e nella pulizia della strategia principale.

**Limiti espliciti:** non è incluso un job server pianificato, né notifiche quando l'applicazione è chiusa. Il calcolo è deterministico; le proposte LLM partono dai pulsanti della schermata. Non è stata verificata la qualità editoriale delle risposte del tuo modello/provider reale: i test usano risposte LLM simulate. Le dipendenze sono descritte e validate nella bozza, ma non bloccano automaticamente il completamento di un'attività. Non è inclusa una ricerca web automatica: per pratiche amministrative l'agente deve indicare i documenti/fonti da verificare e non considerare verificate le ipotesi fornite.

## Pratiche personali

- Crea una pratica con codice, titolo e contesto. Selezionandola puoi modificare la situazione e l'obiettivo.
- Aggiungi manualmente TODO (scadenza facoltativa) o eventi (data obbligatoria, orari e luogo facoltativi). Sono collegati automaticamente alla pratica e diventano subito operativi, senza approvazione del piano.
- Puoi anche avviare un piano dell'agente con il medesimo ciclo di colloquio, bozza, approvazione, pulizia e rigenerazione.
- Attività aperte e storico completate/annullate sono consultabili nella pratica. Il pulsante **Fatto** registra il completamento.

## Regole calendario e storico

Gli elementi collegati a `strategy_id`, `plan_id`, `project_id`, `case_id` o `book_id` non vengono più chiusi o privati della scadenza automaticamente perché la data è passata. Per considerarli svolti serve il completamento esplicito. Gli elementi completati dei nuovi piani e delle pratiche sono visibili nello storico dedicato.

Per gli impegni indipendenti resta il comportamento precedente di rimozione dalle viste operative tramite stato completato o conversione in TODO: non viene introdotta una cancellazione fisica dei record.

## Verifica del test di novembre

1. Genera una bozza del nuovo libro e controlla che il calendario non cambi.
2. Scartala, modifica la scheda, ricomincia e rigenera.
3. Approvala; ripeti l'approvazione e verifica che non ci siano duplicati.
4. Completa un'attività e controlla che sia nello storico.
5. A un checkpoint già raggiunto, registra vendite inferiori del 30% alle attese e conferma la copertura dei dati. Lo stato deve indicare lo scostamento.
6. Genera una correzione, poi approvala.
7. Pulisci la strategia principale: le sue attività aperte e quelle correttive devono risultare annullate; completate e vendite devono restare.
8. In una pratica aggiungi un TODO manuale e un evento; approva e pulisci un piano dell'agente. Gli elementi manuali devono restare.

Per simulare i checkpoint prima di novembre usa un libro dedicato al test e un periodo di prova con checkpoint già raggiunti, senza inserire vendite fittizie nei libri reali. Il sistema non permette di confermare dati di vendita futuri.

## Test inclusi

Da `backend`: `python -m pytest -q` esegue i test unitari. I test di integrazione vengono saltati se manca `TEST_DATABASE_URL`.

Per l'integrazione usa esclusivamente un database separato e sacrificabile, prepara lo schema 005 e la migrazione 013, quindi imposta `TEST_DATABASE_URL` e lancia pytest. I test inseriscono utenti, libri, vendite e attività di prova. Non usare il database reale.

Verifica svolta durante la preparazione: build TypeScript/Vite riuscita; 18 test passati (compreso quello originale), integrazione su PostgreSQL embedded compatibile via PGlite, migrazione SQL eseguita due volte con successo. Non è stata eseguita una prova sulla tua istanza Supabase o una verifica visuale nel browser.
