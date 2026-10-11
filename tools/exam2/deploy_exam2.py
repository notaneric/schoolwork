"""Copy the built Exam 2 study set to its three homes and prove they are byte-identical."""
import hashlib, pathlib, shutil, sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "out" / "chem1211-exam2-study.html"
NAME = SRC.name
DEST = [HERE.parents[1] / NAME,                                                   # repo root, served on GH Pages
        pathlib.Path("B:/School/CSU/Fall Semester 2026/CHEM 1211") / NAME,         # next to the course files
        HERE.parents[2] / "output" / NAME]                                         # Projects/Schoolwork/output
h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
want = h(SRC)
for d in DEST:
    assert d.parent.is_dir(), "missing folder: %s" % d.parent
    shutil.copyfile(SRC, d)
    got = h(d)
    print(("OK  " if got == want else "BAD ") + got[:16] + "  " + str(d))
    if got != want:
        sys.exit(1)
print("source " + want[:16])
