# -*- coding: utf-8 -*-
"""Real click-through of chem1211-exam2-study.html at 1280 and 390 px. Exits 1 on any failure.
Usage: python interact_exam2.py [page.html] [shots_dir]"""
import json, os, sys
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
PAGE = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "out", "chem1211-exam2-study.html")
SHOTS = sys.argv[2] if len(sys.argv) > 2 else None
URL = "file:///" + os.path.abspath(PAGE).replace("\\", "/").replace(" ", "%20")
_p, _f = 0, []


def ok(name, cond, extra=None):
    global _p
    if cond:
        _p += 1; print("  PASS  " + name)
    else:
        _f.append(name); print("  FAIL  " + name + ("  -> " + json.dumps(extra)[:300] if extra is not None else ""))


def overflow(pg):
    return pg.evaluate("() => document.documentElement.scrollWidth - window.innerWidth")


def run(browser, w, h, tag):
    print("\n[%s] %dx%d" % (tag, w, h))
    ctx = browser.new_context(viewport={"width": w, "height": h})
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(URL); pg.wait_for_timeout(300)
    C = pg.evaluate("() => ({q:Q.length, g:GLOSSARY.length, mq:document.getElementById('m-q').textContent, mt:document.getElementById('m-t').textContent, of:document.getElementById('rc-of').textContent, chips:document.querySelectorAll('#chips .chip').length})")
    ok("home counts render from the data", C["mq"] == str(C["q"]) and C["mt"] == str(C["g"]) and C["of"] == "of %d" % (C["q"] + C["g"]), C)
    ok("11 chips (All + 10 chapters)", C["chips"] == 11, C)
    ok("no horizontal overflow on home", overflow(pg) <= 0, overflow(pg))
    if SHOTS: pg.screenshot(path=os.path.join(SHOTS, "%s-home.png" % tag), full_page=False)

    pg.click("#tab-guide"); pg.wait_for_timeout(150)
    G = pg.evaluate("() => ({secs:document.querySelectorAll('#guide .g-sec').length, vis:!document.getElementById('panel-guide').hidden, study:document.getElementById('panel-study').hidden, terms:document.getElementById('panel-terms').hidden, sel:document.getElementById('tab-guide').getAttribute('aria-selected'), ob:document.querySelectorAll('#guide .ob-box').length})")
    ok("guide tab shows 10 sections, hides the other panels", G["secs"] == 10 and G["vis"] and G["study"] and G["terms"] and G["sel"] == "true", G)
    ok("guide renders the oxygen orbital diagram (5 boxes)", G["ob"] == 5, G)
    ok("no horizontal overflow on the guide", overflow(pg) <= 0, overflow(pg))
    if SHOTS: pg.screenshot(path=os.path.join(SHOTS, "%s-guide.png" % tag), full_page=False)
    pg.evaluate("() => setFilter('trends')"); pg.wait_for_timeout(150)
    F = pg.evaluate("() => ({secs:document.querySelectorAll('#guide .g-sec').length, id:(document.querySelector('#guide .g-sec')||{}).id, mq:document.getElementById('m-q').textContent})")
    ok("chapter chip filters the guide to one section", F["secs"] == 1 and F["id"] == "g-trends", F)
    if SHOTS:
        pg.evaluate("() => { const t=document.querySelector('#guide .g-tbl'); if(t) t.scrollIntoView(); }")
        pg.screenshot(path=os.path.join(SHOTS, "%s-guide-trends.png" % tag), full_page=False)
    pg.click("#guide .g-go"); pg.wait_for_timeout(200)
    L = pg.evaluate("() => ({mode:MODE, ch:[...new Set(LN.map(x=>x.q.chId))]})")
    ok("Practice button enters Learn on that chapter only", L["mode"] == "learn" and L["ch"] == ["trends"], L)
    pg.fill("#learn-input", "test answer"); pg.evaluate("() => revealOptions()"); pg.wait_for_timeout(150)
    pg.click("#learn-opts .opt[data-orig='0']"); pg.wait_for_timeout(200)
    fb = pg.evaluate("() => document.getElementById('learn-fb-t').textContent.length")
    ok("picking the stored correct option shows worked feedback", fb > 40, fb)
    ok("no horizontal overflow in Learn", overflow(pg) <= 0, overflow(pg))
    if SHOTS: pg.screenshot(path=os.path.join(SHOTS, "%s-learn.png" % tag), full_page=False)

    pg.evaluate("() => { goHome(); setFilter('econf'); }"); pg.wait_for_timeout(150)
    pg.evaluate("() => enter('flash')"); pg.wait_for_timeout(150)
    D = pg.evaluate("""() => { for (let i=0;i<fc.length;i++){ if(fc[i].q.d){ fi=i; fcRender(); break; } }
        return {mode:MODE, ob:document.querySelectorAll('#flash .ob-box').length}; }""")
    ok("a diagram question renders its orbital boxes in Preview", D["mode"] == "flash" and D["ob"] >= 3, D)
    if SHOTS: pg.screenshot(path=os.path.join(SHOTS, "%s-flash-diagram.png" % tag), full_page=False)
    for mode, label in [("exam", "Mixed Exam"), ("recall", "Recall"), ("match", "Match"), ("videos", "Videos")]:
        pg.evaluate("() => { goHome(); setFilter('all'); }"); pg.wait_for_timeout(100)
        pg.evaluate("m => enter(m)", mode); pg.wait_for_timeout(250)
        ok("%s opens" % label, pg.evaluate("() => MODE") in (mode, "learn" if mode == "exam" else mode))
    V = pg.evaluate("() => document.querySelectorAll('#vid-list .vid-row').length")
    ok("Videos lists all 14 verified videos", V == 14, V)
    pg.evaluate("() => goHome()")
    T = pg.evaluate("() => { setTab('terms'); return document.querySelectorAll('#term-list .term').length; }")
    ok("Key terms lists every glossary entry", T == C["g"], T)
    K = pg.evaluate("() => Object.keys(localStorage).filter(k=>k.startsWith('chem1211u1_')).length")
    ok("never writes the Exam 1 set's storage keys", K == 0, K)
    ok("no JS errors", not errs, errs)
    ctx.close()


with sync_playwright() as pw:
    b = pw.chromium.launch()
    run(b, 1280, 900, "desktop")
    run(b, 390, 844, "mobile")
    b.close()
print("\n%d passed, %d failed" % (_p, len(_f)))
sys.exit(1 if _f else 0)
