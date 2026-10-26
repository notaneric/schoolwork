"""Each mutant reintroduces one v14 defect in a COPY of index.html and must fail its named check."""
import os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "index.html")
MUTANTS = [
    ("date never moves", "      if (hw.dueDate === null) hw.dueDate = hwf.dueDate;", "",
     "[2] placeholder dated, retitled, raised to high"),
    ("stamp not bumped", "const MIGRATION_STAMP = 14;", "const MIGRATION_STAMP = 13;",
     "[2] rewrites stamped at MIGRATION_STAMP 14"),
    ("seed misses the new items", "      ...CHEM1211_OCT26,", "",
     "[1] a fresh device stamps nothing"),  # migrate() backfills the items, so the defect shows as stamps
    ("title guard dropped", "      if (hw.title === CH4P2_HW_V14_OLD.title) hw.title = hwf.title;", "      hw.title = hwf.title;",
     "[3] edited title, date, notes and status kept"),
]

killed = 0
for name, old, new, must in MUTANTS:
    src = open(SRC, encoding="utf-8", newline="").read()
    assert src.count(old) == 1, name
    d = tempfile.mkdtemp(prefix="sw-mut-")
    page = os.path.join(d, "index.html")
    open(page, "w", encoding="utf-8", newline="").write(src.replace(old, new))
    r = subprocess.run([sys.executable, os.path.join(HERE, "verify_oct26_v14.py")], capture_output=True, text=True,
                       encoding="utf-8", env=dict(os.environ, SCHOOLWORK_PAGE=page, PYTHONIOENCODING="utf-8"))
    failed = [l.split("FAILED: ", 1)[1] for l in r.stdout.splitlines() if "FAILED: " in l]
    hit = r.returncode != 0 and must in failed
    killed += hit
    print(("KILLED  " if hit else "SURVIVED") + "  %-28s fails: %s" % (name, failed))
    shutil.rmtree(d, ignore_errors=True)
print("%d/4 mutants killed by their named check" % killed)
sys.exit(0 if killed == 4 else 1)
