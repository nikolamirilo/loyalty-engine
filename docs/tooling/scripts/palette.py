"""Turn a product's brand color into the docs' reading themes: light, paper, dark and midnight.

Every text color is tuned until it reaches WCAG contrast on the surface it sits on, so any brand
color gives readable pages. Section colors (steps, options, rules, examples, careful) keep fixed
hues that read as the same kind of thing in every product, moved away from the brand hue when
the two would look alike.

Usage from Python:  from palette import theme_css;  css = theme_css('#4A7A4C')
Usage from a shell:  python3 palette.py '#4A7A4C'   (prints the CSS)
"""
import colorsys
import sys


def _hex(h):
    h = h.strip().lstrip('#')
    if len(h) == 3:
        h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))


def _to_hex(rgb):
    return '#' + ''.join(f'{max(0, min(255, round(c * 255))):02X}' for c in rgb)


def hsl(h, s, l):
    """h in degrees, s and l in 0..100."""
    return _to_hex(colorsys.hls_to_rgb((h % 360) / 360, l / 100, s / 100))


def hue_sat(hexcolor):
    h, l, s = colorsys.rgb_to_hls(*_hex(hexcolor))
    return h * 360, s * 100, l * 100


def _lum(hexcolor):
    def ch(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (ch(c) for c in _hex(hexcolor))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def fit(h, s, l, against, target, step):
    """Move lightness by `step` (negative darkens) until the color reaches `target` contrast."""
    c = hsl(h, s, l)
    for _ in range(120):
        if contrast(c, against) >= target:
            return c
        l = max(0, min(100, l + step))
        c = hsl(h, s, l)
    return c


def _apart(a, b, gap):
    d = abs((a - b + 180) % 360 - 180)
    return d >= gap


def _hues(brand_h, brand_s):
    """Section hues. Steps follow the brand unless the brand is grey or reads as red or amber."""
    greyish = brand_s < 18
    steps = 140 if greyish or not _apart(brand_h, 0, 22) or not _apart(brand_h, 45, 18) else brand_h
    opts = 212
    if not _apart(opts, steps, 32):
        opts = 190 if _apart(190, steps, 32) else 238
    return {'steps': steps, 'opts': opts, 'rules': 45, 'ex': 292, 'risk': 2}


def _section_tokens(hues, bg_text, bg_tint_l, line_l, text_l, step, sat, dark):
    out = {}
    for k, h in hues.items():
        s = sat if k != 'rules' else min(100, sat + 25)
        bg = hsl(h, s * (0.55 if dark else 0.9), bg_tint_l)
        out[f'--{k}'] = fit(h, s, text_l, bg, 5.0, step)
        out[f'--{k}-bg'] = bg
        out[f'--{k}-line'] = hsl(h, s * 0.7, line_l)
    return out


def _light(brand, hues, neutral_h, nsat):
    bh, bs, bl = hue_sat(brand)
    bg = '#FFFFFF'
    accent_solid = fit(bh, bs, bl, '#FFFFFF', 4.6, -1.5)
    t = {
        '--bg': bg, '--surface': '#FFFFFF',
        '--surface-2': hsl(neutral_h, nsat, 96.5), '--surface-3': hsl(neutral_h, nsat + 4, 92.5),
        '--line': hsl(neutral_h, nsat, 87.5), '--line-strong': hsl(neutral_h, nsat + 6, 79),
        '--fg': hsl(neutral_h, 6, 17), '--fg-strong': hsl(neutral_h, 8, 8), '--fg-muted': hsl(neutral_h, 5, 35),
        '--accent': fit(bh, bs, min(bl, 45), bg, 4.8, -1.5), '--accent-solid': accent_solid,
        '--accent-soft': hsl(bh, min(bs, 55), 95), '--on-accent': '#FFFFFF',
        '--link': '#1158A8' if _apart(bh, 212, 30) else fit(bh, bs, 40, bg, 5.5, -1.5),
        '--focus': '#358CE9', '--hot': '#1877DC',
        '--scrim': 'rgba(20,24,30,.35)',
        '--shadow': '0 1px 2px rgba(0,0,0,.06),0 4px 14px rgba(0,0,0,.08)',
        '--elev': '0 1px 2px rgba(30,30,30,.04),0 4px 14px -4px rgba(30,30,30,.08)',
        '--elev-hi': '0 2px 6px rgba(30,30,30,.06),0 16px 32px -10px rgba(30,30,30,.18)',
    }
    t.update(_section_tokens(hues, bg, 95.5, 76, 36, -1.5, 62, False))
    return t, 'light'


def _paper(brand, hues):
    bh, bs, bl = hue_sat(brand)
    bg = hsl(40, 38, 94.5)
    t = {
        '--bg': bg, '--surface': hsl(40, 45, 97), '--surface-2': hsl(38, 30, 90.5), '--surface-3': hsl(37, 28, 85.5),
        '--line': hsl(37, 26, 80.5), '--line-strong': hsl(36, 25, 70),
        '--fg': hsl(30, 13, 15), '--fg-strong': hsl(30, 21, 7.5), '--fg-muted': hsl(28, 10, 32),
        '--accent': fit(bh, bs, min(bl, 42), bg, 5.0, -1.5), '--accent-solid': fit(bh, bs, bl, '#FFFFFF', 4.6, -1.5),
        '--accent-soft': hsl(bh, min(bs, 35), 90), '--on-accent': '#FFFFFF',
        '--link': '#0F5299' if _apart(bh, 212, 30) else fit(bh, bs, 38, bg, 5.5, -1.5),
        '--focus': '#2F7FD6', '--hot': '#1877DC',
        '--scrim': 'rgba(40,30,20,.35)',
        '--shadow': '0 1px 2px rgba(60,40,10,.08),0 4px 14px rgba(60,40,10,.08)',
        '--elev': '0 1px 2px rgba(60,40,10,.05),0 4px 14px -4px rgba(60,40,10,.10)',
        '--elev-hi': '0 2px 6px rgba(60,40,10,.07),0 16px 32px -10px rgba(60,40,10,.20)',
    }
    t.update(_section_tokens(hues, bg, 90, 68, 33, -1.5, 45, False))
    return t, 'light'


def _dark(brand, hues, neutral_h, nsat, base_l=10, sat_boost=0, hue_override=None):
    bh, bs, bl = hue_sat(brand)
    nh = neutral_h if hue_override is None else hue_override
    ns = nsat + sat_boost
    bg = hsl(nh, ns, base_l)
    t = {
        '--bg': bg, '--surface': hsl(nh, ns, base_l + 2), '--surface-2': hsl(nh, ns, base_l + 5),
        '--surface-3': hsl(nh, ns, base_l + 9), '--line': hsl(nh, ns, base_l + 12), '--line-strong': hsl(nh, ns, base_l + 20),
        '--fg': hsl(nh, 4, 89), '--fg-strong': hsl(nh, 6, 96), '--fg-muted': hsl(nh, 5, 67),
        '--accent': fit(bh, min(bs, 55), 62, bg, 6.0, 1.5), '--accent-solid': fit(bh, bs, bl, '#FFFFFF', 4.6, -1.5),
        '--accent-soft': hsl(bh, min(bs, 30), base_l + 6), '--on-accent': '#FFFFFF',
        '--link': '#7DB4F5' if _apart(bh, 212, 30) else fit(bh, 70, 70, bg, 6.5, 1.5),
        '--focus': '#7DB4F5', '--hot': '#4D9BEF',
        '--scrim': 'rgba(0,0,0,.55)',
        '--shadow': '0 1px 2px rgba(0,0,0,.4),0 6px 18px rgba(0,0,0,.35)',
        '--elev': '0 1px 2px rgba(0,0,0,.35),0 6px 18px -6px rgba(0,0,0,.55)',
        '--elev-hi': '0 2px 6px rgba(0,0,0,.4),0 18px 36px -10px rgba(0,0,0,.65)',
    }
    t.update(_section_tokens(hues, bg, base_l + 5, base_l + 24, 74, 1.5, 55, True))
    return t, 'dark'


def _block(selector, tokens, scheme):
    body = ' '.join(f'{k}:{v};' for k, v in tokens.items())
    return f'{selector}{{{body} color-scheme:{scheme}}}'


def theme_css(brand, brand_mark=None, neutral_tint=10):
    """CSS for every reading theme. `brand_mark` colors the logo in the sidebar (defaults to the
    brand). `neutral_tint` is the saturation of greys, biased toward the brand hue (0 gives pure greys)."""
    bh, bs, _ = hue_sat(brand)
    hues = _hues(bh, bs)
    # a grey brand gets cool greys; any other brand tints the greys toward its own hue
    nh, nsat = (220, 4) if bs < 8 else (bh, neutral_tint)
    light, ls = _light(brand, hues, nh, nsat)
    paper, ps = _paper(brand, hues)
    dark, ds = _dark(brand, hues, nh, max(3, nsat - 2))
    midnight, ms = _dark(brand, hues, nh, 0, base_l=11.5, sat_boost=28, hue_override=222)
    mark = brand_mark or brand
    for t, against in ((light, light['--surface']), (paper, paper['--surface'])):
        mh, msat, ml = hue_sat(mark)
        t['--brand'] = fit(mh, msat, ml, against, 4.5, -1.5)
    for t in (dark, midnight):
        mh, msat, ml = hue_sat(mark)
        t['--brand'] = fit(mh, msat, max(ml, 60), t['--surface'], 6.0, 1.5)
    others = ':not([data-theme="light"]):not([data-theme="paper"]):not([data-theme="midnight"])'
    # Screens keep the product's own light look in every theme, so their frame never changes.
    frame = {'--shot-frame-bg': hsl(nh, nsat, 93.5), '--shot-frame-line': 'rgba(40,40,40,.12)',
             '--shot-bar-bg': hsl(nh, nsat, 89.5), '--shot-bar-line': hsl(nh, nsat, 83),
             '--shot-bar-dot': hsl(nh, nsat, 76), '--shot-bar-fg': hsl(nh, 18, 28)}
    return '\n'.join([
        _block(':root', light, ls),
        _block(':root', frame, ls).replace(' color-scheme:light', ''),
        _block(':root[data-theme="paper"]', paper, ps),
        '@media (prefers-color-scheme:dark){' + _block(f':root{others}', dark, ds) + '}',
        _block(':root[data-theme="dark"]', dark, ds),
        _block(':root[data-theme="midnight"]', midnight, ms),
    ])


def swatches(brand):
    """Colors for the theme picker: (background, text, accent) per theme."""
    bh, bs, _ = hue_sat(brand)
    hues = _hues(bh, bs)
    nh, nsat = (220, 4) if bs < 8 else (bh, 10)
    out = {}
    for name, (t, _) in {'light': _light(brand, hues, nh, nsat), 'paper': _paper(brand, hues),
                         'dark': _dark(brand, hues, nh, max(3, nsat - 2)),
                         'midnight': _dark(brand, hues, nh, 0, base_l=11.5, sat_boost=28, hue_override=222)}.items():
        out[name] = (t['--bg'], t['--fg'], t['--accent'] if name in ('dark', 'midnight') else t['--accent-solid'])
    return out


if __name__ == '__main__':
    print(theme_css(sys.argv[1] if len(sys.argv) > 1 else '#4A7A4C'))
