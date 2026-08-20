-- Double opt-in (DOI) email verification for members.
-- The ALTER TABLE below must be run by hand against Supabase: SQLAlchemy's
-- create_all() only creates brand-new tables on startup, it never alters an
-- existing one (see api/README.md).

ALTER TABLE members ADD COLUMN IF NOT EXISTS email_verified_at timestamp without time zone NULL;

CREATE TABLE IF NOT EXISTS email_verification_codes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id uuid NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    code_hash text NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    attempts integer NOT NULL DEFAULT 0,
    consumed_at timestamp without time zone NULL,
    created_at timestamp without time zone DEFAULT (now() AT TIME ZONE 'utc') NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_email_verification_codes_member_id
    ON email_verification_codes(member_id);

ALTER TABLE email_verification_codes ENABLE ROW LEVEL SECURITY;
