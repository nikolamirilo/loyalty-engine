-- Products catalogue and member purchases.
--
-- A purchase is not a real transaction: no payment provider is involved and no
-- balance is ever checked, because every member pays by "credit card" with
-- unlimited funds. The point of the table is the signal it accumulates - how
-- many purchases a member made and how much they spent over a given window -
-- which gamification campaigns read back through
-- GET /members/{id}/purchase-stats?days=7 to personalise the experience.

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


CREATE TABLE IF NOT EXISTS "public"."products" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "name" character varying NOT NULL,
    "description" "text",
    -- Minor units (cents). Integer, never floating point: money must not round.
    "price_cents" integer NOT NULL,
    "currency" character varying(3) DEFAULT 'EUR'::character varying NOT NULL,
    -- Coarse grouping ("coffee", "tea", ...). Doubles as a personalisation
    -- signal: category affinity is derivable from a member's purchases.
    "category" character varying,
    "is_active" boolean DEFAULT true NOT NULL,
    "created_at" timestamp without time zone DEFAULT ("now"() AT TIME ZONE 'utc'::"text") NOT NULL,
    CONSTRAINT "products_price_cents_positive" CHECK (("price_cents" > 0))
);


ALTER TABLE "public"."products" OWNER TO "postgres";


-- Plain ALTER TABLE ... ADD CONSTRAINT isn't idempotent (unlike CREATE TABLE
-- IF NOT EXISTS above), so a retried push - e.g. after an earlier attempt got
-- this far and failed on a later statement - would otherwise fail here with
-- "multiple primary keys". Guard every constraint addition in this migration
-- the same way.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM "pg_constraint" WHERE "conname" = 'products_pkey'
    ) THEN
        ALTER TABLE ONLY "public"."products"
            ADD CONSTRAINT "products_pkey" PRIMARY KEY ("id");
    END IF;
END $$;


-- Defensive against a partially-applied earlier attempt: if "products" already
-- existed on the remote before this migration first ran (e.g. an earlier push
-- got past CREATE TABLE but failed on a later statement), its columns may be
-- missing the defaults below. ALTER COLUMN ... SET DEFAULT is naturally
-- idempotent, so this is safe to run whether or not the table is brand new.
ALTER TABLE "public"."products" ALTER COLUMN "currency" SET DEFAULT 'EUR'::character varying;
ALTER TABLE "public"."products" ALTER COLUMN "is_active" SET DEFAULT true;
ALTER TABLE "public"."products" ALTER COLUMN "created_at" SET DEFAULT ("now"() AT TIME ZONE 'utc'::"text");


CREATE INDEX IF NOT EXISTS "ix_products_is_active" ON "public"."products" USING "btree" ("is_active");


CREATE TABLE IF NOT EXISTS "public"."purchases" (
    "id" "uuid" DEFAULT "gen_random_uuid"() NOT NULL,
    "member_id" "uuid" NOT NULL,
    -- Nullable on purpose: an admin deleting a product must not erase the spend
    -- history it produced, so the row keeps the snapshot columns below instead.
    "product_id" "uuid",
    "product_name" character varying NOT NULL,
    "quantity" integer DEFAULT 1 NOT NULL,
    -- Price frozen at purchase time. Reading it back off `products` would let a
    -- later price edit silently rewrite everyone's historical spend.
    "unit_price_cents" integer NOT NULL,
    "total_cents" integer NOT NULL,
    "currency" character varying(3) DEFAULT 'EUR'::character varying NOT NULL,
    "created_at" timestamp without time zone DEFAULT ("now"() AT TIME ZONE 'utc'::"text") NOT NULL,
    CONSTRAINT "purchases_quantity_positive" CHECK (("quantity" > 0))
);


ALTER TABLE "public"."purchases" OWNER TO "postgres";


-- Same defensive re-assertion as "products" above, for the same reason.
ALTER TABLE "public"."purchases" ALTER COLUMN "quantity" SET DEFAULT 1;
ALTER TABLE "public"."purchases" ALTER COLUMN "currency" SET DEFAULT 'EUR'::character varying;
ALTER TABLE "public"."purchases" ALTER COLUMN "created_at" SET DEFAULT ("now"() AT TIME ZONE 'utc'::"text");


DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM "pg_constraint" WHERE "conname" = 'purchases_pkey'
    ) THEN
        ALTER TABLE ONLY "public"."purchases"
            ADD CONSTRAINT "purchases_pkey" PRIMARY KEY ("id");
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM "pg_constraint" WHERE "conname" = 'purchases_member_id_fkey'
    ) THEN
        ALTER TABLE ONLY "public"."purchases"
            ADD CONSTRAINT "purchases_member_id_fkey" FOREIGN KEY ("member_id") REFERENCES "public"."members"("id") ON DELETE CASCADE;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM "pg_constraint" WHERE "conname" = 'purchases_product_id_fkey'
    ) THEN
        ALTER TABLE ONLY "public"."purchases"
            ADD CONSTRAINT "purchases_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."products"("id") ON DELETE SET NULL;
    END IF;
END $$;


