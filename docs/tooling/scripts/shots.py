"""Helpers for drawing product screens as HTML (shots/<name>.html) that build.py inlines where a
page says <!--SHOT:name-->.

A screen is a scaled stage of absolutely positioned HTML that uses the screen kit in 01-screens.html
(and any product-specific classes you add). The page script fits it to the column, draws numbered
markers on elements tagged with data-hz, and highlights a spot only while the reader hovers its number.

Typical use, in the site's make_shots.py:

    import sys; sys.path.insert(0, '<skill>/scripts')
    from shots import init, shot, tag, walk, anim, keyframes, cursor_keyframes, ic, btn, inp, sel, sw, field
    init(__file__)                      # shots are written next to make_shots.py, in shots/
    inner = '<div class="aside">...</div><div class="mn" style="left:248px">...</div>'
    inner = tag(inner, '<div class="aside"', 1)          # hotspot 1
    shot('projects-list', 1200, 640, inner, 'The project list.', ['Main menu'], title='Projects')
"""
import os

SHOTS_DIR = ['shots']


def init(make_file_or_dir):
    """Write shots into <site>/shots, where <site> holds make_shots.py (or is the given directory)."""
    d = make_file_or_dir if os.path.isdir(make_file_or_dir) else os.path.dirname(os.path.abspath(make_file_or_dir))
    SHOTS_DIR[0] = os.path.join(d, 'shots')
    os.makedirs(SHOTS_DIR[0], exist_ok=True)


def _path(name):
    return os.path.join(SHOTS_DIR[0], name + '.html')


def ic(spec):
    """An icon inside a screen: 'i:name' is a Lucide icon, 's:name' is one of the product's own SVGs."""
    kind, name = spec.split(':', 1)
    return '{{' + kind + ':' + name + '}}'


def btn(text, kind='p', icon=None, cls=''):
    """kind: p (primary), s (secondary), gh (ghost), d (danger). Add 'sm', 'lg', 'off' or 'full' in cls."""
    i = ic(icon) if icon else ''
    c = ' '.join(x for x in ('btn', kind, cls) if x)
    return f'<span class="{c}">{i}{text}</span>'


def inp(value=None, ph='', cls='', style=''):
    """A text field. cls: 'focus', 'err' or 'ta' (multi-line). style: extra inline CSS, such as a width."""
    v = value if value is not None else f'<span class="ph">{ph}</span>'
    c = ' '.join(x for x in ('inp', cls) if x)
    st = f' style="{style}"' if style else ''
    return f'<div class="{c}"{st}>{v}</div>'


def sel(value=None, ph='Select'):
    v = value if value is not None else f'<span class="ph">{ph}</span>'
    return f'<div class="slt">{v}{ic("i:chevron-down")}</div>'


def sw(on=False):
    return f'<span class="sw{" on" if on else ""}"></span>'


def field(label, control, req=False, hint=''):
    star = ' <span class="req">*</span>' if req else ''
    h = f'<div class="hint">{hint}</div>' if hint else ''
    return f'<div class="fld"><div class="lbl">{label}{star}</div>{control}{h}</div>'


def tag(html, needle, n, occ=1, attr='data-hz'):
    """Mark the occ-th element whose markup starts with `needle` as hotspot n.
    The legend item n (or, in a follow-along block, the step with data-n="n") describes it."""
    idx = -1
    for _ in range(occ):
        idx = html.find(needle, idx + 1)
        if idx < 0:
            raise ValueError(f'tag(): found fewer than {occ} elements starting with {needle!r}')
    # add the attribute at the end of the opening tag, so the needle still matches the same elements
    q, i = None, idx
    while i < len(html):
        c = html[i]
        if q:
            q = None if c == q else q
        elif c in '"\'':
            q = c
        elif c == '>':
            break
        i += 1
    end = i - 1 if html[i - 1] == '/' else i
    return html[:end] + f' {attr}="{n}"' + html[end:]


