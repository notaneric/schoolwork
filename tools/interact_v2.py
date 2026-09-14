"""Real click-through of chem1211-exam1-v2.html the way its UI actually works:
home rows clicked by their real buttons, Learn's produce -> reveal -> grade, Match via enter('match'),
Recall grading, the session-close on exit, and the round-done screen's Next round."""
import sys, pathlib
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
HTML = pathlib.Path(__file__).resolve().parent.parent / "chem1211-exam1-v2.html"
if len(sys.argv) > 1:
    HTML = pathlib.Path(sys.argv[1])
errors, fails = [], []


def check(c, label, extra=""):
    print("  %-56s %s%s" % (label, "PASS" if c else "**FAIL**", (" " + extra) if extra else ""))
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
        pg.evaluate("SES.closed=true; goHome()")
        pg.wait_for_timeout(200)

    print("\n[1] LEARN — real row click, produce, reveal, grade")
    pg.evaluate("FCH='mole'"); home()
    pg.click("button.mode:has-text('Learn')")
    pg.wait_for_timeout(500)
    q = pg.inner_text("#learn-q")
    check(len(q.strip()) > 10, "question shown", repr(q[:40]))
    kick = pg.inner_text("#learn-kick")
    check("undefined" not in kick.lower() and len(kick.strip()) > 0, "chapter label ok", repr(kick[:34]))
    prod_visible = pg.evaluate("getComputedStyle(document.getElementById('learn-produce')).display!=='none'")
    check(prod_visible, "produce step visible before options")
    opts_before = pg.evaluate("document.querySelectorAll('#learn-opts .opt').length")
    check(opts_before == 0, "no options rendered before reveal")
    pg.fill("#learn-input", "4.18 x 10^21")
    pg.click("#learn-produce .conf[data-c='think']")
    pg.click("#learn-produce .btn-primary")
    pg.wait_for_timeout(400)
    btns = [x for x in pg.query_selector_all("#learn-opts button") if x.is_visible()]
    check(len(btns) >= 2, "options revealed", "(%d)" % len(btns))
    btns[0].click(); pg.wait_for_timeout(500)
    fb = pg.evaluate("(()=>{const e=document.getElementById('learn-fb');return getComputedStyle(e).display!=='none' ? e.innerText : '';})()")
    check(len(fb.strip()) > 0, "grading feedback rendered", repr(fb[:52].replace("\n", " ")))
    check("undefined" not in fb.lower(), "feedback has no 'undefined'")
    check("You answered" in fb, "typed answer echoed in feedback")
    check(pg.evaluate("document.querySelectorAll('#learn-opts .opt.correct').length") == 1, "correct option marked")
    check(pg.is_visible("#learn-next"), "Continue button visible after grading")

    print("\n[2] LEARN — '<- Set' before 5 answers goes straight home; after 5 shows the close card")
    pg.click("#learn-play .icon-btn:has-text('Set')"); pg.wait_for_timeout(250)
    check(pg.evaluate("MODE") == "home", "1 answer: Set returns home directly")
    pg.evaluate("FCH='mole'"); home(); pg.evaluate("enter('learn')"); pg.wait_for_timeout(300)
    for i in range(5):
        pg.fill("#learn-input", "x"); pg.evaluate("setConf('guess'); revealOptions()"); pg.wait_for_timeout(120)
        pg.evaluate("learnPick(lnQ[lnPos].q.a)"); pg.wait_for_timeout(120)
        if i < 4:
            pg.evaluate("learnNext()"); pg.wait_for_timeout(120)
    pg.click("#learn-play .icon-btn:has-text('Set')"); pg.wait_for_timeout(400)
    check(pg.evaluate("MODE") == "close", "5 answers: Set shows the session-close card")
    txt = pg.inner_text("#close")
    check("recalled from cold" in txt and "still learning" in txt, "close card has the two counts", repr(txt[:60].replace("\n", " | ")))
    pg.click("#close .btn"); pg.wait_for_timeout(300)
    check(pg.evaluate("MODE") == "home", "Back to set returns home")

    print("\n[3] LEARN — finishing a round shows the summary with Next round")
    pg.evaluate("FCH='sf'"); home(); pg.evaluate("enter('learn')"); pg.wait_for_timeout(300)
    n = pg.evaluate("lnQ.length")
    for i in range(n):
        pg.fill("#learn-input", "x"); pg.evaluate("setConf('guess'); revealOptions()"); pg.wait_for_timeout(80)
        pg.evaluate("learnPick(lnQ[lnPos].q.a)"); pg.wait_for_timeout(80)
        pg.evaluate("learnNext()"); pg.wait_for_timeout(120)
    check(pg.evaluate("MODE") == "close", "round end shows the close screen")
    check(pg.is_visible("#close .btn-primary:has-text('Next round')"), "Next round available")
    pg.click("#close .btn-primary:has-text('Next round')"); pg.wait_for_timeout(400)
    check(pg.evaluate("MODE") == "learn" and pg.evaluate("lnRound") == 2, "Next round enters round 2")
    check(pg.inner_text("#learn-round").strip() == "Round 2", "round pill says Round 2")

    print("\n[4] MIXED EXAM — reachable from home, piles labelled for exam")
    home(); pg.click("button.mode:has-text('Mixed Exam')"); pg.wait_for_timeout(700)
    body = pg.inner_text("body")
    check(len(body.strip()) > 80 and "undefined" not in body.lower(), "exam screen content")
    check(pg.inner_text("#l-master").strip() == "Correct" and pg.inner_text("#l-learn").strip() == "Missed", "exam piles read Remaining / Missed / Correct")
    check(pg.inner_text("#learn-title").strip() == "Mixed Exam", "title reads Mixed Exam")

    print("\n[5] RECALL — the 36 elements, real grade clicks, persistence")
    pg.evaluate("localStorage.removeItem('chem1211u1_recalled_v1'); recalled=new Set()")
    pg.evaluate("FCH='elem'"); home(); pg.click("button.mode:has-text('Recall')"); pg.wait_for_timeout(500)
    body = pg.inner_text("body")
    check(len(body.strip()) > 60 and "undefined" not in body.lower(), "recall screen content")
    pg.fill("#rc-input", "a metal"); pg.click("#rc-reveal-btn"); pg.wait_for_timeout(300)
    check(pg.is_visible("#rc-reveal"), "reveal shows the model answer")
    pg.click(".grade.got"); pg.wait_for_timeout(300)
    stored = pg.evaluate("JSON.parse(localStorage.getItem('chem1211u1_recalled_v1')||'[]').length")
    check(stored == 1, "'Got it' persisted to localStorage", "(%d)" % stored)
    check(pg.inner_text("#rc-n").strip() == "1", "home hero number reflects it", pg.inner_text("#rc-n"))

    print("\n[6] MATCH — 12 tiles via enter('match'), a real pair resolves")
    home(); pg.evaluate("enter('match')"); pg.wait_for_timeout(500)
    tiles = pg.query_selector_all("#match-grid .tile")
    check(len(tiles) == 12, "12 tiles rendered", "(%d)" % len(tiles))
    pair = pg.evaluate("(()=>{const t=mTiles.findIndex(x=>x.pid===0&&x.type==='t'); const d=mTiles.findIndex(x=>x.pid===0&&x.type==='d'); return [t,d];})()")
    pg.click("#match-grid .tile[data-i='%d']" % pair[0]); pg.click("#match-grid .tile[data-i='%d']" % pair[1]); pg.wait_for_timeout(400)
    check(pg.evaluate("document.querySelectorAll('#match-grid .tile.gone').length") == 2, "matched pair leaves the grid")
    check(pg.evaluate("recalled.size") == 1, "Match did not touch recalled-from-cold")

    print("\n[7] PREVIEW + VIDEOS + KEY TERMS tab")
    pg.evaluate("FCH='all'"); home(); pg.click("button.warm:has-text('Preview')"); pg.wait_for_timeout(300)
    check(pg.evaluate("MODE") == "flash" and len(pg.inner_text("#fc-q").strip()) > 5, "preview shows a card")
    pg.click("#flashcard"); pg.wait_for_timeout(300)
    check(pg.evaluate("document.getElementById('flashcard').classList.contains('flipped')"), "card flips on click")
    home(); pg.click("button.mode:has-text('Videos')"); pg.wait_for_timeout(300)
    check(pg.evaluate("document.querySelectorAll('#vid-list .vid-row').length") == 8, "8 video rows")
    home(); pg.click("#tab-terms"); pg.wait_for_timeout(200)
    check(pg.evaluate("document.querySelectorAll('#term-list .term').length") == 94, "Key terms tab lists 94")
    check(pg.evaluate("document.getElementById('panel-study').hidden"), "study panel hidden while terms open")
    pg.click("#tab-study")
    check(not pg.evaluate("document.getElementById('panel-study').hidden"), "study panel back")
    b.close()

print("\n[8] RUNTIME ERRORS: %s" % (errors[:4] if errors else "none"))
if errors:
    fails.append("%d runtime errors" % len(errors))
print("\n" + "=" * 58)
print("STUDY-READY" if not fails else "ISSUES: %s" % fails)
sys.exit(1 if fails else 0)
