# Member app: research notes for end-user documentation

These notes come from reading the code at commit `ed66b7b`. Paths are relative to the repo root (`client/` is the Next.js 16.2 app and `api/` is the FastAPI backend). Labels are quoted exactly as they appear in the source. `?` marks an open question that could not be confirmed by reading the code.

Conventions used below:
- **FE**: a frontend check. **BE**: a backend check.
- Every API error reaches the member as the raw `detail` string from the API (`client/lib/api.ts:157`, `client/lib/api.ts:171-189`). Pydantic validation errors join their `msg` values with ", " (`client/lib/api.ts:176-184`).
- A generic fallback appears whenever a server action throws a non-API error: "Something went wrong. Please try again." (for example `client/lib/memberAuth/actions.ts:37`).
- If the API cannot be reached, members see "Cannot reach the API at <URL>. Make sure the server is running." (`client/lib/api.ts:132-135`). This shows an internal URL to end users.
- The API client retries up to 3 attempts (150 ms base backoff) on status 0, 502, 503 and 504. POST requests are retried too (`client/lib/api.ts:31-36`, `client/lib/api.ts:158-161`).

---

## 0. Global shell, theming and entry points

### Routes and gating
- Member routes that need a session: `/home`, `/products`, `/wallet`, `/account` (`client/proxy.ts:10`). Without a valid `member_session` cookie, the proxy redirects these to `/login` (`client/proxy.ts:58-60`). The member layout checks again and redirects to `/login` (`client/app/(member)/layout.tsx:17-18`).
- `/login` with a valid session redirects to `/home` (`client/proxy.ts:51-55`, `client/app/login/page.tsx:19`).
- `/verify` is always public (`client/proxy.ts:43-45`). `/p/<slug>/claim` is public because it is not in the protected set (`client/proxy.ts:22-23`).
- `/` is the "Welcome to Loyalty Engine" chooser with three tiles (the third, "Read the documentation", opens `/docs`). "Continue as admin" / "Manage members, rewards, and tiers" goes to `/admin/login`. "Continue as user" / "Track your points and rewards" goes to `/login`. Subtitle: "Choose how you'd like to continue" (`client/app/page.tsx:53-71`). Browser title: "Loyalty Engine" (`client/app/page.tsx:7-9`).
- Signing out redirects to `/`, the admin/user chooser, not to `/login` (`client/lib/memberAuth/actions.ts:101-104`).
- Root 404 page: "404", "We couldn't find the page you're looking for.", and a "Go home" button that goes to `/` (`client/app/not-found.tsx:9-22`).
- Root error page: "Something went wrong", then the error message or "An unexpected error occurred.", with buttons "Reload" and "Try again" (`client/app/error.tsx:20-30`). No `(member)/error.tsx` exists, so `client/app/error.tsx` is the nearest boundary. ? Probably a failing API call on a tab replaces the whole shell (header and tab bar included), which would leave no visible sign-out button. Not run.

### Browser tab titles
- Login: "Sign in - Loyalty App" (`client/app/login/page.tsx:13-15`)
- Home: "Home - Loyalty App" (`client/app/(member)/home/page.tsx:5`)
- Products: "Products - Loyalty App" (`client/app/(member)/products/page.tsx:15`)
- Wallet: "Wallet - Loyalty App" (`client/app/(member)/wallet/page.tsx:18`)
- Account: "Account - Loyalty App" (`client/app/(member)/account/page.tsx:17`)
- Verify: "Verify your email - Loyalty App", with noindex (`client/app/verify/page.tsx:12-16`)
- Claim: "Claim your prize - Loyalty App", with noindex (`client/app/p/[slug]/claim/page.tsx:17-21`)
- Default: "Loyalty App" (`client/app/layout.tsx:17-20`)

### Branding (applies to every member screen)
- The app takes the logo, name and colours of the member's current program. With no session, it uses the default program (`client/lib/server/branding.ts:40-45`, `client/app/(member)/layout.tsx:20-28`).
- The colours override the CSS tokens on `:root`, so dialogs and toasts are themed as well (`client/components/branding/ProgramTheme.tsx:4-21`).
- Without a logo, the app shows the stock `/logo.svg` (`client/components/branding/BrandLogo.tsx:25`). Without a reachable program list, the name falls back to "Loyalty App" (`client/components/layout/MemberShell.tsx:171`).
- Stock light tokens: background `#f8fafc`, surface `#fff`, foreground `#0f172a`, muted `#475569`, faint `#64748b`, line `#e2e8f0`, primary `#5b4bd6`, primary-subtle `#efecfd`, primary-subtle-fg `#4338ca`, secondary `#eb6834`. Success, warning, danger and accent colours are in the file. A dark scheme applies through `prefers-color-scheme` (`client/app/globals.css:11-88`). Font: Geist (`client/app/layout.tsx:5-13`).
- Root font size: inside the member shell (`data-app="member"`) it is fixed at 16px. On the public pages (login, verify, claim) it scales with `clamp(16px, 0.75vw + 6px, 24px)` (`client/app/globals.css:159-171`).

### Shell layout (MemberShell)
- Header (`client/components/layout/MemberShell.tsx:162-185`): sticky, `h-14`, `bg-surface`, `border-b border-line/70`, `px-4`. It has three slots:
  - Left: the program logo, `h-8 max-w-20`.
  - Centre: the program name, `text-lg font-semibold tracking-tight text-primary`, truncated.
  - Right: an icon-only sign-out button (LogOut icon, `h-9 w-9 rounded-full text-primary hover:bg-primary/10`) with `aria-label`/`title` "Sign out". It has no visible text and no confirmation.
