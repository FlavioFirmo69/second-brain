# Second Brain 0.28.3

## Inbox

La pagina distingue richieste da riprovare, appunti da contestualizzare e archivio. La lista precede il modulo compatto “＋ Appunto”, con ricerca, anteprime espandibili, modifica e collegamento a progetto/pratica. Le eliminazioni richiedono conferma.

I nuovi fallimenti LLM riportano il motivo disponibile. I vecchi elementi provenienti dall'assistente non distinguono sempre un comando fallito da una nota: sono contrassegnati come precedenti e la categoria è modificabile.

“Riprova richiesta” ritenta esplicitamente la richiesta, comprese le operazioni domandate nel suo testo. In caso di nuovo fallimento aggiorna la voce originale, senza duplicarla. Il risultato riuscito viene salvato nelle conversazioni esistenti e l'elemento passa all'archivio. Articoli e bozze mantengono il formato e i controlli di copia dell'Assistente. L'archiviazione manuale non esegue la richiesta.

Collegare un appunto conserva soltanto un riferimento al progetto o alla pratica nei metadati già esistenti dell'Inbox. Aprirlo nell'assistente permette di chiarirlo senza creare automaticamente attività. L'appunto resta da gestire finché non viene archiviato esplicitamente.

## Calendario

L'Agenda parte da oggi e mostra i giorni successivi in ordine crescente. Il primo giorno rimane visibile anche se non contiene impegni. Tornando alla vista Agenda si riparte da oggi; le frecce permettono ancora di consultare altri periodi.

## Installazione

Aggiornare i file e riavviare backend e frontend. Versione attesa: **0.28.3**. Non sono necessarie nuove migrazioni: vengono riutilizzati tabella Inbox, metadati e conversazioni esistenti.
