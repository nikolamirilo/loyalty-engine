-- Prize claiming: an assigned prize can now be marked as claimed, either by
-- the member pressing "Claim" in their wallet or from a link in the prize
-- email (POST /members/{id}/prizes/{rewardId} with sendEmail: true).
--
-- claimed_at is null until the member claims. The emailed link carries a
-- random token; only its HMAC hash is stored, with its own expiry, so the
-- link can be looked up without the raw token ever being persisted.
--
-- Run this BEFORE deploying the API that reads these columns: create_all
-- never adds columns to an existing table, and every redemption read selects
-- them.
--
-- Safe to run more than once.

ALTER TABLE "public"."redemptions"
    ADD COLUMN IF NOT EXISTS "claimed_at" timestamp without time zone,
    ADD COLUMN IF NOT EXISTS "claim_token_hash" character varying,
    ADD COLUMN IF NOT EXISTS "claim_token_expires_at" timestamp without time zone;

CREATE UNIQUE INDEX IF NOT EXISTS "ix_redemptions_claim_token_hash"
    ON "public"."redemptions" ("claim_token_hash");
