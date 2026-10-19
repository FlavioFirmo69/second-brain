# Aggiornamento 0.28.6

Prima di avviare il backend aggiornato, eseguire sul database la migrazione `database/018_publication_timeline.sql`.

Editoria include una timeline grafica di dodici mesi, con una riga per profilo autore, filtro per profilo e selezione del mese iniziale. Ogni titolo mostra la sua data obiettivo; un elenco cronologico rende le previsioni consultabili anche dal telefono.

Nel modulo della timeline si sceglie un libro esistente e si salva una data obiettivo indipendente, con eventuali note. Selezionare un titolo nel grafico permette di modificarla. Svuotare la data rimuove la previsione. I nuovi titoli devono prima essere inseriti in Progetti → Nuovo libro.

Le previsioni non spostano altri titoli, non creano attività e non attestano una pubblicazione avvenuta. Le date di pubblicazione già registrate non vengono trasferite automaticamente. Il consulente riceve le previsioni come obiettivi e può valutarne il carico complessivo rispetto ai profili.

Questo aggiornamento non inserisce date o libri nel database.
