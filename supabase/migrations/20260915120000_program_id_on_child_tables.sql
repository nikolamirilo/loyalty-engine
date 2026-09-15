-- Denormalise program_id onto the tables that only reached a program through
-- a parent row.
--
-- The programs migration put program_id on the seven tables that *own* their
-- rows (members, rewards, products, challenges, tiers, segments,
-- member_attributes). Everything else was scoped transitively - a points
-- transaction belonged to a program only because its member did. That is
-- correct but awkward: every program-aware query on those tables needs a join,
-- and a policy on them needs an EXISTS subquery rather than a flat compare.
--
-- So each of these six gets its own program_id, kept truthful by a trigger
-- rather than by every caller remembering. The trigger reads the parent on
-- INSERT and UPDATE, so the column cannot drift from it and no application
-- code has to change.
--
--   points_transactions           -> members.program_id
--   redemptions                   -> members.program_id
--   purchases                     -> members.program_id
--   member_segments               -> members.program_id
--   challenge_assignments         -> members.program_id
--   challenge_segment_assignments -> challenges.program_id   (no member_id)
--
-- Deliberately excluded: email_verification_codes and member_login_codes.
-- Those hang off member_identities and follow the *person*, not a membership -
-- one login code works in every program, which is the point. Giving them a
-- program_id would contradict that.


-- ── the columns ──────────────────────────────────────────────────────────────

do $$
declare
  t text;
begin
  foreach t in array array[
    'points_transactions', 'redemptions', 'purchases',
    'member_segments', 'challenge_assignments', 'challenge_segment_assignments'
  ]
  loop
    execute format('alter table public.%I add column program_id uuid', t);
  end loop;
end $$;


-- ── backfill from the parent ─────────────────────────────────────────────────

update public.points_transactions t
   set program_id = m.program_id
  from public.members m where m.id = t.member_id;

update public.redemptions t
   set program_id = m.program_id
  from public.members m where m.id = t.member_id;

update public.purchases t
   set program_id = m.program_id
  from public.members m where m.id = t.member_id;

update public.member_segments t
   set program_id = m.program_id
  from public.members m where m.id = t.member_id;

update public.challenge_assignments t
   set program_id = m.program_id
  from public.members m where m.id = t.member_id;

update public.challenge_segment_assignments t
   set program_id = c.program_id
  from public.challenges c where c.id = t.challenge_id;


-- ── constraints and indexes ──────────────────────────────────────────────────

do $$
declare
  t text;
  orphans bigint;
begin
  foreach t in array array[
    'points_transactions', 'redemptions', 'purchases',
    'member_segments', 'challenge_assignments', 'challenge_segment_assignments'
  ]
  loop
    -- A row whose parent vanished would fail `set not null` with a message that
    -- names no table. Fail loudly instead, naming the one to look at.
    execute format('select count(*) from public.%I where program_id is null', t) into orphans;
    if orphans > 0 then
      raise exception 'public.% has % row(s) with no parent to take a program from', t, orphans;
    end if;

    execute format('alter table public.%I alter column program_id set not null', t);
    execute format(
      'alter table public.%I add constraint %I foreign key (program_id) '
      'references public.programs(id) on delete cascade',
      t, t || '_program_id_fkey'
    );
    execute format(
      'create index %I on public.%I using btree (program_id)', 'ix_' || t || '_program_id', t
    );
  end loop;
end $$;


-- ── keep it truthful ─────────────────────────────────────────────────────────

-- Always derived, never supplied: whatever a caller passes is overwritten with
-- the parent's program. That makes the column impossible to set wrongly, and
-- means no existing insert has to be changed to start populating it.

create or replace function public.set_program_id_from_member()
returns trigger
language plpgsql
as $$
begin
  select program_id into new.program_id from public.members where id = new.member_id;
  return new;
end $$;

create or replace function public.set_program_id_from_challenge()
returns trigger
language plpgsql
as $$
begin
  select program_id into new.program_id from public.challenges where id = new.challenge_id;
  return new;
end $$;

do $$
declare
  t text;
begin
  foreach t in array array[
    'points_transactions', 'redemptions', 'purchases',
    'member_segments', 'challenge_assignments'
  ]
  loop
    execute format(
      'create trigger %I before insert or update on public.%I '
      'for each row execute function public.set_program_id_from_member()',
      t || '_program_id', t
    );
  end loop;
end $$;

create trigger challenge_segment_assignments_program_id
  before insert or update on public.challenge_segment_assignments
  for each row execute function public.set_program_id_from_challenge();
