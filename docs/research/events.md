# Events area: research for staff docs

Source read on 2026-10-23. Every fact cites `file:line`. `?` marks an open question.

**Path legend**

| Short | Full path |
|---|---|
| `list.tsx` | `client/app/admin/(protected)/events/page.tsx` |
| `[id]/page.tsx` | `client/app/admin/(protected)/events/[id]/page.tsx` |
| `logs/page.tsx` | `client/app/admin/(protected)/events/logs/page.tsx` |
| `ETD` | `client/components/events/EventTypeDialog.tsx` |
| `ED` | `client/components/events/EventDetail.tsx` |
| `RED` | `client/components/events/RuleEditorDialog.tsx` |
| `RI` | `client/components/events/RuleItem.tsx` |
| `rules.ts` | `client/components/events/rules.ts` |
| `TED` | `client/components/events/TestEventDialog.tsx` |
| `EAF` | `client/components/events/EventAttributeFields.tsx` |
| `EL` | `client/components/events/EventLog.tsx` |
| `EE` | `client/components/events/EventEffects.tsx` |
| `MEC` | `client/components/members/MemberEventsCard.tsx` |
| `actions.ts` | `client/lib/events/actions.ts` |
| `cond.ts` | `client/lib/conditions.ts` |
| `cattr.ts` | `client/lib/custom-attributes.ts` |
| `keys.ts` | `client/lib/swr/keys.ts` |
| `api.ts` | `client/lib/api.ts` |
| `r/events.py` | `api/app/routers/events.py` |
| `r/event_types.py` | `api/app/routers/event_types.py` |
| `s/events.py` | `api/app/services/events.py` |
| `effects.py` / `conditions.py` / `fields.py` | `api/app/services/rules/…` |
| `schema` | `api/app/schemas/event.py` |
| `model` | `api/app/models/event.py` |
| `ca.py` | `api/app/services/custom_attributes.py` |
| `program.py` | `api/app/core/program.py` |
| `main.py` | `api/app/main.py` |
| `mig1` / `mig2` | `supabase/migrations/20260924090000_member_events.sql` / `20260930090000_event_type_names_and_event_ids.sql` |
| `T-reg` / `T-int` | `api/tests/regression/test_event_rules.py` / `api/tests/integration/test_member_event_flow.py` |

UI primitives: `client/components/ui/{PageHeader,Card,Dialog,Switch,ConfirmButton,Badge,StatusBadge,EmptyState,ErrorBanner,Field,Table,Button,Toast}.tsx`.

---

## Concepts (for the glossary)

- **Event** (code: "event type"): something a member does that an outside system reports, e.g. "Order placed". It must be defined before the API accepts it (`model:26-31`).
- **API key** (code: `key`): what the sending system puts in `type`. It is made from the name when the event is created and never changes (`model:30-31`, `schema:42-43`, `s/events.py:34-41`).
- **Attribute**: data sent with each event. Types are Text, Number, Yes / No, Date, Dropdown (`cattr.ts:9-15`).
- **Rule**: "when this event arrives, if all conditions hold, run all effects" (`services/rules/__init__.py:3-6`, `model:65`).
- **Effect**: one thing a rule does (8 types, see the rule builder section).
- **Event log**: every received event in the program, plus what its rules did.

---

## Screen 1: Events list (`/admin/events`)

**How to reach it**
- Sidebar item **Events** (bolt icon), between **Challenges** and **Tiers** (`client/components/layout/AppShell.tsx:43`).
- Also from the "All events" back links on the detail and log pages (`ED:286-295`, `EL:31-37`).

**Layout (for the mock)**
- Page wrapper `space-y-6` (`list.tsx:34`).
- `PageHeader`: on the left, an h1 `text-2xl font-semibold tracking-tight` with a description `mt-1 text-sm text-muted`. On the right, actions in `flex gap-2`. It stacks on mobile (`flex-col sm:flex-row`) (`PageHeader.tsx:11-23`).
- Actions, left to right: **Logs** (a secondary-styled link with a clock icon), **Test event** (secondary, bolt icon), **New event** (primary, plus icon) (`list.tsx:42-46`, `list.tsx:27-31`).
- A single `Card` (`rounded-xl border border-line bg-surface shadow-sm overflow-hidden`) holds a table (`Card.tsx:8`, `list.tsx:51`).
- Table header row: `text-xs font-medium text-muted`, cells `px-4 py-2.5`. Body rows are `divide-y divide-line` with cells `px-4 py-3` (`Table.tsx`).

**Labels**
- Title: **Events**. Description: "Things members do in your systems. Rules decide what each event earns." (`list.tsx:36-37`)
- Columns: **Event**, **API key**, **Attributes**, **Rules**, **Status**, plus an empty column for the chevron (`list.tsx:84-89`).

**Row content**
- Event: the name as a link (`font-medium hover:underline`), with the description below it truncated at `max-w-xs`, in `text-[0.8125rem] text-muted` (`list.tsx:105-116`).
- API key: the key in a `code` chip (`rounded-md bg-surface-2 px-1.5 py-0.5 font-mono text-xs text-muted`) (`list.tsx:119-121`).
- Attributes: up to 3 neutral badges showing attribute labels, then a "+N" badge. Shows "-" when there are none (`list.tsx:20`, `list.tsx:124-135`).
- Rules: "No rules yet" (muted), or "{n} active" followed by a muted " · {m} paused" (`list.tsx:138-147`). It can read "0 active · 2 paused".
- Status: a green **Active** badge with a check icon, or a neutral **Inactive** badge with a ban icon (`StatusBadge.tsx:63-75`).
- The whole row is clickable (`cursor-pointer hover:bg-surface-2/60`) and opens the detail page (`list.tsx:99-103`).
- Order: oldest event first (`r/event_types.py:85`).

