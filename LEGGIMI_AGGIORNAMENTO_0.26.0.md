# Aggiornamento 0.26.0

Pacchetto cumulativo. Copiare backend e frontend e riavviare il backend. Frontend compilato incluso. Nessuna nuova migrazione rispetto alla 0.25: le migrazioni 013 e 014 servono solo se non già eseguite.

Modifiche: corretta la ricerca calendario che intercettava frasi contenenti “quando ho” dentro post e prompt lunghi; prompt Assistente alto cinque righe; modulo movimenti finanziari su due colonne con importo più ampio e disposizione singola su schermi piccoli; riepilogo magazzino limitato ai titoli con copie disponibili maggiori di zero. Il modulo di acquisto permette ancora tutti i titoli.

La correzione calendario riguarda questa specifica regola: non introduce una modalità conversazione distinta. Le risposte editoriali richiedono il provider LLM già configurato. Nessuna verifica visiva in browser.

Verifica: build TypeScript/Vite riuscita; 9 test unitari passati, inclusi colloquio con testo contenente “quando ho” e domanda autonoma calendario. Test database non rieseguiti per queste modifiche.
