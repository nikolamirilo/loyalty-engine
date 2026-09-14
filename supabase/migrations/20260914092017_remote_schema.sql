create extension if not exists "pg_cron" with schema "pg_catalog";

drop extension if exists "pg_net";

create type "public"."challengestatus" as enum ('assigned', 'in_progress', 'completed', 'expired', 'cancelled');

create type "public"."doitype" as enum ('code', 'link');

create type "public"."redemptionsource" as enum ('redeemed', 'assigned');

create type "public"."transactiontype" as enum ('earn', 'spend', 'adjust');


  create table "public"."challenge_assignments" (
    "id" uuid not null,
    "challenge_id" uuid not null,
    "member_id" uuid not null,
    "status" public.challengestatus not null,
    "current_value" integer not null,
    "assigned_at" timestamp without time zone,
    "completed_at" timestamp without time zone,
    "expires_at" timestamp without time zone
      );


alter table "public"."challenge_assignments" enable row level security;


  create table "public"."challenge_segment_assignments" (
    "id" uuid not null,
    "challenge_id" uuid not null,
    "assigned_at" timestamp without time zone not null,
    "segment_id" uuid not null
      );


alter table "public"."challenge_segment_assignments" enable row level security;


  create table "public"."challenges" (
    "id" uuid not null,
    "name" character varying not null,
    "description" text,
    "target_value" integer not null,
    "reward_points" integer not null,
    "reward_id" uuid,
    "is_active" boolean,
    "starts_at" timestamp without time zone,
    "expires_at" timestamp without time zone,
    "created_at" timestamp without time zone,
    "expiry_days" integer
      );


alter table "public"."challenges" enable row level security;


  create table "public"."email_verification_codes" (
    "id" uuid not null default gen_random_uuid(),
    "member_id" uuid not null,
    "code_hash" text not null,
    "expires_at" timestamp without time zone not null,
    "attempts" integer not null default 0,
    "consumed_at" timestamp without time zone,
    "created_at" timestamp without time zone not null default (now() AT TIME ZONE 'utc'::text),
    "type" public.doitype not null default 'code'::public.doitype
      );


alter table "public"."email_verification_codes" enable row level security;


  create table "public"."member_attributes" (
    "id" uuid not null default gen_random_uuid(),
    "key" character varying not null,
    "label" character varying not null,
    "type" character varying not null,
    "options" jsonb,
    "default_value" jsonb,
    "created_at" timestamp without time zone not null default (now() AT TIME ZONE 'utc'::text)
      );


alter table "public"."member_attributes" enable row level security;


  create table "public"."member_login_codes" (
    "id" uuid not null default gen_random_uuid(),
    "member_id" uuid not null,
    "code_hash" text not null,
    "expires_at" timestamp without time zone not null,
    "attempts" integer not null default 0,
    "consumed_at" timestamp without time zone,
    "created_at" timestamp without time zone not null default (now() AT TIME ZONE 'utc'::text)
      );


alter table "public"."member_login_codes" enable row level security;


  create table "public"."member_segments" (
    "id" uuid not null default gen_random_uuid(),
    "member_id" uuid not null,
    "segment_id" uuid not null,
    "assigned_at" timestamp without time zone not null default (now() AT TIME ZONE 'utc'::text)
      );


alter table "public"."member_segments" enable row level security;


  create table "public"."members" (
    "id" uuid not null,
    "name" character varying not null,
    "email" character varying not null,
    "phone" character varying,
    "total_points" integer not null,
    "tier_id" uuid,
    "created_at" timestamp without time zone,
    "custom_attributes" jsonb not null default '{}'::jsonb,
    "email_verified_at" timestamp without time zone
      );


alter table "public"."members" enable row level security;


  create table "public"."points_transactions" (
    "id" uuid not null,
    "member_id" uuid not null,
    "points" integer not null,
    "type" public.transactiontype not null,
    "description" character varying,
    "created_at" timestamp without time zone
      );


alter table "public"."points_transactions" enable row level security;


  create table "public"."products" (
    "id" uuid not null default gen_random_uuid(),
    "name" character varying not null,
    "description" text,
    "price_cents" integer not null,
    "currency" character varying(3) not null default 'EUR'::character varying,
    "category" character varying,
    "is_active" boolean not null default true,
    "created_at" timestamp without time zone not null default (now() AT TIME ZONE 'utc'::text)
      );


