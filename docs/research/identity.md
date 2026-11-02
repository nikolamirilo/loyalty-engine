# Loyalty Simulator visual identity (for HTML mocks)

Read from code only. The stack is Tailwind CSS v4 (`client/package.json:19`, `:25`), Next 16.2.10 and React 19.2.4 (`client/package.json:12-13`). All tokens are plain **hex**. There are no oklch values in `globals.css`.

## 1. Colour tokens (`client/app/globals.css`)

Tokens are CSS variables on `:root` (`globals.css:11-49`). They are mapped to Tailwind utilities through `@theme inline` (`globals.css:90-128`), so `bg-surface`, `text-muted`, `border-line`, `bg-primary-subtle` and so on resolve to the values below.

| Token | Light | Dark | Used for |
|---|---|---|---|
| `--background` | **#f8fafc** (slate-50) | #0b1020 | page plane (`body`, `globals.css:174-176`) |
| `--surface` | **#ffffff** | #131a2c | cards, sidebar, dialogs, inputs |
| `--surface-2` | **#f1f5f9** (slate-100) | #1c2438 | hover, tab track, login/landing background |
| `--foreground` | **#0f172a** (slate-900) | #f1f5f9 | primary text |
| `--muted` | **#475569** (slate-600) | #b6c2d6 | secondary text, inactive nav |
| `--faint` | **#64748b** (slate-500) | #8493ab | labels, help text, placeholders |
| `--line` | **#e2e8f0** (slate-200) | #263048 | hairline borders (also the default `*` border colour, `globals.css:130-132`) |
| `--ring` | **#5b4bd6** | #8b7ef0 | focus outline |
| `--primary` | **#5b4bd6** (indigo-violet) | #8b7ef0 | primary buttons, links, check marks |
| `--primary-hover` | **#4c3fbf** | #a99ef4 | primary button hover |
| `--primary-fg` | **#ffffff** | #0b1020 | text on primary |
| `--primary-subtle` | **#efecfd** | #23204a | active nav item, "Default" pill, icon chips |
| `--primary-subtle-fg` | **#4338ca** | #c3bafa | text on primary-subtle |
| `--secondary` | **#eb6834** | #d95926 | member tier-card accent |
| `--success` | **#0ca30c** | #0ca30c | success fill and icons |
| `--success-fg` | **#056b05** | #46c246 | success text on subtle |
| `--success-subtle` | **#e5f4e5** | #12341a | success badge background |
| `--warning` | **#fab219** | #fab219 | |
| `--warning-fg` | **#8a5300** | #f0b429 | |
| `--warning-subtle` | **#fbf0d6** | #3a2e0f | |
| `--danger` | **#d03b3b** | #e66767 | danger button, error icon |
| `--danger-fg` | **#b0241d** | #f08a8a | error banner text |
| `--danger-subtle` | **#fbe7e7** | #3a1c1c | error banner and chip background |
| `--accent-blue` | **#2a78d6** | #3987e5 | stat tiles and avatars |
| `--accent-aqua` | **#1baf7a** | #199e70 | |
| `--accent-violet` | **#5b4bd6** | #8b7ef0 | |
| `--accent-orange` | **#eb6834** | #d95926 | |
| `--accent-yellow` | **#eda100** | #c98500 | |

- Dark mode follows the operating system only, through `@media (prefers-color-scheme: dark)` (`globals.css:51-88`). The app has no theme toggle and no `data-theme` attribute. `html { color-scheme: light dark }` (`globals.css:134-136`).
- A program's brand colour overrides the `--primary*`, `--ring` and `--secondary` tokens at runtime (`client/lib/theme.ts:75-139`). See `programs-shell.md` §5.
- Stock primary constant: `STOCK_PRIMARY = "#5b4bd6"` (`client/lib/theme.ts:22`).
- Logo gradient: `#6d5ef0` → `#4c3fbf` (`client/public/logo.svg:3-6`).

## 2. Typography

- Fonts: **Geist** (sans) and **Geist Mono**, loaded with `next/font/google` (`client/app/layout.tsx:2`, `:7-15`).
  - They are exposed as the CSS variables `--font-geist-sans` and `--font-geist-mono` on `<html>` (`layout.tsx:30-33`).
  - `@theme` maps them to `--font-sans` and `--font-mono` (`globals.css:126-127`), and `<body>` uses `font-sans` (`layout.tsx:34`).
  - In a mock: `font-family: "Geist", system-ui, sans-serif`. Both families are on Google Fonts.
