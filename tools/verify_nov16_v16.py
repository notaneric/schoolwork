"""Verify the v16 dashboard change: Exam 3 scope from its study guide + the Exam 3 game link.

Usage: python tools/verify_nov16_v16.py [page.html]   (default: index.html)
Devices: fresh; a real v15 device (state made by loading `git show HEAD:index.html`, then carried
into the new page with an init script); a v15 device whose Exam 3 note was hand-edited (must be
kept); two reloads (idempotent). Failing control: `--control` runs the fresh-device checks against
the pre-patch page from git, and they must FAIL on the scope and link checks.
"""
import pathlib
import subprocess
import sys
import tempfile

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parents[1]
KEY = 'boris_school_fall2026'
CONTROL = '--control' in sys.argv
args = [a for a in sys.argv[1:] if not a.startswith('--')]
old_html = subprocess.run(['git', 'show', 'HEAD:index.html'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8').stdout
assert 'EXAM3_NOTES_V14' in old_html, 'HEAD is not the v15 page'
tmp = pathlib.Path(tempfile.mkdtemp())
OLD = tmp / 'index_v15.html'
OLD.write_text(old_html, encoding='utf-8')
NEW = OLD if CONTROL else (pathlib.Path(args[0]).resolve() if args else ROOT / 'index.html')
fails, oks = [], []


def ok(c, m):
    (oks if c else fails).append(m)


def exam3(pg):
    return pg.evaluate("k => { const d = JSON.parse(localStorage.getItem(k) || 'null'); const a = d && d.assignments.find(x => x.id === 'chem1211-exam3'); return a ? a.notes : null; }", KEY)


def open_page(b, path, state=None):
    ctx = b.new_context(viewport={'width': 1280, 'height': 900})
    if state is not None:
        ctx.add_init_script(f"if (!sessionStorage.getItem('seeded')) {{ localStorage.setItem({KEY!r}, {state!r}); sessionStorage.setItem('seeded', '1'); }}")
    pg = ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'supabase' not in m.text.lower() else None)
    pg.goto(path.as_uri())
    pg.wait_for_timeout(600)
    return ctx, pg, errs


with sync_playwright() as p:
    b = p.chromium.launch()
    # fresh device
    ctx, pg, errs = open_page(b, NEW)
    n = exam3(pg)
    ok(bool(n) and n.startswith('SCOPE IS SET: the Exam 3 study guide'), f'fresh: Exam 3 note carries the study-guide scope ({(n or "")[:50]!r})')
    pg.evaluate("setView('resources')")
    pg.wait_for_timeout(300)
    ok(pg.locator('a[href="chem1211-exam3-game.html"]').count() == 1, 'fresh: Resources links the Exam 3 game')
    ok('Sixteen levels on Ch 4.4 to 4.6' in pg.inner_text('body'), 'fresh: the Resources card describes the Exam 3 game')
    ok(pg.locator('a[href="chem1211-polarity-imf.html"]').count() == 0, 'fresh: the polarity card was replaced, not duplicated')
    ok(not errs, f'fresh: no page errors {errs[:2]}')
    ctx.close()
    if not CONTROL:
        # real v15 device, then the new page
        c0, p0, _ = open_page(b, OLD)
        v15 = p0.evaluate('k => localStorage.getItem(k)', KEY)
        c0.close()
        ok(v15 and 'chem1211_nov16_v16' not in v15, 'v15 device state built from the HEAD page')
        ctx, pg, errs = open_page(b, NEW, v15)
        n = exam3(pg)
        ok(bool(n) and n.startswith('SCOPE IS SET'), 'v15 device: stored note upgraded to v16')
        flag = pg.evaluate("k => JSON.parse(localStorage.getItem(k)).meta.chem1211_nov16_v16", KEY)
        ok(flag is True, 'v15 device: v16 flag set')
        for i in range(2):
            pg.reload()
            pg.wait_for_timeout(400)
            ok(exam3(pg) == n, f'v15 device: note unchanged after reload {i + 1}')
        ok(not errs, f'v15 device: no page errors {errs[:2]}')
        ctx.close()
        # hand-edited note survives
        import json
        d = json.loads(v15)
        for a in d['assignments']:
            if a['id'] == 'chem1211-exam3':
                a['notes'] = 'My own note about Exam 3.'
        ctx, pg, errs = open_page(b, NEW, json.dumps(d))
        ok(exam3(pg) == 'My own note about Exam 3.', 'edited device: a hand-edited note is kept')
        ctx.close()
    b.close()

for f in fails:
    print('FAIL', f)
print(('CONTROL ' if CONTROL else '') + ('PASS' if not fails else 'FAIL') + f' ({len(oks)} ok, {len(fails)} failed)')
sys.exit(1 if fails else 0)