alter table "public"."products" enable row level security;


  create table "public"."purchases" (
    "id" uuid not null default gen_random_uuid(),
    "member_id" uuid not null,
    "product_id" uuid,
    "product_name" character varying not null,
    "quantity" integer not null default 1,
    "unit_price_cents" integer not null,
    "total_cents" integer not null,
    "currency" character varying(3) not null default 'EUR'::character varying,
    "created_at" timestamp without time zone not null default (now() AT TIME ZONE 'utc'::text)
      );


alter table "public"."purchases" enable row level security;


  create table "public"."redemptions" (
    "id" uuid not null,
    "member_id" uuid not null,
    "reward_id" uuid not null,
    "points_spent" integer not null,
    "created_at" timestamp without time zone,
    "source" public.redemptionsource not null default 'redeemed'::public.redemptionsource
      );


alter table "public"."redemptions" enable row level security;


  create table "public"."rewards" (
    "id" uuid not null,
    "name" character varying not null,
    "description" text,
    "points_cost" integer not null,
    "stock" integer,
    "is_active" boolean,
    "created_at" timestamp without time zone
      );


alter table "public"."rewards" enable row level security;


  create table "public"."segments" (
    "id" uuid not null default gen_random_uuid(),
    "name" character varying not null,
    "description" text,
    "color" character varying,
    "created_at" timestamp without time zone not null default (now() AT TIME ZONE 'utc'::text)
      );


alter table "public"."segments" enable row level security;


  create table "public"."tiers" (
    "id" uuid not null,
    "name" character varying not null,
    "min_points" integer not null,
    "multiplier" double precision not null
      );


alter table "public"."tiers" enable row level security;

CREATE UNIQUE INDEX challenge_assignments_pkey ON public.challenge_assignments USING btree (id);

CREATE UNIQUE INDEX challenge_segment_assignments_pkey ON public.challenge_segment_assignments USING btree (id);

CREATE UNIQUE INDEX challenges_pkey ON public.challenges USING btree (id);

CREATE UNIQUE INDEX email_verification_codes_pkey ON public.email_verification_codes USING btree (id);

CREATE INDEX ix_challenge_assignments_member_id ON public.challenge_assignments USING btree (member_id);

CREATE INDEX ix_challenge_segment_assignments_challenge_id ON public.challenge_segment_assignments USING btree (challenge_id);

CREATE INDEX ix_email_verification_codes_member_id ON public.email_verification_codes USING btree (member_id);

CREATE INDEX ix_member_login_codes_member_id ON public.member_login_codes USING btree (member_id);

CREATE INDEX ix_member_segments_member_id ON public.member_segments USING btree (member_id);

CREATE INDEX ix_member_segments_segment_id ON public.member_segments USING btree (segment_id);

CREATE UNIQUE INDEX ix_members_email ON public.members USING btree (email);

CREATE INDEX ix_products_is_active ON public.products USING btree (is_active);

CREATE INDEX ix_purchases_member_id_created_at ON public.purchases USING btree (member_id, created_at DESC);

CREATE INDEX ix_purchases_product_id ON public.purchases USING btree (product_id);

CREATE UNIQUE INDEX member_attributes_key_key ON public.member_attributes USING btree (key);

CREATE UNIQUE INDEX member_attributes_pkey ON public.member_attributes USING btree (id);

CREATE UNIQUE INDEX member_login_codes_pkey ON public.member_login_codes USING btree (id);

CREATE UNIQUE INDEX member_segments_pkey ON public.member_segments USING btree (id);

CREATE UNIQUE INDEX members_pkey ON public.members USING btree (id);

CREATE UNIQUE INDEX points_transactions_pkey ON public.points_transactions USING btree (id);

CREATE UNIQUE INDEX products_pkey ON public.products USING btree (id);

CREATE UNIQUE INDEX purchases_pkey ON public.purchases USING btree (id);

CREATE UNIQUE INDEX redemptions_pkey ON public.redemptions USING btree (id);

CREATE UNIQUE INDEX rewards_pkey ON public.rewards USING btree (id);

CREATE UNIQUE INDEX segments_name_key ON public.segments USING btree (name);

CREATE UNIQUE INDEX segments_pkey ON public.segments USING btree (id);

CREATE UNIQUE INDEX tiers_name_key ON public.tiers USING btree (name);

CREATE UNIQUE INDEX tiers_pkey ON public.tiers USING btree (id);

CREATE UNIQUE INDEX uq_challenge_member ON public.challenge_assignments USING btree (challenge_id, member_id);

