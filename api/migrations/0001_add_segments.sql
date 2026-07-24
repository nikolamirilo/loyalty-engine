-- Adds a proper Segment entity + member<->segment join table, and migrates
-- existing data into them:
--   * members.segments        (JSON array of free-text strings)  -> dropped
--   * challenge_segment_assignments.segment (free-text string)   -> segment_id FK
--
-- Run this once against Supabase before deploying the updated API (which
-- expects these tables/columns to already exist - SQLAlchemy's create_all
-- only creates missing tables, it never alters existing ones).
--
--   psql "$DATABASE_URL" -f api/migrations/0001_add_segments.sql
-- (or paste into the Supabase SQL editor)
--
-- gen_random_uuid() has been built into Postgres core since v13, so no
-- extension needs to be enabled first.

BEGIN;

-- 1. Segments -----------------------------------------------------------

CREATE TABLE IF NOT EXISTS segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR NOT NULL UNIQUE,
    description TEXT,
    color VARCHAR,
    created_at TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc')
);

-- If `segments` was already created by SQLAlchemy's create_all (e.g. the API
-- booted against this DB before this migration ran), CREATE TABLE above is a
-- no-op. models.py only sets a Python-side default for id/created_at, so a
-- table created that way has no database-level default on either column,
-- which makes the backfill INSERT below fail with a NOT NULL violation.
-- Force the defaults so this works regardless of how the table got here.
ALTER TABLE segments ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE segments ALTER COLUMN created_at SET DEFAULT (now() AT TIME ZONE 'utc');

-- Backfill one row per distinct segment name currently in use, whether on a
-- member's segments array or a challenge's segment-assignment history.
INSERT INTO segments (name)
SELECT DISTINCT all_names.name
FROM (
    SELECT json_array_elements_text(m.segments) AS name
    FROM members m
    WHERE m.segments IS NOT NULL AND json_typeof(m.segments) = 'array'
    UNION
    SELECT csa.segment AS name
    FROM challenge_segment_assignments csa
) AS all_names
WHERE all_names.name IS NOT NULL AND all_names.name <> ''
ON CONFLICT (name) DO NOTHING;

-- 2. Member <-> Segment join table --------------------------------------

CREATE TABLE IF NOT EXISTS member_segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    member_id UUID NOT NULL REFERENCES members(id) ON DELETE CASCADE,
    segment_id UUID NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
    CONSTRAINT uq_member_segment UNIQUE (member_id, segment_id)
);
ALTER TABLE member_segments ALTER COLUMN id SET DEFAULT gen_random_uuid();
ALTER TABLE member_segments ALTER COLUMN assigned_at SET DEFAULT (now() AT TIME ZONE 'utc');
CREATE INDEX IF NOT EXISTS ix_member_segments_member_id ON member_segments (member_id);
CREATE INDEX IF NOT EXISTS ix_member_segments_segment_id ON member_segments (segment_id);

INSERT INTO member_segments (member_id, segment_id)
SELECT DISTINCT m.id, s.id
FROM members m
CROSS JOIN LATERAL json_array_elements_text(m.segments) AS seg_name
JOIN segments s ON s.name = seg_name
WHERE m.segments IS NOT NULL AND json_typeof(m.segments) = 'array'
ON CONFLICT (member_id, segment_id) DO NOTHING;

-- 3. Re-point challenge_segment_assignments at segments.id ---------------

ALTER TABLE challenge_segment_assignments ADD COLUMN IF NOT EXISTS segment_id UUID REFERENCES segments(id) ON DELETE CASCADE;

UPDATE challenge_segment_assignments csa
SET segment_id = s.id
FROM segments s
WHERE s.name = csa.segment
  AND csa.segment_id IS NULL;

ALTER TABLE challenge_segment_assignments ALTER COLUMN segment_id SET NOT NULL;
ALTER TABLE challenge_segment_assignments DROP CONSTRAINT IF EXISTS uq_challenge_segment;
ALTER TABLE challenge_segment_assignments ADD CONSTRAINT uq_challenge_segment UNIQUE (challenge_id, segment_id);
ALTER TABLE challenge_segment_assignments DROP COLUMN segment;

-- 4. Drop the old free-text column on members -----------------------------

ALTER TABLE members DROP COLUMN segments;

COMMIT;
