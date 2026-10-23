# Aggiornamento 0.28.7 — Affidabilità del consulente

Le chiamate AI ritentano anche timeout e interruzioni di rete, oltre agli errori temporanei del provider. I tentativi sono limitati a tre, senza ritentare errori di credenziali o richieste non valide. L'attesa indicata dal provider viene rispettata fino a 30 secondi. Il tempo per ciascun tentativo è configurabile tramite LLM_TIMEOUT_SECONDS (90 secondi per impostazione predefinita).

Il contesto del consiglio esclude le attività annullate e lo storico concluso precedente a 30 giorni, salvo collegamenti espliciti alla domanda. Le attività aperte rimangono disponibili anche se scadute. Restano integri profilo personale, ricordi, piani, condizioni, correzioni e date previste. Il contesto dichiara le omissioni, che non rappresentano cancellazioni dal database. La verifica dei nuovi ricordi mantiene il contesto storico completo.

Le vecchie risposte di indisponibilità vengono escluse dallo storico inviato al modello. Durante l'attesa il consulente mostra un messaggio sullo stato della richiesta. I motivi di errore rimangono distinti: credenziali, quota, modello, connessione, timeout o risposta non valida.

Non sono necessarie nuove migrazioni del database rispetto alla versione 0.28.6. Applicare i file aggiornati e riavviare backend e frontend. Nessuna configurazione privata o dato applicativo viene modificato dall'aggiornamento.

Verifica: 108 test superati, 16 test di integrazione saltati. Una chiamata sintetica al provider configurato ha ricevuto risposta; diario e profilo non sono stati trasmessi nella prova. Non costituisce una verifica dal vivo di tutte le richieste strategiche.
