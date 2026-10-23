# Programs, admin sign in, admin shell: behaviour research

Source: `/home/user/loyalty-engine`. Paths: `client/...` is the Next.js 16 frontend and `api/app/...` is the FastAPI backend. The research looked only at code. It did not run the app. Every fact has a `path:line` reference. Notes marked **(to verify)** are inferences from framework behaviour, not from this repo's code.

---

## 1. Landing page (`/`)

- File: `client/app/page.tsx`. The tab title is **"Loyalty Engine"** (`client/app/page.tsx:7-9`).
- Layout: a centred column (`max-w-sm`) on the `surface-2` background (`client/app/page.tsx:41-42`). It has the stock logo (`/logo.svg`, 48×48, `shadow-sm`) (`:44-51`), the heading **"Welcome to Loyalty Engine"** (`:53-55`) and the subtitle **"Choose how you'd like to continue"** (`:56`).
- There are two entry tiles (`:59-72`). Each tile is a card link with an icon chip, a label, a one-line description and a chevron (`:11-37`):
  | Label | Description | Goes to | Icon |
  |---|---|---|---|
  | **Continue as admin** | Manage members, rewards, and tiers | `/admin/login` | DashboardIcon |
  | **Continue as user** | Track your points and rewards | `/login` (member app) | HomeIcon |
- `/` is public. The proxy only guards `/admin/**` and the member routes `/home`, `/products`, `/wallet` and `/account` (`client/proxy.ts:10`, `:31-62`).

## 2. Admin sign in (`/admin/login`)

### Screen
- Files: `client/app/admin/login/page.tsx` and `LoginForm.tsx`. The tab title is **"Sign in - Loyalty Engine"** (`page.tsx:10-12`).
- A centred card on `surface-2`. It has the stock logo, the heading **"Loyalty Engine"** and the subtitle **"Sign in to the admin console"** (`page.tsx:19-38`). The form card is `rounded-xl border border-line bg-surface p-6 shadow-sm` (`page.tsx:39`).
- The sign-in page always shows the stock logo and colours. `ProgramTheme` is only rendered in the protected layout (`client/app/admin/(protected)/layout.tsx:37`), so a program's branding never reaches this page.

### Fields (`LoginForm.tsx`)
| Label | Type | Required | Other |
|---|---|---|---|
| **Username** | text | yes (HTML `required`) | `autoComplete="username"`, autofocus (`LoginForm.tsx:16-24`) |
| **Password** | password | yes (HTML `required`) | `autoComplete="current-password"` (`:25-33`) |

- Button: **"Sign in"**, full width. It shows a spinner while pending (`LoginForm.tsx:35`, `components/ui/SubmitButton.tsx:9-12`, `components/ui/Button.tsx:72`).
- Errors appear in a red `ErrorBanner` above the button (`LoginForm.tsx:34`).
- There is one admin account. Its username and password come from the env vars `ADMIN_USERNAME` and `ADMIN_PASSWORD`. If either is missing, the server throws at startup (`client/lib/auth/config.ts:10-22`). There is no sign-up, no password reset and no "remember me" option.

### Outcomes and messages (`client/lib/auth/actions.ts`)
| Situation | Result |
|---|---|
| Correct credentials | Clears the failure count, creates the session, preselects the default program and redirects to **`/admin/dashboard`** (`actions.ts:58-65`) |
| Wrong username or password, before the limit | **"Invalid username or password. N attempts left before a 10-minute lockout."** It says "attempt" (singular) when N = 1 (`actions.ts:72-78`) |
| The failed attempt that hits the limit | **"Too many failed attempts. Try again in 10 minutes."** (`actions.ts:34-39`, `:67-70`) |
| Any attempt while locked, correct password included | **"Too many failed attempts. Try again in N minute(s)."** N is the remaining time rounded up, minimum 1 (`actions.ts:49-52`, `:34-39`) |

- The message does not say which of the two fields was wrong. Both comparisons run in constant time (`actions.ts:23-32`, `:54-56`).

