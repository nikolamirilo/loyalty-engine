


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


CREATE TYPE "public"."doitype" AS ENUM (
    'code',
    'link'
);


ALTER TYPE "public"."doitype" OWNER TO "postgres";


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


CREATE OR REPLACE FUNCTION "public"."set_program_id_from_challenge"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
begin
  select program_id into new.program_id from public.challenges where id = new.challenge_id;
  return new;
end $$;


ALTER FUNCTION "public"."set_program_id_from_challenge"() OWNER TO "postgres";


CREATE OR REPLACE FUNCTION "public"."set_program_id_from_member"() RETURNS "trigger"
    LANGUAGE "plpgsql"
    AS $$
begin
  select program_id into new.program_id from public.members where id = new.member_id;
  return new;
end $$;


ALTER FUNCTION "public"."set_program_id_from_member"() OWNER TO "postgres";

SET default_tablespace = '';

SET default_table_access_method = "heap";


CREATE TABLE IF NOT EXISTS "public"."challenge_assignments" (
    "id" "uuid" NOT NULL,
    "challenge_id" "uuid" NOT NULL,
    "member_id" "uuid" NOT NULL,
    "status" "public"."challengestatus" NOT NULL,
    "current_value" integer NOT NULL,
    "assigned_at" timestamp without time zone,
    "completed_at" timestamp without time zone,
    "expires_at" timestamp without time zone,
    "program_id" "uuid" NOT NULL
);


ALTER TABLE "public"."challenge_assignments" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."challenge_segment_assignments" (
    "id" "uuid" NOT NULL,
    "challenge_id" "uuid" NOT NULL,
    "assigned_at" timestamp without time zone NOT NULL,
    "segment_id" "uuid" NOT NULL,
    "program_id" "uuid" NOT NULL
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
    "created_at" timestamp without time zone,
    "expiry_days" integer,
    "program_id" "uuid" NOT NULL,
    CONSTRAINT "challenges_expiry_days_positive" CHECK ((("expiry_days" IS NULL) OR ("expiry_days" > 0)))
);


ALTER TABLE "public"."challenges" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."email_verification_codes" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "identity_id" "uuid" NOT NULL,
    "code_hash" "text" NOT NULL,
    "expires_at" timestamp without time zone NOT NULL,
    "attempts" integer DEFAULT 0 NOT NULL,
    "consumed_at" timestamp without time zone,
    "created_at" timestamp without time zone DEFAULT ("now"() AT TIME ZONE 'utc'::"text") NOT NULL,
    "type" "public"."doitype" DEFAULT 'code'::"public"."doitype" NOT NULL
);


ALTER TABLE "public"."email_verification_codes" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."member_attributes" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "key" character varying NOT NULL,
    "label" character varying NOT NULL,
    "type" character varying NOT NULL,
    "options" "jsonb",
    "default_value" "jsonb",
    "created_at" timestamp without time zone DEFAULT ("now"() AT TIME ZONE 'utc'::"text") NOT NULL,
    "program_id" "uuid" NOT NULL
);


ALTER TABLE "public"."member_attributes" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."member_identities" (
    "id" "uuid" NOT NULL,
    "name" character varying NOT NULL,
    "email" character varying NOT NULL,
    "phone" character varying,
    "email_verified_at" timestamp without time zone,
    "created_at" timestamp without time zone
);


ALTER TABLE "public"."member_identities" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."member_login_codes" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "identity_id" "uuid" NOT NULL,
    "code_hash" "text" NOT NULL,
    "expires_at" timestamp without time zone NOT NULL,
    "attempts" integer DEFAULT 0 NOT NULL,
    "consumed_at" timestamp without time zone,
    "created_at" timestamp without time zone DEFAULT ("now"() AT TIME ZONE 'utc'::"text") NOT NULL
);


ALTER TABLE "public"."member_login_codes" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."member_segments" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "member_id" "uuid" NOT NULL,
    "segment_id" "uuid" NOT NULL,
    "assigned_at" timestamp without time zone DEFAULT ("now"() AT TIME ZONE 'utc'::"text") NOT NULL,
    "program_id" "uuid" NOT NULL
);


ALTER TABLE "public"."member_segments" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."members" (
    "id" "uuid" NOT NULL,
    "total_points" integer NOT NULL,
    "tier_id" "uuid",
    "created_at" timestamp without time zone,
    "custom_attributes" "jsonb" DEFAULT '{}'::"jsonb" NOT NULL,
    "program_id" "uuid" NOT NULL,
    "identity_id" "uuid" NOT NULL
);


