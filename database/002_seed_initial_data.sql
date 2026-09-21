/* Dati iniziali ricavati dalla struttura Markdown validata il 18/09/2026. */
SET NOCOUNT ON;
SET XACT_ABORT ON;
BEGIN TRANSACTION;

DECLARE @User UNIQUEIDENTIFIER = '11111111-1111-1111-1111-111111111111';
DECLARE @Flavio UNIQUEIDENTIFIER = '22222222-2222-2222-2222-222222222221';
DECLARE @Cesare UNIQUEIDENTIFIER = '22222222-2222-2222-2222-222222222222';
DECLARE @Peter UNIQUEIDENTIFIER = '33333333-3333-3333-3333-333333333331';
DECLARE @Companion UNIQUEIDENTIFIER = '33333333-3333-3333-3333-333333333332';
DECLARE @Rubicone UNIQUEIDENTIFIER = '33333333-3333-3333-3333-333333333333';
DECLARE @Ing UNIQUEIDENTIFIER = '44444444-4444-4444-4444-444444444441';
DECLARE @Savings UNIQUEIDENTIFIER = '44444444-4444-4444-4444-444444444442';

IF NOT EXISTS (SELECT 1 FROM dbo.sb2_users WHERE id=@User)
    INSERT dbo.sb2_users(id,email,display_name,timezone)
    VALUES(@User,N'owner@secondbrain.local',N'Proprietario',N'Europe/Rome');

IF NOT EXISTS (SELECT 1 FROM dbo.sb2_author_profiles WHERE id=@Flavio)
    INSERT dbo.sb2_author_profiles(id,user_id,code,display_name,is_pseudonym,positioning,voice_markdown,privacy_markdown)
    VALUES(@Flavio,@User,N'FLAVIO',N'Flavio',0,
      N'Uno scrittore che cerca nelle storie la parte più profonda delle persone.',
      N'- Diretta e autentica\n- Riflessiva, narrativa e concreta\n- Rigorosa e cinematografica quando serve\n- Show-don''t-tell e dialoghi naturali\n- Niente guru, slogan motivazionali o prosa artificiosamente spezzata',
      N'Flavio non deve essere percepito esclusivamente come autore legato al Subbuteo.');

IF NOT EXISTS (SELECT 1 FROM dbo.sb2_author_profiles WHERE id=@Cesare)
    INSERT dbo.sb2_author_profiles(id,user_id,code,display_name,is_pseudonym,positioning,voice_markdown,privacy_markdown)
    VALUES(@Cesare,@User,N'CESARE',N'Cesare',1,
      N'Business novel e trasformazione aziendale raccontate attraverso situazioni reali.',
      N'- Concreta, fredda e asciutta\n- Riflessiva e professionale\n- Autorevole senza tono didattico\n- Niente guru-fluff o slogan LinkedIn',
      N'Cesare è uno pseudonimo. Il collegamento con Flavio non deve essere reso pubblico.');

IF NOT EXISTS (SELECT 1 FROM dbo.sb2_channels WHERE author_profile_id=@Flavio AND code=N'BLOG')
BEGIN
    INSERT dbo.sb2_channels(author_profile_id,code,display_name) VALUES
      (@Flavio,N'BLOG',N'Blog'),(@Flavio,N'MAILING',N'Mailing list'),(@Flavio,N'INSTAGRAM',N'Instagram');
END;
IF NOT EXISTS (SELECT 1 FROM dbo.sb2_channels WHERE author_profile_id=@Cesare AND code=N'SUBSTACK')
    INSERT dbo.sb2_channels(author_profile_id,code,display_name) VALUES(@Cesare,N'SUBSTACK',N'Substack');

IF NOT EXISTS (SELECT 1 FROM dbo.sb2_books WHERE id=@Peter)
    INSERT dbo.sb2_books(id,author_profile_id,code,title,status,publication_date,format_notes)
    VALUES(@Peter,@Flavio,N'PETER',N'Peter',N'publishing','2026-09-30',N'Cartaceo; ebook solo dopo 200 copie cartacee');
IF NOT EXISTS (SELECT 1 FROM dbo.sb2_books WHERE id=@Companion)
    INSERT dbo.sb2_books(id,author_profile_id,code,title,status,publication_date,format_notes)
    VALUES(@Companion,@Flavio,N'COMPANION',N'The International Table Football Companion: European & World Championships 1964–1979',N'published','2026-09-04',N'Solo cartaceo, mai ebook');
