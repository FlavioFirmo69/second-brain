# Consulente strategico trasversale

## Installazione

Applicare `database/016_strategic_memories.sql` e `database/017_personal_profile.sql` nel SQL Editor Supabase, dopo le migrazioni esistenti fino alla 015. Usare le credenziali backend già previste dal progetto: le nuove tabelle hanno RLS senza policy pubbliche, come le altre tabelle. Ricostruire il frontend e riavviare il backend. Il consulente usa la configurazione LLM esistente; non occorre un secondo servizio.

## Profilo personale visibile e modificabile

La pagina “Profilo e desideri”, raggiungibile anche dal consulente, mostra il documento ufficiale delle priorità trasversali dell'utente. È possibile leggerlo, modificarlo e affinare desideri, confini lavorativi, visione personale della scrittura, criteri per le consulenze e disponibilità di tempo. Finché non viene salvato, il modello iniziale è soltanto una traccia di titoli, senza preferenze inventate.

Il repository aveva profili autore per posizionamento, voce e privacy, ma non un documento personale trasversale. `sb2_personal_profiles` colma questa lacuna con un unico documento per utente, senza duplicare strategie editoriali o schede progetto. I profili autore sono mostrati dalla loro fonte attuale, con un pulsante per modificarli nella pagina Impostazioni.

Il consulente legge la versione salvata del documento a ogni turno, insieme alle altre fonti ufficiali. Il documento personale prevale sui vecchi ricordi per desideri e vincoli; non sostituisce lo stato ufficiale dei progetti. Il diario non lo riscrive automaticamente. Le modifiche vengono numerate e registrate nel change log esistente. Un controllo della revisione impedisce di sovrascrivere modifiche contemporanee da altre schede. Una bozza non salvata resta aperta quando si naviga tra le pagine dell'app; chiudere o ricaricare il browser può perderla.

## Fonti ufficiali individuate

Il repository usa PostgreSQL/Supabase tramite SQLAlchemy e `Repository`. Le entità ufficiali sono `sb2_projects` (obiettivi e note), `sb2_cases` (contesto delle pratiche), `sb2_plans` (brief, dialogo, bozza, condizioni e revisioni), `sb2_tasks`, `sb2_events`, `sb2_strategies`, `sb2_author_profiles`, `sb2_agent_prompt_versions` attive e `sb2_books`.

Sono recuperati anche canali, edizioni, vendite, obiettivi misurabili, acquisti di copie, conti, movimenti, saldi e inbox, per includere gli altri ambiti realmente disponibili nel repository. Le relazioni senza `user_id` vengono filtrate attraverso il profilo autore proprietario. Inbox e dialoghi sono testimonianze, non necessariamente fatti verificati: il modello deve distinguere le ipotesi dalle evidenze.

Il consulente le legge direttamente con query limitate all'utente configurato. Non usa le viste dashboard come unica fonte: queste escludono lavori non attivi e alcune informazioni di piano. La lettura diretta evita anche gli effetti di manutenzione del calendario presenti in alcuni metodi operativi del Repository.

L'archivio contiene schemi e seed, non una copia del database corrente. Fruit compare nel seed come pratica. Non è possibile dedurre da questi file lo stato attuale di Sigma, Fruit, del lavoro dipendente o della strategia personale. Il codice non inserisce esempi fittizi nel database e non usa nomi di progetto prestabiliti per il recupero.

## Comportamento

### Diario e richiesta di consiglio

Nella pagina del consulente sono disponibili “Registra nel diario” e “Consiglio sulle attività che sto gestendo”. Il primo conserva il racconto, produce un breve riscontro e attiva la memoria selettiva. Il secondo valuta trasversalmente progetti, pratiche, piani, attività, calendario e diario recente rispetto al documento personale, ai desideri e ai vincoli dell'utente. Si può richiedere questa valutazione anche senza compilare il testo: il pulsante usa una domanda generale esplicita. Una domanda scritta può orientare la valutazione, senza limitarla automaticamente al singolo episodio. Le richieste di consiglio non avviano la selezione della memoria e non appaiono come nuovi fatti nella vista diario.

La pagina “Diario” mostra i racconti originali in ordine cronologico inverso, con ricerca testuale, filtri di data e paginazione. Si può preparare una richiesta di consiglio complessivo o aprire la conversazione di un episodio; il pulsante per il consiglio sul singolo episodio è stato rimosso. Per la valutazione complessiva il backend legge inoltre fino a venti voci recenti del diario, per un massimo di 24.000 caratteri, da tutte le conversazioni dell'utente. Le testimonianze del diario non sostituiscono lo stato ufficiale.

