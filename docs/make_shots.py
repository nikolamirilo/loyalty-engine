"""Screens and diagrams for the Loyalty Engine docs. Run it, then build:

    python3 make_shots.py && python3 tooling/scripts/build.py .

Every screen copies its structure, labels and sizes from the client code (client/components/** and
client/app/**). Product classes (le-*, ma-*) live in 01-ui.html. Sample data is invented: one coffee
shop program, "Daybreak Coffee", used across all screens.
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tooling', 'scripts'))
from shots import init, shot, tag, walk  # noqa: E402
from diagrams import Diagram  # noqa: E402

init(__file__)


def ic(name):
    return '{{i:' + name + '}}'


def k(key):
    """A data-k attribute, so tag() and walk() can find an element by a stable needle."""
    return f' data-k="{key}"' if key else ''


def b(text, kind='p', icon=None, size='', key=None, extra=''):
    i = ic(icon) if icon else ''
    cls = ' '.join(x for x in ('le-b', kind, size, extra) if x)
    return f'<span class="{cls}"{k(key)}>{i}{text}</span>'


def badge(text, tone='n', icon=None):
    i = ic(icon) if icon else ''
    return f'<span class="le-bd {tone}">{i}{text}</span>'


def field(label, control, hint='', help_='', key=None):
    h = f'<i>{hint}</i>' if hint else ''
    hp = f'<div class="le-help">{help_}</div>' if help_ else ''
    return f'<div class="le-f"{k(key)}><div class="le-fl"><span>{label}</span>{h}</div>{control}{hp}</div>'


def inp(value='', ph='', cls='', style=''):
    v = value if value else f'<span class="ph">{ph}</span>'
    st = f' style="{style}"' if style else ''
    return f'<div class="le-in {cls}"{st}>{v}</div>'


def sel(value, ph=False, style=''):
    v = f'<span class="ph">{value}</span>' if ph else f'<span>{value}</span>'
    st = f' style="{style}"' if style else ''
    return f'<div class="le-in sel"{st}>{v}{ic("chevron-down")}</div>'


def cb(on=False):
    return f'<span class="le-cb{" on" if on else ""}"></span>'


MEDAL = ('<svg viewBox="0 0 40 40" width="100%" height="100%">'
         '<path d="M15.5,14 L19,14 L19,33 L17.25,30.5 L15.5,33 Z" fill="#fff"/>'
         '<path d="M21,14 L24.5,14 L24.5,33 L22.75,30.5 L21,33 Z" fill="#fff"/>'
         '<circle cx="20" cy="16.5" r="8.3" fill="#fff"/>'
         '<path d="M20,11.5 L21.411,14.558 L24.755,14.955 L22.283,17.242 L22.939,20.545 L20,18.9 L17.061,20.545 L17.717,17.242 L15.245,14.955 L18.589,14.558 Z" fill="#5b4bd6"/>'
         '</svg>')


def logo(size=36):
    """client/public/logo.svg: a medal on an indigo-violet tile (gradient drawn in CSS)."""
    return (f'<span class="le-logo" style="width:{size}px;height:{size}px;border-radius:{round(size * .27)}px;'
            f'background:linear-gradient(135deg,#6d5ef0,#4c3fbf)">{MEDAL}</span>')


ACC = {'blue': ('rgba(42,120,214,.12)', '#2a78d6'), 'aqua': ('rgba(27,175,122,.15)', '#1baf7a'),
       'violet': ('rgba(91,75,214,.12)', '#5b4bd6'), 'orange': ('rgba(235,104,52,.12)', '#eb6834'),
       'yellow': ('rgba(237,161,0,.15)', '#eda100')}


def av(initials, acc='blue', size=36):
    bg, fg = ACC[acc]
    return f'<span class="le-av" style="width:{size}px;height:{size}px;background:{bg};color:{fg}">{initials}</span>'


def mark(initials='DC', acc='orange', size=36):
    bg, fg = ACC[acc]
    return f'<span class="le-mark" style="width:{size}px;height:{size}px;background:{bg};color:{fg}">{initials}</span>'


NAV = [('Dashboard', 'layout-dashboard'), ('Members', 'users'), ('Segments', 'tag'), ('Rewards', 'gift'),
       ('Products', 'shopping-bag'), ('Challenges', 'target'), ('Events', 'zap'), ('Tiers', 'layers')]


def admin(main, active='Dashboard', program='Daybreak Coffee'):
    """AppShell.tsx: w-72 sidebar with brand bar, program switcher, nav and Sign out."""
    items = ''.join(f'<div class="le-ni{" on" if n == active else ""}"{k("nav-" + n.lower())}>{ic(i)}<span>{n}</span></div>' for n, i in NAV)
    switcher = (f'<div class="le-sw"{k("switcher")}><div class="le-swl"><span>Program</span><a{k("manage")}>Manage</a></div>'
                f'<div class="le-swt"{k("switch-trigger")}>{mark()}<b>{program}</b>{ic("chevron-down")}</div></div>')
    return (f'<div class="le-aside"><div class="le-brand">{logo()}<b>Loyalty Engine</b></div>'
            f'<div class="le-nav"{k("nav")}>{switcher}{items}</div>'
            f'<div class="le-signout"><div class="le-ni"{k("signout")}>{ic("log-out")}<span>Sign out</span></div></div></div>'
            f'<div class="le-main">{main}</div>')


def ph(title, desc='', acts='', key=None):
    d = f'<p>{desc}</p>' if desc else ''
    a = f'<div class="acts">{acts}</div>' if acts else ''
    return f'<div class="le-ph"{k(key)}><div><h1>{title}</h1>{d}</div>{a}</div>'


def card(body, title=None, desc='', action='', style='', key=None):
    head = ''
    if title:
        d = f'<p>{desc}</p>' if desc else ''
        head = f'<div class="le-ch"><div><h2>{title}</h2>{d}</div>{action}</div>'
    st = f' style="{style}"' if style else ''
    return f'<div class="le-card"{st}{k(key)}>{head}{body}</div>'


def stat(label, value, icon, acc, sub='', size='', key=None):
    s = f'<div class="s">{sub}</div>' if sub else ''
    return (f'<div class="le-stat {size}"{k(key)}><div><div class="l">{label}</div><div class="v">{value}</div>{s}</div>'
            f'<div class="le-chip a-{acc}">{ic(icon)}</div></div>')


def dialog(title, body, desc='', left=0, top=0, width=512, overlay=True, key=None):
    d = f'<p>{desc}</p>' if desc else ''
    ov = '<div class="le-ov"></div>' if overlay else ''
    return (f'{ov}<div class="le-dlg" style="left:{left}px;top:{top}px;width:{width}px"{k(key)}>'
            f'<div class="le-dh"><div><h2>{title}</h2>{d}</div>{ic("x")}</div><div class="le-db">{body}</div></div>')


def footer(submit, cancel=True, danger=False):
    c = b('Cancel', 's', key='cancel') if cancel else ''
    return f'<div class="le-df">{c}{b(submit, "d" if danger else "p", key="submit")}</div>'


def toast(text, left, top, kind='ok'):
    icon, color = {'ok': ('circle-check', '#0ca30c'), 'err': ('circle-x', '#d03b3b'), 'info': ('info', '#5b4bd6')}[kind]
    return f'<div class="le-toast" style="left:{left}px;top:{top}px"><span style="color:{color}">{ic(icon)}</span><span style="flex:1">{text}</span><span class="le-faint">{ic("x")}</span></div>'


def table(cols, rows, key=None):
    th = ''.join(f'<th>{c}</th>' for c in cols)
    body = ''.join(r if r.startswith('<tr') else f'<tr>{r}</tr>' for r in rows)
    return f'<table class="le-t"{k(key)}><thead><tr>{th}</tr></thead><tbody>{body}</tbody></table>'


def who(name, email, initials, acc):
    return f'<div class="le-who">{av(initials, acc)}<div><b>{name}</b><small>{email}</small></div></div>'


def pts(n):
    return f'<span class="le-pts"><b>{n}</b><small>pts</small></span>'


MEMBERS = [
    ('Maya Torres', 'maya.torres@example.com', 'MT', 'violet', 'Gold', ['VIP', 'Newsletter'], '2,450'),
    ('Liam Chen', 'liam.chen@example.com', 'LC', 'blue', 'Silver', ['Newsletter'], '820'),
    ('Sofia Rossi', 'sofia.rossi@example.com', 'SR', 'orange', 'Bronze', [], '310'),
    ('Noah Becker', 'noah.becker@example.com', 'NB', 'aqua', 'Gold', ['VIP', 'Big spenders', 'Newsletter', 'App users'], '5,120'),
    ('Aisha Khan', 'aisha.khan@example.com', 'AK', 'yellow', None, ['Newsletter'], '40'),
]

# =====================================================================================
# Admin console: sign in, dashboard, programs
# =====================================================================================

login = (f'<div class="ma-center" style="padding-top:56px"><div style="width:384px;display:flex;flex-direction:column;align-items:center;gap:12px">'
         f'{logo(48)}<div style="text-align:center"><div style="font-size:18px;font-weight:600">Loyalty Engine</div>'
         f'<div class="le-muted" style="font-size:14px;margin-top:2px">Sign in to the admin console</div></div>'
         f'<div class="le-card" style="width:100%;padding:24px;margin-top:12px"><div class="le-stack">'
         + field('Username', inp('admin', cls='focus'), key='user') + field('Password', inp('&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;&bull;'), key='pass') +
         '<div class="le-err" data-k="err">' + ic('triangle-alert') + '<span>Invalid username or password. 2 attempts left before a 10-minute lockout.</span></div>' +
         b('Sign in', 'p', size='full', key='signin') + '</div></div></div></div>')
shot('admin-login', 560, 520, login, 'The admin sign-in page after one wrong password.')
walk('admin-login', [('<div class="le-f" data-k="user"', 1), ('<div class="le-f" data-k="pass"', 2), ('<span class="le-b p full" data-k="signin"', 3), ('<div class="le-err"', 4)])

recent = table(['Member', 'Tier', 'Balance'], [
    f'<td>{who(n, e, i, a)}</td><td>{badge(t, "pr") if t else "-"}</td><td>{pts(p)}</td>' for n, e, i, a, t, s, p in MEMBERS[:4]])
dist = ''.join(f'<div><div class="row" style="justify-content:space-between;font-size:14px;margin-bottom:6px"><span class="w5">{n}</span><span class="le-muted">{c} ({p}%)</span></div><div class="le-bar"><i style="width:{p}%"></i></div></div>'
               for n, c, p in [('Gold', '128', 10), ('Silver', '342', 27), ('Bronze', '701', 55), ('No tier', '113', 9)])
dash = (ph('Dashboard', 'Overview of your loyalty program.') +
        '<div class="le-stats" style="grid-template-columns:repeat(4,minmax(0,1fr))" data-k="stats">' +
        stat('Members', '1,284', 'users', 'blue') + stat('Points in circulation', '412.5K', 'database', 'aqua') +
        stat('Active rewards', '6', 'gift', 'orange', '8 total') + stat('Active challenges', '3', 'target', 'violet', '4 total') + '</div>'
        '<div style="display:grid;grid-template-columns:2fr 1fr;gap:24px">' +
        card(recent, 'Members', 'Most recent in the program', '<span class="le-muted w5" style="font-size:13px">View all ›</span>', key='recent') +
        card(f'<div style="padding:20px;display:flex;flex-direction:column;gap:16px">{dist}</div>', 'Tier distribution', 'Members by current tier', key='dist') + '</div>')
inner = admin(dash, 'Dashboard')
for n, needle in enumerate(['<div class="le-sw"', '<a data-k="manage"', '<div class="le-ni on"', '<div class="le-stats"', '<div class="le-card" data-k="recent"', '<div class="le-card" data-k="dist"', '<div class="le-ni" data-k="signout"'], 1):
    inner = tag(inner, needle, n)
shot('tour-console', 1280, 720, inner, 'The admin console on the Dashboard page.',
     ['Program switcher: the program everything below belongs to', 'Manage opens the Programs page', 'Main menu',
      'Program totals', 'The newest members', 'How many members are in each tier', 'Sign out'], title='Loyalty Engine - Admin')

prog_rows = [
    ('DC', 'orange', 'Daybreak Coffee', True, True, 'Coffee shop loyalty, earn on every order'),
    ('SD', 'blue', 'Summer Demo', False, False, 'Sandbox for testing new rules'),
]
rows = ''
for i, (ini, acc, name, dflt, cur, desc) in enumerate(prog_rows):
    pills = (' <span class="le-bd pr">Default</span>' if dflt else '') + (' <span class="le-muted" style="font-size:12px">Currently viewing</span>' if cur else '')
    acts = ('' if cur else b('Switch to', 's', size='sm', key='switch')) + \
        f'<span class="le-b gh ic"{k("copy" if i else None)}>{ic("copy")}</span><span class="le-b gh ic"{k("edit" if i else None)}>{ic("pen-line")}</span>' + \
        ('' if dflt else f'<span class="le-b gh ic" style="color:#d03b3b"{k("del")}>{ic("trash-2")}</span>')
    rows += (f'<div class="le-card" style="padding:16px 20px;display:flex;align-items:center;gap:16px"><span style="flex:none">{mark(ini, acc)}</span>'
             f'<div style="flex:1;min-width:0"><div class="row g8"><b class="w6">{name}</b>{pills}</div><div class="le-muted" style="font-size:13px;margin-top:2px">{desc}</div></div>'
             f'<div class="row g4">{acts}</div></div>')
progs = (ph('Programs', 'Each program has its own rewards, products, challenges, tiers and member points. Switching programs in the sidebar changes everything the console shows.',
            b('New program', 'p', 'plus', key='new')) + f'<div class="le-stack" style="gap:12px">{rows}</div>')
inner = admin(progs, None)
for n, needle in enumerate(['<span class="le-b p" data-k="new"', '<span class="le-bd pr"', '<span class="le-b s sm" data-k="switch"', '<span class="le-b gh ic" data-k="copy"', '<span class="le-b gh ic" data-k="edit"', '<span class="le-b gh ic" style="color:#d03b3b" data-k="del"'], 1):
    inner = tag(inner, needle, n)
shot('programs-list', 1280, 580, inner, 'The Programs page with two programs.',
     ['New program', 'The default program', 'Switch the console to this program', 'Copy program ID', 'Edit', 'Delete (not shown for the default program)'], title='Programs')

colour = lambda label, help_, val, sw, key: field(label, f'<div class="row g8"><span style="width:40px;height:40px;border-radius:8px;border:1px solid #e2e8f0;background:{sw};flex:none"></span>' + inp(val, 'Default', style='font-family:Geist Mono,monospace;width:140px') + b('Reset', 'gh', size='sm') + '</div>', help_=help_, key=key)
pdlg = dialog('New program',
              '<div class="le-stack">' + field('Name', inp('Daybreak Coffee', cls='focus'), key='name') + field('Description', inp('Coffee shop loyalty, earn on every order'), key='desc') +
              '<div class="le-muted" style="font-size:13px">Branding is optional. The console and the member app use this program\'s logo and colours when it is selected.</div>' +
              field('Logo', '<div class="row g12"><span style="width:56px;height:56px;border:1px solid #e2e8f0;border-radius:8px;display:flex;align-items:center;justify-content:center;opacity:.4">' + logo(40) + '</span>' + b('Upload logo', 's', size='sm') + '</div>', help_='PNG, JPG, WebP or SVG, up to 2 MB.', key='logo') +
              '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">' +
              colour('Primary colour', 'Buttons, links and highlights. Pick one that reads on white.', '#b45309', '#b45309', 'primary') +
              colour('Secondary colour', 'Accent on the member tier card.', '', '#eb6834', 'secondary') + '</div>' +
              footer('Create program') + '</div>',
              'A program has its own rewards, products, challenges, tiers and segments. Existing members join it automatically, starting at 0 points.', 24, 24, 640, overlay=False)
shot('program-dialog', 688, 680, pdlg, 'The New program window.')
walk('program-dialog', [('<div class="le-f" data-k="name"', 1), ('<div class="le-f" data-k="desc"', 2), ('<div class="le-f" data-k="logo"', 3), ('<div class="le-f" data-k="primary"', 4), ('<span class="le-b p" data-k="submit"', 5)])

menu = ('<div class="le-menu" style="left:0;right:0;top:100%;margin-top:4px;width:auto">' +
        f'<div class="le-mi on">{mark()}<span>Daybreak Coffee</span>{ic("check")}</div>' +
        f'<div class="le-mi" data-k="pick">{mark("SD", "blue")}<span>Summer Demo</span></div></div>')
sw_inner = admin('', 'Dashboard').replace('<div class="le-swt" data-k="switch-trigger">', '<div class="le-swt" data-k="switch-trigger" style="position:relative">', 1)
sw_inner = sw_inner.replace('</b>' + ic('chevron-down') + '</div></div>', '</b>' + ic('chevron-down') + menu + '</div></div>', 1)
shot('program-switch', 288, 420, sw_inner, 'The program switcher open in the sidebar.')
walk('program-switch', [('<div class="le-swt"', 1), ('<div class="le-mi" data-k="pick"', 2)])

# =====================================================================================
# Members
# =====================================================================================

mrows = []
for i, (n, e, ini, a, t, segs, p) in enumerate(MEMBERS):
    sb = ' '.join(badge(s) for s in segs[:3]) + (f' {badge("+" + str(len(segs) - 3))}' if len(segs) > 3 else '') if segs else '-'
    cls = ' class="sel"' if i == 1 else ''
    mrows.append(f'<tr{cls}><td style="width:40px">{cb(i == 1)}</td><td>{who(n, e, ini, a)}</td><td>{badge(t, "pr") if t else "-"}</td>'
                 f'<td>{sb}</td><td>{pts(p)}</td><td class="le-faint">{ic("chevron-right")}</td></tr>')
mtable = table([cb(), 'Member', 'Tier', 'Segments', 'Balance', ''], mrows)
toolbar = (f'<div class="row" style="justify-content:space-between;gap:12px;padding:12px;border-bottom:1px solid #e2e8f0">'
           f'<div class="le-in" style="max-width:384px" data-k="search">{ic("search")}<span class="ph">Search by name or email…</span></div>'
           f'<div class="row g8" data-k="bulk"><span class="le-muted" style="font-size:13px">1 selected</span>{b("Clear", "gh", size="sm")}{b("Delete selected", "d", "trash-2", "sm")}</div></div>')
pager = f'<div class="row" style="justify-content:space-between;padding:12px 16px;border-top:1px solid #e2e8f0" data-k="pager"><span class="le-muted" style="font-size:13px">Page 1 of 129</span><div class="row g8">{b("‹ Prev", "s", size="sm", extra="off")}{b("Next ›", "s", size="sm")}</div></div>'
mpage = (ph('Members', '1,284 members in the program.', b('Configure', 's', 'sliders-horizontal', key='configure') + b('New member', 'p', 'plus', key='new')) +
         card(toolbar + mtable + pager))
inner = admin(mpage, 'Members')
for n, needle in enumerate(['<div class="le-in" style="max-width:384px" data-k="search"', '<span class="le-b s" data-k="configure"', '<span class="le-b p" data-k="new"', '<span class="le-cb on"', '<div class="row g8" data-k="bulk"', '<td class="le-faint"', '<div class="row" style="justify-content:space-between;padding:12px 16px;border-top:1px solid #e2e8f0" data-k="pager"'], 1):
    inner = tag(inner, needle, n)
shot('members-list', 1280, 680, inner, 'The Members page with one member selected.',
     ['Search by name or email', 'Configure member fields', 'New member', 'Select members for bulk delete', 'Bulk actions for the selected members', 'Open a member', 'Pages of 10 members'], title='Members')

segbox = '<div style="border:1px solid #e2e8f0;border-radius:8px;padding:8px 12px;display:flex;flex-direction:column;gap:6px">' + ''.join(
    f'<div class="row g8">{cb(on)}<span>{s}</span></div>' for s, on in [('App users', False), ('Big spenders', False), ('Newsletter', True), ('VIP', False)]) + '</div>'
ndlg = dialog('New member', '<div class="le-stack">' +
              field('Name', inp('Liam Chen', cls='focus'), key='name') + field('Email', inp('liam.chen@example.com'), key='email') +
              field('Phone', inp('', '+1 555 0100'), 'optional', key='phone') + field('Segments', segbox, 'optional', key='segs') +
              field('Favourite store', inp('Harbour Street'), 'optional', key='attr') + footer('Create member') + '</div>',
              'Add a member to the loyalty program.', 24, 24, 512, overlay=False)
shot('member-new', 560, 690, ndlg, 'The New member window.')
walk('member-new', [('<div class="le-f" data-k="name"', 1), ('<div class="le-f" data-k="email"', 2), ('<div class="le-f" data-k="segs"', 3), ('<div class="le-f" data-k="attr"', 4), ('<span class="le-b p" data-k="submit"', 5)])

tile = lambda label, val: f'<div style="border-radius:8px;background:rgba(241,245,249,.6);padding:12px 14px"><div class="le-muted" style="font-size:12px">{label}</div><div style="margin-top:4px;font-size:14px" class="w5">{val}</div></div>'
profile = (f'<div class="le-back">{ic("chevron-left")}All members</div>'
           f'<div class="le-card" style="padding:24px"><div class="row" style="justify-content:space-between;align-items:flex-start;gap:16px">'
           f'<div class="row g16" style="flex:1;min-width:0">{av("MT", "violet", 56)}<div><div style="font-size:20px;font-weight:600">Maya Torres</div><div class="le-muted">maya.torres@example.com</div>'
           f'<div class="row g8" style="margin-top:8px" data-k="badges">{badge("Gold", "pr", "layers")}{badge("VIP", "n", "tag")}{badge("Newsletter", "n", "tag")}</div></div></div>'
           f'<div class="row g8" style="flex:none">{b("Copy ID", "p", "copy", "sm", key="copy")}{b("Edit", "s", "pen-line", "sm", key="edit")}{b("Delete", "dgr", "trash-2", "sm", key="del")}</div></div>'
           f'<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-top:20px" data-k="details">' +
           tile('Phone', '+1 555 0188') + tile('Email', badge('Verified', 'ok', 'circle-check') + ' <span class="le-muted" style="font-size:12px">Oct 2, 2026</span>') + tile('Favourite store', 'Harbour Street') + tile('Newsletter opt in', 'Yes') + '</div>'
           f'<div class="row g8" style="margin-top:20px;padding-top:16px;border-top:1px solid #e2e8f0"><span class="le-muted w5" style="margin-right:4px">Points:</span>'
           f'<span class="row g8" data-k="points">{b("Earn", "s", "arrow-up", "sm")}{b("Burn", "s", "arrow-down", "sm")}{b("Adjust", "s", "sparkles", "sm")}</span>'
           f'<span style="width:1px;height:24px;background:#e2e8f0;margin:0 4px"></span>{b("Redeem / assign", "p", "gift", "sm", key="redeem")}</div></div>'
           '<div class="le-stats" style="grid-template-columns:repeat(5,minmax(0,1fr))" data-k="stats">' +
           stat('Points balance', '2,450', 'database', 'blue') + stat('Lifetime earned', '3,980', 'database', 'aqua') + stat('Challenges completed', '2/3', 'target', 'violet') +
           stat('Redemptions', '4', 'gift', 'orange') + stat('Total spent', '€186.40', 'shopping-bag', 'aqua', '23 purchases') + '</div>')
inner = admin(profile, 'Members')
for n, needle in enumerate(['<div class="row g8" style="margin-top:8px" data-k="badges"', '<span class="le-b p sm" data-k="copy"', '<span class="le-b s sm" data-k="edit"', '<span class="le-b dgr sm" data-k="del"', '<span class="row g8" data-k="points"', '<span class="le-b p sm" data-k="redeem"', '<div class="le-stats"'], 1):
    inner = tag(inner, needle, n)
shot('member-profile', 1280, 580, inner, 'The top of a member\'s page: profile card and totals.',
     ['Tier and segments', 'Copy ID (this program\'s member ID)', 'Edit the profile', 'Delete the member', 'Earn, Burn and Adjust points', 'Redeem a reward or give a prize', 'Member totals'], title='Maya Torres')

edlg = dialog('Earn points', '<div class="le-stack">' + field('Points', inp('100', cls='focus'), 'before multiplier', key='pts') +
              field('Reason', inp('Birthday bonus'), 'optional', key='reason') + footer('Add points') + '</div>',
              "Awards points; the member's tier multiplier is applied automatically.", 24, 24, 512, overlay=False)
shot('points-earn', 560, 340, edlg, 'The Earn points window.')
walk('points-earn', [('<div class="le-f" data-k="pts"', 1), ('<div class="le-f" data-k="reason"', 2), ('<span class="le-b p" data-k="submit"', 3)])

rw = ''.join(f'<div class="row" style="justify-content:space-between;gap:12px;padding:12px 0;border-top:1px solid #e2e8f0"><div><b class="w6">{n}</b><div class="le-muted" style="font-size:13px">{c}</div></div>'
             f'<div class="row g8">{b("Assign free", "s", size="sm", key="free" if i == 0 else None)}{b("Redeem", "p", size="sm", key="redeem" if i == 0 else None, extra="off" if off else "")}</div></div>'
             for i, (n, c, off) in enumerate([('Free espresso', '150 pts · 42 left', False), ('Pastry of the day', '300 pts', False), ('Daybreak tote bag', '3,000 pts · 8 left', True)]))
gdlg = dialog('Rewards', f'<div class="row g8" style="padding-bottom:12px" data-k="email">{cb(True)}<span>Email free prizes to the member, with a link to claim them</span></div>{rw}',
              'Redeem a reward for points, or assign one as a free prize.', 24, 24, 672, overlay=False)
shot('grant-reward', 720, 400, gdlg, 'The Rewards window on a member\'s page.')
walk('grant-reward', [('<div class="row g8" style="padding-bottom:12px" data-k="email"', 1), ('<span class="le-b s sm" data-k="free"', 2), ('<span class="le-b p sm" data-k="redeem"', 3), ('<span class="le-b p sm off"', 4)])

chal = (f'<div style="border:1px solid #e2e8f0;border-radius:8px;padding:16px;background:#fff;margin:16px">'
        f'<div class="row" style="justify-content:space-between"><div><b class="w6">Five visits in May</b><div class="le-muted" style="font-size:13px">200 pts on completion</div></div>{badge("In progress", "pr", "zap")}</div>'
        f'<div class="row" style="justify-content:space-between;margin-top:12px;font-size:13px"><span class="le-muted">Progress</span><span class="w5">3 / 5</span></div>'
        f'<div class="le-bar" style="margin-top:6px"><i style="width:60%"></i></div><div class="le-faint" style="font-size:12px;margin-top:8px">Expires May 31, 2026</div>'
        f'<div class="row g8" style="margin-top:12px">{b("Progress", "s", "plus", "sm", key="prog")}{b("Complete", "s", "check", "sm", key="done")}<span style="flex:1"></span><span class="le-b gh ic" style="color:#d03b3b" data-k="rm">{ic("trash-2")}</span></div></div>')
cw = card(chal, 'Challenges', '', b('Assign challenge', 's', 'plus', 'sm', key='assign'), style='position:absolute;left:0;top:0;width:560px')
shot('member-challenge', 560, 320, cw, 'A challenge on a member\'s page.')
walk('member-challenge', [('<span class="le-b s sm" data-k="assign"', 1), ('<span class="le-b s sm" data-k="prog"', 2), ('<span class="le-b s sm" data-k="done"', 3), ('<span class="le-b gh ic" style="color:#d03b3b" data-k="rm"', 4)])

builtin = table(['Field', 'Type', 'Notes'], [f'<td><b class="w5">{f}</b> {badge("Built-in")}</td><td class="le-muted">{t}</td><td class="le-muted">{n}</td>' for f, t, n in [
    ('Name', 'Text', 'Required'), ('Email', 'Text', 'Required, unique'), ('Phone', 'Text', '-'),
    ('Tier', 'Reference', 'Derived from points balance'), ('Points balance', 'Number', 'Managed by points actions'), ('Segments', 'Multi-reference', 'Managed on the Segments page')]])
custom = table(['Field', 'Type', 'Default', 'Actions'], [
    f'<td><b class="w5">{f}</b><div><code class="le-key">{key}</code></div></td><td class="le-muted">{t}</td><td class="le-muted">{d}</td><td><div class="row g8">{b("Edit", "s", "pen-line", "sm", key="edit" if i == 0 else None)}{b("Delete", "dgr", "trash-2", "sm")}</div></td>'
    for i, (f, key, t, d) in enumerate([('Favourite store', 'favouriteStore', 'Dropdown: Harbour Street, Old Town, Airport', '-'), ('Newsletter opt in', 'newsletterOptIn', 'Yes / No', 'No'), ('Birthday', 'birthday', 'Date', '-')])])
conf = (f'<div class="le-back">{ic("chevron-left")}All members</div>' +
        ph('Member fields', 'Every field on a member. Built-in fields are fixed; custom attributes are yours to add, rename, and remove.') +
        card(custom, 'Custom attributes', 'Applied to every member. Always optional - a member can leave any of them empty.', b('New custom attribute', 'p', 'plus', 'sm', key='new'), key='custom'))
inner = admin(conf, 'Members')
for n, needle in enumerate(['<span class="le-b p sm" data-k="new"', '<code class="le-key"', '<span class="le-b s sm" data-k="edit"', '<span class="le-b dgr sm"'], 1):
    inner = tag(inner, needle, n)
shot('member-fields', 1280, 580, inner, 'The Member fields page, Custom attributes card.',
     ['New custom attribute', 'Internal key: what integrations use', 'Edit name and default', 'Delete the attribute and its values'], title='Member fields')

adlg = dialog('New custom attribute', '<div class="le-stack">' +
              field('Name', inp('Favourite store', cls='focus'), help_='Internal key: favouriteStore', key='name') +
              field('Type', sel('Dropdown'), key='type') +
              field('Options', '<div class="le-in" style="gap:6px;flex-wrap:wrap">' + ''.join(badge(o, 'pr') for o in ['Harbour Street', 'Old Town', 'Airport']) + '</div>', help_='Press Enter or comma to add each choice.', key='opts') +
              field('Default value', sel('No default'), 'optional', 'Applied to every existing member as soon as you create this attribute.', key='def') +
              footer('Create attribute') + '</div>', 'Adds a field to every member. Custom attributes are always optional.', 24, 24, 512, overlay=False)
shot('attribute-dialog', 560, 560, adlg, 'The New custom attribute window.')
walk('attribute-dialog', [('<div class="le-f" data-k="name"', 1), ('<div class="le-f" data-k="type"', 2), ('<div class="le-f" data-k="opts"', 3), ('<div class="le-f" data-k="def"', 4), ('<span class="le-b p" data-k="submit"', 5)])

# =====================================================================================
# Segments, rewards, products, challenges, tiers
# =====================================================================================


def seg_card(name, count, desc, color, first=False):
    return (f'<div class="le-card" style="padding:20px;display:flex;flex-direction:column">'
            f'<div class="row g12"><span class="le-chip" style="background:{color}22;color:{color}">{ic("tag")}</span>'
            f'<div style="flex:1;min-width:0"><b class="w6">{name}</b><div class="le-faint" style="font-size:12px">{count}</div></div>'
            f'<span class="le-b gh ic"{k("edit" if first else None)}>{ic("pen-line")}</span><span class="le-b gh ic" style="color:#d03b3b"{k("del" if first else None)}>{ic("trash-2")}</span></div>'
            f'<div class="le-muted" style="font-size:13px;margin-top:12px;height:40px">{desc}</div>'
            f'<div style="margin-top:16px;padding-top:16px;border-top:1px solid #e2e8f0">{b("Assign members", "s", "users", "sm", key="assign" if first else None)}</div></div>')


segs = (ph('Segments', 'Named member cohorts you can assign members to and target with challenges.', b('New segment', 'p', 'plus', key='new')) +
        '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px">' +
        seg_card('Big spenders', '96 members', 'Members who spent over €200 this year', '#eb6834') +
        seg_card('Newsletter', '842 members', 'Opted in to the monthly email', '#2a78d6') +
        seg_card('VIP', '58 members', 'Hand-picked regulars', '#5b4bd6', True) + '</div>')
inner = admin(segs, 'Segments')
for n, needle in enumerate(['<span class="le-b p" data-k="new"', '<span class="le-b gh ic" data-k="edit"', '<span class="le-b gh ic" style="color:#d03b3b" data-k="del"', '<span class="le-b s sm" data-k="assign"'], 1):
    inner = tag(inner, needle, n)
shot('segments-page', 1280, 580, inner, 'The Segments page.', ['New segment', 'Edit', 'Delete', 'Assign members'], title='Segments')

amem = ''.join(f'<div class="row g8" style="padding:10px 4px;border-top:1px solid #e2e8f0">{cb(on)}<span>{n} · <span class="le-muted">{e}</span></span></div>'
               for n, e, on in [('Liam Chen', 'liam.chen@example.com', True), ('Sofia Rossi', 'sofia.rossi@example.com', True), ('Aisha Khan', 'aisha.khan@example.com', False)])
asg = dialog('Assign members', f'<div class="le-in" data-k="search">{ic("search")}<span class="ph">Search members…</span></div>'
             f'<div class="row g8" style="padding:12px 4px;border-bottom:1px solid #e2e8f0;margin-top:8px" data-k="all">{cb()}<span class="w5">Select all</span></div>{amem}'
             f'<div class="row" style="justify-content:space-between;border-top:1px solid #e2e8f0;padding-top:12px;margin-top:4px"><span class="le-faint" style="font-size:12px">2 selected</span>{b("Assign (2)", "p", key="submit")}</div>',
             'Add members to "VIP".', 24, 24, 640, overlay=False)
shot('assign-members', 688, 400, asg, 'The Assign members window for a segment.')
walk('assign-members', [('<div class="le-in" data-k="search"', 1), ('<div class="row g8" style="padding:12px 4px;border-bottom:1px solid #e2e8f0;margin-top:8px" data-k="all"', 2), ('<span class="le-cb on"', 3), ('<span class="le-b p" data-k="submit"', 4)])

RMENU = ('<div class="le-menu" style="right:16px;top:44px;width:192px;z-index:5">'
         f'<div class="le-mi"><span class="le-faint">{ic("ban")}</span>Deactivate</div>'
         f'<div class="le-mi"><span class="le-faint">{ic("copy")}</span>Copy ID</div>'
         f'<div class="le-mi"><span class="le-faint">{ic("pen-line")}</span>Edit</div>'
         f'<div class="le-mi" style="color:#d03b3b">{ic("trash-2").replace("{{", "{{")}Delete</div></div>')
rrows = []
for i, (n, d, c, st, active) in enumerate([('Free espresso', 'Any single espresso drink', '150', '42', True), ('Pastry of the day', 'One pastry from the counter', '300', '<span class="le-faint">Unlimited</span>', True),
                                           ('Daybreak tote bag', 'Canvas bag with our logo', '3,000', '<span style="color:#d03b3b" class="w5">Out of stock</span>', True), ('Summer cold brew', 'Seasonal, back in June', '200', '<span class="le-faint">Unlimited</span>', False)]):
    status = badge('Active', 'ok', 'circle-check') if active else badge('Inactive', 'n', 'ban')
    rrows.append(f'<td><b class="w5">{n}</b><div class="le-muted" style="font-size:12px">{d}</div></td><td>{pts(c)}</td><td>{st}</td><td>{status}</td>'
                 f'<td style="position:relative"><span class="le-b gh ic"{k("menu" if i == 0 else None)}>{ic("ellipsis-vertical")}</span>{RMENU if i == 0 else ""}</td>')
rpage = ph('Rewards', '4 rewards · 3 active', b('New reward', 'p', 'plus', key='new')) + card(table(['Reward', 'Cost', 'Stock', 'Status', 'Actions'], rrows))
inner = admin(rpage, 'Rewards')
for n, needle in enumerate(['<span class="le-b p" data-k="new"', '<span class="le-b gh ic" data-k="menu"', '<div class="le-menu"', '<span style="color:#d03b3b" class="w5"'], 1):
    inner = tag(inner, needle, n)
shot('rewards-page', 1280, 580, inner, 'The Rewards page with a reward\'s actions menu open.', ['New reward', 'Actions menu', 'Activate or Deactivate, Copy ID, Edit, Delete', 'Stock ran out'], title='Rewards')

rdlg = dialog('New reward', '<div class="le-stack">' + field('Name', inp('Free espresso', cls='focus'), key='name') +
              field('Description', inp('Any single espresso drink', cls='ta', style='min-height:76px;align-items:flex-start'), key='desc') +
              '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">' + field('Points cost', inp('150'), '> 0', key='cost') + field('Stock', inp('50'), help_='Leave blank for unlimited', key='stock') + '</div>' +
              f'<div class="row g8" data-k="active">{cb(True)}<span class="w5" style="font-size:13px">Active (available to redeem)</span></div>' + footer('Create reward') + '</div>',
              'Add a redeemable reward to the catalog.', 24, 24, 512, overlay=False)
shot('reward-dialog', 560, 520, rdlg, 'The New reward window.')
walk('reward-dialog', [('<div class="le-f" data-k="name"', 1), ('<div class="le-f" data-k="cost"', 2), ('<div class="le-f" data-k="stock"', 3), ('<div class="row g8" data-k="active"', 4), ('<span class="le-b p" data-k="submit"', 5)])

prow = []
for i, (n, d, p, c, active) in enumerate([('Ethiopia Yirgacheffe, 250g', 'Whole beans, floral and bright', '€14.50', 'coffee', True), ('House blend, 1kg', 'Our everyday roast', '€32.00', 'coffee', True),
                                          ('Ceramic cup', 'Hand-glazed, 300 ml', '€18.00', 'merch', True), ('Holiday gift box', 'Back in December', '€45.00', '<span class="le-faint">-</span>', False)]):
    status = badge('Active', 'ok', 'circle-check') if active else badge('Inactive', 'n', 'ban')
    prow.append(f'<td><b class="w5">{n}</b><div class="le-muted" style="font-size:12px">{d}</div></td><td class="w5">{p}</td><td class="le-muted">{c}</td><td>{status}</td><td><span class="le-b gh ic"{k("menu" if i == 0 else None)}>{ic("ellipsis-vertical")}</span></td>')
ppage = ph('Products', '4 products · 3 active', b('New product', 'p', 'plus', key='new')) + card(table(['Product', 'Price', 'Category', 'Status', 'Actions'], prow))
inner = admin(ppage, 'Products')
for n, needle in enumerate(['<span class="le-b p" data-k="new"', '<span class="le-b gh ic" data-k="menu"'], 1):
    inner = tag(inner, needle, n)
shot('products-page', 1280, 580, inner, 'The Products page.', ['New product', 'Actions menu: Activate or Deactivate, Copy ID, Edit, Delete'], title='Products')


def chal_card(name, desc, active, badges, segs, first=False):
    st = badge('Active', 'ok', 'circle-check') if active else badge('Inactive', 'n', 'ban')
    sg = ' '.join(badge(s, 'pr') for s in segs) if segs else '<span class="le-muted" style="font-size:13px">Not assigned to any segment yet.</span>'
    return (f'<div class="le-card" style="padding:20px"><div class="row g12" style="align-items:flex-start"><span class="le-chip a-aqua">{ic("target")}</span>'
            f'<div style="flex:1"><b class="w6">{name}</b><div class="le-muted" style="font-size:13px">{desc}</div></div>{st}</div>'
            f'<div class="row g8" style="margin-top:16px;flex-wrap:wrap"{k("badges" if first else None)}>{badges}</div>'
            f'<div style="margin-top:16px"><div class="le-muted row g4" style="font-size:11px;letter-spacing:.05em;text-transform:uppercase"><span class="le-mini" style="width:12px;height:12px">{ic("tag")}</span>Assigned segments</div><div class="row g8" style="margin-top:8px"{k("segs" if first else None)}>{sg}</div></div>'
            f'<div class="row" style="justify-content:space-between;margin-top:20px;padding-top:16px;border-top:1px solid #e2e8f0">{b("Assign to segment", "s", "users", "sm", key="assign" if first else None)}'
            f'<div class="row g4"><span class="le-b gh ic">{ic("copy")}</span><span class="le-b gh ic">{ic("pen-line")}</span><span class="le-b gh ic" style="color:#d03b3b">{ic("trash-2")}</span></div></div></div>')


cpage = (ph('Challenges', '2 challenges · 2 active', b('New challenge', 'p', 'plus', key='new')) +
         '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">' +
         chal_card('Five visits in May', 'Order five times during May', True, badge('Target 5') + ' ' + badge('200 pts', 'pr') + ' ' + badge('Free espresso', 'wa') + ' ' + badge('Expires May 31, 2026'), ['VIP'], True) +
         chal_card('Try three origins', 'Buy three different single-origin bags', True, badge('Target 3') + ' ' + badge('300 pts', 'pr') + ' ' + badge('30d after assignment'), []) + '</div>')
inner = admin(cpage, 'Challenges')
for n, needle in enumerate(['<span class="le-b p" data-k="new"', '<div class="row g8" style="margin-top:16px;flex-wrap:wrap" data-k="badges"', '<div class="row g8" style="margin-top:8px" data-k="segs"', '<span class="le-b s sm" data-k="assign"'], 1):
    inner = tag(inner, needle, n)
shot('challenges-page', 1280, 580, inner, 'The Challenges page.', ['New challenge', 'Target, points, prize and expiry', 'Segments it was bulk-assigned to', 'Assign to segment'], title='Challenges')

cdlg = dialog('New challenge', '<div class="le-stack">' + field('Name', inp('Five visits in May', cls='focus'), key='name') + field('Description', inp('', 'Optional details'), key='desc') +
              '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">' + field('Target', inp('5'), help_='Progress needed to complete', key='target') + field('Reward points', inp('200'), help_='Granted on completion', key='pts') + '</div>' +
              field('Prize reward', sel('Free espresso'), help_='Optional - assigned on completion', key='prize') +
              '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">' + field('Expires at', inp('05/31/2026, 11:59 PM'), help_='Fixed deadline for everyone / cutoff for new assignments', key='at') +
              field('Expires after (days)', inp('&nbsp;'), help_='Expires N days after being assigned to a member — leave blank to use the fixed date above for everyone.', key='days') + '</div>' +
              f'<div class="row g8">{cb(True)}<span class="w5" style="font-size:13px">Active (can be assigned)</span></div>' + footer('Create challenge') + '</div>',
              'Define a goal members can complete to earn points or a prize.', 24, 24, 640, overlay=False)
shot('challenge-dialog', 688, 700, cdlg, 'The New challenge window.')
walk('challenge-dialog', [('<div class="le-f" data-k="target"', 1), ('<div class="le-f" data-k="pts"', 2), ('<div class="le-f" data-k="prize"', 3), ('<div class="le-f" data-k="at"', 4), ('<div class="le-f" data-k="days"', 5)])


def tier_card(name, count, rank, rate, conds, first=False):
    chips = ' <span class="le-faint" style="font-size:12px">and</span> '.join(f'<span class="le-cc">{c}</span>' for c in conds) if conds else '<span class="le-muted" style="font-size:13px">Every member qualifies</span>'
    boxes = ''.join(f'<div style="border-radius:8px;background:#f1f5f9;padding:10px 12px"><div class="le-muted" style="font-size:12px">{lbl}</div><div class="w6">{v}</div></div>' for lbl, v in [('Rank', rank), ('Earn rate', rate + '×')])
    return (f'<div class="le-card" style="padding:20px"><div class="row g12"><span class="le-chip a-yellow">{ic("layers")}</span><div style="flex:1"><b class="w6">{name}</b><div class="le-faint" style="font-size:12px">{count}</div></div>'
            f'<span class="le-b gh ic"{k("edit" if first else None)}>{ic("pen-line")}</span><span class="le-b gh ic" style="color:#d03b3b">{ic("trash-2")}</span></div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:20px"{k("rank" if first else None)}>{boxes}</div>'
            f'<div class="row" style="flex-wrap:wrap;gap:6px;margin-top:16px;min-height:52px;align-content:flex-start"{k("conds" if first else None)}>{chips}</div>'
            f'<div style="margin-top:12px">{badge("×" + rate + " points on earn", "pr")}</div></div>')


tpage = (ph('Tiers', 'Points, purchase spend, segments and custom attributes, combined however you like, applying an earn-rate multiplier.', b('New tier', 'p', 'plus', key='new')) +
         '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px">' +
         tier_card('Bronze', '701 members', '0', '1', []) +
         tier_card('Silver', '342 members', '1', '1.2', ["Member's points balance is at least 500"]) +
         tier_card('Gold', '128 members', '2', '1.5', ["Member's points balance is at least 2000", "Member's segments include VIP"], True) + '</div>')
inner = admin(tpage, 'Tiers')
for n, needle in enumerate(['<span class="le-b p" data-k="new"', '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:20px" data-k="rank"', '<div class="row" style="flex-wrap:wrap;gap:6px;margin-top:16px;min-height:52px;align-content:flex-start" data-k="conds"', '<span class="le-b gh ic" data-k="edit"'], 1):
    inner = tag(inner, needle, n)
shot('tiers-page', 1280, 580, inner, 'The Tiers page with three tiers.', ['New tier', 'Rank and earn rate', 'Conditions: all must match', 'Edit'], title='Tiers')

crow = lambda f, o, v, key=None: f'<div style="display:grid;grid-template-columns:1.3fr 1fr 1fr auto;gap:8px;align-items:center"{k(key)}>{sel(f)}{sel(o)}{inp(v)}<span class="le-b gh ic">{ic("x")}</span></div>'
tdlg = dialog('New tier', '<div class="le-stack">' + field('Name', inp('Gold', cls='focus'), key='name') +
              '<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px">' + field('Rank', inp('2'), 'highest tried first', key='rank') + field('Multiplier', inp('1.5'), '> 0', key='mult') + '</div>' +
              field('Conditions', '<div class="le-stack" style="gap:8px">' + crow('Points balance', 'is at least', '2000', 'c1') + crow('Segments', 'include', 'VIP') + '</div>' +
                    '<div style="margin-top:8px">' + b('Add condition', 'gh', 'plus', 'sm', key='add') + '</div>',
                    help_='All must match. No conditions means every member qualifies - useful for a catch-all lowest tier.', key='conds') +
              footer('Create tier') + '</div>', 'Members meeting every condition below earn at this multiplier.', 24, 24, 640, overlay=False)
shot('tier-dialog', 688, 540, tdlg, 'The New tier window with two conditions.')
walk('tier-dialog', [('<div class="le-f" data-k="rank"', 1), ('<div class="le-f" data-k="mult"', 2), ('<div style="display:grid;grid-template-columns:1.3fr 1fr 1fr auto;gap:8px;align-items:center" data-k="c1"', 3), ('<span class="le-b gh sm" data-k="add"', 4), ('<span class="le-b p" data-k="submit"', 5)])

# =====================================================================================
# Events
# =====================================================================================

erows = []
for i, (n, d, key, attrs, rules, active) in enumerate([
        ('Order placed', 'Sent by the till and the app after payment', 'orderPlaced', ['Amount', 'Channel'], '2 active', True),
        ('App opened', 'Sent once a day by the mobile app', 'appOpened', [], '1 active · 1 paused', True),
        ('Review written', 'From the review widget', 'reviewWritten', ['Stars'], 'No rules yet', False)]):
    ab = ' '.join(badge(a) for a in attrs) if attrs else '-'
    status = badge('Active', 'ok', 'circle-check') if active else badge('Inactive', 'n', 'ban')
    rl = f'<span class="le-muted">{rules}</span>' if rules.startswith('No') else rules
    erows.append(f'<td><b class="w5">{n}</b><div class="le-muted" style="font-size:13px">{d}</div></td><td><code class="le-key"{k("key" if i == 0 else None)}>{key}</code></td><td>{ab}</td><td>{rl}</td><td>{status}</td><td class="le-faint">{ic("chevron-right")}</td>')
epage = (ph('Events', 'Things members do in your systems. Rules decide what each event earns.',
            b('Logs', 's', 'clock', key='logs') + b('Test event', 's', 'zap', key='test') + b('New event', 'p', 'plus', key='new')) +
         card(table(['Event', 'API key', 'Attributes', 'Rules', 'Status', ''], erows)))
inner = admin(epage, 'Events')
for n, needle in enumerate(['<span class="le-b s" data-k="logs"', '<span class="le-b s" data-k="test"', '<span class="le-b p" data-k="new"', '<code class="le-key" data-k="key"'], 1):
    inner = tag(inner, needle, n)
shot('events-list', 1280, 580, inner, 'The Events page with three events.', ['Event logs', 'Test an event', 'New event', 'The API key your systems send'], title='Events')

attr_row = lambda lbl, typ, key, extra='': (f'<div style="border:1px solid #e2e8f0;border-radius:8px;padding:8px"><div style="display:grid;grid-template-columns:1.4fr 1fr auto;gap:8px;align-items:center">{inp(lbl)}{sel(typ)}<span class="le-b gh ic">{ic("x")}</span></div>{extra}'
                                           f'<div class="le-mono le-faint" style="font-size:11px;margin-top:4px">{key}</div></div>')
evdlg = dialog('New event', '<div class="le-stack">' + field('Name', inp('Order placed', cls='focus'), help_='API key: orderPlaced. Your system sends this as "type".', key='name') +
               field('Description', inp('', 'Who sends it, and when'), 'Optional', key='desc') +
               field('Attributes', '<div class="le-stack" style="gap:8px">' + attr_row('Amount', 'Number', 'amount') + attr_row('Channel', 'Dropdown', 'channel', '<div style="margin-top:8px">' + inp('App, Store') + '</div>') + '</div>' +
                     '<div style="margin-top:8px">' + b('Add attribute', 'gh', 'plus', 'sm', key='add') + '</div>',
                     help_='Data your system sends with the event. Rules can check these values or copy them onto the member.', key='attrs') +
               footer('Create event') + '</div>', 'Something a member does that your systems report, such as placing an order.', 24, 24, 640, overlay=False)
shot('event-dialog', 688, 660, evdlg, 'The New event window with two attributes.')
walk('event-dialog', [('<div class="le-f" data-k="name"', 1), ('<div class="le-f" data-k="attrs"', 2), ('<span class="le-b gh sm" data-k="add"', 3), ('<span class="le-b p" data-k="submit"', 4)])

rule1 = (f'<div style="padding:16px 20px"><div class="row g12"><span class="le-sw2 on"{k("rsw")}></span><b class="w5">Points per euro</b><span style="flex:1"></span>'
         f'<span class="le-b gh ic"{k("redit")}>{ic("pen-line")}</span><span class="le-b gh ic" style="color:#d03b3b">{ic("trash-2")}</span></div>'
         f'<div class="row g8" style="margin-top:10px"><span class="le-kw">If</span><span class="le-muted" style="font-size:13px">Always, on every event</span></div>'
         f'<div class="row g8" style="margin-top:6px"><span class="le-kw">Then</span><span class="le-ec">{ic("database")}Earn points equal to the event\'s amount</span></div></div>')
rule2 = (f'<div style="padding:16px 20px;border-top:1px solid #e2e8f0"><div class="row g12"><span class="le-sw2 on"></span><b class="w5">Big basket bonus</b>{badge("Once per member", "n", "clock")}<span style="flex:1"></span>'
         f'<span class="le-b gh ic">{ic("pen-line")}</span><span class="le-b gh ic" style="color:#d03b3b">{ic("trash-2")}</span></div>'
         f'<div class="row g8" style="margin-top:10px"><span class="le-kw">If</span><span class="le-cc">Amount is at least 50</span><span class="le-faint" style="font-size:12px">and</span><span class="le-cc">Channel is App</span></div>'
         f'<div class="row g8" style="margin-top:6px"><span class="le-kw">Then</span><span class="le-ec">{ic("gift")}Give reward "Free espresso"</span><span class="le-ec">{ic("tag")}Add member to segment "Big spenders"</span></div></div>')
attrs_card = card('<div style="padding:8px 20px">' + ''.join(f'<div class="row" style="justify-content:space-between;padding:8px 0"><div><div class="w5" style="font-size:14px">{l}</div><div class="le-mono le-faint" style="font-size:12px">{kk}</div></div>{badge(t)}</div>' for l, kk, t in [('Amount', 'amount', 'Number'), ('Channel', 'channel', 'Dropdown')]) + '</div>',
                  'Attributes', 'Data sent with each event')
send_card = card('<pre class="le-mono" style="margin:0;background:#f1f5f9;padding:16px 20px;font-size:11px;line-height:1.6;white-space:pre-wrap;color:#0f172a">curl -X POST $API_URL/events \\\n  -H "Authorization: Bearer $API_TOKEN" \\\n  -H "X-Program-Id: daybreak-coffee" \\\n  -d \'{ "memberId": "…", "type": "orderPlaced", … }\'</pre>',
                 'Send this event', 'POST it from your system. The response lists what the rules did.', f'<span class="le-b gh ic">{ic("copy")}</span>', key='send')
edetail = (f'<div class="le-back">{ic("chevron-left")}All events</div>'
           f'<div class="row" style="justify-content:space-between;gap:16px"><div class="row g12"><span class="le-chip" style="width:44px;height:44px;background:rgba(91,75,214,.15);color:#5b4bd6">{ic("zap")}</span>'
           f'<div><div style="font-size:24px;font-weight:600;letter-spacing:-.02em">Order placed</div><div class="le-muted" style="font-size:14px">Sent by the till and the app after payment</div></div>'
           f'<span class="le-mono le-muted" style="font-size:12px;background:#f1f5f9;border-radius:6px;padding:4px 8px"{k("key")}>orderPlaced</span></div>'
           f'<div class="row g8"><span class="row g8" style="margin-right:4px"{k("on")}><span class="le-sw2 on"></span><span class="w5" style="font-size:14px">Active</span></span>'
           f'{b("Test event", "s", "zap", key="test")}{b("Edit event", "s", "pen-line", key="edit")}<span class="le-b gh ic">{ic("copy")}</span><span class="le-b gh ic" style="color:#d03b3b">{ic("trash-2")}</span></div></div>'
           f'<div style="display:grid;grid-template-columns:2fr 1fr;gap:24px;align-items:start">' +
           card(rule1 + rule2, 'Rules', "Every active rule whose conditions match runs. Their order doesn't matter.", b('New rule', 'p', 'plus', 'sm', key='newrule'), key='rules') +
           f'<div class="le-stack" style="gap:24px">{attrs_card}{send_card}</div></div>')
inner = admin(edetail, 'Events')
for n, needle in enumerate(['<span class="row g8" style="margin-right:4px" data-k="on"', '<span class="le-mono le-muted" style="font-size:12px;background:#f1f5f9;border-radius:6px;padding:4px 8px" data-k="key"', '<span class="le-b p sm" data-k="newrule"', '<span class="le-sw2 on" data-k="rsw"', '<span class="le-b gh ic" data-k="redit"', '<span class="le-b s" data-k="test"', '<div class="le-card" data-k="send"'], 1):
    inner = tag(inner, needle, n)
shot('event-detail', 1280, 700, inner, 'An event\'s page with two rules.',
     ['Turn the event on or off', 'API key: select it to copy', 'New rule', 'Pause or turn on a rule', 'Edit a rule', 'Send a test event', 'A ready request for your developers'], title='Order placed')

clause = lambda kw, body, hint='', key=None: (f'<div style="display:grid;grid-template-columns:72px 1fr;gap:12px;align-items:start"{k(key)}><div style="padding-top:6px"><span class="le-pill">{kw}</span></div>'
                                              f'<div>{"<div class=w6 style=font-size:13px;margin-bottom:8px>" + hint + "</div>" if hint else ""}{body}</div></div>')
when = f'<div class="le-in dash" style="height:40px"><span style="color:#5b4bd6">{ic("zap")}</span><b class="w6">Order placed</b><span class="le-muted">happens</span></div>'
cond = f'<div style="display:grid;grid-template-columns:1.3fr 1fr 1fr auto;gap:8px;align-items:center">{sel("Amount")}{sel("is at least")}{inp("50")}<span class="le-b gh ic">{ic("x")}</span></div>'
eff1 = f'<div style="display:grid;grid-template-columns:1.3fr 2fr auto;gap:8px;align-items:center">{sel("Give a reward")}{sel("Free espresso")}<span class="le-b gh ic">{ic("x")}</span></div>'
eff2 = f'<div style="display:grid;grid-template-columns:1.3fr 2fr auto;gap:8px;align-items:center;margin-top:8px">{sel("Add to segment")}{sel("Big spenders")}<span class="le-b gh ic">{ic("x")}</span></div>'
red = dialog('New rule', '<div class="le-stack" style="gap:20px">' + field('Rule name', inp('Big basket bonus', cls='focus'), key='name') +
             clause('When', when) +
             clause('If', cond + '<div style="margin-top:8px">' + b('Add condition', 'gh', 'plus', 'sm') + '</div>', 'All of these must be true', 'if') +
             clause('Then', eff1 + eff2 + '<div style="margin-top:8px">' + b('Add effect', 'gh', 'plus', 'sm') + '</div>', 'All of these happen', 'then') +
             clause('Limit', sel('Only the first time per member'), '', 'limit') +
             f'<div class="le-prev" data-k="prev">{ic("sparkles")}<span><b>In plain words: </b>When "Order placed" happens, if amount is at least 50, then give reward "Free espresso" and add member to segment "Big spenders", only the first time per member.</span></div>' +
             footer('Create rule') + '</div>', 'Decide what a "Order placed" event does for the member.', 24, 24, 672, overlay=False)
shot('rule-editor', 720, 800, red, 'The New rule window.')
walk('rule-editor', [('<div class="le-f" data-k="name"', 1), ('<div style="display:grid;grid-template-columns:72px 1fr;gap:12px;align-items:start" data-k="if"', 2),
                     ('<div style="display:grid;grid-template-columns:72px 1fr;gap:12px;align-items:start" data-k="then"', 3), ('<div style="display:grid;grid-template-columns:72px 1fr;gap:12px;align-items:start" data-k="limit"', 4),
                     ('<div class="le-prev"', 5), ('<span class="le-b p" data-k="submit"', 6)])

tdl = dialog('Test an event', '<div class="le-stack">' + field('Event', sel('Order placed'), key='ev') + field('Member', sel('Maya Torres · maya.torres@example.com'), key='mem') +
             field('Amount', inp('64.50'), 'optional', key='a1') + field('Channel', sel('App'), 'optional') + footer('Send test event') + '</div>',
             'Choose an event and a member to send it for. Its rules run right away.', 24, 24, 512, overlay=False)
shot('test-event', 560, 520, tdl, 'The Test an event window.')
walk('test-event', [('<div class="le-f" data-k="ev"', 1), ('<div class="le-f" data-k="mem"', 2), ('<div class="le-f" data-k="a1"', 3), ('<span class="le-b p" data-k="submit"', 4)])

ok = lambda t: f'<div class="row g4" style="font-size:13px"><span class="le-mini" style="color:#0ca30c">{ic("circle-check")}</span>{t}</div>'
skip = lambda t: f'<div class="le-muted" style="font-size:13px">Skipped: {t}</div>'
lrows = [
    f'<td style="vertical-align:top"><b class="w6">Order placed</b><div class="le-muted" style="font-size:13px">Amount 64.5 · Channel App</div></td><td style="vertical-align:top"><b class="w5" style="color:#5b4bd6">Maya Torres</b><div class="le-muted" style="font-size:12px">maya.torres@example.com</div></td>'
    f'<td style="vertical-align:top"{k("what")}>{ok("Earned 97 points")}{ok("Gave reward &quot;Free espresso&quot;")}{skip("Already in &quot;Big spenders&quot;")}</td><td class="le-muted" style="vertical-align:top">Oct 23, 2026, 3:04 PM</td>',
    f'<td style="vertical-align:top"><b class="w6">App opened</b><div class="le-muted" style="font-size:13px">-</div></td><td style="vertical-align:top"><b class="w5" style="color:#5b4bd6">Liam Chen</b><div class="le-muted" style="font-size:12px">liam.chen@example.com</div></td>'
    f'<td style="vertical-align:top" class="le-muted">No rules matched</td><td class="le-muted" style="vertical-align:top">Oct 23, 2026, 2:51 PM</td>',
    f'<td style="vertical-align:top"><b class="w6">Order placed</b><div class="le-muted" style="font-size:13px">Amount 12 · Channel Store</div></td><td style="vertical-align:top"><b class="w5" style="color:#5b4bd6">Sofia Rossi</b><div class="le-muted" style="font-size:12px">sofia.rossi@example.com</div></td>'
    f'<td style="vertical-align:top">{ok("Earned 12 points")}</td><td class="le-muted" style="vertical-align:top">Oct 23, 2026, 1:17 PM</td>']
lpage = (f'<div class="le-back">{ic("chevron-left")}All events</div>' +
         ph('Event logs', 'Every event received in this program, and what its rules did.', sel('All events', style='width:224px')) +
         card(table(['Event', 'Member', 'What happened', 'When'], lrows)))
inner = admin(lpage, 'Events')
for n, needle in enumerate(['<div class="le-in sel" style="width:224px"', '<td style="vertical-align:top" data-k="what"'], 1):
    inner = tag(inner, needle, n)
shot('event-logs', 1280, 580, inner, 'The Event logs page.', ['Filter by event', 'What the rules did: applied and skipped effects'], title='Event logs')

# =====================================================================================
# Member app (MemberShell: 390 wide phone layout)
# =====================================================================================

MTABS = [('Home', 'house'), ('Products', 'shopping-bag'), ('Wallet', 'wallet'), ('Account', 'user')]


def phone(body, active, left=0):
    tabs = ''.join(f'<div class="ma-tab{" on" if n == active else ""}"{k("tab-" + n.lower())}>{ic(i)}<span>{n}</span></div>' for n, i in MTABS)
    return (f'<div class="ma-phone" style="left:{left}px"><div class="ma-head"{k("head")}>{mark("DC", "orange", 32)}<b>Daybreak Coffee</b><span class="out"{k("out")}>{ic("log-out")}</span></div>'
            f'<div class="ma-body">{body}</div><div class="ma-tabs"{k("tabs")}>{tabs}</div></div>')


def mph(title, desc):
    return f'<div><div style="font-size:24px;font-weight:600;letter-spacing:-.02em">{title}</div><div class="le-muted" style="font-size:14px;margin-top:4px">{desc}</div></div>'


prize_rows = ''.join(f'<div class="ma-row"><span class="le-chip a-orange" style="width:36px;height:36px">{ic("gift")}</span><div style="flex:1;min-width:0"><b class="w5">{n}</b><div class="le-faint" style="font-size:12px">{d}</div></div>{a}</div>'
                     for n, d, a in [('Free espresso', 'Oct 21, 2026', b('Claim', 'p', size='sm', key='claim')), ('Pastry of the day', 'Oct 3, 2026', badge('Claimed', 'ok', 'circle-check'))])
wallet = (mph('Wallet', "Your points and the prizes you've won.") + stat('Points balance', '2,450', 'database', 'yellow', key='bal') +
          card(prize_rows, 'Prizes', "Prizes you've won. Claim them here or from your email.", key='prizes'))
inner = phone(wallet, 'Wallet')
for n, needle in enumerate(['<div class="ma-head"', '<div class="le-stat " data-k="bal"', '<span class="le-b p sm" data-k="claim"', '<div class="ma-tabs"', '<span class="out"'], 1):
    inner = tag(inner, needle, n)
shot('tour-member', 390, 760, inner, 'The member app on the Wallet tab.',
     ['The program\'s logo and name', 'Points balance in this program', 'Claim a prize', 'Tabs: Home, Products, Wallet, Account', 'Sign out'])

inner = phone(wallet, 'Wallet')
inner = tag(inner, '<div class="le-stat " data-k="bal"', 1)
inner = tag(inner, '<div class="le-card" data-k="prizes"', 2)
inner = tag(inner, '<span class="le-b p sm" data-k="claim"', 3)
shot('m-wallet', 390, 760, inner, 'The Wallet tab.', ['Points balance', 'Prizes assigned to you', 'Claim'])

home = card('<div style="padding:20px;display:flex;flex-direction:column;gap:12px"><div class="w5" style="font-size:13px">Campaign URL</div>' +
            inp('https://games.example.com/spin', cls='focus') + b('Open campaign', 'p', 'target', size='full', key='open') + '</div>', key='launch')
inner = phone(home, 'Home')
inner = tag(inner, '<div class="le-in focus"', 1)
inner = tag(inner, '<span class="le-b p full" data-k="open"', 2)
frame = (f'<div class="ma-phone" style="left:430px"><div class="ma-head">{mark("DC", "orange", 32)}<b>Daybreak Coffee</b><span class="out">{ic("log-out")}</span></div>'
         f'<div style="position:absolute;left:0;right:0;top:56px;bottom:72px;background:linear-gradient(160deg,#fde68a,#fb923c);display:flex;align-items:center;justify-content:center;color:#7c2d12;font-size:22px;font-weight:700">Spin to win</div>'
         f'<div style="position:absolute;right:12px;top:68px;display:flex;gap:8px"><span class="le-b s ic" style="border-radius:50%"{k("reload")}>{ic("rotate-cw")}</span><span class="le-b s ic" style="border-radius:50%"{k("close")}>{ic("x")}</span></div>'
         f'<div class="ma-tabs">' + ''.join(f'<div class="ma-tab{" on" if n == "Home" else ""}">{ic(i)}<span>{n}</span></div>' for n, i in MTABS) + '</div></div>')
frame = tag(frame, '<span class="le-b s ic" style="border-radius:50%" data-k="reload"', 3)
frame = tag(frame, '<span class="le-b s ic" style="border-radius:50%" data-k="close"', 4)
shot('m-home', 820, 640, inner + frame, 'The Home tab before and after opening a campaign.', ['Paste the campaign link', 'Open campaign', 'Reload campaign', 'Close campaign'])

grid = '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:16px">' + ''.join(
    f'<div style="border:1px solid #e2e8f0;border-radius:12px;padding:10px 16px;display:flex;justify-content:space-between;align-items:flex-end;gap:8px"><div><div class="w5" style="font-size:12px">{n}</div><div class="w6" style="font-size:14px">{p}</div></div>{b("Buy", "p", size="xs", key="buy" if i == 0 else None)}</div>'
    for i, (n, p) in enumerate([('Ethiopia Yirgacheffe, 250g', '€14.50'), ('House blend, 1kg', '€32.00'), ('Ceramic cup', '€18.00')])) + '</div>'
prods = (mph('Products', 'Browse and buy with your card on file.') +
         f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px"{k("stats")}>' + stat('Spent (7d)', '€46.50', 'database', 'yellow', '2 purchases', 'sm') + stat('Total spent', '€186.40', 'shopping-bag', 'aqua', '23 purchases all-time', 'sm') + '</div>' +
         f'<div class="le-tabs"{k("tabs2")}><span class="on">Catalogue</span><span>Purchase history</span></div>' + card(grid))
inner = phone(prods, 'Products')
for n, needle in enumerate(['<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px" data-k="stats"', '<div class="le-tabs"', '<span class="le-b p xs" data-k="buy"'], 1):
    inner = tag(inner, needle, n)
shot('m-products', 390, 760, inner, 'The Products tab.', ['Spend in the last 7 days and in total', 'Catalogue and Purchase history', 'Buy one'])

acct = (mph('Account', 'Your profile and program.') +
        f'<div class="ma-tier"{k("tier")}><div class="ring">{ic("award")}</div><div style="flex:1"><div style="font-size:12px;letter-spacing:.06em;text-transform:uppercase;opacity:.85">Your tier</div><div style="font-size:20px;font-weight:600">Gold</div></div>'
        f'<span style="border-radius:999px;background:rgba(255,255,255,.2);padding:4px 10px;font-size:12px;font-weight:600">1.5x points</span></div>' +
        card(f'<div class="row g12" style="padding:12px 16px">{av("MT", "violet")}<div style="flex:1;min-width:0"><b class="w6" style="font-size:14px">Maya Torres</b><div class="le-muted row g4" style="font-size:13px">maya.torres@example.com <span class="le-mini" style="color:#0ca30c">{ic("circle-check")}</span></div></div>'
             f'<span class="le-b s ic"{k("copy")}>{ic("copy")}</span><span class="le-b s ic"{k("edit")}>{ic("pen-line")}</span></div>'
             f'<div class="row" style="justify-content:space-between;padding:12px 16px;border-top:1px solid #e2e8f0;font-size:14px"><span class="le-muted">Phone</span><span>+1 555 0188</span></div>') +
        card(f'<div style="padding:16px"><div class="le-faint" style="font-size:12px;letter-spacing:.05em;text-transform:uppercase">Switch Loyalty Program</div><div class="le-swt" style="margin-top:8px"{k("prog")}>{mark("DC", "orange", 32)}<b>Daybreak Coffee</b>{ic("chevron-down")}</div></div>'))
inner = phone(acct, 'Account')
for n, needle in enumerate(['<div class="ma-tier"', '<span class="le-b s ic" data-k="copy"', '<span class="le-b s ic" data-k="edit"', '<div class="le-swt" style="margin-top:8px" data-k="prog"'], 1):
    inner = tag(inner, needle, n)
shot('m-account', 390, 760, inner, 'The Account tab.', ['Your tier and earn rate', 'Copy member ID', 'Edit profile', 'Switch to another program'])


def public(body, title, sub):
    return (f'<div class="ma-center"><div style="width:352px;display:flex;flex-direction:column;align-items:center;gap:12px">{mark("DC", "orange", 48)}'
            f'<div style="text-align:center"><div style="font-size:18px;font-weight:600">{title}</div><div class="le-muted" style="font-size:14px;margin-top:2px">{sub}</div></div>'
            f'<div class="le-card" style="width:100%;padding:24px;margin-top:8px">{body}</div></div></div>')


log = public('<div class="le-tabs" style="display:grid;grid-template-columns:1fr 1fr;margin-bottom:20px" data-k="mode"><span class="on">Log in</span><span>Sign up</span></div>'
             '<div class="le-stack">' + field('Email', inp('maya.torres@example.com', cls='focus'), key='email') + b('Send login code', 'p', size='full', key='send') + '</div>',
             'Daybreak Coffee', 'Log in or create an account to continue')
code = public('<div class="le-stack"><div class="le-muted" style="font-size:14px">We sent a 6-digit code to <b style="color:#0f172a" class="w5">maya.torres@example.com</b>.</div>' +
              field('Code', inp('482913', cls='focus', style='letter-spacing:.2em'), key='code') + b('Continue', 'p', size='full', key='cont') +
              '<div style="text-align:center;font-size:13px" class="le-muted" data-k="other">Use a different email</div></div>',
              'Daybreak Coffee', 'Log in or create an account to continue').replace('<div class="ma-center">', '<div class="ma-center" style="left:420px">', 1)
inner = log.replace('<div class="ma-center">', '<div class="ma-center" style="right:auto;width:400px">', 1) + code.replace('style="left:420px"', 'style="left:420px;width:400px;right:auto"', 1)
for n, needle in enumerate(['<div class="le-tabs" style="display:grid;grid-template-columns:1fr 1fr;margin-bottom:20px" data-k="mode"', '<div class="le-f" data-k="email"', '<span class="le-b p full" data-k="send"', '<div class="le-f" data-k="code"', '<span class="le-b p full" data-k="cont"', '<div style="text-align:center;font-size:13px" class="le-muted" data-k="other"'], 1):
    inner = tag(inner, needle, n)
shot('m-login', 820, 480, inner, 'Member sign in: ask for a code, then enter it.', ['Log in or Sign up', 'Your email', 'Send login code', 'The 6-digit code from the email', 'Continue', 'Use a different email'])

ver = public(f'<div class="le-stack"><div class="le-muted" style="font-size:14px">Press the button below to confirm this email address.</div>{b("Verify my email", "p", size="full", key="v")}</div>',
             'Verify your email', "One tap and you're done")
ver = ver.replace('<div class="ma-center">', '<div class="ma-center" style="right:auto;width:400px">', 1)
clm = public(f'<div class="row g12"><span class="le-chip" style="width:48px;height:48px;border-radius:12px;background:#efecfd;color:#5b4bd6">{ic("gift")}</span><div><b class="w6" style="font-size:16px">Free espresso</b><div class="le-muted" style="font-size:13px">Any single espresso drink</div></div></div>'
             f'<div style="margin-top:20px">{b("Claim my prize", "p", size="full", key="c")}</div>', 'Congratulations, Maya!', 'Daybreak Coffee')
clm = clm.replace('<div class="ma-center">', '<div class="ma-center" style="left:420px;width:400px;right:auto">', 1)
inner = tag(ver + clm, '<span class="le-b p full" data-k="v"', 1)
inner = tag(inner, '<span class="le-b p full" data-k="c"', 2)
shot('m-email-pages', 820, 420, inner, 'The pages that open from member emails: email verification and prize claim.', ['Verify my email', 'Claim my prize'])

# =====================================================================================
# Diagrams (follow the reading theme)
# =====================================================================================

d = Diagram('dg-event', 900, 250)
d.box(10, 90, 150, 60, 'Event arrives', 'member, type, attributes')
d.box(210, 90, 170, 60, 'Checks', 'known? active? new id?', 'q')
d.box(430, 90, 190, 60, 'Every active rule', 'whose conditions all match')
d.box(670, 20, 220, 52, 'Effects run', 'points, rewards, segments...', 'ok')
d.box(670, 168, 220, 52, 'Tier re-checked', 'once, after all rules', 'ok')
d.box(210, 190, 170, 46, 'Rejected', 'nothing is saved', 'bad')
d.arrow('M160,120 H208', '', 0, 0, 'ok')
d.arrow('M380,120 H428', '', 0, 0, 'ok')
d.arrow('M295,150 V188', 'fails', 330, 175, 'no')
d.arrow('M620,108 C645,90 650,60 668,50', '', 0, 0, 'ok')
d.arrow('M780,72 V166', 'then', 805, 125, 'ok')
d.save('What happens when an event arrives. Every matching rule runs, then the tier is checked once.')

d = Diagram('dg-tiers', 900, 200)
d.box(10, 70, 160, 60, 'Points change', 'or purchase, event...')
d.box(220, 70, 150, 60, 'Gold', 'rank 2: all match?', 'q')
d.box(420, 70, 150, 60, 'Silver', 'rank 1: all match?', 'q')
d.box(620, 70, 150, 60, 'Bronze', 'rank 0: all match?', 'q')
d.box(800, 70, 90, 60, 'No tier')
d.arrow('M170,100 H218', '', 0, 0, 'ok')
d.arrow('M370,100 H418', 'no', 394, 92, 'no')
d.arrow('M570,100 H618', 'no', 594, 92, 'no')
d.arrow('M770,100 H798', '', 0, 0, 'no')
d.arrow('M295,130 V175', 'yes: Gold', 340, 168, 'ok')
d.arrow('M495,130 V175', 'yes: Silver', 545, 168, 'ok')
d.arrow('M695,130 V175', 'yes: Bronze', 745, 168, 'ok')
d.save('Tiers are tried from the highest rank down. The member gets the first tier whose conditions all match.')

d = Diagram('dg-person', 860, 230)
d.box(20, 85, 220, 60, 'Person', 'name, email, phone, verified')
d.box(330, 20, 250, 60, 'Member in Daybreak Coffee', 'own ID, points, tier, segments', 'ok')
d.box(330, 150, 250, 60, 'Member in Summer Demo', 'own ID, points, tier, segments', 'ok')
d.box(650, 85, 200, 60, 'Shared everywhere', 'profile edits, deletes')
d.arrow('M240,105 C285,90 290,55 328,50', '', 0, 0, 'ok')
d.arrow('M240,125 C285,140 290,175 328,180', '', 0, 0, 'ok')
d.arrow('M240,115 C440,115 440,115 648,115', '', 0, 0, 'no')
d.save('One person, one membership per program. Points, tier and segments belong to the membership. Name, email and phone belong to the person.')

d = Diagram('dg-challenge', 900, 180)
d.box(10, 60, 150, 56, 'Assigned', 'progress 0')
d.box(240, 60, 170, 56, 'In progress', 'progress added')
d.box(500, 60, 170, 56, 'Completed', 'points and prize paid', 'ok')
d.box(740, 60, 150, 56, 'Expired', 'deadline passed', 'bad')
d.arrow('M160,88 H238', 'Progress', 199, 80, 'ok')
d.arrow('M410,88 H498', 'Target hit', 454, 80, 'ok')
d.arrow('M85,60 C85,10 585,10 585,58', 'Complete (by staff)', 335, 22, 'no')
d.arrow('M325,116 C325,165 815,165 815,118', 'Progress after the deadline', 570, 160, 'no')
d.save('A member\'s challenge moves from Assigned to Completed. Staff can force Complete at any time.')

print('shots done')