CREATE UNIQUE INDEX uq_challenge_segment ON public.challenge_segment_assignments USING btree (challenge_id, segment_id);

CREATE UNIQUE INDEX uq_member_segment ON public.member_segments USING btree (member_id, segment_id);

alter table "public"."challenge_assignments" add constraint "challenge_assignments_pkey" PRIMARY KEY using index "challenge_assignments_pkey";

alter table "public"."challenge_segment_assignments" add constraint "challenge_segment_assignments_pkey" PRIMARY KEY using index "challenge_segment_assignments_pkey";

alter table "public"."challenges" add constraint "challenges_pkey" PRIMARY KEY using index "challenges_pkey";

alter table "public"."email_verification_codes" add constraint "email_verification_codes_pkey" PRIMARY KEY using index "email_verification_codes_pkey";

alter table "public"."member_attributes" add constraint "member_attributes_pkey" PRIMARY KEY using index "member_attributes_pkey";

alter table "public"."member_login_codes" add constraint "member_login_codes_pkey" PRIMARY KEY using index "member_login_codes_pkey";

alter table "public"."member_segments" add constraint "member_segments_pkey" PRIMARY KEY using index "member_segments_pkey";

alter table "public"."members" add constraint "members_pkey" PRIMARY KEY using index "members_pkey";

alter table "public"."points_transactions" add constraint "points_transactions_pkey" PRIMARY KEY using index "points_transactions_pkey";

alter table "public"."products" add constraint "products_pkey" PRIMARY KEY using index "products_pkey";

alter table "public"."purchases" add constraint "purchases_pkey" PRIMARY KEY using index "purchases_pkey";

alter table "public"."redemptions" add constraint "redemptions_pkey" PRIMARY KEY using index "redemptions_pkey";

alter table "public"."rewards" add constraint "rewards_pkey" PRIMARY KEY using index "rewards_pkey";

alter table "public"."segments" add constraint "segments_pkey" PRIMARY KEY using index "segments_pkey";

alter table "public"."tiers" add constraint "tiers_pkey" PRIMARY KEY using index "tiers_pkey";

alter table "public"."challenge_assignments" add constraint "challenge_assignments_challenge_id_fkey" FOREIGN KEY (challenge_id) REFERENCES public.challenges(id) ON DELETE CASCADE not valid;

alter table "public"."challenge_assignments" validate constraint "challenge_assignments_challenge_id_fkey";

alter table "public"."challenge_assignments" add constraint "challenge_assignments_member_id_fkey" FOREIGN KEY (member_id) REFERENCES public.members(id) ON DELETE CASCADE not valid;

alter table "public"."challenge_assignments" validate constraint "challenge_assignments_member_id_fkey";

alter table "public"."challenge_assignments" add constraint "uq_challenge_member" UNIQUE using index "uq_challenge_member";

alter table "public"."challenge_segment_assignments" add constraint "challenge_segment_assignments_challenge_id_fkey" FOREIGN KEY (challenge_id) REFERENCES public.challenges(id) ON DELETE CASCADE not valid;

alter table "public"."challenge_segment_assignments" validate constraint "challenge_segment_assignments_challenge_id_fkey";

alter table "public"."challenge_segment_assignments" add constraint "challenge_segment_assignments_segment_id_fkey" FOREIGN KEY (segment_id) REFERENCES public.segments(id) ON DELETE CASCADE not valid;

alter table "public"."challenge_segment_assignments" validate constraint "challenge_segment_assignments_segment_id_fkey";

alter table "public"."challenge_segment_assignments" add constraint "uq_challenge_segment" UNIQUE using index "uq_challenge_segment";

alter table "public"."challenges" add constraint "challenges_expiry_days_positive" CHECK (((expiry_days IS NULL) OR (expiry_days > 0))) not valid;

alter table "public"."challenges" validate constraint "challenges_expiry_days_positive";

alter table "public"."challenges" add constraint "challenges_reward_id_fkey" FOREIGN KEY (reward_id) REFERENCES public.rewards(id) ON DELETE SET NULL not valid;

alter table "public"."challenges" validate constraint "challenges_reward_id_fkey";

alter table "public"."email_verification_codes" add constraint "email_verification_codes_member_id_fkey" FOREIGN KEY (member_id) REFERENCES public.members(id) ON DELETE CASCADE not valid;

alter table "public"."email_verification_codes" validate constraint "email_verification_codes_member_id_fkey";

alter table "public"."member_attributes" add constraint "member_attributes_key_key" UNIQUE using index "member_attributes_key_key";

