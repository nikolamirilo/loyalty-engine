"""Build the documentation into one self-contained HTML page.

    python3 <skill>/scripts/build.py <site-dir>

<site-dir> holds site.py (configuration and page order), the numbered HTML parts and shots/:
  00-09  head and styles (00-head.html opens <style>, 01-*.html are CSS, 01-zclose.html closes it)
  02     shell markup (sidebar, top bar)
  10-98  content: one <section class="page" id="..."> per page, written with the macros below
  99     foot (closing markup and the page script)

Writes <site-dir>/dist/docs.html (publish this one: no <html>/<head>/<body>, the host adds them)
and <site-dir>/dist/preview.html (a full document for local checks with a browser).

Macros in content:
  {{h:kind|Title}}            section heading. kind: steps opts rules ex risk info screen fix link
  {{o:Name|req;def=X;lim=Y}}  one option row (inside <div class="opts">), closed by {{/o}}
  [[tip Title]] ... [[/]]     note. kinds: info tip warn risk
  {{n:3}}                     number chip that points at hotspot 3 of the nearest screen
  {{i:icon}} {{s:asset}}      Lucide icon, or one of the product's own SVGs (SITE['assets_dir'])
  <!--SHOT:name-->            inline shots/name.html (a screen, diagram or animation)
"""
import glob
import importlib.util
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from palette import theme_css, swatches, hue_sat, hsl, fit  # noqa: E402

site_dir = os.path.abspath(sys.argv[1] if len(sys.argv) > 1 else '.')
spec = importlib.util.spec_from_file_location('site_cfg', os.path.join(site_dir, 'site.py'))
S = importlib.util.module_from_spec(spec)
spec.loader.exec_module(S)
SITE = S.SITE
os.chdir(site_dir)


def opt_attr(name, default):
    return getattr(S, name, default)


PAGES = S.PAGES
NEW_PAGES = opt_attr('NEW_PAGES', {})
RESULT = opt_attr('RESULT', {})
BEFORE = opt_attr('BEFORE', {})
BADGES = opt_attr('BADGES', {})
RELATED = opt_attr('RELATED', {})
OPEN_MESSAGES = opt_attr('OPEN_MESSAGES', set())
TABS = opt_attr('TABS', {})
CHECKLIST = opt_attr('CHECKLIST', set())

parts = sorted(glob.glob('[0-9][0-9]-*.html'))
head = ''.join(open(p).read() for p in parts if int(p[:2]) < 10)
content = ''.join(open(p).read() for p in parts if 10 <= int(p[:2]) < 99)
foot = ''.join(open(p).read() for p in parts if int(p[:2]) == 99)

# ---- restructure: parse pages, merge parts, add the page header, reorder ----
src = {m.group(1): m.group(2) for m in re.finditer(r'<section class="page[^"]*" id="([^"]+)"[^>]*>(.*?)</section>', content, re.S)}


def split(inner, pid):
    m = re.match(r'\s*<header>(.*?)</header>(.*)', inner, re.S)
    if not m:
        sys.exit(f'Page {pid}: the section must start with <header>...</header>')
    hdr, body = m.group(1), m.group(2)
    h1 = re.search(r'<h1>(.*?)</h1>', hdr, re.S)
    lead = re.search(r'<p class="lead">(.*?)</p>', hdr, re.S)
    where = re.search(r'<div class="where">.*?</div>', hdr, re.S)
    return (h1.group(1) if h1 else ''), (lead.group(1) if lead else ''), (where.group(0) if where else ''), body


def collapse(body):
    def rep(m):
        return (f'<details class="msgs"><summary><span class="k k-risk">{{{{i:life-buoy}}}}</span>{m.group(1)}'
                f'{{{{i:chevron-down|chev}}}}</summary>{m.group(2)}</details>')
    return re.sub(r'\{\{h:fix\|([^}]*)\}\}\s*(<div class="tbl">.*?</table></div>)', rep, body, flags=re.S)


