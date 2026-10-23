# User docs

End-user documentation for Loyalty Engine: how staff run a program in the admin console, and
what members see in the member app. It is one self-contained HTML page, served by the client app
at **`/docs`** (public, no session needed).

Everything in it was written from the code and checked against it. Screens are HTML drawings that
copy the real components' layout, labels and design tokens, so they stay sharp and never go stale
silently: when a screen changes, redraw it in `make_shots.py`.

## Rebuild

```bash
./docs/build.sh            # draw screens, build, copy to client/public/docs/index.html
./docs/build.sh --check    # also run the browser checks and the label check
```

Needs Python 3. The checks also need Node and Playwright with Chromium.

`build.sh` writes `docs/dist/` (ignored) and `client/public/docs/index.html` (committed: it is what
`/docs` serves, through a rewrite in `client/next.config.ts`).

## What is in here

| Path | What it is |
|---|---|
| `site.py` | Site settings, sidebar order, "Result" lines, related pages, glossary and search synonyms. |
| `10-*.html` to `90-*.html` | The pages, one `<section class="page">` each, grouped by file. |
| `make_shots.py` | Draws every screen and diagram into `shots/`. |
| `01-ui.html` | Product styles for the screens, copied from `client/components/ui` and `client/app/globals.css`. |
| `00-head.html`, `01-screens.html`, `01-zclose.html`, `02-shell.html`, `99-foot.html` | The docs layout. Leave as is. |
| `research/` | Facts from the code, with `path:line` evidence, that the pages are written from. `decisions.md` records the scope. |
| `tooling/` | The build, screen helpers and checks. |

## Keeping the docs current

`site.py` records the commit the docs were last checked against (`SOURCE['commit']`). It is not
shown anywhere in the docs.

```bash
python3 docs/changes.py          # commits since then that change app or API code
python3 docs/changes.py --diff   # the same, with the diff
python3 docs/changes.py --mark origin/main   # after updating the docs
```

Only paths in `SOURCE['watch']` count (the client app, the API, migrations), minus
`SOURCE['ignore']` (the docs, the built page, Markdown, tests). A commit that only touches the
docs never asks for an update.

A scheduled Claude Code routine does this for you: it follows
[`UPDATE_ROUTINE.md`](UPDATE_ROUTINE.md), does nothing when there is nothing to document, and
otherwise opens a pull request with the updated docs.

## Updating after a product change

1. Re-read the changed code and update the matching `research/*.md` notes.
2. Update the pages. Quote UI labels and messages exactly as the code has them.
3. Redraw changed screens in `make_shots.py`.
4. Run `./docs/build.sh --check`.

Writing rules: short sentences, second person, present tense, no em or en dashes (the build counts
them), and the product's exact labels.
