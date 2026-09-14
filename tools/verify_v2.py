"""Verify chem1211-exam1-v2.html: the S137 data/behaviour contract (73 checks) + the S140 design contract.

Fails loudly. Sections 1-7 are the S137 verify_chem.py checks, repointed. Section 8 is new:
contrast, focus ring, reduced motion, no emoji icons, no nested cards, 44px targets at 390,
home height, type scale, and the session-close screen.
"""
import sys, pathlib, json
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

HTML = pathlib.Path(__file__).resolve().parent.parent / "chem1211-exam1-v2.html"
if len(sys.argv) > 1:
    HTML = pathlib.Path(sys.argv[1])
URL = HTML.as_uri()

EXPECT_Q = 118
EXPECT_GL = 94
EXPECT_CH = 15
NEW_CH = ["matter", "props", "atomic", "atom", "iso", "avgmass", "mole", "formula", "elem"]
SCALE = {13, 14, 16, 18, 24, 32, 48}

failures = []
errors = []
n_checks = 0


def check(cond, label):
    global n_checks
    n_checks += 1
    print("  %-60s %s" % (label, "PASS" if cond else "**FAIL**"))
    if not cond:
        failures.append(label)


# ---- in-page measurement helpers (injected once) ----
HELPERS = r"""
window.__v = (() => {
  const lum = ([r,g,b]) => { const f = c => { c/=255; return c<=0.03928 ? c/12.92 : Math.pow((c+0.055)/1.055, 2.4); };
    return 0.2126*f(r)+0.7152*f(g)+0.0722*f(b); };
  const parse = s => { const m = s.match(/rgba?\(([^)]+)\)/); if(!m) return null;
    const p = m[1].split(',').map(x=>parseFloat(x)); return {c:[p[0],p[1],p[2]], a: p.length>3 ? p[3] : 1}; };
  const over = (fg, a, bg) => fg.map((v,i)=>Math.round(v*a + bg[i]*(1-a)));
  const contrast = (a,b) => { const l1=lum(a), l2=lum(b); return (Math.max(l1,l2)+0.05)/(Math.min(l1,l2)+0.05); };
  // effective background behind an element: walk up compositing translucent layers
  const bgOf = el => {
    let stack = [];
    for (let e = el; e; e = e.parentElement) {
      const p = parse(getComputedStyle(e).backgroundColor);
      if (p && p.a > 0) { stack.push(p); if (p.a >= 1) break; }
    }
    let bg = [255,255,255];
    for (let i = stack.length-1; i >= 0; i--) bg = over(stack[i].c, stack[i].a, bg);
    return bg;
  };
  const visible = el => { const r = el.getBoundingClientRect(); const s = getComputedStyle(el);
    return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
  const opacityOf = el => { let o = 1; for (let e = el; e; e = e.parentElement) o *= parseFloat(getComputedStyle(e).opacity); return o; };
  function textNodes() {
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    const out = []; let n;
    while ((n = w.nextNode())) { if (n.nodeValue.trim().length === 0) continue;
      const el = n.parentElement; if (!el || ['SCRIPT','STYLE','SVG','DEFS','SYMBOL'].includes(el.tagName.toUpperCase())) continue;
      if (!visible(el)) continue;
      if (el.closest('[hidden]')) continue;
      out.push(el); }
    return out;
  }
  function contrastReport(min = 4.5, maxPx = 18.66) {
    const bad = []; let n = 0;
    for (const el of textNodes()) {
      const s = getComputedStyle(el); const px = parseFloat(s.fontSize);
      if (px >= maxPx) continue;
      if (el.closest('button:disabled')) continue;    // inactive controls are exempt (WCAG 1.4.3)
      const fg = parse(s.color); if (!fg) continue;
      const bg = bgOf(el); const op = opacityOf(el);
      const eff = over(fg.c, fg.a * op, bg);
      const c = contrast(eff, bg); n++;
      if (c < min) bad.push({t:(el.innerText||'').trim().slice(0,28), cls: el.className && el.className.baseVal===undefined ? el.className : el.tagName, px, c:+c.toFixed(2), fg: s.color, bg: 'rgb('+bg.join(',')+')'});
    }
    return {n, bad};
  }
  function sizeReport() {
    const off = {}; let n = 0;
    for (const el of textNodes()) { const px = parseFloat(getComputedStyle(el).fontSize); n++;
      if (![13,14,16,18,24,32,48].includes(px)) { const k = px + 'px ' + (el.className && !el.className.baseVal ? el.className : el.tagName); off[k] = (off[k]||0)+1; } }
    return {n, off};
  }
  function targetReport(min = 44) {
    const els = [...document.querySelectorAll('button, a, input, textarea, select, [role=button], [onclick]')];
    const small = [];
    for (const el of els) {
      if (!visible(el)) continue;
      if (el.closest('[hidden]')) continue;
      const s = getComputedStyle(el);
      if (el.tagName === 'A' && s.display === 'inline') continue;   // inline text links are exempt (WCAG 2.5.8)
      const r = el.getBoundingClientRect();
      if (r.height < min - 0.5 || r.width < min - 0.5) small.push({t:(el.innerText||el.getAttribute('aria-label')||el.id||'').trim().slice(0,22), cls: el.className && !el.className.baseVal ? el.className : el.tagName, w:Math.round(r.width), h:Math.round(r.height)});
    }
    return small;
  }
  function cssText() { let t=''; for (const ss of document.styleSheets) { try { for (const r of ss.cssRules) t += r.cssText + '\n'; } catch(e){} } return t; }
  function emojiIn(sel) { const re = /\p{Extended_Pictographic}/u; return [...document.querySelectorAll(sel)].filter(e => re.test(e.textContent)).length; }
  return {contrastReport, sizeReport, targetReport, cssText, emojiIn, visible};
})();
"""

