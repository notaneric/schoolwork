"""Deploy chem1211-exam1-v2.html to the 3 locations, backing up the S137 build once as .bak-S140,
then re-read every target and sha256-match it against the source."""
import io, os, sys, shutil, hashlib, pathlib

sys.stdout.reconfigure(encoding="utf-8")
SRC = pathlib.Path(__file__).resolve().parent.parent / "chem1211-exam1-v2.html"
TARGETS = [
    r"B:/School/CSU/Fall Semester 2026/CHEM 1211/chem1211-unit1-study.html",
    r"C:/Claude Code/Projects/Schoolwork/fall2026/chem1211-unit1-study.html",
    r"C:/Claude Code/Projects/Schoolwork/output/chem1211-unit1-study.html",
]

data = io.open(SRC, encoding="utf-8").read()
want = hashlib.sha256(data.encode("utf-8")).hexdigest()
print("source sha256: %s" % want)
print("size: %d chars\n" % len(data))

for t in TARGETS:
    if not os.path.exists(os.path.dirname(t)):
        print("  SKIP (no dir): %s" % t); continue
    if os.path.exists(t) and not os.path.exists(t + ".bak-S140"):
        shutil.copy2(t, t + ".bak-S140")
        print("  backed up S137 build -> %s" % (t + ".bak-S140"))
    io.open(t, "w", encoding="utf-8", newline="\n").write(data)

print("\nVERIFY: re-read each deployed file and hash it")
allok = True
for t in TARGETS:
    if not os.path.exists(t):
        print("  MISSING  %s" % t); allok = False; continue
    got = hashlib.sha256(io.open(t, encoding="utf-8").read().encode("utf-8")).hexdigest()
    ok = got == want; allok &= ok
    print("  %-8s %s  %s" % ("MATCH" if ok else "**DIFF**", got[:16], t))
print("\n%s" % ("ALL 3 LOCATIONS SHA256-IDENTICAL" if allok else "**DEPLOY MISMATCH**"))
sys.exit(0 if allok else 1)
