# Admin console research: Segments, Rewards, Products, Challenges, Tiers

Source research for staff-facing end-user docs. All paths are relative to the repo root
(`/home/user/loyalty-engine`). `?` marks something I could not confirm from code alone.
Nothing was run in a browser; behaviour is read from code.

---

## 0. Shared behaviour (applies to all five screens)

### Navigation and shell
- Sidebar items, in order: Dashboard, Members, **Segments**, **Rewards**, **Products**, **Challenges**, Events, **Tiers**. Routes `/admin/segments`, `/admin/rewards`, `/admin/products`, `/admin/challenges`, `/admin/tiers` - `client/components/layout/AppShell.tsx:37-45`.
- Sidebar icons: Segments = Tag, Rewards = Gift, Products = ShoppingBag, Challenges = Target, Tiers = Layers - `client/components/layout/AppShell.tsx:39-44`.
- Active nav item: `bg-primary-subtle text-primary-subtle-fg` - `client/components/layout/AppShell.tsx:101-105`.
- Sidebar is `fixed w-72 border-r border-line bg-surface`, visible from `lg`. Main content is `lg:pl-72`, inner wrapper `mx-auto max-w-6xl px-4 py-6 sm:px-6 lg:px-8 lg:py-8` - `client/components/layout/AppShell.tsx:135,188-189`.
- You must be signed in. Otherwise you are redirected to `/admin/login` - `client/app/admin/(protected)/layout.tsx:26`.
- Hovering a nav link pre-loads its data. Segments also pre-loads the member list used by "Assign members" - `client/lib/swr/preload.ts:77-81`.

### Program scoping
- Every screen shows data for the program picked in the sidebar program switcher. The choice is kept in the `admin_program` cookie - `client/lib/server/program.ts:26-32`.
- Browser reads go through `/api/le/*`, which adds `X-Program-Id` from that cookie - `client/app/api/le/[...path]/route.ts:54-59`. Server actions do the same - `client/lib/api.ts:106-110` (`apiRequest`).
- The API filters every list, read, update and delete by program. An id that belongs to another program returns 404 "<Thing> not found" - `api/app/services/scoping.py:22-36`, `api/app/core/program.py:51-73`.
- Without the header, the API uses the default program. If the program is unknown, it returns 404 `Program not found: <value>` - `api/app/core/program.py:68-80`.
- Switching program clears the whole client cache, so another program's rows never flash on screen - `client/app/admin/(protected)/providers.tsx:15-31`.
- Names that must be unique are unique **per program** only: segment names (`api/app/models/segment.py:28`) and tier names (`api/app/models/tier.py:45`). Reward, product and challenge names do not have to be unique (no check found in `api/app/routers/{rewards,products,challenges}.py`).

### Common UI patterns
- **Page header**: `h1` "text-2xl font-semibold tracking-tight", description `mt-1 text-sm text-muted`, actions on the right on `sm+`, stacked on mobile - `client/components/ui/PageHeader.tsx:11-23`.
- **Primary "New ..." button**: primary variant, size md (`h-10 px-4 text-sm rounded-lg`), Plus icon - `client/components/ui/Button.tsx:10-25`.
- **Card**: `rounded-xl border border-line bg-surface shadow-sm` - `client/components/ui/Card.tsx:8-10`.
- **Table**: `w-full text-sm`. Header `text-xs font-medium text-muted`, `px-4 py-2.5`. Cells `px-4 py-3`. Rows have `divide-y` - `client/components/ui/Table.tsx`.
- **Empty state**: centred, 48px round icon `bg-surface-2 text-faint`, bold title, muted description `max-w-sm`, optional action - `client/components/ui/EmptyState.tsx:17-33`.
- **Form dialogs (FormDialog)**: modal panel `rounded-2xl border bg-surface shadow-xl`. `md` = `max-w-lg`, `lg` = `max-w-2xl`, `sm` = `max-w-sm`. The panel hangs from the top (`items-start`). Header is title (`text-base font-semibold`) + description (`text-[0.8125rem] text-muted`) + X close button. Body `px-5 py-4`. Footer buttons are right-aligned: **Cancel** (secondary) and the submit label (primary) - `client/components/ui/Dialog.tsx:10-99`, `client/components/ui/FormDialog.tsx:100-110`.
  - Field values reset every time the dialog opens - `client/components/ui/FormDialog.tsx:14-17`.
  - On success: green toast with the action's message (fallback "Saved."), list refresh, dialog closes - `client/components/ui/FormDialog.tsx:90-95`.
  - On error: red inline banner above the buttons, and the dialog stays open - `client/components/ui/FormDialog.tsx:103`, `client/components/ui/ErrorBanner.tsx:5`.
  - Close with Escape or a backdrop click - `client/components/ui/Dialog.tsx:45-71`.
- **Confirm dialogs (ConfirmButton)**: `sm` dialog showing the title, the description, **Cancel**, and a red danger button with the confirm label. Errors appear inline in the dialog. Success shows a toast and closes the dialog - `client/components/ui/ConfirmButton.tsx:45-95`.
- **Toasts**: bottom-centre on mobile, bottom-right from `sm`. They close by themselves after 4.5 s and have a Dismiss X - `client/components/ui/Toast.tsx:42,61,96-107`.
- **Field labels**: label on the left, optional `hint` on the right in faint text (for example "optional", "> 0"), optional `help` line below the input (`text-xs text-faint`) - `client/components/ui/Field.tsx:15-61`.
- **Status badge**: "Active" (green, check-circle icon) or "Inactive" (grey, ban icon) - `client/components/ui/StatusBadge.tsx:56-68`.
- **Error text conversion**: an API `{detail: "..."}` is shown as written. A pydantic list is shown as its `msg` values joined with ", ". Other cases show `Request failed (<status>).` or `Cannot reach the API at <url>. Make sure the server is running.` - `client/lib/api.ts:134,171-188`. An unexpected (non-API) error shows "Something went wrong. Please try again." - `client/lib/actions.ts:9-16`.
- An unhandled DB constraint failure becomes **409 "The request conflicts with existing data."** - `api/app/main.py:154-170`.
- Loading: card grids show `CardGridSkeleton` and tables show `TableRowsSkeleton` (5 rows) - `client/components/ui/Skeletons.tsx`.

---

## 1. Segments (`/admin/segments`)

### Reach
- Sidebar → **Segments** (`client/components/layout/AppShell.tsx:39`). Page: `client/app/admin/(protected)/segments/page.tsx`.

