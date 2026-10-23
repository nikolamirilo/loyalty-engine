# Research: Members area and Dashboard (admin console)

Scope: `/admin/dashboard`, `/admin/members`, `/admin/members/[id]` (with the Points, Rewards, Challenges and Events dialogs), `/admin/members/configure`.
Evidence: `path:line`. Client paths are relative to `client/`, API paths to `api/app/`. `?` marks an open question.

---

## 0. Things every screen shares

### Shell and navigation
- The protected layout redirects to `/admin/login` if there is no admin session (`app/admin/(protected)/layout.tsx:26`). `proxy.ts:31-37` also does this for every `/admin/*` path. The session lasts 7 days (`lib/auth/config.ts:28`).
- `/admin` redirects to `/admin/dashboard` (`app/admin/(protected)/page.tsx:4`).
- The browser tab title is "Loyalty Engine - Admin" (`layout.tsx:14`).
- Sidebar order is **Dashboard, Members, Segments, Rewards, Products, Challenges, Events, Tiers** (`components/layout/AppShell.tsx:37-44`). Dashboard is only active on the exact path. "Members" stays active on `/admin/members/*` (`AppShell.tsx:47-50`).
- Above the nav is the **"Program"** label, a "Manage" link to `/admin/programs`, and a dropdown that shows the current program name or "Choose a program" (`components/layout/ProgramSwitcher.tsx:53-61,80`). Below the nav is "Sign out" (`AppShell.tsx:72-84`).
- The brand link reads "Loyalty Engine" and uses the program's logo if it has one (`AppShell.tsx:56-69`).
- Layout:
  - Desktop sidebar: `fixed w-72` with a `h-16` brand row (`AppShell.tsx:135-144`).
  - Below `lg`: a `h-14` sticky header with a hamburger button that opens a drawer `w-72 max-w-[85%]` (`AppShell.tsx:147-185`).
  - Content area: `lg:pl-72`, `mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8` (`AppShell.tsx:188-189`).
- While a page loads, the content area shows a centered logo loader (`app/admin/(protected)/loading.tsx:13-18`).
- Hovering a nav item pre-loads that page's data (`AppShell.tsx:92-100`, `lib/swr/preload.ts:43-59`).

### Program scoping
- Every list belongs to the program picked in the switcher.
  - The choice is stored in the `admin_program` cookie (`lib/server/program.ts:26`).
  - It is sent to the API as the `X-Program-Id` header, both by the browser proxy (`app/api/le/[...path]/route.ts:54-59`) and by server actions (`lib/api.ts:106-110`).
  - With no header, the API uses the default program (`core/program.py:75-89`). An unknown program returns `404 "Program not found: <x>"` (`core/program.py:69-71`).
- Switching program clears the whole client data cache (`app/admin/(protected)/providers.tsx:15-31`).
- **Surprise: members are global.**
  - Creating a member creates the person plus a membership in *every* program (`services/memberships.py:1-24,81-86`, `services/members.py:43`).
  - Name, email and phone belong to the person, so editing them changes them in every program (`services/members.py:25,76-77`, `models/member.py:65-84`).
  - Points, tier, custom attributes, segments, challenges, purchases and events are per program (`models/member.py:21-33`).
- The member ID in URLs and from "Copy ID" is the **per-program membership ID** (`models/member.py:37`, `schemas/member.py:44-49`). The same person has a different ID in each program. Opening a member URL after switching program shows "Member not found".

### Generic dialog, toast and error behavior
- **Dialog** (`components/ui/Dialog.tsx`):
  - Widths: sm = `max-w-sm`, md = `max-w-lg`, lg = `max-w-2xl` (`:10-14`).
  - The panel hangs from the top by default (`:23,63-66`). Panel classes: `rounded-2xl border bg-surface shadow-xl my-6` (`:77`).
  - Header: `px-5 py-4 border-b`, with the title as `h2 text-base font-semibold` and the description as `text-[0.8125rem] text-muted`. A "Close" X button sits top-right (`:83-98`). The body is `px-5 py-4` (`:99`).
  - Esc or a click on the backdrop (`bg-black/40 backdrop-blur-[2px]`) closes it (`:45-49,68-71`).
- **FormDialog** (`components/ui/FormDialog.tsx`):
  - Fields are stacked with `space-y-4`. An error banner appears above the buttons. At the bottom right are **"Cancel"** (secondary) and the submit button (default label "Save") (`:24,101-110`).
  - On success it shows a success toast with the action's message (fallback "Saved."), then closes (`:90-95`).
  - Fields reset every time it opens (`:14-17`).
- **ConfirmButton** (`components/ui/ConfirmButton.tsx`):
  - A size-sm dialog with title and description only. Buttons are **"Cancel"** and the confirm button, styled red by default (`:23,73,78-92`).
  - Errors appear inline in an `ErrorBanner` (fallback "Something went wrong."). On success it shows a toast (fallback "Done.") (`:49-56`).
- **ActionButton**: no confirmation. Success shows a toast (fallback "Done."). Failure shows an error toast (fallback "Something went wrong.") (`components/ui/ActionButton.tsx:30-39`).
- **Toasts**:
  - They sit bottom-center on mobile and bottom-right from `sm` (`components/ui/Toast.tsx:61`).
  - Each card is `max-w-sm rounded-xl`, with a success, error or info icon and an "Dismiss" X (`Toast.tsx:96-106`).
  - They close on their own after **4.5 s** (`Toast.tsx:42`).
- **Error banner**: red box with a warning icon (`components/ui/ErrorBanner.tsx:5-8`).
- **Error text from the backend**:
  - FastAPI `detail` strings are shown word for word.
  - Pydantic validation lists are shown as their `msg` values joined with ", " (`lib/api.ts:171-189`, `lib/swr/fetcher.ts:22-43`).
  - With no `detail`, the UI shows "Request failed (<status>)." A 401 without detail shows "Unauthorized - check the API_TOKEN configuration." (`lib/api.ts:187-188`).
- **Generic failure** (a non-API exception in a server action): "Something went wrong. Please try again." (`lib/actions.ts:9-16`).
- **Backend catch-alls**:
  - DB unreachable: 503 "Database is temporarily unavailable. Please try again shortly." (`main.py:135-151`).
  - Constraint violation: 409 "The request conflicts with existing data." (`main.py:154-170`).
- **Limits and timeouts**:
  - Server actions try up to 3 times with 150 ms and 300 ms backoff, only on network errors and 502, 503 and 504 (`lib/api.ts:31-36,121-164`). If the API can't be reached: "Cannot reach the API at <url>. Make sure the server is running." (`lib/api.ts:132-135`).
  - Browser reads go through `/api/le/*` with an **8 s deadline**. Past that: 504 "The API took too long to respond. Please try again." If the API is unreachable: 502 "Cannot reach the API at <url>." With no session: 401 "Unauthorized" (`app/api/le/[...path]/route.ts:27,35,82-93`).
  - Client cache: dedupes for 5 s, retries errors 2 times, refetches when the tab regains focus, and keeps old data on screen while reloading (`providers.tsx:32-38`).
