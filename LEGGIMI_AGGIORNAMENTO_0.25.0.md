# Aggiornamento 0.25.0

Aggiornamento cumulativo con piani, pratiche, calendario finanziario e magazzino delle copie cartacee.

## Installazione
Copia le cartelle backend e frontend nel progetto. Esegui database/013_planning_workflow.sql se non già eseguito, poi database/014_book_inventory.sql nel database. Riavvia il backend. Il frontend compilato è incluso in frontend/dist.

## Magazzino
In Editoriale trovi Magazzino copie cartacee: registra libro, data e quantità acquistata da Amazon. Le vendite cartacee hanno una provenienza separata dal canale: esterna oppure dal mio magazzino. Solo queste ultime scalano la giacenza. Gli acquisti non sono vendite e non entrano nel monitoraggio dei target. Nessun importo monetario richiesto.
Eliminare una vendita restituisce le copie. Eliminare un acquisto è impedito se porterebbe la giacenza sotto zero. Per correggere una registrazione, eliminala e reinseriscila; se necessario correggi prima le vendite collegate. Le vendite precedenti restano esterne: nessuna giacenza viene dedotta retroattivamente.

## Verifica
Build TypeScript/Vite riuscita. 23 test passati su PostgreSQL emulato PGlite, incluse migrazioni ripetute, acquisto 30 copie, vendita interna 7 ed esterna 5, giacenza 23, vendite totali 12, controlli disponibilità e annullamenti. Nessuna verifica visiva in browser né verifica su database di produzione.