ALTER TABLE "public"."members" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."points_transactions" (
    "id" "uuid" NOT NULL,
    "member_id" "uuid" NOT NULL,
    "points" integer NOT NULL,
    "type" "public"."transactiontype" NOT NULL,
    "description" character varying,
    "created_at" timestamp without time zone,
    "program_id" "uuid" NOT NULL
);


ALTER TABLE "public"."points_transactions" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."products" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "name" character varying NOT NULL,
    "description" "text",
    "price_cents" integer NOT NULL,
    "currency" character varying(3) DEFAULT 'EUR'::character varying NOT NULL,
    "category" character varying,
    "is_active" boolean DEFAULT true NOT NULL,
    "created_at" timestamp without time zone DEFAULT ("now"() AT TIME ZONE 'utc'::"text") NOT NULL,
    "program_id" "uuid" NOT NULL,
    CONSTRAINT "products_price_cents_positive" CHECK (("price_cents" > 0))
);


ALTER TABLE "public"."products" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."programs" (
    "id" "uuid" NOT NULL,
    "name" character varying NOT NULL,
    "slug" character varying NOT NULL,
    "description" "text",
    "is_default" boolean DEFAULT false NOT NULL,
    "created_at" timestamp without time zone
);


ALTER TABLE "public"."programs" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."purchases" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "member_id" "uuid" NOT NULL,
    "product_id" "uuid",
    "product_name" character varying NOT NULL,
    "quantity" integer DEFAULT 1 NOT NULL,
    "unit_price_cents" integer NOT NULL,
    "total_cents" integer NOT NULL,
    "currency" character varying(3) DEFAULT 'EUR'::character varying NOT NULL,
    "created_at" timestamp without time zone DEFAULT ("now"() AT TIME ZONE 'utc'::"text") NOT NULL,
    "program_id" "uuid" NOT NULL,
    CONSTRAINT "purchases_quantity_positive" CHECK (("quantity" > 0))
);


ALTER TABLE "public"."purchases" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."redemptions" (
    "id" "uuid" NOT NULL,
    "member_id" "uuid" NOT NULL,
    "reward_id" "uuid" NOT NULL,
    "points_spent" integer NOT NULL,
    "created_at" timestamp without time zone,
    "source" "public"."redemptionsource" DEFAULT 'redeemed'::"public"."redemptionsource" NOT NULL,
    "program_id" "uuid" NOT NULL
);


ALTER TABLE "public"."redemptions" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."rewards" (
    "id" "uuid" NOT NULL,
    "name" character varying NOT NULL,
    "description" "text",
    "points_cost" integer NOT NULL,
    "stock" integer,
    "is_active" boolean,
    "created_at" timestamp without time zone,
    "program_id" "uuid" NOT NULL
);


ALTER TABLE "public"."rewards" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."segments" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "name" character varying NOT NULL,
    "description" "text",
    "color" character varying,
    "created_at" timestamp without time zone DEFAULT ("now"() AT TIME ZONE 'utc'::"text") NOT NULL,
    "program_id" "uuid" NOT NULL
);


ALTER TABLE "public"."segments" OWNER TO "postgres";


CREATE TABLE IF NOT EXISTS "public"."tiers" (
    "id" "uuid" NOT NULL,
    "name" character varying NOT NULL,
    "min_points" integer NOT NULL,
    "multiplier" double precision NOT NULL,
    "program_id" "uuid" NOT NULL
);


ALTER TABLE "public"."tiers" OWNER TO "postgres";


ALTER TABLE ONLY "public"."challenge_assignments"
    ADD CONSTRAINT "challenge_assignments_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."challenge_segment_assignments"
    ADD CONSTRAINT "challenge_segment_assignments_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."challenges"
    ADD CONSTRAINT "challenges_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."email_verification_codes"
    ADD CONSTRAINT "email_verification_codes_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."member_attributes"
    ADD CONSTRAINT "member_attributes_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."member_identities"
    ADD CONSTRAINT "member_identities_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."member_login_codes"
    ADD CONSTRAINT "member_login_codes_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."member_segments"
    ADD CONSTRAINT "member_segments_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."members"
    ADD CONSTRAINT "members_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."points_transactions"
    ADD CONSTRAINT "points_transactions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."products"
    ADD CONSTRAINT "products_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."programs"
    ADD CONSTRAINT "programs_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."purchases"
    ADD CONSTRAINT "purchases_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."redemptions"
    ADD CONSTRAINT "redemptions_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."rewards"
    ADD CONSTRAINT "rewards_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."segments"
    ADD CONSTRAINT "segments_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."tiers"
    ADD CONSTRAINT "tiers_pkey" PRIMARY KEY ("id");