- **Formatting**:
  - Numbers use en-US grouping ("1,284") (`lib/format.ts:7-9`).
  - Stat tiles shorten values of 10,000 and up, e.g. "12.9K" (`lib/format.ts:12-18`, `components/ui/StatTile.tsx:67`).
  - Dates look like "Oct 23, 2026, 3:04 PM", in the viewer's local time. The API sends UTC (`lib/format.ts:46-66`).
- **Shared UI pieces**:
  - **StatTile**: Card `p-5`, a label (`text-[0.8125rem] text-muted`), the value (`text-3xl font-semibold`), an optional sub line (`text-xs`), and a `h-10 w-10` colored icon chip on the right (`components/ui/StatTile.tsx:56-82`).
  - **Card**: `rounded-xl border bg-surface shadow-sm`.
  - **CardHeader**: `px-5 py-4 border-b`, with the title as `h2 text-sm font-semibold`, an optional description, and an optional action on the right (`components/ui/Card.tsx:5-44`).
  - **PageHeader**: `h1 text-2xl font-semibold` with a `text-sm text-muted` description. Actions sit on the right from `sm` up (`components/ui/PageHeader.tsx:11-22`).
  - **Table**:
    - The table scrolls sideways when needed.
    - Header text: `text-xs text-muted`, `px-4 py-2.5`.
    - Cells: `px-4 py-3`, with rows split by divider lines (`components/ui/Table.tsx:5-51`).
  - **EmptyState**: centered `py-14`, with a `h-12 w-12` round icon, a `text-sm font-semibold` title and a `text-[0.8125rem]` description (`components/ui/EmptyState.tsx:16-34`).
  - **Avatar**: a `h-9 w-9` round chip with initials (first and last word, or the first 2 letters), colored by name (`components/ui/Avatar.tsx:17-35`, `lib/format.ts:79-84`).
  - **Button sizes**: sm = `h-8 px-3 text-[0.8125rem]`, md = `h-10 px-4`, icon = `h-9 w-9`. Variants: primary, secondary (bordered), ghost, danger (red), success (`components/ui/Button.tsx:9-27`).
- **Data access**: the client never talks to the DB. Reads go through the `/api/le` proxy and writes through server actions that call the API (`lib/swr/fetcher.ts:9-19`, `lib/api.ts:1-7`).

---

## 1. Dashboard — `/admin/dashboard`

**How to reach it:** the sidebar's "Dashboard" item, the brand logo link (`AppShell.tsx:59`), `/admin`, or the redirect after login (`proxy.ts:38-39`).

### Labels
- Page title **"Dashboard"**, description **"Overview of your loyalty program."** (`app/admin/(protected)/dashboard/page.tsx:61`).
- Stat tiles, left to right (`dashboard/page.tsx:63-101`):
  1. **"Members"**: the member count in this program. Users icon, blue accent.
  2. **"Points in circulation"**: the sum of every member's balance in this program. Coins icon, aqua accent.
  3. **"Active rewards"**: the count of active rewards, with the sub line **"<n> total"**. Gift icon, orange accent.
  4. **"Active challenges"**: the count of active challenges, with the sub line **"<n> total"**. Target icon, violet accent.
- Card **"Members"**, description **"Most recent in the program"**, action link **"View all ›"** to `/admin/members` (`dashboard/page.tsx:105-117`).
  - Columns: **Member | Tier | Balance** (`:128-134`).
  - The Member cell shows the avatar, name (bold) and email (`text-xs`). The whole cell links to `/admin/members/<id>` (`:140-154`).
  - The Tier cell shows a primary badge with the tier name, or "-" if the member has none (`:156-162`).
  - The Balance cell shows a bold number followed by a small "pts" (`:163-166`).
  - Shows up to **6** rows, newest first (`:37`, `routers/members.py:91`).
  - Empty state: **"No members yet"** / **"Add your first member from the Members page."** (`:121-125`).
- Card **"Tier distribution"**, description **"Members by current tier"** (`dashboard/page.tsx:177`).
  - One row per tier, **highest rank first**. The API returns tiers by rank ascending and the page reverses them (`:51`, `routers/tiers.py:55`).
  - A **"No tier"** row is added when untiered members exist or no tiers are defined (`:52-54`).
  - Each row shows the name on the left and "<count> (<pct>%)" on the right. The percentage is rounded. Under it is an `h-2` progress bar (`:194-209`).
  - Empty state when the program has 0 members: **"Nothing to show"** / **"Add members and tiers to see the breakdown."** (`:186-192`).

### Behavior
- Stats come from `GET /members/stats`, which returns `count`, `pointsInCirculation`, `byTier` and `untiered` (`routers/members.py:126-132`, `services/members.py:131-170`).
- The tier distribution uses each member's **stored** tier, not a fresh calculation (`services/members.py:136-142`).
- Active counts are worked out in the browser from `/rewards?limit=1000` and `/challenges?limit=1000` (`dashboard/page.tsx:39-40`, `lib/swr/keys.ts:43-48`).
- **Surprise:** because every person belongs to every program, "Members" shows the same number in every program, i.e. the total number of people (`services/memberships.py:1-24`). Only points and tiers differ.
- "Recent" sorts by membership creation time (`routers/members.py:91`). A program created later enrolls everyone at once (`services/memberships.py:89-121`), so their order there is effectively arbitrary (?).
- Loading shows skeleton tiles, 6 skeleton rows, and 4 skeleton bars (`dashboard/page.tsx:64-68,118-119,179-185`).
- **No error state:** if a request fails, its tile or card stays a skeleton forever (`dashboard/page.tsx:64-90,179`).

### Layout
- Top to bottom, `space-y-6`: the PageHeader, then the stat grid `grid gap-4 sm:grid-cols-2 lg:grid-cols-4`, then `grid gap-6 lg:grid-cols-3` (`dashboard/page.tsx:60-103`).
- In that last grid, the Members card is `lg:col-span-2 overflow-hidden` with the table inside. The Tier distribution card takes the third column, with its body in `space-y-4 p-5` (`:105,176-178`).
- Table rows highlight on hover (`hover:bg-surface-2/60`) and the name turns primary on row hover (`:139,147`).

---

## 2. Members list — `/admin/members`

**How to reach it:** the sidebar's "Members", "View all" on the Dashboard, or "All members" on the member and configure pages.