IF NOT EXISTS (SELECT 1 FROM dbo.sb2_books WHERE id=@Rubicone)
    INSERT dbo.sb2_books(id,author_profile_id,code,title,status,publication_date,format_notes)
    VALUES(@Rubicone,@Cesare,N'RUBICONE',N'Rubicone',N'publishing','2026-09-30',N'Solo cartaceo fino ad almeno 2.000 copie');

IF NOT EXISTS (SELECT 1 FROM dbo.sb2_targets WHERE book_id=@Peter AND metric_code=N'copies_sold' AND target_date='2026-12-31')
    INSERT dbo.sb2_targets(user_id,book_id,metric_code,target_value,target_date,notes)
    VALUES(@User,@Peter,N'copies_sold',250,'2026-12-31',N'Target Q4');
IF NOT EXISTS (SELECT 1 FROM dbo.sb2_targets WHERE book_id=@Companion AND metric_code=N'copies_sold' AND target_date='2026-12-31')
    INSERT dbo.sb2_targets(user_id,book_id,metric_code,target_value,target_date,notes)
    VALUES(@User,@Companion,N'copies_sold',100,'2026-12-31',N'Target Q4');
IF NOT EXISTS (SELECT 1 FROM dbo.sb2_targets WHERE book_id=@Rubicone AND metric_code=N'copies_sold' AND target_date='2026-12-31')
    INSERT dbo.sb2_targets(user_id,book_id,metric_code,target_value,target_date,notes)
    VALUES(@User,@Rubicone,N'copies_sold',200,'2026-12-31',N'Target Q4');

IF NOT EXISTS (SELECT 1 FROM dbo.sb2_strategies WHERE user_id=@User AND code=N'AUTHOR_FLAVIO')
    INSERT dbo.sb2_strategies(user_id,author_profile_id,code,title,content_markdown)
    VALUES(@User,@Flavio,N'AUTHOR_FLAVIO',N'Strategia generale Flavio',
      N'# Posizionamento\nUno scrittore che cerca nelle storie la parte più profonda delle persone.\n\n## Pilastri\n1. Animo delle persone\n2. Ascolto e testimonianza\n3. Ricerca e memoria\n4. Dietro la scrittura\n5. Libri diversi come espressioni dello stesso sguardo');
IF NOT EXISTS (SELECT 1 FROM dbo.sb2_strategies WHERE user_id=@User AND code=N'BOOK_PETER')
    INSERT dbo.sb2_strategies(user_id,author_profile_id,book_id,code,title,content_markdown)
    VALUES(@User,@Flavio,@Peter,N'BOOK_PETER',N'Strategia Peter',
      N'Peter deve vendere come libro e dimostrare il posizionamento di Flavio. Il Subbuteo è il contesto; il cuore è umano. Fasi: prelancio, lancio, Arona, follow-up, Natale e coda lunga.');
IF NOT EXISTS (SELECT 1 FROM dbo.sb2_strategies WHERE user_id=@User AND code=N'BOOK_RUBICONE')
    INSERT dbo.sb2_strategies(user_id,author_profile_id,book_id,code,title,content_markdown)
    VALUES(@User,@Cesare,@Rubicone,N'BOOK_RUBICONE',N'Strategia Rubicone',
      N'Rubicone costruisce pubblico e autorevolezza di Cesare tramite Substack. I concetti Lean diventano situazioni narrative su decisioni, responsabilità e trasformazione aziendale.');

IF NOT EXISTS (SELECT 1 FROM dbo.sb2_projects WHERE user_id=@User AND code=N'PETER')
    INSERT dbo.sb2_projects(user_id,author_profile_id,book_id,code,title,status,objective)
    VALUES(@User,@Flavio,@Peter,N'PETER',N'Peter',N'in_progress',N'Pubblicazione e 250 copie entro il 31/12/2026');
IF NOT EXISTS (SELECT 1 FROM dbo.sb2_projects WHERE user_id=@User AND code=N'RUBICONE')
    INSERT dbo.sb2_projects(user_id,author_profile_id,book_id,code,title,status,objective)
    VALUES(@User,@Cesare,@Rubicone,N'RUBICONE',N'Rubicone',N'in_progress',N'Pubblicazione e 200 copie nel Q4 2026');
