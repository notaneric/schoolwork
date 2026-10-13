# -*- coding: utf-8 -*-
"""Real click-through of chem1211-exam2-study.html (study-plan home) at 1280 and 390 px. Exits 1 on any failure.
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


EDGES = """sels => { const out = {}; for (const s of sels) { const e = document.querySelector(s);
  if (!e) { out[s] = null; continue; } const b = e.getBoundingClientRect(); out[s] = [Math.round(b.left), Math.round(b.right)]; } return out; }"""

PLAN = """() => ({rows:[...document.querySelectorAll('#plan > .step')].map(li => ({
    t:li.querySelector('.step-t').textContent, next:li.classList.contains('next'), done:li.classList.contains('done'), sum:li.classList.contains('done-sum'),
    tag:(li.querySelector('.step-tag')||{}).textContent||'', st:(li.querySelector('.step-st')||{}).textContent||'',
    btns:[...li.querySelectorAll('.step-act .btn')].map(b=>b.textContent)})),
  done:document.getElementById('plan-done').textContent, tools:document.querySelectorAll('#tools .tool').length,
  titles:CHAPTERS.map(c => GUIDE.find(g => g.ch === c.id).title).concat(['Mixed exam'])})"""

# where the highlighted step and its first button land, against the first screenful
FOLD = """() => { const li = document.querySelector('#plan .step.next'); if (!li) return null;
  const b = li.querySelector('.step-act .btn-primary').getBoundingClientRect();
  return {tag:Math.round(li.querySelector('.step-tag').getBoundingClientRect().top), btn:Math.round(b.bottom), vh:innerHeight}; }"""

BACK_X = "() => { const s = document.querySelector('.wrap.on .mode-bar > .icon-btn .ic'); return s ? Math.round(s.getBoundingClientRect().left) : null; }"


def seed(pg, js):
    """Write localStorage through the page's own qId(), then reload so the plan renders from storage."""
    pg.evaluate("() => localStorage.clear()")
    pg.evaluate(js)
    pg.reload(); pg.wait_for_timeout(250)