### Lockout
- After **3** failed attempts (`MAX_ATTEMPTS = 3`, `client/lib/auth/config.ts:31`), sign-in is blocked for **10 minutes** (`LOCKOUT_MS`, `config.ts:34`).
- So the sequence is: the 1st failure says "2 attempts left", the 2nd says "1 attempt left", and the 3rd starts the lockout (`client/lib/auth/attempts.ts:56-70`).
- The lockout applies to the client IP. The IP is taken from the first `x-forwarded-for` value, then `x-real-ip`, otherwise "unknown" (`actions.ts:16-21`).
- The counter lives in memory in one server process and resets on restart (`attempts.ts:3-9`; README `client/README.md:106-108`).
- When a lockout expires, the count starts again from zero (`attempts.ts:50-54`, `:58-61`). A successful sign-in clears the count (`attempts.ts:74-76`, `actions.ts:59`).

### Session
- Cookie `admin_session`: httpOnly, `secure` in production, `sameSite=lax`, path `/` (`client/lib/auth/session.ts:7-16`, `config.ts:25`).
- It lasts **7 days** from sign-in (`config.ts:27-28`). The token is `<expiresAtMs>.<hmac>`, signed with `AUTH_SECRET` (`client/lib/auth/token.ts:5-23`). It is not renewed while you use the console, so you are signed out exactly 7 days after signing in. `createSession` is only called from `login` (`actions.ts:60`).
- Gating: the proxy sends anyone without a valid session from `/admin/*` to `/admin/login`. It sends a signed-in admin from `/admin/login` to `/admin/dashboard` (`client/proxy.ts:31-41`). The protected layout and the login page check again (`(protected)/layout.tsx:26`, `login/page.tsx:16`).
- `/admin` itself redirects to `/admin/dashboard` (`client/app/admin/(protected)/page.tsx:3-5`).
- Browser data calls go through `/api/le/*`. Without a valid session they get a 401 JSON response `{"detail":"Unauthorized"}` instead of a redirect (`client/app/api/le/[...path]/route.ts:34-36`).

### Sign out
- The **"Sign out"** button with LogOutIcon sits at the bottom of the sidebar and of the mobile drawer (`client/components/layout/AppShell.tsx:72-84`, `:143`, `:182`).
- It deletes the session cookie and the program-selection cookie, then redirects to `/admin/login` (`client/lib/auth/actions.ts:81-85`). There is no confirmation step.

## 3. Admin navigation shell

File: `client/components/layout/AppShell.tsx`. The protected layout wraps every console page in it (`client/app/admin/(protected)/layout.tsx:38-45`). The tab title for console pages is **"Loyalty Engine - Admin"** (`layout.tsx:13-17`). The Programs page sets no title of its own.

### Desktop sidebar (≥ `lg`, 1024px)
- A fixed left column, `w-72` (18rem), with `bg-surface` and a right border (`AppShell.tsx:135`).
- Top bar, `h-16`: the brand block. It shows the selected program's logo if it has one, otherwise the stock logo, followed by the text **"Loyalty Engine"**. It links to `/admin/dashboard` (`AppShell.tsx:56-69`, `:136-138`). The product name always says "Loyalty Engine", even with a brand logo.
- Below that, the **program switcher** (section 4), then the nav list (`:139-142`).
- **Sidebar items, in order** (`AppShell.tsx:36-45`):
  1. **Dashboard**: `/admin/dashboard`, DashboardIcon. Highlighted only on an exact path match.
  2. **Members**: `/admin/members`, UsersIcon
  3. **Segments**: `/admin/segments`, TagIcon
  4. **Rewards**: `/admin/rewards`, GiftIcon
  5. **Products**: `/admin/products`, ShoppingBagIcon
  6. **Challenges**: `/admin/challenges`, TargetIcon
  7. **Events**: `/admin/events`, BoltIcon
  8. **Tiers**: `/admin/tiers`, LayersIcon
