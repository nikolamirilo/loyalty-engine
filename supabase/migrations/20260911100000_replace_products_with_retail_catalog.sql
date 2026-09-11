-- Replace the coffee/tea seed catalogue with a general retail one (beer,
-- snacks, confectionery, soft drinks) - the earlier set skewed entirely
-- coffee-shop, which doesn't exercise category-based personalisation signals
-- as well as a mixed basket does.
--
-- Deleting from "products" is safe for existing purchase history: purchases
-- keep their own snapshot (product_name, unit_price_cents, ...) and
-- purchases.product_id is ON DELETE SET NULL, so no purchase row is lost or
-- corrupted - it just stops pointing at a live catalogue row.

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;


DELETE FROM "public"."products";


-- Titles stay short (no pack size/weight in the name); that detail lives in
-- the description instead - see the member-facing product card, which shows
-- only name + price on the tile and the rest in its detail modal.
INSERT INTO "public"."products"
    ("id", "name", "description", "price_cents", "currency", "category", "is_active")
VALUES
    ('7645e421-7f92-404e-a33d-24b3c76def94',
     'Craft Lager Beer',
     '6 x 330ml cans, 4.7% ABV. A crisp, cold-fermented lager with a light malt sweetness and a clean hop finish. Keep chilled and drink within 6 months of the can date.',
     899, 'EUR', 'beer', true),

    ('61ee7050-8b68-40d1-a70f-eddeb1c71ea0',
     'Potato Chips',
     '150g bag of thick-cut, kettle-cooked potato chips, lightly salted. Cooked in small batches, which gives a denser crunch than standard fried chips.',
     249, 'EUR', 'snacks', true),

    ('c7283334-4a40-4f99-ae52-9a2350f229fc',
     'Oreo Cookies',
     '154g pack, 14 cookies. The classic chocolate sandwich cookie with a vanilla creme filling - twist, lick, dunk, or just eat them whole.',
     199, 'EUR', 'snacks', true),

    ('6d26ca58-ff65-4b6b-b81c-715f2274d9ae',
     'Milk Chocolate Bar',
     '100g bar, 32% cocoa, ten breakable squares. Made with whole milk powder for a creamier melt than a standard dark-leaning blend.',
     179, 'EUR', 'confectionery', true),

    ('77e9ee5a-7f0c-4e71-bcda-968dcf5fd5ab',
     'Cola Soft Drink',
     '6 x 330ml cans of classic cola, carbonated and caffeinated. Best served ice-cold - refrigerate before opening for the fullest fizz.',
     549, 'EUR', 'beverages', true),

    ('7712220a-0010-4a1d-b26b-ad28c6de45a8',
     'Sparkling Mineral Water',
     '6 x 500ml bottles of naturally sourced sparkling mineral water. Unflavoured, zero calories, fine bubble carbonation.',
     429, 'EUR', 'beverages', true),

    ('af6f8737-1df2-4571-b587-471b6a7e284a',
     'Salted Pretzels',
     '200g bag of oven-baked pretzel sticks, lightly salted. Lower fat than a fried snack, with a crunch that holds up in a bowl for hours.',
     229, 'EUR', 'snacks', true),

    ('437d003c-1afe-439e-9aa0-88343b19b645',
     'Butter Popcorn',
     '3-pack of 91g microwave bags, butter flavour. Ready in under 3 minutes; one bag makes about 6 cups popped.',
     289, 'EUR', 'snacks', true),

    ('2672b45a-80bd-4eb7-92d7-dcae5c03c4bd',
     'Energy Drink',
     '4 x 250ml cans, 80mg caffeine each. Carbonated; check the can for this batch''s sugar content, since it varies by run.',
     599, 'EUR', 'beverages', true),

    ('347c770e-b4de-4836-83e2-a338f016cf93',
     'Gummy Bears',
     '200g bag of fruit-flavoured gummy bears in five flavours. Chewy texture, no artificial colours in this recipe.',
     199, 'EUR', 'confectionery', true)
ON CONFLICT ("id") DO NOTHING;