- Content `<main>`: `relative mx-auto w-full max-w-lg flex-1 px-4 py-6` (`client/components/layout/MemberShell.tsx:187`).
- Bottom tab bar (`client/components/layout/MemberShell.tsx:194-242`): `bg-primary-subtle`, `border-t border-line/70`, inner row `h-[4.5rem] max-w-lg`, four equal tabs. Each tab has a `text-2xl` icon above an `text-xs` label.
  - Tabs in order: **Home** (house icon) → `/home`, **Products** (shopping bag) → `/products`, **Wallet** (wallet) → `/wallet`, **Account** (user) → `/account` (`client/components/layout/MemberShell.tsx:45-51`).
  - Active tab: `font-semibold text-primary`, the icon filled at 20% opacity, and a 3px `bg-primary` bar across the top of the tab (`inset-x-3 top-0 h-[3px] rounded-full`). Inactive tabs: `font-medium text-muted` (`client/components/layout/MemberShell.tsx:213-236`).
  - A tab is active only when the path matches exactly (`client/components/layout/MemberShell.tsx:197`).
  - All tabs prefetch in production (`client/components/layout/MemberShell.tsx:211`).
- **Mobile (<768px)**: full-screen layout. The document scrolls, the tab bar is `fixed` to the bottom with safe-area padding, and content gets `pb-[calc(4.5rem+env(safe-area-inset-bottom))]` (`client/components/layout/MemberShell.tsx:161`, `client/components/layout/MemberShell.tsx:194`).
- **Desktop (md ≥768px)**: the same one-column app is drawn inside a fake phone (`client/components/layout/MemberShell.tsx:119-247`).
  - Page `md:bg-surface-2 md:p-6`, centred.
  - Phone body 390×844 px, `md:rounded-[3rem] md:bg-neutral-800 md:shadow-xl`, scaled with `transform: scale(innerHeight*0.9/844)` to 90% of the viewport height (`client/components/layout/MemberShell.tsx:31`, `client/components/layout/MemberShell.tsx:99-111`, `client/components/layout/MemberShell.tsx:131-134`).
  - Screen inset 10px with `rounded-[2.4rem]`.
  - Two decorative side buttons on the right edge.
  - Punch-hole camera, 10px black dot.
  - Android status bar `h-7` showing the fixed time **"9:41"** plus signal, wifi and battery icons.
  - Gesture pill `w-28 h-1` at the bottom.
  - On desktop the tab bar is `absolute` with `md:pb-2.5`.
- Loading between tabs: an animated logo loader centred in the content area. The header and tab bar stay (`client/app/(member)/loading.tsx:18-24`).
- Toasts are portalled to `document.body` with `fixed inset-x-0 bottom-0 z-[60]`. They are centred on mobile and bottom-right from `sm` up. Each toast is `max-w-sm rounded-xl border bg-surface shadow-lg` with a tone icon and an "Dismiss" × button, and auto-hides after **4.5 s** (`client/components/ui/Toast.tsx:38-44`, `client/components/ui/Toast.tsx:59-66`, `client/components/ui/Toast.tsx:96-106`).
- Dialogs are also portalled to `body`: `fixed inset-0 z-50`, `bg-black/40` blurred backdrop, panel `rounded-2xl border bg-surface shadow-xl`. The header row has a title and a × button labelled "Close". Esc and a backdrop click both close the dialog (`client/components/ui/Dialog.tsx:45-103`).
- Both are portalled to `body`, so on desktop they render over the whole browser window, outside the phone frame. Toasts are at the bottom-right of the browser, not inside the phone.
- Shared page header used by Products, Wallet and Account: `h1` `text-2xl font-semibold tracking-tight` plus a `text-sm text-muted` description (`client/components/ui/PageHeader.tsx:11-18`). Home has no page header.
- Cards: `rounded-xl border border-line bg-surface shadow-sm` (`client/components/ui/Card.tsx:5-14`).

---

## 1. Sign in / sign up: `/login`

### How to reach
- Go to `/login` directly, choose "Continue as user" on `/`, or open any protected tab while signed out (`client/proxy.ts:58-60`).

### Layout
- Centred column on `bg-surface-2`, `max-w-sm`, `px-4 py-10` (`client/app/login/page.tsx:26-28`).
- Brand block: the logo at `h-12 max-w-40`, then the program name as `h1` (`text-lg font-semibold`), then the subtitle **"Log in or create an account to continue"** (`client/app/login/page.tsx:29-43`).
- White card `rounded-xl border p-6 shadow-sm` holding the form (`client/app/login/page.tsx:44-46`).
- Segmented control at the top of the card: `grid-cols-2 rounded-lg bg-surface-2 p-1`. Its two buttons are **"Log in"** (selected by default) and **"Sign up"**. The selected button is `bg-surface shadow-sm` (`client/app/login/AuthForm.tsx:82`, `client/app/login/AuthForm.tsx:125-144`).

### Step 1a: Log in (request a code)
- Field **"Email"**: `type=email`, required (HTML), autofocus, `autocomplete=email` (`client/app/login/AuthForm.tsx:49-58`).
- Button **"Send login code"**, full width, primary. It shows a spinner while pending (`client/app/login/AuthForm.tsx:65-67`, `client/components/ui/SubmitButton.tsx:8-14`).
- FE checks: the email is trimmed. If empty: "Enter your email address." (`client/lib/memberAuth/actions.ts:24-25`).
- BE: `email` is a Pydantic `EmailStr` (`api/app/schemas/auth.py:15-16`). An invalid address fails with a message starting "value is not a valid email address: …". ? The exact text comes from the email-validator library.
- BE: unknown email sends nothing and answers the same 200 as a sent code, "If this email has an account, a login code is on its way." (`api/app/routers/auth.py:19-22`, `api/app/services/member_auth.py:195-201`). A request inside the 60 s cooldown also sends nothing and answers 200 (`api/app/services/member_auth.py:122-128`).
- The lookup is an exact string match on the identity email (`api/app/services/member_auth.py:42-43`). ? EmailStr probably lowercases only the domain, so `John@x.com` and `john@x.com` would be different accounts.
- No program is sent. Signing in always lands in the default program (`client/lib/memberAuth/actions.ts:15-17`, `api/app/routers/auth.py:14-16`).

### Step 1b: Sign up (request a code)
- Fields, in this order (`client/app/login/AuthForm.tsx:44-63`):
  - **"Name"**: text, required, `autocomplete=name`.
  - **"Email"**: `type=email`, required, autofocus.
  - **"Phone"**: `type=tel`, shows the hint "Optional" at the right of the label, no validation.