out, used_src, missing_pages = [], set(), []
for i, (pid, group, sub, title, merged) in enumerate(PAGES):
    if pid in NEW_PAGES:
        lead, wh = NEW_PAGES[pid]
        where = f'<div class="where"><b>{{{{i:map-pin}}}} Where</b>{wh}</div>' if wh else ''
        body = ''
    elif pid not in src:
        missing_pages.append(pid)
        continue
    else:
        _, lead, where, body = split(src[pid], pid)
        used_src.add(pid)
    tabs = TABS.get(pid)
    tabbar = ''
    if tabs:
        if 'main' in tabs and body.strip():
            body = f'<div class="pw tabp" id="{pid}-main">{body}</div>'
        ids = ([f'{pid}-main'] if 'main' in tabs else []) + list(merged)
        tabbar = ('<div class="tabsbar" role="tablist">' + ''.join(
            f'<button type="button" role="tab" data-for="{t}" aria-selected="{"true" if k == 0 else "false"}">{tabs["main" if t == pid + "-main" else t]}</button>'
            for k, t in enumerate(ids)) + '</div>')
        body = body.replace(f'<div class="pw tabp" id="{pid}-main">', f'<div class="pw tabp act" id="{pid}-main">')
    for k, sid in enumerate(merged):
        if sid not in src:
            missing_pages.append(sid)
            continue
        h1, l2, w2, b2 = split(src[sid], sid)
        used_src.add(sid)
        cls = ('pw tabp' + (' act' if k == 0 and 'main' not in tabs else '')) if tabs else 'pw'
        body += (f'<div class="{cls}" id="{sid}"><div class="part"><div class="pt"><span>{h1}</span></div>'
                 + (f'<p class="pl">{l2}</p>' if l2 else '') + f'</div>{w2}{b2}</div>')
    if pid not in OPEN_MESSAGES:
        body = collapse(body)
    badges = ''.join(f'<span class="bd {k}">{{{{i:{ic}}}}}{t}</span>' for k, ic, t in BADGES.get(pid, []))
    badges = f'<div class="badges">{badges}</div>' if badges else ''
    res = RESULT.get(pid)
    inshort = (f'<dl class="inshort"><dt>In short</dt><dd>{lead}</dd>' + (f'<dt>Result</dt><dd>{res}</dd>' if res else '') + '</dl>') if lead else ''
    before = ''
    if pid in BEFORE:
        before = '<div class="before"><b>{{i:list-checks}} Before you start</b><ul>' + ''.join(f'<li>{x}</li>' for x in BEFORE[pid]) + '</ul></div>'
    sub_attr = f' data-sub="{sub}"' if sub else ''
    cls = 'page on' if i == 0 else 'page'
    ck = ' data-check="1"' if pid in CHECKLIST else ''
    out.append(f'<section class="{cls}" id="{pid}" data-group="{group}"{sub_attr}{ck} data-title="{title}" data-related="{RELATED.get(pid, "")}">'
               f'<header><h1>{title}</h1>{badges}{inshort}{where}{before}</header>{tabbar}{body}</section>\n')
if missing_pages:
    sys.exit(f'PAGES lists pages with no <section> in the content files: {missing_pages}')
unused = set(src) - used_src
if unused:
    sys.exit(f'Sections not listed in PAGES (add them, or merge them into a page): {sorted(unused)}')
s = head + ''.join(out) + foot

# ---- product-specific values from SITE ----
brand = SITE['brand_color']


def logo_parts():
    path = SITE.get('logo')
    name = SITE.get('product', 'Product')
    if path:
        p = path if os.path.isabs(path) else os.path.join(site_dir, path)
        svg = open(p).read()
        vb = re.search(r'viewBox="([^"]+)"', svg)
        vb = vb.group(1) if vb else '0 0 100 24'
        inner = re.search(r'<svg[^>]*>(.*)</svg>', svg, re.S).group(1)
        inner = re.sub(r'<\?xml[^>]*>|<!--.*?-->', '', inner, flags=re.S)
        if SITE.get('logo_mono', True):
            inner = re.sub(r'(fill|stroke)="(?!none)[^"]*"', r'\1="currentColor"', inner)
        w, h = [float(x) for x in vb.split()[2:4]]
    else:
        # no logo file: a word mark in the docs font
        w, h = 11.5 * len(name) + 6, 24
        vb = f'0 0 {w:.0f} {h}'
        inner = f'<text x="0" y="18" fill="currentColor" style="font:600 18px var(--font)">{name}</text>'
    ratio = w / h

    def use(height):
        return f'<svg viewBox="{vb}" width="{ratio * height:.0f}" height="{height}" role="img" aria-label="{name}"><use href="#logo"/></svg>'
    return f'<symbol id="logo" viewBox="{vb}">{inner}</symbol>', use(24), use(20)


logo_symbol, logo_use, logo_use_small = logo_parts()
sw = swatches(brand)
theme_buttons = ''.join(
    f'<button type="button" data-set-theme="{k}" aria-pressed="false"><i style="background:{bg};--sw-fg:{fg};--sw-ac:{ac}"></i>{k.capitalize()}</button>'
    for k, (bg, fg, ac) in sw.items())

