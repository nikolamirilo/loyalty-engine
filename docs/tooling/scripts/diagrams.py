"""Concept diagrams as inline SVG (shots/<name>.html). Unlike screens, diagrams follow the reading
theme: boxes, text and arrows take their colors from the docs' tokens.

    import sys; sys.path.insert(0, '<skill>/scripts')
    from shots import init
    from diagrams import Diagram
    init(__file__)
    d = Diagram('dg-states', 830, 200)
    d.box(10, 70, 150, 52, 'Draft', 'not published')
    d.box(230, 70, 150, 52, 'Live', 'open to visitors', 'ok')
    d.arrow('M160,96 H228', 'Publish', 194, 88)
    d.save('A project moves from Draft to Live when you publish it.')

Box kinds: '' (plain), 'q' (a question, dashed), 'ok' (the good result, accent), 'bad' (a failure, red).
Arrow kinds: '' (plain), 'ok' (the main path), 'no' (dashed, the other path).
Keep every label inside the viewBox; give long sublines a second box row instead of squeezing them.
"""
from shots import _path


class Diagram:
    def __init__(self, name, w, h):
        self.name, self.w, self.h, self.parts = name, w, h, []
        # marker ids must be unique per diagram: a marker inside a hidden page does not render elsewhere
        self.p = 'm' + ''.join(c for c in name if c.isalnum())[:12]

    def box(self, x, y, w, h, title, sub='', kind=''):
        cls = 'bx' + (' ' + kind if kind else '')
        self.parts.append(f'<rect class="{cls}" x="{x}" y="{y}" width="{w}" height="{h}" rx="10"/>')
        cx = x + w / 2
        if sub:
            self.parts.append(f'<text class="t" x="{cx}" y="{y + h / 2 - 3}" text-anchor="middle">{title}</text>')
            self.parts.append(f'<text class="s" x="{cx}" y="{y + h / 2 + 13}" text-anchor="middle">{sub}</text>')
        else:
            self.parts.append(f'<text class="t" x="{cx}" y="{y + h / 2 + 4.5}" text-anchor="middle">{title}</text>')

    def arrow(self, d, label='', lx=0, ly=0, kind='', anchor='middle'):
        cls = 'ar' + (' ' + kind if kind else '')
        mk = {'ok': f'{self.p}A', 'no': f'{self.p}N'}.get(kind, self.p)
        self.parts.append(f'<path class="{cls}" d="{d}" marker-end="url(#{mk})"/>')
        if label:
            self.parts.append(f'<text class="l{" " + kind if kind else ""}" x="{lx}" y="{ly}" text-anchor="{anchor}">{label}</text>')

    def text(self, x, y, s, cls='s', anchor='middle'):
        self.parts.append(f'<text class="{cls}" x="{x}" y="{y}" text-anchor="{anchor}">{s}</text>')

    def save(self, caption):
        p = self.p
        defs = ('<defs>'
                f'<marker id="{p}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="ah" d="M0,0 L10,5 L0,10 z"/></marker>'
                f'<marker id="{p}A" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="ah ok" d="M0,0 L10,5 L0,10 z"/></marker>'
                f'<marker id="{p}N" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path class="ah no" d="M0,0 L10,5 L0,10 z"/></marker>'
                '</defs>')
        html = (f'<figure class="dgm"><div class="dgw"><svg viewBox="0 0 {self.w} {self.h}" role="img" aria-label="{caption}">{defs}{"".join(self.parts)}</svg></div>'
                f'<figcaption>{caption}</figcaption></figure>')
        open(_path(self.name), 'w').write(html)
        return html