### Layout
- PageHeader with title **"Segments"** and description **"Named member cohorts you can assign members to and target with challenges."**, plus the **"+ New segment"** button - `segments/page.tsx:41-45`.
- Body: a card grid `grid gap-4 sm:grid-cols-2 lg:grid-cols-3` - `segments/page.tsx:61`. Segments are sorted alphabetically by name (`api/app/routers/segments.py:53`).
- **Segment card** (`client/components/segments/SegmentCard.tsx`): `Card flex flex-col p-5`.
  - Top row: a 40×40 icon tile (`rounded-lg bg-surface-2 text-xl text-muted`, Tag icon, tinted with the segment colour when set) (`:27-32`), the name (`font-semibold`, truncated) (`:34`), and "N member(s)" (`text-xs text-faint`) (`:35-37`). Right side: ghost icon buttons Pencil (Edit) and red Trash (Delete) (`:40-73`).
  - Description, if set: `mt-3 line-clamp-2 text-[0.8125rem] text-muted` (`:75-77`).
  - Footer: `mt-4 border-t pt-4` with a secondary small button **"Assign members"** (Users icon) (`:78-80`, `AssignMembersDialog.tsx:21-23`).

### States
- Loading: 3 skeleton cards - `segments/page.tsx:47-50`.
- Empty: in a Card, Tag icon, title **"No segments yet"**, description **"Create a segment (e.g. VIP or Newsletter) so you can assign members to it and target it from challenges."**, and a "New segment" button - `segments/page.tsx:51-59`.
- Load error: there is no error state. The page reads only `data`, so a failed fetch leaves the skeleton on screen - `segments/page.tsx:37,47` (rough edge).

### Create / edit segment dialog
- Create: dialog title **"New segment"**, description **"Segments group members so you can target them - e.g. when bulk-assigning a challenge."**, submit **"Create segment"** - `segments/page.tsx:25-28`.
- Edit (Pencil, aria-label "Edit <name>"): title **"Edit segment"**, no description, submit **"Save changes"** - `SegmentCard.tsx:43-49`.
- Fields (`client/components/segments/SegmentFields.tsx`):

| Field | Control | Required | Default | Placeholder / help | Validation |
|---|---|---|---|---|---|
| Name | text | yes (HTML `required`) | current name | "e.g. VIP" | Front end: empty after trim → "Name is required." (`client/lib/actions.ts:707,725`). Back end: duplicate in the program → **"Segment name already exists"** (`api/app/routers/segments.py:29-34,76-82`). No length limit (`api/app/schemas/segment.py:9`). |
| Description | textarea | no; label hint "optional" | current / empty | "What this segment represents" | none |
| Color | colour swatch + text input | no; hint "optional" | current / empty | placeholder "#f59e0b"; help **"Accent used for this segment's badge - pick a color or type a hex value"** | No validation on either side. The swatch shows grey `#94a3b8` unless the text is a 6-digit hex (`SegmentFields.tsx:8-9,44`). The API stores any string (`api/app/schemas/segment.py:11`). |

- Success toasts: **"Segment created."** / **"Segment updated."** - `client/lib/actions.ts:712,730`.
- Name matching is exact and case-sensitive ("VIP" and "vip" can both exist). The client trims the name before sending - `client/lib/actions.ts:20-23,694-699`. Case-sensitivity follows from `models/segment.py:28` (plain unique constraint). `?` A collation override could change this; I found none.

### Delete segment
- Red Trash icon (aria-label "Delete <name>") opens a confirm dialog titled **`Delete "<name>"?`** with the text **"Members lose this segment, and it's removed from any challenge it was bulk-assigned to. This cannot be undone."**, button **"Delete segment"**, toast **"Segment deleted."** - `SegmentCard.tsx:55-72`.
- Cascades:
  - The member ↔ segment rows are deleted (`api/app/models/segment.py:30`, `api/app/models/member.py:99` ON DELETE CASCADE).
  - The challenge's "bulk-assigned to this segment" record is deleted (`api/app/models/challenge.py:97` CASCADE).
  - Challenge assignments already handed to members are **kept**. Only the segment link is removed.
- **Not** done on delete:
  - Tiers are not re-evaluated (`api/app/routers/segments.py:90-98` has no `reapply_tiers`). Members keep a tier that relied on this segment until something else triggers a re-check.
  - Tier conditions that reference the segment are not cleaned up. They can never match again, and the tier card shows the raw segment id because the name lookup fails (`client/lib/conditions.ts:135-138`).
  - Event rules with add/remove-segment effects later skip with "Segment no longer exists" (`api/app/services/rules/effects.py:285-286`).

### Assign members (AssignMembersDialog)
- Opened from the card footer button **"Assign members"**. Dialog title **"Assign members"**, description **`Add members to "<segment name>".`**, size `lg` (`max-w-2xl`) - `client/components/segments/AssignMembersDialog.tsx:21-29`.
- Layout, top to bottom - `AssignMembersDialog.tsx:105-158`:
  1. Search input, placeholder **"Search members…"** (aria-label "Search members").
  2. A "Select all" checkbox row with a bottom border. The label is **"Select all"**, or **"Select all (N matching)"** while a search is typed.
  3. A scrollable list (`max-h-[50vh] divide-y`). Each row is a checkbox labelled **"<name> · <email>"**.
  4. A footer with a top border: left **"N selected"** (`text-xs text-faint`), right a primary **"Assign"** / **"Assign (N)"** button.
  - There is no Cancel button. Close with X, Escape or a backdrop click.
- Behaviour:
  - Members already in the segment are left out of the list (`:51-54`).
  - Search runs in the browser on name or email, case-insensitive (`:56-62`).
  - Selections are kept when the search changes.
  - "Select all" toggles only the rows currently shown (`:68-76`).
  - "Assign" is disabled while 0 are selected (`:147`).
  - The selection resets every time the dialog opens (`:31-33`).
- Messages:
  - While loading: **"Loading members…"** (`:113-114`).
  - No search match: **`No members match "<query>".`** (`:116-118`).
  - Everyone already in: empty state **"Everyone's already in"** / **"Every member is already part of this segment."** (`:94-102`).
  - Members failed to load: empty state **"Couldn't load members"** with the error text (`:84-92`).
- On success: toast **"Members assigned."** and the dialog closes. The server's "Assigned to N member(s); M already had it." message is **hidden**, because the dialog passes its own `successMessage` (`AssignMembersDialog.tsx:149`, `client/components/ui/ActionButton.tsx:34`, `client/lib/actions.ts:760-763`).
- On error: a red toast with the API detail, and the dialog stays open (`client/components/ui/ActionButton.tsx:37`). Examples:
  - "Select at least one member." (`client/lib/actions.ts:751`, not reachable from the UI)
  - `Member(s) not found: <ids>` (404) (`api/app/routers/segments.py:120-122`)
  - "Segment not found"
