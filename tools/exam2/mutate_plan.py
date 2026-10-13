# -*- coding: utf-8 -*-
"""Failing controls for the study-plan checks in interact_exam2.py. Each mutant reintroduces one defect;
the run passes only if interact_exam2.py fails on the check that names that defect. Real output is never touched."""
import os, re, sys, subprocess, tempfile, pathlib
HERE = pathlib.Path(__file__).resolve().parent
TMP = pathlib.Path(tempfile.mkdtemp(prefix="exam2_mut_"))
REAL = (HERE / "out" / "chem1211-exam2-study.html").read_text(encoding="utf-8")

def build(plan_js=None):
    out = TMP / "built.html"; env = dict(os.environ, EXAM2_OUT=str(out))
    if plan_js:
        f = TMP / "plan_mut.js"; f.write_text(plan_js, encoding="utf-8"); env["EXAM2_PLAN_JS"] = str(f)
    r = subprocess.run([sys.executable, "-I", str(HERE / "build_exam2.py")], env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    return out.read_text(encoding="utf-8")

def fails(html, name):
    page = TMP / "mut.html"; page.write_text(html, encoding="utf-8")
    r = subprocess.run([sys.executable, "-I", str(HERE / "interact_exam2.py"), str(page)], capture_output=True, text=True, encoding="utf-8")
    failed = re.findall(r"^  FAIL  (.+?)(?:  -> .*)?$", r.stdout, re.M)
    return r.returncode != 0 and any(f.startswith(name) for f in failed), failed

plan = (HERE / "plan.js").read_text(encoding="utf-8")
anchor = "let next=st.findIndex(s=>!s.done);"
assert plan.count(anchor) == 1
mutants = [
    ("highlight stuck on step 1", build(plan.replace(anchor, "let next=0;")), "after step 1 is done, step 2 becomes the one highlighted step"),
    ("guide capped at 68ch", REAL.replace(".guide{max-width:none}", ".guide{max-width:68ch}", 1), "read view: prose, math, Memorize box and buttons share one measure"),
    ("column pushed left", REAL.replace(".wrap{max-width:640px}", ".wrap{max-width:640px;margin-right:auto}", 1), "home column is centered (equal side gaps)"),
    ("Learn restarts from zero", REAL.replace("  if(!exam){ const had=LN.filter(x=>recalled.has(x.id)); if(had.length<LN.length) had.forEach(x=>x.status='master'); }", "", 1),
     "Practice from a partly done step resumes: 11 remaining, 5 mastered"),
    ("Memorize headings uppercased", REAL.replace(".g-memo-h,.g-ex-h{font-size:var(--t14);font-weight:700;margin:0 0 6px}",
     ".g-memo-h,.g-ex-h{font-size:var(--t14);font-weight:700;margin:0 0 6px;text-transform:uppercase}", 1), "Memorize headings keep chemistry case (d4/d9, NClOF)"),
    ("done steps never fold", build(plan.replace("if(lead>=2){", "if(lead>=99){").replace("if(i>=lead || lead<2 || showDone)", "if(true)")),
     "four steps done fold into one row, then step 5 is highlighted"),
    ("Learn back at the old 720px width", REAL.replace(".close-card{max-width:none}", ".close-card{max-width:none} #learn{max-width:720px}", 1),
     "the Plan back arrow sits at the same x on every screen"),
]
bad = 0
for label, html, check in mutants:
    assert html != REAL, label + ": mutation did not apply"
    hit, failed = fails(html, check)
    print(("CAUGHT  " if hit else "MISSED  ") + label + "  ->  " + check + ("" if hit else "   (failed instead: %s)" % failed))
    bad += not hit
print("%d of %d mutants caught by the named check" % (len(mutants) - bad, len(mutants)))
sys.exit(1 if bad else 0)