- Button **"Create account"** (`client/app/login/AuthForm.tsx:66`).
- FE checks: if the name or email is empty: "Enter your name and email address." (`client/lib/memberAuth/actions.ts:45-50`). An empty phone is sent as undefined (`client/lib/memberAuth/actions.ts:55`).
- BE: an existing email mails that account a login code and creates nothing. Name and phone are ignored (`api/app/services/member_auth.py:176-184`).
- BE: the account is **created and committed before the code is emailed or verified**. The new person gets a membership in every program (`api/app/services/member_auth.py:156-163`).
- No length limits on name or phone, FE or BE (`api/app/schemas/auth.py:9-12`).

### Step 2: Enter the code
- After a successful send, the card switches to the code step (`client/app/login/AuthForm.tsx:31-34`, `client/app/login/AuthForm.tsx:149-152`).
- Text: in Log in mode **"If <email> has an account, we sent it a 6-digit code."**; in Sign up mode "We sent a 6-digit code to <email>." (`client/app/login/AuthForm.tsx:92-98`). The email is shown in `font-medium text-foreground` (`client/app/login/AuthForm.tsx:92-95`).
- Field **"Code"**: `inputMode=numeric`, `autocomplete=one-time-code`, `maxLength=6`, required, autofocus. There is no `pattern`, so letters are accepted (`client/app/login/AuthForm.tsx:96-106`).
- Button **"Continue"**, full width (`client/app/login/AuthForm.tsx:108`).
- Link-style button **"Use a different email"** (`text-[0.8125rem] text-muted`). It returns to step 1 with an **empty** form (`client/app/login/AuthForm.tsx:109-118`).
- **There is no "Resend code" button and no countdown.** To get a new code, the member uses "Use a different email" and submits the same address again.
- FE checks: an empty code gives "Enter the code from your email." (`client/lib/memberAuth/actions.ts:77-79`).
- BE results (`api/app/services/member_auth.py:179-204`):
  - Correct code: the member is signed in to the default program and redirected to `/home` (`client/lib/memberAuth/actions.ts:97-98`).
  - Wrong code: **"That code is invalid or has expired. Request a new one."** (400, `INVALID_CODE`, `api/app/services/member_auth.py:41`). Each wrong guess adds one attempt.
  - After **5** wrong guesses the code is burned (`MAX_ATTEMPTS = 5`, `api/app/services/member_auth.py:31`, `api/app/services/member_auth.py:190-195`). The next try gets the same message (`api/app/services/member_auth.py:209-211`).
  - Expired code, or an email with no account: the same message (`api/app/services/member_auth.py:205-211`).

### Code email
- Subject **"Your login code"**. Text version: "Your login code is NNNNNN. It expires in 10 minutes." (`api/app/services/member_auth.py:89-96`).
- HTML version: label "Your login code", a large monospaced code on a violet tint, then "Tap and hold the code above to select and copy it.", then "This code expires in 10 minutes. If you didn't request this, you can ignore this email." The card is 480px wide with a 4px primary stripe (`api/app/services/code_emails.py:35-93`).
- The code is 6 digits with leading zeros (`api/app/services/member_auth.py:46-47`).

### Limits and timeouts
- Code lifetime: **10 minutes** (`api/app/services/member_auth.py:30`).
- Attempts: **5 per code** (`api/app/services/member_auth.py:31`).
- Resend cooldown: **60 s** between code emails to the same person (`api/app/services/code_emails.py:19`). Inside the cooldown the API returns 429 **"A code was just sent. Please wait N seconds before requesting another."** with a `Retry-After` header (`api/app/services/code_emails.py:96-112`). The member sees it as a red banner on step 1.
- A code that was used to sign in does not count toward the cooldown. A code burned by 5 wrong guesses does count (`api/app/services/member_auth.py:70-86`). Signing in again right after signing out works immediately (`api/tests/regression/test_member_login_resend.py:155-161`).
- Each new code replaces the previous unused one, and only the newest code works (`api/app/services/member_auth.py:135-146`, `api/tests/regression/test_member_login_resend.py:135-146`).
- Email failures:
  - Transient failure: **"Could not send the login code. Please try again shortly."** (502) (`api/app/services/member_auth.py:127-130`).
  - Permanent failure: "Login code could not be sent - email delivery is misconfigured. <provider reason>" (500) (`api/app/services/member_auth.py:131-133`). This shows provider internals to members.
  - When the send fails, no code row is written and the old code stays valid (`api/app/services/member_auth.py:115-117`).
- Login codes are separate from email verification. Signing in never marks the email as verified (`api/app/services/member_auth.py:1-8`).

### Session and sign out
- The session is an HMAC-signed cookie `member_session` of the form `<memberId>.<programId>.<expiresAt>.<sig>` (`client/lib/memberAuth/config.ts:13`, `client/lib/memberAuth/token.ts:5-38`).
- Lifetime: **30 days**, fixed (not sliding) (`client/lib/memberAuth/config.ts:15-16`). Cookie flags: `httpOnly`, `sameSite=lax`, `secure` in production, `path=/` (`client/lib/memberAuth/session.ts:11-19`). Switching program issues a fresh 30-day cookie (`client/lib/member/programs.ts:36`).
- Older two-part tokens are rejected and force a single re-login (`client/lib/memberAuth/token.ts:51-55`).
- Sign out: the header icon button deletes the cookie and redirects to `/` (`client/components/layout/MemberShell.tsx:174-183`, `client/lib/memberAuth/actions.ts:101-104`, `client/lib/memberAuth/session.ts:23-26`). Tokens are stateless and nothing revokes them on the server.

---

## 2. Home: campaign launcher (`/home`)

### How to reach
- The **Home** tab. It is also where the member lands after signing in (`client/lib/memberAuth/actions.ts:98`).

### Layout
- There is no page title. The page holds one card `p-5` with a vertical stack `gap-3` (`client/components/campaigns/CampaignLauncher.tsx:24-42`):
  - Label **"Campaign URL"**.
  - A `type=url` input with placeholder **"https://example.com/campaign"**.
  - A full-width primary button **"Open campaign"** with a target icon.