ALTER TABLE ONLY "public"."challenge_assignments"
    ADD CONSTRAINT "uq_challenge_member" UNIQUE ("challenge_id", "member_id");



ALTER TABLE ONLY "public"."challenge_segment_assignments"
    ADD CONSTRAINT "uq_challenge_segment" UNIQUE ("challenge_id", "segment_id");



ALTER TABLE ONLY "public"."member_segments"
    ADD CONSTRAINT "uq_member_segment" UNIQUE ("member_id", "segment_id");



ALTER TABLE ONLY "public"."member_attributes"
    ADD CONSTRAINT "uq_program_attribute_key" UNIQUE ("program_id", "key");



ALTER TABLE ONLY "public"."members"
    ADD CONSTRAINT "uq_program_identity" UNIQUE ("program_id", "identity_id");



ALTER TABLE ONLY "public"."segments"
    ADD CONSTRAINT "uq_program_segment_name" UNIQUE ("program_id", "name");



ALTER TABLE ONLY "public"."tiers"
    ADD CONSTRAINT "uq_program_tier_name" UNIQUE ("program_id", "name");



CREATE INDEX "ix_challenge_assignments_member_id" ON "public"."challenge_assignments" USING "btree" ("member_id");



CREATE INDEX "ix_challenge_assignments_program_id" ON "public"."challenge_assignments" USING "btree" ("program_id");



CREATE INDEX "ix_challenge_segment_assignments_challenge_id" ON "public"."challenge_segment_assignments" USING "btree" ("challenge_id");



CREATE INDEX "ix_challenge_segment_assignments_program_id" ON "public"."challenge_segment_assignments" USING "btree" ("program_id");



CREATE INDEX "ix_challenges_program_id" ON "public"."challenges" USING "btree" ("program_id");



CREATE INDEX "ix_email_verification_codes_member_id" ON "public"."email_verification_codes" USING "btree" ("identity_id");



CREATE INDEX "ix_member_attributes_program_id" ON "public"."member_attributes" USING "btree" ("program_id");



CREATE UNIQUE INDEX "ix_member_identities_email" ON "public"."member_identities" USING "btree" ("email");



CREATE INDEX "ix_member_login_codes_member_id" ON "public"."member_login_codes" USING "btree" ("identity_id");



CREATE INDEX "ix_member_segments_member_id" ON "public"."member_segments" USING "btree" ("member_id");



CREATE INDEX "ix_member_segments_program_id" ON "public"."member_segments" USING "btree" ("program_id");



CREATE INDEX "ix_member_segments_segment_id" ON "public"."member_segments" USING "btree" ("segment_id");



CREATE INDEX "ix_members_identity_id" ON "public"."members" USING "btree" ("identity_id");



CREATE INDEX "ix_members_program_id" ON "public"."members" USING "btree" ("program_id");



CREATE INDEX "ix_points_transactions_program_id" ON "public"."points_transactions" USING "btree" ("program_id");



CREATE INDEX "ix_products_is_active" ON "public"."products" USING "btree" ("is_active");



CREATE INDEX "ix_products_program_id" ON "public"."products" USING "btree" ("program_id");



CREATE UNIQUE INDEX "ix_programs_slug" ON "public"."programs" USING "btree" ("slug");



CREATE INDEX "ix_purchases_member_id_created_at" ON "public"."purchases" USING "btree" ("member_id", "created_at" DESC);



CREATE INDEX "ix_purchases_product_id" ON "public"."purchases" USING "btree" ("product_id");



CREATE INDEX "ix_purchases_program_id" ON "public"."purchases" USING "btree" ("program_id");



CREATE INDEX "ix_redemptions_program_id" ON "public"."redemptions" USING "btree" ("program_id");



CREATE INDEX "ix_rewards_program_id" ON "public"."rewards" USING "btree" ("program_id");



CREATE INDEX "ix_segments_program_id" ON "public"."segments" USING "btree" ("program_id");



CREATE INDEX "ix_tiers_program_id" ON "public"."tiers" USING "btree" ("program_id");



CREATE UNIQUE INDEX "uq_programs_single_default" ON "public"."programs" USING "btree" ("is_default") WHERE "is_default";



CREATE OR REPLACE TRIGGER "challenge_assignments_program_id" BEFORE INSERT OR UPDATE ON "public"."challenge_assignments" FOR EACH ROW EXECUTE FUNCTION "public"."set_program_id_from_member"();



