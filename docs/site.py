"""Configuration and page order for one docs site. build.py reads this file.

Everything specific to the product lives here or in the content files. Take every value from the
product's code: its name, logo, brand color and fonts from the theme or design tokens, its screen
tokens from the component styles, and its words (labels, menu names) from the UI strings.
"""

# The code the docs were last checked against. Never shown in the docs. `python3 changes.py` lists
# the commits since then that touch code in `watch` (minus `ignore`); the update routine in
# UPDATE_ROUTINE.md updates the pages for them and then moves `commit` forward with --mark.
SOURCE = {
    'commit': '13db3b222673788479be000558b6bb1c936c5a6d',   # main, after the docs were first merged
    'checked': '2026-10-23',
    # code that can change what users see or what happens when they act
    'watch': [
        'client/app/', 'client/components/', 'client/lib/', 'client/proxy.ts', 'client/next.config.ts',
        'api/app/', 'supabase/migrations/',
    ],
    # never a reason to update the docs, even inside `watch`: the docs themselves, the built page,
    # notes for developers and tests
    'ignore': [
        'docs/', 'client/public/docs/', '*.md', 'api/tests/',
    ],
}

SITE = {
    'title': 'Loyalty Engine Docs',              # browser tab and gallery name: a short name, no explanation
    'product': 'Loyalty Engine',                 # used in the logo's accessible name and the word mark fallback
    'docs_label': 'Docs',              # the small tag next to the logo in the sidebar
    'logo': 'logo.svg',                      # path to the product's logo SVG (relative to this folder), or None
    'logo_mono': False,                 # True paints the logo in the brand mark color; False keeps its own colors
    'brand_color': '#5b4bd6',          # the product's primary brand color, from its theme
    'brand_mark': None,                # logo color if it differs from brand_color (for example a darker tone)
    'neutral_tint': 10,                # 0 = pure greys, 10 = greys leaning slightly toward the brand hue

    # Fonts must come from Google Fonts (the only font host the artifact allows). Use the product's
    # font when it is there; otherwise pick the closest one and keep a system fallback.
    'google_fonts': 'family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500',
    'font_body': "'Geist',system-ui,-apple-system,'Segoe UI',Roboto,sans-serif",
    'font_mono': "'Geist Mono',ui-monospace,SFMono-Regular,Menlo,monospace",
    'font_screen': None,               # font used inside screens; None uses font_body

    # Screen tokens (01-screens.html). Copy them from the product's design tokens. Missing ones are
    # derived from brand_color. Keys: font bg canvas surface line line-strong fg fg-strong muted
    # placeholder primary primary-fg primary-soft primary-text brand danger success warning radius
    # radius-sm radius-lg shadow
    'screen': {
        # client/app/globals.css (light tokens) and components/ui/* radius and shadows
        'font': "'Geist',system-ui,sans-serif",
        'bg': '#ffffff', 'canvas': '#f8fafc', 'surface': '#f1f5f9',
        'line': '#e2e8f0', 'line-strong': '#e2e8f0',
        'fg': '#0f172a', 'fg-strong': '#0f172a', 'muted': '#475569', 'placeholder': '#64748b',
        'primary': '#5b4bd6', 'primary-fg': '#ffffff', 'primary-soft': '#efecfd', 'primary-text': '#4338ca',
        'brand': '#5b4bd6', 'danger': '#d03b3b', 'success': '#0ca30c', 'warning': '#fab219',
        'radius': '8px', 'radius-sm': '6px', 'radius-lg': '12px',
        'shadow': '0 20px 25px -5px rgba(0,0,0,.1),0 8px 10px -6px rgba(0,0,0,.1)',
    },

    'assets_dir': None,                # folder of the product's own SVG icons, for {{s:name}}
    'extra_icons_dir': None,           # folder of extra line icons (24x24) to use with {{i:name}}
    'url': '',                         # the published link, so "copy link" buttons copy the real address
    'storage_key': 'loyalty-engine-docs',
    'glossary_page': 'glossary',

    'group_icons': {'Get started': 'rocket', 'Admin console': 'layout-dashboard', 'Members': 'users',
                    'Program setup': 'gift', 'Events and rules': 'zap', 'Member app': 'smartphone',
                    'Reference': 'book-open'},
    'popular': ['quickstart', 'members', 'points', 'rules', 'tiers', 'troubleshooting'],
    'glossary': {
        'segment': 'A named group of members, such as VIP. Segments can hand out challenges and drive tiers.',
        'tier': 'A level, such as Gold, with conditions and an earn rate multiplier. Members get one on their own.',
        'multiplier': "A tier's earn rate. 1.5 means members in the tier earn 1.5 times the points.",
        'slug': "A program's short web name, such as daybreak-coffee. Made from the name; renaming the program in the console does not change it.",
        'default program': 'The program members sign in to, and the one the console opens first.',
        'API key': 'The short name of an event, such as orderPlaced, that your systems send as "type".',
    },
    'synonyms': {
        'delete': ['remove'], 'points': ['balance', 'credit'], 'burn': ['spend', 'deduct', 'subtract'],
        'earn': ['add points', 'award', 'give points'], 'prize': ['gift', 'free reward'],
        'program': ['brand', 'tenant', 'workspace'], 'segment': ['group', 'cohort', 'list'],
        'tier': ['level', 'status'], 'event': ['webhook', 'integration', 'api'], 'rule': ['automation', 'trigger'],
        'member': ['customer', 'user', 'person'], 'login': ['sign in', 'log in', 'code'],
        'logo': ['branding', 'colour', 'color', 'theme'], 'challenge': ['goal', 'mission', 'quest'],
    },
}