### Labels
- Page title **"Members"** (`app/admin/(protected)/members/page.tsx:44`).
  - Description: **"<n> member(s) in the program."**, singular for 1. Until the count loads it reads **"Loyalty program members."** (`:45-49`).
  - This is the **unfiltered** total. It doesn't change while searching (`:36-39`).
- Header buttons, right side:
  - **"Configure"**, a secondary button-styled link with a sliders icon, to `/admin/members/configure` (`:54-59`).
  - **"+ New member"**, primary (`:20-22`).
- Toolbar, inside the card at the top:
  - Search input with a magnifier icon, placeholder **"Search by name or email…"** (aria-label "Search members"), `w-full max-w-sm` (`components/members/MembersView.tsx:84-92`).
  - When rows are selected, a group appears on the right: **"<n> selected"**, then **"Clear"** (ghost), then **"Delete selected"** (danger, trash icon) (`MembersView.tsx:94-115`).
- Table columns, in order (`components/members/MembersTable.tsx:36-52`):
  1. Checkbox column (`w-10`). The header checkbox is aria-labelled "Select all on this page" or "Clear selection on this page".
  2. **Member**: avatar, name and email, linking to the member.
  3. **Tier**: primary badge or "-".
  4. **Segments**: up to 3 neutral badges, then "+N". Shows "-" if none (`:99-113`).
  5. **Balance**: "1,234 pts".
  6. Chevron link (`w-8`), aria "Open <name>".
- Selected rows are tinted `bg-primary/5` (`MembersTable.tsx:60-63`).
- Pager: **"Page X of Y"** on the left; **"‹ Prev"** and **"Next ›"** (secondary sm) on the right. It is hidden when there is only one page (`components/ui/Pagination.tsx:22-53`).
- Empty states (`MembersView.tsx:119-146`):
  - No results for the search: **"No matching members"** / **"Try a different search term."**
  - No members at all: **"No members yet"** / **"Add your first member to get started."**
  - Load error: **"Couldn't load members"** plus the error message, or "Please try again.".
- Loading shows 10 skeleton rows (`MembersView.tsx:152-168`).

### Search, filter, pagination
- The search waits **300 ms** after typing stops, trims the text, and jumps back to page 1 (`MembersView.tsx:36-43`).
- Search runs on the server and matches name OR email, case-insensitive, anywhere in the text (`routers/members.py:67-76`).
  - Phone is **not** searched.
  - `%` and `_` in the search text act as wildcards because they are not escaped (`routers/members.py:72`) (rough edge).
- **There is no filter** by tier, segment or anything else. Search is the only way to narrow the list.
- Page size is **10** (`MembersView.tsx:18`). Results are fetched with `GET /members?skip=&limit=10&q=` and `GET /members/count?q=` (`MembersView.tsx:45-57`).
  - Sorted newest membership first (`routers/members.py:91`).
  - The API's default limit is 100, with no maximum (`routers/members.py:81-82`).
- If deleting empties the last page, the view moves back to the last page that still exists (`MembersView.tsx:49-51`).
- Hovering or focusing a row pre-loads that member's detail data (`MembersTable.tsx:77-78`, `lib/swr/preload.ts:89-95`).

### Bulk delete
- Selection survives paging and searching (`MembersView.tsx:26-27`). The header checkbox only toggles the rows on the current page (`MembersView.tsx:67-77`).
- Confirm dialog (`MembersView.tsx:100-113`):
  - Title **"Delete <n> member(s)?"**
  - Text **"This permanently deletes them from every program, with all of their points, redemptions, and challenge history."**
  - Confirm button **"Delete <n> member(s)"**.
- Calls `POST /members/bulk-delete {memberIds}` (`lib/actions.ts:174-186`). The API requires at least 1 ID (`schemas/member.py:35-36`).
- Success toast **"<n> member(s) deleted."** (`lib/actions.ts:182`). The selection is then cleared and the list reloads (`MembersView.tsx:110-113`).
- **All or nothing.** If any ID isn't a member of this program, the API returns 404 **"Member(s) not found: <uuid>, …"**, which shows inline in the dialog, and nothing is deleted (`services/members.py:110-128`).
- **Cascade:** deleting removes the person, so their memberships in every program go too, along with points, redemptions, purchases, challenges, segments and events (`services/members.py:97-107`, `models/member.py:41-43,59-63`). Their email can then be registered again (`routers/members.py:216-220`).
- Rough edge: selected members hidden by the current search are deleted too. The dialog only shows a count.

### New member dialog
- Trigger: **"+ New member"**. Title **"New member"**, description **"Add a member to the loyalty program."**, submit **"Create member"**, size md (`members/page.tsx:18-31`).
- Fields, in order (`components/members/MemberFields.tsx`):

| Field | Control | Required | Default / placeholder | Validation |
|---|---|---|---|---|
| **Name** | text | yes (HTML `required`) | placeholder "Ada Lovelace" (`:15-22`) | Client: trimmed; if blank, "Name is required." (`lib/actions.ts:110-112`). API: any string, no length limit (`schemas/member.py:13`) |
| **Email** | `type=email` | yes | "ada@example.com" (`:24-32`) | Client: "Email is required." (`lib/actions.ts:113`). API: `EmailStr`; a bad address gives "value is not a valid email address: <reason>" (`schemas/member.py:14`). Duplicate: **"A member with this email already exists"** (400, `services/members.py:37-38`) |
| **Phone** | `type=tel` | no (hint "optional") | "+1 555 0100" (`:34-41`) | None anywhere; any string is accepted (`schemas/member.py:15`) |
| **Segments** | checkboxes in a bordered box `max-h-40` that scrolls | no (hint "optional") | none checked (`:43-63`) | "Loading segments…" while loading; **"No segments yet — create one on the Segments page first."** if there are none. Unknown ID from the API: "Segment(s) not found: …" (`services/segments.py:40`) |
| custom attributes | one field per definition, hint "optional" | no | **pre-filled with each attribute's default** (`components/members/CustomAttributeFields.tsx:55-61`) | See §4 for coercion rules and messages |

- Success toast **"Member created."**. The dialog closes and the list reloads. The page does **not** open the new member (`lib/actions.ts:127`, `members/page.tsx:28`).
- Automatic behavior on create:
  - A membership is created in every program (`services/members.py:43`).
  - Attribute defaults are filled in, then the typed values override them (`:50-53`).
  - Segments are set. Joining a segment **automatically assigns any active challenges that were bulk-assigned to that segment** (`services/segments.py:47`, `services/challenges.py:102-161`).
  - The tier is calculated, so a member can start in a tier that has no conditions (`services/members.py:56`, `schemas/tier.py:16-19`).
- Rough edges:
  - The duplicate-email message is worded differently on create and on edit (see §3).
  - Email uniqueness is an exact, case-sensitive match (`services/members.py:37`, `models/member_identity.py:30`). Whether `Ada@x.com` and `ada@x.com` can both exist is **?**: pydantic normalizes the domain but likely not the local part.