CREATE OR REPLACE TRIGGER "challenge_segment_assignments_program_id" BEFORE INSERT OR UPDATE ON "public"."challenge_segment_assignments" FOR EACH ROW EXECUTE FUNCTION "public"."set_program_id_from_challenge"();



CREATE OR REPLACE TRIGGER "member_segments_program_id" BEFORE INSERT OR UPDATE ON "public"."member_segments" FOR EACH ROW EXECUTE FUNCTION "public"."set_program_id_from_member"();



CREATE OR REPLACE TRIGGER "points_transactions_program_id" BEFORE INSERT OR UPDATE ON "public"."points_transactions" FOR EACH ROW EXECUTE FUNCTION "public"."set_program_id_from_member"();



CREATE OR REPLACE TRIGGER "purchases_program_id" BEFORE INSERT OR UPDATE ON "public"."purchases" FOR EACH ROW EXECUTE FUNCTION "public"."set_program_id_from_member"();



CREATE OR REPLACE TRIGGER "redemptions_program_id" BEFORE INSERT OR UPDATE ON "public"."redemptions" FOR EACH ROW EXECUTE FUNCTION "public"."set_program_id_from_member"();



ALTER TABLE ONLY "public"."challenge_assignments"
    ADD CONSTRAINT "challenge_assignments_challenge_id_fkey" FOREIGN KEY ("challenge_id") REFERENCES "public"."challenges"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."challenge_assignments"
    ADD CONSTRAINT "challenge_assignments_member_id_fkey" FOREIGN KEY ("member_id") REFERENCES "public"."members"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."challenge_assignments"
    ADD CONSTRAINT "challenge_assignments_program_id_fkey" FOREIGN KEY ("program_id") REFERENCES "public"."programs"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."challenge_segment_assignments"
    ADD CONSTRAINT "challenge_segment_assignments_challenge_id_fkey" FOREIGN KEY ("challenge_id") REFERENCES "public"."challenges"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."challenge_segment_assignments"
    ADD CONSTRAINT "challenge_segment_assignments_program_id_fkey" FOREIGN KEY ("program_id") REFERENCES "public"."programs"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."challenge_segment_assignments"
    ADD CONSTRAINT "challenge_segment_assignments_segment_id_fkey" FOREIGN KEY ("segment_id") REFERENCES "public"."segments"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."challenges"
    ADD CONSTRAINT "challenges_program_id_fkey" FOREIGN KEY ("program_id") REFERENCES "public"."programs"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."challenges"
    ADD CONSTRAINT "challenges_reward_id_fkey" FOREIGN KEY ("reward_id") REFERENCES "public"."rewards"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."email_verification_codes"
    ADD CONSTRAINT "email_verification_codes_identity_id_fkey" FOREIGN KEY ("identity_id") REFERENCES "public"."member_identities"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."member_attributes"
    ADD CONSTRAINT "member_attributes_program_id_fkey" FOREIGN KEY ("program_id") REFERENCES "public"."programs"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."member_login_codes"
    ADD CONSTRAINT "member_login_codes_identity_id_fkey" FOREIGN KEY ("identity_id") REFERENCES "public"."member_identities"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."member_segments"
    ADD CONSTRAINT "member_segments_member_id_fkey" FOREIGN KEY ("member_id") REFERENCES "public"."members"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."member_segments"
    ADD CONSTRAINT "member_segments_program_id_fkey" FOREIGN KEY ("program_id") REFERENCES "public"."programs"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."member_segments"
    ADD CONSTRAINT "member_segments_segment_id_fkey" FOREIGN KEY ("segment_id") REFERENCES "public"."segments"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."members"
    ADD CONSTRAINT "members_identity_id_fkey" FOREIGN KEY ("identity_id") REFERENCES "public"."member_identities"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."members"
    ADD CONSTRAINT "members_program_id_fkey" FOREIGN KEY ("program_id") REFERENCES "public"."programs"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."members"
    ADD CONSTRAINT "members_tier_id_fkey" FOREIGN KEY ("tier_id") REFERENCES "public"."tiers"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."points_transactions"
    ADD CONSTRAINT "points_transactions_member_id_fkey" FOREIGN KEY ("member_id") REFERENCES "public"."members"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."points_transactions"
    ADD CONSTRAINT "points_transactions_program_id_fkey" FOREIGN KEY ("program_id") REFERENCES "public"."programs"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."products"
    ADD CONSTRAINT "products_program_id_fkey" FOREIGN KEY ("program_id") REFERENCES "public"."programs"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."purchases"
    ADD CONSTRAINT "purchases_member_id_fkey" FOREIGN KEY ("member_id") REFERENCES "public"."members"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."purchases"
    ADD CONSTRAINT "purchases_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."products"("id") ON DELETE SET NULL;