- **Limit**: the list shows at most 1,000 members, newest first, with no paging. Members beyond that cannot be found here (`client/lib/swr/keys.ts:24`, `client/lib/swr/hooks.ts:39`, `api/app/routers/members.py:80-95`).
- Automatic side effects of assigning (`api/app/routers/segments.py:131-154`):
  - Every active, not-expired challenge that was bulk-assigned to this segment is assigned to the selected members who do not have it yet. Their personal deadlines are computed now (`api/app/services/challenges.py:102-161`).
  - Tiers are re-evaluated for the **newly added** members (`segments.py:147-152`).
  - Members already in the segment are counted as "skipped".
- Other places that change segment membership: the member form (`api/app/services/segments.py:17-47`) and event-rule effects (`api/app/services/rules/effects.py:272-291`). These are out of scope here, but they trigger the same challenge sync.

---

## 2. Rewards (`/admin/rewards`)

### Reach
- Sidebar → **Rewards**. Page: `client/app/admin/(protected)/rewards/page.tsx`.

### Layout
- Header title **"Rewards"**. The description is **"N reward(s) · M active"** when rewards exist, otherwise **"Catalog of redeemable rewards."** Button **"+ New reward"** - `rewards/page.tsx:43-51`.
- One Card holding a table - `rewards/page.tsx:53-80`. Columns in order: **Reward | Cost | Stock | Status | Actions** (`:67-71`).
  - Reward: name (`font-medium`) with the description below it (`text-xs text-muted line-clamp-1 max-w-md`) - `client/components/rewards/RewardRow.tsx:75-82`.
  - Cost: number with a small faint "pts" (for example "1,000 pts") - `RewardRow.tsx:83-86`.
  - Stock: faint **"Unlimited"** when empty, red **"Out of stock"** when ≤ 0, otherwise the number - `RewardRow.tsx:87-95`.
  - Status: Active / Inactive badge - `RewardRow.tsx:96-98`.
  - Actions: a ghost "⋮" icon button (aria "Actions for <name>") opening a `w-48` dropdown with: **Deactivate** (ban icon) / **Activate** (check icon), **Copy ID**, **Edit**, and **Delete** (red) - `RewardRow.tsx:100-136`.
  - Rows highlight on hover (`hover:bg-surface-2/60`).
- Row order: the API sets **no ORDER BY**, so the order is whatever the database returns - `api/app/routers/rewards.py:42-45`. The page asks for up to 1,000 rewards - `client/lib/swr/keys.ts:43`.

### States
- Loading: skeleton rows. Empty: Gift icon, **"No rewards yet"**, **"Create your first reward so members have something to redeem their points for."**, and a New reward button - `rewards/page.tsx:54-62`. There is no error state (same rough edge as Segments).

### Create / edit reward dialog
- Create: title **"New reward"**, description **"Add a redeemable reward to the catalog."**, submit **"Create reward"** - `rewards/page.tsx:26-29`.
- Edit: title **"Edit reward"**, submit **"Save changes"** - `RewardRow.tsx:35-37`.
- Fields (`client/components/rewards/RewardFields.tsx`):

| Field | Control | Required | Default | Hint / help | Validation |
|---|---|---|---|---|---|
| Name | text, placeholder "e.g. $10 gift card" | yes | - | - | FE "Name is required." (`client/lib/actions.ts:310,330`). The API also accepts an empty string (`api/app/schemas/reward.py:11`). |
| Description | textarea, placeholder "Optional details shown to members" | no | - | - | - |
| Points cost | number, min 1, step 1 | yes | - | hint **"> 0"** | FE "Points cost must be greater than 0." (`actions.ts:311-312`). API `gt=0`, integer (`api/app/schemas/reward.py:13`). A decimal sent past the browser check returns pydantic's "Input should be a valid integer, got a number with a fractional part" `?` (exact text depends on pydantic 2.9.2). |
| Stock | number, min 0, step 1 | no | empty | help **"Leave blank for unlimited"** | Blank sends `null` = unlimited (`actions.ts:300`). API `ge=0` (`schemas/reward.py:14`). |
| Active (available to redeem) | checkbox | - | checked for new rewards | - | - |

- Fields sit in a two-column grid for Points cost / Stock (`RewardFields.tsx:25`).
- Toasts: **"Reward created."**, **"Reward updated."** - `actions.ts:317,337`.

### Row actions
- **Activate / Deactivate**: runs at once with no confirm. Toasts **"Reward activated."** / **"Reward deactivated."** On failure, a red toast with the error or "Something went wrong." - `RewardRow.tsx:61-71`.
- **Copy ID**: toast **"Reward ID copied."**, or on failure **"Couldn't copy reward ID."** - `RewardRow.tsx:52-59`.
- **Delete**: confirm **`Delete "<name>"?`**, text **"This removes the reward from the catalog. Existing redemption history is kept."**, button **"Delete reward"**, toast **"Reward deleted."** - `RewardRow.tsx:123-135`.
  - **Contradiction**: a reward that has *any* redemption (bought or given free) **cannot be deleted**. `redemptions.reward_id` is NOT NULL with no cascade (`api/app/models/redemption.py:21`, `supabase/migrations/20260921104524_remote_schema.sql:744`). The API answers 409 **"The request conflicts with existing data."** (`api/app/main.py:154-170`), which shows as a red banner in the confirm dialog. The API's own test confirms this: `api/tests/integration/test_member_reward_flow.py:11-14`. The workaround is to **Deactivate** the reward.
  - A deleted reward that was a challenge prize is cleared from the challenge (`api/app/models/challenge.py:38` ON DELETE SET NULL).
  - **Suspected bug (high confidence from reading the code, not reproduced)**: **Edit** and **Delete** live inside the dropdown panel. A click on any item also closes the panel (`client/components/ui/DropdownMenu.tsx:70`), and closing it unmounts the panel's children (`:61`), including the FormDialog/ConfirmButton that just opened. The edit and confirm dialogs would therefore never appear. Activate and Copy ID are unaffected because their handlers live on the row. The same applies to Products.

