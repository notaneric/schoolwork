# -*- coding: utf-8 -*-
"""Mutation harness for verify_oct2_v11.py.

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

def mutate_due(src):
    """M1: put the Chapter 3 Part 2 deadline back to Oct 5 in the data array only."""
    old = '"dueDate":"2026-10-07T23:59:00-04:00"'
    assert src.count(old) == 2, "expected 2 Oct 7 dueDates, found %d" % src.count(old)
    return src.replace(old, '"dueDate":"2026-10-05T23:59:00-04:00"')


def mutate_guard(src):
    """M2: drop the guard on the oral-presentation notes so the migration overwrites Eric's edit."""
    old = "if (op && opf && op.notes === ORAL_PRES_NOTES_V11_OLD) op.notes = opf.notes;"
    assert src.count(old) == 1
    return src.replace(old, "if (op && opf) op.notes = opf.notes;")


def mutate_stale_text(src):
    """M3: leak the stale Oct 5 sentence into a RENDERED label.
    This is the control for the one check that was rewritten after a false positive: the first
    version read <script> source and failed on the clean file."""
    old = "{ label: 'Chapter 3 Part 2: homework due Wed Oct 7 (moved off Oct 5)', open: true, files: ["
    assert src.count(old) == 1
    return src.replace(old, "{ label: 'Chapter 3 Part 2, all due Mon Oct 5', open: true, files: [")


def mutate_invented_date(src):
    """M4: invent a due date for the literature review, which the document does not give."""
    old = '{"id": "sci2900-lit-review", "title": "Primary Literature Review: the basis of your final presentation (25 pts)", "courseId": "sci2900", "type": "assignment", "dueDate": null'
    assert src.count(old) == 1
    return src.replace(old, old.replace('"dueDate": null', '"dueDate": "2026-11-02T09:00:00-05:00"'))


CASES = [
    # M1 legitimately breaks three checks: both MOVED items share the date, so the
    # user-edited state's "untouched sibling" assertion reads the same field.
    ("M1 deadline never moved", mutate_due,
     ["Oct 5 deadline corrected to Oct 7", "both moved items read Oct 7",
      "the untouched sibling still gets corrected"]),
    ("M2 guard removed, Eric's edit clobbered", mutate_guard,
     ["his rewritten notes survive"]),
    ("M3 stale Oct 5 text in a rendered label", mutate_stale_text,
     ["no view states the Chapter 3 Part 2 deadline as Oct 5"]),
    # M4 also empties the Deadline-unknown panel of that item, which is the point of the panel.
    ("M4 invented due date on the literature review", mutate_invented_date,
     ["both SCI items carry dueDate null (no invented date)",
      "both dateless SCI items render in the Deadline-unknown panel"]),
]


def run(page_path):
    env = dict(os.environ)
    env["SCHOOLWORK_PAGE"] = page_path
    env["PYTHONUTF8"] = "1"
    r = subprocess.run([sys.executable, "-X", "utf8", os.path.join(HERE, "verify_oct2_v11.py")],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       cwd=REPO, env=env)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def main():
    tmp = tempfile.mkdtemp(prefix="oct2v11-mut-")
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
