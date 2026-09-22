# Regole deterministiche

Queste regole sono applicate dal backend senza consultare l'LLM. Producono sempre lo stesso risultato a parità di dati e orario.

## Calendario e attività

- Un'attività scaduta **senza orario** perde la vecchia data e torna nei **TODO senza data**.
- Un'attività scaduta **con orario** viene contrassegnata come completata e rimossa dalle viste operative.
- Un evento passato **con orario** viene contrassegnato come completato e rimosso da Oggi e Calendario.
- Un evento passato **senza orario** viene trasformato in un TODO senza data, conservando l'eventuale collegamento a progetto o pratica; l'evento originale viene chiuso.
- Gli elementi con stato `completed` o `cancelled` non vengono mostrati nelle viste operative.
- Il comando **Fatto** chiude immediatamente l'attività o l'evento selezionato.
- L'eliminazione di un evento usa lo stato `cancelled`: non effettua una cancellazione fisica dal database.

## Inserimento e modifica

- Titolo e data sono obbligatori per creare un evento.
- Ora, luogo e tipo sono facoltativi.
- Le modifiche manuali passano sempre dalle API del backend e vengono validate prima del salvataggio.
- Vendite, saldi e movimenti finanziari si inseriscono tramite campi strutturati, non tramite LLM.

## LLM

- L'LLM può interpretare richieste naturali e proporre o creare attività ed eventi attraverso azioni autorizzate.
- L'LLM può generare bozze di strategie, riepiloghi e proposte di calendario.
- L'LLM non calcola scadenze automatiche, non chiude elementi scaduti e non modifica direttamente il database.
- Una strategia generata dall'LLM deve essere presentata come bozza prima di diventare la versione attiva.
- La sostituzione delle attività strategiche richiede una conferma esplicita.

## Date e visibilità

- Il fuso orario applicativo è configurato dal backend; il valore previsto è `Europe/Rome`.
- Le date sono mostrate nell'interfaccia nel formato `dd/MM/yyyy`.
- Oggi, Calendario e TODO mostrano soltanto elementi operativi ancora aperti.
