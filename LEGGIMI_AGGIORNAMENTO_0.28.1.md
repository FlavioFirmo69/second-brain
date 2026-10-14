# Second Brain 0.28.1

Aggiornamento del pacchetto di partenza 0.28.0, successivo alla versione di riferimento dell'utente 0.27.1.

- Consulente strategico trasversale con consiglio sulle attività gestite rispetto al profilo personale.
- Documento “Profili” modificabile e diario consultabile, con eliminazione delle singole voci.
- Eliminazione delle attività collegate, anche completate con date passate; correzione esplicita delle informazioni false, considerata nelle valutazioni successive.
- Generazione di articoli nella chat dedicata al libro con profilo autore, strategia e pulsante “Copia per Substack”.
- Navigazione con Profili e Diario sotto Consulente strategico. Sul telefono accesso fisso a Oggi, Calendario e Menu; apertura iniziale su Oggi.
- Ordinamento decrescente nella consultazione del calendario e riferimenti tecnici nascosti nelle risposte.
- Contesto del consiglio ridotto, errori del provider distinguibili e nessuna rielaborazione automatica della memoria quando viene chiesto consiglio.

## Installazione

Sovrascrivere i file aggiunti o modificati nel progetto esistente. Conservare `.env` e le dipendenze locali. Il pacchetto è parziale e include anche il frontend compilato.

Il database deve avere le migrazioni applicative precedenti fino alla 015. Applicare `016_strategic_memories.sql` e `017_personal_profile.sql` se non già applicate. Le successive modifiche di questa versione non richiedono nuove tabelle.

Riavviare backend e frontend. In Impostazioni, Informazioni applicazione, la versione attesa è **0.28.1**.

Per i dettagli sul consulente e sulle differenze tra diario, memoria e fonti ufficiali consultare `LEGGIMI_CONSULENTE_STRATEGICO.md`.
