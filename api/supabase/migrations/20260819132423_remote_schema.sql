


SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


CREATE EXTENSION IF NOT EXISTS "pg_cron" WITH SCHEMA "pg_catalog";






COMMENT ON SCHEMA "public" IS 'standard public schema';



CREATE EXTENSION IF NOT EXISTS "pg_stat_statements" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "pgcrypto" WITH SCHEMA "extensions";






CREATE EXTENSION IF NOT EXISTS "supabase_vault" WITH SCHEMA "vault";






CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA "extensions";






CREATE TYPE "public"."challengestatus" AS ENUM (
    'assigned',
    'in_progress',
    'completed',
    'expired',
    'cancelled'
);


ALTER TYPE "public"."challengestatus" OWNER TO "postgres";


CREATE TYPE "public"."redemptionsource" AS ENUM (
    'redeemed',
    'assigned'
);


ALTER TYPE "public"."redemptionsource" OWNER TO "postgres";


CREATE TYPE "public"."transactiontype" AS ENUM (
    'earn',
    'spend',
    'adjust'
);


ALTER TYPE "public"."transactiontype" OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."challenge_assignments" (
    "id" "uuid" NOT NULL,
    "challenge_id" "uuid" NOT NULL,
    "member_id" "uuid" NOT NULL,
    "status" "public"."challengestatus" NOT NULL,
    "current_value" integer NOT NULL,
    "assigned_at" timestamp without time zone,
    "completed_at" timestamp without time zone
);


ALTER TABLE "public"."challenge_assignments" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."challenge_segment_assignments" (
    "id" "uuid" NOT NULL,
    "challenge_id" "uuid" NOT NULL,
    "assigned_at" timestamp without time zone NOT NULL,
    "segment_id" "uuid" NOT NULL
);


ALTER TABLE "public"."challenge_segment_assignments" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."challenges" (
    "id" "uuid" NOT NULL,
    "name" character varying NOT NULL,
    "description" "text",
    "target_value" integer NOT NULL,
    "reward_points" integer NOT NULL,
    "reward_id" "uuid",
    "is_active" boolean,
    "starts_at" timestamp without time zone,
    "expires_at" timestamp without time zone,
    "created_at" timestamp without time zone
);


ALTER TABLE "public"."challenges" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."member_attributes" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "key" character varying NOT NULL,
    "label" character varying NOT NULL,
    "type" character varying NOT NULL,
    "options" "jsonb",
    "default_value" "jsonb",
    "created_at" timestamp without time zone DEFAULT ("now"() AT TIME ZONE 'utc'::"text") NOT NULL
);


ALTER TABLE "public"."member_attributes" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."member_segments" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "member_id" "uuid" NOT NULL,
    "segment_id" "uuid" NOT NULL,
    "assigned_at" timestamp without time zone DEFAULT ("now"() AT TIME ZONE 'utc'::"text") NOT NULL
);


ALTER TABLE "public"."member_segments" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."members" (
    "id" "uuid" NOT NULL,
    "name" character varying NOT NULL,
    "email" character varying NOT NULL,
    "phone" character varying,
    "total_points" integer NOT NULL,
    "tier_id" "uuid",
    "created_at" timestamp without time zone,
    "custom_attributes" "jsonb" DEFAULT '{}'::"jsonb" NOT NULL
);


ALTER TABLE "public"."members" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."points_transactions" (
    "id" "uuid" NOT NULL,
    "member_id" "uuid" NOT NULL,
    "points" integer NOT NULL,
    "type" "public"."transactiontype" NOT NULL,
    "description" character varying,
    "created_at" timestamp without time zone
);


ALTER TABLE "public"."points_transactions" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."redemptions" (
    "id" "uuid" NOT NULL,
    "member_id" "uuid" NOT NULL,
    "reward_id" "uuid" NOT NULL,
    "points_spent" integer NOT NULL,
    "created_at" timestamp without time zone,
    "source" "public"."redemptionsource" DEFAULT 'redeemed'::"public"."redemptionsource" NOT NULL
);


ALTER TABLE "public"."redemptions" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."rewards" (
    "id" "uuid" NOT NULL,
    "name" character varying NOT NULL,
    "description" "text",
    "points_cost" integer NOT NULL,
    "stock" integer,
    "is_active" boolean,
    "created_at" timestamp without time zone
);


ALTER TABLE "public"."rewards" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."segments" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "name" character varying NOT NULL,
    "description" "text",
    "color" character varying,
    "created_at" timestamp without time zone DEFAULT ("now"() AT TIME ZONE 'utc'::"text") NOT NULL
);


ALTER TABLE "public"."segments" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."tiers" (
    "id" "uuid" NOT NULL,
    "name" character varying NOT NULL,
    "min_points" integer NOT NULL,
    "multiplier" double precision NOT NULL
);


