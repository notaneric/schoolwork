"""Play-through checks for the study-game pages (first: chem1211-polarity-imf.html).

Usage: python tools/check_polarity_game.py <page.html> <screenshot dir> [--only-lock]
Covers: unlock rules, XP math, the second-try flow, typed-answer accept/reject, the boss timer,
persistence across reload, reduced motion, overflow at 1280/390/320 on every level.

Failing control (run it whenever the unlock code changes; it must FAIL on the three lock checks):
  sed 's/const unlocked = n => n === 1 ||/const unlocked = n => true ||/' page.html > mutant.html
  python tools/check_polarity_game.py mutant.html <dir> --only-lock
For a new game page, swap the level-specific assertions (L1 tiles, L2 table rows, typed cases).
"""
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

SRC = pathlib.Path(sys.argv[1]).resolve()
OUT = pathlib.Path(sys.argv[2])
ONLY_LOCK = '--only-lock' in sys.argv
URL = SRC.as_uri()
KEY = 'chem1211q3_game_v1'
fails, oks = [], []


def ok(cond, msg):
    (oks if cond else fails).append(msg)


def norm(s):
    return re.sub(r'\s+', ' ', s).strip()


def new_page(b, w, h=860, rm='no-preference'):
    ctx = b.new_context(viewport={'width': w, 'height': h}, reduced_motion=rm)
    pg = ctx.new_page()
    errs = []
    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' and 'ytimg' not in m.text and 'youtube' not in m.text else None)
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(URL)
    pg.wait_for_timeout(250)
    return ctx, pg, errs


def set_state(pg, stars, boss=0, xp=0):
    pg.evaluate('([k, v]) => localStorage.setItem(k, JSON.stringify(v))', [KEY, {'xp': xp, 'stars': stars, 'boss': boss}])
    pg.reload()
    pg.wait_for_timeout(250)


def text_ok(pg, tag):
    t = pg.inner_text('body')
    ok('<sub>' not in t and 'undefined' not in t and 'NaN' not in t, f'{tag}: no literal tags, undefined or NaN')
    ok(not re.search('[—·]', t), f'{tag}: no em dash or middot in visible text')


def overflow(pg, w, tag):
    sw = pg.evaluate('document.documentElement.scrollWidth')
    ok(sw <= w, f'{tag}: scrollWidth {sw} <= {w}')


def find_q(pg, Q):
    prompt = norm(pg.inner_text('.prompt'))
    return next(x for x in Q if norm(x['q']) == prompt)


def click_answer(pg, q, right):
    if q['t'] == 'type':
        pg.fill('#ans', q['ans'] if right else 'zzz')
        pg.press('#ans', 'Enter')
        return
    tiles = pg.locator('.tile')
    for i in range(tiles.count()):
        is_right = norm(tiles.nth(i).locator('span').nth(1).inner_text()) == norm(q['a'][0])
        if is_right == right:
            tiles.nth(i).click()
            return
    raise AssertionError('no tile matched for ' + q['q'])


def play_level(pg, mode, shots=None):
    """mode: right | wrong (wrong first, right on the second try) | first3wrong. Returns (expected xp, saw retry, first-pass count)."""
    Q = pg.evaluate('Q')
    streak = pg.evaluate('streak')
    exp, first, saw_retry = 0, 0, False
    pg.click('#go')
    for _ in range(60):
        if pg.locator('.result').count():
            break
        q = find_q(pg, Q)
        retry = pg.locator('.chip', has_text='Second try').count() > 0
        saw_retry = saw_retry or retry
        right = True if mode == 'right' else retry if mode == 'wrong' else (retry or first >= 3)
        click_answer(pg, q, right)
        if right:
            streak += 1
            exp += 5 if retry else (20 if q['t'] == 'type' else 10) + (5 if streak >= 3 else 0)
        else:
            streak = 0
        if not retry:
            first += 1
        if shots is not None and not right and q['t'] == 'mc' and 'fb' not in shots:
            shots['fb'] = True
            pg.screenshot(path=str(OUT / 'v2_feedback_390.png'))
        pg.click('#next')
    return exp, saw_retry, first


