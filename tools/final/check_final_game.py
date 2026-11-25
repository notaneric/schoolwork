"""Play-through checks for chem1211-final-game.html (cloned from tools/exam3/check_exam3_game.py).

Usage: python tools/final/check_final_game.py <page.html> <screenshot dir> [--only-lock] [--http]
(--http serves the page from a local server so the YouTube embed path runs; without it the page is a
file:// URL and the checker expects the video to open on YouTube in a new tab instead.)
Covers: open access (all 37 levels and the boss open on a fresh start, any level playable in any
order), XP math, the second-try flow, typed answers driven by the page's own checkTyped, the
20-question, 40-minute boss, persistence across reload, reduced motion, carets/sup rendering, overflow at
1280/390/320 on every lesson and a practice screen.

Failing controls (each must FAIL on the named checks; the first two restore the old gating, the
third drops the closing-parenthesis subscript rule and must fail the subify checks, the fourth
restores the old minus-stripping norm and must fail the typed Avogadro and -40 °C cases):
  sed 's/const unlocked = () => true;/const unlocked = n => n === 1;/' page.html > mutant.html
  sed 's/const bossUnlocked = () => true;/const bossUnlocked = () => false;/' page.html > mutant2.html
  python -c "import sys;s=open(sys.argv[1],encoding='utf-8').read();open(sys.argv[2],'w',encoding='utf-8').write(s.replace(\".replace(/\\)(\\d+)/g, ')<sub>$1</sub>')\", ''))" page.html mutant3.html
  python tools/final/check_final_game.py mutant.html <dir> --only-lock
"""
import pathlib
import re
import sys

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding='utf-8')  # failure messages carry arrows and sub tags; a cp1252 console crashed on them
SRC = pathlib.Path(sys.argv[1]).resolve()
OUT = pathlib.Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
ONLY_LOCK = '--only-lock' in sys.argv
URL = SRC.as_uri()
if '--http' in sys.argv:
    # serve over http so the embed path (what GitHub Pages does) is tested instead of the file:// fallback
    import functools
    import http.server
    import threading

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass

    srv = http.server.ThreadingHTTPServer(('127.0.0.1', 0), functools.partial(Quiet, directory=str(SRC.parent)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    URL = f'http://127.0.0.1:{srv.server_address[1]}/{SRC.name}'
KEY = 'chem1211fin_game_v1'
TYPED_N = int(sys.argv[sys.argv.index('--typed') + 1]) if '--typed' in sys.argv else -1  # exact typed count, from the contract line
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
    ok('<sub>' not in t and '<sup>' not in t and 'undefined' not in t and not re.search(r'\bNaN\b', t), f'{tag}: no literal tags, undefined or NaN')
    ok(not re.search('[—·]', t), f'{tag}: no em dash or middot in visible text')
    ok('^' not in t, f'{tag}: no literal caret in visible text')
    ok('->' not in t, f'{tag}: no ASCII arrow in visible text (it should render as one arrow)')


def overflow(pg, w, tag):
    sw = pg.evaluate('document.documentElement.scrollWidth')
    ok(sw <= w, f'{tag}: scrollWidth {sw} <= {w}')


def canon(s):
    """Text as data and as displayed compare equal: the page draws -> as an arrow, carets as superscripts,
    minus signs as real minus signs, and binds some spaces as non-breaking."""
    s = s.replace('→', '->').replace('−', '-').replace('^', '')
    return re.sub(r'\s+', '', s)


def find_q(pg, Q):
    prompt = norm(pg.inner_text('.prompt'))
    # the page shows "->" as one arrow, so compare against the stem as displayed
    return next(x for x in Q if canon(x['q']) == canon(pg.inner_text('.prompt')))


def click_answer(pg, q, right):
    if q['t'] == 'type':
        pg.fill('#ans', q['ans'] if right else 'zzz')
        pg.press('#ans', 'Enter')
        return
    tiles = pg.locator('.tile')
    for i in range(tiles.count()):
        is_right = canon(tiles.nth(i).locator('span').nth(1).inner_text()) == canon(q['a'][0])
        if is_right == right:
            tiles.nth(i).click()
            return
    raise AssertionError('no tile matched for ' + q['q'])


def play_level(pg, mode, shots=None, inspect=None):
    """mode: right | wrong | first3wrong. inspect(stage) runs on the first question ('q') and after its answer ('fb')."""
    Q = pg.evaluate('Q')
    streak = pg.evaluate('streak')
    exp, first, saw_retry = 0, 0, False
    pg.click('#go')
    for k in range(80):
        if pg.locator('.result').count():
            break
        q = find_q(pg, Q)
        if k == 0 and inspect:
            inspect('q')
        retry = pg.locator('.chip', has_text='Second try').count() > 0
        saw_retry = saw_retry or retry
        right = True if mode == 'right' else retry if mode == 'wrong' else (retry or first >= 3)
        click_answer(pg, q, right)
        if k == 0 and inspect:
            inspect('fb')
        if right:
            streak += 1
            exp += 5 if retry else (20 if q['t'] == 'type' else 10) + (5 if streak >= 3 else 0)
        else:
            streak = 0
        if not retry:
            first += 1
        if shots is not None and not right and q['t'] == 'mc' and 'fb' not in shots:
            shots['fb'] = True
            pg.screenshot(path=str(OUT / 'fin_feedback_390.png'))
        pg.click('#next')
    return exp, saw_retry, first


def lab(pg, n):
    return pg.get_attribute(f'.node[data-lv="{n}"]', 'aria-label') or ''


with sync_playwright() as p:
    b = p.chromium.launch()

    # 1. fresh start, open access (the failing controls target these)
    ctx, pg, errs = new_page(b, 1280)
    open_set = [n for n in range(1, 38) if 'locked' not in lab(pg, n)]
    ok(open_set == list(range(1, 38)), f'lock: fresh start opens all 37 levels (open: {open_set})')
    ok(pg.locator('.node.locked').count() == 0 and pg.locator('.label.dim').count() == 0, 'lock: no node or label renders locked')
    ok('locked' not in pg.get_attribute('#boss', 'aria-label'), 'lock: boss open on a fresh start')
    ok('Every level is open' in pg.inner_text('.hint'), 'lock: the hint says every level is open')
    pg.click('.node[data-lv="9"]')
    pg.wait_for_timeout(150)
    # text_content, not inner_text: .kicker is uppercased by CSS. Back is clicked only if the screen
    # changed, so a gated mutant fails these named checks instead of crashing on a missing #back.
    opened = pg.locator('#go').count() == 1
    ok(opened and 'Level 9 of 37' in (pg.text_content('.kicker') or ''), 'lock: level 9 opens with nothing cleared')
    if pg.locator('#back').count():
        pg.click('#back')
        pg.wait_for_timeout(200)
    pg.click('#boss')
    pg.wait_for_timeout(150)
    ok(pg.locator('#go').count() == 1 and '40 minutes' in pg.inner_text('body'), 'lock: boss round opens with nothing cleared')
    if pg.locator('#back').count():
        pg.click('#back')
        pg.wait_for_timeout(200)
    ok(pg.locator('.path').count() == 1, 'lock: back returns to the path')
    # formula rendering, driven by the page's own subify (control: drop the ")" rule and this fails)
    SUB_CASES = {
        'Pb(NO3)2 -> PbI2': 'Pb(NO<sub>3</sub>)<sub>2</sub> → PbI<sub>2</sub>',
        '3 Ca(OH)2 and (NH4)2SO4': '3&nbsp;Ca(OH)<sub>2</sub> and (NH<sub>4</sub>)<sub>2</sub>SO<sub>4</sub>',
        'SO4^2- and 10^-3 and [Ar]4s^2': 'SO<sub>4</sub><sup>2−</sup> and 10<sup>−3</sup> and [Ar]4s<sup>2</sup>',
        'E = 6.626 x 10^-34 J': 'E = 6.626&nbsp;x&nbsp;10<sup>−34</sup> J',
        'gives 70.4 g NH3 from N2 + 3 H2': 'gives 70.4&nbsp;g&nbsp;NH<sub>3</sub> from N<sub>2</sub> + 3&nbsp;H<sub>2</sub>',
        'V = 31.4 - 25.0 = 6.4 mL': 'V = 31.4 −&nbsp;25.0 = 6.4 mL',
        '(Handout 17, #5) at 25 C': '(Handout 17, #5) at 25 C',
    }
    for src, want in SUB_CASES.items():
        got = pg.evaluate('(s) => { const d = document.createElement("div"); d.textContent = s; document.body.appendChild(d); subify(d); const h = d.innerHTML; d.remove(); return h; }', src)
        ok(got == want, f'subify({src!r}) gives {got!r}, want {want!r}')

    # typed answers, driven by the page itself
    Q = pg.evaluate('Q')
    typed = [i for i, q in enumerate(Q) if q['t'] == 'type']
    ok(len(typed) == TYPED_N, f'{len(typed)} typed questions (want {TYPED_N})')
    for i in typed:
        ok(pg.evaluate('([i]) => checkTyped(Q[i], Q[i].ans)', [i]), f'typed #{i} accepts its own ans {Q[i]["ans"]!r}')
    cases = {
        'Mass of NaCl': (['7.50 g', '7.50'], ['7.5', '7.6']),
        'Empirical formula, as CxHyOz': (['C4H8O', 'c4h8o'], ['C4H8O2', 'C2H4O']),
        'Name the ion OH': (['hydroxide', 'Hydroxide ion'], ['hydroxyl', 'hydronium']),
        # control: the old norm stripped every minus sign and accepted both wrong answers below
        'Write Avogadro': (['6.022 x 10^23', '6.022x10^23'], ['6.022 x 10^-23', '6.022 x 10^22']),
        'What is -40 °C in kelvin': (['233', '233 K'], ['-233', '313']),
    }
    for key, (acc, rej) in cases.items():
        idx = [i for i in typed if key in Q[i]['q']]
        ok(len(idx) >= 1, f'typed case found for "{key}"')
        for i in idx[:1]:
            for s in acc:
                ok(pg.evaluate('([i, s]) => checkTyped(Q[i], s)', [i, s]), f'typed "{key}" accepts {s!r}')
            for s in rej:
                ok(not pg.evaluate('([i, s]) => checkTyped(Q[i], s)', [i, s]), f'typed "{key}" rejects {s!r}')

    if ONLY_LOCK:
        b.close()
        print('PASS' if not fails else 'FAIL')
        for m in fails:
            print('  FAIL', m)
        sys.exit(0 if not fails else 1)

    ok(norm(pg.text_content('.tag')) == 'Start', 'path: Start tag on a fresh start')
    ok(pg.locator('div.unit').count() == 8, 'path: eight unit headers')
    ok(pg.locator('.node[data-lv]').count() == 37, 'path: 37 level nodes')
    ok('Final exam study game' in pg.inner_text('h1'), 'title h1 is "Final exam study game"')
    ok('/111' in pg.evaluate("document.querySelector('#h-st').parentElement.innerText"), 'HUD: star max is /111')
    text_ok(pg, 'path fresh 1280')


    pg.click('.node[data-lv="1"]')
    ok(pg.locator('.box').count() >= 2, 'L1 lesson: at least two boxes')
    vid1 = pg.evaluate('VIDEOS[1].id')
    ok(pg.locator('.vid').count() == 1 and pg.locator('.also a').count() == 1, 'L1: video and an alternate link')
    if URL.startswith('file:'):
        # embeds fail on file:// (YouTube Error 153), so the local page opens YouTube in a new tab
        with pg.context.expect_page() as newp:
            pg.click('.vid')
        purl = newp.value.url
        newp.value.close()
        ok('youtube.com/watch?v=' + vid1 in purl, f'L1: a local copy opens the video on YouTube ({purl[:70]})')
        ok(pg.locator('iframe.vframe').count() == 0, 'L1: no dead embed on a local copy')
    else:
        pg.click('.vid')
        src = pg.get_attribute('iframe.vframe', 'src') or ''
        ok('youtube-nocookie.com/embed/' + vid1 in src, f'L1: the video swaps in an embed ({src[:70]})')
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
    ok(pg.locator('#go').count() == 1, 'Next level opens a lesson')
    ok(pg.locator('.vid').count() == 1, 'L2: one video')
    text_ok(pg, 'L2 lesson')
    exp, retry, n2 = play_level(pg, 'first3wrong')
    ok(retry, 'L2: missed questions come back as a second try')
    exp_st = 3 if (n2 - 3) / n2 >= 0.9 else 2 if (n2 - 3) / n2 >= 0.75 else 1 if (n2 - 3) / n2 >= 0.6 else 0
    ok(pg.locator('.big-stars svg.on').count() == exp_st, f'L2: 3 misses of {n2} gives {exp_st} star(s) per the page rule (>=.9/.75/.6)')
    pg.click('#back')
    pg.wait_for_timeout(250)
    ok(pg.locator('.path').count() == 1, 'Back arrow returns to the path')
    ok(f'{exp_st} of 3 stars' in lab(pg, 2) and 'locked' not in lab(pg, 3), f'Path: level 2 shows {exp_st} star(s) and level 3 opens')
    ok(all('locked' not in lab(pg, n) for n in (4, 5, 6, 7)), 'Path: unplayed levels 4 to 7 stay open')
    ok(pg.locator('.stop', has=pg.locator('.node[data-lv="3"]')).locator('.tag').count() == 1, 'Path: the Next tag moves to level 3')

    pg.click('.node[data-lv="3"]')
    play_level(pg, 'wrong')
    ok('Not cleared yet' in pg.inner_text('.result h2'), 'L3 all wrong: not cleared')
    ok(pg.locator('.big-stars svg.on').count() == 0, 'L3 all wrong: 0 stars')
    ok('Clearing it takes' in pg.inner_text('.result'), 'L3: says what clearing takes')
    pg.click('#home')
    pg.wait_for_timeout(250)
    ok('locked' not in lab(pg, 4), 'L4 stays open after a failed level 3')

    pg.click('.node[data-lv="7"]')
    ok(pg.locator('#go').count() == 1, 'L7 opens with no stars on 4 to 6')
    pg.click('#back')
    pg.wait_for_timeout(200)

    pg.reload()
    pg.wait_for_timeout(250)
    ok('3 of 3 stars' in lab(pg, 1) and f'{exp_st} of 3 stars' in lab(pg, 2), 'Progress survives a reload')
    pg.screenshot(path=str(OUT / 'fin_path_1280.png'))
    ok(not errs, f'1280 run: console/page errors {errs[:3]}')
    ctx.close()

    # 2. boss round
    ctx, pg, errs = new_page(b, 390)
    set_state(pg, {str(n): 1 for n in range(1, 37)}, 0, 500)
    ok('locked' not in pg.get_attribute('#boss', 'aria-label'), 'Boss open with 36 of 37 levels starred')
    set_state(pg, {str(n): 3 for n in range(1, 38)}, 0, 500)
    ok('locked' not in pg.get_attribute('#boss', 'aria-label'), 'Boss open when all 37 levels have a star')
    ok(norm(pg.text_content('.tag')) == 'Boss', 'Path: the Boss tag shows once every level is cleared')
    ok(pg.inner_text('#h-st') == '111', 'HUD: 111 stars when all 3-starred')
    overflow(pg, 390, 'path 390, all cleared')
    pg.click('#boss')
    ok('40 minutes' in pg.inner_text('body') and pg.evaluate('BOSS_SECS') == 2400 and pg.evaluate('BOSS_N') == 20, 'Boss: 20 questions on a 2400 s clock')
    pg.click('#go')
    Q = pg.evaluate('Q')
    for k in range(20):
        q = find_q(pg, Q)
        ok(q['t'] == 'mc', f'boss question {k + 1} is multiple choice')
        if k == 2:
            text_ok(pg, 'boss question')
            pg.screenshot(path=str(OUT / 'fin_boss_390.png'))
        click_answer(pg, q, True)
        pg.click('#next')
    ok('20 of 20 right' in pg.inner_text('.result h2'), 'Boss: 20 of 20 right')
    ok('New best' in pg.inner_text('.result'), 'Boss: new best shown')
    pg.click('#home')
    pg.wait_for_timeout(250)
    ok('Best: 20 of 20' in pg.inner_text('.path'), 'Path shows the boss best')
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

    # 4. layout at 1280, 390, 320: every lesson and a practice screen
    for w in (1280, 390, 320):
        ctx, pg, errs = new_page(b, w)
        overflow(pg, w, f'path {w}')
        text_ok(pg, f'path {w}')
        if w == 390:
            pg.screenshot(path=str(OUT / 'fin_path_390.png'), full_page=True)
        set_state(pg, {str(n): 1 for n in range(1, 38)})
        for n in range(1, 38):
            pg.click(f'.node[data-lv="{n}"]')
            overflow(pg, w, f'L{n} lesson {w}')
            text_ok(pg, f'L{n} lesson {w}')
            if n == 25:
                ok(pg.locator('#pol tr').count() == 13, f'L25 lesson {w}: shape table has 13 rows')
                tw = pg.evaluate("(() => { const r = document.querySelector('#pol').closest('.scroll').getBoundingClientRect(); return [r.left, r.right]; })()")
                ok(tw[0] >= -1 and tw[1] <= w + 1, f'L25 lesson {w}: shape table scroll box inside viewport {tw}')
            if n == 18:
                ok(pg.locator('sup').count() >= 1, f'L18 lesson {w}: charges render as <sup>')
            if w == 390 and n == 2:
                pg.screenshot(path=str(OUT / 'fin_lesson2_390.png'), full_page=True)
            if w == 390 and n == 25:
                pg.screenshot(path=str(OUT / 'fin_lesson25_390.png'), full_page=True)

            def insp(stage, n=n, w=w):
                overflow(pg, w, f'L{n} practice {stage} {w}')
                text_ok(pg, f'L{n} practice {stage} {w}')
            shots = {} if (w == 390 and n == 4) else None
            play_level(pg, 'first3wrong', shots, insp)
            overflow(pg, w, f'L{n} result {w}')
            pg.click('#back')
            pg.wait_for_timeout(200)
        ok(not errs, f'{w} run: console/page errors {errs[:3]}')
        ctx.close()
    b.close()

print('PASS' if not fails else 'FAIL', f'({len(oks)} ok, {len(fails)} failed)')
for m in fails:
    print('  FAIL', m)
sys.exit(1 if fails else 0)  # a failed check must fail the run, not just print FAIL