def shot(name, w, h, inner, caption, legend=None, title=None):
    """Write one screen. `legend` lists what hotspots 1, 2, 3... point at. `title` adds a window bar."""
    lg = ''
    if legend:
        lg = '<ol class="legend">' + ''.join(f'<li data-n="{i}"><i>{i}</i><span>{t}</span></li>' for i, t in enumerate(legend, 1)) + '</ol>'
    bar = f'<div class="bar"><i></i><i></i><i></i><span>{title}</span></div>' if title else ''
    html = (f'<figure class="shot"><div class="frame">{bar}<div class="vp" data-w="{w}" data-h="{h}" role="img" aria-label="{caption}">'
            f'<div class="stage sx" style="width:{w}px;height:{h}px">{inner}</div></div></div>'
            f'<figcaption>{caption}</figcaption>{lg}</figure>')
    open(_path(name), 'w').write(html)
    return html


def walk(name, spots):
    """Tag hotspots in an existing shot for a follow-along block. spots: [(needle, n), ...] or
    [(needle, n, occ), ...]. Each n matches a <li data-n="n"> in the steps under the screen; the marker
    on the screen shows that step's number."""
    h = open(_path(name)).read()
    for s in spots:
        needle, n = s[0], s[1]
        h = tag(h, needle, n, s[2] if len(s) > 2 else 1)
    open(_path(name), 'w').write(h)


# ---------- short animations: still until the reader presses play ----------
CURSOR = ('<div class="cur" data-a="cur"><svg viewBox="0 0 22 26" aria-hidden="true">'
          '<path d="M2 2 L2 21 L7 16.5 L10.5 24 L14 22.5 L10.6 15.2 L17 15 Z" fill="#141414" stroke="#fff" '
          'stroke-width="1.6" stroke-linejoin="round"/></svg></div>')


def keyframes(anim_name, key, frames):
    """CSS that plays `frames` on the element with data-a="key" when the reader presses play.
    frames: [(percent, 'css declarations'), ...]"""
    body = ''.join(f'{p}%{{{css}}}' for p, css in frames)
    kf = f'{anim_name}-{key}'
    return f'[data-anim="{anim_name}"].play [data-a="{key}"]{{animation-name:{kf}}}@keyframes {kf}{{{body}}}'


def cursor_keyframes(anim_name, path):
    """Move the pointer through path = [(percent, x, y, pressed), ...]. It fades in at the first point
    and out after the last. pressed=True shows a click (slightly smaller pointer)."""
    frames = []
    for i, (p, x, y, down) in enumerate(path):
        t = f'transform:translate({x}px,{y}px){" scale(.88)" if down else ""}'
        op = 'opacity:0;' if i == 0 else ('opacity:1;' if i == 1 else '')
        frames.append((p, op + t))
    last = path[-1]
    frames.append((min(100, last[0] + 8), f'opacity:0;transform:translate({last[1]}px,{last[2]}px)'))
    return keyframes(anim_name, 'cur', frames)


def anim(name, w, h, inner, caption, label, css, dur=3.4):
    """Write an animation shot. Put data-a="key" on each element that moves and pass the CSS from
    keyframes() and cursor_keyframes() as `css`. The resting frame (before play) must already make sense."""
    html = (f'<figure class="shot anim" data-anim="{name}" style="--anim-dur:{dur}s"><style>{css}</style>'
            f'<div class="frame"><div class="vp" data-w="{w}" data-h="{h}" role="img" aria-label="{caption}">'
            f'<div class="stage sx" style="width:{w}px;height:{h}px">{inner}{CURSOR}</div></div>'
            f'<button class="playbtn" type="button" aria-label="Play: {label}"><span class="pi"></span><span>{label}</span></button></div>'
            f'<figcaption>{caption}</figcaption></figure>')
    open(_path(name), 'w').write(html)
    return html