- **Programs is not in the nav list.** You reach it through the **"Manage"** link next to the switcher label (section 4).
- Highlighting: the current item is `bg-primary-subtle text-primary-subtle-fg` with `aria-current="page"`. Other items are `text-muted` and turn `bg-surface-2 text-foreground` on hover (`AppShell.tsx:101-107`). An item also counts as current on its sub-pages (`/admin/members/...`) (`:47-50`).
- Hovering or focusing an item preloads that page's data (`AppShell.tsx:92`, `:99-100`).
- Bottom: **Sign out**, above a top border (`:74`, `:143`).

### Mobile (< `lg`)
- Sticky header, `h-14`, `bg-surface/85` with backdrop blur (`AppShell.tsx:147`). It has a hamburger button (aria-label "Open navigation", MenuIcon) and then the brand block (`:148-156`).
- The drawer slides in from the left: `w-72`, `max-w-[85%]`, `shadow-xl`, over a `bg-black/40` backdrop (`:160-166`). Its header has the brand block and an X close button (aria-label "Close navigation") (`:167-177`). Below come the switcher, the nav list and Sign out (`:178-182`).
- The drawer closes when you tap the backdrop, the X, or any nav link (`:164`, `:171`, `:180`). It has no Escape-key handler, unlike Dialog and DropdownMenu.

### Content area
- `lg:pl-72`. The inner wrapper is `mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8` (`AppShell.tsx:188-189`).
- While a page loads, the content area shows the animated logo loader and the sidebar stays in place (`client/app/admin/(protected)/loading.tsx:13-18`). The loader uses the program's logo if it has one, otherwise an animated stock mark (`client/components/ui/LogoLoader.tsx:15-31`).

## 4. Program switcher

File: `client/components/layout/ProgramSwitcher.tsx`.

- **Where**: at the top of the sidebar nav, above Dashboard, and in the same place in the mobile drawer (`AppShell.tsx:140`, `:179`).
  - The label row reads **"PROGRAM"** (uppercase, `text-faint`) with a **"Manage"** link to `/admin/programs` on the right (`ProgramSwitcher.tsx:52-62`).
  - The trigger is a full-width bordered button. It shows the program mark (logo, or coloured initials), the program name (or **"Choose a program"** if none matches) and a chevron. A spinner replaces the chevron while a switch is in progress (`:71-87`).
- **Menu**: lists every program in creation order (`api/app/routers/programs.py:83-85`), each with its mark and name. The current one has a `primary-subtle` background, a bold name and a check icon (`ProgramSwitcher.tsx:90-121`). Choosing the current program does nothing (`:39`). The menu closes on a click outside or on Escape (`client/components/ui/DropdownMenu.tsx:37-51`).
- **Hidden** when there are no programs, or when the API could not be reached (the program list is then empty) (`ProgramSwitcher.tsx:32`, `client/lib/server/branding.ts:30-32`).
- **How the selection is remembered**: in an httpOnly cookie **`admin_program`** that holds the program's **slug** (`client/lib/server/program.ts:26`, `client/lib/programs/actions.ts:32-48`).
  - The cookie is not signed (`client/lib/server/program.ts:21-23`).
  - It has no `expires`/`maxAge` (`actions.ts:34-39`), so it is a browser-session cookie (see the product-team notes).
  - Signing in sets it to the default program, or to the first program if none is the default (`actions.ts:61-69`, `client/lib/auth/actions.ts:63`).
  - Signing out deletes it (`client/lib/auth/actions.ts:83`, `actions.ts:71-74`).
- **What changes when you switch**:
  - Every server request sends the slug as `X-Program-Id` (`client/lib/api.ts:106-110`). Browser calls go through the proxy, which reads the cookie, so the browser cannot choose a different program (`client/app/api/le/[...path]/route.ts:49-59`).
  - The whole `/admin` layout is revalidated (`client/lib/programs/actions.ts:28-30`, `:47`).
  - The client data cache is thrown away, so no rows from the previous program flash on screen (`client/app/admin/(protected)/providers.tsx:15-19`, `:30`).
  - The console takes on the program's **colours** (ProgramTheme) and **logo**: in the brand block, the switcher and the loader (`client/app/admin/(protected)/layout.tsx:34-44`, `client/components/branding/ProgramTheme.tsx:13-22`).
  - You stay on the page you were on.
