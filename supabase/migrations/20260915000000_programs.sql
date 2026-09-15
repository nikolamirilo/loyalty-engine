-- Programs: isolate each demo dataset from the others.
--
-- A program owns its rewards, products, challenges, tiers, segments and custom
-- attribute definitions. Member identity is the exception: a person exists once
-- in `member_identities` and holds one `members` row per program they joined,
-- which is where their points, tier and progress live.
--
-- Everything that already exists is moved into a single "Default" program, so
-- the API keeps answering exactly as it did for callers that send no
-- X-Program-Id header.


-- ── programs ─────────────────────────────────────────────────────────────────

create table "public"."programs" (
    "id" uuid not null,
    "name" character varying not null,
    "slug" character varying not null,
    "description" text,
    "is_default" boolean not null default false,
    "created_at" timestamp without time zone
);

alter table "public"."programs" enable row level security;

alter table "public"."programs" add constraint "programs_pkey" primary key ("id");

create unique index ix_programs_slug on public.programs using btree (slug);

-- At most one program may be the default, since it is what a request without
-- an X-Program-Id header resolves to.
create unique index uq_programs_single_default on public.programs using btree (is_default)
  where is_default;

insert into public.programs (id, name, slug, description, is_default, created_at)
values (
  gen_random_uuid(),
  'Default',
  'default',
  'Everything that existed before programs were introduced.',
  true,
  now()
);


-- ── member_identities ────────────────────────────────────────────────────────

create table "public"."member_identities" (
    "id" uuid not null,
    "name" character varying not null,
    "email" character varying not null,
    "phone" character varying,
    "email_verified_at" timestamp without time zone,
    "created_at" timestamp without time zone
);

alter table "public"."member_identities" enable row level security;

alter table "public"."member_identities"
  add constraint "member_identities_pkey" primary key ("id");

create unique index ix_member_identities_email on public.member_identities using btree (email);

-- One identity per existing member, reusing the member's id so the mapping is
-- obvious afterwards. Safe as a straight copy because members.email is unique
-- today. `members.created_at` is nullable while this column is not, and naming
-- it in the insert suppresses any default, so it is coalesced.
insert into public.member_identities (id, name, email, phone, email_verified_at, created_at)
select id, name, email, phone, email_verified_at, coalesce(created_at, now())
from public.members;


-- ── members becomes the per-program membership ───────────────────────────────

alter table "public"."members"
  add column "program_id" uuid,
  add column "identity_id" uuid;

update public.members
set program_id = (select id from public.programs where is_default),
    identity_id = id;

alter table "public"."members"
  alter column "program_id" set not null,
  alter column "identity_id" set not null,
  drop column "name",
  drop column "email",
  drop column "phone",
  drop column "email_verified_at";

alter table "public"."members"
  add constraint "members_program_id_fkey" foreign key (program_id)
    references public.programs(id) on delete cascade,
  add constraint "members_identity_id_fkey" foreign key (identity_id)
    references public.member_identities(id) on delete cascade,
  add constraint "uq_program_identity" unique (program_id, identity_id);

create index ix_members_program_id on public.members using btree (program_id);
create index ix_members_identity_id on public.members using btree (identity_id);


-- ── program_id on every owning table ─────────────────────────────────────────

do $$
declare
  t text;
  default_program uuid := (select id from public.programs where is_default);
begin
  foreach t in array array['rewards', 'products', 'challenges', 'tiers', 'segments', 'member_attributes']
  loop
    execute format('alter table public.%I add column program_id uuid', t);
    execute format('update public.%I set program_id = %L', t, default_program);
    execute format('alter table public.%I alter column program_id set not null', t);
    execute format(
      'alter table public.%I add constraint %I foreign key (program_id) '
      'references public.programs(id) on delete cascade',
      t, t || '_program_id_fkey'
    );
    execute format('create index %I on public.%I using btree (program_id)', 'ix_' || t || '_program_id', t);
  end loop;
end $$;


-- ── uniqueness moves from global to per program ──────────────────────────────

-- These were created as unique indexes by the ORM, but an equally named UNIQUE
-- constraint would shadow them, and dropping the wrong one fails the migration.
-- Drop whichever form is actually present.
do $$
declare
  spec record;
begin
  for spec in
    select * from (values
      ('members', 'ix_members_email'),
      ('tiers', 'tiers_name_key'),
      ('segments', 'segments_name_key'),
      ('member_attributes', 'member_attributes_key_key')
    ) as s(table_name, object_name)
  loop
    if exists (
      select 1 from pg_constraint
      where conname = spec.object_name
        and conrelid = format('public.%I', spec.table_name)::regclass
    ) then
      execute format('alter table public.%I drop constraint %I', spec.table_name, spec.object_name);
    elsif exists (
      select 1 from pg_class where relname = spec.object_name and relkind = 'i'
    ) then
      execute format('drop index public.%I', spec.object_name);
    end if;
  end loop;
end $$;

alter table "public"."tiers"
  add constraint "uq_program_tier_name" unique (program_id, name);
alter table "public"."segments"
  add constraint "uq_program_segment_name" unique (program_id, name);
alter table "public"."member_attributes"
  add constraint "uq_program_attribute_key" unique (program_id, key);


-- ── verification and login codes follow the person, not the membership ───────

alter table "public"."email_verification_codes"
  drop constraint "email_verification_codes_member_id_fkey";
alter table "public"."email_verification_codes"
  rename column "member_id" to "identity_id";
alter table "public"."email_verification_codes"
  add constraint "email_verification_codes_identity_id_fkey" foreign key (identity_id)
    references public.member_identities(id) on delete cascade;

alter table "public"."member_login_codes"
  drop constraint "member_login_codes_member_id_fkey";
alter table "public"."member_login_codes"
  rename column "member_id" to "identity_id";
alter table "public"."member_login_codes"
  add constraint "member_login_codes_identity_id_fkey" foreign key (identity_id)
    references public.member_identities(id) on delete cascade;

-- The ORM salts each code hash with the id it is keyed to. That id is unchanged
-- (an identity reuses its member's id above), so codes outstanding at deploy
-- time still verify.


-- ── grants, matching every other table in this schema ────────────────────────

do $$
declare
  t text;
  p text;
begin
  foreach t in array array['programs', 'member_identities']
  loop
    foreach p in array array['delete', 'insert', 'references', 'select', 'trigger', 'truncate', 'update']
    loop
      execute format('grant %s on table public.%I to service_role', p, t);
    end loop;
  end loop;
end $$;