-- Every stats query is "this member's purchases, newest first", optionally cut
-- off at a window start - so member_id plus a descending created_at covers both
-- the lifetime aggregate and the period one.
CREATE INDEX IF NOT EXISTS "ix_purchases_member_id_created_at" ON "public"."purchases" USING "btree" ("member_id", "created_at" DESC);


CREATE INDEX IF NOT EXISTS "ix_purchases_product_id" ON "public"."purchases" USING "btree" ("product_id");


ALTER TABLE "public"."products" ENABLE ROW LEVEL SECURITY;


ALTER TABLE "public"."purchases" ENABLE ROW LEVEL SECURITY;


-- No policies are defined, so anon/authenticated reach nothing. The API
-- connects as the table owner over DATABASE_URL and is unaffected, matching
-- every other table in this schema.
GRANT ALL ON TABLE "public"."products" TO "service_role";


GRANT ALL ON TABLE "public"."purchases" TO "service_role";


-- ── Seed catalogue ──────────────────────────────────────────────────────────
-- Fixed ids so re-running this migration is a no-op rather than a duplicate.

INSERT INTO "public"."products"
    ("id", "name", "description", "price_cents", "currency", "category", "is_active")
VALUES
    ('a1f3c7d2-0b91-4e6a-9c3d-1e5f8a2b4c60',
     'Ethiopia Yirgacheffe Whole Beans, 250g',
     'Washed heirloom varietals grown between 1,900 and 2,200 metres in the Gedeo zone. Bright and tea-like, with jasmine on the nose and a clean bergamot-and-lemon finish. Roasted light for filter and rested seven days before it ships.',
     1450, 'EUR', 'coffee', true),

    ('b2e4d8c1-6a72-4f15-8d90-3c7b1e6a9f24',
     'Colombia Huila Decaf Whole Beans, 250g',
     'Decaffeinated by the sugarcane ethyl acetate process, which keeps the sweetness that solvent methods strip out. Red apple, panela and milk chocolate, with a soft syrupy body. Works as espresso or as filter.',
     1290, 'EUR', 'coffee', true),

    ('c3d5e9b0-7f83-4a26-9e01-4d8c2f7b0a35',
     'House Espresso Blend, 1kg',
     'Our everyday bar blend: 70% Brazilian Cerrado pulped natural for body, 30% washed Guatemalan Huehuetenango for acidity. Pulls thick and forgiving at 1:2 in 28 seconds, and holds its own under milk instead of going flat.',
     3900, 'EUR', 'coffee', true),

    ('d4c6f0a9-8094-4b37-af12-5e9d3a8c1b46',
     'Cold Brew Cans, 8-pack',
     'Single-origin Brazilian coffee steeped for 18 hours at 4C and never heated, so it stays low in acidity. Unsweetened and ready to drink straight from the fridge. 250ml cans, nine months unopened shelf life.',
     2400, 'EUR', 'coffee', true),

    ('e5b70192-91a5-4c48-b023-6f0e4b9d2c57',
     'Ceremonial Grade Matcha, 40g',
     'First-harvest tencha from Uji in Kyoto, stone-milled to roughly ten microns. Vivid green, thick and umami-forward with almost no bitterness. Meant for usucha whisked with water at 80C rather than for lattes. Resealable tin.',
     2750, 'EUR', 'tea', true),

    ('f6a812a3-a2b6-4d59-a134-70f15cae3d68',
     'Assam Breakfast Loose Leaf, 200g',
     'Second-flush orthodox Assam from the Brahmaputra valley, with the malty depth and brisk finish that stands up to milk. Whole leaf rather than dust, so it brews strong without turning tannic. Around 80 cups per tin.',
     1150, 'EUR', 'tea', true),

    ('07b923b4-b3c7-4e6a-b245-81a26dbf4e79',
     'Hand-Blown Glass Pour-Over Carafe, 600ml',
     'Borosilicate glass blown in a single piece, so there is no seam to trap grounds and nothing to unscrew and lose. Graduated at 200, 400 and 600ml, heat-safe to 150C and dishwasher safe. Fits any standard 02-size dripper.',
     3450, 'EUR', 'equipment', true),

    ('18ca34c5-c4d8-4f7b-e356-92b37ec05f8a',
     'Conical Burr Coffee Grinder',
     '40mm hardened steel conical burrs with 30 stepped settings, from fine espresso through to coarse French press. The low-speed motor keeps the grounds cool and the static down, and the anti-static catch cup keeps them in the cup.',
     8900, 'EUR', 'equipment', true),

    ('29db45d6-d5e9-4a8c-a467-a3c48fd1608b',
     'Double-Wall Insulated Travel Tumbler, 350ml',
     'Vacuum-sealed 18/8 stainless steel that holds coffee hot for six hours and iced drinks cold for twelve. The lid seals completely for a bag, and the body fits a standard car cup holder. No plastic liner anywhere.',
     2200, 'EUR', 'accessories', true),

    ('3aec56e7-e6fa-4b9d-a578-b4d590e2719c',
     'Reusable Ceramic Pour-Over Filter',
     'A micro-porous ceramic cone that replaces paper filters outright, so there is no paper taste and nothing to throw away. Lets more of the coffee oils through than paper does, which reads as a fuller cup. Rinse after use, boil monthly.',
     1650, 'EUR', 'accessories', true)
ON CONFLICT ("id") DO NOTHING;