### Stock and active rules
- A reward can be handed out only when it is active **and** (stock is empty or stock > 0) - `api/app/services/rewards.py:39-43`.
- API errors: **"Reward is not active"** and **"Reward is out of stock"** (`services/rewards.py:46-51`), and **`Insufficient points: has X, needs Y`** (`api/app/routers/redemptions.py:37-38`).
- Stock goes down by 1 on every redemption **and** every free prize: member-page Redeem, member-page Assign free, a challenge prize on completion, and the event-rule "grant reward" effect - `services/rewards.py:54-74`, `routers/redemptions.py:40`, `services/challenges.py:362-374`, `services/rules/effects.py:175-187`. Stock never goes back up automatically.
- An out-of-stock reward still shows the **Active** badge. Only the Stock column says "Out of stock" (`RewardRow.tsx:90-91,97`).

### Redemption vs assignment (done from the member detail page, not this screen)
- Member detail → **"Redeem / assign"** opens a dialog titled **"Rewards"** with the description **"Redeem a reward for points, or assign one as a free prize."** It lists only active, in-stock rewards - `client/components/members/GrantRewardDialog.tsx:32-46`.
  - **Redeem**: takes `pointsCost` from the balance (spend transaction "Redeemed: <name>"), reduces stock, records redemption source `redeemed`, re-evaluates the tier - `api/app/routers/redemptions.py:19-55`. The button is disabled when the member cannot afford it (tooltip "Insufficient points to redeem"). Toast "Reward redeemed." - `GrantRewardDialog.tsx:83-96`.
  - **Assign free**: costs no points, reduces stock, records source `assigned` - `routers/redemptions.py:58-85`. An optional checkbox **"Email free prizes to the member, with a link to claim them"** sends a claim email. Toasts: "Prize assigned." / "Prize assigned and emailed." / "Prize assigned, but the email was not sent. <reason>" - `client/lib/actions.ts:268-291`.
  - Empty state: **"No available rewards"** / **"Create an active, in-stock reward first."** - `GrantRewardDialog.tsx:48-53`.
- Because a tier's "points balance" is the **current** balance, a redemption can **demote** a member's tier at once (`api/app/services/points.py:35-37`, `api/app/services/rules/fields.py:139`).

---

## 3. Products (`/admin/products`)

### Reach
- Sidebar → **Products**. Page: `client/app/admin/(protected)/products/page.tsx`.

### Layout
- Header title **"Products"**. The description is **"N product(s) · M active"**, or **"Catalog of products members can purchase."** when there are none. Button **"+ New product"** - `products/page.tsx:43-51`.
- Card with a table. Columns: **Product | Price | Category | Status | Actions** (`:66-71`).
  - Product: name with a one-line description below.
  - Price: formatted currency, for example "€14.50" (en-US `Intl` currency) - `client/components/products/ProductRow.tsx:82-84`, `client/lib/format.ts:28-33`.
  - Category: muted text, or a faint "-" when empty - `ProductRow.tsx:85-87`.
  - Status: Active / Inactive badge.
  - Actions: the same "⋮" dropdown as Rewards, with **Deactivate/Activate, Copy ID, Edit, Delete** - `ProductRow.tsx:91-129`.
- Sorted newest first (`api/app/routers/products.py:41`). The page asks for up to 1,000 products.

### States
- Empty: ShoppingBag icon, **"No products yet"**, **"Create your first product so members have something to buy."** - `products/page.tsx:56-62`. There is no error state.

### Create / edit product dialog
- Create: title **"New product"**, description **"Add a product members can purchase."**, submit **"Create product"** - `products/page.tsx:26-29`.
- Edit: **"Edit product"** / **"Save changes"** - `ProductRow.tsx:35-37`.
- Fields (`client/components/products/ProductFields.tsx`):

| Field | Control | Required | Default | Hint / help | Validation |
|---|---|---|---|---|---|
| Name | text, placeholder "e.g. Ethiopia Yirgacheffe Whole Beans, 250g" | yes | - | - | FE "Name is required." |
| Description | textarea, placeholder "Details shown to members in the catalog" | no | - | - | - |
| Price | number, min 0.01, step 0.01 | yes | on edit: `priceCents/100` to 2 decimals | hint = the product's currency (**"EUR"** for new products) | Converted to cents with `Math.round(price*100)` (`client/lib/actions.ts:375-384`). FE "Price must be greater than 0." (`:392-393,411-412`). API `price_cents gt=0` (`api/app/schemas/product.py:13`). |
| Category | text, placeholder "e.g. coffee" | no | - | help **"Optional grouping"** | - |
| Active (visible to members) | checkbox | - | checked for new products | - | - |

- **Currency cannot be set in the UI.** The form never sends it, so new products are always EUR (`api/app/schemas/product.py:14`), and edits leave the currency unchanged (`api/app/routers/products.py:61` uses exclude_unset).
- Toasts: **"Product created."**, **"Product updated."**, **"Product activated."** / **"Product deactivated."**, **"Product ID copied."** / **"Couldn't copy product ID."** - `client/lib/actions.ts:397,416`, `ProductRow.tsx:51-69`.

### Delete
- Confirm **`Delete "<name>"?`**, **"This removes the product from the catalog. Existing purchase history is kept."**, **"Delete product"**, toast **"Product deleted."** - `ProductRow.tsx:115-127`.
- This statement is true: past purchases keep a snapshot of the name and price, and their product link is set to empty - `api/app/models/purchase.py:16-23,29`.
- The same suspected dropdown bug applies to Edit/Delete (see Rewards).

### How purchases are recorded (member app, not admin)
- Purchases are created **only by members** in the member app: Products → "Catalogue" tab → **Buy** - `client/components/products/BuyButton.tsx:42-58`. Each Buy is quantity 1 (`client/lib/member/actions.ts:66-69`). There is no admin UI to record a purchase. `?` External callers can POST `/members/{id}/purchases` with `quantity` > 0 (`api/app/schemas/purchase.py:12`).
- The member catalogue shows **active products only** (`client/app/(member)/products/page.tsx:29`). Buying an inactive product returns **"Product is not available"** (`api/app/services/products.py:57-60`).
- The purchase is simulated:
  - No payment and no balance check (`api/app/routers/purchases.py:31-34`).
  - **No loyalty points are earned** from a purchase. Nothing in the purchase path writes a points transaction (`routers/purchases.py:19-41`).
  - Name, unit price, total and currency are snapshotted when the purchase is made (`api/app/services/products.py:63-80`).
