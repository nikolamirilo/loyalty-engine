"""Screens, diagrams and animations for this docs site. Run it, then build:

    python3 make_shots.py && python3 <skill>/scripts/build.py .

EXAMPLE: these screens show how to use the helpers. Replace them with screens drawn from the
product's real layout, labels and tokens (see references/screens.md in the skill).
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tooling', 'scripts'))
from shots import init, shot, tag, walk, anim, keyframes, cursor_keyframes, ic, btn, inp, sel, field  # noqa: E402
from diagrams import Diagram  # noqa: E402

init(__file__)


def app(main, active='Projects'):
    """The product's frame: sidebar on the left, main area on the right."""
    nav = [('Home', 'house'), ('Projects', 'folder-kanban'), ('People', 'users'), ('Settings', 'settings')]
    items = ''.join(f'<div class="li{" act" if n == active else ""}">{ic("i:" + i)}<span>{n}</span></div>' for n, i in nav)
    return (f'<div class="aside"><div class="logo">{ic("i:hexagon")}<span>Acme</span></div>{items}</div>'
            f'<div class="mn" style="left:248px">{main}</div>')


rows = [('Website relaunch', 'ok', 'Active', 'Today'), ('Company handbook', 'mute', 'Archived', '12 May'),
        ('Client A onboarding', 'ok', 'Active', '3 Jun')]
table = ('<table class="tb"><thead><tr><th>Name</th><th>Status</th><th>Updated</th></tr></thead><tbody>' +
         ''.join(f'<tr{" class=hov" if i == 0 else ""}><td class="w5">{n}</td><td><span class="badge {k}">{s}</span></td><td class="muted">{d}</td></tr>'
                 for i, (n, k, s, d) in enumerate(rows)) + '</tbody></table>')
toolbar = ('<div class="row" style="justify-content:space-between;margin-bottom:16px"><span class="h24">Projects</span>' + btn('New project', 'p', 'i:plus') + '</div>'
           '<div class="row" style="margin-bottom:12px">' + inp(None, 'Search projects', style='width:260px') + '</div>')
listing = app('<div class="card" style="padding:20px">' + toolbar + table + '</div>')

# ---------- 1. a screen with a legend ----------
inner = listing
for n, needle in enumerate(['<div class="aside"', '<div class="inp', '<tr class=hov', '<span class="btn p"'], 1):
    inner = tag(inner, needle, n)
shot('projects-list', 1100, 420, inner, 'The project list.',
     ['Main menu', 'Search by name', 'A project: select it to open it', 'Create a project'], title='Projects')

# ---------- 2. a follow-along screen: hotspots match the steps' data-n ----------
dialog = ('<div class="overlay"></div><div class="mdl" style="left:330px;top:70px;width:440px">'
          '<div class="dh">New project</div><div class="db">' +
          field('Name', inp('Website relaunch', cls='focus'), req=True) +
          field('Visibility', sel('Private'), hint='Only people you add can open the project.') +
          '</div><div class="df">' + btn('Cancel', 's') + btn('Create', 'p') + '</div></div>')
shot('qs-new-project', 1100, 420, listing + dialog, 'The New project window.')
walk('qs-new-project', [('<span class="btn p"', 1), ('<div class="fld"', 2), ('<div class="fld"', 3, 2), ('<span class="btn p"', 4, 2)])

# ---------- 3. a concept diagram (follows the reading theme) ----------
d = Diagram('dg-lifecycle', 760, 150)
d.box(10, 50, 170, 52, 'Active', 'everyone can change it', 'ok')
d.box(290, 50, 170, 52, 'Archived', 'read only')
d.box(570, 50, 170, 52, 'Deleted', 'gone for everyone', 'bad')
d.arrow('M180,76 H288', 'Archive', 234, 68)
d.arrow('M460,76 H568', 'Delete', 514, 68, 'no')
d.arrow('M375,102 C375,140 95,140 95,104', 'Restore', 235, 136, 'ok')
d.save('A project is active until you archive it. Restore brings it back. Delete removes it for good.')

# ---------- 4. a short animation: still until the reader presses play ----------
members = app('<div class="card" style="padding:20px"><div class="row" style="justify-content:space-between;margin-bottom:16px">'
              '<span class="h24">Members</span><span data-a="btn">' + btn('Add member', 'p', 'i:user-plus') + '</span></div>' +
              '<table class="tb"><tbody><tr><td class="w5">Alex Kim</td><td class="muted">Owner</td></tr></tbody></table></div>'
              '<div class="toast" data-a="toast" style="left:560px;top:330px;opacity:0">' + ic('i:check') + 'Invitation sent</div>')
css = (cursor_keyframes('anim-create', [(0, 900, 360, False), (10, 900, 360, False), (40, 1010, 50, False), (48, 1010, 50, True), (56, 1010, 50, False)]) +
       keyframes('anim-create', 'toast', [(0, 'opacity:0'), (58, 'opacity:0;transform:translateY(8px)'), (66, 'opacity:1;transform:none'), (100, 'opacity:1')]))
anim('anim-create', 1100, 400, members, 'Select Add member. Acme sends the invitation at once.', 'Add a member', css)
print('shots done')
