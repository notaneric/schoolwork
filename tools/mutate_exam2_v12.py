# -*- coding: utf-8 -*-
"""Mutation harness for verify_exam2_v12.py.

A check that has only ever been observed passing is an untested branch, and on a verifier a green
that cannot go red is worse than no verifier. Each mutant below reintroduces one specific defect
into a COPY of index.html, and the run is only accepted if the suite fails AND names the expected
check. A mutant that fails some other check tests the parser, not the check.

The live index.html is never written to. Usage: python tools/mutate_oct2_v11.py
"""
import io, os, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SRC = io.open(os.path.join(REPO, "index.html"), encoding="utf-8", newline="").read()

def mutate_notes(src):
    """M1: drop the Exam 2 notes rewrite from the v12 migration."""
    old = "if (e2 && e2.notes === EXAM2_NOTES_V12_OLD + EXAM_NOTE) e2.notes = EXAM2_NOTES_V12 + EXAM_NOTE;"
    assert src.count(old) == 1
    return src.replace(old, "")
def mutate_guard(src):
    """M2: drop the guard so the migration overwrites an Exam 2 note Eric wrote himself."""
    old = "if (e2 && e2.notes === EXAM2_NOTES_V12_OLD + EXAM_NOTE) e2.notes"
    assert src.count(old) == 1
    return src.replace(old, "if (e2) e2.notes")
def mutate_ch4_old(src):
    """M3: the Chapter 4 guard constant no longer matches the stored v11 title (one character off)."""
    old = 'const CH4_TITLE_V12_OLD = "Chapter 4: Chemical Bonding and Molecular Geometry. He has still'
    assert src.count(old) == 1
    return src.replace(old, old.replace("He has still", "He has stil"))
def mutate_stale_count(src):
    """M4: leak the stale Unit 1 launcher count back into a rendered view."""
    old = "Chapters 1 and 2 plus 6.1, 118 questions and 94 terms. Final exam review"
    assert src.count(old) == 1
    return src.replace(old, "All of Chapter 1 in Knewton order, 94 questions and 54 terms")
CASES = [
    ("M1 Exam 2 notes never migrated", mutate_notes, ["Exam 2 notes migrated"]),
    ("M2 guard removed, Eric's note clobbered", mutate_guard, ["his Exam 2 note survives"]),
    # Only the HEAD-state device depends on this guard. A pre-v10 device is rewritten by the v10/v11
    # migrations straight to the CURRENT seed title, so the chain check correctly stays green here.
    ("M3 Chapter 4 guard off by one character", mutate_ch4_old, ["Chapter 4 title migrated"]),
    ("M4 stale launcher count rendered", mutate_stale_count,
     ["no view still states a superseded scope, deadline or count (6 views swept)"]),
]
def run(page_path):
    env = dict(os.environ)
    env["SCHOOLWORK_PAGE"] = page_path
    env["PYTHONUTF8"] = "1"
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "verify_exam2_v12.py")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       cwd=REPO, env=env)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    tmp = tempfile.mkdtemp(prefix="exam2v12-mut-")
    print("=== baseline: the clean page must PASS ===")
    rc, out = run(os.path.join(REPO, "index.html"))
    print("  exit %d  |  %s" % (rc, out.strip().splitlines()[-1] if out.strip() else "no output"))
    if rc != 0:
        print("BASELINE FAILED - fix the page before mutation testing")
        print(out)
        sys.exit(1)

    bad = 0
    for name, fn, expect in CASES:
        path = os.path.join(tmp, name.split()[0] + ".html")
        io.open(path, "w", encoding="utf-8", newline="").write(fn(SRC))
        rc, out = run(path)
        failed_lines = [l.strip()[6:].split("  ->")[0].strip()
                        for l in out.splitlines() if l.strip().startswith("FAIL  ")]
        missing = [e for e in expect if not any(e in f for f in failed_lines)]
        extra = [f for f in failed_lines if not any(e in f for e in expect)]
        status = "OK" if (rc != 0 and not missing and not extra) else "BAD"
        if status == "BAD":
            bad += 1
        print("\n%s  %s (exit %d)" % (status, name, rc))
        print("   killed by: " + (", ".join(failed_lines) if failed_lines else "NOTHING"))
        if missing:
            print("   MISSING expected failure(s): " + ", ".join(missing))
        if extra:
            print("   UNEXPECTED failure(s) - this mutant may be testing the parser: " + ", ".join(extra))

    print("\n%d/%d mutants killed by exactly the named check(s)" % (len(CASES) - bad, len(CASES)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
