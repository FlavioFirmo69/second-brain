# Aggiornamento 0.27.1 — Inserimenti dalla chat dedicata

Pacchetto incrementale rispetto a 0.27.0: contiene solo file modificati o nuovi.
Copiare le cartelle nella radice del progetto e riavviare il backend. Il frontend compilato è incluso; se usi Vite la pagina si aggiorna dai sorgenti. Ricaricare la pagina del browser.
Non occorrono nuove migrazioni: la 015 della versione precedente deve essere già applicata.

Nella chat di Fruit (o di un altro lavoro) scrivere, per esempio:
“Crea un evento domani alle 10:00 per verificare l’errore numero DDT.”
L’assistente prepara un modulo con titolo, data, ora e luogo. Completarlo se necessario e premere “Conferma e inserisci”. L’evento viene creato nel calendario con case_id della pratica; per i libri viene salvato book_id. La pratica mostra gli elementi collegati e la dashboard li recupera al successivo aggiornamento.
Le attività senza data sono TODO, non eventi a calendario. Gli eventi richiedono una data. La proposta resta nel messaggio e l’inserimento richiede un solo click; una seconda conferma non crea duplicati. L’inserimento multiplo e la registrazione della conferma avvengono in una sola transazione.
Il nuovo comportamento vale anche nelle conversazioni già aperte: le precedenti risposte che negavano gli inserimenti non sono più valide. Chiedere nuovamente di preparare gli inserimenti per ottenere il modulo.

Verifica: 19 test unitari passati; build TypeScript/Vite riuscita. 15 test PostgreSQL saltati perché manca un database di test separato; provider LLM reale e interfaccia browser non verificati.
