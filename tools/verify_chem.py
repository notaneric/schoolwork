"""Verify the spliced CHEM 1211 Exam-1 study set: every mode, every chapter, mobile.

Fails loudly. A pass here means: no console errors, all data present, every mode
renders content, and every chapter chip (including the new ones) can be selected
in the question-driven modes without throwing.
"""
import sys, pathlib, json
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

HTML = pathlib.Path(
    r"C:/Users/notan/AppData/Local/Temp/claude/c--Claude-Code-Boris/"
    r"8ba021ce-2805-4aac-bcc5-02200582055d/scratchpad/chem1211-exam1-spliced.html"
)
URL = HTML.as_uri()

# Measured in-browser, not grepped. Earlier text-based guesses were both wrong:
# the glossary "27 existing" came from a regex that also matched the 3 VIDEOS
# groups ({ch:'Lecture 1...'}), and a ",," splice bug briefly made Q.length 119
# while filter/map saw 118 (a sparse-array hole).
EXPECT_Q = 118      # 51 pre-existing + 67 new
EXPECT_GL = 94      # 24 pre-existing + 70 new
EXPECT_CH = 15      # 6 pre-existing + 9 new
NEW_CH = ["matter", "props", "atomic", "atom", "iso", "avgmass", "mole", "formula", "elem"]

failures = []
errors = []


def check(cond, label):
    print("  %-52s %s" % (label, "PASS" if cond else "**FAIL**"))
    if not cond:
        failures.append(label)


