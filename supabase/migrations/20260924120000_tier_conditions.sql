-- Tiers gain a general condition list - points balance, lifetime purchase
-- spend/count, segments, custom attributes, ANDed together - the same field
-- language event rules already use (see api/app/services/rules). "rank"
-- replaces "min_points" as the ordering a member's highest-qualifying tier is
-- picked by: with several independent conditions there is no longer one
-- number every tier can be sorted by, so an admin sets it explicitly.
--
-- Safe to run more than once: the ADD COLUMNs are IF NOT EXISTS, and the
-- backfill only touches rows that still have the just-added empty default.

ALTER TABLE "public"."tiers"
    ADD COLUMN IF NOT EXISTS "rank" integer DEFAULT 0 NOT NULL,
    ADD COLUMN IF NOT EXISTS "conditions" jsonb DEFAULT '[]'::jsonb NOT NULL,
    ADD COLUMN IF NOT EXISTS "created_at" timestamp without time zone DEFAULT (now() AT TIME ZONE 'utc'::text) NOT NULL;

-- Carry every existing tier's min_points threshold forward as an equivalent
-- single condition, and as its initial rank, so a tier already configured in
-- a program keeps assigning members exactly the same way once min_points is
-- gone.
UPDATE "public"."tiers"
SET "rank" = "min_points",
    "conditions" = jsonb_build_array(
        jsonb_build_object('field', 'member.pointsBalance', 'operator', 'gte', 'value', "min_points")
    )
WHERE "conditions" = '[]'::jsonb;

ALTER TABLE "public"."tiers" DROP COLUMN IF EXISTS "min_points";
