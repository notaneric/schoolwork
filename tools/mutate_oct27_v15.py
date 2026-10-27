"""Each mutant reintroduces one v15 defect in a COPY of index.html and must fail its named check."""
import os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "index.html")
MUTANTS = [
    ("drop one id from list", "'chem1211-ch3-video-assignment', 'chem1211-practice-quiz',", "'chem1211-ch3-video-assignment',",
     "[1] 13 ids absent"),
    ("no presentation retype", "if (talk && talk.type === 'assignment') talk.type = 'presentation';", "",
     "[2] presentation retyped"),
    ("typeBadge ignores presentation", "new Set(['exam', 'presentation'])", "new Set(['exam'])",
     "[1] exactly the 6 in-person ids render the badge"),
    ("option deleted", '<option value="presentation">Presentation</option>', "",
     "[1] modal shows presentation selected"),
]
killed = 0
for name, old, new, must in MUTANTS:
    src = open(SRC, encoding="utf-8", newline="").read()
    assert src.count(old) == 1, (name, src.count(old))
    d = tempfile.mkdtemp(prefix="sw-mut-")
    page = os.path.join(d, "index.html")
    open(page, "w", encoding="utf-8", newline="").write(src.replace(old, new))
    r = subprocess.run([sys.executable, os.path.join(HERE, "verify_oct27_v15.py")], capture_output=True, text=True,
                       encoding="utf-8", env=dict(os.environ, SCHOOLWORK_PAGE=page, PYTHONIOENCODING="utf-8"))
    failed = [l.split("FAILED: ", 1)[1] for l in r.stdout.splitlines() if "FAILED: " in l]
    hit = r.returncode != 0 and must in failed
    killed += hit
    print(("KILLED  " if hit else "SURVIVED") + "  %-30s fails: %s" % (name, failed))
    shutil.rmtree(d, ignore_errors=True)
print("%d/4 mutants killed by their named check" % killed)
sys.exit(0 if killed == 4 else 1)