- Until browser storage has been read after mount, the page renders **nothing**, so there is a brief blank content area (`client/components/campaigns/CampaignLauncher.tsx:20-22`, `client/components/campaigns/CampaignContext.tsx:81-86`).

### Actions
- Press **Enter** in the field or tap **"Open campaign"** (`client/components/campaigns/CampaignLauncher.tsx:33-39`).
- Validation, shown as error toasts (`client/components/campaigns/CampaignContext.tsx:109-122`):
  - Empty or whitespace: **"Enter a campaign URL."**
  - Not parseable by `new URL()`: **"Enter a valid campaign URL."** A URL without a scheme, such as `example.com/x`, fails this check.
- Accepted URLs: anything `new URL()` parses. There is no allow-list and no scheme check, so `http:`, `https:`, `data:` and others pass (`client/components/campaigns/CampaignContext.tsx:11-15`). ? React 19 blocks `javascript:` URLs in `src`.
- Automatic behaviour: the app adds `userId=<member id>` to the query string, overwriting any existing `userId` (`client/components/campaigns/CampaignContext.tsx:9-15`).
  - The member id is **different in each program**.
  - When the member switches program, the provider remounts because it is keyed by member id, and it reloads the campaign with the new id (`client/components/campaigns/CampaignContext.tsx:88-94`). ? Inferred from the key, not run.

### The campaign frame
- An iframe with title "Campaign" fills the content area edge to edge, between the header and the tab bar (`absolute inset-0 bg-background`) (`client/components/campaigns/CampaignFrame.tsx:39-52`).
- Two round icon buttons sit at the top-right (`right-3 top-3`, `h-9 w-9 rounded-full border bg-surface/90 shadow-sm backdrop-blur`). They have no visible text:
  - **Reload** (refresh icon), title "Reload campaign": restarts the campaign from scratch.
  - **Close** (× icon), title "Close campaign".
  (`client/components/campaigns/CampaignFrame.tsx:29-30`, `client/components/campaigns/CampaignFrame.tsx:53-71`)
- **Persists across tabs**: the frame lives in the shell. On other tabs it is hidden with `display:none` but **keeps running**, so audio and timers continue. Returning to Home shows it in the same state (`client/components/campaigns/CampaignFrame.tsx:10-18`, `client/components/campaigns/CampaignFrame.tsx:40-46`).
- **Persists across reloads and browser restarts**: `localStorage` key `loyaltyEngine.campaign` holds `{url, open}` (`client/lib/campaign-storage.ts:19-26`, `client/components/campaigns/CampaignContext.tsx:125`).
  - Only the typed URL is stored. `userId` is applied again on load (`client/lib/campaign-storage.ts:14-16`).
  - The key is the same for every member and is **not cleared on sign-out** (`client/lib/memberAuth/actions.ts:101-104`).
- Closing: the × button hides the frame, and the input comes back **pre-filled** with the same URL (`client/components/campaigns/CampaignContext.tsx:128-133`).
- If a stored URL no longer parses, it is dropped and the form shows (`client/components/campaigns/CampaignContext.tsx:40-46`).
- ? Sites that refuse framing (X-Frame-Options or CSP) show the browser's own error inside the frame, and the app cannot detect this. The iframe has no `allow` or `sandbox` attributes, so features like fullscreen or camera may be blocked. Not tested.

---

## 3. Products (`/products`)

### How to reach
- The **Products** tab.

### Layout (top to bottom, `space-y-6`)
1. Page header **"Products"** with the description **"Browse and buy with your card on file."** (`client/app/(member)/products/page.tsx:36`)
2. Two stat tiles side by side in `grid grid-cols-2 gap-4`, small size: card `p-4`, label `text-[0.8125rem] text-muted`, value `text-xl font-semibold`, sub-line `text-xs text-faint`, and an `h-8 w-8` icon chip at the top-right (`client/app/(member)/products/page.tsx:38-55`, `client/components/ui/StatTile.tsx:17-80`):
   - **"Spent (7d)"**: the amount spent in the last 7 days. Sub-line "N purchase" / "N purchases". Coins icon, yellow chip.
   - **"Total spent"**: lifetime spend. Sub-line "N purchase(s) all-time". Shopping-bag icon, aqua chip.
3. Segmented tabs (`flex gap-1 rounded-lg bg-surface-2 p-1`; selected tab `bg-surface shadow-sm`): **"Catalogue"** (the default) and **"Purchase history"** (`client/app/(member)/products/page.tsx:57-70`, `client/components/ui/Tabs.tsx:32-51`). The choice is not remembered and resets to Catalogue on every visit.

### Catalogue
- One card containing a `grid grid-cols-2 gap-3 p-4` of tiles. Each tile is `rounded-xl border bg-surface px-4 py-2.5` and shows (`client/components/products/ProductCatalog.tsx:19-23`, `client/components/products/ProductCard.tsx:25-50`):
  - The name, `text-xs font-medium`, wrapping.
  - The price, `text-sm font-semibold`.
  - A small **"Buy"** button (`xs`: `h-7 px-2 text-xs`) on the right.
- Only active products are shown, newest first, up to 1000 (`client/lib/api.ts:253-257`, `client/app/(member)/products/page.tsx:29`, `api/app/routers/products.py:38-41`).
- Prices use `Intl.NumberFormat("en-US", currency)`, for example "€14.50" (`client/lib/format.ts:28-33`).
- Tapping the tile anywhere except Buy opens a **dialog** (`size sm` = `max-w-sm`, vertically centred) (`client/components/products/ProductCard.tsx:52-80`). It contains:
  - The product name as the title.
  - The category as a grey pill, if set.
  - The description, if set.
  - The price (`text-lg font-semibold`) and a **"Buy"** button (`sm`).
- Empty state (shopping-bag icon): **"Nothing here yet"** / **"Products will show up here once they're added."** (`client/components/products/ProductCatalog.tsx:12-17`)

