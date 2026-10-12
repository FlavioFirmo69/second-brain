# Second Brain 0.28.0

## Modifiche
- Finanze: Segna pagato / Segna incassato conferma il movimento e lo rimuove dalle previsioni. Il saldo effettivo resta aggiornabile manualmente.
- Tutti i movimenti contabili con data precedente a oggi vengono cancellati automaticamente, anche se non confermati.
- Eventi passati senza orario: conversione atomica in TODO senza data, conservando i collegamenti a pratica, progetto, libro, piano o strategia.
- Eventi passati con orario senza collegamenti: cancellazione.
- Eventi eseguiti senza collegamenti: cancellazione immediata; quelli collegati restano nello storico, esclusi dal calendario.
- I collegamenti editoriali (libro, piano, strategia) sono trattati come contesti da conservare, insieme a pratiche e progetti.
- Controllo dell'intero storico all'avvio, ogni 60 secondi mentre il backend resta attivo e durante la consultazione di calendario / finanze. La data di riferimento usa APP_TIMEZONE.
- Se il backend non è attivo (o in hosting serverless non riceve richieste), la pulizia avviene al successivo avvio / accesso.
- Piani e pratiche: progetti active, in_progress e draft visibili di default; Mostra tutti espone gli altri stati. Il filtro non modifica gli stati nel database.

## Installazione
Aggiornare i sorgenti e frontend/dist dal presente archivio, poi riavviare il backend. Nessuna nuova migrazione SQL: mantenere le migrazioni già richieste dalla versione 0.27.1 (inclusa la 013).
Il frontend compilato è incluso. Per ricompilare: dalla cartella frontend eseguire npm install e npm run build.
Il primo controllo gestirà anche i record molto vecchi secondo le regole sopra.

## Verifiche
- Frontend: npm run build riuscito.
- Backend: 26 test passati; 16 test di integrazione esistenti saltati perché TEST_DATABASE_URL non configurata.
- Query di pulizia verificate separatamente con motore PostgreSQL PGlite: storico remoto, eventi di oggi/futuri, contesti, eventi completati, isolamento utente, movimenti scaduti e ripetizione senza TODO duplicati.
- Nessuna connessione al database personale durante la verifica.
