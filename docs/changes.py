"""Lists the code changes the docs have not caught up with yet.

    python3 docs/changes.py             commits since SOURCE['commit'] (site.py) that touch watched code
    python3 docs/changes.py --diff      the same, with the diff of the watched files
    python3 docs/changes.py --to REF    compare up to REF instead of HEAD
    python3 docs/changes.py --mark REF  record REF as the commit the docs are now valid for

A commit counts only for the files it changes under SOURCE['watch'] that are not under
SOURCE['ignore']. A commit that only changes the docs, the built page, Markdown or tests is skipped.

Exit codes: 0 = docs are up to date, 10 = there are changes to document, 2 = setup problem.
"""
import argparse
import fnmatch
import importlib.util
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SITE_FILE = os.path.join(HERE, 'site.py')


def load_source():
    spec = importlib.util.spec_from_file_location('site_cfg', SITE_FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.SOURCE


def git(*args, check=True):
    r = subprocess.run(['git', *args], cwd=HERE, capture_output=True, text=True)
    if check and r.returncode:
        sys.exit(f'git {" ".join(args)} failed: {r.stderr.strip()}')
    return r


def matches(path, patterns):
    for p in patterns:
        if p.endswith('/') and path.startswith(p):
            return True
        if p == path or fnmatch.fnmatch(path, p) or fnmatch.fnmatch(os.path.basename(path), p):
            return True
    return False


def relevant(paths, source):
    return [p for p in paths if matches(p, source['watch']) and not matches(p, source['ignore'])]


def mark(ref):
    sha = git('rev-parse', '--verify', ref + '^{commit}').stdout.strip()
    date = git('show', '-s', '--format=%cs', sha).stdout.strip()
    text = open(SITE_FILE).read()
    text, n = re.subn(r"('commit': ')[0-9a-f]{7,40}(')", rf'\g<1>{sha}\g<2>', text, count=1)
    text, m = re.subn(r"('checked': ')[0-9-]+(')", rf'\g<1>{date}\g<2>', text, count=1)
    if not (n and m):
        sys.exit("Could not find SOURCE['commit'] and SOURCE['checked'] in site.py")
    open(SITE_FILE, 'w').write(text)
    print(f'Docs marked valid for {sha} ({date}).')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--to', default='HEAD')
    ap.add_argument('--diff', action='store_true')
    ap.add_argument('--mark', metavar='REF')
    a = ap.parse_args()
    if a.mark:
        return mark(a.mark)

    source = load_source()
    base = source['commit']
    if git('cat-file', '-e', base + '^{commit}', check=False).returncode:
        print(f'The docs commit {base} is not in this clone. Fetch more history (git fetch --unshallow).')
        sys.exit(2)
    if git('merge-base', '--is-ancestor', base, a.to, check=False).returncode:
        print(f'{base} is not an ancestor of {a.to}. Was history rewritten? Compare by hand, then --mark.')
        sys.exit(2)

    log = git('log', '--reverse', '--no-merges', '--format=@@%H%x09%cs%x09%s', '--name-only', f'{base}..{a.to}').stdout
    found, files = [], set()
    for block in log.split('@@')[1:]:
        head, *paths = [line for line in block.splitlines() if line.strip()]
        sha, date, subject = head.split('\t', 2)
        hits = relevant(paths, source)
        if hits:
            found.append((sha, date, subject, hits))
            files.update(hits)

    if not found:
        print(f'Docs are up to date: no watched code changed since {base[:7]} ({source["checked"]}).')
        sys.exit(0)

    print(f'{len(found)} commit(s) since {base[:7]} change watched code:\n')
    for sha, date, subject, hits in found:
        print(f'{sha[:7]} {date} {subject}')
        for p in hits:
            print(f'    {p}')
    print(f'\n{len(files)} file(s) changed in total.')
    if a.diff:
        print()
        sys.stdout.write(git('diff', f'{base}..{a.to}', '--', *sorted(files)).stdout)
    sys.exit(10)


if __name__ == '__main__':
    main()
