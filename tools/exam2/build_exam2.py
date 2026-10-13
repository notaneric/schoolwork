"""Assemble chem1211-exam2-study.html from the S140 v2 engine + CSS and the Exam 2 data.

The v2 engine is reused unchanged except for the asserted substitutions below (storage keys, the
study-plan home from home.html + plan.js, and the Plan back labels). Every substitution must hit exactly once or the build fails.
Output goes to tools/exam2/out/ ; deploy_exam2.py copies it to the three live locations.
"""
import io, os, re, sys, json, pathlib, subprocess

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
V2 = HERE.parent / "v2"
# EXAM2_OUT keeps failing-control builds away from the real output file.
OUT = pathlib.Path(os.environ.get("EXAM2_OUT") or (HERE / "out" / "chem1211-exam2-study.html"))

def rd(p): return io.open(p, encoding="utf-8").read()

def sub(text, old, new, label):
    n = text.count(old)
    assert n == 1, "%s: expected exactly 1 match, got %d" % (label, n)
    return text.replace(old, new)

# The Notion-style page: cover, icon, properties, Plan/Board/Gallery views, page menu (S214). The plain
# study-plan look it replaced is in git history at 3222be5.
LOOK_CSS, LOOK_JS, LOOK_HOME = "notion.css", "notion.js", "notion-home.html"
css = rd(V2 / "style.css") + rd(HERE / "guide.css") + rd(HERE / LOOK_CSS)
body = rd(V2 / "body.html")
# EXAM2_PLAN_JS lets the failing-control test swap in a mutated plan; the live file is never edited.
plan_js = rd(os.environ.get("EXAM2_PLAN_JS") or (HERE / LOOK_JS))
ea, eb, ec = rd(V2 / "engine-a.js"), rd(V2 / "engine-b.js"), rd(V2 / "engine-c.js")
# EXAM2_DATA_Q lets the failing-control test point the build at a mutated copy; the live file is never edited.
data = rd(os.environ.get("EXAM2_DATA_Q") or (HERE / "data-q.js")) + "\n" + rd(HERE / "data-rest.js")

# ---- counts come from the data itself, never typed ----
tmp = HERE / "_data_eval.js"
io.open(tmp, "w", encoding="utf-8", newline="\n").write(ea + "\n" + data +
    "\nconsole.log(JSON.stringify({q:Q.length,g:GLOSSARY.length,c:CHAPTERS.length,s:GUIDE.length,"
    "v:VIDEOS.reduce((a,g)=>a+g.items.length,0),noKhan:Q.filter(q=>!(q.khan||KHAN[q.lec])).length,"
    "badA:Q.filter(q=>q.a!==0).length,badCh:Q.filter(q=>!CHAPTERS.some(c=>c.id===q.chId)).length,"
    "badG:GLOSSARY.filter(g=>!CHAPTERS.some(c=>c.id===g.ch)).length,"
    "noGuide:CHAPTERS.filter(c=>!GUIDE.some(g=>g.ch===c.id)).length,"
    "dupQ:Q.length-new Set(Q.map(q=>q.q+'|'+q.o.join('~'))).size,"
    "dupOpt:Q.filter(q=>new Set(q.o).size!==q.o.length).length,"
    # the plan takes one step per chapter and turns 'Study guide topics 1 to 3' into 'Topics 1 to 3'
    "guideN:CHAPTERS.filter(c=>GUIDE.filter(g=>g.ch===c.id).length!==1).length,"
    "badTopics:GUIDE.filter(g=>!/^Study guide topics? /.test(g.topics)).length,"
    # Options are shuffled at runtime, so 'the last option' points at a random choice (S206 review).
    "posRef:Q.filter(q=>/\\b(first|second|third|fourth|fifth|last)\\s+option\\b|\\boption\\s+[1-5]\\b/i.test(q.e)).length}));\n")
