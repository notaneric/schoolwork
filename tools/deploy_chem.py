import io, os, sys, shutil, hashlib

sys.stdout.reconfigure(encoding="utf-8")

SRC = (r"C:/Users/notan/AppData/Local/Temp/claude/c--Claude-Code-Boris/"
       r"8ba021ce-2805-4aac-bcc5-02200582055d/scratchpad/chem1211-exam1-spliced.html")

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
        print("  SKIP (no dir): %s" % t)
        continue
    # back up the pre-edit version once, next to the file
    if os.path.exists(t) and not os.path.exists(t + ".bak-S137"):
        shutil.copy2(t, t + ".bak-S137")
    io.open(t, "w", encoding="utf-8", newline="\n").write(data)

print("VERIFY — re-read each deployed file and hash it:")
allok = True
for t in TARGETS:
    if not os.path.exists(t):
        print("  MISSING  %s" % t)
        allok = False
        continue
    got = hashlib.sha256(io.open(t, encoding="utf-8").read().encode("utf-8")).hexdigest()
    ok = got == want
    allok &= ok
    print("  %-8s %s  %s" % ("MATCH" if ok else "**DIFF**", got[:16], t))

print("\n%s" % ("ALL 3 LOCATIONS SHA256-IDENTICAL" if allok else "**DEPLOY MISMATCH**"))
sys.exit(0 if allok else 1)