- **Data isolation**: each program has its own rewards, products, challenges, tiers, segments, custom-attribute definitions and member balances. No query spans two programs (`api/app/models/program.py:12-22`).
  - Lookups by id are filtered by program. A row from another program returns **404**, not 403 (`api/app/services/scoping.py:21-36`).
  - A person exists once, but has a separate membership (points, tier) in every program (`api/app/services/memberships.py:1-23`).
  - An unknown `X-Program-Id` returns 404 **"Program not found: <value>"** (`api/app/core/program.py:68-71`).
  - With no header, the API falls back to the default program and logs a warning (`api/app/core/program.py:75-89`). If no default exists, the message is **"No X-Program-Id header was sent and no default program is configured."** (`:77-80`).
- If the selected program has been deleted, the console falls back to the default program, then to the first program (`client/lib/server/branding.ts:16-24`).

## 5. Programs page (`/admin/programs`)

File: `client/app/admin/(protected)/programs/page.tsx`. To reach it, click **"Manage"** next to the sidebar's "Program" label (`ProgramSwitcher.tsx:56-61`) or go to the URL directly. It is not a sidebar item.

### Layout
- Page header (`programs/page.tsx:28-32`):
  - Title: **"Programs"**.
  - Description: **"Each program has its own rewards, products, challenges, tiers and member points. Switching programs in the sidebar changes everything the console shows."**
  - Action: **"+ New program"** (primary button, PlusIcon) (`client/components/programs/ProgramActions.tsx:42-45`).
- Empty state: a card reading **"No programs yet. Create one to start adding rewards, challenges and tiers."** (`programs/page.tsx:34-37`).
- Otherwise there is one card per program, in creation order (`programs/page.tsx:39-90`). Each card shows:
  - the program mark: a round logo on white, or coloured initials (`page.tsx:46`, `client/components/branding/ProgramMark.tsx:12-22`);
  - the **name** in bold;
  - a **"Default"** pill (`bg-primary-subtle text-primary-subtle-fg`) on the default program (`page.tsx:52-56`);
  - **"Currently viewing"** in muted text on the selected program (`:57-61`);
  - the description on one truncated line, if set (`:63-67`).
- The slug and the id are **not shown** on the page.

### Row actions, left to right (`programs/page.tsx:69-85`)
| Action | Shown when | Result |
|---|---|---|
| **Switch to** (secondary, sm) | the program is not the one being viewed | Same as the sidebar switcher. Sets the cookie and refreshes the console. You stay on Programs, and the row now says "Currently viewing" (`page.tsx:70-77`) |
| Copy icon (title "Copy program ID") | always | Copies the program **UUID** to the clipboard. Toast **"Program ID copied."**, or on failure **"Couldn't copy program ID."** (`ProgramActions.tsx:61-84`) |
| Pencil icon ("Edit <name>") | always | Opens the Edit dialog |
| Trash icon ("Delete <name>") | the program is **not** the default | Opens the delete confirmation (`page.tsx:80-85`) |

### Create: "New program" dialog (`ProgramActions.tsx:39-55`)
- Title: **"New program"**.
- Description: **"A program has its own rewards, products, challenges, tiers and segments. Existing members join it automatically, starting at 0 points."**
- Buttons: **Cancel** and **Create program** (`client/components/ui/FormDialog.tsx:104-109`).

### Edit dialog (`ProgramActions.tsx:86-117`)
- Title: **"Edit <name>"**. No description. Buttons: **Cancel** and **Save changes**.
- It has the same fields as Create, plus a checkbox at the end (described below).