### Buying
- One tap buys **one** unit. There is no confirmation, no cart and no quantity picker (`client/components/products/BuyButton.tsx:11-14`, `client/lib/member/actions.ts:66-70`).
- **It costs money, not points.** No real payment happens and no balance is checked. The purchase is only recorded so spend can be tracked (`client/lib/member/actions.ts:51-58`, `api/app/routers/purchases.py:31-34`, `api/app/services/products.py:49-55`).
- No points are awarded directly. The member's tier is recalculated because tiers can depend on lifetime spend or count (`api/app/routers/purchases.py:35-38`, `api/app/services/rules/fields.py:21-26`).
- Success: toast **"Purchased for <price>."** The page refreshes so the stats and history update, and the dialog closes if it was open (`client/components/products/BuyButton.tsx:42-53`).
- Errors arrive as error toasts:
  - "Product is not available" for a product deactivated since the page loaded (`api/app/services/products.py:57-60`).
  - "Your session has expired. Please sign in again." (`client/lib/member/actions.ts:60-63`).
- The record keeps the product name and price as they were at purchase time (`api/app/services/products.py:63-80`).

### Purchase history
- One card with a divided list (`client/components/products/PurchaseHistory.tsx:20-36`). Each row is `px-5 py-4` and shows:
  - An aqua bag chip, `h-9 w-9`.
  - The product name, truncated.
  - The date and time, e.g. "Oct 23, 2026, 3:04 PM", in `text-xs text-faint` (`client/lib/format.ts:46-57`).
  - The total, right-aligned.
- Newest first, at most 200 rows, no paging (`client/lib/api.ts:261-265`, `api/app/routers/purchases.py:57-64`).
- Empty state: **"No purchases yet"** / **"Products you buy will show up here."** (`client/components/products/PurchaseHistory.tsx:14-18`)

### 7-day stats
- The window is a rolling 7 days ending now, not a calendar week (`client/app/(member)/products/page.tsx:20`, `api/app/services/products.py:99`).
- Currency comes from the member's first purchase found. With no purchases it is "EUR" (`api/app/services/products.py:115-122`). Mixed currencies are not handled.

---

## 4. Wallet (`/wallet`)

### How to reach
- The **Wallet** tab.

### Layout
- Page header **"Wallet"** with the description **"Your points and the prizes you've won."** (`client/app/(member)/wallet/page.tsx:38`)
- Stat tile **"Points balance"**, medium size: `p-5`, value `text-3xl`, `h-10 w-10` yellow coins chip (`client/app/(member)/wallet/page.tsx:40-45`).
  - Values of 10,000 or more are shortened, e.g. "12.9K" or "4.2M" (`client/lib/format.ts:12-18`).
  - The balance is for the current program only (`api/app/routers/points.py:33-40`).
- Card with header **"Prizes"** and the description **"Prizes you've won. Claim them here or from your email."** (`client/app/(member)/wallet/page.tsx:47-51`).
  - Divided list. Each row has an orange gift chip `h-9 w-9`, the reward name (truncated), the date it was assigned (`text-xs text-faint`), and at the right either:
    - A green **"Claimed"** badge, or
    - A small primary **"Claim"** button.
  (`client/app/(member)/wallet/page.tsx:59-83`)
  - Empty state (wallet icon): **"Nothing here yet"** / **"Prizes you win will show up here."** (`client/app/(member)/wallet/page.tsx:52-57`)
- Only **assigned** prizes are listed (granted by campaigns or admins), newest first, up to 200. Rewards the member bought with points are **not** shown (`client/app/(member)/wallet/page.tsx:29-32`, `api/app/routers/redemptions.py:109-130`).

### Claiming
- **"Claim"**: success toast **"Prize claimed."** (`client/lib/member/actions.ts:86-104`, `client/components/ui/ActionButton.tsx:30-39`).
  - Claiming twice changes nothing (`api/app/services/prize_claims.py:184-196`).
  - Claiming in the wallet works even after the email link has expired, because there is no expiry check here (`api/app/routers/redemptions.py:88-106`).
  - Errors: "Prize not found" (404) and "Your session has expired. Please sign in again."
- ? After a claim, the action calls `revalidatePath("/wallet")` without `router.refresh()`. The BuyButton comment says this alone does not re-render the page that is open (`client/components/products/BuyButton.tsx:15-21`). If that is true, the row may keep showing "Claim" until the member navigates away and back.

### Redeeming rewards with points
- **Not possible in the member app.** There is no rewards catalogue or redeem button. The API has `POST /members/{id}/redeem/{rewardId}` ("Insufficient points: has X, needs Y") (`api/app/routers/redemptions.py:19-55`), but the client never calls it from member screens.
- No points history or transaction list is shown.

### Auto refresh
- **There is no timer or polling interval.** The page refreshes (`client/components/wallet/BalanceAutoRefresh.tsx:27-58`):
  - Once each time the member arrives on the Wallet tab.
  - Whenever the browser tab becomes visible or the window gets focus, at most once per 1 s.
- Client router cache: dynamic pages are cached for 30 s (`client/next.config.ts`, `staleTimes.dynamic: 30`). The refresh on arrival skips this cache.

---

## 5. Account (`/account`)

### How to reach
- The **Account** tab.

### Layout (`space-y-6`)
1. Page header **"Account"** with the description **"Your profile and program."** (`client/app/(member)/account/page.tsx:54`)
2. **Tier banner**, shown only if the member has a tier (`client/app/(member)/account/page.tsx:56-58`).
   - Styling: `rounded-2xl p-5`, gradient `from-primary via-primary to-secondary`, white text, a blurred white highlight in the corner (`client/components/account/TierBadge.tsx:16-22`).
   - Contents: an award icon in a `h-12 w-12 rounded-full bg-white/20` circle, the small uppercase label **"Your tier"** (shown as "YOUR TIER"), and the tier name at `text-xl` (`client/components/account/TierBadge.tsx:24-33`).
   - A pill **"<multiplier>x points"** appears only when the multiplier is above 1, e.g. "1.5x points" (`client/components/account/TierBadge.tsx:34-38`).
   - There is no progress toward the next tier.