### Layout
- `space-y-6`: the PageHeader, then one Card `overflow-hidden p-0` (`MembersView.tsx:82`).
- Inside the card: the toolbar row (`flex flex-wrap justify-between gap-3 border-b p-3`), the table, then the pager row (`border-t px-4 py-3`).

---

## 3. Member detail — `/admin/members/[id]`

**How to reach it:** click a row (name or chevron) in the Members list, or a row in the Dashboard's Members card.

### States
- Loading: every section has its own skeleton (`components/members/MemberDetail.tsx:389-433`, `MemberProfileCard.tsx:310-335`).
- **404**: **"Member not found"** / **"This member may have been deleted."** (`MemberDetail.tsx:73-79`). This also happens for a member ID from another program.
- Any other error: **"Couldn't load member"** plus the message (`MemberDetail.tsx:81-87`).
  - A malformed ID gives a pydantic UUID error (422) here, not "Member not found" (`routers/members.py:137`) (rough edge).
- Both error states show the "All members" back link above a Card with an EmptyState (`MemberDetail.tsx:366-387`).
- Sub-widgets have **no error state**: they keep their skeleton if their request fails (`MemberDetail.tsx:129-169,177`).

### Layout, top to bottom (`MemberDetail.tsx:100-362`)
1. **"‹ All members"** back link (`text-sm text-muted`) to `/admin/members` (`:102-108`).
2. **Profile card** (Card `p-6`, see 3a).
3. **Stat tiles**: `grid gap-4 sm:grid-cols-2 lg:grid-cols-5` (`:118-170`):
   1. **"Points balance"**: coins icon, blue.
   2. **"Lifetime earned"**: coins icon, aqua.
   3. **"Challenges completed"**: shows "<completed>/<assigned>". Target icon, violet.
   4. **"Redemptions"**: the count. Gift icon, orange.
   5. **"Total spent"**: a currency amount with the sub line "<n> purchase(s)". Shopping-bag icon, aqua.
4. **"Points activity"** widget, full width. Description **"Earn, burn, and adjustment history"** (`:173-224`).
5. A `grid gap-6 lg:grid-cols-2` holding 4 widgets: **Challenges**, **Redemptions & prizes**, **Purchases**, **Events** (`:227-361`).
- Every widget is a Card that is `lg:h-[26rem]` tall with a body that scrolls (`components/members/MemberWidget.tsx:20-22`).

### 3a. Profile card (view mode)
- Left side (`MemberProfileCard.tsx:126-160`):
  - Avatar `h-14 w-14`.
  - Name as `h1 text-xl font-semibold`, email below it in `text-sm text-muted`.
  - Then badges: the tier (primary, layers icon), or **"No tier"** (neutral), followed by one neutral badge per segment (tag icon).
- Right side, `flex gap-2` (`:176-206`):
  - **"Copy ID"**: **primary** button, sm, copy icon.
  - **"Edit"**: secondary, pencil icon.
  - **"Delete"**: secondary with red text, trash icon.
- Detail tiles in a `<dl>` grid, `grid-cols-2 sm:grid-cols-3 lg:grid-cols-4`. Each tile is `rounded-lg bg-surface-2/60 px-3.5 py-3` with a `text-xs` label (`:244-260`, `components/members/ProfileDetail.tsx:14-21`):
  - **"Phone"**: the value, or "Not set".
  - **"Email"**: a **"Verified"** badge (green) or **"Unverified"** badge (neutral). When verified, the date follows, with the full date and time on hover (`:248-258`, `components/ui/StatusBadge.tsx:70-82`).
  - One tile per custom attribute, in definition order. The value or "Not set"; Yes/No for booleans (`components/members/CustomAttributeList.tsx:15-41`, `lib/custom-attributes.ts:36-44`).
- Bottom row, separated by `border-t` (`:264-278`):
  - The label **"Points:"**.
  - **"↑ Earn"**, **"↓ Burn"**, **"✦ Adjust"** (secondary sm).
  - A vertical divider.
  - **"🎁 Redeem / assign"** (primary sm) (`components/members/PointsActions.tsx:12-111`, `GrantRewardDialog.tsx:38-40`).
- **Copy ID** copies the membership ID. Toast **"Member ID copied."**, or the error toast **"Couldn't copy member ID."** (`MemberProfileCard.tsx:112-119`).

### 3b. Profile card (edit mode)
- Opened with **"Edit"**. The form is edited in place on the card; there is no dialog (`MemberProfileCard.tsx:44-48`).
- Fields:
  - Name and email become two stacked inputs **without visible labels** (`:130-138`).
    - Name: `required`, `text-lg`. Email: `type=email`, `required`.
  - A grid below, `sm:grid-cols-2 lg:grid-cols-4` (`:220-242`):
    - **"Phone"**: plain text input with no placeholder and no `tel` type.
    - **"Email"**: a **"Verified"** checkbox, help text **"Normally set by the verification email."**
    - The custom attribute fields.
    - **"Segments"**: checkboxes, full width, `max-h-32`.
    - The note **"The tier updates on its own from points balance, purchases, segments and custom attributes."**
- Buttons: **"Cancel"** (secondary) and **"Save changes"** (primary submit). In edit mode, Copy ID, Edit and Delete are hidden (`:163-174`).
- The Points/Rewards row is dimmed and can't be clicked while editing (`pointer-events-none opacity-40`, `:264-268`).
- Errors appear in a banner under the header (`:211-215`).
- Validation:
  - Client: "Missing member id.", "Name is required.", "Email is required." (`lib/actions.ts:140-142`).
  - API: **"Email already registered"** (400, `services/members.py:63-72`), "value is not a valid email address: …", "Segment(s) not found: …", and the custom-attribute messages in §4.
- Success: toast **"Member updated."**, the card goes back to view mode, and the data reloads (`MemberProfileCard.tsx:102-107`, `lib/actions.ts:157`).
- Automatic behavior:
  - Name, email and phone change for the person in **every program** (`services/members.py:25,76-77`).
  - Custom attributes are merged into the stored values; a blank field clears that value (`services/members.py:82-88`).
  - The tier is recalculated if segments or attributes were sent. The form always sends both (`services/members.py:91-94`, `lib/actions.ts:150-153`).
  - Joining a segment auto-assigns that segment's challenges (`services/segments.py:47`).
