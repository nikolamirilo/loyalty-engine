"""Start a new docs site from the template.

    python3 <skill>/scripts/new_site.py <target-dir> [--product "Acme"] [--brand "#2563EB"] [--force]

Copies the layout, styles, page script, example pages, site.py and make_shots.py into <target-dir>.
Then: edit site.py, replace the example pages and screens, run make_shots.py and build.py.
"""
import argparse
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(os.path.dirname(HERE), 'assets', 'site')

ap = argparse.ArgumentParser()
ap.add_argument('target')
ap.add_argument('--product')
ap.add_argument('--brand')
ap.add_argument('--force', action='store_true')
a = ap.parse_args()

target = os.path.abspath(a.target)
if os.path.exists(os.path.join(target, 'site.py')) and not a.force:
    sys.exit(f'{target} already has a site.py. Use --force to overwrite the template files.')
os.makedirs(os.path.join(target, 'shots'), exist_ok=True)
for f in sorted(os.listdir(TEMPLATE)):
    shutil.copy(os.path.join(TEMPLATE, f), os.path.join(target, f))

ms = os.path.join(target, 'make_shots.py')
text = open(ms).read()
open(ms, 'w').write(text.replace('{{SKILL_SCRIPTS}}', HERE))

site = os.path.join(target, 'site.py')
s = open(site).read()
if a.product:
    s = s.replace("'title': 'Acme Docs'", f"'title': '{a.product} Docs'").replace("'product': 'Acme'", f"'product': '{a.product}'")
    key = re.sub(r'[^a-z0-9]+', '-', a.product.lower()).strip('-')
    s = s.replace("'storage_key': 'acme-docs'", f"'storage_key': '{key}-docs'")
if a.brand:
    s = s.replace("'brand_color': '#2563EB'", f"'brand_color': '{a.brand}'")
open(site, 'w').write(s)
print(f'New docs site in {target}')
print(f'Next: edit site.py, then  python3 {ms} && python3 {os.path.join(HERE, "build.py")} {target}')
