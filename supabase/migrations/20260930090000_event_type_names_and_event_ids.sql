-- Two changes to how events are told apart.
--
-- An eventId now marks a repeat only within one event type, so an integration
-- can use one order number for both orderPlaced and orderRefunded. The new
-- constraint is looser than the old one, so no existing row can break it.
-- Apply this before deploying the API that checks per type: until then the
-- old constraint rejects a reused eventId on another type with a 409.
--
-- Event type names become unique within a program, like tier and segment
-- names. A rename could already have made two alike, so any duplicates are
-- numbered first ("Order placed (2)"), the oldest keeping its name. Keys
-- are untouched, so integrations keep working.
--
-- Safe to run more than once: each constraint is dropped if present before
-- it is added, and the renaming finds nothing once names are unique.

ALTER TABLE "public"."member_events"
    DROP CONSTRAINT IF EXISTS "uq_member_event_external_id",
    DROP CONSTRAINT IF EXISTS "uq_member_event_type_external_id";

ALTER TABLE "public"."member_events"
    ADD CONSTRAINT "uq_member_event_type_external_id" UNIQUE ("member_id", "type", "external_id");

UPDATE "public"."event_types" AS e
SET "name" = e."name" || ' (' || d."n" || ')'
FROM (
    SELECT "id", row_number() OVER (PARTITION BY "program_id", "name" ORDER BY "created_at", "id") AS "n"
    FROM "public"."event_types"
) AS d
WHERE e."id" = d."id" AND d."n" > 1;

ALTER TABLE "public"."event_types" DROP CONSTRAINT IF EXISTS "uq_program_event_type_name";

ALTER TABLE "public"."event_types"
    ADD CONSTRAINT "uq_program_event_type_name" UNIQUE ("program_id", "name");
