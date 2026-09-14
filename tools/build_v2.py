"""Assemble chem1211-exam1-v2.html: new CSS + markup + engine around the UNTOUCHED data blocks.

The data (Q, KHAN, GLOSSARY, CHAPTERS, SHORT, VIDEOS) is sliced out of the deployed S137 file by
marker lines and spliced in byte-for-byte. Never retyped. Every slice boundary is asserted.
"""
import io, re, sys, pathlib, subprocess

sys.stdout.reconfigure(encoding="utf-8")
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "chem1211-unit1-study.html"          # deployed S137 build (data source)
OUT = ROOT / "chem1211-exam1-v2.html"              # working copy (never the deployed file)
V2 = HERE / "v2"

src = io.open(SRC, encoding="utf-8").read()
lines = src.split("\n")

def one(pattern):
    hits = [i for i, l in enumerate(lines) if re.match(pattern, l)]
    assert len(hits) == 1, "expected exactly one line matching %r, got %d" % (pattern, len(hits))
    return hits[0]

# ---- data slice A: Q .. SHORT (inclusive) ----
a0 = one(r"^const Q = \[")
a1 = one(r"^const SHORT = Object\.fromEntries")
assert a0 < a1, "slice A order"
data_a = "\n".join(lines[a0:a1 + 1])
assert data_a.count("const KHAN") == 1 and data_a.count("const GLOSSARY") == 1 and data_a.count("const CHAPTERS") == 1

# ---- data slice B: VIDEOS array (up to and including its closing `];`) ----
b0 = one(r"^const VIDEOS=\[")
b1 = one(r"^function videosInit\(")
assert b0 < b1, "slice B order"
tail = lines[b0:b1]
while tail and not tail[-1].strip():
    tail.pop()
assert tail[-1].strip() == "];", "VIDEOS must close with ]; got %r" % tail[-1]
data_b = "\n".join(tail)

# ---- head (doctype .. <style>) is rewritten: title kept ----
head = ('<!DOCTYPE html>\n<html lang="en">\n<head>\n<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        '<title>CHEM 1211 Exam 1 Study Set</title>\n<style>\n')

css = io.open(V2 / "style.css", encoding="utf-8").read()
body = io.open(V2 / "body.html", encoding="utf-8").read()
ea = io.open(V2 / "engine-a.js", encoding="utf-8").read()
eb = io.open(V2 / "engine-b.js", encoding="utf-8").read()
ec = io.open(V2 / "engine-c.js", encoding="utf-8").read()

out = (head + css + "</style>\n</head>\n" + body + "\n<script>\n" + ea + data_a + "\n" + eb + data_b + "\n" + ec
       + "\n</script>\n</body>\n</html>\n")

# ---- static assertions on the assembled file ----
assert out.count("<script>") == 1 and out.count("</script>") == 1
assert out.count("const Q = [") == 1 and out.count("const VIDEOS=[") == 1
assert "outline:none" not in out and "outline: none" not in out, "outline:none must be gone"
assert ":focus-visible" in out and "prefers-reduced-motion" in out
assert "const SHORT = Object.fromEntries(CHAPTERS.map(c=>[c.id,c.short]));" in out
# no emoji in the chrome. The data slices carry one U+2194 in a JS comment (never rendered);
# verify_v2.py checks the RENDERED text of every state with \p{Extended_Pictographic}.
chrome = out.replace(data_a, "").replace(data_b, "")
emo = re.findall(r"[\U0001F000-\U0001FFFF☀-➿▶⭐↔-↙↩↪]", chrome)
assert not emo, "emoji/pictographs present in chrome: %r" % sorted(set(emo))
# no em dashes in chrome (the data keeps its own copy; check only outside the data slices)
rendered = "\n".join(l for l in chrome.split("\n") if not l.lstrip().startswith("//") and not l.lstrip().startswith("/*"))
assert "—" not in rendered, "em dash in rendered chrome copy"
# every explicit px font-size in the CSS is on the scale
sizes = set(re.findall(r"font-size:\s*(\d+(?:\.\d+)?)px", css))
assert sizes <= {"48", "32", "24", "18", "16", "14", "13"}, "off-scale px sizes in CSS: %s" % sorted(sizes)

io.open(OUT, "w", encoding="utf-8", newline="\n").write(out)
print("wrote %s (%d chars)" % (OUT, len(out)))
print("data A: lines %d-%d (%d chars)   data B: lines %d-%d (%d chars)" % (a0 + 1, a1 + 1, len(data_a), b0 + 1, b0 + len(tail), len(data_b)))

# ---- node --check on the extracted script ----
js = re.search(r"<script>\n(.*)\n</script>", out, re.S).group(1)
jsf = HERE / "_v2_script_check.js"
io.open(jsf, "w", encoding="utf-8", newline="\n").write(js)
r = subprocess.run(["node", "--check", str(jsf)], capture_output=True, text=True)
print("node --check:", "OK" if r.returncode == 0 else "**FAIL**\n" + r.stderr[:2000])
jsf.unlink(missing_ok=True)
sys.exit(r.returncode)
