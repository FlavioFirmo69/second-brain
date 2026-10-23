# Aggiornamento 0.28.10 — Decisioni collegate alla strategia

Le schede di proposta mostrano il nome della strategia collegata, il profilo autore e il titolo del libro quando disponibili. Le etichette provengono dai record ufficiali; il legame usa gli identificativi della strategia esistente, senza creare copie di strategie o progetti.

Accettando una proposta, il backend verifica nuovamente che la strategia sia dell'utente e ancora attiva. Se non è più accessibile o attiva, blocca la registrazione e invita a rivalutare la proposta. Il diario riporta il nome leggibile della strategia e conserva il riferimento nei metadati della decisione, che vengono recuperati anche nei consigli successivi.

Per una proposta editoriale il solo riferimento al libro o al profilo autore non sostituisce la strategia. In caso di ambiguità, il consulente deve chiedere di precisare il legame. L'accettazione registra una decisione collegata: non cambia lo stato della strategia e non crea automaticamente attività, eventi o ricordi permanenti.

Nessuna nuova migrazione rispetto alla 0.28.6. Applicare i file e riavviare backend e frontend. Le etichette testuali nel diario documentano la decisione al momento della registrazione; lo stato corrente della strategia rimane nella fonte ufficiale.
