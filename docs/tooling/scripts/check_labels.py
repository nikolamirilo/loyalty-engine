"""Check that the product words in the docs really exist in the code.

    python3 <skill>/scripts/check_labels.py <docs-dir> <code-dir> [<code-dir> ...]

Collects every UI name in the built docs (buttons, fields and tabs written with the .b .f .t spans,
places and menu items with .m) and every quoted message ("..."), then looks for each one, letter by
letter, in the source files under the code folders. It prints the ones it cannot find. Each one is
a typo, a paraphrase that should be an exact quote, an example you made up on purpose, or text the
product builds at runtime (check those by hand). Pass every folder that holds user-visible text:
the frontend, translation files, and backend code that returns messages to users.
"""
import html
import os
import re
import sys

EXT = {'.ts', '.tsx', '.js', '.jsx', '.vue', '.svelte', '.json', '.yaml', '.yml', '.html', '.cs', '.py', '.rb',
       '.go', '.java', '.kt', '.swift', '.php', '.po', '.properties', '.resx', '.xml', '.md', '.txt', '.cshtml', '.razor', '.erb', '.textproto'}
SKIP_DIRS = {'node_modules', '.git', 'dist', 'build', '.next', 'out', 'coverage', 'bin', 'obj', '__pycache__', 'vendor', '.venv'}


def load_code(dirs):
    chunks = []
    for d in dirs:
        for root, subdirs, files in os.walk(d):
            subdirs[:] = [s for s in subdirs if s not in SKIP_DIRS and not s.startswith('.')]
            for f in files:
                p = os.path.join(root, f)
                if os.path.splitext(f)[1].lower() not in EXT or os.path.getsize(p) > 3_000_000:
                    continue
                try:
                    chunks.append(open(p, encoding='utf-8', errors='ignore').read())
                except OSError:
                    pass
    text = '\n'.join(chunks)
    # JSX and templates often split text across lines and escape apostrophes
    flat = re.sub(r'\s+', ' ', text.replace("\\'", "'").replace('&apos;', "'").replace('&#39;', "'"))
    return flat


def clean(s):
    s = re.sub(r'<svg.*?</svg>', ' ', s, flags=re.S)
    s = re.sub(r'<[^>]+>', ' ', s)
    s = html.unescape(s)
    return re.sub(r'\s+', ' ', s).strip()


def collect(docs_html):
    body = re.sub(r'<script.*?</script>|<style.*?</style>', ' ', docs_html, flags=re.S)
    body = re.sub(r'<figure class="shot.*?</figure>', ' ', body, flags=re.S)  # screens repeat the same words
    names, places = set(), set()
    for m in re.finditer(r'<span class="(b|b alt|f|m|t)">(.*?)</span>', body, re.S):
        t = clean(m.group(2))
        if 2 <= len(t) <= 80:
            (places if m.group(1) == 'm' else names).add(t)
    # quotes are matched inside one block of text, so a stray inch mark cannot pair across paragraphs
    blocks = re.sub(r'</?(p|li|td|th|dd|dt|h[1-6]|div|figcaption|summary|tr|ul|ol)\b[^>]*>', '\n', body)
    quotes = set()
    for block in clean_lines(blocks):
        for m in re.finditer(r'"([^"]{3,200})"', block):
            q = m.group(1).strip()
            if not re.search(r'[A-Za-z]{2}', q) or q.startswith(('http', '#', '.', '/')):
                continue
            quotes.add(q)
    return names, places, quotes


def clean_lines(text):
    for line in text.split('\n'):
        line = clean(line)
        if line:
            yield line


def found(s, code):
    parts = [p.strip(' .,:;') for p in re.split(r'…|\.\.\.', s)]
    parts = [p for p in parts if len(p) >= 3]
    return all(p in code for p in parts) if parts else True


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    docs_dir, code_dirs = sys.argv[1], sys.argv[2:]
    p = os.path.join(docs_dir, 'dist', 'docs.html')
    if not os.path.exists(p):
        sys.exit(f'Build first: {p} is missing')
    code = load_code(code_dirs)
    names, places, quotes = collect(open(p, encoding='utf-8').read())
    miss_n = sorted(n for n in names if not found(n, code))
    miss_q = sorted(q for q in quotes if not found(q, code))
    miss_p = sorted(n for n in places if not found(n, code))
    print(f'Checked {len(names)} buttons, fields and tabs, {len(places)} places and menu items, and '
          f'{len(quotes)} quotes against {len(code) // 1024} KB of code.')
    if miss_n:
        print('\nButtons, fields and tabs not found in the code (most likely typos or paraphrases):')
        for n in miss_n:
            print('  ' + n)
    if miss_q:
        print('\nQuotes not found in the code (fix them, or confirm the text is built at runtime or is an example):')
        for q in miss_q:
            print('  "' + q + '"')
    if miss_p:
        print('\nPlaces and menu items not found (often fine: descriptions such as "Select a project" are not labels):')
        for n in miss_p:
            print('  ' + n)
    if not (miss_n or miss_q or miss_p):
        print('Every UI name and quote was found in the code.')


if __name__ == '__main__':
    main()
