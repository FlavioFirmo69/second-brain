/*
  Second Brain - schema iniziale per SQL Server
  Eseguire nel database ESISTENTE scelto dall'utente.
  Lo script non crea database e non modifica tabelle prive del prefisso sb2_.
  E' rieseguibile: ogni tabella viene creata soltanto se assente.
*/
SET NOCOUNT ON;
SET XACT_ABORT ON;
BEGIN TRANSACTION;

IF OBJECT_ID(N'dbo.sb2_users', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sb2_users (
        id UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_sb2_users PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        email NVARCHAR(320) NOT NULL,
        display_name NVARCHAR(160) NOT NULL,
        timezone NVARCHAR(64) NOT NULL CONSTRAINT DF_sb2_users_timezone DEFAULT N'Europe/Rome',
        is_active BIT NOT NULL CONSTRAINT DF_sb2_users_active DEFAULT 1,
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_users_created DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_users_updated DEFAULT SYSUTCDATETIME(),
        CONSTRAINT UQ_sb2_users_email UNIQUE (email)
    );
END;

IF OBJECT_ID(N'dbo.sb2_author_profiles', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sb2_author_profiles (
        id UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_sb2_author_profiles PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        user_id UNIQUEIDENTIFIER NOT NULL,
        code NVARCHAR(40) NOT NULL,
        display_name NVARCHAR(160) NOT NULL,
        is_pseudonym BIT NOT NULL CONSTRAINT DF_sb2_profiles_pseudonym DEFAULT 0,
        positioning NVARCHAR(1000) NULL,
        voice_markdown NVARCHAR(MAX) NOT NULL CONSTRAINT DF_sb2_profiles_voice DEFAULT N'',
        privacy_markdown NVARCHAR(MAX) NOT NULL CONSTRAINT DF_sb2_profiles_privacy DEFAULT N'',
        is_active BIT NOT NULL CONSTRAINT DF_sb2_profiles_active DEFAULT 1,
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_profiles_created DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_profiles_updated DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_sb2_profiles_user FOREIGN KEY (user_id) REFERENCES dbo.sb2_users(id),
        CONSTRAINT UQ_sb2_profiles_code UNIQUE (user_id, code)
    );
END;

IF OBJECT_ID(N'dbo.sb2_agent_prompt_versions', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sb2_agent_prompt_versions (
        id UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_sb2_prompt_versions PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        author_profile_id UNIQUEIDENTIFIER NOT NULL,
        version_number INT NOT NULL,
        content_markdown NVARCHAR(MAX) NOT NULL,
        change_reason NVARCHAR(500) NULL,
        is_active BIT NOT NULL CONSTRAINT DF_sb2_prompt_active DEFAULT 0,
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_prompt_created DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_sb2_prompt_profile FOREIGN KEY (author_profile_id) REFERENCES dbo.sb2_author_profiles(id),
        CONSTRAINT UQ_sb2_prompt_version UNIQUE (author_profile_id, version_number)
    );
    CREATE UNIQUE INDEX UX_sb2_prompt_one_active
        ON dbo.sb2_agent_prompt_versions(author_profile_id)
        WHERE is_active = 1;
END;

IF OBJECT_ID(N'dbo.sb2_channels', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sb2_channels (
        id UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_sb2_channels PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        author_profile_id UNIQUEIDENTIFIER NOT NULL,
        code NVARCHAR(40) NOT NULL,
        display_name NVARCHAR(100) NOT NULL,
        is_active BIT NOT NULL CONSTRAINT DF_sb2_channels_active DEFAULT 1,
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_channels_created DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_sb2_channels_profile FOREIGN KEY (author_profile_id) REFERENCES dbo.sb2_author_profiles(id),
        CONSTRAINT UQ_sb2_channels_code UNIQUE (author_profile_id, code)
    );
END;

IF OBJECT_ID(N'dbo.sb2_books', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sb2_books (
        id UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_sb2_books PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        author_profile_id UNIQUEIDENTIFIER NOT NULL,
        code NVARCHAR(60) NOT NULL,
        title NVARCHAR(500) NOT NULL,
        status NVARCHAR(30) NOT NULL,
        publication_date DATE NULL,
        format_notes NVARCHAR(500) NULL,
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_books_created DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_books_updated DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_sb2_books_profile FOREIGN KEY (author_profile_id) REFERENCES dbo.sb2_author_profiles(id),
        CONSTRAINT UQ_sb2_books_code UNIQUE (code)
    );
END;

IF OBJECT_ID(N'dbo.sb2_strategies', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sb2_strategies (
        id UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_sb2_strategies PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        user_id UNIQUEIDENTIFIER NOT NULL,
        author_profile_id UNIQUEIDENTIFIER NULL,
        book_id UNIQUEIDENTIFIER NULL,
        code NVARCHAR(80) NOT NULL,
        title NVARCHAR(250) NOT NULL,
        content_markdown NVARCHAR(MAX) NOT NULL,
        status NVARCHAR(30) NOT NULL CONSTRAINT DF_sb2_strategies_status DEFAULT N'active',
        version_number INT NOT NULL CONSTRAINT DF_sb2_strategies_version DEFAULT 1,
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_strategies_created DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_strategies_updated DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_sb2_strategies_user FOREIGN KEY (user_id) REFERENCES dbo.sb2_users(id),
        CONSTRAINT FK_sb2_strategies_profile FOREIGN KEY (author_profile_id) REFERENCES dbo.sb2_author_profiles(id),
        CONSTRAINT FK_sb2_strategies_book FOREIGN KEY (book_id) REFERENCES dbo.sb2_books(id),
        CONSTRAINT UQ_sb2_strategies_code UNIQUE (user_id, code)
    );
END;

IF OBJECT_ID(N'dbo.sb2_projects', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sb2_projects (
        id UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_sb2_projects PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        user_id UNIQUEIDENTIFIER NOT NULL,
        author_profile_id UNIQUEIDENTIFIER NULL,
        book_id UNIQUEIDENTIFIER NULL,
        code NVARCHAR(80) NOT NULL,
        title NVARCHAR(250) NOT NULL,
        status NVARCHAR(30) NOT NULL,
        objective NVARCHAR(MAX) NULL,
        notes_markdown NVARCHAR(MAX) NOT NULL CONSTRAINT DF_sb2_projects_notes DEFAULT N'',
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_projects_created DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_projects_updated DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_sb2_projects_user FOREIGN KEY (user_id) REFERENCES dbo.sb2_users(id),
        CONSTRAINT FK_sb2_projects_profile FOREIGN KEY (author_profile_id) REFERENCES dbo.sb2_author_profiles(id),
        CONSTRAINT FK_sb2_projects_book FOREIGN KEY (book_id) REFERENCES dbo.sb2_books(id),
        CONSTRAINT UQ_sb2_projects_code UNIQUE (user_id, code)
    );
END;

IF OBJECT_ID(N'dbo.sb2_cases', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sb2_cases (
        id UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_sb2_cases PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        user_id UNIQUEIDENTIFIER NOT NULL,
        code NVARCHAR(80) NOT NULL,
        title NVARCHAR(250) NOT NULL,
        status NVARCHAR(30) NOT NULL,
        context_markdown NVARCHAR(MAX) NOT NULL CONSTRAINT DF_sb2_cases_context DEFAULT N'',
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_cases_created DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_cases_updated DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_sb2_cases_user FOREIGN KEY (user_id) REFERENCES dbo.sb2_users(id),
        CONSTRAINT UQ_sb2_cases_code UNIQUE (user_id, code)
    );
END;

IF OBJECT_ID(N'dbo.sb2_tasks', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sb2_tasks (
        id UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_sb2_tasks PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        user_id UNIQUEIDENTIFIER NOT NULL,
        project_id UNIQUEIDENTIFIER NULL,
        case_id UNIQUEIDENTIFIER NULL,
        author_profile_id UNIQUEIDENTIFIER NULL,
        book_id UNIQUEIDENTIFIER NULL,
        title NVARCHAR(500) NOT NULL,
        description NVARCHAR(MAX) NULL,
        status NVARCHAR(30) NOT NULL CONSTRAINT DF_sb2_tasks_status DEFAULT N'open',
        priority TINYINT NOT NULL CONSTRAINT DF_sb2_tasks_priority DEFAULT 3,
        due_date DATE NULL,
        due_time TIME(0) NULL,
        completed_at DATETIME2(0) NULL,
        source NVARCHAR(50) NOT NULL CONSTRAINT DF_sb2_tasks_source DEFAULT N'manual',
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_tasks_created DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_tasks_updated DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_sb2_tasks_user FOREIGN KEY (user_id) REFERENCES dbo.sb2_users(id),
        CONSTRAINT FK_sb2_tasks_project FOREIGN KEY (project_id) REFERENCES dbo.sb2_projects(id),
        CONSTRAINT FK_sb2_tasks_case FOREIGN KEY (case_id) REFERENCES dbo.sb2_cases(id),
        CONSTRAINT FK_sb2_tasks_profile FOREIGN KEY (author_profile_id) REFERENCES dbo.sb2_author_profiles(id),
        CONSTRAINT FK_sb2_tasks_book FOREIGN KEY (book_id) REFERENCES dbo.sb2_books(id),
        CONSTRAINT CK_sb2_tasks_status CHECK (status IN (N'open',N'planned',N'in_progress',N'blocked',N'to_verify',N'completed',N'cancelled'))
    );
    CREATE INDEX IX_sb2_tasks_open_due ON dbo.sb2_tasks(user_id, status, due_date);
END;

IF OBJECT_ID(N'dbo.sb2_events', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sb2_events (
        id UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_sb2_events PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        user_id UNIQUEIDENTIFIER NOT NULL,
        project_id UNIQUEIDENTIFIER NULL,
        author_profile_id UNIQUEIDENTIFIER NULL,
        book_id UNIQUEIDENTIFIER NULL,
        title NVARCHAR(500) NOT NULL,
        event_date DATE NOT NULL,
        start_time TIME(0) NULL,
        end_time TIME(0) NULL,
        location NVARCHAR(500) NULL,
        status NVARCHAR(30) NOT NULL CONSTRAINT DF_sb2_events_status DEFAULT N'planned',
        event_type NVARCHAR(40) NOT NULL CONSTRAINT DF_sb2_events_type DEFAULT N'personal',
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_events_created DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_events_updated DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_sb2_events_user FOREIGN KEY (user_id) REFERENCES dbo.sb2_users(id),
        CONSTRAINT FK_sb2_events_project FOREIGN KEY (project_id) REFERENCES dbo.sb2_projects(id),
        CONSTRAINT FK_sb2_events_profile FOREIGN KEY (author_profile_id) REFERENCES dbo.sb2_author_profiles(id),
        CONSTRAINT FK_sb2_events_book FOREIGN KEY (book_id) REFERENCES dbo.sb2_books(id)
    );
    CREATE INDEX IX_sb2_events_date ON dbo.sb2_events(user_id, event_date, start_time);
END;

IF OBJECT_ID(N'dbo.sb2_sales', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sb2_sales (
        id UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_sb2_sales PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        user_id UNIQUEIDENTIFIER NOT NULL,
        book_id UNIQUEIDENTIFIER NOT NULL,
        sale_date DATE NOT NULL,
        quantity INT NOT NULL,
        channel NVARCHAR(100) NULL,
        notes NVARCHAR(500) NULL,
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_sales_created DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_sb2_sales_user FOREIGN KEY (user_id) REFERENCES dbo.sb2_users(id),
        CONSTRAINT FK_sb2_sales_book FOREIGN KEY (book_id) REFERENCES dbo.sb2_books(id),
        CONSTRAINT CK_sb2_sales_quantity CHECK (quantity > 0)
    );
    CREATE INDEX IX_sb2_sales_book_date ON dbo.sb2_sales(book_id, sale_date);
END;

IF OBJECT_ID(N'dbo.sb2_targets', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sb2_targets (
        id UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_sb2_targets PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        user_id UNIQUEIDENTIFIER NOT NULL,
        author_profile_id UNIQUEIDENTIFIER NULL,
        book_id UNIQUEIDENTIFIER NULL,
        metric_code NVARCHAR(80) NOT NULL,
        target_value DECIMAL(18,2) NOT NULL,
        warning_value DECIMAL(18,2) NULL,
        target_date DATE NOT NULL,
        notes NVARCHAR(500) NULL,
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_targets_created DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_sb2_targets_user FOREIGN KEY (user_id) REFERENCES dbo.sb2_users(id),
        CONSTRAINT FK_sb2_targets_profile FOREIGN KEY (author_profile_id) REFERENCES dbo.sb2_author_profiles(id),
        CONSTRAINT FK_sb2_targets_book FOREIGN KEY (book_id) REFERENCES dbo.sb2_books(id)
    );
END;

IF OBJECT_ID(N'dbo.sb2_accounts', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sb2_accounts (
        id UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_sb2_accounts PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        user_id UNIQUEIDENTIFIER NOT NULL,
        code NVARCHAR(60) NOT NULL,
        display_name NVARCHAR(160) NOT NULL,
        account_type NVARCHAR(40) NOT NULL,
        currency CHAR(3) NOT NULL CONSTRAINT DF_sb2_accounts_currency DEFAULT 'EUR',
        include_in_projection BIT NOT NULL CONSTRAINT DF_sb2_accounts_projection DEFAULT 1,
        is_active BIT NOT NULL CONSTRAINT DF_sb2_accounts_active DEFAULT 1,
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_accounts_created DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_sb2_accounts_user FOREIGN KEY (user_id) REFERENCES dbo.sb2_users(id),
        CONSTRAINT UQ_sb2_accounts_code UNIQUE (user_id, code)
    );
END;

IF OBJECT_ID(N'dbo.sb2_transactions', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sb2_transactions (
        id UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_sb2_transactions PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        user_id UNIQUEIDENTIFIER NOT NULL,
        account_id UNIQUEIDENTIFIER NOT NULL,
        transaction_date DATE NOT NULL,
        description NVARCHAR(500) NOT NULL,
        amount DECIMAL(18,2) NOT NULL,
        status NVARCHAR(20) NOT NULL,
        is_recurring BIT NOT NULL CONSTRAINT DF_sb2_transactions_recurring DEFAULT 0,
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_transactions_created DEFAULT SYSUTCDATETIME(),
        confirmed_at DATETIME2(0) NULL,
        CONSTRAINT FK_sb2_transactions_user FOREIGN KEY (user_id) REFERENCES dbo.sb2_users(id),
        CONSTRAINT FK_sb2_transactions_account FOREIGN KEY (account_id) REFERENCES dbo.sb2_accounts(id),
        CONSTRAINT CK_sb2_transactions_status CHECK (status IN (N'planned',N'confirmed',N'cancelled'))
    );
    CREATE INDEX IX_sb2_transactions_date ON dbo.sb2_transactions(account_id, status, transaction_date);
END;

IF OBJECT_ID(N'dbo.sb2_balance_checks', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sb2_balance_checks (
        id UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_sb2_balance_checks PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        user_id UNIQUEIDENTIFIER NOT NULL,
        account_id UNIQUEIDENTIFIER NOT NULL,
        balance_date DATE NOT NULL,
        balance DECIMAL(18,2) NOT NULL,
        previous_balance DECIMAL(18,2) NULL,
        reconciliation_amount DECIMAL(18,2) NULL,
        notes NVARCHAR(500) NULL,
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_balance_created DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_sb2_balance_user FOREIGN KEY (user_id) REFERENCES dbo.sb2_users(id),
        CONSTRAINT FK_sb2_balance_account FOREIGN KEY (account_id) REFERENCES dbo.sb2_accounts(id)
    );
    CREATE INDEX IX_sb2_balance_latest ON dbo.sb2_balance_checks(account_id, balance_date DESC, created_at DESC);
END;

IF OBJECT_ID(N'dbo.sb2_inbox', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sb2_inbox (
        id UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_sb2_inbox PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        user_id UNIQUEIDENTIFIER NOT NULL,
        source NVARCHAR(40) NOT NULL CONSTRAINT DF_sb2_inbox_source DEFAULT N'desktop',
        text NVARCHAR(MAX) NOT NULL,
        status NVARCHAR(30) NOT NULL CONSTRAINT DF_sb2_inbox_status DEFAULT N'new',
        interpretation_json NVARCHAR(MAX) NULL,
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_inbox_created DEFAULT SYSUTCDATETIME(),
        processed_at DATETIME2(0) NULL,
        CONSTRAINT FK_sb2_inbox_user FOREIGN KEY (user_id) REFERENCES dbo.sb2_users(id),
        CONSTRAINT CK_sb2_inbox_status CHECK (status IN (N'new',N'interpreted',N'confirmed',N'cancelled')),
        CONSTRAINT CK_sb2_inbox_json CHECK (interpretation_json IS NULL OR ISJSON(interpretation_json) = 1)
    );
END;

IF OBJECT_ID(N'dbo.sb2_change_log', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sb2_change_log (
        id BIGINT IDENTITY(1,1) NOT NULL CONSTRAINT PK_sb2_change_log PRIMARY KEY,
        user_id UNIQUEIDENTIFIER NULL,
        entity_type NVARCHAR(80) NOT NULL,
        entity_id UNIQUEIDENTIFIER NULL,
        action NVARCHAR(60) NOT NULL,
        before_json NVARCHAR(MAX) NULL,
        after_json NVARCHAR(MAX) NULL,
        source NVARCHAR(50) NOT NULL CONSTRAINT DF_sb2_log_source DEFAULT N'api',
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_log_created DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_sb2_log_user FOREIGN KEY (user_id) REFERENCES dbo.sb2_users(id),
        CONSTRAINT CK_sb2_log_before_json CHECK (before_json IS NULL OR ISJSON(before_json) = 1),
        CONSTRAINT CK_sb2_log_after_json CHECK (after_json IS NULL OR ISJSON(after_json) = 1)
    );
    CREATE INDEX IX_sb2_log_entity ON dbo.sb2_change_log(entity_type, entity_id, created_at DESC);
END;

COMMIT TRANSACTION;
GO

