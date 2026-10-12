"""Assemble chem1211-exam2-study.html from the S140 v2 engine + CSS and the Exam 2 data.

The v2 engine is reused unchanged except for the asserted substitutions below (title, storage keys,
and a third home tab, the review guide). Every substitution must hit exactly once or the build fails.
Output goes to tools/exam2/out/ ; deploy_exam2.py copies it to the three live locations.
"""
import io, os, re, sys, json, pathlib, subprocess

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
V2 = HERE.parent / "v2"
OUT = HERE / "out" / "chem1211-exam2-study.html"

def rd(p): return io.open(p, encoding="utf-8").read()

def sub(text, old, new, label):
    n = text.count(old)
    assert n == 1, "%s: expected exactly 1 match, got %d" % (label, n)
    return text.replace(old, new)

css = rd(V2 / "style.css") + rd(HERE / "guide.css")
body = rd(V2 / "body.html")
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
    # Options are shuffled at runtime, so 'the last option' points at a random choice (S206 review).
    "posRef:Q.filter(q=>/\\b(first|second|third|fourth|fifth|last)\\s+option\\b|\\boption\\s+[1-5]\\b/i.test(q.e)).length}));\n")
r = subprocess.run(["node", str(tmp)], capture_output=True, text=True)
assert r.returncode == 0, "data does not evaluate:\n" + r.stderr
C = json.loads(r.stdout.strip().splitlines()[-1])
print("data:", C)
for k in ("noKhan", "badA", "badCh", "badG", "noGuide", "dupQ", "dupOpt", "posRef"):
    assert C[k] == 0, "data contract failed: %s = %d" % (k, C[k])
NQ, NG, NC = C["q"], C["g"], C["c"]

# ---- markup ----
head = ('<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<title>CHEM 1211 Exam 2 Study Set</title>\n<style>\n')
body = sub(body, '<div class="eyebrow">CHEM 1211</div>', '<div class="eyebrow">CHEM 1211 Exam 2, Wed Oct 14</div>', "eyebrow")
body = sub(body, '<h1 class="set-title">Exam 1 Prep</h1>', '<h1 class="set-title">Chapter 3 and Chapter 4.1 to 4.3</h1>', "title")
body = sub(body, '<b id="m-q">118</b> questions, <b id="m-t">94</b> key terms, <span id="m-ch">15 chapters</span>',
           '<b id="m-q">%d</b> questions, <b id="m-t">%d</b> key terms, <span id="m-ch">%d chapters</span>' % (NQ, NG, NC), "meta")
body = sub(body, '<span class="hero-of" id="rc-of">of 212</span>', '<span class="hero-of" id="rc-of">of %d</span>' % (NQ + NG), "hero")
body = sub(body, 'onclick="setTab(\'terms\')">Key terms (<span id="m-t2">94</span>)</button>',
           'onclick="setTab(\'terms\')">Key terms (<span id="m-t2">%d</span>)</button>' % NG, "terms tab")
body = sub(body, '<button class="tab" id="tab-terms"',
           '<button class="tab" id="tab-guide" role="tab" aria-selected="false" onclick="setTab(\'guide\')">Review guide</button>\n    <button class="tab" id="tab-terms"', "guide tab")
body = sub(body, '  <div id="panel-terms" hidden>',
           '  <div id="panel-guide" hidden>\n    <div class="guide" id="guide"></div>\n  </div>\n  <div id="panel-terms" hidden>', "guide panel")
body = sub(body, 'All <span id="m-q2">118</span> questions', 'All <span id="m-q2">%d</span> questions' % NQ, "exam count")
body = sub(body, '<div class="fc-count" id="fc-count">1 of 118</div>', '<div class="fc-count" id="fc-count">1 of %d</div>' % NQ, "fc count")

# ---- engine ----
eb = sub(eb, "const TOTAL_RECALLABLE = Q.length + GLOSSARY.length; // 118 + 94 = 212",
         "const TOTAL_RECALLABLE = Q.length + GLOSSARY.length;", "total")
for k in ("stars", "recalled_v1", "matchbest"):
    n = eb.count("chem1211u1_" + k)
    assert n == 2, "storage key %s: expected 2, got %d" % (k, n)
    eb = eb.replace("chem1211u1_" + k, "chem1211e2_" + k)
assert "chem1211u1_" not in eb, "an Exam 1 storage key survived"
eb = sub(eb, "  document.getElementById('panel-terms').hidden = t!=='terms';\n  ['study','terms'].forEach(",
         "  document.getElementById('panel-terms').hidden = t!=='terms';\n  document.getElementById('panel-guide').hidden = t!=='guide';\n  ['study','guide','terms'].forEach(", "setTab panels")
eb = sub(eb, "  if(t==='terms') renderTerms();\n}", "  if(t==='terms') renderTerms();\n  if(t==='guide') renderGuide();\n}", "setTab render")
eb = sub(eb, "  renderTerms();\n  renderProgress();\n}", "  renderTerms();\n  renderGuide();\n  renderProgress();\n}", "renderHome guide")
GUIDE_FN = r"""
function renderGuide(){
  if(document.getElementById('panel-guide').hidden) return;
  const secs=GUIDE.filter(g=>FCH==='all'||g.ch===FCH);
  const intro = FCH==='all' ? `<p class="g-intro">Read a section, then practice it. The formula sheet and periodic table are handed out with the exam; everything in a Memorize box is not.</p>` : '';
  document.getElementById('guide').innerHTML = intro + secs.map(g=>{
    const n=Q.filter(q=>q.chId===g.ch).length;
    return `<section class="g-sec" id="g-${g.ch}"><div class="g-topics">${g.topics}</div><h2 class="g-h">${g.title}</h2>${g.html}`+
      `<button class="btn btn-ghost g-go" onclick="practiceCh('${g.ch}')">Practice ${SHORT[g.ch]}, ${n} questions</button></section>`;
  }).join('');
}
function practiceCh(id){ FCH=id; enter('learn'); }
"""
eb = sub(eb, "function setFilter(id){", GUIDE_FN.strip("\n") + "\nfunction setFilter(id){", "guide fn")

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

OUT.parent.mkdir(exist_ok=True)
io.open(OUT, "w", encoding="utf-8", newline="\n").write(out)
js = re.search(r"<script>\n(.*)\n</script>", out, re.S).group(1)
jsf = HERE / "_script_check.js"
io.open(jsf, "w", encoding="utf-8", newline="\n").write(js)
r = subprocess.run(["node", "--check", str(jsf)], capture_output=True, text=True)
assert r.returncode == 0, "node --check failed:\n" + r.stderr
for f in (jsf, tmp): f.unlink()
print("wrote %s (%d chars), node --check OK" % (OUT, len(out)))