alter table "public"."member_login_codes" add constraint "member_login_codes_member_id_fkey" FOREIGN KEY (member_id) REFERENCES public.members(id) ON DELETE CASCADE not valid;

alter table "public"."member_login_codes" validate constraint "member_login_codes_member_id_fkey";

alter table "public"."member_segments" add constraint "member_segments_member_id_fkey" FOREIGN KEY (member_id) REFERENCES public.members(id) ON DELETE CASCADE not valid;

alter table "public"."member_segments" validate constraint "member_segments_member_id_fkey";

alter table "public"."member_segments" add constraint "member_segments_segment_id_fkey" FOREIGN KEY (segment_id) REFERENCES public.segments(id) ON DELETE CASCADE not valid;

alter table "public"."member_segments" validate constraint "member_segments_segment_id_fkey";

alter table "public"."member_segments" add constraint "uq_member_segment" UNIQUE using index "uq_member_segment";

alter table "public"."members" add constraint "members_tier_id_fkey" FOREIGN KEY (tier_id) REFERENCES public.tiers(id) ON DELETE SET NULL not valid;

alter table "public"."members" validate constraint "members_tier_id_fkey";

alter table "public"."points_transactions" add constraint "points_transactions_member_id_fkey" FOREIGN KEY (member_id) REFERENCES public.members(id) ON DELETE CASCADE not valid;

alter table "public"."points_transactions" validate constraint "points_transactions_member_id_fkey";

alter table "public"."products" add constraint "products_price_cents_positive" CHECK ((price_cents > 0)) not valid;

alter table "public"."products" validate constraint "products_price_cents_positive";

alter table "public"."purchases" add constraint "purchases_member_id_fkey" FOREIGN KEY (member_id) REFERENCES public.members(id) ON DELETE CASCADE not valid;

alter table "public"."purchases" validate constraint "purchases_member_id_fkey";

alter table "public"."purchases" add constraint "purchases_product_id_fkey" FOREIGN KEY (product_id) REFERENCES public.products(id) ON DELETE SET NULL not valid;

alter table "public"."purchases" validate constraint "purchases_product_id_fkey";

alter table "public"."purchases" add constraint "purchases_quantity_positive" CHECK ((quantity > 0)) not valid;

alter table "public"."purchases" validate constraint "purchases_quantity_positive";

alter table "public"."redemptions" add constraint "redemptions_member_id_fkey" FOREIGN KEY (member_id) REFERENCES public.members(id) ON DELETE CASCADE not valid;

alter table "public"."redemptions" validate constraint "redemptions_member_id_fkey";

alter table "public"."redemptions" add constraint "redemptions_reward_id_fkey" FOREIGN KEY (reward_id) REFERENCES public.rewards(id) not valid;

alter table "public"."redemptions" validate constraint "redemptions_reward_id_fkey";

alter table "public"."segments" add constraint "segments_name_key" UNIQUE using index "segments_name_key";

alter table "public"."tiers" add constraint "tiers_name_key" UNIQUE using index "tiers_name_key";

grant delete on table "public"."challenge_assignments" to "service_role";

grant insert on table "public"."challenge_assignments" to "service_role";

grant references on table "public"."challenge_assignments" to "service_role";

grant select on table "public"."challenge_assignments" to "service_role";

grant trigger on table "public"."challenge_assignments" to "service_role";

grant truncate on table "public"."challenge_assignments" to "service_role";

grant update on table "public"."challenge_assignments" to "service_role";

grant delete on table "public"."challenge_segment_assignments" to "service_role";

grant insert on table "public"."challenge_segment_assignments" to "service_role";

grant references on table "public"."challenge_segment_assignments" to "service_role";

grant select on table "public"."challenge_segment_assignments" to "service_role";

grant trigger on table "public"."challenge_segment_assignments" to "service_role";

grant truncate on table "public"."challenge_segment_assignments" to "service_role";

grant update on table "public"."challenge_segment_assignments" to "service_role";

grant delete on table "public"."challenges" to "service_role";

grant insert on table "public"."challenges" to "service_role";

grant references on table "public"."challenges" to "service_role";

grant select on table "public"."challenges" to "service_role";

grant trigger on table "public"."challenges" to "service_role";

grant truncate on table "public"."challenges" to "service_role";

grant update on table "public"."challenges" to "service_role";

grant delete on table "public"."email_verification_codes" to "service_role";