- **Bugs and rough edges:**
  - **The phone can't be cleared.** A blank phone is sent as `null` (`lib/actions.ts:149`). The API drops `None` values before applying (`services/members.py:73-77`), so the old phone stays.
  - **"Verified" re-stamps the date on every save.** The checkbox state is always sent (`lib/actions.ts:153`). `true` sets `email_verified_at = now` again (`services/members.py:78-81`). Editing anything on a verified member moves its verification date to today.
  - **Segments can be wiped by accident.** Saving while segments still show "Loading segments…" sends `segmentIds: []` (`MemberProfileCard.tsx:286`, `lib/actions.ts:37-42,150`). The API then removes every segment (`services/segments.py:41-44`). Custom attributes are guarded against this case, but segments are not (`CustomAttributeFields.tsx:12-17`).
  - The "Configure" page says Segments are "Managed on the Segments page" and Tier is "Derived from points balance". Both are contradicted here (see §4).

### 3c. Delete member (from the profile)
- Confirm dialog (`MemberProfileCard.tsx:192-205`):
  - Title **"Delete <name>?"**
  - Text **"This permanently deletes the member from every program, with all of their points, redemptions, and challenge history."**
  - Confirm button **"Delete member"**.
- Calls `DELETE /members/{id}` (`lib/actions.ts:163-172`). On success: toast **"Member deleted."**, then a redirect to `/admin/members`.
- Same cascade as bulk delete: the identity is deleted everywhere (`routers/members.py:210-223`, `services/members.py:97-107`).

### 3d. Points actions (Earn / Burn / Adjust)
All three are FormDialogs, size md (`components/members/PointsActions.tsx`). The member ID is a hidden field.

| | Earn | Burn | Adjust |
|---|---|---|---|
| Trigger | "↑ Earn" | "↓ Burn" | "✦ Adjust" |
| Title | **"Earn points"** | **"Burn points"** | **"Adjust balance"** |
| Description | "Awards points; the member's tier multiplier is applied automatically." | "Deducts points from the member's balance." | "Manual adjustment, positive or negative, with an optional note." |
| Amount field | **"Points"**, hint "before multiplier"; number, min 1, step 1, placeholder "100", required, autofocus (`:25-36`) | **"Points"**; number, min 1, step 1, placeholder "30", required (`:59-70`) | **"Amount"**, help "Use a negative value to subtract"; number, step 1, placeholder "e.g. -50", required (`:93-103`) |
| Reason field | **"Reason"** (optional), "e.g. Birthday bonus" | **"Reason"** (optional), "e.g. Redeemed via support" | **"Reason"** (optional), "e.g. Goodwill credit" |
| Submit | **"Add points"** | **"Burn points"** | **"Apply adjustment"** |
| Client error | "Enter a positive number of points." (`lib/actions.ts:196-197`) | same (`:216-217`) | "Enter a non-zero adjustment (+ or -)." (`:236-237`) |
| API rule | `points: int > 0` (`schemas/points.py:11-13`) | `points: int > 0`; **"Insufficient points: has X, needs Y"** (400, `routers/points.py:67-68`) | `points: int`, may be negative or 0; **"Adjustment would result in negative balance"** (400, `routers/points.py:83-84`) |
| Toast | **"Points earned."** | **"Points burned."** | **"Balance adjusted."** |
| Ledger type and badge | earn, green "Earn" | **spend**, red **"Spend"** | adjust, blue "Adjust" |

- Endpoints: `POST /members/{id}/points/earn|burn|adjust` (`routers/points.py:43-88`). If the member is missing: "Member not found" (404).
- **The tier multiplier is applied to Earn only.** The amount is multiplied by the member's *current* tier multiplier and rounded with Python's `round()`, which rounds halves to the nearest even number (`routers/points.py:51-52`). The toast doesn't say how many points were actually added; you have to check Points activity.
- **The balance can't go negative**: Burn and Adjust are blocked, as are redemptions (`routers/points.py:67,83`, `routers/redemptions.py:37-38`).
- **The tier is recalculated after every points change**, so a member can move up *or down* a tier (`services/points.py:16-38`, `services/tiers.py:52-61`).
- The Reason is stored as the transaction's `description`, with no length limit (`models/points.py:22`). It shows in the "Description" column.
- Decimals: the browser blocks them because of `step=1`. If that is bypassed, the API returns a pydantic integer error (?).
- Very large values: the column is a 32-bit `Integer` (`models/member.py:44`). Overflow behavior is **?**; probably a 500 error.
- "Burn" in the UI shows up as "Spend" in the history (`components/ui/StatusBadge.tsx:41-43`) (rough edge).

### 3e. Grant reward dialog ("Redeem / assign")
- Trigger: **"Redeem / assign"** (primary sm, gift icon). Dialog title **"Rewards"**, description **"Redeem a reward for points, or assign one as a free prize."**, size lg (`max-w-2xl`) (`components/members/GrantRewardDialog.tsx:38-47`).
- At the top, a checkbox **"Email free prizes to the member, with a link to claim them"**, unchecked by default (`:56-60`).
  - It stays as set across open and close while the page is open (`:26`).
- The list (`ul max-h-[60vh] divide-y`) shows only rewards that are active and in stock (`:32-34`). The rewards are fetched active-only (`MemberDetail.tsx:68`).
  - The API returns rewards in **no set order** (`routers/rewards.py:40-45`).
- Each row:
  - The name (bold, truncated) and **"<cost> pts · <stock> left"**. The stock part only shows for limited stock (`:66-74`).
  - **"Assign free"** (secondary sm).
  - **"Redeem"** (primary sm). It is disabled when the balance is below the cost, with the tooltip **"Insufficient points to redeem"** (`:75-96`).
- Empty state: **"No available rewards"** / **"Create an active, in-stock reward first."** (`:48-53`).
- **Redeem** calls `POST /members/{id}/redeem/{rewardId}` (`lib/actions.ts:252-266`):
  - Uses one unit of stock and creates a **spend** transaction "Redeemed: <reward name>" (`routers/redemptions.py:40-44`).
  - Creates a redemption with source "redeemed" and `pointsSpent` = the cost. Recalculates the tier.
  - Toast **"Reward redeemed."**
- **Assign free** calls `POST /members/{id}/prizes/{rewardId} {sendEmail}` (`lib/actions.ts:268-291`, `routers/redemptions.py:58-85`):
  - Uses one unit of stock and creates a redemption with source "assigned" and 0 points. It starts unclaimed.
  - Toast **"Prize assigned."**, or **"Prize assigned and emailed."** when the email was sent.
  - If the email failed: **"Prize assigned, but the email was not sent. <reason>"**. The prize stays assigned either way (`services/prize_claims.py:134-164`). Reasons:
    - **"Prize emails need CLIENT_BASE_URL set to the public base URL of the client app."** (`services/prize_claims.py:87-89`)
    - **"The email could not be sent. Resend <status>: …"**. In the toast this reads "…email was not sent. The email could not be sent. …", which repeats itself (rough edge).
  - The claim link expires after **30 days** and only the newest link works (`services/prize_claims.py:40,61-70`).
