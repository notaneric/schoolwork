# -*- coding: utf-8 -*-
"""Failing controls for the study-plan checks in interact_exam2.py. Each mutant reintroduces one defect;
the run passes only if interact_exam2.py (desktop width) fails on the check that names that defect.
Real output is never touched. Usage: python mutate_plan.py [label-substring]"""
import os, re, sys, subprocess, tempfile, pathlib
HERE = pathlib.Path(__file__).resolve().parent
TMP = pathlib.Path(tempfile.mkdtemp(prefix="exam2_mut_"))
REAL = (HERE / "out" / "chem1211-exam2-study.html").read_text(encoding="utf-8")
ONLY = sys.argv[1] if len(sys.argv) > 1 else ""

def build(plan_js):
    out = TMP / "built.html"; f = TMP / "plan_mut.js"; f.write_text(plan_js, encoding="utf-8")
    env = dict(os.environ, EXAM2_OUT=str(out), EXAM2_PLAN_JS=str(f))
    r = subprocess.run([sys.executable, "-I", str(HERE / "build_exam2.py")], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return out.read_text(encoding="utf-8")

def fails(html, name, width="desktop"):
    page = TMP / "mut.html"; page.write_text(html, encoding="utf-8")
    r = subprocess.run([sys.executable, "-I", str(HERE / "interact_exam2.py"), str(page)], capture_output=True, text=True,
                       encoding="utf-8", env=dict(os.environ, EXAM2_ONLY=width))
    failed = re.findall(r"^  FAIL  (.+?)(?:  -> .*)?$", r.stdout, re.M)
    return r.returncode != 0 and any(f.startswith(name) for f in failed), failed

def mut(s, a, b):
    assert s.count(a) == 1, "anchor not found once: " + a[:70]
    return s.replace(a, b)

js = (HERE / "notion.js").read_text(encoding="utf-8")
mutants = [
    ("highlight stuck on step 1", lambda: build(mut(js, "let next=st.findIndex(s=>!s.done);", "let next=0;")),
     "after step 1 is done, step 2 becomes the one highlighted step"),
    ("guide capped at 68ch", lambda: mut(REAL, ".guide{max-width:none}", ".guide{max-width:68ch}"),
     "step page: properties, prose, math, callouts and buttons share one measure"),
    ("column pushed left", lambda: mut(REAL, ".pg{margin:0 auto;", ".pg{margin:0 auto 0 0;"), "page column is centered (equal side gaps)"),
    ("Learn restarts from zero", lambda: mut(REAL, "  if(!exam){ const had=LN.filter(x=>recalled.has(x.id)); if(had.length<LN.length) had.forEach(x=>x.status='master'); }", ""),
     "Practice from a partly done step resumes: 11 remaining, 5 mastered"),
    ("Memorize headings uppercased", lambda: mut(REAL, ".g-memo-h,.g-ex-h{font-size:var(--t14);font-weight:700;margin:0 0 6px}",
     ".g-memo-h,.g-ex-h{font-size:var(--t14);font-weight:700;margin:0 0 6px;text-transform:uppercase}"), "Memorize headings keep chemistry case (d4/d9, NClOF)"),
    ("done steps never fold", lambda: build(mut(mut(js, "if(lead>=2) rows.push(", "if(lead>=99) rows.push("), "if(i>=lead || lead<2 || showDone)", "if(true)")),
     "four steps done fold into one row, then step 5 is highlighted"),
    ("Learn back at the old 720px width", lambda: mut(REAL, ".card{border:1px solid var(--line)}", ".card{border:1px solid var(--line)} #learn{max-width:720px}"),
     "the Plan back arrow sits at the same x on every practice screen"),
    ("back arrow shows on home", lambda: mut(REAL, ".tb-back[hidden]{display:none}", ""), "home: top bar shows, back arrow hidden"),
    ("choices never saved", lambda: build(mut(js, "function saveLook(){ lsSet('chem1211e2_look_v1',LOOK); }", "function saveLook(){}")),
     "the chosen view survives a reload"),
    ("muted text too light", lambda: mut(REAL, "--muted:#6B6A66", "--muted:#8F8D87"), "text contrast is at least 4.5:1"),
    ("top bar stays during practice", lambda: mut(REAL, "body[data-mode]:not([data-mode=home]):not([data-mode=read]):not([data-mode=terms]) #topbar{display:none}", ""),
     "the top bar hides during practice"),
    ("no Up next bar on Board", lambda: build(mut(js, "LOOK.view==='board' ? nextBar(p)+renderBoard(p)", "LOOK.view==='board' ? renderBoard(p)")),
     "Board: an Up next bar names step 1 and its button is on the first screen"),
    ("board never scrolls to the current card", lambda: build(mut(js, "if(bc && bd.scrollWidth>bd.clientWidth) bd.scrollLeft +=", "if(false) bd.scrollLeft +=")),
     "Board mid-plan: the current card is scrolled into view", "mobile"),
    ("top bar shrinks", lambda: mut(REAL, "align-self:stretch;flex-shrink:0;", "align-self:stretch;"), "the top bar keeps its 44px height on a long page"),
    ("phone gallery goes three-up in full width", lambda: mut(REAL, "  :root.full .gallery{grid-template-columns:1fr}", ""),
     "Full width on a phone keeps the gallery to one column", "mobile"),
    ("cover button too short on phones", lambda: mut(REAL, "  .cover-btn{min-height:44px}", ""), "phone tap targets", "mobile"),
    ("serif stops at the titles", lambda: mut(REAL, "[data-font=serif] .pg{font-family:var(--serif)}", "[data-font=serif] .pg-title{font-family:var(--serif)}"),
     "Serif reaches the step sublines too"),
]
bad = n = 0
for m in mutants:
    label, make, check = m[:3]; width = m[3] if len(m) > 3 else "desktop"
    if ONLY and ONLY not in label: continue
    html = make(); n += 1
    assert html != REAL, label + ": mutation did not apply"
    hit, failed = fails(html, check, width)
    print(("CAUGHT  " if hit else "MISSED  ") + label + "  ->  " + check + ("" if hit else "   (failed instead: %s)" % failed), flush=True)
    bad += not hit
print("%d of %d mutants caught by the named check" % (n - bad, n))
sys.exit(1 if bad else 0)
