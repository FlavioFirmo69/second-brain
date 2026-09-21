/*
  ESEMPIO OPZIONALE: adattare nomi e password alla propria policy.
  Richiede permessi amministrativi. Non eseguire senza avere sostituito i placeholder.
*/
/*
USE [master];
CREATE LOGIN [second_brain_app] WITH PASSWORD = N'<PASSWORD_FORTE>', CHECK_POLICY = ON;
GO
USE [NOME_DATABASE_ESISTENTE];
CREATE USER [second_brain_app] FOR LOGIN [second_brain_app];

GRANT SELECT, INSERT, UPDATE, DELETE ON dbo.sb2_users TO [second_brain_app];
-- Ripetere i GRANT per ogni tabella sb2_ creata dallo script principale.
-- Non assegnare db_owner e non concedere permessi sulle tabelle dell'altra applicazione.
GO
*/