ALTER TABLE ONLY "public"."purchases"
    ADD CONSTRAINT "purchases_program_id_fkey" FOREIGN KEY ("program_id") REFERENCES "public"."programs"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."redemptions"
    ADD CONSTRAINT "redemptions_member_id_fkey" FOREIGN KEY ("member_id") REFERENCES "public"."members"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."redemptions"
    ADD CONSTRAINT "redemptions_program_id_fkey" FOREIGN KEY ("program_id") REFERENCES "public"."programs"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."redemptions"
    ADD CONSTRAINT "redemptions_reward_id_fkey" FOREIGN KEY ("reward_id") REFERENCES "public"."rewards"("id");



ALTER TABLE ONLY "public"."rewards"
    ADD CONSTRAINT "rewards_program_id_fkey" FOREIGN KEY ("program_id") REFERENCES "public"."programs"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."segments"
    ADD CONSTRAINT "segments_program_id_fkey" FOREIGN KEY ("program_id") REFERENCES "public"."programs"("id") ON DELETE CASCADE;



ALTER TABLE ONLY "public"."tiers"
    ADD CONSTRAINT "tiers_program_id_fkey" FOREIGN KEY ("program_id") REFERENCES "public"."programs"("id") ON DELETE CASCADE;



ALTER TABLE "public"."challenge_assignments" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."challenge_segment_assignments" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."challenges" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."email_verification_codes" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."member_attributes" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."member_identities" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."member_login_codes" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."member_segments" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."members" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."points_transactions" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."products" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."programs" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."purchases" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."redemptions" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."rewards" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."segments" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."tiers" ENABLE ROW LEVEL SECURITY;




ALTER PUBLICATION "supabase_realtime" OWNER TO "postgres";





GRANT USAGE ON SCHEMA "public" TO "postgres";
GRANT USAGE ON SCHEMA "public" TO "anon";
GRANT USAGE ON SCHEMA "public" TO "authenticated";
GRANT USAGE ON SCHEMA "public" TO "service_role";











































































































































































GRANT ALL ON FUNCTION "public"."set_program_id_from_challenge"() TO "service_role";



GRANT ALL ON FUNCTION "public"."set_program_id_from_member"() TO "service_role";
























GRANT ALL ON TABLE "public"."challenge_assignments" TO "service_role";



GRANT ALL ON TABLE "public"."challenge_segment_assignments" TO "service_role";



GRANT ALL ON TABLE "public"."challenges" TO "service_role";



GRANT ALL ON TABLE "public"."email_verification_codes" TO "service_role";



GRANT ALL ON TABLE "public"."member_attributes" TO "service_role";



GRANT ALL ON TABLE "public"."member_identities" TO "service_role";



GRANT ALL ON TABLE "public"."member_login_codes" TO "service_role";



GRANT ALL ON TABLE "public"."member_segments" TO "service_role";



GRANT ALL ON TABLE "public"."members" TO "service_role";



GRANT ALL ON TABLE "public"."points_transactions" TO "service_role";



GRANT ALL ON TABLE "public"."products" TO "service_role";



GRANT ALL ON TABLE "public"."programs" TO "service_role";



GRANT ALL ON TABLE "public"."purchases" TO "service_role";



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

drop trigger if exists "challenge_assignments_program_id" on "public"."challenge_assignments";

drop trigger if exists "challenge_segment_assignments_program_id" on "public"."challenge_segment_assignments";

drop trigger if exists "member_segments_program_id" on "public"."member_segments";

drop trigger if exists "points_transactions_program_id" on "public"."points_transactions";

drop trigger if exists "purchases_program_id" on "public"."purchases";

drop trigger if exists "redemptions_program_id" on "public"."redemptions";

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

revoke references on table "public"."email_verification_codes" from "anon";

revoke trigger on table "public"."email_verification_codes" from "anon";

revoke truncate on table "public"."email_verification_codes" from "anon";

revoke references on table "public"."email_verification_codes" from "authenticated";

revoke trigger on table "public"."email_verification_codes" from "authenticated";

revoke truncate on table "public"."email_verification_codes" from "authenticated";

revoke references on table "public"."member_attributes" from "anon";

revoke trigger on table "public"."member_attributes" from "anon";

revoke truncate on table "public"."member_attributes" from "anon";

revoke references on table "public"."member_attributes" from "authenticated";

revoke trigger on table "public"."member_attributes" from "authenticated";

revoke truncate on table "public"."member_attributes" from "authenticated";

revoke references on table "public"."member_identities" from "anon";