def run(browser, w, h, tag):
    print("\n[%s] %dx%d" % (tag, w, h))
    ctx = browser.new_context(viewport={"width": w, "height": h})
    pg = ctx.new_page()
    errs = []
    pg.on("pageerror", lambda e: errs.append(str(e)))
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto(URL); pg.wait_for_timeout(300)

    # ---- home: the plan, in study-guide order, with exactly one place to begin ----
    P = pg.evaluate(PLAN)
    ok("plan lists the 10 guide sections in chapter order, then the mixed exam", [r["t"] for r in P["rows"]] == P["titles"], [r["t"] for r in P["rows"]])
    nx = [i for i, r in enumerate(P["rows"]) if r["next"]]
    ok("fresh visitor: exactly one highlighted step, step 1, tagged Start here", nx == [0] and P["rows"][0]["tag"] == "Start here", P["rows"][0])
    ok("fresh visitor: Read the guide comes first, then Practice 17 questions", P["rows"][0]["btns"] == ["Read the guide", "Practice 17 questions"], P["rows"][0]["btns"])
    F = pg.evaluate(FOLD)
    ok("fresh visitor: the Start here step and its button are on the first screen", F["btn"] <= F["vh"], F)
    ok("fresh visitor: progress reads 0 of 10 done", P["done"] == "0 of 10 done", P["done"])
    ok("five More practice tools", P["tools"] == 5, P["tools"])
    E = pg.evaluate(EDGES, ["#home", ".ph", "#plan", "#tools"])
    vw = pg.evaluate("() => document.documentElement.clientWidth")
    ok("home column is centered (equal side gaps)", abs(E["#home"][0] - (vw - E["#home"][1])) <= 1, [E["#home"], vw])
    ok("header, plan and tools share the column's edges", all(E[s] == E["#home"] for s in (".ph", "#plan", "#tools")), E)
    ok("no horizontal overflow on home", overflow(pg) <= 0, overflow(pg))
    if SHOTS: pg.screenshot(path=os.path.join(SHOTS, "%s-home.png" % tag), full_page=False)

    # ---- read view: one section, same measure, then practice ----
    pg.click("#plan .step.next .btn-primary"); pg.wait_for_timeout(200)
    R = pg.evaluate("() => ({mode:MODE, fch:FCH, pos:document.getElementById('read-pos').textContent, h:document.querySelector('#read .read-h').textContent, t0:GUIDE.find(g=>g.ch===CHAPTERS[0].id).title})")
    ok("Read the guide opens step 1 on its own", R["mode"] == "read" and R["fch"] == "light" and R["pos"] == "Step 1 of 10" and R["h"] == R["t0"], R)
    E = pg.evaluate(EDGES, ["#read", "#read-body > p", "#read-body .math-block", "#read-body .g-memo", ".read-do", ".read-next"])
    ok("read view: prose, math, Memorize box and buttons share one measure", all(v == E["#read"] for v in E.values()), E)
    ok("no horizontal overflow in the read view", overflow(pg) <= 0, overflow(pg))
    bx = {"read": pg.evaluate(BACK_X)}
    if SHOTS: pg.screenshot(path=os.path.join(SHOTS, "%s-read.png" % tag), full_page=False)
    B = pg.evaluate("() => { let n=0; CHAPTERS.forEach((c,i)=>{ readStep(i); n+=document.querySelectorAll('#read-body .ob-box').length; }); readStep(0); return n; }")
    ok("the guide's oxygen orbital diagram renders (5 boxes across the steps)", B == 5, B)
    M = pg.evaluate("() => { readStep(4); const m=[...document.querySelectorAll('#read-body .g-memo-h')].map(e=>e.innerText).join(' | '); readStep(8); return m + ' | ' + [...document.querySelectorAll('#read-body .g-memo-h')].map(e=>e.innerText).join(' | '); }")
    ok("Memorize headings keep chemistry case (d4/d9, NClOF)", "the d4 and d9 exceptions" in M and "NClOF" in M, M)
    pg.evaluate("() => readStep(0)"); pg.wait_for_timeout(100)
    pg.click("#read .read-next"); pg.wait_for_timeout(150)
    ok("Next goes to step 2", pg.evaluate("() => document.getElementById('read-pos').textContent") == "Step 2 of 10")
    pg.evaluate("() => readStep(0)"); pg.wait_for_timeout(100)
    pg.click("#read .read-do .btn-primary"); pg.wait_for_timeout(200)
    L = pg.evaluate("() => ({mode:MODE, ch:[...new Set(LN.map(x=>x.q.chId))], n:LN.length, want:Q.filter(q=>q.chId==='light').length})")
    ok("Practice enters Learn on that step's questions only", L["mode"] == "learn" and L["ch"] == ["light"] and L["n"] == L["want"], L)
    bx["learn"] = pg.evaluate(BACK_X)
    ok("Learn card drops the narrating hint", pg.evaluate("() => !document.querySelector('#learn .produce-hint')"))
    pg.fill("#learn-input", "test answer"); pg.evaluate("() => revealOptions()"); pg.wait_for_timeout(150)
    pg.click("#learn-opts .opt[data-orig='0']"); pg.wait_for_timeout(200)
    fb = pg.evaluate("() => document.getElementById('learn-fb-t').textContent.length")
    ok("picking the stored correct option shows worked feedback", fb > 40, fb)
    ok("no horizontal overflow in Learn", overflow(pg) <= 0, overflow(pg))
    if SHOTS: pg.screenshot(path=os.path.join(SHOTS, "%s-learn.png" % tag), full_page=False)
    ok("every back button says Plan", pg.evaluate("() => [...document.querySelectorAll('.mode-bar .icon-btn')].filter(b=>b.textContent.trim()==='Set').length") == 0)
    pg.evaluate("() => goHome()"); pg.wait_for_timeout(150)
    ok("back on the plan, the step's chapter filter is cleared", pg.evaluate("() => MODE==='home' && FCH==='all'"))
    T = pg.evaluate("() => { readStep(9); recallCh('names'); return {mode:MODE, n:rc.length, want:GLOSSARY.filter(g=>g.ch==='names').length}; }")
    ok("Recall key terms from a step drills that step's terms only", T["mode"] == "recall" and T["n"] == T["want"], T)
    bx["recall"] = pg.evaluate(BACK_X)
    X = pg.evaluate("() => { goHome(); readStep(9); document.querySelector('#read .read-next').click(); return {mode:MODE, exam:examMode, n:lnQ.length, q:Q.length, title:document.getElementById('learn-title').textContent}; }")
    ok("Next after step 10 starts the mixed exam over every question", X["mode"] == "learn" and X["exam"] and X["n"] == X["q"] and X["title"] == "Mixed exam", X)

    # ---- progress drives the highlight ----
    seed(pg, """() => { const ids = ch => Q.filter(q=>q.chId===ch).map(qId); const b = ids('bohr');
        localStorage.setItem('chem1211e2_recalled_v1', JSON.stringify(ids('light').concat(b.slice(0, 5))));
        localStorage.setItem('chem1211e2_read_v1', JSON.stringify(['light', 'qm'])); }""")
    P = pg.evaluate(PLAN)
    nx = [i for i, r in enumerate(P["rows"]) if r["next"]]
    ok("after step 1 is done, step 2 becomes the one highlighted step", nx == [1] and P["rows"][1]["tag"] == "Continue here", [nx, P["rows"][1]])
    ok("step 1 is labeled Done, step 2 shows 5 of 16 recalled, step 3 shows Guide read",
       P["rows"][0]["done"] and P["rows"][0]["st"] == "Done" and P["rows"][1]["st"] == "5 of 16 recalled" and P["rows"][2]["st"] == "Guide read", P["rows"][:3])
    ok("a step in progress leads with Practice the last 11", P["rows"][1]["btns"] == ["Practice the last 11", "Reread the guide"], P["rows"][1]["btns"])
    ok("progress reads 1 of 10 done", P["done"] == "1 of 10 done", P["done"])
    if SHOTS: pg.screenshot(path=os.path.join(SHOTS, "%s-home-partial.png" % tag), full_page=False)
    pg.click("#plan .step.next .btn-primary"); pg.wait_for_timeout(200)
    C = pg.evaluate("() => ({mode:MODE, remain:+document.getElementById('c-remain').textContent, master:+document.getElementById('c-master').textContent})")
    ok("Practice from a partly done step resumes: 11 remaining, 5 mastered", C == {"mode": "learn", "remain": 11, "master": 5}, C)
    seed(pg, """() => { const ids = CHAPTERS.slice(0, 4).flatMap(c => Q.filter(q=>q.chId===c.id).map(qId));
        localStorage.setItem('chem1211e2_recalled_v1', JSON.stringify(ids)); }""")
    P = pg.evaluate(PLAN)
    ok("four steps done fold into one row, then step 5 is highlighted", P["rows"][0]["sum"] and P["rows"][0]["t"] == "Steps 1 to 4 done" and P["rows"][1]["next"]
       and P["rows"][1]["t"] == P["titles"][4] and len(P["rows"]) == 8, [r["t"] for r in P["rows"]])
    F = pg.evaluate(FOLD)
    ok("with four done, the highlighted step and its button are on the first screen", F["btn"] <= F["vh"], F)
    pg.focus("#plan .done-sum .step-row"); pg.keyboard.press("Enter"); pg.wait_for_timeout(100)
    ok("Show keeps keyboard focus on the folded row", pg.evaluate("() => document.activeElement === document.querySelector('#plan .done-sum .step-row')"))
    P = pg.evaluate(PLAN)
    ok("Show unfolds the four done steps in place", len(P["rows"]) == 12 and all(r["done"] for r in P["rows"][1:5]), [r["t"] for r in P["rows"]])
    seed(pg, "() => localStorage.setItem('chem1211e2_recalled_v1', JSON.stringify(Q.map(qId)))")
    P = pg.evaluate(PLAN)
    nx = [i for i, r in enumerate(P["rows"]) if r["next"]]
    ok("all ten done: one folded row, then the highlighted mixed exam", len(P["rows"]) == 2 and nx == [1] and P["done"] == "10 of 10 done"
       and P["rows"][1]["btns"] == ["Start the mixed exam"], [[r["t"], r["btns"]] for r in P["rows"]])
    F = pg.evaluate(FOLD)
    ok("all ten done: the mixed exam button is on the first screen", F["btn"] <= F["vh"], F)
    pg.click("#plan .step.next .btn-primary"); pg.wait_for_timeout(200)
    ok("Start the mixed exam runs every question", pg.evaluate("() => MODE==='learn' && examMode && lnQ.length===Q.length"))
    pg.evaluate("() => localStorage.clear()"); pg.reload(); pg.wait_for_timeout(250)

    # ---- More practice tools run over every chapter ----
    pg.evaluate("() => { FCH='econf'; enter('flash'); }"); pg.wait_for_timeout(150)
    D = pg.evaluate("""() => { for (let i=0;i<fc.length;i++){ if(fc[i].q.d){ fi=i; fcRender(); break; } }
        return {mode:MODE, ob:document.querySelectorAll('#flash .ob-box').length}; }""")
    ok("a diagram question renders its orbital boxes in Preview", D["mode"] == "flash" and D["ob"] >= 3, D)
    bx["flash"] = pg.evaluate(BACK_X)
    tools = pg.evaluate("() => [...document.querySelectorAll('#tools .tool')].map(b=>b.getAttribute('onclick'))")
    expect = [("openTool('recall')", "() => MODE==='recall' && rc.length===GLOSSARY.length"),
              ("openTerms()", "() => MODE==='terms' && document.querySelectorAll('#term-list .term').length===GLOSSARY.length"),
              ("openTool('flash')", "() => MODE==='flash' && fc.length===Q.length"),
              ("openTool('match')", "() => MODE==='match'"),
              ("openTool('videos')", "() => MODE==='videos' && document.querySelectorAll('#vid-list .vid-row').length===14")]
    ok("tools are Recall, Key terms, Preview, Match, Videos in that order", tools == [e[0] for e in expect], tools)
    for i, (fn, check) in enumerate(expect):
        pg.evaluate("() => { FCH='light'; goHome(); }"); pg.wait_for_timeout(100)
        pg.click("#tools .tool >> nth=%d" % i); pg.wait_for_timeout(250)
        ok("%s opens over all chapters" % fn, pg.evaluate(check))
        ok("no horizontal overflow in %s" % fn, overflow(pg) <= 0, overflow(pg))
        bx[fn] = pg.evaluate(BACK_X)
    ok("the Plan back arrow sits at the same x on every screen", len(set(bx.values())) == 1 and None not in bx.values(), bx)
    V = pg.evaluate("() => { goHome(); openTool('videos'); const c=document.getElementById('videos').getBoundingClientRect(); return [...document.querySelectorAll('#vid-list .vid-row')].filter(r=>{const b=r.getBoundingClientRect(); return b.left<c.left-0.5||b.right>c.right+0.5;}).length; }")
    ok("every video row stays inside the column", V == 0, V)
    W = pg.evaluate("() => { goHome(); openTool('match'); matchWin(); return [...document.querySelectorAll('#match-win .close-actions .btn')].map(b=>b.textContent.trim()); }")
    ok("the Match win card offers Back to plan", "Back to plan" in W, W)
    pg.click("#match-win .close-actions .btn >> text=Back to plan"); pg.wait_for_timeout(150)
    ok("Back to plan from the Match win card lands on the plan", pg.evaluate("() => MODE==='home'"))
    pg.evaluate("() => { goHome(); openTerms(); document.getElementById('term-filter').value='zzqx'; renderTerms(); }")
    ok("an empty term search does not mention a chapter", "chapter" not in pg.evaluate("() => document.getElementById('term-list').textContent"))
    pg.evaluate("() => goHome()"); pg.wait_for_timeout(100)
    pg.click("#plan .step.final .step-start"); pg.wait_for_timeout(200)
    ok("the Mixed exam row's Start button runs the exam over every question", pg.evaluate("() => MODE==='learn' && examMode && lnQ.length===Q.length"))
    pg.evaluate("() => goHome()")
    K = pg.evaluate("() => ({u1:Object.keys(localStorage).filter(k=>k.startsWith('chem1211u1_')).length})")
    ok("never writes the Exam 1 set's storage keys", K["u1"] == 0, K)
    ok("no JS errors", not errs, errs)
    ctx.close()


with sync_playwright() as pw:
    b = pw.chromium.launch()
    run(b, 1280, 900, "desktop")
    run(b, 390, 844, "mobile")
    run(b, 320, 700, "small")
    b.close()
print("\n%d passed, %d failed" % (_p, len(_f)))
sys.exit(1 if _f else 0)