IF NOT EXISTS (SELECT 1 FROM dbo.sb2_projects WHERE user_id=@User AND code=N'ARONA')
    INSERT dbo.sb2_projects(user_id,author_profile_id,book_id,code,title,status,objective)
    VALUES(@User,@Flavio,@Peter,N'ARONA',N'Il Subbuteo si racconta',N'in_progress',N'Evento, relazione con il pubblico e raccolta contatti');

IF NOT EXISTS (SELECT 1 FROM dbo.sb2_cases WHERE user_id=@User AND code=N'FRUIT')
    INSERT dbo.sb2_cases(user_id,code,title,status,context_markdown) VALUES(@User,N'FRUIT',N'Fruit',N'in_progress',N'Accesso ai PC ELIA/ARCPROC, installazione Experience, test, switch e backup.');
IF NOT EXISTS (SELECT 1 FROM dbo.sb2_cases WHERE user_id=@User AND code=N'INCIDENT')
    INSERT dbo.sb2_cases(user_id,code,title,status,context_markdown) VALUES(@User,N'INCIDENT',N'Incidente stradale / patente',N'in_progress',N'Patente riconsegnata; restano documentazione, art. 335 e valutazioni difensive.');
IF NOT EXISTS (SELECT 1 FROM dbo.sb2_cases WHERE user_id=@User AND code=N'WELFARE')
    INSERT dbo.sb2_cases(user_id,code,title,status,context_markdown) VALUES(@User,N'WELFARE',N'Welfare',N'in_progress',N'Credito €250 in scadenza marzo 2027; decidere allocazione entro novembre.');

IF NOT EXISTS (SELECT 1 FROM dbo.sb2_accounts WHERE id=@Ing)
    INSERT dbo.sb2_accounts(id,user_id,code,display_name,account_type,include_in_projection)
    VALUES(@Ing,@User,N'ING_CURRENT',N'Conto corrente ING',N'current',1);
IF NOT EXISTS (SELECT 1 FROM dbo.sb2_accounts WHERE id=@Savings)
    INSERT dbo.sb2_accounts(id,user_id,code,display_name,account_type,include_in_projection)
    VALUES(@Savings,@User,N'ING_SAVINGS',N'Conto risparmio ING',N'savings',0);
IF NOT EXISTS (SELECT 1 FROM dbo.sb2_balance_checks WHERE account_id=@Ing AND balance_date='2026-09-18' AND balance=2553)
    INSERT dbo.sb2_balance_checks(user_id,account_id,balance_date,balance,previous_balance,reconciliation_amount,notes)
    VALUES(@User,@Ing,'2026-09-18',2553,2558,-5,N'Saldo comunicato; differenza dovuta a movimenti non pianificati');
IF NOT EXISTS (SELECT 1 FROM dbo.sb2_balance_checks WHERE account_id=@Savings)
    INSERT dbo.sb2_balance_checks(user_id,account_id,balance_date,balance,notes)
    VALUES(@User,@Savings,'2026-09-18',30000,N'Conto separato, escluso dalle proiezioni');

IF NOT EXISTS (SELECT 1 FROM dbo.sb2_transactions WHERE account_id=@Ing AND transaction_date='2026-09-21' AND description=N'A2A Gas')
BEGIN
    INSERT dbo.sb2_transactions(user_id,account_id,transaction_date,description,amount,status,is_recurring) VALUES
      (@User,@Ing,'2026-09-21',N'A2A Gas',-53,N'planned',0),
      (@User,@Ing,'2026-09-22',N'A2A Acqua',-35.90,N'planned',0),
      (@User,@Ing,'2026-10-01',N'Affitto',-702,N'planned',1),
      (@User,@Ing,'2026-10-10',N'Stipendio',2300,N'planned',1),
      (@User,@Ing,'2026-11-01',N'Affitto',-702,N'planned',1),
      (@User,@Ing,'2026-11-10',N'Stipendio',2300,N'planned',1),
      (@User,@Ing,'2026-12-01',N'Affitto',-702,N'planned',1),
      (@User,@Ing,'2026-12-10',N'Stipendio',2300,N'planned',1);
END;

