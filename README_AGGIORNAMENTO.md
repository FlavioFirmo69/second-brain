# Aggiornamento Second Brain

Questo archivio contiene file completi da sostituire nel progetto esistente.

## Installazione

1. Arrestare backend e frontend.
2. Estrarre lo ZIP dentro `C:\Sorgenti\second-brain`, mantenendo la gerarchia e confermando la sostituzione dei file.
3. Da PowerShell eseguire:

   ```powershell
   cd C:\Sorgenti\second-brain
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\install-windows.ps1
   powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\start-dev.ps1
   ```

L'installazione aggiorna anche le dipendenze Python; non servono modifiche al database.

## Novità incluse

- calendario con viste Giorno, Settimana, Mese e Agenda;
- filtro degli eventi per tipo e pulsante `Crea evento`;
- modifica ed eliminazione controllata degli eventi;
- comando `Fatto` per eventi e attività da Oggi e Calendario;
- regole automatiche per elementi scaduti, senza intervento dell'LLM;
- manuale Markdown delle regole mostrato in sola lettura nelle Impostazioni;
- inserimento vendite tramite campi strutturati, senza LLM;
- strategie più leggibili e mantenute in sola lettura;
- date visualizzate nel formato `dd/MM/yyyy`;
- comandi rapidi `todo: ...`, `stasera 19:00 ...` e `domani 09:30 ...`;
- azioni LLM controllate per creare eventi e attività;
- risposta Gemini vincolata da uno schema JSON;
- fallback leggibile se il provider restituisce comunque testo normale;
- tre tentativi automatici per errori temporanei `429` o `5xx`;
- configurazione di esempio per `gemini-3.6-flash`.

## Verifica rapida

- aprire `http://localhost:8000/api/health`;
- aprire `http://localhost:5173`;
- in Calendario provare `Crea evento` e le quattro viste;
- cliccare un evento per modificarlo, eliminarlo o dichiararlo `Fatto`;
- aprire Impostazioni e verificare il riquadro `Regole deterministiche`;
- in Editoria registrare una vendita di prova;
- nell'inserimento rapido provare `stasera 19:00 aperitivo`.
- con Gemini attivo provare `Riassumi in tre punti la strategia di Rubicone senza modificarla`.

Il file personale `backend\.env` non viene incluso né sovrascritto. Conservare la chiave già configurata e usare `LLM_MODEL=gemini-3.6-flash`.
