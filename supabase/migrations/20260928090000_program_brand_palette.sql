-- The rest of a program's brand palette, next to primary_color and
-- secondary_color (20260925090000_program_branding.sql): the text colour on
-- primary, the header/tab bar colour, the page background and the text
-- colour. Together they let a demo program (Lidl: yellow and blue) look like
-- that brand's own app. All nullable - null is the stock Loyalty Engine colour.
--
-- Run this BEFORE deploying the API that reads these columns: create_all
-- never adds columns to an existing table, and every /programs read selects
-- them.
--
-- Safe to run more than once.

ALTER TABLE "public"."programs"
    ADD COLUMN IF NOT EXISTS "on_primary_color" character varying(7),
    ADD COLUMN IF NOT EXISTS "header_color" character varying(7),
    ADD COLUMN IF NOT EXISTS "background_color" character varying(7),
    ADD COLUMN IF NOT EXISTS "text_color" character varying(7);