- `html` has the `antialiased` class, and body sets `text-rendering: optimizeLegibility` (`layout.tsx:32`, `globals.css:177-178`).
- **Fluid root size**: `html { font-size: clamp(16px, 0.75vw + 6px, 24px) }` (`globals.css:159-161`). It is 16px up to 1280px wide, 18px at 1600px, about 20.4px at 1920px, and capped at 24px. All rem sizes scale with it. The member app pins it to 16px (`globals.css:170-172`).
- Type scale in use:
  - Page title: `text-2xl font-semibold tracking-tight` (`client/components/ui/PageHeader.tsx:13`).
  - Dialog title: `text-base font-semibold` (`Dialog.tsx:85`).
  - Card title: `text-sm font-semibold` (`Card.tsx:36`).
  - Body and nav text: `text-sm`. Small text: `text-[0.8125rem]` (13px), used for labels, dialog descriptions and toasts. Meta text: `text-xs`.
  - Brand wordmark: `text-[0.9375rem] font-semibold tracking-tight` (`AppShell.tsx:65`).

## 3. Radius, shadow, focus, motion

| Element | Radius | Shadow |
|---|---|---|
| Buttons (sm/md/icon), inputs, nav items, error banner, tab track | `rounded-lg` (0.5rem) | primary/danger/success buttons `shadow-sm` |
| xs button, tab pill, switcher trigger | `rounded-md` (0.375rem) | tab pill `shadow-sm` |
| Card, login card, landing tiles, toast | `rounded-xl` (0.75rem) | Card `shadow-sm`. Toast `shadow-lg` |
| Dialog panel | `rounded-2xl` (1rem) | `shadow-xl` |
| Dropdown panel | `rounded-lg` | `shadow-lg` |
| Mobile drawer | none | `shadow-xl` |
| Badges, avatars, program marks, progress bar | `rounded-full` | none |
| Logo tile | `rx=11` on a 40×40 viewBox (about 27%) | `shadow-sm` where used as an `<img>` |

- These radius and shadow names are Tailwind v4 defaults. No custom radius or shadow tokens are defined in `globals.css`.
- Focus: `outline: 2px solid var(--ring); outline-offset: 2px; border-radius: 6px` on links, buttons and inputs when focused with the keyboard (`globals.css:182-186`). Inputs use `focus:border-primary focus:ring-2 focus:ring-primary/25` instead (`Field.tsx:10-13`).
- Overlays: `bg-black/40`. Dialogs add `backdrop-blur-[2px]` (`Dialog.tsx:69`, `AppShell.tsx:163`).
- Motion: `fade-in` takes 0.15s. `dialog-in` takes 0.16s: translateY 6px→0 and scale 0.98→1 (`globals.css:194-220`). The logo loader floats, flips, glints and flutters on a 2.4s loop and respects reduced-motion (`globals.css:222-349`).
- Scrollbars are thin, `scrollbar-color: var(--line) transparent` (`globals.css:189-192`).

## 4. Logo

`client/public/logo.svg` is 1,465 bytes. `client/app/icon.svg` (the favicon) is byte-identical. The mark is a medal on an indigo-violet rounded tile:

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40" fill="none">
  <defs>
    <linearGradient id="logo-bg" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#6d5ef0" />
      <stop offset="1" stop-color="#4c3fbf" />
    </linearGradient>
    <linearGradient id="logo-hl" x1="0" y1="0" x2="0" y2="40" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#ffffff" stop-opacity="0.20" />
      <stop offset="0.55" stop-color="#ffffff" stop-opacity="0" />
    </linearGradient>
  </defs>

  <!-- Tile: indigo-violet plane, soft top highlight, hairline inner edge -->
  <rect width="40" height="40" rx="11" fill="url(#logo-bg)" />
  <rect width="40" height="40" rx="11" fill="url(#logo-hl)" />
  <rect x="0.7" y="0.7" width="38.6" height="38.6" rx="10.3" fill="none" stroke="#ffffff" stroke-opacity="0.14" stroke-width="1.2" />

  <!-- Mark: a medal - the reward for loyalty. Ribbon tails tuck behind the medallion;
       the star is a cutout showing the tile gradient through, like enamel on a medal face. -->
  <path d="M15.5,14 L19,14 L19,33 L17.25,30.5 L15.5,33 Z" fill="#ffffff" />
  <path d="M21,14 L24.5,14 L24.5,33 L22.75,30.5 L21,33 Z" fill="#ffffff" />
  <circle cx="20" cy="16.5" r="8.3" fill="#ffffff" />
  <path d="M20,11.5 L21.411,14.558 L24.755,14.955 L22.283,17.242 L22.939,20.545 L20,18.9 L17.061,20.545 L17.717,17.242 L15.245,14.955 L18.589,14.558 Z" fill="url(#logo-bg)" />