ALTER TABLE "public"."tiers" OWNER TO "postgres";


ALTER TABLE ONLY "public"."challenge_assignments"
    ADD CONSTRAINT "challenge_assignments_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."challenge_segment_assignments"
    ADD CONSTRAINT "challenge_segment_assignments_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."challenges"
    ADD CONSTRAINT "challenges_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."member_attributes"
    ADD CONSTRAINT "member_attributes_key_key" UNIQUE ("key");



ALTER TABLE ONLY "public"."member_attributes"
    ADD CONSTRAINT "member_attributes_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."member_segments"
    ADD CONSTRAINT "member_segments_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."members"
    ADD CONSTRAINT "members_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."points_transactions"
    ADD CONSTRAINT "points_transactions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."redemptions"
    ADD CONSTRAINT "redemptions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."rewards"
    ADD CONSTRAINT "rewards_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."segments"
    ADD CONSTRAINT "segments_name_key" UNIQUE ("name");



ALTER TABLE ONLY "public"."segments"
    ADD CONSTRAINT "segments_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."tiers"
    ADD CONSTRAINT "tiers_name_key" UNIQUE ("name");



ALTER TABLE ONLY "public"."tiers"
    ADD CONSTRAINT "tiers_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."challenge_assignments"
    ADD CONSTRAINT "uq_challenge_member" UNIQUE ("challenge_id", "member_id");



ALTER TABLE ONLY "public"."challenge_segment_assignments"
    ADD CONSTRAINT "uq_challenge_segment" UNIQUE ("challenge_id", "segment_id");



ALTER TABLE ONLY "public"."member_segments"
    ADD CONSTRAINT "uq_member_segment" UNIQUE ("member_id", "segment_id");



CREATE INDEX "ix_challenge_assignments_member_id" ON "public"."challenge_assignments" USING "btree" ("member_id");



CREATE INDEX "ix_challenge_segment_assignments_challenge_id" ON "public"."challenge_segment_assignments" USING "btree" ("challenge_id");



CREATE INDEX "ix_member_segments_member_id" ON "public"."member_segments" USING "btree" ("member_id");



CREATE INDEX "ix_member_segments_segment_id" ON "public"."member_segments" USING "btree" ("segment_id");



CREATE UNIQUE INDEX "ix_members_email" ON "public"."members" USING "btree" ("email");



ALTER TABLE ONLY "public"."challenge_assignments"
    ADD CONSTRAINT "challenge_assignments_challenge_id_fkey" FOREIGN KEY ("challenge_id") REFERENCES "public"."challenges"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."challenge_assignments"
    ADD CONSTRAINT "challenge_assignments_member_id_fkey" FOREIGN KEY ("member_id") REFERENCES "public"."members"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."challenge_segment_assignments"
    ADD CONSTRAINT "challenge_segment_assignments_challenge_id_fkey" FOREIGN KEY ("challenge_id") REFERENCES "public"."challenges"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."challenge_segment_assignments"
    ADD CONSTRAINT "challenge_segment_assignments_segment_id_fkey" FOREIGN KEY ("segment_id") REFERENCES "public"."segments"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."challenges"
    ADD CONSTRAINT "challenges_reward_id_fkey" FOREIGN KEY ("reward_id") REFERENCES "public"."rewards"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."member_segments"
    ADD CONSTRAINT "member_segments_member_id_fkey" FOREIGN KEY ("member_id") REFERENCES "public"."members"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."member_segments"
    ADD CONSTRAINT "member_segments_segment_id_fkey" FOREIGN KEY ("segment_id") REFERENCES "public"."segments"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."members"
    ADD CONSTRAINT "members_tier_id_fkey" FOREIGN KEY ("tier_id") REFERENCES "public"."tiers"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."points_transactions"
    ADD CONSTRAINT "points_transactions_member_id_fkey" FOREIGN KEY ("member_id") REFERENCES "public"."members"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."redemptions"
    ADD CONSTRAINT "redemptions_member_id_fkey" FOREIGN KEY ("member_id") REFERENCES "public"."members"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."redemptions"
    ADD CONSTRAINT "redemptions_reward_id_fkey" FOREIGN KEY ("reward_id") REFERENCES "public"."rewards"("id");



ALTER TABLE "public"."challenge_assignments" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."challenge_segment_assignments" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."challenges" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."member_attributes" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."member_segments" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."members" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."points_transactions" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."redemptions" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."rewards" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."segments" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."tiers" ENABLE ROW LEVEL SECURITY;




ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";





GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";
































































































































































































GRANT ALL ON TABLE "public"."challenge_assignments" TO "service_role";



GRANT ALL ON TABLE "public"."challenge_segment_assignments" TO "service_role";



GRANT ALL ON TABLE "public"."challenges" TO "service_role";



