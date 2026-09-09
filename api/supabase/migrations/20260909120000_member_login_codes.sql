-- Member login one-time codes. Independent of email_verification_codes
-- (DOI): a login code can be requested every sign-in, DOI proves an address
-- once. The ALTER TABLE convention below must be run by hand against
-- Supabase: SQLAlchemy's create_all() only creates brand-new tables on
-- startup, it never alters an existing one (see api/README.md) - this
-- migration only creates a new table, so no ALTER is needed here.

CREATE TABLE IF NOT EXISTS member_login_codes (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id uuid NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    code_hash text NOT NULL,
    expires_at timestamp without time zone NOT NULL,
    attempts integer NOT NULL DEFAULT 0,
    consumed_at timestamp without time zone NULL,
    created_at timestamp without time zone DEFAULT (now() AT TIME ZONE 'utc') NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_member_login_codes_member_id
    ON member_login_codes(member_id);

ALTER TABLE member_login_codes ENABLE ROW LEVEL SECURITY;