revoke trigger on table "public"."member_identities" from "anon";

revoke truncate on table "public"."member_identities" from "anon";

revoke references on table "public"."member_identities" from "authenticated";

revoke trigger on table "public"."member_identities" from "authenticated";

revoke truncate on table "public"."member_identities" from "authenticated";

revoke references on table "public"."member_login_codes" from "anon";

revoke trigger on table "public"."member_login_codes" from "anon";

revoke truncate on table "public"."member_login_codes" from "anon";

revoke references on table "public"."member_login_codes" from "authenticated";

revoke trigger on table "public"."member_login_codes" from "authenticated";

revoke truncate on table "public"."member_login_codes" from "authenticated";

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

revoke references on table "public"."products" from "anon";

revoke trigger on table "public"."products" from "anon";

revoke truncate on table "public"."products" from "anon";

revoke references on table "public"."products" from "authenticated";

revoke trigger on table "public"."products" from "authenticated";

revoke truncate on table "public"."products" from "authenticated";

revoke references on table "public"."programs" from "anon";

revoke trigger on table "public"."programs" from "anon";

revoke truncate on table "public"."programs" from "anon";

revoke references on table "public"."programs" from "authenticated";

revoke trigger on table "public"."programs" from "authenticated";

revoke truncate on table "public"."programs" from "authenticated";

revoke references on table "public"."purchases" from "anon";

revoke trigger on table "public"."purchases" from "anon";

revoke truncate on table "public"."purchases" from "anon";

revoke references on table "public"."purchases" from "authenticated";

revoke trigger on table "public"."purchases" from "authenticated";

revoke truncate on table "public"."purchases" from "authenticated";

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

alter table "public"."challenge_assignments" drop constraint "challenge_assignments_challenge_id_fkey";

alter table "public"."challenge_assignments" drop constraint "challenge_assignments_member_id_fkey";

alter table "public"."challenge_assignments" drop constraint "challenge_assignments_program_id_fkey";

alter table "public"."challenge_segment_assignments" drop constraint "challenge_segment_assignments_challenge_id_fkey";

alter table "public"."challenge_segment_assignments" drop constraint "challenge_segment_assignments_program_id_fkey";

alter table "public"."challenge_segment_assignments" drop constraint "challenge_segment_assignments_segment_id_fkey";

alter table "public"."challenges" drop constraint "challenges_program_id_fkey";

alter table "public"."challenges" drop constraint "challenges_reward_id_fkey";

alter table "public"."email_verification_codes" drop constraint "email_verification_codes_identity_id_fkey";

alter table "public"."member_attributes" drop constraint "member_attributes_program_id_fkey";

alter table "public"."member_login_codes" drop constraint "member_login_codes_identity_id_fkey";

alter table "public"."member_segments" drop constraint "member_segments_member_id_fkey";

alter table "public"."member_segments" drop constraint "member_segments_program_id_fkey";

alter table "public"."member_segments" drop constraint "member_segments_segment_id_fkey";

alter table "public"."members" drop constraint "members_identity_id_fkey";

alter table "public"."members" drop constraint "members_program_id_fkey";

alter table "public"."members" drop constraint "members_tier_id_fkey";

alter table "public"."points_transactions" drop constraint "points_transactions_member_id_fkey";

alter table "public"."points_transactions" drop constraint "points_transactions_program_id_fkey";

alter table "public"."products" drop constraint "products_program_id_fkey";

alter table "public"."purchases" drop constraint "purchases_member_id_fkey";

alter table "public"."purchases" drop constraint "purchases_product_id_fkey";

alter table "public"."purchases" drop constraint "purchases_program_id_fkey";

alter table "public"."redemptions" drop constraint "redemptions_member_id_fkey";

alter table "public"."redemptions" drop constraint "redemptions_program_id_fkey";

alter table "public"."redemptions" drop constraint "redemptions_reward_id_fkey";

alter table "public"."rewards" drop constraint "rewards_program_id_fkey";

alter table "public"."segments" drop constraint "segments_program_id_fkey";

alter table "public"."tiers" drop constraint "tiers_program_id_fkey";

alter table "public"."challenge_assignments" alter column "status" set data type public.challengestatus using "status"::text::public.challengestatus;

alter table "public"."email_verification_codes" alter column "type" set default 'code'::public.doitype;

alter table "public"."email_verification_codes" alter column "type" set data type public.doitype using "type"::text::public.doitype;

alter table "public"."points_transactions" alter column "type" set data type public.transactiontype using "type"::text::public.transactiontype;