- After each purchase the member's **tier is re-evaluated**, because tiers can read lifetime spend and count (`routers/purchases.py:35-38`).
- Spend signals:
  - Tier conditions can use **"Lifetime purchase spend (cents)"** and **"Lifetime purchase count"** (`api/app/services/rules/fields.py:111-123`). These are lifetime totals only, on purpose (`fields.py:21-24`).
  - `GET /members/{id}/purchase-stats?days=` (default 7, max 365) returns lifetime and windowed spend (`routers/purchases.py:16,69-77`, `services/products.py:83-137`).
  - Admin Member detail shows a **"Total spent"** tile ("N purchases") and a **"Purchases"** widget ("Simulated buys, used to track spend and frequency", columns Product | Qty | Total | When) - `client/components/members/MemberDetail.tsx:159-166,318-358`.
  - The Products screen itself shows no sales figures.
- Currency handling assumes one currency per member (`services/products.py:115-123`).

---

## 4. Challenges (`/admin/challenges`)

### Reach
- Sidebar → **Challenges**. Page: `client/app/admin/(protected)/challenges/page.tsx`.

### Layout
- Header title **"Challenges"**. The description is **"N challenge(s) · M active"**, or **"Goals members complete to earn points and prizes."** when there are none. Button **"+ New challenge"** - `challenges/page.tsx:44-52`.
- Grid `grid gap-4 md:grid-cols-2` (two columns from `md`) - `:81`. Sorted newest first (`api/app/routers/challenges.py:86`).
- **Challenge card** (`client/components/challenges/ChallengeCard.tsx`), `Card flex flex-col p-5`:
  - Top row: a 40×40 tile `bg-accent-aqua/15 text-accent-aqua` with a Target icon; the name (`font-semibold`); the description (`line-clamp-2 text-[0.8125rem] text-muted`); and the Active/Inactive badge on the right (`:57-72`).
  - Badge row (`mt-4 flex flex-wrap gap-2`) (`:74-98`):
    - neutral **"Target N"**
    - primary **"N pts"**, only if reward points > 0
    - warning (amber) badge with the prize reward's name, if a prize is set and found in the rewards list
    - neutral **"Expires <Mon D, YYYY>"**, if a fixed date is set
    - neutral **"Nd after assignment"**, if days are set
  - Section label **"Assigned segments"** (Tag icon, `text-[0.6875rem] uppercase tracking-wide text-muted`, so it shows as "ASSIGNED SEGMENTS"). Below it, primary badges with segment names, or **"Not assigned to any segment yet."** (`:100-115`).
  - Footer (`mt-5 border-t pt-4`): left a secondary small **"Assign to segment"** button (Users icon); right ghost icon buttons Copy (aria "Copy ID for <name>"), Pencil (Edit) and red Trash (`:117-165`).

### States
- Loading: 4 skeleton cards.
- Load error (this is the only one of the five screens with one): AlertTriangle, **"Couldn't load challenges"**, the error message, and a **"Retry"** secondary button - `challenges/page.tsx:54-66`.
- Empty: Target icon, **"No challenges yet"**, **"Create a challenge to give members a goal - completing it grants points and/or a prize."** - `:71-79`.

### Create / edit challenge dialog
- Create: **"New challenge"**, description **"Define a goal members can complete to earn points or a prize."**, submit **"Create challenge"** - `challenges/page.tsx:26-29`.
- Edit: **"Edit challenge"** / **"Save changes"** - `ChallengeCard.tsx:138-140`.
- Fields (`client/components/challenges/ChallengeFields.tsx`):

| Field | Control | Required | Default | Help | Validation |
|---|---|---|---|---|---|
| Name | text, placeholder "e.g. Refer 3 friends" | yes | - | - | FE "Name is required." |
| Description | textarea, placeholder "Optional details" | no | - | - | - |
| Target | number, min 1, step 1 | yes | 1 | **"Progress needed to complete"** | FE "Target value must be greater than 0." (`client/lib/actions.ts:476-477`). API `gt=0` (`api/app/schemas/challenge.py:14`). |
| Reward points | number, min 0, step 1 | no | 0 (blank → 0) | **"Granted on completion"** | API `ge=0` (`schemas/challenge.py:15`). A negative value sent past the browser check returns pydantic "Input should be greater than or equal to 0" `?`. |
| Prize reward | select: **"No prize"** + every reward (active and inactive) | no | current | **"Optional - assigned on completion"** | API: a reward from another program or a missing reward → 404 "Reward not found" (`api/app/routers/challenges.py:56-57,107-108`). |
| Expires at | datetime-local | no | current (shown in browser local time) | **"Fixed deadline for everyone / cutoff for new assignments"** | - |
| Expires after (days) | number, min 1, step 1 | no | blank | **"Expires N days after being assigned to a member — leave blank to use the fixed date above for everyone."** | API `gt=0` (`schemas/challenge.py:23`) |
| Active (can be assigned) | checkbox | - | checked for new challenges | - | - |

- Target/Reward points and Expires at/Expires after are shown in two-column grids (`ChallengeFields.tsx:32,77`).
- Toasts: **"Challenge created."**, **"Challenge updated."** (`client/lib/actions.ts:482,502`).
- `startsAt` exists in the API but is not in the form, and nothing enforces it (only echoed at `api/app/services/challenges.py:292`).

### Deadlines (how the two expiry fields combine)
- A member's personal deadline is set **once, at assignment time**. It is `assigned_at + expiryDays` when days are set, otherwise the fixed **Expires at** - `api/app/services/challenges.py:40-52`.
- Editing either field later does **not** change deadlines already handed out (`challenges.py:45-48`).
- The fixed **Expires at** also blocks *new* assignments once it has passed: **"Challenge has expired"** - `challenges.py:94-99`. This applies even when days are set.
- The definition card has no "expired" indicator. A past "Expires …" badge and the Active badge both still show (`ChallengeCard.tsx:71,88-92`).

### Assign to segment (bulk assignment)
- Dialog **"Assign to segment"**, description **`Assign "<name>" to every member in a segment.`**, field **"Segment"** with the select placeholder **"Choose a segment"** (**"Loading…"** while loading), help **"Every member currently in this segment will be assigned."**, submit **"Assign"** - `ChallengeCard.tsx:170-208`.
- Success toast: **"Assigned to N member(s); M already had it."** (`client/lib/actions.ts:533-536`).
- Errors (inline banner):
  - "Choose a segment." (`actions.ts:525`)
  - **"Challenge is not active"** / **"Challenge has expired"** (`api/app/services/challenges.py:94-99`)
  - "Segment not found"