IF NOT EXISTS (SELECT 1 FROM dbo.sb2_tasks WHERE user_id=@User AND title=N'Seconda mano di pittura alla cucina')
BEGIN
    INSERT dbo.sb2_tasks(user_id,title,status,priority) VALUES
      (@User,N'Seconda mano di pittura alla cucina',N'open',3),
      (@User,N'Pubblicare in cartaceo i libri su Amazon',N'open',3),
      (@User,N'Rinnovo patente: derubricare la categoria C',N'open',3),
      (@User,N'Preparare per Torino la felpa Tablerugby e una copia di Peter',N'open',3),
      (@User,N'Verificare se il campanello wireless è già stato montato',N'to_verify',3),
      (@User,N'Verificare la tariffa oraria 2A luce',N'open',3),
      (@User,N'Decidere come utilizzare €250 di credito welfare',N'planned',3);
    UPDATE dbo.sb2_tasks SET due_date='2026-11-30' WHERE user_id=@User AND title=N'Decidere come utilizzare €250 di credito welfare';
END;

IF NOT EXISTS (SELECT 1 FROM dbo.sb2_events WHERE user_id=@User AND event_date='2026-09-18' AND title=N'Cena Sissi/Bianchi')
BEGIN
    INSERT dbo.sb2_events(user_id,title,event_date,start_time,event_type) VALUES
      (@User,N'Cena Sissi/Bianchi','2026-09-18','20:00',N'personal'),
      (@User,N'Mostra a Orzinuovi','2026-09-19','14:00',N'personal'),
      (@User,N'Prendere Antonella','2026-09-19','15:00',N'personal'),
      (@User,N'Morte a Venezia','2026-09-27','15:30',N'theatre'),
      (@User,N'Controllare se sono stati caricati i buoni pasto','2026-10-30',NULL,N'reminder');
END;

IF NOT EXISTS (SELECT 1 FROM dbo.sb2_tasks WHERE user_id=@User AND title LIKE N'Substack: Muda%')
BEGIN
    INSERT dbo.sb2_tasks(user_id,author_profile_id,book_id,title,status,due_date,source) VALUES
      (@User,@Cesare,@Rubicone,N'Substack: Muda — gli sprechi raccontati attraverso una situazione aziendale concreta',N'planned','2026-09-20',N'strategy'),
      (@User,@Cesare,@Rubicone,N'Substack: Gemba — cosa si vede quando si esce dalla sala riunioni',N'planned','2026-09-23',N'strategy'),
      (@User,@Cesare,@Rubicone,N'Substack: Muri/Mura — quando l’urgenza permanente diventa il sistema',N'planned','2026-09-27',N'strategy'),
      (@User,@Flavio,@Peter,N'Blog: dalla ricerca alla persona — cosa unisce Companion e Peter',N'planned','2026-09-22',N'strategy'),
      (@User,@Flavio,@Peter,N'Blog: la famiglia Czarkowski — ascoltare e ricostruire prima di raccontare',N'planned','2026-09-25',N'strategy'),
      (@User,@Flavio,@Peter,N'Mailing list: storia umana, uscita e richiesta esplicita di acquisto',N'planned','2026-09-30',N'strategy'),
      (@User,@Flavio,NULL,N'Blog: perché cerco nelle storie la parte più profonda delle persone',N'planned','2026-10-12',N'strategy'),
      (@User,@Flavio,NULL,N'Blog: ascoltare una persona prima di trasformarne la storia in racconto',N'planned','2026-11-19',N'strategy'),
      (@User,@Flavio,NULL,N'Blog: fallimento, dignità e speranza nelle persone che raccontiamo',N'planned','2026-12-17',N'strategy');
END;