grant insert on table "public"."email_verification_codes" to "service_role";

grant references on table "public"."email_verification_codes" to "service_role";

grant select on table "public"."email_verification_codes" to "service_role";

grant trigger on table "public"."email_verification_codes" to "service_role";

grant truncate on table "public"."email_verification_codes" to "service_role";

grant update on table "public"."email_verification_codes" to "service_role";

grant delete on table "public"."member_attributes" to "service_role";

grant insert on table "public"."member_attributes" to "service_role";

grant references on table "public"."member_attributes" to "service_role";

grant select on table "public"."member_attributes" to "service_role";

grant trigger on table "public"."member_attributes" to "service_role";

grant truncate on table "public"."member_attributes" to "service_role";

grant update on table "public"."member_attributes" to "service_role";

grant delete on table "public"."member_login_codes" to "service_role";

grant insert on table "public"."member_login_codes" to "service_role";

grant references on table "public"."member_login_codes" to "service_role";

grant select on table "public"."member_login_codes" to "service_role";

grant trigger on table "public"."member_login_codes" to "service_role";

grant truncate on table "public"."member_login_codes" to "service_role";

grant update on table "public"."member_login_codes" to "service_role";

grant delete on table "public"."member_segments" to "service_role";

grant insert on table "public"."member_segments" to "service_role";

grant references on table "public"."member_segments" to "service_role";

grant select on table "public"."member_segments" to "service_role";

grant trigger on table "public"."member_segments" to "service_role";

grant truncate on table "public"."member_segments" to "service_role";

grant update on table "public"."member_segments" to "service_role";

grant delete on table "public"."members" to "service_role";

grant insert on table "public"."members" to "service_role";

grant references on table "public"."members" to "service_role";

grant select on table "public"."members" to "service_role";

grant trigger on table "public"."members" to "service_role";

grant truncate on table "public"."members" to "service_role";

grant update on table "public"."members" to "service_role";

grant delete on table "public"."points_transactions" to "service_role";

grant insert on table "public"."points_transactions" to "service_role";

grant references on table "public"."points_transactions" to "service_role";

grant select on table "public"."points_transactions" to "service_role";

grant trigger on table "public"."points_transactions" to "service_role";

grant truncate on table "public"."points_transactions" to "service_role";

grant update on table "public"."points_transactions" to "service_role";

grant delete on table "public"."products" to "service_role";

grant insert on table "public"."products" to "service_role";

grant references on table "public"."products" to "service_role";

grant select on table "public"."products" to "service_role";

grant trigger on table "public"."products" to "service_role";

grant truncate on table "public"."products" to "service_role";

grant update on table "public"."products" to "service_role";

grant delete on table "public"."purchases" to "service_role";

grant insert on table "public"."purchases" to "service_role";

grant references on table "public"."purchases" to "service_role";

grant select on table "public"."purchases" to "service_role";

grant trigger on table "public"."purchases" to "service_role";

grant truncate on table "public"."purchases" to "service_role";

grant update on table "public"."purchases" to "service_role";

grant delete on table "public"."redemptions" to "service_role";

grant insert on table "public"."redemptions" to "service_role";

grant references on table "public"."redemptions" to "service_role";

grant select on table "public"."redemptions" to "service_role";

grant trigger on table "public"."redemptions" to "service_role";

grant truncate on table "public"."redemptions" to "service_role";

grant update on table "public"."redemptions" to "service_role";

grant delete on table "public"."rewards" to "service_role";

grant insert on table "public"."rewards" to "service_role";

grant references on table "public"."rewards" to "service_role";

grant select on table "public"."rewards" to "service_role";

grant trigger on table "public"."rewards" to "service_role";

grant truncate on table "public"."rewards" to "service_role";

grant update on table "public"."rewards" to "service_role";

grant delete on table "public"."segments" to "service_role";

grant insert on table "public"."segments" to "service_role";

grant references on table "public"."segments" to "service_role";

grant select on table "public"."segments" to "service_role";

grant trigger on table "public"."segments" to "service_role";

grant truncate on table "public"."segments" to "service_role";

grant update on table "public"."segments" to "service_role";

grant delete on table "public"."tiers" to "service_role";

grant insert on table "public"."tiers" to "service_role";

grant references on table "public"."tiers" to "service_role";

grant select on table "public"."tiers" to "service_role";

grant trigger on table "public"."tiers" to "service_role";

grant truncate on table "public"."tiers" to "service_role";

grant update on table "public"."tiers" to "service_role";