**States**
- Loading: 3 skeleton rows (`list.tsx:63-72`).
- Error: icon, "Couldn't load events", the error text, and a **Retry** button (`list.tsx:52-62`).
- Empty: bolt icon, "No events yet", "Define an event, such as an order or an app visit, then add rules for it.", and a **New event** button (`list.tsx:73-79`).

**Actions**
- **Logs** opens `/admin/events/logs` (`list.tsx:42`).
- **Test event** opens the "Test an event" dialog (Screen 5). It is disabled when no event is active, with the tooltip "Define an event and turn it on to test it." (`TED:125-135`).
- **New event** opens the event dialog (Screen 2) (`list.tsx:163`).

---

## Screen 2: New event / Edit event dialog

**How to reach it**
- **New event** on the list page (`list.tsx:28`).
- **Edit event** on the detail page (`ED:131-133`, `ED:247`).

**Layout**
- `Dialog` size `lg` (`max-w-2xl`), hung from the top, with `rounded-2xl border shadow-xl`. The header has a title, a description and an X close button (`Dialog.tsx:10-14`, `Dialog.tsx:65-97`). Esc and a click on the backdrop close it (`Dialog.tsx:46-48`, `Dialog.tsx:69-72`).
- Body `space-y-4`: Name, Description, an Attributes block, then the buttons right-aligned (`ETD:118-218`).
- Each attribute is a bordered box (`rounded-lg border border-line p-2`) with a 3-column grid `[1.4fr_1fr_auto]`: label input, type select, X button. Below it sits a small mono key preview (`font-mono text-[0.6875rem] text-faint`) (`ETD:153-194`).

**Labels**
- Title: "New event" or "Edit event". Description: "Something a member does that your systems report, such as placing an order." (`ETD:33-34`)
- **Name**: placeholder "e.g. Order placed". Help text on create: `API key: {key or "…"}. Your system sends this as "type".` Help text on edit: `API key: {key}. It can't change once created.` (`ETD:119-135`)
- **Description**, with the hint "Optional" and the placeholder "Who sends it, and when" (`ETD:137-144`).
- **Attributes**, with the help text "Data your system sends with the event. Rules can check these values or copy them onto the member." (`ETD:147-150`)
- Per attribute: a label input (placeholder "e.g. Amount"), a type select (Text / Number / Yes / No / Date / Dropdown), and a remove button (aria "Remove attribute"). A Dropdown also shows an options input with the placeholder "Options, separated by commas" (`ETD:155-191`, `cattr.ts:9-15`).
- **+ Add attribute** (a ghost button, sm). A new attribute defaults to type Text (`ETD:198-205`).
- Buttons: **Cancel**, then **Create event** or **Save changes** (`ETD:210-217`).

**Fields and rules**
- Name: required. The UI sets no length limit; the API allows 1–100 characters (`schema:36`, `schema:45`). The name is trimmed (`r/event_types.py:60`).
- Name must be unique in the program. API message: "An event named '{name}' already exists" (`s/events.py:25-31`). The DB enforces it too (`mig2:39-40`, `model:52`).
- Key: derived from the name in camelCase ("Order placed" → `orderPlaced`), using only ASCII letters and digits, at most 63 characters (`ca.py:27-41`). The UI preview mirrors this (`cattr.ts:24-33`). Keys must be unique: "An event with the key '{key}' already exists" (`s/events.py:38-40`). Example: "Order placed!" clashes with "Order placed" (`T-reg:139-140`).
- Description: optional. No limit in the UI or the API. Blank is saved as null (`ETD:84`, `r/event_types.py:47-48`).
- Attribute label: required in the UI ("Every attribute needs a label." `ETD:78-80`). The API allows 1–100 characters (`schema:23`).
- Attribute key: made from the label and fixed once saved (`s/events.py:47-65`). Renaming the label later keeps the key (`T-reg:317-329`).
- Attribute type: fixed once saved. The UI disables the select for existing attributes (`ETD:164`). API message: "The type of '{label}' can't change once created." (`s/events.py:61-62`)
- Dropdown options: comma-separated, trimmed, with blanks dropped (`ETD:92-95`). The API also removes duplicates and requires at least one option: "A dropdown attribute needs at least one option." (`ca.py:44-54`)
- Two attributes with the same key: "Two attributes share the key '{key}'. Rename one of them." (`s/events.py:74-77`)
- Removing an attribute that a rule uses: "'{label}' is used by the rule '{rule}'. Change or delete that rule first." (`s/events.py:94-104`)

**Validation messages, in order**
- UI: "Give the event a name that starts with a letter." Shown only when the name is blank or has no letters or digits at all (`ETD:74-76`).
- UI: "Every attribute needs a label." (`ETD:78-80`)
- Server action: "Name is required." (`actions.ts:31`, `actions.ts:42`). It can't be reached because the dialog checks first.
- API: "Label must contain at least one letter and start with one, so a valid internal key can be derived from it." This appears when the name or an attribute label starts with a digit, e.g. "7-Eleven visit" (`ca.py:36-40`).
- Errors show in a red `ErrorBanner` above the buttons (`ETD:208`, `ErrorBanner.tsx`).

**After saving**
- Create: the toast "Event created. Add a rule, then turn it on." and then a redirect to the new event's detail page (`actions.ts:35`, `ETD:108-113`).
- Edit: the toast "Event saved." and the dialog closes (`actions.ts:46`, `ETD:100-106`).
- Toasts sit bottom-right (bottom-centre on mobile) and disappear after 4.5 s (`Toast.tsx:42`, `Toast.tsx:60`).

**Surprising automatic behaviour**
- **Events created in the console start off (Inactive).** The console sends `isActive: false` (`ETD:85-87`), but the API default is `true` (`schema:38`, `mig1:15`). Events created through the API directly start active.
- Editing never changes the on/off state (`ETD:85-87`).