### Fields (shared, `ProgramActions.tsx:16-37`, `BrandingFields.tsx`)
| Label | Name / type | Required | Default | Limits and validation |
|---|---|---|---|---|
| **Name** | `name`, text | yes (HTML `required`; the server action says **"Enter a name."** if it is blank after trimming, `client/lib/programs/actions.ts:132`, `:175`) | blank on create, current name on edit | API: `min_length=1` (`api/app/schemas/program.py:34`, `:44`). No maximum length in the schema or the column (`api/app/models/program.py:27`) |
| **Description** | `description`, single-line text (not a textarea) | no | blank or current | Blank is saved as `null` (`actions.ts:143`, `:186`). No length limit (Text column, `models/program.py:32`) |
| *(info line)* | | | | **"Branding is optional. The console and the member app use this program's logo and colours when it is selected."** (`BrandingFields.tsx:26-29`) |
| **Logo** | `logo`, hidden file input that a button opens | no | stock logo preview at 40% opacity | Help text: **"PNG, JPG, WebP or SVG, up to 2 MB."** (`BrandingFields.tsx:78`). Accept filter: `image/png,image/jpeg,image/webp,image/svg+xml` (`:11`, `:110`). Details below |
| **Primary colour** | `primaryColor`, colour swatch plus hex text box (`font-mono`, `maxLength=7`, placeholder **"Default"**) | no | blank = stock `#5b4bd6` (`client/lib/theme.ts:22`) | Help: **"Buttons, links and highlights. Pick one that reads on white."** (`BrandingFields.tsx:32-38`). Details below |
| **Secondary colour** | `secondaryColor`, same control | no | blank = stock `#eb6834` (`BrandingFields.tsx:12`) | Help: **"Accent on the member tier card."** (`:39-45`) |
| **Use as the default program** | `isDefault` checkbox, **Edit only** | no | checked if already default | Disabled (cannot be unchecked) on the default program (`ProgramActions.tsx:104-114`) |

**Logo control**
- A 56px preview square on white (`BrandingFields.tsx:82-88`).
- The button says **"Upload logo"** when no logo is set and **"Replace"** when one is (`:90-97`). **"Remove"** (ghost) appears when there is a preview (`:98-102`).
- A file you pick is previewed straight away. Remove clears the pick, or marks the existing logo for deletion (`removeLogo=on`) (`:65-75`, `:115`).
- Size check in the frontend: over 2 MB gives **"The logo must be 2 MB or smaller."** (`client/lib/programs/actions.ts:78`, `:105`).
- The Server Action body limit is raised to 3 MB to allow this (`client/next.config.ts:16-22`).
- Backend (`PUT /programs/{id}/logo`): the file type is read from the file's bytes, not from the declared type (`api/app/services/program_branding.py:25-43`). Messages:
  - empty file: **"The logo file is empty."** (400)
  - over 2 MB: **"The logo must be 2 MB or smaller."** (413)
  - not PNG/JPEG/WebP/SVG: **"The logo must be a PNG, JPEG, WebP or SVG image."** (400)
- Storage: a public Supabase Storage bucket, with a new file path for every upload. The previous file is deleted after the program points at the new one (`api/app/routers/programs.py:119-146`, `program_branding.py:46-52`).
- If storage is not configured, upload fails with 503 **"Logo uploads are not configured. Set SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY on the API."** (`api/app/integrations/storage.py:99-114`). Other storage failures:
  - **"Could not reach file storage. Please try again."** (502)
  - **"File storage rejected the upload."** (502) (`storage.py:50-64`)
- Removing the logo works even without storage configured. The file is then left in the bucket (`routers/programs.py:149-163`, `storage.py:86-96`).

**Colour controls**
- The text box holds the value. The swatch is a picker for it, and shows the stock colour while the box is blank (`BrandingFields.tsx:133-161`).
- **"Reset"** (ghost) clears the value back to stock (`:162-166`).
- Accepted input: `#rrggbb` or `rrggbb`, any case. It is stored in lower case (`client/lib/programs/actions.ts:88-94`, `api/app/schemas/program.py:27-30`).
- Messages:
  - **"Enter the primary colour as a hex code, like #0050aa."**
  - **"Enter the secondary colour as a hex code, like #fff000."** (`actions.ts:100-101`)
