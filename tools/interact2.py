"""Correct interaction test — drives the app the way its UI actually works:
goHome() between modes, and Learn's produce-then-reveal flow
(learn-produce -> learn-opts -> learn-fb)."""
import sys, pathlib
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
HTML = pathlib.Path(r"B:/School/CSU/Fall Semester 2026/CHEM 1211/chem1211-unit1-study.html")
errors, fails = [], []


def check(c, label, extra=""):
    print("  %-52s %s%s" % (label, "PASS" if c else "**FAIL**", (" " + extra) if extra else ""))
    if not c:
        fails.append(label)


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    pg.goto(HTML.as_uri())
    pg.wait_for_timeout(600)

    def home():
        pg.evaluate("if(typeof goHome==='function') goHome(); else show('home')")
        pg.wait_for_timeout(200)

    print("\n[1] LEARN on NEW content — produce, reveal, grade")
    pg.evaluate("FCH='mole'")
    home()
    pg.click("text=Learn")
    pg.wait_for_timeout(500)

    q = pg.inner_text("#learn-q")
    check(len(q.strip()) > 10, "question shown", repr(q[:40]))
    kick = pg.inner_text("#learn-kick")
    check("undefined" not in kick.lower(), "chapter label ok", repr(kick[:34]))

    # produce-then-reveal: type an attempt, then reveal the options
    prod_visible = pg.evaluate("(()=>{const e=document.getElementById('learn-produce');"
                               "return !!e && getComputedStyle(e).display!=='none';})()")
    print("     produce step visible: %s" % prod_visible)
    inp = pg.query_selector("#learn-input")
    if inp and prod_visible:
        try:
            inp.fill("4.18 x 10^21")
        except Exception:
            pass
        # commit: Enter, or the visible button inside the produce block
        try:
            inp.press("Enter")
        except Exception:
            pass
        pg.wait_for_timeout(400)

    opts_html = pg.evaluate("(document.getElementById('learn-opts')||{}).innerHTML||''")
    if not opts_html.strip():
        for lbl in ["Show options", "Reveal", "See options", "Continue"]:
            e = pg.query_selector("#learn-play >> text=%s" % lbl)
            if e and e.is_visible():
                e.click(); pg.wait_for_timeout(350); break
    btns = [x for x in pg.query_selector_all("#learn-opts button") if x.is_visible()]
    check(len(btns) >= 2, "options revealed", "(%d)" % len(btns))

    if btns:
        btns[0].click()
        pg.wait_for_timeout(500)
        fb = pg.evaluate("(()=>{const e=document.getElementById('learn-fb');"
                         "return e? (getComputedStyle(e).display!=='none' ? e.innerText : '') : '';})()")
        check(len(fb.strip()) > 0, "grading feedback rendered", repr(fb[:52].replace("\n", " ")))
        check("undefined" not in fb.lower(), "feedback has no 'undefined'")

    print("\n[2] MIXED EXAM — reachable from home, renders")
    home()
    pg.click("text=Mixed Exam")
    pg.wait_for_timeout(700)
    body = pg.inner_text("body")
    check(len(body.strip()) > 80, "exam screen content")
    check("undefined" not in body.lower(), "no 'undefined' in exam")

    print("\n[3] RECALL — the 36 elements")
    pg.evaluate("FCH='elem'")
    home()
    pg.click("text=Recall")
    pg.wait_for_timeout(500)
    body = pg.inner_text("body")
    check(len(body.strip()) > 60, "recall screen content")
    check("undefined" not in body.lower(), "no 'undefined' in recall")

    print("\n[4] MATCH — glossary pairs")
    home()
    pg.click("text=Match")
    pg.wait_for_timeout(600)
    tiles = pg.query_selector_all("#match-play button, .tile, .match-tile")
    check(len(tiles) >= 4, "match tiles rendered", "(%d)" % len(tiles))

    home()
    pg.screenshot(path=str(HTML.parent / "study_ready.png"))
    b.close()

print("\n[5] RUNTIME ERRORS: %s" % (errors[:4] if errors else "none"))
if errors:
    fails.append("%d runtime errors" % len(errors))

print("\n" + "=" * 58)
print("STUDY-READY" if not fails else "ISSUES: %s" % fails)
sys.exit(1 if fails else 0)
