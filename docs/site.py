"""Configuration and page order for one docs site. build.py reads this file.

Everything specific to the product lives here or in the content files. Take every value from the
product's code: its name, logo, brand color and fonts from the theme or design tokens, its screen
tokens from the component styles, and its words (labels, menu names) from the UI strings.
"""

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
    'storage_key': 'loyalty-engine-docs',        # prefix for what the page remembers in the reader's browser
    'glossary_page': 'glossary',       # page id where glossary hover hints are not added

    # sidebar icons per group (Lucide names: https://lucide.dev/icons)
    'group_icons': {'Get started': 'rocket', 'Projects': 'folder-kanban', 'Reference': 'book-open'},
    # pages listed when the search box is empty
    'popular': ['quickstart', 'troubleshooting'],
    # first mention of each term on a page gets a dotted underline with this definition
    'glossary': {
        'workspace': 'Your team\'s space in Acme. Projects and people belong to one workspace.',
    },
    # words readers type, mapped to the words the docs use (search shows both)
    'synonyms': {
        'delete': ['remove'], 'invite': ['add people'], 'teammate': ['member'],
    },
}

# Sidebar order: (page id, group, sub-heading or None, title, merged-in page ids shown as parts or tabs)
PAGES = [
    ('welcome', 'Get started', None, 'Welcome', []),
    ('quickstart', 'Get started', None, 'Create your first project', []),
    ('projects', 'Projects', None, 'Projects', []),
    ('project-settings', 'Projects', None, 'Project settings', ['settings-general', 'settings-members']),
    ('troubleshooting', 'Reference', None, 'Troubleshooting', []),
    ('glossary', 'Reference', None, 'Glossary', []),
]

# Pages with no content section of their own (their parts fill them): {id: (lead, where-bar html)}
NEW_PAGES = {
    'project-settings': ('Change a project\'s name, members and access. Each tab below matches a tab in the settings window.',
                         '<span class="m">Project</span><span class="sep">›</span><span class="m">{{i:settings}} Settings</span>'),
}

# "Result" line under "In short": what the reader ends up with
RESULT = {
    'welcome': 'You know where to start and how these pages work.',
    'quickstart': 'A project with your first task, shared with a teammate.',
    'projects': 'You can find, create and archive projects.',
    'project-settings': 'A project set up the way your team works.',
    'troubleshooting': 'A fix for common problems.',
    'glossary': 'Acme terms in plain language.',
}

# "Before you start" list
BEFORE = {
    'project-settings': ['<a href="#projects">A project</a> you own or manage'],
}

# small badges under the title: (kind, icon, text). kinds: role, avail
BADGES = {
    'project-settings': [('role', 'users', 'Owners and admins')],
}

# Related pages, shown as cards at the end of a page (space-separated ids)
RELATED = {
    'welcome': 'quickstart projects',
    'quickstart': 'projects project-settings',
    'projects': 'project-settings quickstart',
    'project-settings': 'projects',
    'troubleshooting': 'glossary',
    'glossary': 'troubleshooting',
}

# pages whose message tables stay open; everywhere else they collapse into a "Messages" box
OPEN_MESSAGES = {'troubleshooting'}

# pages shown as tabs, one tab per merged part: {page: {part id or 'main': tab label}}
# Name the tabs exactly like the product's own tabs.
TABS = {
    'project-settings': {'settings-general': 'General', 'settings-members': 'Members'},
}

# tutorial pages whose steps readers can tick off; progress shows in the right column
CHECKLIST = {'quickstart'}