- API pattern: `^#[0-9a-fA-F]{6}$`, so no shorthand, colour names or alpha (`schemas/program.py:15-18`). The frontend also checks with `HEX_COLOR = /^#[0-9a-f]{6}$/i` (`client/lib/theme.ts:19`).

### How the theme is derived from the colours (`client/lib/theme.ts`)
- **Light scheme** (`theme.ts:75-87`):
  - `--primary` is the brand colour exactly as entered.
  - `--primary-hover` is the brand colour mixed 85% with 15% black.
  - `--primary-fg` is white or ink `#0f172a`, whichever has more contrast on the brand colour.
  - `--primary-subtle` is 12% brand on white.
  - `--primary-subtle-fg` is the brand colour moved toward black in 5% steps until it reaches 4.5:1 contrast on the subtle colour.
  - `--ring` is the brand colour.
- **Dark scheme** (`theme.ts:88-99`):
  - `--primary` is the brand colour lightened toward white until it reaches 4.5:1 on the dark surface `#131a2c`.
  - `--primary-hover` is that colour with 15% white.
  - `--primary-subtle` is 25% brand on the dark surface.
  - `--primary-subtle-fg` is lightened until it reaches 4.5:1.
- **Secondary**: only overrides `--secondary`. It is used on the member app's tier card (`theme.ts:132-135`, `client/app/globals.css:27-29`).
- The overrides are written as `html:root{...}` plus a `prefers-color-scheme: dark` block, and override the root tokens. This means dialogs and toasts (which render in portals) are themed too (`theme.ts:108-139`, `client/components/branding/ProgramTheme.tsx:4-11`).
- Without any colours, no style tag is output (`ProgramTheme.tsx:18-19`).

### Slug
- Neither dialog asks for a slug. On create, the API derives it from the name (`client/components/programs/ProgramActions.tsx:13-15`, `api/app/routers/programs.py:63-69`). The rule (`api/app/services/programs.py:20-43`):
  - Accents are converted to ASCII, the text is lowercased, and each run of other characters becomes `-`. Leading and trailing hyphens are trimmed.
  - Maximum 64 characters.
  - If nothing is left, the slug is `program`.
  - A taken slug gets `-2`, `-3`, and so on. Example: "Café Club Rewards!" becomes `cafe-club-rewards`.
- The slug never changes after creation, including when the program is renamed (`programs.py:1-6`, `client/lib/programs/actions.ts:180-181`). API callers may set their own slug matching `^[a-z0-9]+(-[a-z0-9]+)*$`, maximum 64 characters (`api/app/schemas/program.py:13`, `:35`). A duplicate gives **"A program with the slug '<slug>' already exists"** (`routers/programs.py:66-67`, `:96-98`).
- The slug is what the console stores in the selection cookie, and the API accepts it in `X-Program-Id` in place of the UUID (`api/app/core/program.py:34-40`).

### Outcomes and messages
| Action | Success toast | Notes |
|---|---|---|
| Create | **"Program created."** (`actions.ts:163`) | The API enrols **every existing person** into the new program at 0 points, on the lowest matching tier (`api/app/routers/programs.py:75-77`, `api/app/services/memberships.py:89-121`). Creating a program does **not** switch to it |
| Create, but the logo upload fails | **"Program created, but the logo was not saved: <reason> Add it with Edit."** (`actions.ts:153-161`) | Shown as a *success* toast. The dialog closes |
| Edit | **"Program updated."** (`actions.ts:196`) | A blank colour resets to stock (sends `null`). A blank description clears it (`routers/programs.py:24-26`, `:110-113`) |
| Delete | **"Program deleted."** (`actions.ts:221`) | See below |
| Unexpected error | **"Something went wrong. Please try again."** (`actions.ts:21-25`) | API errors show the API's `detail` text (`client/lib/api.ts:170-189`) |