r = subprocess.run(["node", str(tmp)], capture_output=True, text=True)
assert r.returncode == 0, "data does not evaluate:\n" + r.stderr
C = json.loads(r.stdout.strip().splitlines()[-1])
print("data:", C)
for k in ("noKhan", "badA", "badCh", "badG", "noGuide", "dupQ", "dupOpt", "posRef", "guideN", "badTopics"):
    assert C[k] == 0, "data contract failed: %s = %d" % (k, C[k])
NQ, NG, NC = C["q"], C["g"], C["c"]

# ---- markup ----
head = ('<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<title>CHEM 1211 Exam 2 Study Set</title>\n<style>\n')
# The v2 home (hero count, chapter chips, Study/Guide/Terms tabs) is replaced whole by the study plan
# in home.html: a numbered step per chapter, a read view per step, and a key-terms screen.
H0, H1 = "<!-- ================= HOME ================= -->", "<!-- ================= FLASHCARDS ================= -->"
assert body.count(H0) == 1 and body.count(H1) == 1 and body.index(H0) < body.index(H1), "home block markers"
body = body[:body.index(H0)] + rd(HERE / LOOK_HOME) + "\n" + body[body.index(H1):]
# chemistry icons (one per step, plus page-menu glyphs) join the shared sprite
body = sub(body, "</defs></svg>", rd(HERE / "icons.html") + "</defs></svg>", "icon sprite")
body = sub(body, '<div class="fc-count" id="fc-count">1 of 118</div>', '<div class="fc-count" id="fc-count">1 of %d</div>' % NQ, "fc count")
n = body.count('</svg>Set</button>')
assert n == 5, "mode-bar back buttons: expected 5, got %d" % n
body = body.replace('</svg>Set</button>', '</svg>Plan</button>')
# the answer box, its placeholder and Show options already say what to do; the hint only narrated it
body = sub(body, '<p class="produce-hint">Answer from memory first, even a rough guess. Producing the answer is where the learning happens.</p>', '', "produce hint")

# ---- engine ----
eb = sub(eb, "const TOTAL_RECALLABLE = Q.length + GLOSSARY.length; // 118 + 94 = 212",
         "const TOTAL_RECALLABLE = Q.length + GLOSSARY.length;", "total")
for k in ("stars", "recalled_v1", "matchbest"):
    n = eb.count("chem1211u1_" + k)
    assert n == 2, "storage key %s: expected 2, got %d" % (k, n)
    eb = eb.replace("chem1211u1_" + k, "chem1211e2_" + k)
assert "chem1211u1_" not in eb, "an Exam 1 storage key survived"
eb = sub(eb, "const screens=['home','flash','learn','match','recall','videos','close'];",
         "const screens=['home','read','terms','flash','learn','match','recall','videos','close'];", "screens")
# home always shows the whole plan, so the chapter filter a step set is cleared on the way back
eb = sub(eb, "show('home'); renderHome();", "FCH='all'; show('home'); renderHome();", "goHome resets filter")
# the Notion top bar shows only on page screens; each screen change tags <body> so CSS can tell
eb = sub(eb, "MODE=id; }", "MODE=id; document.body.dataset.mode=id; }", "show tags body")
n = eb.count("label:'Back to set'")
assert n == 2, "close-card back labels: expected 2, got %d" % n
eb = eb.replace("label:'Back to set'", "label:'Back to plan'")
n = eb.count("Mixed Exam")
assert n == 3, "Mixed Exam labels: expected 3, got %d" % n
eb = eb.replace("Mixed Exam", "Mixed exam")  # the plan's step 11 is 'Mixed exam'; one name everywhere
# Practice from a plan step resumes: questions already recalled start mastered, so the Learn piles match the
# plan's "8 of 16 recalled". A step recalled in full is a full review instead (else Learn would end at once).
eb = sub(eb, "  LN = filtered().map(x=>({q:x.q, id:qId(x.q), status:'new', c:0, pc:0, cm:false}));",
         "  LN = filtered().map(x=>({q:x.q, id:qId(x.q), status:'new', c:0, pc:0, cm:false}));\n"
         "  if(!exam){ const had=LN.filter(x=>recalled.has(x.id)); if(had.length<LN.length) had.forEach(x=>x.status='master'); }",
         "learn resumes from recalled")
