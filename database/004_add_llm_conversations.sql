SET NOCOUNT ON;
SET XACT_ABORT ON;
BEGIN TRANSACTION;

IF OBJECT_ID(N'dbo.sb2_conversations', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sb2_conversations (
        id UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_sb2_conversations PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        user_id UNIQUEIDENTIFIER NOT NULL,
        title NVARCHAR(250) NOT NULL CONSTRAINT DF_sb2_conversations_title DEFAULT N'Nuova conversazione',
        status NVARCHAR(20) NOT NULL CONSTRAINT DF_sb2_conversations_status DEFAULT N'active',
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_conversations_created DEFAULT SYSUTCDATETIME(),
        updated_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_conversations_updated DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_sb2_conversations_user FOREIGN KEY (user_id) REFERENCES dbo.sb2_users(id),
        CONSTRAINT CK_sb2_conversations_status CHECK (status IN (N'active',N'archived'))
    );
    CREATE INDEX IX_sb2_conversations_user_updated ON dbo.sb2_conversations(user_id, updated_at DESC);
END;

IF OBJECT_ID(N'dbo.sb2_messages', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.sb2_messages (
        id UNIQUEIDENTIFIER NOT NULL CONSTRAINT PK_sb2_messages PRIMARY KEY DEFAULT NEWSEQUENTIALID(),
        conversation_id UNIQUEIDENTIFIER NOT NULL,
        role NVARCHAR(20) NOT NULL,
        content_markdown NVARCHAR(MAX) NOT NULL,
        message_kind NVARCHAR(40) NOT NULL CONSTRAINT DF_sb2_messages_kind DEFAULT N'text',
        metadata_json NVARCHAR(MAX) NULL,
        created_at DATETIME2(0) NOT NULL CONSTRAINT DF_sb2_messages_created DEFAULT SYSUTCDATETIME(),
        CONSTRAINT FK_sb2_messages_conversation FOREIGN KEY (conversation_id) REFERENCES dbo.sb2_conversations(id) ON DELETE CASCADE,
        CONSTRAINT CK_sb2_messages_role CHECK (role IN (N'user',N'assistant',N'system')),
        CONSTRAINT CK_sb2_messages_json CHECK (metadata_json IS NULL OR ISJSON(metadata_json) = 1)
    );
    CREATE INDEX IX_sb2_messages_conversation_created ON dbo.sb2_messages(conversation_id, created_at, id);
END;

COMMIT TRANSACTION;
GO