- Errors appear in a red banner inside the dialog, and the dialog stays open (`client/components/ui/FormDialog.tsx:103`, `ConfirmButton.tsx:76`).
- The API being unreachable gives **"Cannot reach the API at <url>. Make sure the server is running."** (`client/lib/api.ts:132-135`).

### Default program
- Only one program can be the default. Making one the default removes the flag from the previous one in the same save (`api/app/routers/programs.py:48-58`, `:99-100`). A partial unique index enforces this (`api/app/models/program.py:33-35`).
- What it does:
  - API requests without `X-Program-Id` use it (`api/app/core/program.py:75-89`).
  - Admin sign-in preselects it (`client/lib/programs/actions.ts:61-69`).
  - Member sign-in always lands in it (`api/app/core/program.py:13-17`).
- You cannot unset the default directly. The checkbox is disabled (`ProgramActions.tsx:100-114`). The API would answer **"Cannot unset the default program. Make another program the default instead."** (`routers/programs.py:101-109`). To change it, edit another program and tick **"Use as the default program"**.
- You cannot delete the default program either. There is no trash icon (`programs/page.tsx:80-85`), and the API refuses with **"Cannot delete the default program. Make another program the default first."** (`routers/programs.py:179-183`).

### Delete
- Confirmation dialog (`ProgramActions.tsx:119-133`, `client/components/ui/ConfirmButton.tsx:68-95`):
  - Title: **"Delete <name>?"**
  - Text: **"Everything inside it goes too: members, points, rewards, products, challenges, tiers and segments. People keep their accounts and any memberships in other programs."**
  - Buttons: **Cancel** and a red **Delete program**.
- Effect: the API deletes the program, and the database cascades the delete to every table that belongs to it. Member identities (email, name, verification) survive. The stored logo file is deleted when storage is configured (`api/app/routers/programs.py:166-188`).
- If you deleted the program you were viewing, the console switches to the default program (`client/lib/programs/actions.ts:208-218`).
- There is no undo and no typed confirmation.

## 6. 404 and error pages

- **404** (`client/app/not-found.tsx`): there is one, at the root. It renders **without the admin shell**, as a centred card (`min-h-[60vh]`) showing **"404"** (text-5xl), **"We couldn't find the page you're looking for."** and a primary **"Go home"** button that links to `/` (`not-found.tsx:6-23`). No other `not-found.tsx` exists, including under `/admin`.
- **Error** (`client/app/error.tsx`): there is one, at the root. It shows a card with a red alert-triangle chip, the heading **"Something went wrong"**, the error's own message (or **"An unexpected error occurred."**) and two buttons: **"Reload"** (secondary, full page reload) and **"Try again"** (primary, `reset()`) (`error.tsx:15-33`).
  - Because the only error boundary is at the root, an error on a console page probably replaces the sidebar as well. **(to verify, Next.js convention)**
  - The Programs page lets a `getPrograms()` failure throw (`programs/page.tsx:21-24`), unlike the layout, which catches it (`client/lib/server/branding.ts:30-32`).
- Loading: the root shows the full-screen `LogoLoader` (`client/app/loading.tsx:3-8`). The console shows it in the content area only (see section 3).

---

## For the product team: bugs and rough edges

1. **The program selection is forgotten when the browser closes, but the session lasts 7 days.**
   - `admin_program` has no `expires`/`maxAge` (`client/lib/programs/actions.ts:34-39`), while `admin_session` lasts 7 days (`client/lib/auth/session.ts:10-16`).
   - After a browser restart, the console shows the default program (`client/lib/server/branding.ts:16-24`).
   - Server calls then send no `X-Program-Id`, so the API logs a fallback warning on each one (`client/lib/api.ts:106-110`, `api/app/core/program.py:81-87`). This is exactly what `selectDefaultProgram` is meant to prevent (`client/lib/programs/actions.ts:50-60`).