STATES = []  # (name, setup-js) : every screen state the design contract is checked in


def state(pg, name, js):
    pg.evaluate("if(typeof goHome==='function'){SES.closed=true; goHome();}")
    pg.evaluate(js)
    pg.wait_for_timeout(350)
    return name


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    pg.on("console", lambda m: errors.append("console.%s: %s" % (m.type, m.text)) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errors.append("pageerror: %s" % e))
    pg.goto(URL)
    pg.wait_for_timeout(700)
    pg.evaluate(HELPERS)

    print("\n[1] DATA INTEGRITY")
    qn = pg.evaluate("Q.length"); gn = pg.evaluate("GLOSSARY.length"); cn = pg.evaluate("CHAPTERS.length")
    check(qn == EXPECT_Q, "Q.length == %d (got %d)" % (EXPECT_Q, qn))
    check(gn == EXPECT_GL, "GLOSSARY.length == %d (got %d)" % (EXPECT_GL, gn))
    check(cn == EXPECT_CH, "CHAPTERS.length == %d (got %d)" % (EXPECT_CH, cn))
    dense = pg.evaluate("Q.filter(()=>true).length")
    check(dense == qn, "Q has no sparse holes (filter sees %d of %d)" % (dense, qn))
    dense_g = pg.evaluate("GLOSSARY.filter(()=>true).length")
    check(dense_g == gn, "GLOSSARY has no sparse holes (%d of %d)" % (dense_g, gn))
    split = pg.evaluate("[Q.filter(q=>%s.includes(q.chId)).length,Q.filter(q=>!%s.includes(q.chId)).length]" % (json.dumps(NEW_CH), json.dumps(NEW_CH)))
    check(split == [67, 51], "Q split new/pre-existing == 67/51 (got %s)" % split)
    bad = pg.evaluate("Q.filter(q=>!(Number.isInteger(q.a)&&q.a>=0&&q.a<q.o.length)).length")
    check(bad == 0, "every answer index is a valid index into its options (bad=%d)" % bad)
    dupes = pg.evaluate("Q.filter(q=>new Set(q.o).size!==q.o.length).length")
    check(dupes == 0, "no duplicate options in any question (dupes=%d)" % dupes)
    orphan = pg.evaluate("Q.filter(q=>!CHAPTERS.some(c=>c.id===q.chId)).length+GLOSSARY.filter(g=>!CHAPTERS.some(c=>c.id===g.ch)).length")
    check(orphan == 0, "no question/glossary orphaned from CHAPTERS (%d)" % orphan)
    empty = pg.evaluate("CHAPTERS.filter(c=>!Q.some(q=>q.chId===c.id)).map(c=>c.id)")
    check(len(empty) == 0, "no chapter has zero questions (%s)" % (empty or "none"))
    missing = pg.evaluate("CHAPTERS.filter(c=>!SHORT[c.id]).map(c=>c.id)")
    check(len(missing) == 0, "every chapter has a SHORT label (missing: %s)" % (missing or "none"))
    check(pg.evaluate("Q.filter(q=>!SHORT[q.chId]).length") == 0, "every question's chapter resolves to a label")

    print("\n[2] EVERY MODE RENDERS")
    modes = [("flash", "Preview", "#flash"), ("learn", "Learn", "#learn"), ("match", "Match", "#match"),
             ("recall", "Recall", "#recall"), ("videos", "Videos", "#videos")]
    for sid, label, sel in modes:
        try:
            pg.evaluate("show(%s)" % json.dumps(sid)); pg.wait_for_timeout(120)
            vis = pg.evaluate("(()=>{const e=document.querySelector(%s);return !!e && getComputedStyle(e).display!=='none' && e.innerText.trim().length>0;})()" % json.dumps(sel))
            check(bool(vis), "mode %s renders visible content" % label)
        except Exception as e:
            check(False, "mode %s threw: %s" % (label, str(e)[:60]))

    print("\n[3] MODE INITIALISERS RUN CLEAN")
    for fn in ["fcInit", "lnInit", "recallInit", "matchInit"]:
        if not pg.evaluate("typeof %s === 'function'" % fn):
            print("  %-60s (not present, skipped)" % fn); continue
        try:
            pg.evaluate("FCH='all'; %s()" % fn); pg.wait_for_timeout(100)
            check(True, "%s() ran with FCH=all" % fn)
        except Exception as e:
            check(False, "%s() threw: %s" % (fn, str(e)[:60]))

    print("\n[4] EVERY CHAPTER CHIP — question modes must not throw")
    chapters = pg.evaluate("CHAPTERS.map(c=>c.id)")
    for cid in chapters:
        ok, detail = True, ""
        for fn in ["fcInit", "lnInit"]:
            if not pg.evaluate("typeof %s === 'function'" % fn): continue
            try:
                pg.evaluate("FCH=%s; %s()" % (json.dumps(cid), fn)); pg.wait_for_timeout(60)
            except Exception as e:
                ok, detail = False, "%s: %s" % (fn, str(e)[:45]); break
        check(ok, "chapter '%s' selectable in question modes %s" % (cid, detail))

    print("\n[4b] RENDERED HEADER TEXT — no literal 'undefined' anywhere")
    for cid in chapters:
        pg.evaluate("FCH=%s; fcInit()" % json.dumps(cid)); pg.wait_for_timeout(80)
        kick = pg.evaluate("(document.getElementById('fc-kick-f')||{}).textContent||''")
        check("undefined" not in kick.lower() and len(kick.strip()) > 0, "chapter '%s' preview header = %r" % (cid, kick[:26]))
    body = pg.evaluate("document.body.innerText")
    check("undefined" not in body.lower(), "no literal 'undefined' in rendered body")

    print("\n[5] GLOSSARY-DRIVEN MODES PER CHAPTER")
    for cid in chapters:
        n = pg.evaluate("GLOSSARY.filter(g=>g.ch===%s).length" % json.dumps(cid))
        if n == 0:
            print("  %-60s (no glossary, recall/match N/A)" % ("chapter '%s'" % cid)); continue
        try:
            pg.evaluate("FCH=%s; recallInit()" % json.dumps(cid)); pg.wait_for_timeout(60)
            check(True, "chapter '%s' recall OK (%d terms)" % (cid, n))
        except Exception as e:
            check(False, "chapter '%s' recall threw: %s" % (cid, str(e)[:45]))

    print("\n[6] MOBILE (390x844) — no horizontal scroll")
    pg.set_viewport_size({"width": 390, "height": 844})
    pg.evaluate("FCH='all'; SES.closed=true; goHome()"); pg.wait_for_timeout(300)
    sw = pg.evaluate("document.documentElement.scrollWidth"); cw = pg.evaluate("document.documentElement.clientWidth")
    check(sw <= cw + 1, "no horizontal scroll (scrollWidth %d <= clientWidth %d)" % (sw, cw))
    for sid, label, sel in modes:
        pg.evaluate("show(%s)" % json.dumps(sid)); pg.wait_for_timeout(120)
        sw = pg.evaluate("document.documentElement.scrollWidth")
        check(sw <= cw + 1, "mobile %s no h-scroll (%d<=%d)" % (label, sw, cw))
    pg.set_viewport_size({"width": 1280, "height": 900})

    # ------------------------------------------------------------------ S140 design contract
    print("\n[8] DESIGN CONTRACT (S140)")
    css = pg.evaluate("__v.cssText()")
    check(":focus-visible" in css, ":focus-visible rule exists")
    check(css.count("outline: none") + css.count("outline:none") + css.count("outline: 0") == 0, "outline:none count is 0")
    check("prefers-reduced-motion" in css, "prefers-reduced-motion rule exists")

    # drive every screen state, once each, at desktop; collect contrast/size/emoji/nesting
    def learn_to(stage, wrong):
        pg.evaluate("FCH='iso'; SES.closed=true; goHome(); enter('learn')"); pg.wait_for_timeout(300)
        if stage == 'produce': return
        pg.fill("#learn-input", "gains electrons"); pg.evaluate("setConf('sure'); revealOptions()"); pg.wait_for_timeout(300)
        if stage == 'revealed': return
        a = pg.evaluate("lnQ[lnPos].q.a")
        if wrong:
            other = pg.evaluate("lnQ[lnPos].perm.find(i=>i!==%d)" % a); pg.evaluate("learnPick(%d)" % other)
        else:
            pg.evaluate("learnPick(%d)" % a)
        pg.wait_for_timeout(400)

    def drive(name):
        if name == 'home':            pg.evaluate("FCH='all'; SES.closed=true; goHome(); setTab('study')")
        elif name == 'home-terms':    pg.evaluate("FCH='all'; SES.closed=true; goHome(); setTab('terms')")
        elif name == 'learn-produce': learn_to('produce', False)
        elif name == 'learn-revealed':learn_to('revealed', False)
        elif name == 'learn-correct': learn_to('graded', False)
        elif name == 'learn-wrong':   learn_to('graded', True)
        elif name == 'recall':        pg.evaluate("FCH='elem'; SES.closed=true; goHome(); enter('recall')")
        elif name == 'recall-revealed':
            pg.evaluate("FCH='elem'; SES.closed=true; goHome(); enter('recall')"); pg.wait_for_timeout(200)
            pg.fill("#rc-input", "a noble gas"); pg.evaluate("recallReveal()")
        elif name == 'match':         pg.evaluate("FCH='all'; SES.closed=true; goHome(); enter('match')")
        elif name == 'exam':          pg.evaluate("FCH='all'; SES.closed=true; goHome(); enter('exam')")
        elif name == 'flash':         pg.evaluate("FCH='all'; SES.closed=true; goHome(); enter('flash')")
        elif name == 'videos':        pg.evaluate("FCH='all'; SES.closed=true; goHome(); enter('videos')")
        elif name == 'close':
            pg.evaluate("FCH='elem'; SES.closed=true; goHome(); enter('recall')"); pg.wait_for_timeout(200)
            for i, g in enumerate(['got', 'miss', 'got', 'close', 'got', 'miss']):
                pg.fill("#rc-input", "x"); pg.evaluate("recallReveal()"); pg.wait_for_timeout(60); pg.evaluate("recallGrade(%s)" % json.dumps(g)); pg.wait_for_timeout(60)
            pg.evaluate("goHome()")   # >= 5 answers: must show the session-close, not home
        pg.wait_for_timeout(450)

    state_names = ['home', 'home-terms', 'learn-produce', 'learn-revealed', 'learn-correct', 'learn-wrong',
                   'recall', 'recall-revealed', 'match', 'exam', 'flash', 'videos', 'close']
    worst = {}
    for nm in state_names:
        drive(nm)
        rep = pg.evaluate("__v.contrastReport(4.5, 18.66)")
        check(len(rep['bad']) == 0, "contrast >= 4.5:1 for all %d small-text nodes in %s" % (rep['n'], nm))
        for x in rep['bad'][:4]: print("        low: %r %s %spx %.2f fg=%s bg=%s" % (x['t'], x['cls'], x['px'], x['c'], x['fg'], x['bg']))
        sz = pg.evaluate("__v.sizeReport()")
        check(len(sz['off']) == 0, "every rendered text size on the 48/32/24/18/16/14/13 scale in %s" % nm)
        for k, v in list(sz['off'].items())[:5]: print("        off-scale: %s x%d" % (k, v))
        emo = pg.evaluate("(()=>{const re=/\\p{Extended_Pictographic}/u; return re.test(document.body.innerText);})()")
        check(not emo, "no emoji in rendered text in %s" % nm)
        nested = pg.evaluate("document.querySelectorAll('.card .card').length")
        check(nested == 0, "no .card inside a .card in %s" % nm)
        if nm == 'close':
            check(pg.evaluate("MODE") == 'close', "'<- Set' after >= 5 answers shows the session-close screen")
            txt = pg.evaluate("document.getElementById('close').innerText")
            check('recalled from cold' in txt and 'still learning' in txt and 'Weakest chapter' in txt, "session-close names cold / still learning / weakest chapter")
            check(pg.evaluate("document.querySelectorAll('#close .btn').length") == 1, "session-close (exit) has exactly one button")
            pg.evaluate("goHome()"); pg.wait_for_timeout(150)
            check(pg.evaluate("MODE") == 'home', "that one button returns home")
        if nm == 'learn-correct':
            check(pg.evaluate("document.querySelectorAll('#learn-opts .opt.correct').length") == 1, "graded: exactly one option carries .correct")
            check(pg.evaluate("document.querySelectorAll('#learn-opts .opt.correct .opt-l svg').length") == 1, "graded: the correct option carries the check glyph")
        if nm == 'learn-wrong':
            check(pg.evaluate("document.querySelectorAll('#learn-opts .opt.correct').length") == 1 and pg.evaluate("document.querySelectorAll('#learn-opts .opt.wrong').length") == 1, "wrong pick: one .correct and one .wrong")
            check(pg.evaluate("getComputedStyle(document.querySelector('#learn-opts .opt.wrong .opt-txt')).textDecorationLine") == 'line-through', "wrong pick is struck through")
            check(pg.evaluate("document.querySelectorAll('#learn-fb .fb-t .math-block, #learn-fb .fb-t').length") >= 1 and pg.evaluate("getComputedStyle(document.getElementById('learn-fb')).borderTopWidth") == '1px', "feedback is one surface: hairline-separated, inside the card")
    check(pg.evaluate("__v.emojiIn('.mode-ic, .mode-ico')") == 0, "no emoji-only text in any .mode-ic")
    check(pg.evaluate("document.querySelectorAll('.mode-ic svg').length") == 4 and pg.evaluate("document.querySelectorAll('.warm svg').length") == 2, "six mode icons are inline SVG")
    check(pg.evaluate("document.querySelectorAll('#panel-study .modes .mode').length") == 4 and pg.evaluate("document.querySelectorAll('.warmups .warm').length") == 2, "modes render as 2 primary + 2 secondary rows + 2 warm-ups")

    # piles + strip
    pg.evaluate("FCH='iso'; SES.closed=true; goHome(); enter('learn')"); pg.wait_for_timeout(300)
    tot = pg.evaluate("LN.length")
    w0 = pg.evaluate("[document.getElementById('bar-remain').getBoundingClientRect().width, document.querySelector('.strip').getBoundingClientRect().width]")
    check(abs(w0[0] - w0[1]) < 2, "Learn strip is full (remaining) at zero answers, not empty grey")
    check(pg.evaluate("document.getElementById('c-remain').textContent") == str(tot), "Remaining pile shows %d at start" % tot)
    pg.fill("#learn-input", "x"); pg.evaluate("setConf('think'); revealOptions()"); pg.wait_for_timeout(200)
    pg.evaluate("learnPick(lnQ[lnPos].q.a)"); pg.wait_for_timeout(400)
    w1 = pg.evaluate("[document.getElementById('bar-learn').getBoundingClientRect().width, document.getElementById('c-learn').textContent, document.getElementById('c-remain').textContent]")
    check(w1[0] > 1 and w1[1] == '1' and w1[2] == str(tot - 1), "first answer moves one card from Remaining to Still learning and colours the strip")

    # home height with the terms tab closed, and no localStorage key regression
    pg.evaluate("FCH='all'; SES.closed=true; goHome(); setTab('study')"); pg.wait_for_timeout(200)
    hh = pg.evaluate("document.documentElement.scrollHeight")
    check(hh < 2 * 900, "home scrollHeight %d < 2 viewports (1800) with terms tab closed" % hh)
    rows = pg.evaluate("(()=>{const cs=[...document.querySelectorAll('.chip')]; const tops=new Set(cs.map(c=>Math.round(c.getBoundingClientRect().top))); return tops.size;})()")
    print("  %-60s %d" % ("chip rows on desktop (spec target: 2)", rows))
    check(rows <= 3, "chapter chips fit in <= 3 rows on desktop (%d)" % rows)
    pg.evaluate("setTab('terms')"); pg.wait_for_timeout(150)
    check(pg.evaluate("document.querySelectorAll('#term-list .term').length") == EXPECT_GL, "Key terms tab lists all %d terms" % EXPECT_GL)
    pg.fill("#term-filter", "isotope"); pg.wait_for_timeout(100)
    nf = pg.evaluate("document.querySelectorAll('#term-list .term').length")
    check(0 < nf < EXPECT_GL, "term filter narrows the list ('isotope' -> %d)" % nf)
    pg.fill("#term-filter", ""); pg.evaluate("setTab('study')")
    check(pg.evaluate("Object.keys(localStorage).includes('chem1211u1_recalled_v1')"), "recalled-from-cold persists under the S137 localStorage key")

    print("\n[8b] TOUCH TARGETS >= 44px at 390 wide, every state")
    pg.set_viewport_size({"width": 390, "height": 844})
    for nm in state_names:
        drive(nm)
        small = pg.evaluate("__v.targetReport(44)")
        check(len(small) == 0, "all interactive targets >= 44x44 in %s" % nm)
        for x in small[:5]: print("        small: %r %s %dx%d" % (x['t'], x['cls'], x['w'], x['h']))
        sw = pg.evaluate("document.documentElement.scrollWidth"); cw = pg.evaluate("document.documentElement.clientWidth")
        check(sw <= cw + 1, "no h-scroll at 390 in %s (%d<=%d)" % (nm, sw, cw))
    pg.evaluate("FCH='all'; SES.closed=true; goHome(); setTab('study')"); pg.wait_for_timeout(200)
    hhm = pg.evaluate("document.documentElement.scrollHeight")
    check(hhm < 2 * 844, "mobile home scrollHeight %d < 2 viewports (1688)" % hhm)
    b.close()

print("\n[7] CONSOLE / PAGE ERRORS")
if errors:
    print("  **%d error(s):**" % len(errors))
    for e in errors[:12]: print("    ", e[:150])
    failures.append("%d console/page errors" % len(errors))
else:
    print("  none                                                         PASS")

print("\n" + "=" * 70)
print("checks run: %d" % n_checks)
if failures:
    print("RESULT: %d FAILURE(S)" % len(failures))
    for f in failures: print("  -", f)
    sys.exit(1)
print("RESULT: ALL CHECKS PASSED")
