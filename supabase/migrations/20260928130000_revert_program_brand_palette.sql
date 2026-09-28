-- Reverts 20260928090000_program_brand_palette.sql.
--
-- The six-colour palette was dropped in favour of the original two brand
-- colours (primary_color, secondary_color, from 20260925090000), so the four
-- extra columns go again. A forward migration rather than deleting the
-- original: that one is already applied remotely, and a migration the remote
-- history knows about but the repo does not makes `supabase db push` refuse
-- to run.
--
-- Safe at any time: no deployed API reads these columns. Safe to run more
-- than once.

ALTER TABLE "public"."programs"
    DROP COLUMN IF EXISTS "on_primary_color",
    DROP COLUMN IF EXISTS "header_color",
    DROP COLUMN IF EXISTS "background_color",
    DROP COLUMN IF EXISTS "text_color";