# Sidebar order: (page id, group, sub-heading or None, title, merged-in page ids)
PAGES = [
    ('welcome', 'Get started', None, 'Welcome', []),
    ('tour', 'Get started', None, 'Loyalty Engine at a glance', []),
    ('quickstart', 'Get started', None, 'Set up your first program', []),
    ('recipe-order-points', 'Get started', 'Recipes', 'Give points for every order', []),
    ('recipe-vip-tier', 'Get started', 'Recipes', 'Create a VIP tier', []),
    ('recipe-prize-email', 'Get started', 'Recipes', 'Email a member a prize', []),
    ('recipe-challenge', 'Get started', 'Recipes', 'Run a challenge for a segment', []),
    ('admin-sign-in', 'Admin console', None, 'Sign in to the console', []),
    ('programs', 'Admin console', None, 'Programs and branding', []),
    ('dashboard', 'Admin console', None, 'Dashboard', []),
    ('members', 'Members', None, 'Find and add members', []),
    ('member-page', 'Members', None, "A member's page", []),
    ('points', 'Members', None, 'Earn, burn and adjust points', []),
    ('member-rewards', 'Members', None, 'Rewards and prizes for a member', []),
    ('member-challenges', 'Members', None, "A member's challenges", []),
    ('member-fields', 'Members', None, 'Custom member fields', []),
    ('segments', 'Program setup', None, 'Segments', []),
    ('rewards', 'Program setup', None, 'Rewards', []),
    ('products', 'Program setup', None, 'Products', []),
    ('challenges', 'Program setup', None, 'Challenges', []),
    ('tiers', 'Program setup', None, 'Tiers', []),
    ('events', 'Events and rules', None, 'Events', []),
    ('rules', 'Events and rules', None, 'Rules', []),
    ('test-events', 'Events and rules', None, 'Test an event', []),
    ('event-logs', 'Events and rules', None, 'Event logs', []),
    ('send-events', 'Events and rules', None, 'Send events from your systems', []),
    ('member-sign-in', 'Member app', None, 'Sign up and sign in', []),
    ('member-home', 'Member app', None, 'Open a campaign', []),
    ('member-products', 'Member app', None, 'Products and purchases', []),
    ('member-wallet', 'Member app', None, 'Wallet and prizes', []),
    ('member-account', 'Member app', None, 'Account and programs', []),
    ('member-emails', 'Member app', None, 'Emails members get', []),
    ('limits', 'Reference', None, 'Limits and rules', []),
    ('troubleshooting', 'Reference', None, 'Troubleshooting', []),
    ('glossary', 'Reference', None, 'Glossary', []),
]

NEW_PAGES = {}