2. **The lockout is held in memory per process** (`client/lib/auth/attempts.ts:3-9`). On a multi-instance or serverless deployment (`client/vercel.json` exists), attempts can be spread across instances. The lockout is then unreliable, and a cold start resets it.
3. **While locked out, the correct password is refused too.** The lock is checked before the credentials (`client/lib/auth/actions.ts:49-52`). Everyone behind the same NAT or proxy IP shares one counter.
4. **Programs is hard to find.** It is not in the sidebar list. The only way in is the small "Manage" link next to the "PROGRAM" label (`client/components/layout/ProgramSwitcher.tsx:56-61`).
5. **The slug is never shown**, but the code comment says "the slug next to the name is the readable handle" (`client/components/programs/ProgramActions.tsx:57-60`). The page shows neither the slug nor the id (`programs/page.tsx:47-68`). Integrators need the slug for `X-Program-Id` and MCP.
6. **A partly failed create is reported as success.** "Program created, but the logo was not saved…" uses a green success toast (`client/lib/programs/actions.ts:153-161`, `client/components/ui/FormDialog.tsx:91-95`).
7. **Edit can save half the changes.** The PATCH runs first and the logo upload second. If the upload fails, an error banner shows, but the name and colour changes are already saved (`actions.ts:179-201`).
8. **A failed upload is retried and can leave orphaned files.** `apiRequest` retries a 502 (`client/lib/api.ts:36`, `:157-162`). The storage errors are 502 `UpstreamError` (`api/app/integrations/storage.py:57-64`), so a logo upload can be attempted 3 times. Each attempt uses a new object path (`api/app/services/program_branding.py:46-52`).
9. **The delete dialog says "members … goes too".** Only the memberships (points, tier) in that program are deleted. Identities survive. The second sentence clarifies this, but "members" first reads as deleting people (`ProgramActions.tsx:128`, `api/app/routers/programs.py:172-177`).
10. **New programs are not switched to automatically.** Create shows "Program created." and the console stays on the previous program (`actions.ts:162-163`).
11. **The Secondary colour has no visible effect in the console.** It only affects the member tier card (`client/components/programs/BrandingFields.tsx:39-45`, `client/app/globals.css:27-29`).
12. **No name length limit** in the frontend or the API (`api/app/schemas/program.py:34`, `api/app/models/program.py:27`). Long names truncate in the switcher, but the Programs card does not truncate the name (`programs/page.tsx:49-51`).
13. **The Programs row may be cramped on phones.** The action group is `shrink-0`, with up to 4 controls ("Switch to" plus 3 icons) beside the name block (`programs/page.tsx:45`, `:69`).
14. **The mobile drawer does not close on Escape**, unlike Dialog and DropdownMenu (`AppShell.tsx:160-185` vs `client/components/ui/Dialog.tsx:45-57`).
15. **The 404 page nests a `<button>` inside a link** (`client/app/not-found.tsx:17-19`). This is invalid HTML; `buttonClass` exists for exactly this case (`client/components/ui/Button.tsx:29-31`). The 404 page also has no console chrome and no path back to the console other than `/`.
16. **The error page shows the raw `error.message`**, which can be technical, such as "Cannot reach the API at http://127.0.0.1:8000…" (`client/app/error.tsx:23-25`, `client/lib/api.ts:132-135`).
17. **A leftover debug route `/admin/test-btn`** shows a raw "N / M" count and a test dialog (`client/app/admin/(protected)/test-btn/page.tsx:11-21`).
18. **Inconsistent product name.** The root layout's title and description say **"Loyalty App"** (`client/app/layout.tsx:19-22`). Everywhere else says "Loyalty Engine".
19. **The program cookie is unsigned.** The code says this is acceptable only while there is no per-program access control (`client/lib/server/program.ts:21-23`).
20. **Possible form reset after an error (to verify).** Under React 19, uncontrolled inputs (Name, Description, the picked logo file) may be reset after a form action returns an error. The colour fields are controlled state and would keep their values (`client/components/ui/FormDialog.tsx:101`, `BrandingFields.tsx:136`).
