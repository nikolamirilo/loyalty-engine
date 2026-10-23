# Docs update routine

Instructions for the scheduled Claude Code routine that keeps the user docs in step with the code.
Its prompt is just: **"Follow docs/UPDATE_ROUTINE.md in nikolamirilo/loyalty-engine."**

The docs record the last commit they were checked against in `docs/site.py` (`SOURCE['commit']`).
`docs/changes.py` lists the commits since then that change watched code (the apps and the API, see
`SOURCE['watch']`). Commits that only change the docs, the built page, Markdown files or tests are
skipped, so a docs-only commit never starts an update, including the routine's own.

## 1. Find out whether there is anything to do

```bash
git fetch origin main && git checkout main && git reset --hard origin/main
python3 docs/changes.py
```

- **Exit 0** ("Docs are up to date"): stop. Change nothing, commit nothing, open no pull request.
- **Exit 2**: setup problem, for example a shallow clone (`git fetch --unshallow`) or rewritten
  history. Fix it if you can; otherwise stop and report the message.
- **Exit 10**: there are commits to document. Note the SHA of `origin/main` now: that is the commit
  you are documenting up to, even if more land while you work.

If a pull request from an earlier run is still open (branch `claude/docs-update-*`), update that
branch instead of opening a second one.

## 2. Work out what changed for users

```bash
python3 docs/changes.py --diff
```

For each commit, decide whether it changes anything a staff member or a member sees or does:
labels, fields, defaults, limits, validation and error messages, what an action does, who can do
it, new or removed screens. Internal changes (refactors, logging, monitoring, config names) need no
page changes. Write down which commits you judged to need nothing, and why.

Read the changed code itself, not only the diff, when the effect is not obvious.

## 3. Update the docs

Work only inside `docs/`. Never change app or API code, even to fix a bug you notice; list bugs in
the pull request instead.

1. Update the matching notes in `docs/research/` with `path:line` evidence.
2. Update the pages (`docs/10-*.html` to `docs/90-*.html`). Quote labels and messages exactly as the
   code has them. Follow the writing rules in `docs/README.md`: short sentences, second person,
   present tense, no em or en dashes.
3. A new screen or feature gets a page or a section, and an entry in `PAGES`, `RESULT` and
   `RELATED` in `docs/site.py`. Removed features come out of the docs.
4. Redraw screens whose layout or labels changed in `docs/make_shots.py`.
5. Update `docs/90-reference.html` (Limits and rules, Troubleshooting, Glossary) for any number,
   message or term that changed.

## 4. Check

```bash
./docs/build.sh --check
```

It must end with "All checks passed." The label check lists quotes it cannot find in the code; each
one must be an example or text built at runtime. Then re-read every sentence you changed against
the code. For anything about deleting data, points, money or permissions, check it twice.

## 5. Record and publish

```bash
python3 docs/changes.py --mark <the origin/main SHA from step 1>
./docs/build.sh
```

Do this even when step 2 found nothing that needs a page change, so the next run does not re-check
the same commits.

Commit only `docs/` and `client/public/docs/index.html` to a branch named
`claude/docs-update-<YYYY-MM-DD>`, push it, and open a pull request to `main`:

- Title: `docs: update for changes up to <short SHA>`
- Body: the commits covered, what changed in the docs for each (or "no user-visible change"), and a
  "For the product team" list of bugs or rough edges you noticed.