- API errors shown as error toasts:
  - **"Reward is not active"**, **"Reward is out of stock"** (`services/rewards.py:46-51`)
  - **"Insufficient points: has X, needs Y"** (`routers/redemptions.py:38`)
  - "Reward not found", "Member not found"
- The dialog **stays open** after each action. The list and balance reload (`GrantRewardDialog.tsx:28-31`).
- **Neither button asks for confirmation.** A double click can create two prizes (rough edge).
- Whether the email is sent to unverified addresses is **?**. No check was found in `send_prize_email`.

### 3f. Points activity widget
- Title **"Points activity"**, description **"Earn, burn, and adjustment history"**. Columns **Type | Points | Description | When** (`MemberDetail.tsx:173-193`).
  - Type: a badge, Earn / Spend / Adjust.
  - Points: signed, "+100" in green or "-30" in red (`:201-212`).
  - Description: truncated `max-w-xs`, or "-".
- Empty state: **"No activity yet"** / **"Points transactions will appear here."** (`:180-184`).
- Loads the newest **200** transactions (`lib/swr/keys.ts:32-33`).
- **"Lifetime earned"** adds up only `earn` rows among those 200. Positive adjustments are left out, and members with more than 200 transactions are undercounted (`MemberDetail.tsx:90-92`) (rough edge).

### 3g. Challenges widget and the Assign challenge dialog
- Widget title **"Challenges"** with the action **"+ Assign challenge"** (secondary sm) (`MemberDetail.tsx:229-237`, `AssignChallengeDialog.tsx:32-34`). Body `p-4 space-y-3`.
- Empty state: **"No challenges"** / **"Assign a challenge to get this member started."** (`MemberDetail.tsx:243-247`).
- Dialog title **"Assign a challenge"**, description **"Active challenges the member hasn't been assigned yet."**, size lg (`AssignChallengeDialog.tsx:35-41`).
  - Each row: the name, **"Target <n> · <pts> pts"** (the points part only shows if above 0), and the **"Assign"** button (primary sm) (`:50-74`).
  - Empty state: **"Nothing to assign"** / **"This member already has every active challenge, or none are active."** (`:42-47`).
  - Success toast **"Challenge assigned."**. The dialog stays open and the row disappears after the reload.
  - Expired challenges are **not** filtered out. The API rejects them with **"Challenge has expired"** (`services/challenges.py:94-99`).
  - Other API errors: "Challenge is not active", **"Challenge already assigned to this member"** (`routers/challenges.py:149,159`).
- Each challenge is a bordered box, `rounded-lg border p-4` (`components/members/MemberChallengeItem.tsx:40-136`):
  - Name, and **"<pts> pts on completion"** when the challenge gives points.
  - A status badge in the top right: **Assigned / In progress / Completed / Expired / Cancelled** (`StatusBadge.tsx:16-25`).
  - **"Progress"** with "<current> / <target>", and a bar that is green when completed, amber when expired and primary otherwise.
  - **"Expires <date>"** while the challenge is open.
  - Buttons:
    - **"+ Progress"**: only when the status is assigned or in progress.
    - **"✓ Complete"**: whenever the status is not completed or cancelled, so expired ones too.
    - A red trash icon button (aria "Remove challenge"), pushed to the right.
- **Add progress** dialog (`MemberChallengeItem.tsx:75-104`):
  - Title **"Add progress"**, description **'Record progress toward "<name>".'**
  - **"Amount"**: number, min 1, step 1, **default 1**, required.
  - **"Note"** (optional), placeholder "Optional".
  - Submit **"Add progress"**. Toast **"Progress recorded."**
  - Client error: "Enter a positive amount." API errors: **"Challenge is already completed|cancelled"**, **"Challenge has expired"**, **"Challenge is not assigned to this member"** (`services/challenges.py:90,235-247`).
  - Reaching the target **completes the challenge automatically** and pays its reward (`services/challenges.py:318-327`).
  - **The "Note" is accepted but never stored** (`schemas/challenge.py:86-88`, `services/challenges.py:318-327`) (bug).
- **Complete** forces completion with no confirmation. Toast **"Challenge completed."** (`MemberChallengeItem.tsx:106-116`).
  - It pays out whatever the progress or deadline (`routers/challenges.py:237-250`).
  - Payout: `rewardPoints` as an **earn** transaction "Challenge completed: <name>", **without** the tier multiplier. The linked reward is given as a free prize only if it is still active and in stock (`services/challenges.py:330-374`).
- **Remove** asks to confirm:
  - Title **'Remove "<name>"?'**
  - Text **"This unassigns the challenge from this member."**
  - Confirm button **"Remove"**. Toast **"Challenge removed."** (`MemberChallengeItem.tsx:117-134`).
  - Points already paid out are **kept**. The challenge can be assigned again and starts from 0 (`routers/challenges.py:253-263`).
- The stored status changes to "expired" only when progress is attempted (`services/challenges.py:244-246`). Until then, a challenge past its deadline still shows "Assigned" or "In progress" with a past "Expires" date, and the Progress button is visible (rough edge).

### 3h. Redemptions & prizes widget
- Title **"Redemptions & prizes"**, description **"Rewards redeemed for points or assigned for free"**. Columns **Reward | Source | Claimed | Points spent | When** (`MemberDetail.tsx:263-284`).
  - Source: **"Prize"** (amber) or **"Redeemed"** (neutral).
  - Claimed: "—" for redeemed rewards; the claim date, or an amber **"Not yet"** badge, for prizes.
  - Points spent: the number, or **"Free"**.
- Empty state: **"No redemptions yet"** / **"Redeemed rewards and assigned prizes will appear here."** (`:270-274`).
- Shows up to 200 (`lib/swr/keys.ts:34-35`).

### 3i. Purchases widget (shown on the page, outside the main scope)
- Title **"Purchases"**, description **"Simulated buys, used to track spend and frequency"**. Columns **Product | Qty | Total | When**.
- Empty state: **"No purchases yet"** / **"Products this member buys will appear here."** (`MemberDetail.tsx:319-357`).
- There is no admin action here.

### 3j. Events card
- Title **"Events"**, description **"What this member did, and what the rules gave them"**, action **"⚡ Send event"** (secondary sm) (`components/members/MemberEventsCard.tsx:31-35,110-112`).
- Columns **Event | What happened | When | ›** (`:55-60`). The whole row can be clicked.
  - "What happened" lists one line per effect with a green check, **"Skipped: <summary>"** in muted text, or **"No rules matched"** (`components/events/EventEffects.tsx:9-31`).