alter table "public"."redemptions" alter column "source" set default 'redeemed'::public.redemptionsource;

alter table "public"."redemptions" alter column "source" set data type public.redemptionsource using "source"::text::public.redemptionsource;

alter table "public"."challenge_assignments" add constraint "challenge_assignments_challenge_id_fkey" FOREIGN KEY (challenge_id) REFERENCES public.challenges(id) ON DELETE CASCADE not valid;

alter table "public"."challenge_assignments" validate constraint "challenge_assignments_challenge_id_fkey";

alter table "public"."challenge_assignments" add constraint "challenge_assignments_member_id_fkey" FOREIGN KEY (member_id) REFERENCES public.members(id) ON DELETE CASCADE not valid;

alter table "public"."challenge_assignments" validate constraint "challenge_assignments_member_id_fkey";

alter table "public"."challenge_assignments" add constraint "challenge_assignments_program_id_fkey" FOREIGN KEY (program_id) REFERENCES public.programs(id) ON DELETE CASCADE not valid;

alter table "public"."challenge_assignments" validate constraint "challenge_assignments_program_id_fkey";

alter table "public"."challenge_segment_assignments" add constraint "challenge_segment_assignments_challenge_id_fkey" FOREIGN KEY (challenge_id) REFERENCES public.challenges(id) ON DELETE CASCADE not valid;

alter table "public"."challenge_segment_assignments" validate constraint "challenge_segment_assignments_challenge_id_fkey";

alter table "public"."challenge_segment_assignments" add constraint "challenge_segment_assignments_program_id_fkey" FOREIGN KEY (program_id) REFERENCES public.programs(id) ON DELETE CASCADE not valid;

alter table "public"."challenge_segment_assignments" validate constraint "challenge_segment_assignments_program_id_fkey";

alter table "public"."challenge_segment_assignments" add constraint "challenge_segment_assignments_segment_id_fkey" FOREIGN KEY (segment_id) REFERENCES public.segments(id) ON DELETE CASCADE not valid;

alter table "public"."challenge_segment_assignments" validate constraint "challenge_segment_assignments_segment_id_fkey";

alter table "public"."challenges" add constraint "challenges_program_id_fkey" FOREIGN KEY (program_id) REFERENCES public.programs(id) ON DELETE CASCADE not valid;

alter table "public"."challenges" validate constraint "challenges_program_id_fkey";

alter table "public"."challenges" add constraint "challenges_reward_id_fkey" FOREIGN KEY (reward_id) REFERENCES public.rewards(id) ON DELETE SET NULL not valid;

alter table "public"."challenges" validate constraint "challenges_reward_id_fkey";

alter table "public"."email_verification_codes" add constraint "email_verification_codes_identity_id_fkey" FOREIGN KEY (identity_id) REFERENCES public.member_identities(id) ON DELETE CASCADE not valid;

alter table "public"."email_verification_codes" validate constraint "email_verification_codes_identity_id_fkey";

alter table "public"."member_attributes" add constraint "member_attributes_program_id_fkey" FOREIGN KEY (program_id) REFERENCES public.programs(id) ON DELETE CASCADE not valid;

alter table "public"."member_attributes" validate constraint "member_attributes_program_id_fkey";

alter table "public"."member_login_codes" add constraint "member_login_codes_identity_id_fkey" FOREIGN KEY (identity_id) REFERENCES public.member_identities(id) ON DELETE CASCADE not valid;

alter table "public"."member_login_codes" validate constraint "member_login_codes_identity_id_fkey";

alter table "public"."member_segments" add constraint "member_segments_member_id_fkey" FOREIGN KEY (member_id) REFERENCES public.members(id) ON DELETE CASCADE not valid;

alter table "public"."member_segments" validate constraint "member_segments_member_id_fkey";

alter table "public"."member_segments" add constraint "member_segments_program_id_fkey" FOREIGN KEY (program_id) REFERENCES public.programs(id) ON DELETE CASCADE not valid;

alter table "public"."member_segments" validate constraint "member_segments_program_id_fkey";

alter table "public"."member_segments" add constraint "member_segments_segment_id_fkey" FOREIGN KEY (segment_id) REFERENCES public.segments(id) ON DELETE CASCADE not valid;

alter table "public"."member_segments" validate constraint "member_segments_segment_id_fkey";

alter table "public"."members" add constraint "members_identity_id_fkey" FOREIGN KEY (identity_id) REFERENCES public.member_identities(id) ON DELETE CASCADE not valid;

alter table "public"."members" validate constraint "members_identity_id_fkey";

