-- Member events and the rule engine: event definitions, their rules, the
-- events received per member, and a count of rule runs for per-member limits.
--
-- The API's create_all makes these tables too, so every statement here is
-- idempotent: it is safe to run before or after the API first starts. What
-- create_all cannot do is enable row level security, which every other table
-- has, so that part is required either way.

CREATE TABLE IF NOT EXISTS "public"."event_types" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "program_id" "uuid" NOT NULL,
    "key" character varying NOT NULL,
    "name" character varying NOT NULL,
    "description" "text",
    "is_active" boolean DEFAULT true NOT NULL,
    "attributes" "jsonb" DEFAULT '[]'::"jsonb" NOT NULL,
    "created_at" timestamp without time zone DEFAULT ("now"() AT TIME ZONE 'utc'::"text") NOT NULL,
    CONSTRAINT "event_types_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "uq_program_event_type_key" UNIQUE ("program_id", "key"),
    CONSTRAINT "event_types_program_id_fkey" FOREIGN KEY ("program_id")
        REFERENCES "public"."programs"("id") ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS "ix_event_types_program_id"
    ON "public"."event_types" USING "btree" ("program_id");


CREATE TABLE IF NOT EXISTS "public"."event_rules" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "event_type_id" "uuid" NOT NULL,
    "name" character varying NOT NULL,
    "is_active" boolean DEFAULT true NOT NULL,
    "conditions" "jsonb" DEFAULT '[]'::"jsonb" NOT NULL,
    "effects" "jsonb" DEFAULT '[]'::"jsonb" NOT NULL,
    "limit_per_member" integer,
    "created_at" timestamp without time zone DEFAULT ("now"() AT TIME ZONE 'utc'::"text") NOT NULL,
    CONSTRAINT "event_rules_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "event_rules_event_type_id_fkey" FOREIGN KEY ("event_type_id")
        REFERENCES "public"."event_types"("id") ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS "ix_event_rules_event_type_id"
    ON "public"."event_rules" USING "btree" ("event_type_id");


-- event_type_id is set to null when a definition is deleted; "type" keeps the
-- key it had, so the member's history still reads.
CREATE TABLE IF NOT EXISTS "public"."member_events" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "member_id" "uuid" NOT NULL,
    "event_type_id" "uuid",
    "type" character varying NOT NULL,
    "attributes" "jsonb" DEFAULT '{}'::"jsonb" NOT NULL,
    "effects" "jsonb" DEFAULT '[]'::"jsonb" NOT NULL,
    "external_id" character varying,
    "created_at" timestamp without time zone DEFAULT ("now"() AT TIME ZONE 'utc'::"text") NOT NULL,
    CONSTRAINT "member_events_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "uq_member_event_external_id" UNIQUE ("member_id", "external_id"),
    CONSTRAINT "member_events_member_id_fkey" FOREIGN KEY ("member_id")
        REFERENCES "public"."members"("id") ON DELETE CASCADE,
    CONSTRAINT "member_events_event_type_id_fkey" FOREIGN KEY ("event_type_id")
        REFERENCES "public"."event_types"("id") ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS "ix_member_events_member_id"
    ON "public"."member_events" USING "btree" ("member_id");


CREATE TABLE IF NOT EXISTS "public"."event_rule_runs" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "rule_id" "uuid" NOT NULL,
    "member_id" "uuid" NOT NULL,
    "member_event_id" "uuid" NOT NULL,
    "created_at" timestamp without time zone DEFAULT ("now"() AT TIME ZONE 'utc'::"text") NOT NULL,
    CONSTRAINT "event_rule_runs_pkey" PRIMARY KEY ("id"),
    CONSTRAINT "event_rule_runs_rule_id_fkey" FOREIGN KEY ("rule_id")
        REFERENCES "public"."event_rules"("id") ON DELETE CASCADE,
    CONSTRAINT "event_rule_runs_member_id_fkey" FOREIGN KEY ("member_id")
        REFERENCES "public"."members"("id") ON DELETE CASCADE,
    CONSTRAINT "event_rule_runs_member_event_id_fkey" FOREIGN KEY ("member_event_id")
        REFERENCES "public"."member_events"("id") ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS "ix_event_rule_runs_rule_member"
    ON "public"."event_rule_runs" USING "btree" ("rule_id", "member_id");
CREATE INDEX IF NOT EXISTS "ix_event_rule_runs_member_event_id"
    ON "public"."event_rule_runs" USING "btree" ("member_event_id");


-- Only the API (service role) reads these tables, like every other one.
ALTER TABLE "public"."event_types" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."event_rules" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."member_events" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "public"."event_rule_runs" ENABLE ROW LEVEL SECURITY;

GRANT ALL ON TABLE "public"."event_types" TO "service_role";
GRANT ALL ON TABLE "public"."event_rules" TO "service_role";
GRANT ALL ON TABLE "public"."member_events" TO "service_role";
GRANT ALL ON TABLE "public"."event_rule_runs" TO "service_role";
