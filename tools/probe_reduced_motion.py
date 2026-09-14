"""Prove the prefers-reduced-motion path: no draw animation, counts land immediately, card has no rise."""
import pathlib, sys
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
HTML = pathlib.Path(__file__).resolve().parent.parent / "chem1211-exam1-v2.html"
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 1280, "height": 900})
    pg.emulate_media(reduced_motion="reduce"); pg.goto(HTML.as_uri()); pg.wait_for_timeout(500)
    print("REDUCED() in page:", pg.evaluate("REDUCED()"))
    pg.evaluate("FCH='iso'; enter('learn')"); pg.wait_for_timeout(200)
    print("learn-input visible:", pg.is_visible("#learn-input"))
    pg.evaluate("document.getElementById('learn-input').value='x'; setConf('sure'); revealOptions()"); pg.wait_for_timeout(150)
    pg.evaluate("learnPick(lnQ[lnPos].q.a)"); pg.wait_for_timeout(50)
    print("check glyph dashoffset (0 = drawn, no animation):", pg.evaluate("getComputedStyle(document.querySelector('#learn-opts .opt.correct .opt-l .ic')).strokeDashoffset"))
    print("card animation-name:", pg.evaluate("getComputedStyle(document.getElementById('learn-card')).animationName"))
    print("fb animation-name:", pg.evaluate("getComputedStyle(document.getElementById('learn-fb')).animationName"))
    pg.evaluate("FCH='elem'; SES.closed=true; goHome(); enter('recall')"); pg.wait_for_timeout(150)
    print("rc-input visible:", pg.is_visible("#rc-input"))
    for g in ['got', 'miss', 'got', 'close', 'got', 'miss']:
        pg.evaluate("document.getElementById('rc-input').value='x'; recallReveal()"); pg.wait_for_timeout(30)
        pg.evaluate("recallGrade(%r)" % g); pg.wait_for_timeout(30)
    pg.evaluate("goHome()"); pg.wait_for_timeout(30)
    print("MODE:", pg.evaluate("MODE"), "| close counts immediately after render (no count-up):", pg.evaluate("[...document.querySelectorAll('#close .n')].map(e=>e.textContent)"))
    print("close check path dashoffset:", pg.evaluate("getComputedStyle(document.querySelector('#close .stat.g .draw path.chk')).strokeDashoffset"))
    b.close()