- What happens (`api/app/services/challenges.py:164-220`):
  - Each current segment member without the challenge gets an assignment with status `assigned`, progress 0, and their own deadline.
  - Members who already have the challenge in **any** status, including completed or expired, are skipped. A member can never repeat a challenge.
  - The segment is recorded on the challenge (it appears under "Assigned segments") **only if the segment had at least one member** (`:205-218`).
  - Once recorded, **people who join the segment later get the challenge automatically**, as long as the challenge is still active and not expired (`challenges.py:102-161`, called from `api/app/routers/segments.py:145` and `api/app/services/segments.py:47`).
  - Surprise: assigning to an **empty** segment shows "Assigned to 0 member(s); 0 already had it." and records nothing, so later joiners are **not** auto-assigned.
- Single-member assignment happens on the member detail page ("Assign challenge" → **"Assign a challenge"** / **"Active challenges the member hasn't been assigned yet."**) - `client/components/members/AssignChallengeDialog.tsx:26-46`. API errors include **"Challenge already assigned to this member"** (`api/app/routers/challenges.py:149,159`).

### Progress, statuses and payout (member detail page)
- Statuses and badges: **Assigned** (neutral, clock), **In progress** (primary, bolt), **Completed** (success), **Expired** (warning), **Cancelled** (danger) - `client/components/ui/StatusBadge.tsx:16-25`.
- Nothing in the code ever sets **cancelled** (grep: it is only read, never assigned, in `api/app/services/challenges.py:242,281,313`).
- Member challenge item (`client/components/members/MemberChallengeItem.tsx`):
  - Shows "N pts on completion", **"Progress"** with "current / target" and a meter, and "Expires <date>".
  - Buttons:
    - **"+ Progress"** opens **"Add progress"** / `Record progress toward "<name>".` with fields Amount (min 1, default 1) and Note (optional), submit "Add progress". Toast "Progress recorded."
    - **"Complete"**: toast "Challenge completed."
    - Trash opens **`Remove "<name>"?`** / "This unassigns the challenge from this member." / "Remove". Toast "Challenge removed."
- Progress rules (`api/app/services/challenges.py:235-247,318-327`):
  - Adding progress moves the status to `in_progress`. Reaching the target auto-completes the challenge.
  - Blocked with **"Challenge is already completed"** / **"Challenge is already cancelled"** / **"Challenge has expired"**. The expired status is saved the first time progress is attempted after the deadline (`api/app/routers/challenges.py:225-229`).
  - Progress is **not** blocked when the challenge has been deactivated. Deactivation only stops new assignments.
  - FE validation: "Enter a positive amount." (`client/lib/actions.ts:566-567`).
- **Complete** (admin force-complete) pays out even when progress is short or the deadline has passed. It is refused only when already completed or cancelled - `api/app/services/challenges.py:306-315`. The button is shown for expired assignments too (`MemberChallengeItem.tsx:106`).
- Payout on completion (`api/app/services/challenges.py:330-374`):
  - Reward points are granted as an earn transaction "Challenge completed: <name>". The **tier multiplier is NOT applied** (`:352`). The tier is re-evaluated (via `api/app/services/points.py:37`).
  - The prize reward is given free (points 0, source `assigned`, stock −1) **only if** it is active and in stock. Otherwise it is **skipped silently**, and the challenge still completes (`:362-374`).
- Lowering a challenge's target does not complete members already above it until their next progress (`apply_progress` is the only place that checks, `:323-325`).

### Delete challenge
- Confirm **`Delete "<name>"?`**, **"This removes the challenge and all of its member assignments. This cannot be undone."**, **"Delete challenge"**, toast **"Challenge deleted."** - `ChallengeCard.tsx:146-163`.
- Cascades: assignments and segment links (`api/app/models/challenge.py:48-49,67,96`). Points and prizes already paid are kept (they live in the ledger and redemptions).
- Copy ID toasts: **"Challenge ID copied."** / **"Couldn't copy challenge ID."** (`ChallengeCard.tsx:46-53`).

---

## 5. Tiers (`/admin/tiers`)

### Reach
- Sidebar → **Tiers**. Page: `client/app/admin/(protected)/tiers/page.tsx`.

### Layout
- Header title **"Tiers"**, description **"Points, purchase spend, segments and custom attributes, combined however you like, applying an earn-rate multiplier."**, button **"+ New tier"** - `tiers/page.tsx:54-58`.
- Grid `sm:grid-cols-2 lg:grid-cols-3`. Cards are sorted by **rank ascending** (lowest first) (`api/app/routers/tiers.py:55`). Assignment tries the highest rank first (see below), so the display order is the reverse of the evaluation order.
- **Tier card** (`client/components/tiers/TierCard.tsx`), `Card flex flex-col p-5`:
  - Top row: a 40×40 tile `bg-accent-yellow/15 text-accent-yellow` with a Layers icon; the name; and "N member(s)" (or "…" while member stats load); Edit and red Delete icon buttons on the right (`:31-78`).
  - Two stat boxes (`mt-5 grid grid-cols-2 gap-3`, each `rounded-lg bg-surface-2 px-3 py-2.5`): **"Rank"** → number, and **"Earn rate"** → "1.5×" (`:79-90`).
  - Condition chips (`rounded-md border bg-surface-2 px-2 py-0.5`) joined by a faint **"and"**. With no conditions it reads **"Every member qualifies"** (`:91-104`). Chip text is a sentence such as "Member's points balance is at least 500", "Member's segments include VIP", or "Member's lifetime purchase spend (cents) is at least 20000" (`client/lib/conditions.ts:131-144`). An unknown field shows **"Unknown field"**.
  - Primary badge **"×1.5 points on earn"** (`:105-107`).
- The member count comes from `/members/stats` `byTier`, which counts members by their **stored** tier (`client/app/admin/(protected)/tiers/page.tsx:47-50`, `api/app/services/members.py:134-169`).

### States
- Empty: Layers icon, **"No tiers yet"**, **"Create tiers to reward members with higher earn rates as their balance grows."** - `tiers/page.tsx:64-72`. There is no error state.

### Create / edit tier dialog
- Create: **"New tier"**, description **"Members meeting every condition below earn at this multiplier."**, submit **"Create tier"** - `tiers/page.tsx:34-37`.
- Edit: **"Edit tier"**, same description, **"Save changes"** - `TierCard.tsx:50-53`.
- Fields (`client/components/tiers/TierFields.tsx`):