3. **Profile card** (`client/app/(member)/account/page.tsx:60-108`):
   - Top row `px-4 py-3`:
     - An avatar circle with initials, tinted from the name (`client/components/ui/Avatar.tsx:12-35`).
     - The name, `text-sm font-semibold`.
     - The email, `text-[0.8125rem] text-muted`. Next to it is a small icon: a green check when verified, an amber info icon when not. The only text for this state is the screen-reader text "Email verified" / "Email not verified" (`client/app/(member)/account/page.tsx:77-91`).
     - Two square icon buttons on the right (`secondary`, `h-9 w-9`): **Copy** (title "Copy member ID") and **Pencil** (title "Edit profile").
   - Details list under a border: the row **"Phone"** shows the number or a faint **"Not set"** (`client/app/(member)/account/page.tsx:103-107`). An empty-string phone also counts as "Not set" (`client/app/(member)/account/page.tsx:48-50`).
   - The member id itself is never shown (`client/app/(member)/account/page.tsx:93-96`).
4. **Program switcher card** (`client/components/account/ProgramSwitcher.tsx:58-134`). It is shown only when 2 or more programs exist (`client/components/account/ProgramSwitcher.tsx:42`).
   - Contents: `p-4`, the uppercase label **"Switch Loyalty Program"** (`text-xs text-faint`), then a full-width dropdown trigger. The trigger shows the program mark (logo on white, or initials), the program name or "Choose a program", and a chevron or spinner.
   - The menu **opens upward**. The current program has a tinted background and a check mark (`client/components/account/ProgramSwitcher.tsx:64-127`).