GRANT ALL ON TABLE "public"."member_attributes" TO "service_role";



GRANT ALL ON TABLE "public"."member_segments" TO "service_role";



GRANT ALL ON TABLE "public"."members" TO "service_role";



GRANT ALL ON TABLE "public"."points_transactions" TO "service_role";



GRANT ALL ON TABLE "public"."redemptions" TO "service_role";



GRANT ALL ON TABLE "public"."rewards" TO "service_role";



GRANT ALL ON TABLE "public"."segments" TO "service_role";



GRANT ALL ON TABLE "public"."tiers" TO "service_role";









ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON SEQUENCES TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON FUNCTIONS TO "service_role";






ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "postgres";
ALTER DEFAULT PRIVILEGES FOR ROLE "postgres" IN SCHEMA "public" GRANT ALL ON TABLES TO "service_role";































drop extension if exists "pg_net";

revoke references on table "public"."challenge_assignments" from "anon";

revoke trigger on table "public"."challenge_assignments" from "anon";

revoke truncate on table "public"."challenge_assignments" from "anon";

revoke references on table "public"."challenge_assignments" from "authenticated";

revoke trigger on table "public"."challenge_assignments" from "authenticated";

revoke truncate on table "public"."challenge_assignments" from "authenticated";

revoke references on table "public"."challenge_segment_assignments" from "anon";

revoke trigger on table "public"."challenge_segment_assignments" from "anon";

revoke truncate on table "public"."challenge_segment_assignments" from "anon";

revoke references on table "public"."challenge_segment_assignments" from "authenticated";

revoke trigger on table "public"."challenge_segment_assignments" from "authenticated";

revoke truncate on table "public"."challenge_segment_assignments" from "authenticated";

revoke references on table "public"."challenges" from "anon";

revoke trigger on table "public"."challenges" from "anon";

revoke truncate on table "public"."challenges" from "anon";

revoke references on table "public"."challenges" from "authenticated";

revoke trigger on table "public"."challenges" from "authenticated";

revoke truncate on table "public"."challenges" from "authenticated";

revoke references on table "public"."member_attributes" from "anon";

revoke trigger on table "public"."member_attributes" from "anon";

revoke truncate on table "public"."member_attributes" from "anon";

revoke references on table "public"."member_attributes" from "authenticated";

revoke trigger on table "public"."member_attributes" from "authenticated";

revoke truncate on table "public"."member_attributes" from "authenticated";

revoke references on table "public"."member_segments" from "anon";

revoke trigger on table "public"."member_segments" from "anon";

revoke truncate on table "public"."member_segments" from "anon";

revoke references on table "public"."member_segments" from "authenticated";

revoke trigger on table "public"."member_segments" from "authenticated";

revoke truncate on table "public"."member_segments" from "authenticated";

revoke references on table "public"."members" from "anon";

revoke trigger on table "public"."members" from "anon";

revoke truncate on table "public"."members" from "anon";

revoke references on table "public"."members" from "authenticated";

revoke trigger on table "public"."members" from "authenticated";

revoke truncate on table "public"."members" from "authenticated";

revoke references on table "public"."points_transactions" from "anon";

revoke trigger on table "public"."points_transactions" from "anon";

revoke truncate on table "public"."points_transactions" from "anon";

revoke references on table "public"."points_transactions" from "authenticated";

revoke trigger on table "public"."points_transactions" from "authenticated";

revoke truncate on table "public"."points_transactions" from "authenticated";

revoke references on table "public"."redemptions" from "anon";

revoke trigger on table "public"."redemptions" from "anon";

revoke truncate on table "public"."redemptions" from "anon";

revoke references on table "public"."redemptions" from "authenticated";

revoke trigger on table "public"."redemptions" from "authenticated";

revoke truncate on table "public"."redemptions" from "authenticated";

revoke references on table "public"."rewards" from "anon";

revoke trigger on table "public"."rewards" from "anon";

revoke truncate on table "public"."rewards" from "anon";

revoke references on table "public"."rewards" from "authenticated";

revoke trigger on table "public"."rewards" from "authenticated";

revoke truncate on table "public"."rewards" from "authenticated";

revoke references on table "public"."segments" from "anon";

revoke trigger on table "public"."segments" from "anon";

revoke truncate on table "public"."segments" from "anon";

revoke references on table "public"."segments" from "authenticated";

revoke trigger on table "public"."segments" from "authenticated";

revoke truncate on table "public"."segments" from "authenticated";

revoke references on table "public"."tiers" from "anon";

revoke trigger on table "public"."tiers" from "anon";

revoke truncate on table "public"."tiers" from "anon";

revoke references on table "public"."tiers" from "authenticated";

revoke trigger on table "public"."tiers" from "authenticated";

revoke truncate on table "public"."tiers" from "authenticated";