RESULT = {
    'welcome': 'You know where to start and how these pages work.',
    'tour': 'You know the two apps and where everything is.',
    'quickstart': 'A program with a reward, a tier and an event that earns points, tested on a member.',
    'recipe-order-points': 'Orders from your systems earn points automatically.',
    'recipe-vip-tier': 'VIP members earn at a higher rate.',
    'recipe-prize-email': 'The member has a prize and an email to claim it.',
    'recipe-challenge': 'A segment works toward a goal and gets paid when they reach it.',
    'admin-sign-in': 'You are in the admin console, or safely signed out.',
    'programs': 'Programs set up with their own branding, and the right one selected.',
    'dashboard': 'You know how the program is doing.',
    'members': 'You can find any member, add new ones and remove old ones.',
    'member-page': "You know a member's full picture and can keep their profile up to date.",
    'points': 'The member has the right balance, with a reason in their history.',
    'member-rewards': 'The member has their reward, paid with points or for free.',
    'member-challenges': "The member's challenges are where they should be.",
    'member-fields': 'Every member carries the extra fields your program needs.',
    'segments': 'Groups of members you can target with challenges and tiers.',
    'rewards': 'A catalog of rewards with the right costs and stock.',
    'products': 'A product catalog members can buy from.',
    'challenges': 'Challenges handed out to the right members.',
    'tiers': 'Members sorted into tiers with the right earn rates.',
    'events': 'Events defined and switched on, ready for your systems.',
    'rules': 'Events that award exactly what you intend.',
    'test-events': 'Proof that your rules do what you expect.',
    'event-logs': 'You know what each event did, and why.',
    'send-events': 'Your developers know how to send events.',
    'member-sign-in': 'Members can get into the member app.',
    'member-home': 'A campaign open for the member.',
    'member-products': 'You know how members buy and what it counts for.',
    'member-wallet': 'Members see their points and claim their prizes.',
    'member-account': 'Members keep their profile current and use the right program.',
    'member-emails': 'You know what each email does and how long it works.',
    'limits': 'Every limit in one place.',
    'troubleshooting': 'A fix for common problems.',
    'glossary': 'Loyalty Engine terms in plain language.',
}

BEFORE = {
    'quickstart': ['The admin username and password'],
    'programs': ['<a href="#admin-sign-in">Signed in</a> to the admin console'],
    'points': ['A member. See <a href="#members">Find and add members</a>'],
    'member-rewards': ['An active reward in stock. See <a href="#rewards">Rewards</a>'],
    'member-challenges': ['An active challenge. See <a href="#challenges">Challenges</a>'],
    'recipe-vip-tier': ['Some members to put in the VIP segment'],
    'recipe-challenge': ['A segment with members in it', 'A reward to use as the prize'],
    'rules': ['An event. See <a href="#events">Events</a>'],
    'test-events': ['An event that is turned on', 'A member'],
    'send-events': ['An event with its attributes', 'A developer who can call the loyalty API'],
}

BADGES = {
    'admin-sign-in': [('role', 'shield', 'Staff')],
    'send-events': [('role', 'code', 'For developers')],
    'member-sign-in': [('role', 'smartphone', 'Members')],
    'member-home': [('role', 'smartphone', 'Members')],
    'member-products': [('role', 'smartphone', 'Members')],
    'member-wallet': [('role', 'smartphone', 'Members')],
    'member-account': [('role', 'smartphone', 'Members')],
    'member-emails': [('role', 'smartphone', 'Members')],
}

RELATED = {
    'welcome': 'tour quickstart',
    'tour': 'quickstart programs',
    'quickstart': 'events rules tiers',
    'recipe-order-points': 'events rules send-events',
    'recipe-vip-tier': 'segments tiers',
    'recipe-prize-email': 'member-rewards member-emails',
    'recipe-challenge': 'challenges segments rules',
    'admin-sign-in': 'programs dashboard',
    'programs': 'tour dashboard',
    'dashboard': 'members tiers',
    'members': 'member-page member-fields',
    'member-page': 'points member-rewards member-challenges',
    'points': 'tiers member-page',
    'member-rewards': 'rewards member-wallet',
    'member-challenges': 'challenges member-page',
    'member-fields': 'tiers rules',
    'segments': 'challenges tiers',
    'rewards': 'member-rewards challenges',
    'products': 'member-products tiers',
    'challenges': 'member-challenges segments',
    'tiers': 'points segments',
    'events': 'rules test-events send-events',
    'rules': 'test-events event-logs',
    'test-events': 'event-logs rules',
    'event-logs': 'rules troubleshooting',
    'send-events': 'events event-logs',
    'member-sign-in': 'member-account member-emails',
    'member-home': 'member-wallet',
    'member-products': 'products',
    'member-wallet': 'member-rewards member-emails',
    'member-account': 'programs member-sign-in',
    'member-emails': 'member-wallet member-sign-in',
    'limits': 'troubleshooting',
    'troubleshooting': 'limits glossary',
    'glossary': 'troubleshooting',
}

OPEN_MESSAGES = {'troubleshooting'}

TABS = {}

CHECKLIST = {'quickstart', 'recipe-order-points', 'recipe-vip-tier', 'recipe-prize-email', 'recipe-challenge'}