| Field | Control | Required | Default | Hint / help | Validation |
|---|---|---|---|---|---|
| Name | text, placeholder "e.g. Gold" | yes | - | - | FE "Name is required."; API **"Tier name already exists"** (per program, exact match) (`api/app/routers/tiers.py:28-33,78-84`) |
| Rank | number, step 1 (negatives allowed) | yes | 0 | hint **"highest tried first"** | FE "Rank must be a number." (`client/lib/actions.ts:636,664`). API integer (`api/app/schemas/tier.py:14`). Duplicate ranks are allowed and ties go to the tier created first (`api/app/services/tiers.py:31`). |
| Multiplier | number, min 0, step 0.1 | yes | 1 | hint **"> 0"** | FE "Multiplier must be greater than 0." (`actions.ts:637-638`). API `gt=0`, float (`schemas/tier.py:21`). Values below 1 are allowed and reduce earning. |
| Conditions | builder of rows | no | none | help **"All must match. No conditions means every member qualifies - useful for a catch-all lowest tier."** | see below |

- With no rows, the builder shows **"Every member qualifies."**
- **"+ Add condition"** (ghost) adds a row that always starts as "Points balance / is at least / (empty)" (`TierFields.tsx:84-97`, `client/lib/conditions.ts:115-121`).
- Each row has: Field select, Operator select, Value input, and an X button (aria "Remove condition").
- Row layout: on `sm+` the grid is `sm:grid-cols-[minmax(0,1.3fr)_minmax(0,1fr)_minmax(0,1fr)_auto]`. On mobile each row is a bordered box (`TierFields.tsx:120`).
- Changing the Field resets the operator and value (`:124-128`).
- Field options and operators (`client/lib/tiers/conditions.ts:26-34`, `client/lib/conditions.ts:71-105`, mirrored in `api/app/services/rules/fields.py:111-123` and `api/app/services/rules/conditions.py:21-29`):

| Field label | Value input | Operators (labels) |
|---|---|---|
| Points balance | number | is at least, is more than, is, is not, is at most, is less than |
| Lifetime purchase spend (cents) | number (in **cents**) | same as above |
| Lifetime purchase count | number | same as above |
| Segments | segment select (or **"Nothing to choose yet"** when there are none) | include |
| each custom member attribute (its label) | text / number / date / select of options / Yes-No | text: is, is not, contains; number: as above; date: is before, is after, is on; select: is, is not; boolean: is |

- Conditions are sent as JSON. A broken payload gives FE "Couldn't read the tier's conditions." (`client/lib/actions.ts:616-625,639`).
- API condition errors (inline banner) - `api/app/services/rules/conditions.py:34-73`:
  - `The condition on '<label>' needs a value.` (for example when Add condition is clicked and the value left blank)
  - `The condition on '<label>' needs an id.`
  - `Unknown condition field '<path>'.`
  - `'<label>' can't be compared with '<op>'.`
  - "Segment not found"
  - custom attribute type errors such as `'<label>' must be a number.` / `must be a date in YYYY-MM-DD format.` / `must be one of: …` / `must be true or false.` (`api/app/services/custom_attributes.py:57-104`)
- Toasts: **"Tier created."**, **"Tier updated."**, **"Tier deleted."** (`client/lib/actions.ts:647,675,686`).

### How assignment works
- All conditions are ANDed. There is no OR and no nesting. For an OR, create two tiers - `api/app/schemas/tier.py:15-19`, `api/app/services/rules/conditions.py:94-97`.
- Tiers are tried from the **highest rank down**, with ties broken by creation order. The member gets the **first** tier whose conditions all match, or **no tier** - `api/app/services/tiers.py:27-43,52-61`.
  - A higher-ranked tier with fewer conditions therefore hides lower ones.
  - A tier with no conditions at the highest rank captures everyone.
- "Points balance" is the **current** balance, not lifetime earnings (`api/app/services/rules/fields.py:139`). Burns and redemptions can demote.
- A missing value never satisfies more/less comparisons (`conditions.py:85-87`). "contains" on text is case-insensitive (`:77-80`).
- **Earn-rate multiplier**:
  - Applies to manual "earn" points (`api/app/routers/points.py:51-52`) and to event-rule "add points" effects (`api/app/services/rules/effects.py:127-137`). Both use the tier **when the points arrive**.
  - Does **not** apply to burns, adjustments, challenge completion points (`api/app/services/challenges.py:352`) or purchases (purchases earn no points).
  - Rounding uses Python `round()`, which rounds half to even (2.5 → 2).
- **When tiers are re-evaluated** (automatic; no schedule exists - `fields.py:21-24`):
  - every points transaction: earn, burn, adjust, redeem, challenge points (`api/app/services/points.py:35-37`)
  - every purchase (`api/app/routers/purchases.py:35-38`)
  - member create/update (`api/app/services/members.py:56,91-94`), joining a program (`api/app/services/memberships.py:59,118`)
  - after an event's rules applied anything (`api/app/services/events.py:161-167`)
  - bulk "Assign members" to a segment, for newly added members only (`api/app/routers/segments.py:147-152`)
  - **for every member in the program** when a tier is created, edited or deleted (`api/app/routers/tiers.py:41,92,109`)
- **Not** re-evaluated:
  - segment delete (`api/app/routers/segments.py:90-98`)
  - custom attribute create (default backfill) or delete (`api/app/routers/member_attributes.py:128-148`, no tier call)
  - product delete or edit
  - passage of time
- Delete tier: confirm **`Delete "<name>"?`**, **"Members in this tier are re-checked against every remaining tier and reassigned, or left tierless if none match. This cannot be undone."**, **"Delete tier"** (`TierCard.tsx:59-76`). This matches the backend (`api/app/routers/tiers.py:98-110`, `api/app/models/member.py:45` SET NULL).
- After any tier change, the page refreshes both tiers and members, so the counts update (`tiers/page.tsx:16-23`).

---

## 6. Contradictions between frontend and backend