</svg>
```

- Sizes in use:
  - Login and landing: 48px (`h-12 w-12 shadow-sm`) (`client/app/admin/login/page.tsx:22-29`).
  - Sidebar brand: `h-9` (36px) followed by the text "Loyalty Simulator" (`client/components/layout/AppShell.tsx:60-67`).
  - Loader: `h-16` (`LogoLoader.tsx:41`).
- **Unused second logo**: `client/components/ui/Logo.tsx` draws a different, *blue* mark (gradient `#3987e5`→`#1c5cab`, an infinity loop with a sparkle) (`Logo.tsx:13-32`). No file imports it. Do not use it in mocks.

## 5. Icons (`client/components/ui/icons.tsx`)

- **Custom inline SVGs, not the Lucide package.** No icon library is in `package.json`.
- They are drawn in the Lucide/Feather style: a 24×24 viewBox, `stroke="currentColor"`, **strokeWidth 1.75** (Lucide's default is 2), round caps and joins, and a size of `1em × 1em`. Icon size is therefore set with font-size classes such as `text-lg` (`icons.tsx:5-23`).
- Several icons copy Lucide/Feather paths exactly. Others are redrawn, for example with circles of radius 9 where Lucide uses 10.
- In the table, "exact" means the path data matches the Lucide/Feather icon as far as known. "Close" means the same idea with altered geometry.

| Export | Nearest Lucide icon | Match |
|---|---|---|
| DashboardIcon | `layout-dashboard` | close (rx 1.5) |
| SlidersIcon | `sliders-horizontal` | close/custom |
| LogOutIcon | `log-out` | exact (Feather) |
| UsersIcon | `users` | exact (Feather) |
| GiftIcon | `gift` | close |
| TargetIcon | `target` | close (r 9/5/1.5) |
| LayersIcon | `layers` | close |
| PlusIcon | `plus` | exact |
| MinusIcon | `minus` | exact |
| SearchIcon | `search` | close (r 7) |
| TrashIcon | `trash-2` | close |
| PencilIcon | `pen-line` (formerly `edit-3`) | exact |
| CheckIcon | `check` | exact |
| XIcon | `x` | exact |
| ArrowUpIcon / ArrowDownIcon | `arrow-up` / `arrow-down` | exact |
| CoinsIcon | `database` (stacked ellipses) | close; it is not Lucide `coins` |
| SparklesIcon | `sparkles` | custom |
| ChevronRightIcon / ChevronDownIcon | `chevron-right` / `chevron-down` | exact |
| MailIcon | `mail` | close |
| PhoneIcon | `phone` | exact (Feather) |
| TagIcon | `tag` | close |
| AlertTriangleIcon | `triangle-alert` | exact (Feather `alert-triangle`) |
| CheckCircleIcon | `circle-check` | close (r 9) |
| InfoIcon | `info` | close (r 9) |
| XCircleIcon | `circle-x` | close (r 9) |
| AwardIcon | `award` | close |
| BoltIcon | `zap` | close |
| ClockIcon | `clock` | close |
| BanIcon | `ban` | close |
| MenuIcon | `menu` | exact (as paths) |
| CopyIcon | `copy` | exact (Feather) |
| HomeIcon | `house` | custom |
| PackageIcon | `package` | custom |
| WalletIcon | `wallet` | close |
| UserIcon | `user` | custom |
| ShoppingBagIcon | `shopping-bag` | custom |
| MoreVerticalIcon | `ellipsis-vertical` | filled dots, strokeWidth 0 |
| SignalIcon / WifiIcon / BatteryIcon | `signal` / `wifi` / `battery-full` | custom (phone status bar) |
| RefreshIcon | `rotate-cw` | close |

- For mocks, Lucide icons at `stroke-width="1.75"` are a faithful stand-in.
- Admin nav mapping (`AppShell.tsx:36-45`):
  - Dashboard: layout-dashboard
  - Members: users
  - Segments: tag
  - Rewards: gift
  - Products: shopping-bag
  - Challenges: target
  - Events: zap
  - Tiers: layers
  - Sign out: log-out

## 6. Admin layout sizes (`client/components/layout/AppShell.tsx`)

| Part | Value |
|---|---|
| Sidebar | `w-72` (18rem = 288px at 16px root), fixed, `bg-surface`, `border-r border-line`, shown from `lg` (1024px) (`:135`) |
| Sidebar brand bar | `h-16` (64px), `px-5`, `border-b` (`:136`) |
| Sidebar nav | `p-3`, items `space-y-1` (`:139`, `:90`) |
| Nav item | `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium`, icon `text-lg`. Active: `bg-primary-subtle text-primary-subtle-fg`. Idle: `text-muted hover:bg-surface-2 hover:text-foreground` (`:102-109`) |
| Program switcher block | `mb-4`. Label `text-xs font-medium uppercase tracking-wide text-faint`. "Manage" `text-xs font-medium text-muted`. Trigger `mt-1.5 w-full rounded-md border border-line bg-surface px-2 py-1.5 gap-2.5` with a 36px program mark (`ProgramSwitcher.tsx:51-87`) |
| Sign out | `border-t border-line p-3`, styled like a nav item (`:74-81`) |
| Mobile header | `h-14` (56px), sticky, `bg-surface/85 backdrop-blur px-4 gap-3`, 36px icon buttons (`:147-152`) |
| Mobile drawer | `w-72 max-w-[85%]`, header `h-14` (`:166-167`) |
| Main | `lg:pl-72`. Inner `mx-auto max-w-6xl` (72rem = 1152px), `px-4 py-6 sm:px-6 lg:px-8 lg:py-8` (`:188-189`) |
| Page rhythm | Pages stack with `space-y-6` (for example `programs/page.tsx:27`) |

## 7. Primitives (exact Tailwind classes)

**Button** (`client/components/ui/Button.tsx`)
- Base: `inline-flex items-center justify-center font-medium whitespace-nowrap transition-colors select-none cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed` (`:42-43`).
- Variants (`:9-18`):
  - primary: `bg-primary text-primary-fg hover:bg-primary-hover shadow-sm`
  - secondary: `bg-surface text-foreground border border-line hover:bg-surface-2`
  - ghost: `text-muted hover:bg-surface-2 hover:text-foreground`
  - danger: `bg-danger text-white hover:brightness-95 shadow-sm`
  - success: `bg-success text-white hover:brightness-95 shadow-sm`
- Sizes (`:20-27`):
  - xs: `h-7 px-2 text-xs gap-1 rounded-md`
  - sm: `h-8 px-3 text-[0.8125rem] gap-1.5 rounded-lg`
  - md (default): `h-10 px-4 text-sm gap-2 rounded-lg`
  - icon: `h-9 w-9 rounded-lg justify-center`
- The loading state puts a spinner before the label (`:72`).

**Card** (`Card.tsx`)
- `rounded-xl border border-line bg-surface shadow-sm` (`:9`).
- CardHeader: `flex items-start justify-between gap-4 border-b border-line px-5 py-4`. Title `text-sm font-semibold text-foreground`. Description `mt-0.5 text-[0.8125rem] text-muted` (`:31-38`).

**Table** (`Table.tsx`)
- Wrapper `overflow-x-auto`. Table `w-full border-collapse text-sm`.
- THead: `border-b border-line text-left text-xs font-medium text-muted`. TBody: `divide-y divide-line`.
- TH: `px-4 py-2.5 text-left font-medium whitespace-nowrap`. TD: `px-4 py-3 text-left align-middle text-foreground`.
- TR: `transition-colors`. Rows add `hover:bg-surface-2/60`, and selected rows `bg-primary/5` (`components/members/MembersTable.tsx:61-62`).
- Tables usually sit inside a Card.

**Badge** (`Badge.tsx`)
- `inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium` (`:24`).
- Tones (`:7-13`):
  - neutral: `bg-surface-2 text-muted`
  - primary: `bg-primary-subtle text-primary-subtle-fg`
  - success: `bg-success-subtle text-success-fg`
  - warning: `bg-warning-subtle text-warning-fg`
  - danger: `bg-danger-subtle text-danger-fg`

**StatusBadge** (`StatusBadge.tsx`)
- A Badge with an icon (`text-[0.8125rem]`) and a label. Status is always shown with an icon, never by colour alone (`:15`).
- Challenge statuses:
  - Assigned: neutral, clock
  - In progress: primary, bolt
  - Completed: success, check-circle
  - Expired: warning, clock
  - Cancelled: danger, ban
- Transaction types: Earn (success, arrow-up), Spend (danger, arrow-down), Adjust (primary, sparkles).
- Active/Inactive and Verified/Unverified: success with check-circle, or neutral with ban (`:16-82`).

**Dialog** (`Dialog.tsx`)
- Overlay: `fixed inset-0 z-50 flex justify-center overflow-y-auto p-4 sm:p-6`, top-aligned by default. Backdrop: `bg-black/40 backdrop-blur-[2px]`.
- Panel: `relative z-10 my-6 w-full animate-dialog-in rounded-2xl border border-line bg-surface shadow-xl`.
- Widths: sm `max-w-sm`, md (default) `max-w-lg`, lg `max-w-2xl` (`:10-14`, `:62-82`).
- Header: `flex items-start justify-between gap-4 border-b border-line px-5 py-4`. Title `text-base font-semibold`. Description `mt-0.5 text-[0.8125rem] text-muted`. Close X: `h-8 w-8 rounded-lg text-lg text-faint` (`:83-98`).
- Body: `px-5 py-4` (`:99`).
- Form footer: `flex justify-end gap-2 pt-1`, with a secondary **Cancel** and then the primary submit (`FormDialog.tsx:104-109`). A confirm dialog uses `size="sm"` and a danger button (`ConfirmButton.tsx:73`, `:85-92`).

**Field and inputs** (`Field.tsx`)
- Control: `w-full rounded-lg border border-line bg-surface px-3 py-2 text-sm text-foreground placeholder:text-faint transition-colors focus:border-primary focus-visible:outline-none focus:ring-2 focus:ring-primary/25 disabled:opacity-60` (`:10-13`).
- Label: `mb-1.5 flex items-center justify-between gap-2 text-[0.8125rem] font-medium text-foreground`. An optional hint sits on the right as `font-normal text-faint` (`:25-31`).
- Help text: `mt-1 text-xs text-faint` (`:58`). Fields stack with `space-y-4`.
- Textarea adds `min-h-19 resize-y`. Select adds `appearance-none pr-9` and a chevron at `right-3` (`:75`, `:86-89`).
- Checkbox: `h-4 w-4 rounded border-line accent-primary` (`:104`).

**ErrorBanner** (`ErrorBanner.tsx:5-8`)
- `flex items-start gap-2 rounded-lg border border-danger/30 bg-danger-subtle px-3 py-2 text-[0.8125rem] text-danger-fg`, with an alert-triangle icon.

**Tabs** (`Tabs.tsx`)
- Segmented control. Track: `flex gap-1 rounded-lg bg-surface-2 p-1`.
- Tab: `flex-1 rounded-md px-3 py-2 text-sm font-medium`. Active: `bg-surface text-foreground shadow-sm`. Idle: `text-muted hover:text-foreground`.
- Panel: `mt-4` (`:32-51`).

**PageHeader** (`PageHeader.tsx:11-22`)
- Row: `flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between`.
- Title: `text-2xl font-semibold tracking-tight text-foreground`. Description: `mt-1 text-sm text-muted`. Actions: `flex shrink-0 items-center gap-2`.

**StatTile** (`StatTile.tsx`)
- A Card with `p-5` (md) or `p-4` (sm).
- Label: `text-[0.8125rem] font-medium text-muted`. Value: `mt-2 text-3xl font-semibold tracking-tight` (sm: `mt-1.5 text-xl`). Sub-line: `mt-1 text-xs text-faint`.
- Icon chip on the right: `h-10 w-10 text-xl rounded-lg`, tinted with the accent colour: `bg-accent-blue/12 text-accent-blue` (aqua and yellow use /15) (`:7-33`, `:57-80`).
- Numbers of 10,000 or more are shortened ("12.9K") (`client/lib/format.ts:12-14`).
- Dashboard example: a grid of 4 tiles, `grid gap-4 sm:grid-cols-2 lg:grid-cols-4`, starting with "Members" (blue, users) (`client/app/admin/(protected)/dashboard/page.tsx:61-65`).

**EmptyState** (`EmptyState.tsx:17-33`)
- `flex flex-col items-center justify-center px-6 py-14 text-center`.
- Icon disc: `mb-3 h-12 w-12 rounded-full bg-surface-2 text-xl text-faint`.
- Title: `text-sm font-semibold`. Description: `mt-1 max-w-sm text-[0.8125rem] text-muted`. Action: `mt-4`.

**Toast** (`Toast.tsx`)
- Stack: `fixed inset-x-0 bottom-0 z-[60] flex flex-col items-center gap-2 p-4 sm:items-end sm:p-6`. It is centred at the bottom on phones and bottom-right on larger screens (`:61`).
- Card: `flex w-full max-w-sm animate-dialog-in items-start gap-3 rounded-xl border border-line bg-surface px-4 py-3 shadow-lg`.
- Icon: `text-lg`. Success is `text-success` with check-circle, error is `text-danger` with x-circle, info is `text-primary` with info.
- Message: `text-[0.8125rem] text-foreground`. Dismiss X: `text-faint` (`:72-108`).
- Toasts disappear after 4.5 s (`:42`).

**Other pieces seen in these screens**
- Avatar and initials mark: `h-9 w-9 rounded-full text-xs font-semibold`, tinted with one of the 5 accent colours, picked from a hash of the name (`Avatar.tsx:4-34`).
- Program logo mark: `h-9 w-9 rounded-full border border-line bg-white p-1` (`client/components/branding/ProgramMark.tsx:16`).
- DropdownMenu panel: `rounded-lg border border-line bg-surface py-1 shadow-lg`, default `w-48`. Items: `flex w-full items-center gap-2 px-3 py-2 text-[0.8125rem] hover:bg-surface-2` (`DropdownMenu.tsx:62-69`, `:88-90`).
- Switch: `h-5 w-9 rounded-full`, `bg-primary` when on and `bg-line` when off, with a white `h-4 w-4` knob (`Switch.tsx:21-31`).
- ProgressMeter: `h-2 rounded-full`. The track is the `*-subtle` tone and the fill the solid tone (`ProgressMeter.tsx:6-43`).
- Skeleton: `animate-pulse rounded-md bg-surface-2` (`Skeleton.tsx:12`).
- "Default" pill on the Programs page: `rounded-full bg-primary-subtle px-2 py-0.5 text-xs font-medium text-primary-subtle-fg` (`client/app/admin/(protected)/programs/page.tsx:53`).
- Landing and login: page `bg-surface-2`, centred `max-w-sm` column. Entry tile: `rounded-xl border border-line bg-surface p-5 shadow-sm hover:border-primary/40`, with a `h-11 w-11 rounded-lg bg-primary-subtle text-primary-subtle-fg` icon chip (`client/app/page.tsx:25-27`).

## Identity rough edges (for the product team)

- `components/ui/Logo.tsx` is an unused, off-brand *blue* logo (`Logo.tsx:13-16`). It could confuse anyone who picks it up.
- The root metadata says **"Loyalty App Simulator"** (`client/app/layout.tsx:20-21`) while the product is called "Loyalty Simulator" everywhere else.
- A stock program saved with the stock primary `#5b4bd6` entered explicitly would derive slightly different tints from the hand-tuned defaults. For example, the derived subtle colour is 12% brand on white, while the stock `--primary-subtle` is the hand-picked `#efecfd` (`client/lib/theme.ts:78`, `globals.css:24`).