alter table "public"."members" add constraint "members_program_id_fkey" FOREIGN KEY (program_id) REFERENCES public.programs(id) ON DELETE CASCADE not valid;

alter table "public"."members" validate constraint "members_program_id_fkey";

alter table "public"."members" add constraint "members_tier_id_fkey" FOREIGN KEY (tier_id) REFERENCES public.tiers(id) ON DELETE SET NULL not valid;

alter table "public"."members" validate constraint "members_tier_id_fkey";

alter table "public"."points_transactions" add constraint "points_transactions_member_id_fkey" FOREIGN KEY (member_id) REFERENCES public.members(id) ON DELETE CASCADE not valid;

alter table "public"."points_transactions" validate constraint "points_transactions_member_id_fkey";

alter table "public"."points_transactions" add constraint "points_transactions_program_id_fkey" FOREIGN KEY (program_id) REFERENCES public.programs(id) ON DELETE CASCADE not valid;

alter table "public"."points_transactions" validate constraint "points_transactions_program_id_fkey";

alter table "public"."products" add constraint "products_program_id_fkey" FOREIGN KEY (program_id) REFERENCES public.programs(id) ON DELETE CASCADE not valid;

alter table "public"."products" validate constraint "products_program_id_fkey";

alter table "public"."purchases" add constraint "purchases_member_id_fkey" FOREIGN KEY (member_id) REFERENCES public.members(id) ON DELETE CASCADE not valid;

alter table "public"."purchases" validate constraint "purchases_member_id_fkey";

alter table "public"."purchases" add constraint "purchases_product_id_fkey" FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE SET NULL not valid;

alter table "public"."purchases" validate constraint "purchases_product_id_fkey";

alter table "public"."purchases" add constraint "purchases_program_id_fkey" FOREIGN KEY (program_id) REFERENCES public.programs(id) ON DELETE CASCADE not valid;

alter table "public"."purchases" validate constraint "purchases_program_id_fkey";

alter table "public"."redemptions" add constraint "redemptions_member_id_fkey" FOREIGN KEY (member_id) REFERENCES public.members(id) ON DELETE CASCADE not valid;

alter table "public"."redemptions" validate constraint "redemptions_member_id_fkey";

alter table "public"."redemptions" add constraint "redemptions_program_id_fkey" FOREIGN KEY (program_id) REFERENCES public.programs(id) ON DELETE CASCADE not valid;

alter table "public"."redemptions" validate constraint "redemptions_program_id_fkey";

alter table "public"."redemptions" add constraint "redemptions_reward_id_fkey" FOREIGN KEY (reward_id) REFERENCES public.rewards(id) not valid;

alter table "public"."redemptions" validate constraint "redemptions_reward_id_fkey";

alter table "public"."rewards" add constraint "rewards_program_id_fkey" FOREIGN KEY (program_id) REFERENCES public.programs(id) ON DELETE CASCADE not valid;

alter table "public"."rewards" validate constraint "rewards_program_id_fkey";

alter table "public"."segments" add constraint "segments_program_id_fkey" FOREIGN KEY (program_id) REFERENCES public.programs(id) ON DELETE CASCADE not valid;

alter table "public"."segments" validate constraint "segments_program_id_fkey";

alter table "public"."tiers" add constraint "tiers_program_id_fkey" FOREIGN KEY (program_id) REFERENCES public.programs(id) ON DELETE CASCADE not valid;

alter table "public"."tiers" validate constraint "tiers_program_id_fkey";

CREATE TRIGGER challenge_assignments_program_id BEFORE INSERT OR UPDATE ON public.challenge_assignments FOR EACH ROW EXECUTE FUNCTION public.set_program_id_from_member();

CREATE TRIGGER challenge_segment_assignments_program_id BEFORE INSERT OR UPDATE ON public.challenge_segment_assignments FOR EACH ROW EXECUTE FUNCTION public.set_program_id_from_challenge();

CREATE TRIGGER member_segments_program_id BEFORE INSERT OR UPDATE ON public.member_segments FOR EACH ROW EXECUTE FUNCTION public.set_program_id_from_member();

CREATE TRIGGER points_transactions_program_id BEFORE INSERT OR UPDATE ON public.points_transactions FOR EACH ROW EXECUTE FUNCTION public.set_program_id_from_member();

CREATE TRIGGER purchases_program_id BEFORE INSERT OR UPDATE ON public.purchases FOR EACH ROW EXECUTE FUNCTION public.set_program_id_from_member();

CREATE TRIGGER redemptions_program_id BEFORE INSERT OR UPDATE ON public.redemptions FOR EACH ROW EXECUTE FUNCTION public.set_program_id_from_member();