1. **Reward delete**: the confirm text says "Existing redemption history is kept", but the API refuses to delete any reward with redemptions (409 "The request conflicts with existing data.") - `RewardRow.tsx:130` vs `api/app/models/redemption.py:21`, `api/tests/integration/test_member_reward_flow.py:11-14`.
2. **Segment edit cannot clear Description or Color.** The FE sends `null` for blank fields, but the API drops `None` values (`exclude_none=True`), so the old value stays and the toast still says "Segment updated." - `client/lib/actions.ts:694-699` vs `api/app/routers/segments.py:75`.
3. **Tier rank order**: the hint says "highest tried first", but the list is shown lowest rank first - `TierFields.tsx:44` vs `api/app/routers/tiers.py:55` (and `api/app/services/tiers.py:31`).
4. **TS `Reward` type has `segments: string[]`**, which the API never returns - `client/lib/types.ts:151` vs `api/app/schemas/reward.py:10-28`.
5. **Validation lives mostly in the FE**. The API accepts empty names for segments, rewards, products, challenges and tiers (`name: str` with no min length in each schema). The FE checks are the only guard.
6. **Segment colour**: the help says "type a hex value", but neither side validates it. Any string is stored and used as a CSS colour (`SegmentFields.tsx:38`, `SegmentCard.tsx:29`, `api/app/schemas/segment.py:11`).
7. **AssignMembersDialog success message**: the server builds "Assigned to N member(s); M already had it.", but the UI shows only "Members assigned." (`AssignMembersDialog.tsx:149`).
8. **Tiers empty-state copy** says tiers reward members "as their balance grows", but tiers can be based on spend, segments or attributes, and the balance used is current, not lifetime (`tiers/page.tsx:69`).

## 7. Could not confirm (`?`)
- The Rewards/Products dropdown **Edit** and **Delete** never opening (code reading strongly suggests it; not run in a browser) - `client/components/ui/DropdownMenu.tsx:61,70`.
- Timezone of **Expires at**. The `datetime-local` value is turned into ISO inside a **server action** (`"use server"`, `client/lib/actions.ts:1,464-468`), so it is read in the *server's* timezone, while the edit form shows it in the browser's timezone (`client/lib/format.ts:63-77`). If they differ, the deadline shifts. Deployment timezone unknown.
- Exact pydantic message wording for out-of-range numbers sent past browser validation (pydantic 2.9.2, `api/requirements.txt:4`). No custom `RequestValidationError` handler exists (`api/app/main.py:120-170`).
- When rewards have not loaded yet, opening **Edit challenge** may render the Prize select without the saved prize. Saving would then clear the prize (`ChallengeFields.tsx:64-75` uses an uncontrolled `defaultValue`; `challenges/page.tsx:86` passes `rewards ?? []`). Not reproduced.
- Whether segment and tier name uniqueness is case-sensitive under the production DB collation (assumed yes).

## 8. For the product team (bugs and rough edges; not fixed)
- **Edit/Delete in the Rewards and Products row menus probably do not open** (the dropdown unmounts the dialog) - `client/components/ui/DropdownMenu.tsx:61,70`, `RewardRow.tsx:122-135`, `ProductRow.tsx:114-127`.
- **Rewards with any redemption cannot be deleted.** The error is a generic 409, and the confirm text promises otherwise. Consider soft-delete or a clear message.
- **Segment description/colour cannot be cleared** once set (`api/app/routers/segments.py:75`).
- **Deleting a segment or custom attribute leaves tier conditions dangling and does not re-evaluate tiers.** Cards show a raw id or "Unknown field", and editing such a tier fails with `Unknown condition field '…'`.
- **Bulk-assigning a challenge to an empty segment** records nothing, so future members are never auto-assigned. The toast gives no hint.
- **The AssignMembersDialog loads only the newest 1,000 members**, with no server search or paging (`client/lib/swr/keys.ts:24`).
- **Assign members** hides the assigned/skipped counts.
- **Rewards list has no ORDER BY** (`api/app/routers/rewards.py:45`), so row order can change between loads.
- **No load-error state** on Segments, Rewards, Products or Tiers. A failed fetch shows a permanent skeleton. Only Challenges has "Couldn't load challenges" + Retry.
- **The product currency cannot be chosen in the UI** (always EUR). The price hint shows the currency, but nothing lets you change it.
- **The tier spend condition is entered in cents** ("Lifetime purchase spend (cents)"), which invites mistakes by 100×.
- **The multiplier uses banker's rounding** (`round()`), and challenge points ignore the multiplier. Both need documenting or deciding.
- **Purchases earn no points.** That may be surprising for a loyalty product.
- **Challenge `cancelled` status** has a badge but no way to reach it. **`startsAt`** is stored but never enforced and has no field.
- **Expired challenges still look Active** on the definition card. Assignment then fails with "Challenge has expired".
- **Deactivating a challenge does not stop progress** on existing assignments. Lowering the target does not complete members who are already past it.
- **Out-of-stock rewards still show the "Active" badge.** A challenge prize that is inactive or out of stock is skipped silently on completion.
- **Challenge prize select lists inactive rewards** (`ChallengeFields.tsx:70-74`), and those will never be paid out.
- **"Assign members" has no Cancel button**, unlike every other dialog.
- **Reward/product/challenge names are not unique**, while segment and tier names are. This is inconsistent.
- **Tier list display order (rank ascending) is the opposite of evaluation order.**

---

## 9. Visual mock cheat-sheet

- Page background `--background #f8fafc`. Cards are white `--surface` with a `--line #e2e8f0` border. Text is `--foreground #0f172a`, `--muted #475569` and `--faint #64748b`. Primary is `#5b4bd6` (subtle `#efecfd`, subtle-fg `#4338ca`). Success `#0ca30c`, warning `#fab219`, danger `#d03b3b`. Accents: aqua `#1baf7a`, yellow `#eda100` - `client/app/globals.css:10-48`. The selected program can override the brand colours (`client/components/branding/ProgramTheme`).
- Icons are inline line SVGs (24 viewBox, stroke 1.75, `1em`) - `client/components/ui/icons.tsx:5-21`.
- Page: `space-y-6`, PageHeader on top, then either a card grid (Segments, Challenges, Tiers) or a single Card holding a table (Rewards, Products).
- Segment / Tier grids are 1 → 2 (`sm`) → 3 (`lg`) columns. The Challenge grid is 1 → 2 (`md`).
- Badges: `rounded-full px-2 py-0.5 text-xs font-medium` with tone backgrounds (neutral `bg-surface-2 text-muted`, primary `bg-primary-subtle`, success, warning, danger) - `client/components/ui/Badge.tsx:7-27`.
- Ghost icon buttons are `h-9 w-9 rounded-lg`. Small buttons are `h-8 px-3 text-[0.8125rem]` - `client/components/ui/Button.tsx:20-27`.
- Dropdown panel: `absolute right-0 mt-1 w-48 rounded-lg border bg-surface py-1 shadow-lg`. Items are `px-3 py-2 text-[0.8125rem]`, and Delete is `text-danger` - `client/components/ui/DropdownMenu.tsx:64-69,79-96`.
- Inputs: `rounded-lg border border-line px-3 py-2 text-sm`, focus ring primary/25. Selects have a chevron on the right. Checkboxes are 16px with accent primary - `client/components/ui/Field.tsx:10-111`.