---

## Screen 3: Event detail (`/admin/events/{id}`)

**How to reach it**
- Click a row or name on the list page (`list.tsx:94-111`).
- After creating an event (`ETD:113`).

**Layout**
- Wrapper `space-y-6`. A back link at the top: chevron plus "All events" (`text-sm text-muted`) (`ED:286-295`).
- Header (`flex-col sm:flex-row sm:justify-between`) (`ED:110-157`):
  - On the left, a 44 px violet icon tile (`h-11 w-11 rounded-lg bg-accent-violet/15 text-accent-violet`, bolt icon). Next to it: the h1 name (`text-2xl font-semibold`), the description (`text-sm text-muted`), and a key chip button (`font-mono text-xs bg-surface-2 rounded-md px-2 py-1`) with a copy icon.
  - On the right, in a row: an on/off switch with the text **Active**/**Inactive**, **Test event** (secondary), **Edit event** (secondary, pencil), a copy-ID icon button, and a trash icon button.
- Body: a grid `lg:grid-cols-3` (`ED:159`).
  - Left (`lg:col-span-2`): the **Rules** card.
  - Right column (`space-y-6`): the **Attributes** card, then the **Send this event** card.
- Card headers: `border-b px-5 py-4`, title `text-sm font-semibold`, description `text-[0.8125rem] text-muted`, action on the right (`Card.tsx:17-43`).

**Labels and content**
- Rules card: title "Rules", description "Every active rule whose conditions match runs. Their order doesn't matter." Action: **+ New rule** (primary, sm) (`ED:161-169`).
- Inactive banner, shown when the event is off. It is amber (`bg-warning-subtle text-warning-fg`) with a warning icon: "This event is off, so incoming events are rejected and no rules run. Turn it on at the top when it's ready." (`ED:170-176`)
- No rules: bolt icon, "No rules yet". The description is `Events are still recorded. Add a rule to decide what "{name}" earns.` The first sentence only shows when the event is active. A **+ New rule** button follows (`ED:177-187`).
- Rule list: `ul.divide-y`, one rule card per rule (Screen 3a) (`ED:189-199`).
- Attributes card: title "Attributes", description "Data sent with each event". Each row shows the label (`text-sm font-medium`), the key (`font-mono text-xs text-faint`) and a type badge (Text / Number / Yes / No / Date / Dropdown). With no attributes: "None. The event only says which member it was." (`ED:204-223`)
- Send this event card: title "Send this event", description "POST it from your system. The response lists what the rules did." A copy icon button (aria "Copy request") sits on the right. Below is a `pre` block (`bg-surface-2 px-5 py-4 font-mono text-xs`) with a curl example (`ED:225-243`, `rules.ts:189-208`).

**Actions**
- Key chip: copies the API key. Toast "API key copied." On failure: "Couldn't copy api key." (`ED:97-104`, `ED:118-125`)
- Copy-ID icon (tooltip "Copy event ID"): copies the event type's UUID. Toast "Event ID copied." (`ED:134-142`)
- **Active switch**: takes effect at once, with no Save. Toasts: "Event turned on." or "Event turned off. Incoming events are rejected." On error, a red toast with the API message, or "Couldn't change the event." (`ED:260-284`, `actions.ts:52-63`)
- **Test event**: opens Screen 5 (fixed-event version). It is disabled while the event is off, with the tooltip "Turn this event on to test it." (`TED:33-39`)
- **Edit event**: opens Screen 2 in edit mode (`ED:131`, `ED:247`).
- **Delete** (trash icon): a confirm dialog (size sm) titled `Delete "{name}"?` with "Its rules are deleted too. Events already received stay in each member's history." and the buttons **Cancel** / **Delete event** (red). On success: the toast "Event deleted." and a redirect to `/admin/events` (`ED:143-155`, `ConfirmButton.tsx:46-57`, `actions.ts:65-73`).
- **New rule**: shows a spinner and stays disabled until rewards, challenges, segments, tiers and member attributes have all loaded (`ED:67-71`, `ED:165`).

**States**
- Loading: a skeleton of the header and both columns (`ED:298-326`).
- 404: bolt icon, "Event not found", "It may have been deleted." with no retry (`ED:73-93`).
- Other errors: "Couldn't load this event", the message, and **Retry** (`ED:81-89`).

**What deleting does (API)**
- Rules are deleted with the event (`model:55-61`, `mig1:41-42`).
- Received events stay. Their `event_type_id` is set to null, and the log then shows the **key** instead of the name (`model:122-125`, `mig1:62-63`, `T-reg:337-339`, `T-int:154-161`).

---

## Screen 3a: Rule card (inside the Rules card)

**Layout** (`RI:72-142`)
- `li` with `px-5 py-4`.
- Top line: a switch (`h-5 w-9`, `bg-primary` when on, `bg-line` when off, `Switch.tsx`), the rule name (`font-medium`), and optional badges. Pencil and trash icon buttons sit on the right.
- Below that, two clause lines. Each has a keyword column (`w-10 text-[0.6875rem] font-semibold uppercase tracking-wide text-faint`) reading **IF** or **THEN**, then chips (`RI:145-153`).
  - Condition chips: `rounded-md border border-line bg-surface-2 px-2 py-0.5`, joined by a faint "and" (`RI:112-125`).
  - Effect chips: `rounded-md bg-primary-subtle text-primary-subtle-fg px-2 py-0.5`, each with an icon: coins (earn), down arrow (burn), gift (reward), target (both challenge effects), tag (both segment effects), user (update member) (`RI:33-42`, `RI:126-139`).
- A paused rule shows the badge **Paused**, and its clause lines fade to `opacity-60` (`RI:84`, `RI:111`).
- Limit badge (clock icon): "Once per member" or "Up to {n} per member" (`RI:85-90`).
- No conditions: the IF line reads "Always, on every event" (`RI:113-114`).

**Sentence wording** (chips are capitalised, `RI:120`, `RI:134`)
- Conditions: `{subject} {operator} {value}`. Member fields read "member's {label}", e.g. "Member's tier is Gold" or "Amount is at least 100" (`cond.ts:131-144`). A field that no longer exists reads "Unknown field" (`cond.ts:142`).
- Effects (`rules.ts:102-140`):
  - "Earn 10 points" / "Earn 1 point" / "Earn points equal to the event's amount"
  - "Burn 5 points" / "Burn points equal to the event's {attr}"
  - `Give reward "{name}"`
  - `Assign challenge "{name}"`
  - `Add {n} progress to "{name}"` / `Add progress to "{name}" equal to the event's {attr}`
  - `Add member to segment "{name}"` / `Remove member from segment "{name}"`
  - `Set member's name to Ada, member's phone to the event's phone` / "… to empty"
  - A deleted reward, challenge or segment shows as `"…"` (`rules.ts:99-100`).

**Actions**
- Switch: pauses or turns on at once. Toasts: `"{rule}" is on.` / `"{rule}" is paused.` (info). On error: the API message or "Couldn't change the rule." (`RI:61-70`)
- Pencil: opens the rule editor with this rule (`RI:93-95`, `ED:196`).
- Trash: a confirm dialog `Delete "{rule}"?` with "New events stop triggering it. Events already received keep what they earned." and the buttons **Cancel** / **Delete rule**. Toast "Rule deleted." (`RI:96-107`, `actions.ts:113-121`)

**Order**
- Rules are listed oldest first, by `created_at` (`model:58`). There is no drag or reorder control anywhere.

---

## Screen 4: Rule builder dialog (New rule / Edit rule)

**How to reach it**
- **New rule** on the detail page (header or empty state).
- The pencil on a rule card (`ED:165`, `ED:183`, `RI:93`).

**Layout**
- `Dialog` size `lg` with `scrollBody`: the panel is capped at the viewport height and the body scrolls (`RED:55-62`, `Dialog.tsx:80-81`). The draft resets each time the dialog opens (`RED:63`).
- Body `space-y-5`. Each clause is a `section` with a 2-column grid `[4.5rem_1fr]`. On the left is a keyword pill (`rounded-md bg-surface-2 px-2 py-0.5 text-xs font-semibold uppercase tracking-wide text-muted`). On the right are an optional bold hint line and the rows (`RED:390-412`).
- Clause order: **Rule name** field, **WHEN**, **IF**, **THEN**, **LIMIT**, then the "In plain words" preview box, the error banner and the buttons (`RED:278-386`).
- WHEN shows a read-only dashed box (`h-10 rounded-lg border border-dashed`) with a violet bolt, the **event name** and a muted "happens" (`RED:289-295`).
- Condition row: grid `[1.3fr_1fr_1fr_auto]` with Field select, Operator select, Value input and an X. On mobile the row becomes a bordered box (`RED:475`).
- Effect row: grid `[1.3fr_2fr_auto]` with Effect select, a settings area and an X. Challenge progress adds a second line "by [amount]". Update member adds an indented sub-list (`border-l-2 border-line pl-3`) (`RED:583-676`).
- Preview: `rounded-lg bg-primary-subtle px-3.5 py-3 text-sm` with a sparkles icon, bold "In plain words: ", then the sentence (`RED:368-374`).

**Labels**
- Title: "New rule" or "Edit rule". Description: `Decide what a "{event}" event does for the member.` (`RED:58-59`)
- **Rule name**: placeholder "e.g. Big basket bonus" (`RED:279-287`).
- IF hint: "All of these must be true". With no conditions: `No conditions, so the rule runs on every "{event}" event.` Button: **+ Add condition** (`RED:297-322`).
- THEN hint: "All of these happen". Button: **+ Add effect** (`RED:325-338`).
- Under THEN, when any Earn points effect exists: "The member's tier multiplier applies to earned points, the same as a manual earn." (`RED:339-343`)
- Under THEN, when any Burn points effect exists: "A burn is skipped when the member doesn't have enough points, the same as a manual burn." (`RED:344-348`)
- LIMIT select (aria "How often a member can trigger this rule"): **Every time the event happens** / **Only the first time per member** / "Up to {n} times per member". The last option only appears if the API already set n > 1 (`RED:351-366`).
- Buttons: **Cancel**, then **Create rule** or **Save changes** (`RED:378-385`).

**Defaults**
- A new rule starts with no conditions and one **Earn points** effect with 10 points (`RED:100-111`, `RED:235-237`).
- A new rule is saved as active. Editing keeps the rule's current on/off state (`RED:262`, `schema:141`).
- Limit defaults to "Every time" (null) (`RED:238`).
- **Add condition** picks the first field (the first event attribute, or Points balance if the event has none), that field's first operator, and its first option or an empty value (`RED:313-319`, `cond.ts:115-121`).

### Conditions

- All conditions must be true (AND). There is no OR and no nesting; "two rules express an OR" (`conditions.py:1-5`, `conditions.py:94-97`).
- **Field picker** (aria "Field"). Group "{Event name} event" holds the event's attributes. Group "Member" holds **Points balance** (number), **Tier**, **Segments**, then each member custom attribute (`RED:414-457`, `rules.ts:58-66`). The API list matches (`fields.py:71-79`).
- **Operators by field type**. The UI label is shown, with the API code in brackets; the first one listed is the default (`cond.ts:71-105`). The API allows the same sets (`conditions.py:21-29`).

  | Field type | Operators (UI order) |
  |---|---|
  | Number (incl. Points balance) | is at least (gte), is more than (gt), is (eq), is not (neq), is at most (lte), is less than (lt) |
  | Text | is (eq), is not (neq), contains |
  | Dropdown | is, is not |
  | Yes / No | is |
  | Date | is before (lt), is after (gt), is on (eq) |
  | Tier | is, is not |
  | Segments | include (contains) |

- **Value input** (`RED:503-537`):
  - Dropdown, Yes / No, Tier and Segments use a select. Yes / No offers Yes or No. Tier and Segments list the program's tiers and segments by name. With nothing to choose, the select shows "Nothing to choose yet".
  - Number uses a number input, Date a date input, Text a text input. The placeholder is "Value".
- **Matching details** (API, `conditions.py:76-91`):
  - Text "is" is an exact, case-sensitive match. "contains" ignores case (`conditions.py:78-80`).
  - Segments "include" checks whether the member is in that segment (`conditions.py:78-79`, `fields.py:106`).
  - Comparisons on a missing value are false (`conditions.py:85-87`).
  - **"is not" is TRUE when the attribute was not sent, or when the member has no tier.** `None != x` (`conditions.py:83-84`). This contradicts the comment "a condition on a missing one just doesn't match" (`s/events.py:111`).
- **Snapshot**: conditions read the member as they were when the event arrived, before any rule's effects. Earlier rules therefore never change whether later rules match (`fields.py:96-108`, `s/events.py:135`).
- **Save-time checks (API)**:
  - "Unknown condition field '{field}'." (`conditions.py:62-63`)
  - "'{label}' can't be compared with '{op}'." (`conditions.py:64-65`)
  - "The condition on '{label}' needs a value." (`conditions.py:42-43`)
  - "The condition on '{label}' needs an id." for a bad tier or segment id (`conditions.py:34-38`)
  - "Tier not found" / "Segment not found" (404) (`conditions.py:44-47`, `services/scoping.py:35`)
  - Type checks: "'{label}' must be a number." / "must be true or false." / "must be a date in YYYY-MM-DD format." / "must be one of: A, B." / "must be 500 characters or fewer." (`ca.py:67-104`)
  - Values are stored typed, e.g. "100" becomes 100 (`conditions.py:66-72`, `T-reg:184`).

### Effects (Then)

Effect picker (aria "Effect"), in UI order, with UI label and API `type` (`rules.ts:86-95`, `schema:58-136`):

| UI label | API type | Settings (UI) | API rules | Result text in log (applied / skipped) |
|---|---|---|---|---|
| **Earn points** | `addPoints` | "Points source" select: "a fixed amount" or "the event's {number attr}". The select only shows if the event has number attributes. A number input (`w-24`, min 1, default 10) shows when the amount is fixed (`RED:597-606`, `RED:681-729`) | Exactly one of `points` (integer > 0) or `fromAttribute` (a number attribute) (`schema:58-64`, `effects.py:100-118`). **The tier multiplier applies**, rounded (`effects.py:137`) | "Earned N points" / skipped: "No points: the event had no {key}", "No points to earn" (`effects.py:133-141`) |
| **Burn points** | `burnPoints` | Same as Earn | Same. No multiplier. Never takes the balance below 0 (`effects.py:144-165`) | "Burned N points" / skipped: "Not enough points to burn N: the member has M", "No points burned: the event had no {key}", "No points to burn" |
| **Give a reward** | `grantReward` | "Reward" select of all program rewards. Shows "No rewards yet" (disabled) when there are none (`RED:607-615`) | The reward must exist when the rule is saved, else 404 "Reward not found" (`effects.py:171-173`). The reward is free (0 points), uses up stock, and has source "assigned" (`services/rewards.py:60-74`) | `Gave reward "X"` / skipped: `"X" is inactive or out of stock`, "Reward no longer exists" (`effects.py:175-187`) |
| **Assign challenge** | `assignChallenge` | "Challenge" select; "No challenges yet" when empty (`RED:616-624`) | The challenge must exist, else 404 "Challenge not found" (`effects.py:194-196`) | `Assigned challenge "X"` / skipped: `Already has the challenge "X"`, `"X": challenge is not active`, `"X": challenge has expired`, "Challenge no longer exists" (`effects.py:198-224`) |
| **Add challenge progress** | `addChallengeProgress` | "Challenge" select, plus a second line "by" with a progress source and amount (default 1) (`RED:641-653`) | `amount` > 0 or `fromAttribute` (number), not both. Neither means 1 (`schema:86-93`, `effects.py:230-236`) | `Added N progress to "X"`, `Completed "X"` (pays out the challenge's rewards, `services/challenges.py:330-360`) / skipped: `Doesn't have the challenge "X"`, `"X": challenge is already completed/cancelled`, `"X": challenge has expired`, "No progress: the event had no {key}", "No progress to add" (`effects.py:238-269`) |
| **Add to segment** | `addToSegment` | "Segment" select; "No segments yet" when empty (`RED:625-633`) | The segment must exist (404 "Segment not found"). Joining also hands out the segment's challenges (`effects.py:272-291`) | `Added to segment "X"` / skipped: `Already in "X"`, "Segment no longer exists" |
| **Remove from segment** | `removeFromSegment` | Same as Add to segment | Challenges the segment handed out are kept (`effects.py:294-313`) | `Removed from segment "X"` / skipped: `Not in "X"` |
| **Update member** | `updateMember` | The text "Set these member fields:", then rows of [Member field] [Set it to: "to a fixed value" or "to the event's {attr}"] [value] [X], **+ Add field**, and the note "Name and phone belong to the person, so a change shows in every program." (`RED:634-673`, `RED:731-780`) | At least 1 field (`schema:121`). Fields: **Name**, **Phone**, and member custom attributes. **Email is not allowed** ("'member.email' can't be updated by a rule.") (`fields.py:82-93`, `effects.py:335-336`). The same field twice is refused: "'{label}' is set twice in one effect." (`effects.py:337-338`). A copy source must have the same type, or the target must be Text: "'{src}' ({type}) can't be copied into '{dst}' ({type})." (`effects.py:347-351`) | "Set favourite store to Berlin, phone to +41 1, newsletter opt in to Yes", partial "Set … (skipped: …)", all failed "Nothing updated: …" (`effects.py:361-403`, `T-reg:239`) |

- Copy sources offered in the UI: for a Text target, every attribute; otherwise only attributes of the same type (`rules.ts:80-82`). This matches the API.
- A value select for a custom Dropdown or Yes / No target includes "Empty", which clears the value. A text value has the placeholder "Empty clears it". Name can't be emptied (`RED:513-535`, `RED:773`).
- **Effect order inside a rule matters for live state.** "Assign challenge" followed by "Add challenge progress" works because of an explicit flush (`effects.py:221-223`, `T-reg:385-401`). Burn checks the live balance (`effects.py:160`).
- **Multiplier**: taken once per event, before any effect. A tier change caused by the event doesn't change what later effects earn (`effects.py:75-77`, `s/events.py:136`).
- **Ledger**: point effects write a transaction with the description "Effect of event {event name}" (`effects.py:121-122`, `T-reg:303-306`).
- After all rules run, the member's tier is re-checked once if any effect ran or was skipped (`s/events.py:161-167`).

### Limit (once per member)
- Null means every time; 1 means "Only the first time per member". Any n > 0 is possible through the API (`schema:146`, `schema:155`).
- Counted as one "rule run" per matching event (`s/events.py:142-144`, `model:128-145`).
- **A run counts even when all of the rule's effects were skipped**, e.g. a reward out of stock. The "once" is then used up (`s/events.py:144-148`).

### Rule builder validation (UI, first failure wins, `RED:186-213`)
1. "Give the rule a name."
2. "Fill in a value for every condition."
3. "Add at least one effect, otherwise the rule does nothing."
4. "Points must be a whole number above 0." (Earn and Burn with a fixed amount)
5. "Create a reward first, then pick it here."
6. "Create a challenge first, then pick it here."
7. "Challenge progress must be a whole number above 0."
8. "Create a segment first, then pick it here."
9. "Choose at least one member field to set."
10. "A member's name can't be set to empty."

Then the server action ("Give the rule a name.", `actions.ts:83`) and the API checks listed above run. API messages appear in the same red banner (`RED:267-270`). Pydantic 422 errors appear as raw text, e.g. "String should have at most 100 characters" for a rule name over 100 characters (`schema:140`, `api.ts:171-189`).

**After saving**: the toast "Rule created." or "Rule saved.", and the dialog closes (`actions.ts:90`, `RED:271-273`).

### Preview sentence ("In plain words")
- Format: `When "{event}" happens, if {conditions joined by " and "}, then {effects joined by " and "}.` With no conditions: `When "{event}" happens, {effects}.` (`rules.ts:143-155`)
- The suffix ", only the first time per member" appears only for limit 1. A limit above 1 is not mentioned (`rules.ts:153`).

### How multiple rules evaluate
- **Every active rule whose conditions all match runs. There is no "first match wins" and no stop-processing** (`s/events.py:139-159`, `ED:163`).
- Rules run in creation order (oldest first, `model:58`). Within a rule, effects run in the order listed.
- Matching uses the start-of-event snapshot, so order never changes which rules match (`fields.py:99-100`). It can still change outcomes that depend on live state: burn after earn, segment "Already in", challenge assign then progress.
- Paused rules (`is_active=false`) are skipped (`s/events.py:140`, `T-reg:331-334`).

---

## Screen 5: Test event dialogs

**Two variants**
- **"Test an event"**: from **Test event** on the list page. It has an **Event** select ("Choose an event", active events only) and a **Member** select (`TED:123-206`). Description: "Choose an event and a member to send it for. Its rules run right away." (`TED:141-142`)
- **`Test "{event}"`**: from **Test event** on the detail page. The event is fixed, so only the member and attributes are asked for. Description: "Send this event for a member you choose. Its rules run right away." (`TED:28-52`, `TED:78-115`)
- Related: on a member's page, the **Events** card has **Send event**, which opens "Send an event" with the description "Record an event for this member, the way your systems would. Its rules run right away." and the button **Send event**. With no active events it shows: "There are no active events yet. Define one first." (`MEC:105-160`)

**Layout**
- Dialog size md (`max-w-lg`). Form `space-y-4`. Buttons on the right: **Cancel**, **Send test event** (`TED:84-113`, `Dialog.tsx:10-14`).

**Fields**
- **Member**: a select. The first option is "Loading members…" (disabled while loading) or "Choose a member". Each option reads "{name} · {email}" (`TED:19-21`, `TED:87-102`). Up to 1000 members are listed, with no search (`keys.ts:22-26`).
- One field per event attribute, labelled with the attribute label and the hint "optional" (`EAF:12-22`):
  - Text: a text input. Number: a number input (any step). Date: a date input.
  - Dropdown: a select of "Not sent" plus the options. Yes / No: a select of "Not sent" / "Yes" / "No" (`EAF:24-53`).
  - Blank inputs are not sent (`actions.ts:141-146`).
- Switching the event in the picker clears the attribute inputs (`TED:192-195`).
- **Send test event** stays disabled until a member (and, in the picker, an event) is chosen (`TED:111`, `TED:202`).

**After sending** (`actions.ts:135-166`, `TED:58-76`)
- Success toasts:
  - "Event recorded. No rules matched."
  - "Event recorded. {applied summaries joined by ". "}." with " ({n} skipped)" appended when some were skipped, e.g. "Event recorded. Earned 40 points. Added to segment "Big spenders"."
  - "Event recorded. Nothing applied ({n} skipped)."
- On success the dialog closes. Members, segments and the event log refresh.
- Errors appear in a red banner inside the dialog with the API text. Server-action guards: "Choose a member." / "Choose an event." Unexpected errors: "Something went wrong. Please try again." (`actions.ts:16-20`, `actions.ts:138-139`)
- **Each console test gets a fresh eventId `console-{uuid}`.** Tests are never treated as duplicates, and a retry after a network error is safe (`actions.ts:130-134`, `actions.ts:151`).
- Test events are real events. Points, rewards, segments and limits are actually applied, and the event shows in the log just like events from an integration (`EL:87`, `actions.ts:125-128`).

---

## Sending events from external systems (user-visible facts)

- The detail page's **Send this event** card shows a ready request (`rules.ts:189-208`):
  ```
  curl -X POST $API_URL/events \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "X-Program-Id: <program id>" \
    -H "Content-Type: application/json" \
    -d '{ "memberId": "<member id>", "type": "<API key>", "attributes": {…}, "eventId": "<optional: your unique id for this event, e.g. order number>" }'
  ```
  Sample attribute values: number 45, Yes / No `false`, date "2026-10-01", the first dropdown option, and for text either a guess from the label ("member@example.com", "+41 79 123 45 67", "Ada Lovelace", "https://example.com") or `<label>` (`rules.ts:163-187`).
- **`type` is the event's API key** (e.g. `orderPlaced`), not its name and not its UUID (`schema:185`, `s/events.py:202-208`). The "Copy event ID" button copies the UUID, which senders do **not** need (`ED:134-142`).
- `memberId` is the loyalty member's UUID (`schema:184`). It must belong to the program, else 404 "Member not found" (`s/events.py:179-186`, `T-reg:294-295`).
- `X-Program-Id` takes the program's UUID **or slug**. **If the header is left out, the event goes to the default program** (`program.py:51-90`). An unknown program gives 404 "Program not found: {value}".
- `attributes`: optional. Every attribute is optional. Unknown keys are refused: "Unknown attribute(s) for '{key}': a, b" (`s/events.py:107-117`). Values are converted ("45" becomes 45, "true" becomes true) or refused with the type messages from `ca.py:67-104`.
- `eventId`: optional, 1–200 characters (`schema:190`).
- Responses: **201** for a new event, **200** for a duplicate (`r/events.py:17-33`). The body lists `effects` (ruleId, ruleName, type, summary, skipped, points (negative for burns), rewardId), `eventId` and `createdAt` (`schema:193-211`). All JSON keys are camelCase (`schemas/base.py` CamelModel).
- Errors: 400 "Unknown event type '{type}'. Define it in the console first." / 400 "The event type '{type}' is inactive." (`s/events.py:207-210`). An inactive event is **not recorded** at all and doesn't appear in the log.

## Idempotency (duplicate event ids)

- The same `eventId` + same `type` + same member returns the **original** event with 200 and runs nothing, even if the new attributes differ (`s/events.py:188-200`, `T-int:116-125`, `T-reg:252-255`).
- The same eventId on a **different type** is a new event, e.g. `order-1` for both orderPlaced and orderRefunded (`mig2:3-6`, `T-reg:422-434`). The same eventId for a different member is also new. The DB enforces this with a unique (member, type, eventId) constraint (`mig2:17-22`).
- With no eventId, every call is a new event (`s/events.py:189`).
- The duplicate check runs **before** the type and active checks. A resend of an already recorded event therefore gets 200 even if the event has since been turned off (`s/events.py:188-210`).
- Concurrency: the member row is locked for the whole event, so two retries can't both run (`s/events.py:176-184`). A constraint race would surface as 409 "The request conflicts with existing data." (`main.py:154-170`).
- The console's API client retries only on network errors and 502/503/504, not on 500 (`api.ts:35-36`).

## What happens on errors (partial application?)

- **Validation errors (unknown member, type, attribute or value; inactive type)** happen before anything is stored. Nothing is recorded (`s/events.py:179-216`).
- **Stale targets never fail the event.** A deleted reward, challenge or segment, an out-of-stock reward, a member without enough points, and so on each become a **skipped** effect with a reason. Other effects and rules still run (`effects.py:5-9`). A stored effect that no longer validates is skipped with "This effect is no longer valid. Edit the rule to fix it." (`effects.py:426-431`)
- Update member can be **partially** applied: good fields are set, bad ones are listed in "(skipped: …)" (`effects.py:398-403`).
- The whole event (record, rule runs, effects) is **one transaction**, committed once at the end (`s/events.py:3-5`, `s/events.py:222-223`). An unexpected exception mid-way means no commit. The session is closed without commit, so nothing is kept (`core/database.py` get_db closes only; `autocommit=False`). ? I did not find an explicit rollback; I infer it from no-commit plus close. The caller would get a 500.

---

## Screen 6: Event logs (`/admin/events/logs`)

**How to reach it**
- **Logs** on the Events list (`list.tsx:42-44`). There is no sidebar entry.

**Layout**
- Wrapper `space-y-6`. A back link "All events" sits on top (`EL:31-37`).
- `PageHeader` with the title on the left. On the right is the filter select (`w-56`) (`EL:39-58`).
- A `Card` holding a table with header row `text-xs text-muted` and top-aligned rows (`align-top`) (`EL:90-125`).

**Labels**
- Title: **Event logs**. Description: "Every event received in this program, and what its rules did." (`EL:40-41`)
- Filter (aria "Filter by event"): **All events** plus every event type by name, including inactive ones (`EL:44-55`).
- Columns: **Event**, **Member**, **What happened**, **When** (`EL:93-96`).

**Row content**
- Event: the name in bold. Below it, attribute values on one line using current labels, e.g. "Order total 45 · Channel App". Yes / No values show as Yes/No, null as "-", in `max-w-56 text-[0.8125rem] text-muted` (`EL:104-107`, `EE:39-49`). For a deleted event type, the name shows as the key and attributes as raw keys (`model:122-125`, `EE:40-42`).
- Member: the name links to `/admin/members/{id}`, with the email below it (`EL:108-116`).
- What happened, one line per effect (`EE:8-32`):
  - Applied: a green check icon plus the summary.
  - Skipped: muted text "Skipped: {summary}".
  - None: "No rules matched".
  - Hovering a line shows the **rule name** as a tooltip (`EE:17`).
- When: a date and time like "Oct 23, 2026, 3:04 PM", converted from UTC to local time (`client/lib/format.ts:46-70`).
- Order: newest first (`r/events.py:57`).

**Filters and limits**
- Only one filter: event type (by key, applied on the server) (`r/events.py:55-56`). There is no member, date or status filter and no search.
- **Only the latest 200 events are shown, with no pagination** (`keys.ts:55`). The API default is 50 (`r/events.py:40`).
- Rows are not clickable. The external `eventId` and the rule names (except on hover) are not shown. The full JSON is only viewable from the member page's Events card, where clicking a row opens a dialog with `JSON.stringify(event)` (`MEC:63-101`).

**States**
- Loading: 5 skeleton rows (`EL:72-82`).
- Error: "Couldn't load event logs", the message, and **Retry** (`EL:61-71`).
- Empty: "No events yet", or `No "{name}" events yet` when filtered. Description: "Events your systems send, and test events, will appear here." (`EL:83-88`)

---

## Contradictions between frontend and backend

1. **Default on/off**: the console creates events off (`ETD:85-87`). The API and DB default to on (`schema:38`, `mig1:15`).
2. **"Their order doesn't matter"** (`ED:163`): true for matching (`fields.py:99-100`), but not for live-state outcomes such as burn after earn, assign then progress, or segment checks (`effects.py:160`, `effects.py:221-223`).
3. **Missing attributes**: the API comment says a condition on a missing attribute "just doesn't match" (`s/events.py:111`), but `neq` returns true (`conditions.py:83-84`).
4. **Name check**: the UI only rejects names with no letters or digits (`ETD:74`, `cattr.ts:24-33`). The API also rejects names starting with a digit, with a message about "Label" (`ca.py:36-40`).
5. **Lengths**: the UI sets no maximum on event name, attribute label or rule name. The API allows 100 characters (`schema:23,36,140`) and answers with raw pydantic text.
6. **Points input**: the UI uses `parseInt`, so "1.5" is accepted as 1 (`RED:155`, `RED:192`). The API requires an integer (`schema:63`).
7. **Rule toggle toasts**: the server action returns "Rule turned on." / "Rule paused." (`actions.ts:107`), but the UI ignores it and shows `"{rule}" is on.` / `is paused.` (`RI:65`).
8. **Limit > 1**: the API supports any n (`schema:146`). The UI can't set it and can only keep it, and the preview sentence doesn't mention it (`RED:360-363`, `rules.ts:153`).
9. **Hint casing**: "Optional" in the event dialog (`ETD:137`) vs "optional" in test forms (`EAF:16`).

## For the product team (bugs / rough edges, not fixed)

- Copy-failure toast lowercases the label: "Couldn't copy api key." / "Couldn't copy event id." (`ED:102`).
- "Copy event ID" (the type UUID) is easy to confuse with the request's `eventId` field. Integrators don't need the UUID (`ED:134-142`, `rules.ts:195`).
- Leaving out `X-Program-Id` silently writes to the default program. Only a server log warning records it (`program.py:75-89`).
- **Deleting and re-creating an event with the same name reuses the key.** Old events then count for duplicate checks: an old `eventId` returns the old event with 200 and runs nothing. They also show up under the new type in the log filter (`s/events.py:188-200`, `r/events.py:55-56`).
- A duplicate `eventId` returns 200 even for a now-inactive or deleted type (`s/events.py:188-210`).
- A once-per-member run is used up even when every effect was skipped (`s/events.py:142-148`).
- Skip reasons use attribute **keys**, not labels: "No points: the event had no amount" (`effects.py:136`, `effects.py:248`, `effects.py:375`).
- Removing a dropdown option from an event attribute is allowed even if a rule's condition uses it. The rule then never matches, and opening it in the editor shows a different option than the one stored, so saving fails with "must be one of" (`s/events.py:47-78`, `RED:515-526`).
- Rewards, challenges, segments and member attributes can be deleted while rules use them. The rule then shows `"…"` and the effect is skipped at run time (`rules.ts:99-100`, `effects.py:182-183`). ? No delete guard found in those routers.
- Reward and challenge pickers list inactive items too (`keys.ts:43-48` `activeOnly=false`).
- Points use Python `round()` (banker's rounding): 44.5 becomes 44 and 45.5 becomes 46 (`effects.py:137`).
- The event log is capped at 200 rows with no paging and no member or date filter (`keys.ts:55`).
- The test dialog member select caps at 1000 members and has no search (`keys.ts:22-26`).
- The list page's Rules column can read "0 active · 2 paused" (`list.tsx:141-145`).
- If a rule is toggled while its editor is open, saving brings back the old on/off state (`RED:262`).
- Only the first validation problem is shown, and API 422 messages are pydantic English, e.g. "Input should be greater than 0" (`api.ts:171-189`).

## Open questions

- ? Is an unexpected error inside an effect really fully rolled back? I infer this from no commit plus `db.close()` (`core/database.py`), not from an explicit rollback, and no test covers it.
- ? Where does staff find the program id or slug for `X-Program-Id`? It is not shown on the Events screens; check the Programs area.
- ? Who holds `$API_TOKEN` (one shared bearer token, per `program.py:5-8`)? This isn't covered in the Events UI.
- ? Whether the member-page Events card belongs in the Events docs or the Members docs. Its JSON view is the only per-event detail view.
