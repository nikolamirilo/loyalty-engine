-- Per-program branding: a logo and two brand colours, so a demo program
-- (say, one for Lidl) makes the admin console and the member app look like
-- that brand. All nullable - a program without them keeps the stock theme.
--
-- Run this BEFORE deploying the API that reads these columns: create_all
-- never adds columns to an existing table, and every /programs read selects
-- them.
--
-- Safe to run more than once.

ALTER TABLE "public"."programs"
    ADD COLUMN IF NOT EXISTS "logo_url" text,
    ADD COLUMN IF NOT EXISTS "primary_color" character varying(7),
    ADD COLUMN IF NOT EXISTS "secondary_color" character varying(7);

-- The bucket logos are uploaded to (STORAGE_BUCKET on the API, default
-- "program-assets"). Public, so the browser loads a logo straight from its
-- URL. Only the API writes to it, with the service role key, which bypasses
-- Storage RLS - so no policies are added and anonymous clients cannot upload.
-- The size and type limits repeat the API's own checks
-- (app/services/program_branding.py) as a second line of defence.
INSERT INTO "storage"."buckets" ("id", "name", "public", "file_size_limit", "allowed_mime_types")
VALUES (
    'program-assets',
    'program-assets',
    true,
    2097152,
    ARRAY['image/png', 'image/jpeg', 'image/webp', 'image/svg+xml']
)
ON CONFLICT ("id") DO NOTHING;
