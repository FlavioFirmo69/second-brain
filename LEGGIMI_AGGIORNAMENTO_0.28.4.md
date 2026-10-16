# Second Brain 0.28.4

Editoria apre direttamente “Vendite e target”, con una sola scheda per ogni pubblicazione. Sono rimossi gli elenchi separati “Schede libri” e “Magazzino copie cartacee”.

La scheda chiusa espone titolo, autore, stato editoriale reale (published, draft, writing e altri stati), copie vendute e target, ripartizione ebook/cartaceo e disponibilità del magazzino. La lista include anche le pubblicazioni senza target o senza vendite; sono disponibili ricerca e filtro per stato.

Espandendo il libro si accede alla stessa anagrafica modificabile, ai dettagli editoriali, ai progetti e alle strategie collegate. Nella stessa scheda è possibile registrare vendite, scegliere la provenienza delle copie cartacee, caricare acquisti di copie autore e consultare o eliminare vendite e acquisti. Il libro è già selezionato implicitamente, per evitare di registrare operazioni su un titolo diverso.

Lo storico vendite viene recuperato per il singolo libro e mostra le sue ultime 50 registrazioni. Gli acquisti sono associati tramite codice libro, non tramite titolo, così titoli uguali di autori diversi non vengono mescolati. Magazzino a zero e pubblicazioni senza movimenti restano visibili.

Il monitoraggio e i testi delle strategie restano disponibili sotto la lista unificata. Non vengono duplicati dati nel database.

Aggiornare backend e frontend insieme e riavviarli. Versione attesa: **0.28.4**. Non servono nuove migrazioni.
