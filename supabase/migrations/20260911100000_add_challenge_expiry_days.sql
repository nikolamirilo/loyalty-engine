-- Per-member relative challenge expiry.
--
-- Today a challenge's `expires_at` is a single absolute deadline shared by
-- every member it's assigned to. `expiry_days` lets a challenge instead say
-- "N days after whoever is assigned gets assigned", so a member who joins
-- late still gets a full N-day window. The concrete per-member deadline is
-- resolved once at assignment time and stored on `challenge_assignments`,
-- mirroring `email_verification_codes.expires_at`.

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


ALTER TABLE "public"."challenges" ADD COLUMN IF NOT EXISTS "expiry_days" integer;


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM "pg_constraint" WHERE "conname" = 'challenges_expiry_days_positive'
    ) THEN
        ALTER TABLE ONLY "public"."challenges"
            ADD CONSTRAINT "challenges_expiry_days_positive" CHECK (("expiry_days" IS NULL OR "expiry_days" > 0));
    END IF;
END $$;


ALTER TABLE "public"."challenge_assignments" ADD COLUMN IF NOT EXISTS "expires_at" timestamp without time zone;


-- Backfill so already-assigned members keep today's behavior: an assignment
-- with no expiry_days on its challenge falls back to that challenge's
-- absolute expires_at.
UPDATE "public"."challenge_assignments" ca
SET "expires_at" = c."expires_at"
FROM "public"."challenges" c
WHERE ca."challenge_id" = c."id" AND c."expires_at" IS NOT NULL AND ca."expires_at" IS NULL;