### Copy member ID
- Copies the member id (a UUID for **this program's** membership) to the clipboard (`client/components/account/CopyIdButton.tsx:12-19`).
  - Success toast: **"User ID copied."**
  - Failure toast: **"Couldn't copy user ID."**
  - The toast says "User ID" while the button title says "member ID".

### Edit profile (dialog)
- The pencil opens a dialog (`size sm`, centred) titled **"Edit profile"** with the description **"Update your name, email address and phone number."** (`client/components/account/EditProfileButton.tsx:23-41`).
- Fields, pre-filled with current values (`client/components/account/EditProfileButton.tsx:43-74`):
  - **"Name"**: text, required.
  - **"Email"**: `type=email`, required. Help text below: **"Your sign-in code is sent to this address."**
  - **"Phone"**: `type=tel`, hint "Optional".
- Buttons: **"Cancel"** (secondary) and **"Save changes"** (primary), right-aligned (`client/components/ui/FormDialog.tsx:104-109`).
- FE checks: **"Enter your name."** and **"Enter your email address."** (`client/lib/member/actions.ts:29-30`). An empty phone is sent as "" so the number is cleared (`client/lib/member/actions.ts:35-38`).
- BE checks:
  - The email must be a valid `EmailStr` (`api/app/schemas/member.py:20-23`).
  - An email already used by someone else gives **"Email already registered"** (400) (`api/app/services/members.py:63-72`).
- Success: toast **"Profile updated."**, the dialog closes and the page refreshes (`client/lib/member/actions.ts:47-48`, `client/components/ui/FormDialog.tsx:90-98`). Errors appear as a red banner inside the dialog.
- Name, email and phone belong to the person, so a change applies in **every program** (`api/app/services/members.py:25`, `api/app/services/members.py:76-77`).
- Changing the email **does not reset the verified status**. The new address keeps the green check (`api/app/services/members.py:73-81`).
- The new email is used for sign-in codes straight away, without any confirmation step.

### Switching program
- Choosing another program (`client/components/account/ProgramSwitcher.tsx:46-56`, `client/lib/member/programs.ts:19-45`):
  - The trigger shows a spinner.
  - The API returns the member's membership in that program, creating it at zero if missing (`api/app/routers/members.py:170-193`).
  - The session cookie is re-issued with the new member and program id.
  - The whole app re-renders with the new program's logo, name, colours, points, tier, products and prizes.
  - Toast: **"Switched program."**
- Choosing the current program does nothing (`client/components/account/ProgramSwitcher.tsx:49`).
- Errors appear in a red banner under the dropdown: e.g. "Program not found", "You are not signed in.", "No program selected.", or the fallback "Could not switch program." (`client/components/account/ProgramSwitcher.tsx:54`, `client/lib/member/programs.ts:21-22`).
- If the program list fails to load, the switcher is hidden without a message (`client/app/(member)/account/page.tsx:43-47`).
- Every member belongs to every program, so all programs are offered (`api/app/services/memberships.py:1-23`, `api/app/routers/members.py:144-167`).

---

## 6. Email verification landing page (`/verify`)

### What it is and how to reach
- The page that the **"Verify my email"** link in a verification email opens. URL: `/verify?memberId=<id>&code=<code>` (`api/app/services/email_verification.py:146-161`).
- No session is needed (`client/proxy.ts:43-45`).
- **It only handles the link type. There is no field for typing a 6-digit code.** The code type of email is typed back "into whatever screen triggered the flow", meaning a campaign, not this app (`api/app/models/enums.py:38-50`). The member app has no button to request verification (`client/lib/doi/actions.ts:1-41` is the only DOI call).

### Layout
- Same centred `max-w-sm` layout as login. Logo, then `h1` **"Verify your email"**, then the subtitle **"One tap and you're done"**, then a white card (`client/app/verify/page.tsx:47-72`).
- Branding is the default program, or the current program if the member is signed in (`client/app/verify/page.tsx:41-44`).

### States and messages
- Link missing `memberId` or `code`: red banner **"This verification link is incomplete. Open the link from your email again, or request a new one."** (`client/app/verify/page.tsx:66-70`). Only the first value of a repeated query parameter is used (`client/app/verify/page.tsx:18-21`).
- Ready state: **"Press the button below to confirm this email address."** and a full-width button **"Verify my email"** (`client/app/verify/VerifyForm.tsx:38-47`). The id and code are sent as hidden fields.
- Success: a green check icon, **"Your email address is verified."**, and **"You can close this page."** (`client/app/verify/VerifyForm.tsx:26-35`, `client/lib/doi/actions.ts:35`). Verification is recorded on the person, so it counts in every program (`api/app/services/email_verification.py:277-279`).
- Errors (red banner above the button; the button stays):
  - "Invalid verification code". Each wrong try uses one of **5** attempts (`api/app/services/email_verification.py:40`, `api/app/services/email_verification.py:269-274`).
  - "Verification code has expired" (`api/app/services/email_verification.py:266-267`).
  - "No active verification code for this member" (`api/app/services/email_verification.py:264-265`).
  - "Member not found" (`api/app/services/email_verification.py:70-72`).
  - A `memberId` that is not a UUID gives the raw Pydantic message, e.g. "Input should be a valid UUID, …" (`api/app/schemas/email_verification.py:23-26`).
  - "This verification link is incomplete." (`client/lib/doi/actions.ts:25-27`).
- An already-verified person sees **success whatever the code is** (`api/app/services/email_verification.py:258-261`).

### Limits
- The link and code expire after **10 minutes** (`api/app/services/email_verification.py:39`). The email says "This link expires in 10 minutes." (`api/app/services/code_emails.py:67-71`).
- Re-sends follow the same **60 s** cooldown (`api/app/services/email_verification.py:213`). A new email replaces the old code, so older links stop working (`api/app/services/email_verification.py:241-246`, `api/tests/regression/test_doi_link_flow.py:1-15`).

### Email contents
- Subject **"Confirm your email address"**.
- Body: "Confirm your email address", a **"Verify my email"** button, "Or paste this address into your browser:" followed by the raw link, and the expiry note (`api/app/services/email_verification.py:119-143`, `api/app/services/email_verification.py:166-176`).

---

## 7. Prize claim page (`/p/<slug>/claim`)

### What it is and how to reach
- The landing page for the **"Claim your prize"** button in a prize email. URL: `/p/<programSlug>/claim?token=<token>` (`api/app/services/prize_claims.py:78-90`).
- No session is needed (`client/proxy.ts:22-23`).
- The email is sent only when a prize is assigned with `sendEmail: true` (`api/app/routers/redemptions.py:58-85`).
- The token is random (`token_urlsafe(32)`) and valid for **30 days** (`api/app/services/prize_claims.py:40`, `api/app/services/prize_claims.py:61-70`).
- If the slug in the URL does not match the prize's real program, the page redirects to the correct slug (`client/app/p/[slug]/claim/page.tsx:61-63`).

### Layout
- Same centred `max-w-sm` layout. The logo is the prize's program logo, falling back to the slug's program or the default (`client/app/p/[slug]/claim/page.tsx:65-68`).
- Heading: **"Congratulations, <member name>!"** for a valid token, otherwise **"Claim your prize"**. The program name appears below it as a subtitle (`client/app/p/[slug]/claim/page.tsx:80-85`).
- With a valid token the card shows (`client/app/p/[slug]/claim/page.tsx:88-116`):
  - A gift icon in a `h-12 w-12 rounded-xl bg-primary-subtle` tile.
  - The reward name (`text-base font-semibold`) and its description, if any.
  - Below that, one of three states.

### States and messages
- **Unclaimed, link valid**: a full-width button **"Claim my prize"** (`client/app/p/[slug]/claim/ClaimForm.tsx:30-36`).
  - Success: a green check, **"Your prize is claimed."**, and **"You can close this page."** (`client/app/p/[slug]/claim/ClaimForm.tsx:18-28`, `client/lib/prizes/actions.ts:28`).
- **Already claimed**: a green check and **"You claimed this prize on <Mon D, YYYY>."** (`client/app/p/[slug]/claim/page.tsx:99-105`, `client/lib/format.ts:35-44`).
- **Link expired, not claimed**: red banner **"This link has expired, but your prize is still waiting in your wallet."** and a link **"Sign in to claim it"** to `/login` (`client/app/p/[slug]/claim/page.tsx:106-112`).
  - If the press itself happens after expiry, the API answers: "This prize link has expired. Sign in to claim the prize from your wallet." (`api/app/services/prize_claims.py:199-205`).
- **Invalid or unknown token**: red banner **"This prize link is not valid."** (`api/app/services/prize_claims.py:168-176`, `client/app/p/[slug]/claim/page.tsx:117-119`).
- **No token**: **"This prize link is incomplete. Open the link from your email again."** (`client/app/p/[slug]/claim/page.tsx:29-31`). If the token disappears at press time: "This prize link is incomplete." (`client/lib/prizes/actions.ts:20`).
- Claiming twice is harmless (`api/app/services/prize_claims.py:184-196`).

### Email contents
- Subject **"You've won <reward>!"**.
- Body: the program logo, "Congratulations, <name>! You've won", the reward name and description, a **"Claim your prize"** button in the program colour, the raw link, and "This link expires in 30 days. You can also claim the prize from your wallet in <program>." (`api/app/services/prize_claims.py:93-131`, `api/app/services/prize_claims.py:134-151`).

---

## Contradictions found

1. **Products page copy vs behaviour**: "Browse and buy with your card on file." (`client/app/(member)/products/page.tsx:36`) suggests a stored card. No card exists and no payment happens (`client/lib/member/actions.ts:54-56`).
2. **Catalogue layout comments disagree.** ProductCatalog says "two per row" (`client/components/products/ProductCatalog.tsx:7`, matching `grid-cols-2` at `client/components/products/ProductCatalog.tsx:19`). ProductCard says "one product per row" (`client/components/products/ProductCard.tsx:35-36`). The code produces two per row.
3. **Price format comment** says `"14.50 EUR"` (`client/lib/format.ts:25`). The en-US currency formatter actually produces "€14.50" (`client/lib/format.ts:29-32`).
4. **"User ID" vs "member ID"**: the toasts say "User ID copied." / "Couldn't copy user ID." while the button title says "Copy member ID" (`client/components/account/CopyIdButton.tsx:15-31`).
5. **"Create account" creates the account before the code is verified** (`api/app/services/member_auth.py:156-163`). The UI suggests the account exists only after "Continue".
6. **The Wallet refresh comment contradicts itself.** It says `router.refresh()` remounts MemberShell and tears down the campaign iframe, yet it calls `router.refresh()` every time Wallet opens (`client/components/wallet/BalanceAutoRefresh.tsx:15-25`). ? Next.js documents that refresh keeps client state, so the iframe probably survives. Not verified.
7. **Unused PointsCard.** `client/components/wallet/PointsCard.tsx` describes a gradient "Points balance" banner at the top of Wallet, but Wallet uses a plain StatTile (`client/app/(member)/wallet/page.tsx:40-45`). PointsCard is imported nowhere and uses undefined tokens `brand-card-end` / `brand-card-fg`.
8. **The task brief expects `/verify` to support a link or a 6-digit code.** The page supports only the link. Codes are typed in campaigns (`api/app/models/enums.py:38-50`).
9. **proxy.ts says "Failed-login lockout is handled in the login Server Action"** (`client/proxy.ts:26`). Member login has no lockout beyond 5 attempts per code. This probably refers to the admin login.

## Could not confirm (`?`)

- The exact Pydantic message for an invalid email, and whether the local part of an email is case-sensitive when looking up an account.
- Whether a Wallet "Claim" re-renders the row to "Claimed" straight away.
- Whether an API error on a tab replaces the whole shell, including the tab bar and sign-out button, because only the root `client/app/error.tsx` exists.
- Behaviour inside the iframe for sites that refuse framing, and permissions such as fullscreen, camera or autoplay.
- Whether the campaign reloads with the new `userId` after a program switch (inferred from `key={memberId}`).
- Whether `javascript:` campaign URLs are blocked (React 19 should block them).
- Whether automatic retries on 502/503/504 (`client/lib/api.ts:36`) could ever record a purchase twice after a gateway timeout.

## For the product team: bugs and rough edges

1. **No "Resend code" on the code step.** There is also no on-screen mention of the 10-minute expiry or the 60 s cooldown. To resend, the member must use "Use a different email" and retype the address (`client/app/login/AuthForm.tsx:88-120`).
2. **A stale error banner survives "Use a different email".** `verifyState` lives in `AuthForm` and is never reset, so the next code step shows the previous "That code is invalid or has expired. Request a new one." error (`client/app/login/AuthForm.tsx:86`, `client/app/login/AuthForm.tsx:107-114`).
3. **Members see raw technical messages**:
   - The same invalid-code message is shown after 5 wrong codes, with only a generic hint to request a new code.
   - Pydantic validation text.
   - "Cannot reach the API at <URL>…".
   - Provider reasons in the "email delivery is misconfigured" errors (`api/app/services/member_auth.py:131-133`).
4. **Sign-up creates the account first.** If the code email fails, retrying gives "An account with this email already exists. Log in instead." Typo addresses create orphan people enrolled in every program (`api/app/services/member_auth.py:149-163`).
5. **The code field accepts non-digits** (no `pattern`), and each wrong value uses one of the 5 attempts (`client/app/login/AuthForm.tsx:97-105`).
6. **Sign-out lands on the admin/user chooser** at `/`, which shows members "Continue as admin". There is also no sign-out confirmation (`client/lib/memberAuth/actions.ts:103`, `client/app/page.tsx:60-71`).
7. **Sessions cannot be revoked.** The 30-day stateless token stays valid if copied, and deleting a member does not end their session. The pages then fail with "Member not found".
8. **Changing the email keeps the verified status and takes effect at once.** A typo locks the member out of sign-in (`api/app/services/members.py:63-81`).
9. **Profile edits apply in all programs**, and the dialog does not say so.
10. **The email-not-verified icon is tiny, has no visible label and offers no action.** The app has no way to request verification.
11. **The campaign URL has no allow-list.** Any parseable URL loads with the member id attached as `userId`, which could send member ids to arbitrary sites (`client/components/campaigns/CampaignContext.tsx:11-15`, `client/components/campaigns/CampaignContext.tsx:109-126`).
12. **Campaign storage is shared across members** on a device and is not cleared on sign-out (`client/lib/campaign-storage.ts:19`).
13. **A hidden campaign keeps running**, including sound, while the member is on other tabs (`client/components/campaigns/CampaignFrame.tsx:40-46`).
14. **Home is blank for a moment on load** until storage has been read (`client/components/campaigns/CampaignLauncher.tsx:22`).
15. **Buy has no confirmation.** One tap records a purchase, and there is no undo or refund in the member app (`client/components/products/BuyButton.tsx:42-59`).
16. **Wallet gaps**: no way to redeem rewards for points, rewards bought with points are not listed, and there is no points history.
17. **The balance only refreshes on arrival or focus.** It does not update while the member is on the page (`client/components/wallet/BalanceAutoRefresh.tsx:32-58`).
18. **Large balances are rounded**: 12,945 shows as "12.9K" (`client/lib/format.ts:12-18`).
19. **The expired prize link sends the member to `/login`, which always lands in the default program.** If the prize belongs to another program, the member must find it with the Account program switcher, and nothing tells them so (`client/app/p/[slug]/claim/page.tsx:109-111`, `api/app/services/member_auth.py:197-201`).
20. **Desktop phone frame**: dialogs and toasts open outside the phone, over the whole browser, and the status bar shows a fake fixed time "9:41" (`client/components/ui/Dialog.tsx:61-102`, `client/components/ui/Toast.tsx:59-66`, `client/components/layout/MemberShell.tsx:153`).
21. **On mobile, toasts cover the bottom tab bar** (`z-[60]` above `z-30`, both at the bottom) (`client/components/ui/Toast.tsx:61`, `client/components/layout/MemberShell.tsx:194`).
22. **Lists stop at 200 items** for purchase history and prizes, with no paging (`client/lib/api.ts:224-232`, `client/lib/api.ts:261-265`).
23. **Stats currency** falls back to EUR and assumes a single currency (`api/app/services/products.py:115-122`).
24. **The tier banner disappears entirely when the member has no tier**, and there is no progress toward the next tier (`client/app/(member)/account/page.tsx:56-58`).
25. **The verify page returns success for any code once the person is already verified**, which is harmless but surprising (`api/app/services/email_verification.py:260-261`).