with sync_playwright() as p:
    b = p.chromium.launch()

    # 1. fresh start, lock rules (the negative control targets these)
    ctx, pg, errs = new_page(b, 1280)
    labels = [pg.get_attribute(f'.node[data-lv="{n}"]', 'aria-label') for n in range(1, 6)]
    ok('locked' not in labels[0] and all('locked' in l for l in labels[1:]), 'lock: only level 1 open on a fresh start')
    ok('locked' in pg.get_attribute('#boss', 'aria-label'), 'lock: boss locked on a fresh start')
    pg.click('.node[data-lv="2"]')
    pg.wait_for_timeout(150)
    ok(pg.locator('#go').count() == 0 and pg.locator('.path').count() == 1, 'lock: clicking locked level 2 stays on the path')
    ok('Clear level 1 first' in pg.inner_text('body'), 'lock: the toast names the level to clear')
    if ONLY_LOCK:
        b.close()
        print('PASS' if not fails else 'FAIL')
        for m in fails:
            print('  FAIL', m)
        sys.exit(0 if not fails else 1)

    ok(norm(pg.text_content('.tag')) == 'Start', 'path: Start tag on a fresh start')
    text_ok(pg, 'path fresh 1280')

    pg.click('.node[data-lv="1"]')
    ok(pg.locator('.el').count() == 6, 'L1 lesson: six element tiles')
    ok(pg.locator('.vid').count() == 1 and pg.locator('.also a').count() == 1, 'L1: video and an alternate link')
    pg.click('.vid')
    src = pg.get_attribute('iframe.vframe', 'src') or ''
    ok('youtube-nocookie.com/embed/QPd1nYyNhyc' in src, f'L1: the video swaps in an embed ({src[:70]})')
    text_ok(pg, 'L1 lesson')
    xp0 = pg.evaluate('S.xp')
    exp, _, n1 = play_level(pg, 'right')
    canvas = pg.locator('canvas.confetti').count()
    ok(pg.locator('.big-stars svg.on').count() == 3, 'L1 all right: 3 stars')
    ok('Level 1 cleared' in pg.inner_text('.result h2'), 'L1: cleared heading')
    ok(pg.evaluate('S.xp') - xp0 == exp + 30, f'L1: XP gained {pg.evaluate("S.xp") - xp0} == expected {exp + 30}')
    ok(canvas == 1, 'L1: celebration shown when motion is allowed')
    ok(pg.inner_text('#h-st') == '3', 'HUD: 3 stars after level 1')
    text_ok(pg, 'L1 result')

    pg.click('#fwd')
    ok('Polar molecules' in pg.inner_text('h1'), 'Next level opens level 2')
    ok(pg.locator('#pol tr').count() == 13, 'L2: shape table has 13 rows')
    exp, retry, n2 = play_level(pg, 'first3wrong')
    ok(retry, 'L2: missed questions come back as a second try')
    ok(pg.locator('.big-stars svg.on').count() == 1, f'L2: 3 misses of {n2} gives 1 star')
    pg.click('#back')
    pg.wait_for_timeout(250)
    ok(pg.locator('.path').count() == 1, 'Back arrow returns to the path')
    l2 = pg.get_attribute('.node[data-lv="2"]', 'aria-label')
    l3 = pg.get_attribute('.node[data-lv="3"]', 'aria-label')
    ok('1 of 3 stars' in l2 and 'locked' not in l3, 'Path: level 2 shows 1 star and level 3 opens')
    ok(pg.locator('.stop', has=pg.locator('.node[data-lv="3"]')).locator('.tag').count() == 1, 'Path: the Next tag moves to level 3')

    pg.click('.node[data-lv="3"]')
    play_level(pg, 'wrong')
    ok('Not cleared yet' in pg.inner_text('.result h2'), 'L3 all wrong: not cleared')
    ok(pg.locator('.big-stars svg.on').count() == 0, 'L3 all wrong: 0 stars')
    ok('Clearing it takes' in pg.inner_text('.result'), 'L3: says what clearing takes')
    pg.click('#home')
    pg.wait_for_timeout(250)
    ok('locked' in pg.get_attribute('.node[data-lv="4"]', 'aria-label'), 'L4 stays locked after a failed level 3')

    cases = {
        '3.5': (['3.5', '3.50', ' 3.5 '], ['3', '35', '4.0']),
        '4.0': (['4', '4.0', '4.00'], ['3.5', '40']),
        '1.0': (['1', '1.0'], ['0.5', '10', '1.5']),
        'nonpolar': (['nonpolar', 'Non-polar', 'non polar', 'NONPOLAR', 'nonpolar molecule'], ['polar', 'non']),
        'dispersion': (['dispersion', 'London dispersion forces', 'london', 'Dispersion force', 'London forces', 'LDF', 'LDFs'], ['dipole', 'hydrogen bonding', 'force']),
        'hydrogen bonding': (['hydrogen bonding', 'H-bonding', 'hydrogen bonds', 'H bond', 'hydrogen bond', 'hydrogen bonding interactions'], ['hydrogen', 'dipole-dipole', 'bonding']),
        'dipole-dipole': (['dipole-dipole', 'dipole dipole forces', 'Dipole-Dipole', 'dipole', 'dipole-dipole interactions'], ['dispersion', 'hydrogen bonding']),
        'H2O': (['H2O', 'h2o', 'water', 'H20'], ['CH4', 'h2']),
    }
    Q = pg.evaluate('Q')
    typed = [i for i, q in enumerate(Q) if q['t'] == 'type']
    ok(len(typed) == 8, f'{len(typed)} typed questions')
    for i in typed:
        acc, rej = cases[Q[i]['ans']]
        for s in acc:
            ok(pg.evaluate('([i, s]) => checkTyped(Q[i], s)', [i, s]), f'typed "{Q[i]["ans"]}" accepts {s!r}')
        for s in rej:
            ok(not pg.evaluate('([i, s]) => checkTyped(Q[i], s)', [i, s]), f'typed "{Q[i]["ans"]}" rejects {s!r}')

    pg.reload()
    pg.wait_for_timeout(250)
    ok('3 of 3 stars' in pg.get_attribute('.node[data-lv="1"]', 'aria-label') and '1 of 3 stars' in pg.get_attribute('.node[data-lv="2"]', 'aria-label'), 'Progress survives a reload')
    pg.screenshot(path=str(OUT / 'v2_path_1280.png'))
    ok(not errs, f'1280 run: console/page errors {errs[:3]}')
    ctx.close()

    # 2. boss round
    ctx, pg, errs = new_page(b, 390)
    set_state(pg, {str(n): 3 for n in range(1, 6)}, 0, 500)
    ok('locked' not in pg.get_attribute('#boss', 'aria-label'), 'Boss unlocks when all five levels are cleared')
    ok(norm(pg.text_content('.tag')) == 'Boss', 'Path: the Boss tag shows once every level is cleared')
    overflow(pg, 390, 'path 390, all cleared')
    pg.click('#boss')
    pg.click('#go')
    Q = pg.evaluate('Q')
    for k in range(6):
        q = find_q(pg, Q)
        ok(q['t'] == 'mc', f'boss question {k + 1} is multiple choice')
        if k == 2:
            pg.screenshot(path=str(OUT / 'v2_boss_390.png'))
        click_answer(pg, q, True)
        pg.click('#next')
    ok('6 of 6 right' in pg.inner_text('.result h2'), 'Boss: 6 of 6 right')
    ok('New best' in pg.inner_text('.result'), 'Boss: new best shown')
    pg.click('#home')
    pg.wait_for_timeout(250)
    ok('Best: 6 of 6' in pg.inner_text('.path'), 'Path shows the boss best')
    pg.click('#boss')
    pg.click('#go')
    pg.evaluate('boss.left = 2')
    pg.wait_for_timeout(2600)
    ok(pg.locator('.result').count() == 1 and 'Time' in pg.text_content('.result .kicker'), 'Boss: the clock running out ends the round')
    ok(not errs, f'boss run: console/page errors {errs[:3]}')
    ctx.close()

    # 3. reduced motion
    ctx, pg, errs = new_page(b, 390, rm='reduce')
    pg.click('.node[data-lv="1"]')
    play_level(pg, 'right')
    ok(pg.locator('canvas.confetti').count() == 0, 'Reduced motion: no confetti')
    ctx.close()

    # 4. layout at phone widths, every level
    for w in (390, 320):
        ctx, pg, errs = new_page(b, w)
        overflow(pg, w, f'path {w}')
        text_ok(pg, f'path {w}')
        if w == 390:
            pg.screenshot(path=str(OUT / 'v2_path_390.png'), full_page=True)
        set_state(pg, {str(n): 1 for n in range(1, 5)})
        for n in range(1, 6):
            pg.click(f'.node[data-lv="{n}"]')
            overflow(pg, w, f'L{n} lesson {w}')
            text_ok(pg, f'L{n} lesson {w}')
            if w == 390 and n == 2:
                pg.screenshot(path=str(OUT / 'v2_lesson2_390.png'), full_page=True)
            shots = {} if (w == 390 and n == 4) else None
            play_level(pg, 'first3wrong', shots)
            overflow(pg, w, f'L{n} result {w}')
            if w == 390 and n == 5:
                pg.screenshot(path=str(OUT / 'v2_result_390.png'))
            pg.click('#back')
            pg.wait_for_timeout(200)
        ok(not errs, f'{w} run: console/page errors {errs[:3]}')
        ctx.close()
    b.close()

print('PASS' if not fails else 'FAIL', f'({len(oks)} ok, {len(fails)} failed)')
for m in fails:
    print('  FAIL', m)
