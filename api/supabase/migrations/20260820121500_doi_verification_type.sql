-- DOI trigger type: which email a verification code was issued for.
-- `code` (the default, and what every existing row was) mails a 6-digit code;
-- `page` mails a link to the client's /verify page.
--
-- As with the migration next to this one, the ALTER TABLE must be run by hand
-- against Supabase: SQLAlchemy's create_all() only creates brand-new tables on
-- startup, it never alters an existing one (see api/README.md).

DO $$
BEGIN
    CREATE TYPE doitype AS ENUM ('code', 'page');
EXCEPTION
    WHEN duplicate_object THEN NULL;
END
$$;

ALTER TABLE email_verification_codes
    ADD COLUMN IF NOT EXISTS type doitype NOT NULL DEFAULT 'code';