with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 900})
    pg.on("console", lambda m: errors.append("console.%s: %s" % (m.type, m.text)) if m.type == "error" else None)
    pg.on("pageerror", lambda e: errors.append("pageerror: %s" % e))
    pg.goto(URL)
    pg.wait_for_timeout(700)

    print("\n[1] DATA INTEGRITY")
    qn = pg.evaluate("Q.length")
    gn = pg.evaluate("GLOSSARY.length")
    cn = pg.evaluate("CHAPTERS.length")
    check(qn == EXPECT_Q, "Q.length == %d (got %d)" % (EXPECT_Q, qn))
    check(gn == EXPECT_GL, "GLOSSARY.length == %d (got %d)" % (EXPECT_GL, gn))
    check(cn == EXPECT_CH, "CHAPTERS.length == %d (got %d)" % (EXPECT_CH, cn))

    # No holes: a sparse array reports a length that filter/map never see.
    dense = pg.evaluate("Q.filter(()=>true).length")
    check(dense == qn, "Q has no sparse holes (filter sees %d of %d)" % (dense, qn))
    dense_g = pg.evaluate("GLOSSARY.filter(()=>true).length")
    check(dense_g == gn, "GLOSSARY has no sparse holes (%d of %d)" % (dense_g, gn))
    split = pg.evaluate("[Q.filter(q=>%s.includes(q.chId)).length,Q.filter(q=>!%s.includes(q.chId)).length]"
                        % (json.dumps(NEW_CH), json.dumps(NEW_CH)))
    check(split == [67, 51], "Q split new/pre-existing == 67/51 (got %s)" % split)

    # The real correctness check: `a` must index into `o`. Option COUNT may vary —
    # the pre-existing questions use 4 options, the new ones 5. That is not a defect.
    bad = pg.evaluate("Q.filter(q=>!(Number.isInteger(q.a)&&q.a>=0&&q.a<q.o.length)).length")
    check(bad == 0, "every answer index is a valid index into its options (bad=%d)" % bad)
    dupes = pg.evaluate("Q.filter(q=>new Set(q.o).size!==q.o.length).length")
    check(dupes == 0, "no duplicate options in any question (dupes=%d)" % dupes)
    orphan = pg.evaluate(
        "Q.filter(q=>!CHAPTERS.some(c=>c.id===q.chId)).length"
        "+GLOSSARY.filter(g=>!CHAPTERS.some(c=>c.id===g.ch)).length")
    check(orphan == 0, "no question/glossary orphaned from CHAPTERS (%d)" % orphan)
    empty = pg.evaluate("CHAPTERS.filter(c=>!Q.some(q=>q.chId===c.id)).map(c=>c.id)")
    check(len(empty) == 0, "no chapter has zero questions (%s)" % (empty or "none"))

    # SHORT[] labels the header in fcRender() and Learn. A missing id renders the
    # literal string "undefined" — which every "does it render content" check passes.
    missing = pg.evaluate("CHAPTERS.filter(c=>!SHORT[c.id]).map(c=>c.id)")
    check(len(missing) == 0, "every chapter has a SHORT label (missing: %s)" % (missing or "none"))
    check(pg.evaluate("Q.filter(q=>!SHORT[q.chId]).length") == 0,
          "every question's chapter resolves to a label")

    print("\n[2] EVERY MODE RENDERS")
    modes = [
        ("flash", "Preview", "#flash"),
        ("learn", "Learn", "#learn"),
        ("match", "Match", "#match"),
        ("recall", "Recall", "#recall"),
        ("videos", "Videos", "#videos"),
    ]
    for sid, label, sel in modes:
        try:
            pg.evaluate("show(%s)" % json.dumps(sid))
            pg.wait_for_timeout(120)
            vis = pg.evaluate(
                "(()=>{const e=document.querySelector(%s);"
                "return !!e && getComputedStyle(e).display!=='none' && e.innerText.trim().length>0;})()"
                % json.dumps(sel))
            check(bool(vis), "mode %s renders visible content" % label)
        except Exception as e:
            check(False, "mode %s threw: %s" % (label, str(e)[:60]))

    print("\n[3] MODE INITIALISERS RUN CLEAN")
    for fn in ["fcInit", "lnInit", "recallInit", "matchInit"]:
        exists = pg.evaluate("typeof %s === 'function'" % fn)
        if not exists:
            print("  %-52s (not present, skipped)" % fn)
            continue
        try:
            pg.evaluate("FCH='all'; %s()" % fn)
            pg.wait_for_timeout(100)
            check(True, "%s() ran with FCH=all" % fn)
        except Exception as e:
            check(False, "%s() threw: %s" % (fn, str(e)[:60]))

    print("\n[4] EVERY CHAPTER CHIP — question modes must not throw")
    chapters = pg.evaluate("CHAPTERS.map(c=>c.id)")
    for cid in chapters:
        ok = True
        detail = ""
        for fn in ["fcInit", "lnInit"]:
            if not pg.evaluate("typeof %s === 'function'" % fn):
                continue
            try:
                pg.evaluate("FCH=%s; %s()" % (json.dumps(cid), fn))
                pg.wait_for_timeout(60)
            except Exception as e:
                ok = False
                detail = "%s: %s" % (fn, str(e)[:45])
                break
        check(ok, "chapter '%s' selectable in question modes %s" % (cid, detail))

    print("\n[4b] RENDERED HEADER TEXT — no literal 'undefined' anywhere")
    for cid in [c for c in chapters]:
        pg.evaluate("FCH=%s; fcInit()" % json.dumps(cid))
        pg.wait_for_timeout(80)
        kick = pg.evaluate("(document.getElementById('fc-kick-f')||{}).textContent||''")
        check("undefined" not in kick.lower() and len(kick.strip()) > 0,
              "chapter '%s' preview header = %r" % (cid, kick[:26]))
    body = pg.evaluate("document.body.innerText")
    check("undefined" not in body.lower(), "no literal 'undefined' in rendered body")

    print("\n[5] GLOSSARY-DRIVEN MODES PER CHAPTER")
    for cid in chapters:
        n = pg.evaluate("GLOSSARY.filter(g=>g.ch===%s).length" % json.dumps(cid))
        if n == 0:
            print("  %-52s (no glossary, recall/match N/A)" % ("chapter '%s'" % cid))
            continue
        try:
            pg.evaluate("FCH=%s; recallInit()" % json.dumps(cid))
            pg.wait_for_timeout(60)
            check(True, "chapter '%s' recall OK (%d terms)" % (cid, n))
        except Exception as e:
            check(False, "chapter '%s' recall threw: %s" % (cid, str(e)[:45]))

    print("\n[6] MOBILE (390x844) — no horizontal scroll")
    pg.set_viewport_size({"width": 390, "height": 844})
    pg.evaluate("FCH='all'; show('home')")
    pg.wait_for_timeout(300)
    sw = pg.evaluate("document.documentElement.scrollWidth")
    cw = pg.evaluate("document.documentElement.clientWidth")
    check(sw <= cw + 1, "no horizontal scroll (scrollWidth %d <= clientWidth %d)" % (sw, cw))
    for sid, label, sel in modes:
        pg.evaluate("show(%s)" % json.dumps(sid))
        pg.wait_for_timeout(120)
        sw = pg.evaluate("document.documentElement.scrollWidth")
        check(sw <= cw + 1, "mobile %s no h-scroll (%d<=%d)" % (label, sw, cw))

    pg.screenshot(path=str(HTML.parent / "chem_mobile.png"), full_page=False)
    pg.set_viewport_size({"width": 1280, "height": 900})
    pg.evaluate("show('home')")
    pg.wait_for_timeout(200)
    pg.screenshot(path=str(HTML.parent / "chem_desktop.png"), full_page=False)
    b.close()

print("\n[7] CONSOLE / PAGE ERRORS")
if errors:
    print("  **%d error(s):**" % len(errors))
    for e in errors[:12]:
        print("    ", e[:150])
    failures.append("%d console/page errors" % len(errors))
else:
    print("  none                                                 PASS")

print("\n" + "=" * 62)
if failures:
    print("RESULT: %d FAILURE(S)" % len(failures))
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("RESULT: ALL CHECKS PASSED")