bh, bs, bl = hue_sat(brand)
screen = {
    'font': SITE.get('font_screen') or SITE.get('font_body') or "system-ui,sans-serif",
    'bg': '#FFFFFF', 'canvas': hsl(bh, 8 if bs > 8 else 0, 97), 'surface': hsl(bh, 10 if bs > 8 else 0, 97.5),
    'line': hsl(bh, 8 if bs > 8 else 0, 90), 'line-strong': hsl(bh, 8 if bs > 8 else 0, 82),
    'fg': '#3F4450', 'fg-strong': '#141821', 'muted': '#6B7280', 'placeholder': '#9CA3AF',
    'primary': brand, 'primary-fg': '#FFFFFF', 'primary-soft': hsl(bh, min(bs, 60), 95),
    'primary-text': fit(bh, bs, min(bl, 45), '#FFFFFF', 4.8, -1.5), 'brand': brand,
    'danger': '#DC2626', 'success': '#16A34A', 'warning': '#D97706',
    'radius': '8px', 'radius-sm': '6px', 'radius-lg': '12px',
    'shadow': '0 1px 2px rgba(0,0,0,.06),0 8px 24px -8px rgba(0,0,0,.18)',
}
screen.update(SITE.get('screen', {}))
screen_tokens = '.sx{' + ''.join(f'--p-{k}:{v};' for k, v in screen.items()) + '}'

fonts_q = SITE.get('google_fonts')
fonts_link = f'<link rel="stylesheet" href="https://fonts.googleapis.com/css2?{fonts_q}&display=swap">' if fonts_q else ''

cfg = {
    'groupIcons': {g: '#i-' + ic for g, ic in SITE.get('group_icons', {}).items()},
    'glossary': SITE.get('glossary', {}),
    'synonyms': SITE.get('synonyms', {}),
    'popular': SITE.get('popular', []),
    'storageKey': SITE.get('storage_key', 'docs'),
    'url': SITE.get('url', ''),
    'glossaryPage': SITE.get('glossary_page', 'glossary'),
}
config_json = json.dumps(cfg, ensure_ascii=False).replace('</', '<\\/')

for k, v in {
    'SITE_TITLE': SITE['title'], 'FONTS_LINK': fonts_link,
    'FONT_BODY': SITE.get('font_body', "system-ui,-apple-system,'Segoe UI',Roboto,sans-serif"),
    'FONT_MONO': SITE.get('font_mono', 'ui-monospace,SFMono-Regular,Menlo,monospace'),
    'FONT_SCREEN': screen['font'],
    'THEME_TOKENS': theme_css(brand, SITE.get('brand_mark'), SITE.get('neutral_tint', 10)),
    'SCREEN_TOKENS': screen_tokens, 'LOGO_SYMBOL': logo_symbol, 'LOGO_USE': logo_use, 'LOGO_USE_SMALL': logo_use_small,
    'DOCS_LABEL': SITE.get('docs_label', 'Docs'), 'HOME': PAGES[0][0], 'THEME_BUTTONS': theme_buttons,
    'CONFIG_JSON': config_json,
}.items():
    s = s.replace('{{' + k + '}}', str(v))

# ---- macros ----
s = re.sub(r'\{\{n:(\d+)\}\}', lambda m: f'<button type="button" class="nchip" data-n="{m.group(1)}" aria-label="Show item {m.group(1)} on the screen">{m.group(1)}</button>', s)

missing_shots = []


def shot(m):
    f = os.path.join('shots', m.group(1) + '.html')
    if not os.path.exists(f):
        missing_shots.append(m.group(1))
        return '<p class="note warn">[screen ' + m.group(1) + ']</p>'
    return open(f).read()


s = re.sub(r'<!--SHOT:([a-z0-9-]+)-->', shot, s)

assets = SITE.get('assets_dir')
if assets and not os.path.isabs(assets):
    assets = os.path.join(site_dir, assets)


def sasset(m):
    name, cls = m.group(1), (m.group(2) or '')
    if not assets:
        sys.exit(f'{{{{s:{name}}}}} needs SITE["assets_dir"]')
    svg = open(os.path.join(assets, name + '.svg')).read()
    svg = re.sub(r'<\?xml[^>]*>|<!--.*?-->', '', svg, flags=re.S).strip()
    svg = re.sub(r'\s+', ' ', svg)
    svg = re.sub(r'<svg([^>]*?) width="[^"]*"', r'<svg\1', svg, count=1)
    svg = re.sub(r'<svg([^>]*?) height="[^"]*"', r'<svg\1', svg, count=1)
    return svg.replace('<svg', f'<svg class="sico {cls}" aria-hidden="true"', 1)


ICONS = json.load(open(os.path.join(SKILL, 'assets', 'icons.json')))
extra = SITE.get('extra_icons_dir')
if extra:
    extra = extra if os.path.isabs(extra) else os.path.join(site_dir, extra)
    for f in glob.glob(os.path.join(extra, '*.svg')):
        body = open(f).read()
        ICONS[os.path.basename(f)[:-4]] = re.sub(r'\s+', ' ', re.search(r'<svg[^>]*>(.*)</svg>', body, re.S).group(1)).strip()