IF NOT EXISTS (SELECT 1 FROM dbo.sb2_tasks WHERE user_id=@User AND title LIKE N'Substack: Kanban%')
BEGIN
    INSERT dbo.sb2_tasks(user_id,author_profile_id,book_id,title,status,due_date,source) VALUES
      (@User,@Cesare,@Rubicone,N'Substack: perché ho scritto Rubicone',N'planned','2026-10-04',N'strategy'),
      (@User,@Cesare,@Rubicone,N'Verifica lancio Rubicone: target cumulato 15 copie',N'planned','2026-10-07',N'strategy'),
      (@User,@Cesare,@Rubicone,N'Substack: Kanban — rendere visibile il lavoro che tutti fingono di controllare',N'planned','2026-10-14',N'strategy'),
      (@User,@Cesare,@Rubicone,N'Substack: Poka-yoke — affidarsi all’attenzione non è un processo',N'planned','2026-10-21',N'strategy'),
      (@User,@Cesare,@Rubicone,N'Substack: Kaizen — il miglioramento continuo usato come alibi',N'planned','2026-10-28',N'strategy'),
      (@User,@Cesare,@Rubicone,N'Verifica Rubicone: target cumulato 60 copie; sotto 40 rivedere messaggio e CTA',N'planned','2026-10-31',N'strategy'),
      (@User,@Cesare,@Rubicone,N'Substack: Jidoka — fermare il processo e assumersi la responsabilità',N'planned','2026-11-04',N'strategy'),
      (@User,@Cesare,@Rubicone,N'Substack: Heijunka — l’illusione di poter trattare tutto come urgente',N'planned','2026-11-11',N'strategy'),
      (@User,@Cesare,@Rubicone,N'Substack: 5S — ordine visibile e disordine decisionale',N'planned','2026-11-18',N'strategy'),
      (@User,@Cesare,@Rubicone,N'Substack: Genchi Genbutsu — vedere ciò che i report nascondono',N'planned','2026-11-25',N'strategy'),
      (@User,@Cesare,@Rubicone,N'Verifica Rubicone: target cumulato 125 copie; sotto 90 intensificare rete e prove sociali',N'planned','2026-11-30',N'strategy'),
      (@User,@Cesare,@Rubicone,N'Substack: per chi è Rubicone e per chi non lo è',N'planned','2026-12-02',N'strategy'),
      (@User,@Cesare,@Rubicone,N'Substack: le parole dei primi lettori',N'planned','2026-12-09',N'strategy'),
      (@User,@Cesare,@Rubicone,N'Verifica Rubicone: target cumulato 160 copie',N'planned','2026-12-15',N'strategy'),
      (@User,@Cesare,@Rubicone,N'Substack: Rubicone come regalo',N'planned','2026-12-16',N'strategy'),
      (@User,@Cesare,@Rubicone,N'Substack: bilancio di fine anno',N'planned','2026-12-23',N'strategy'),
      (@User,@Cesare,@Rubicone,N'Verifica risultato Rubicone: target Q4 200 copie',N'planned','2026-12-31',N'strategy');
END;

IF NOT EXISTS (SELECT 1 FROM dbo.sb2_tasks WHERE user_id=@User AND title LIKE N'Instagram: frammento sul rapporto%')
BEGIN
    INSERT dbo.sb2_tasks(user_id,author_profile_id,book_id,title,status,due_date,source) VALUES
      (@User,@Flavio,@Peter,N'Instagram: frammento sul rapporto padre/figlio',N'planned','2026-10-08',N'strategy'),
      (@User,@Flavio,@Peter,N'Mailing: Arona — incontrare la storia e chi l’ha vissuta',N'planned','2026-10-15',N'strategy'),
      (@User,@Flavio,@Peter,N'Mailing: cosa ci ha lasciato Arona, testimonianze e invito all’acquisto o recensione',N'planned','2026-10-29',N'strategy'),
      (@User,@Flavio,@Peter,N'Verifica Peter: target cumulato 90 copie; sotto 65 rivedere messaggio e CTA',N'planned','2026-10-31',N'strategy'),
      (@User,@Flavio,@Peter,N'Blog: che cosa Arona ha rivelato sulle storie familiari e sui lettori',N'planned','2026-11-05',N'strategy'),
      (@User,@Flavio,@Peter,N'Verifica Peter: target cumulato 170 copie; sotto 130 intensificare testimonianze e mailing',N'planned','2026-11-30',N'strategy'),
      (@User,@Flavio,@Peter,N'Mailing: Peter come regalo, centrato sulla storia umana',N'planned','2026-12-03',N'strategy'),
      (@User,@Flavio,@Peter,N'Verifica Peter: target cumulato 210 copie',N'planned','2026-12-15',N'strategy'),
      (@User,@Flavio,@Peter,N'Verifica risultato Peter: target 250 copie',N'planned','2026-12-31',N'strategy');
END;

COMMIT TRANSACTION;
GO