- Empty state: **"No events yet"** / **"Events your systems send for this member will appear here."** (`:47-51`).
- Clicking a row opens a dialog titled with the event name and its date and time. It shows the full event as JSON (`pre max-h-[60vh] font-mono text-xs`) (`:88-100`).
- **Send an event** dialog (`MemberEventsCard.tsx:105-167`):
  - Title **"Send an event"**, description **"Record an event for this member, the way your systems would. Its rules run right away."**, submit **"Send event"**.
  - **"Event"** select lists active event types only and defaults to the first one.
  - One field per event attribute, each with the hint "optional".
    - Select and boolean attributes offer **"Not sent"**, then the options (or Yes / No).
    - Number and date attributes use number and date inputs (`components/events/EventAttributeFields.tsx:12-54`).
  - Changing the event type clears the attribute inputs.
  - With no active events, the dialog reads: **"There are no active events yet. Define one first."**, with "Define one" linking to `/admin/events` (`:138-147`).
    - The submit button still shows. Pressing it gives **"Choose an event."** (`lib/events/actions.ts:139`) (rough edge).
  - Success toasts: **"Event recorded. No rules matched."**, or **"Event recorded. <effect summaries joined by '. '> (<n> skipped)."** (`lib/events/actions.ts:154-161`).
  - API errors:
    - "Member not found"
    - **"Unknown event type '<key>'. Define it in the console first."**
    - **"The event type '<key>' is inactive."**
    - **"Unknown attribute(s) for '<key>': …"**
    - Value-coercion errors (`services/events.py:116,186,208,210`).
  - Each send gets a unique `eventId` (`console-<uuid>`), so retries are safe and rules don't run twice (`lib/events/actions.ts:151`, `routers/events.py:24-33`).
  - Rules can move points and change prizes, challenges, segments and member fields. The tier is recalculated once afterwards (`services/events.py:159-167`). After sending, the page reloads member, segment and event data (`MemberEventsCard.tsx:118-123`).
- Shows up to 200 events (`lib/swr/keys.ts:53`).

---

## 4. Member fields (Configure) — `/admin/members/configure`

**How to reach it:** the **"Configure"** button on the Members page header (`members/page.tsx:54-59`). There is no sidebar item; the "Members" item stays highlighted.

### Labels
- The **"‹ All members"** back link (`configure/page.tsx:118-124`).
- Page title **"Member fields"**, description **"Every field on a member. Built-in fields are fixed; custom attributes are yours to add, rename, and remove."** (`:126-129`).
- Card **"Built-in fields"**, description **"Part of the loyalty engine itself - these can't be changed or removed."** (`:131-135`).
  - Columns **Field | Type | Notes**. Each field name carries a neutral **"Built-in"** badge.
  - Rows (`:38-45`):

    | Field | Type | Notes |
    |---|---|---|
    | Name | Text | Required |
    | Email | Text | Required, unique |
    | Phone | Text | - |
    | Tier | Reference | Derived from points balance |
    | Points balance | Number | Managed by points actions |
    | Segments | Multi-reference | Managed on the Segments page |

- Card **"Custom attributes"**, description **"Applied to every member. Always optional - a member can leave any of them empty."** (`:161-166`).
  - Action **"+ New custom attribute"** (primary). It shows in the card header only when at least one attribute exists; otherwise it appears inside the empty state (`:165,178`).
  - Columns **Field | Type | Default | Actions** (`:182-189`):
    - Field: the label (bold) with the internal key under it in `code text-xs`.
    - Type: Text / Number / Yes / No / Date / Dropdown. For dropdowns, the options follow as a comma list (`lib/custom-attributes.ts:9-15`, `:197-204`).
    - Default: the formatted default, or "-".
    - Actions: **"✎ Edit"** (secondary sm) and **"🗑 Delete"** (secondary sm, red text).
  - Empty state: **"No custom attributes yet"** / **"Add a field like Birthday or Favourite store to track it on every member."** (`:174-179`).
  - Loading shows 3 skeleton bars. There is **no error state**, so it stays a skeleton (`:167-172`).
- Attributes are listed oldest first (`routers/member_attributes.py:85-89`).

### New / Edit attribute dialog (`components/members/attributes/AttributeFields.tsx`)
- New: title **"New custom attribute"**, description **"Adds a field to every member. Custom attributes are always optional."**, submit **"Create attribute"** (`configure/page.tsx:60-74`).
- Edit: title **"Edit <label>"**, description **"The name and default value can change; the type and internal key can't."**, submit **"Save changes"** (`configure/page.tsx:81-95`).

| Field | Control | Rules / text |
|---|---|---|
| **Name** | text, required, placeholder "Favourite colour" (`:34-51`) | Help: **"Internal key: <key>"**, plus " (can't be changed)" on edit. The key preview updates as you type (`lib/custom-attributes.ts:25-33`). Client: "Name is required." (`lib/actions.ts:803,832`). API: 1–100 chars (`schemas/member_attribute.py:13,26`); the key is derived as camelCase from ASCII letters and digits, max 63 (`services/custom_attributes.py:27-42`). Error **"Label must contain at least one letter and start with one, so a valid internal key can be derived from it."**; duplicate key **"A custom attribute with the key '<key>' already exists"** (`routers/member_attributes.py:49-55`) |
| **Type** | select: Text (default), Number, Yes / No, Date, Dropdown (`:53-76`) | Disabled on edit, with help **"Type can't be changed after creation."** Client: "Type is required." (`lib/actions.ts:804`) |
| **Options** | shown for Dropdown only; tag input, placeholder "red, green, blue" (`:78-94`) | Help **"Press Enter or comma to add each choice."** Leaving the field also adds what was typed, Backspace on an empty input removes the last tag, and duplicates are ignored (`components/ui/TagsInput.tsx:39-57,83`). API trims and dedupes; with none: **"A dropdown attribute needs at least one option."** (`services/custom_attributes.py:45-54`) |
| **Default value** | hint "optional"; the control depends on type: checkbox "Yes", number (`step=any`), date, select with **"No default"**, or text (`:96-163`) | Help on create: **"Applied to every existing member as soon as you create this attribute."** On edit: **"Applies to members created from now on; existing members keep their values."** |

- Toasts: **"Custom attribute created."** / **"Custom attribute updated."** (`lib/actions.ts:816,843`).
- **Delete** asks to confirm:
  - Title **"Delete <label>?"**
  - Text **"This removes the field and its stored value from every member. It can't be undone."**
  - Confirm button **"Delete attribute"**. Toast **"Custom attribute deleted."** (`configure/page.tsx:96-108`).
- **Value rules**: these apply to the default and to member values, on the API side (`services/custom_attributes.py:57-104`):
  - An empty value is always allowed (null).
  - Boolean: true or false, else **"'<label>' must be true or false."**
  - Number: else **"'<label>' must be a number."**
  - Date: ISO date, else **"'<label>' must be a date in YYYY-MM-DD format."**
  - Dropdown: must be one of the options, else **"'<label>' must be one of: a, b, c."**
  - Text: trimmed, 500 characters or fewer, else **"'<label>' must be 500 characters or fewer."** An empty string becomes null.
  - An unknown key gives **"Unknown custom attribute(s): …"** (`:125`).
  - The browser does **not** limit text length; there is no `maxLength`.