used = set()


def icon(m):
    name, cls = m.group(1), (m.group(2) or '')
    used.add(name)
    return f'<svg class="ico{" " + cls if cls else ""}" aria-hidden="true"><use href="#i-{name}"/></svg>'


def expand(t):
    t = re.sub(r'\{\{s:([a-zA-Z0-9_-]+)(?:\|([a-z0-9 -]+))?\}\}', sasset, t)
    return re.sub(r'\{\{i:([a-z0-9-]+)(?:\|([a-z0-9 -]+))?\}\}', icon, t)


s = expand(s)

HT = {'steps': ('k-steps', 'list-ordered'), 'opts': ('k-opts', 'sliders-horizontal'), 'rules': ('k-rules', 'shield-alert'),
      'ex': ('k-ex', 'lightbulb'), 'risk': ('k-risk', 'octagon-alert'), 'info': ('k-info', 'info'),
      'screen': ('k-info', 'app-window'), 'fix': ('k-risk', 'life-buoy'), 'link': ('k-info', 'link')}


def heading(m):
    kind, title = m.group(1), m.group(2)
    if kind not in HT:
        sys.exit(f'Unknown heading kind {{{{h:{kind}|...}}}}. Use one of {sorted(HT)}')
    cls, ic = HT[kind]
    return f'<h2><span class="k {cls}">{{{{i:{ic}}}}}</span><span>{title}</span></h2>'


s = re.sub(r'\{\{h:([a-z]+)\|([^}]*)\}\}', heading, s)
NI = {'info': 'info', 'tip': 'lightbulb', 'warn': 'triangle-alert', 'risk': 'octagon-alert'}
s = re.sub(r'\[\[(info|tip|warn|risk) ([^\]]*)\]\]', lambda m: f'<div class="note {m.group(1)}">{{{{i:{NI[m.group(1)]}}}}}<div><b>{m.group(2)}</b>', s)
s = s.replace('[[/]]', '</div></div>')


def opt(m):
    name, tags = m.group(1), (m.group(2) or '')
    tg = []
    for t in [t for t in tags.split(';') if t]:
        if t == 'req':
            tg.append('<span class="tg req">Required</span>')
        elif t == 'opt':
            tg.append('<span class="tg opt-">Optional</span>')
        elif t.startswith('def='):
            tg.append(f'<span class="tg def">Default: {t[4:]}</span>')
        elif t.startswith('lim='):
            tg.append(f'<span class="tg lim">{t[4:]}</span>')
    tags_html = f'<div class="tags">{"".join(tg)}</div>' if tg else ''
    return f'<div class="opt"><div class="n">{name}{tags_html}</div><div class="d">'


s = re.sub(r'\{\{o:([^|}]*)(?:\|([^}]*))?\}\}', opt, s)
s = s.replace('{{/o}}', '</div></div>')
s = expand(s)
for n in re.findall(r'#i-([a-z0-9-]+)', s):
    used.add(n)

symbols, missing_icons = [], []
for n in sorted(used):
    if n not in ICONS:
        missing_icons.append(n)
        continue
    symbols.append(f'<symbol id="i-{n}" viewBox="0 0 24 24">{ICONS[n]}</symbol>')
if missing_icons:
    sys.exit(f'Unknown icons (not in Lucide or extra_icons_dir): {missing_icons}')
sprite = '<svg width="0" height="0" style="position:absolute" aria-hidden="true" focusable="false"><defs>' + ''.join(symbols) + '</defs></svg>'
s = s.replace('<!--SPRITE-->', sprite)

# ---- write ----
os.makedirs('dist', exist_ok=True)
open('dist/docs.html', 'w').write(s)
open('dist/preview.html', 'w').write('<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">' + s + '</body></html>')

# ---- report ----
ids = set(re.findall(r'id="([^"]+)"', s))
broken = sorted({h for h in re.findall(r'href="#([^"]+)"', s) if h not in ids and "'" not in h and '+' not in h})
left = sorted(set(re.findall(r'\{\{[^}]{0,40}\}\}', s)))
print(f'dist/docs.html: {len(s) // 1024} KB, {len(PAGES)} pages, {len(used)} icons, '
      f'em-dash {s.count(chr(0x2014))}, en-dash {s.count(chr(0x2013))}')
for label, items in (('MISSING SHOTS', missing_shots), ('BROKEN LINKS', broken), ('UNEXPANDED', left)):
    if items:
        print(f'{label}: {items}')