# the terms screen always lists every chapter now
eb = sub(eb, 'No terms match "${escapeHtml(f)}" in this chapter.', 'No terms match "${escapeHtml(f)}".', "terms empty state")
# the Match win card hides the mode bar, so it needs its own way back
eb = sub(eb, '<div class="close-actions"><button class="btn btn-ghost" onclick="matchStart()">Play again</button>',
         '<div class="close-actions"><button class="btn btn-ghost" onclick="goHome()">Back to plan</button><button class="btn btn-ghost" onclick="matchStart()">Play again</button>', "match win back")
body = sub(body, "<p class=\"vid-intro\">Every video I found and verified for this course, grouped by topic. Watch one to unblock a concept you're stuck on, then go <b>produce</b> it in Recall or Learn. Watching alone builds recognition, not recall.</p>",
           "<p class=\"vid-intro\">When a topic won't click, watch one, then go practice it. Watching alone builds recognition, not recall.</p>", "videos intro")
# renderProgress + renderHome (hero, chips, tab counts) give way to the plan; renderTerms and the rest stay
for f in ("function renderProgress(){", "function renderHome(){", "function renderTerms(){"):
    assert eb.count(f) == 1, "engine anchor %s" % f
a, z = eb.index("function renderProgress(){"), eb.index("function renderTerms(){")
assert a < eb.index("function renderHome(){") < z, "renderProgress/renderHome/renderTerms order"
eb = eb[:a] + plan_js.strip("\n") + "\n" + eb[z:]

out = (head + css + "</style>\n</head>\n" + body + "\n<script>\n" + ea + "\n" + data + "\n" + eb + "\n" + ec
       + "\n</script>\n</body>\n</html>\n")

# ---- static assertions on the assembled file ----
assert out.count("<script>") == 1 and out.count("</script>") == 1
chrome = out.replace(data, "")
assert "outline:none" not in chrome and ":focus-visible" in chrome and "prefers-reduced-motion" in chrome
emo = re.findall(r"[\U0001F000-\U0001FFFF☀-➿▶⭐↔-↙↩↪]", out)
assert not emo, "emoji/pictographs present: %r" % sorted(set(emo))
rendered = "\n".join(l for l in out.split("\n") if not l.lstrip().startswith(("//", "/*")))
assert "—" not in rendered and "·" not in rendered, "raw em dash or middot outside a code comment"
sizes = set(re.findall(r"font-size:\s*(\d+(?:\.\d+)?)px", css))
assert sizes <= {"48", "32", "24", "18", "16", "14", "13"}, "off-scale px sizes in CSS: %s" % sorted(sizes)
assert "Exam 1" not in chrome.replace("Exam 1 Study Set", ""), "stale 'Exam 1' copy in the chrome"
# one measure: the 640px plan column sets the line length, so no element caps itself in ch inside it
assert not re.search(r"max-width:\s*\d+ch", rd(HERE / "guide.css") + rd(HERE / LOOK_CSS)), "ch-capped measure inside the plan column"

OUT.parent.mkdir(exist_ok=True)
io.open(OUT, "w", encoding="utf-8", newline="\n").write(out)
js = re.search(r"<script>\n(.*)\n</script>", out, re.S).group(1)
jsf = HERE / "_script_check.js"
io.open(jsf, "w", encoding="utf-8", newline="\n").write(js)
r = subprocess.run(["node", "--check", str(jsf)], capture_output=True, text=True)
assert r.returncode == 0, "node --check failed:\n" + r.stderr
for f in (jsf, tmp): f.unlink()
print("wrote %s (%d chars), node --check OK" % (OUT, len(out)))
