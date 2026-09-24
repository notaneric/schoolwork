# -*- coding: utf-8 -*-
"""Prove verify_v10_ch3part2.py can go red. A green suite is worth nothing until
each check has been shown to fail for its own reason.

Uses Boris's mutation harness, which reports CAUGHT only when the mutant compiles
AND the check named for it is the one that failed. Passing green because some
other assertion broke is reported WRONG-CHECK, not CAUGHT.

Usage:
  python tools/mutate_v10_ch3part2.py <old_index.html> [--harness <dir holding mutation_harness.py>]

<old_index.html> is the pre-v10 page, e.g.  git show HEAD~1:index.html > old.html
"""
import os
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8")

argv = sys.argv[1:]
if not argv:
    sys.exit(__doc__)
OLD = str(pathlib.Path(argv[0]).resolve())

harness_dir = os.environ.get("BORIS_SCRIPTS")
if "--harness" in argv:
    harness_dir = argv[argv.index("--harness") + 1]
if not harness_dir:
    # Default to the Boris repo sitting beside this one.
    harness_dir = str(pathlib.Path(__file__).resolve().parents[3] / "Boris" / ".boris" / "scripts")
if not pathlib.Path(harness_dir, "mutation_harness.py").is_file():
    sys.exit("mutation_harness.py not found in %s - pass --harness <dir> or set BORIS_SCRIPTS"
             % harness_dir)
sys.path.insert(0, harness_dir)
from mutation_harness import mutate  # noqa: E402

REPO = pathlib.Path(__file__).resolve().parents[1]
TARGET = REPO / "index.html"
src = TARGET.read_bytes()

# Build the date anchor from the real bytes rather than retyping it.
i = src.index(b'{"id":"chem1211-knewton-3-4-7"')
due_anchor = src[i:src.index(b'"dueDate":"2026-10-05', i) + len(b'"dueDate":"2026-10-05')]

MUTATIONS = [
    ("due date moved a month",
     due_anchor, due_anchor.replace(b"2026-10-05", b"2026-11-05"),
     "fresh: chem1211-knewton-3-4-7 due 2026-10-05T23:59:00-04:00"),

    ("migration adds nothing",
     b"    CHEM1211_CH3_PART2.forEach(item => {",
     b"    [].forEach(item => {",
     "v9: chem1211-knewton-3-4-7 added"),

    ("note guard dropped - clobbers Eric's own text",
     b"if (ps3a && ps3f && ps3a.notes === PS3_PART1_NOTES_V9_OLD) ps3a.notes = ps3f.notes;",
     b"if (ps3a && ps3f) ps3a.notes = ps3f.notes;",
     "edited: hand-written notes survive"),

    ("flag gate removed - migration re-runs on a done device",
     b"  if (!db.meta.chem1211_ch3_part2_v10) {",
     b"  if (true) {",
     "control: notes untouched"),

    ("exam 2 note guard dropped - clobbers Eric's own text",
     b"if (ex2 && ex2f && ex2.notes === EXAM2_NOTES_V9_OLD + EXAM_NOTE) ex2.notes = ex2f.notes;",
     b"if (ex2 && ex2f) ex2.notes = ex2f.notes;",
     "edited: Exam 2 notes survive"),

    ("exam 2 scope warning removed",
     b"expect Chapter 10 to be the part that goes",
     b"expect nothing in particular",
     "v9: Exam 2 card carries the Sep 23 scope warning"),

    ("DUE OCT 5 alert deleted",
     b"{ kw: 'DUE OCT 5'", b"{ kw: 'NO SUCH KW'",
     "instructors: the DUE OCT 5 alert renders"),

    ("Handout 10 dropped from the pinned Part 2 group",
     b"'10: Orbital diagrams and electron configurations",
     b"'10: ORBITAL DIAGRAMS GONE",
     "resources: Handout 10 is in the pinned Part 2 group"),

    ("pinned group loses its Oct 5 label",
     b"label: 'Chapter 3 Part 2: homework due Mon Oct 5'",
     b"label: 'Chapter 3 Part 2'",
     "resources: the pinned group is labelled with the Oct 5 deadline"),
]

report = mutate(
    target=str(TARGET),
    test_cmd=[sys.executable, str(REPO / "tools" / "verify_v10_ch3part2.py"), OLD, str(TARGET)],
    mutations=MUTATIONS,
    timeout=240,
)
for r in report.results:
    print("  %-12s %-52s %s" % (r.verdict, r.label, r.detail))
print("restored byte-exact:", report.restored_clean)
report.assert_all_caught()
print("ALL MUTANTS CAUGHT")