- **Automatic behavior and program scope**:
  - Definitions and keys are **per program** (`models/member_attribute.py:39`).
  - Creating an attribute with a default **writes that default onto every member of this program** (`routers/member_attributes.py:69-73`).
  - Editing the default does **not** backfill (`:116-120`).
  - Deleting **removes the key from every member of this program** (`:134-146`).
  - New members get the defaults (`services/custom_attributes.py:130-136`). In the create form, defaults are pre-filled; in the edit form they are not (`CustomAttributeFields.tsx:55-61`).
- **Bugs and rough edges:**
  - **A Yes / No attribute always gets a default of "No".** An unchecked box is sent as `false`, not null (`lib/actions.ts:780`). The API then writes `false` onto every member (`routers/member_attributes.py:72`), and the table shows Default "No". It is impossible to have "no default" for a Yes / No field.
  - Editing a dropdown's options can silently clear data:
    - Removing an option leaves stored member values that are no longer valid.
    - When such a member is edited later, the select shows "—", and saving **clears** the value (`CustomAttributeFields.tsx:99-112`, `lib/actions.ts:84-85`).
    - If the default's option is removed, the default select falls back to "No default" and saving clears the default.
  - Creating or deleting an attribute does **not** recalculate tiers, even though tier conditions can read custom attributes (`routers/member_attributes.py:43-77,127-148`, `services/tiers.py:12-16`).
  - The key preview is shown even for labels the API will reject, such as ones starting with a digit (`AttributeFields.tsx:37-41`).
  - Non-ASCII letters are dropped from keys, e.g. "Größe" becomes "grE" (`services/custom_attributes.py:22,35`) (?).

---

## 5. Contradictions between frontend and backend (and within the UI)
1. Configure says **Tier is "Derived from points balance"** (`configure/page.tsx:42`). The API derives it from points, purchases, segments and custom attributes (`services/tiers.py:1-16`), which the profile edit note also says (`MemberProfileCard.tsx:238-241`).
2. Configure says **Segments are "Managed on the Segments page"** (`configure/page.tsx:44`). They can also be edited in the New member dialog and the profile edit form (`MemberFields.tsx:43-63`, `MemberProfileCard.tsx:235-237`).
3. The default value is labelled "optional" (`AttributeFields.tsx:97-98`), but a Yes / No attribute is always saved with default `false` (`lib/actions.ts:780`).
4. The duplicate-email message differs: create says "A member with this email already exists" (`services/members.py:38`), edit says "Email already registered" (`:72`).
5. Adjust: the client blocks 0 (`lib/actions.ts:236`), but the API accepts 0 and would log a 0-point "adjust" (`schemas/points.py:21-23`).
6. The UI says "Burn", but the stored type and the history badge say "Spend" (`PointsActions.tsx:49`, `routers/points.py:69`, `StatusBadge.tsx:42`).
7. The Earn description promises the multiplier is applied, but the toast "Points earned." doesn't show the amount added (`lib/actions.ts:204`).
8. The challenge progress "Note" field is sent (`lib/actions.ts:571`), accepted by the schema (`schemas/challenge.py:88`), and never stored.
9. Clearing the phone looks supported because the client sends null, but the API ignores null (`services/members.py:73-75`).
10. The Configure built-in table says "Phone — Text" and shows no notes. The phone is per person and shared across programs, and so are Name and Email. The UI never says this.

## 6. For the product team: bugs and rough edges
- **Phone can't be cleared** once set (§3b).
- **The email verification date resets to "now" on every profile save** while "Verified" is checked (§3b).
- **Segments can be wiped by accident** when saving the profile before they finish loading (§3b).
- **A Yes / No attribute always has default "No"**, which is backfilled onto all members (§4).
- **Removing a dropdown option silently clears values** on the next member edit (§4).
- **The challenge progress note is discarded** (§3g).
- **Tiers are not recalculated** when attributes are created or deleted (§4).
- **No confirmation for Redeem, Assign free, or force Complete.** A double click can grant twice (§3e, §3g).
- **Dashboard, Configure and member sub-widgets have no error state**: a failed request leaves a skeleton forever (§1, §3, §4).
- **"Lifetime earned" is wrong** past 200 transactions and leaves out positive adjustments (§3f).
- **Overdue challenges** still show "Assigned" or "In progress" with a past "Expires" date and a Progress button, until someone tries to add progress (§3g).
- **Expired challenges are offered in Assign challenge** and then rejected (§3g).
- **The Send event dialog** shows the "Send event" button even when there are no events (§3j).
- **The email-failure toast repeats itself**: "…email was not sent. The email could not be sent…" (§3e).
- **The rewards list has no set order** in the Grant dialog (`routers/rewards.py:45`).
- **Search treats `%` and `_` as wildcards**; there is no tier or segment filter (§2).
- **Bulk delete can include members hidden by the current search** (§2).
- **"Copy ID" is the primary (most prominent) button** on the profile, and the ID it copies is per program. Pasting it while another program is selected gives "Member not found" (§0, §3a).
- **The name and email inputs have no visible labels** in profile edit mode (§3b).
- **Malformed member URLs** show a pydantic UUID error instead of "Member not found" (§3).
- **Member list ordering in programs created later** is effectively arbitrary, because every enrollment has the same creation time (§1).
- **Possible security issue (?):** the admin server actions in `lib/actions.ts` don't check the admin session themselves. They rely on `proxy.ts` gating `/admin/*` paths. Next.js server actions can be called by POSTing to any route, including public member-app pages that `proxy.ts` doesn't gate as admin. This needs checking.

## 7. Could not confirm (?)
- Whether emails that differ only in case (`Ada@x.com` and `ada@x.com`) can both be registered. Uniqueness is case-sensitive (`models/member_identity.py:30`), and pydantic normalization of the local part is not confirmed. Also, requirements pin pydantic 2.9.2 (`api/requirements.txt:4`) but 2.13.5 is installed locally.
- What happens when an amount overflows the 32-bit `Integer` points column. It is probably a raw 500.
- Whether prize emails go to members whose email is not verified. No check was seen.
- The exact pydantic message for a non-integer points value. It is only reachable by bypassing the browser's `step=1`.
- How member ordering behaves in programs created after their members. All share one `created_at` (`services/memberships.py:89-121`, `models/member.py:46`).
- Whether an unhandled DB error, such as a value out of range, comes back as JSON or plain text. If plain text, the UI shows the raw text (`lib/api.ts:172`).