Ogni voce dispone di “Elimina episodio” e di una conferma locale. Il backend elimina soltanto il messaggio utente corrispondente, dopo aver verificato proprietà e tipo diario, e registra l'operazione senza copiare il testo cancellato nel change log. Non elimina la conversazione o gli altri episodi. I ricordi strategici eventualmente già derivati restano gestibili separatamente tramite “Dimentica”; cancellare un episodio non equivale a cancellare ogni apprendimento precedente. Nessuna voce viene eliminata automaticamente durante i test o gli aggiornamenti.

Non viene creata una seconda tabella diario: la vista legge `sb2_messages` e `sb2_conversations`. I nuovi racconti sono marcati `strategic_diary`, le nuove domande `strategic_question`; sono mostrati anche i messaggi utente delle vecchie conversazioni strategiche, che non avevano questa distinzione. I filtri usano la data di registrazione nel fuso configurato dell'applicazione; la data raccontata nel testo non viene inventata. Questa funzionalità non richiede migrazioni ulteriori rispetto a 016 e 017.

### Installazione dall'archivio delle modifiche

Lo zip contiene soltanto file aggiunti o modificati rispetto a `second-brain.zip` originale, incluse tutte le modifiche del consulente, del profilo e del diario. Estrarre e sovrascrivere i file nella cartella `second-brain` già esistente. Non sostituire l'intero progetto con lo zip parziale. Applicare le migrazioni 016 e 017 se non già applicate e riavviare il backend. Il frontend compilato aggiornato è incluso; per lo sviluppo sono presenti anche i sorgenti. Non sono incluse credenziali, dipendenze o cartelle di cache.

La nuova pagina “Consulente strategico” chiama `/api/strategic/advice`. Ogni turno recupera tutte le fonti ufficiali elencate, incluse le relazioni e le sequenze dei piani, quindi la memoria trasversale; il modello identifica i contesti pertinenti e confronta la novità con gli obiettivi complessivi. I profili autore e le strategie restano disponibili anche quando la domanda riguarda il lavoro o la consulenza. Nessun contesto viene sostituito da una copia persistente.

Per il consiglio, il contesto inviato al modello usa proiezioni transitorie delle fonti ufficiali: mantiene integralmente il documento personale, i profili autore, i progetti e le pratiche, brief e draft dei piani e l'episodio selezionato. Per libri e calendario conserva i campi principali, ripristinando i dettagli completi quando è nominato il progetto, la pratica o il libro pertinente. Le vendite sono aggregate per libro come copie e numero di registrazioni, senza derivare ricavi. I vecchi snapshot e dialoghi dei piani non vengono rispediti come copia dello stato corrente. Lo storico è limitato ai trenta messaggi recenti e a 24.000 caratteri, senza tagliare i singoli messaggi. L'episodio selezionato resta recuperato per intero anche se più vecchio.

Il contesto non viene salvato come seconda memoria. Con database molto grandi occorrerà ampliare la selezione relazionale prima della chiamata LLM. I dettagli esclusi dalle proiezioni non devono essere inventati. I controlli di duplicazione della memoria continuano a leggere le fonti complete.

Gli errori del provider sono distinti tra configurazione mancante, credenziali, modello/indirizzo, quota, richiesta rifiutata, timeout, connessione e formato della risposta. Sono mostrati messaggi sanitizzati, senza chiavi, risposte grezze del provider o affermazioni inesatte di salvataggio nell'inbox. I messaggi system vengono riuniti in uno, conservandone il contenuto, per compatibilità tra provider.

Se il consiglio fallisce, il backend conserva la domanda ma non avvia una seconda chiamata di selezione della memoria al provider già fallito. Chiedere consiglio su un episodio già registrato non rielabora automaticamente il diario storico per creare ricordi. Una successiva selezione del diario importato richiede l'autorizzazione dell'utente.

Il consulente non dispone di funzioni per modificare progetti, attività o eventi. Riutilizza `sb2_conversations` e `sb2_messages` per lo storico e per il diario conversazionale. L'endpoint operativo della chat impedisce di proseguire una conversazione strategica attraverso l'assistente generale: va usata la pagina dedicata.

Il sistema dichiara esplicitamente le fonti che non è riuscito a leggere, indipendentemente dalla risposta del modello. Le query usano savepoint per permettere di recuperare le altre fonti dopo un errore PostgreSQL. Lo stato ufficiale prevale su storico e ricordi. Dati e documenti recuperati vengono trattati come contenuti, non come istruzioni.

## Memoria selettiva

### Eliminazione delle attività e correzione dei fatti

Il consulente recupera dal change log ufficiale anche le eliminazioni delle attività, incluse quelle completate e rimosse prima di questo aggiornamento. Il titolo di un'attività eliminata non può più essere usato come prova che il fatto sia avvenuto. L'eliminazione normale ritira un'evidenza; non dimostra da sola che il lavoro non sia stato fatto.

Nel comando “Elimina” di Progetti e Pratiche è disponibile l'opzione “Informazione non vera”, con un motivo facoltativo. Il motivo e la smentita sono registrati nello stesso change log dell'eliminazione, senza creare una copia dei progetti nella memoria. Ad esempio, eliminare “Pubblicato libro” con la nota “Il libro non è stato pubblicato” fornisce una correzione esplicita che prevale sulle precedenti affermazioni di diario, chat e ricordi. Il consulente la legge alla prossima richiesta di consiglio; l'eliminazione non avvia chiamate AI automatiche.

Se anche lo stato del catalogo libri riporta una pubblicazione incompatibile con la smentita, il consulente deve segnalare il disallineamento, senza presentare il fatto smentito come certo. Il catalogo e il diario non vengono riscritti automaticamente. Le eliminazioni non più attuali, perché l'attività è stata ripristinata, vengono escluse dal contesto delle correzioni. Non servono nuove migrazioni.

L'utente racconta liberamente la giornata nella chat, senza compilare schede o scegliere quali dati memorizzare. Il racconto completo viene conservato nello storico esistente. Dopo ogni turno il consulente estrae da zero a cinque candidati alla memoria, distinguendo gli episodi con valore strategico dai dettagli occasionali. Nessun dettaglio irrilevante diventa un ricordo durevole solo perché appare nella chat.

Ogni candidato deve contenere citazioni esatte delle testimonianze dell'utente, almeno una del turno corrente. Lo storico serve a chiarire i riferimenti; le precedenti risposte dell'assistente non sono prove. Le citazioni inventate, quelle troppo lunghe e quelle presenti soltanto nello storico vengono scartate. La motivazione salvata include una breve evidenza riferita dall'utente e la data di acquisizione, che non è necessariamente la data dell'episodio.

Il secondo controllo recupera nuovamente fonti ufficiali e ricordi, blocca duplicati esatti e valuta utilità futura, fedeltà alle testimonianze, duplicati semantici e copie di stato operativo. Una citazione autentica non basta se non sostiene l'interpretazione. Le preferenze non documentate non devono essere inventate. Ad esempio evitare il coinvolgimento AI durante un colloquio HR può sostenere un apprendimento coerente con il desiderio già noto di restare ai margini, ma non prova una decisione definitiva di HR e non modifica il progetto AI.

Il salvataggio automatico riutilizza la stessa tabella e la stessa validazione dell'endpoint `/api/strategic/memories`, mantenuto per compatibilità. Il modulo manuale è stato rimosso dalla pagina. Le informazioni effettivamente ricordate sono elencate nella risposta soltanto dopo il salvataggio riuscito. Se fonti, verifica o salvataggio non sono disponibili, il consulente dichiara che la selezione non è stata completata; il racconto resta nello storico. La migrazione 017 aggiunge esclusivamente il documento personale, non una seconda memoria strategica.

Il controllo semantico è affidato al modello e non costituisce una prova formale di assenza di duplicati. La barriera strutturale alle scritture operative è invece nel codice. Il salvataggio è serializzato per utente. La memoria conserva solo tipo, contenuto, motivazione con evidenza ed eventuali riferimenti `fonte:id`, verificati contro le entità dell'utente. Un ricordo si può eliminare con “Dimentica”, anche per sostituire una decisione ormai superata. Le correzioni conversazionali esplicite possono essere ricordate come correzioni; il consulente deve dar loro precedenza sulle vecchie interpretazioni personali, senza usarle per sovrascrivere stati ufficiali.

## Collaudo e limiti

`backend/tests/test_strategic.py` copre Sigma, sequenze Fruit, lavoro dipendente e tempo disponibile, visione di scrittore indipendente, decisione trasversale con riferimento, informazioni occasionali, duplicati, verifica non disponibile, fonti mancanti e letture isolate per utente. I test usano fonti sintetiche e risposte LLM controllate: verificano il percorso del contesto e le barriere alle scritture, non la qualità di un consiglio del modello reale.

Il collaudo del diario aggiunge una chat mista HR/caffè/spesa, citazioni inventate, evidenze soltanto storiche, preferenze non documentate, racconti occasionali e indisponibilità dell'estrazione dopo aver conservato il racconto.

Prima dell'uso operativo verificare con il database e il modello configurati che i profili personali contengano davvero la visione desiderata e che i piani ufficiali rappresentino le condizioni di Sigma e Fruit. Il consulente non può ricostruire priorità o vincoli assenti dalle fonti.
