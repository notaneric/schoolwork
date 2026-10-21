# -*- coding: utf-8 -*-
"""Mutation harness for verify_oct21_v13.py (v13 migration + cross-device sync).

Each mutant reintroduces one specific defect into a COPY of index.html or of the sync Worker, and is
accepted only if the suite fails AND names exactly the predicted checks. A mutant that fails some
other check tests the parser, not the check. The live page and the Worker source are never written.

Usage: python tools/mutate_oct21_v13.py
"""
import io, os, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
SRC = io.open(os.path.join(REPO, "index.html"), encoding="utf-8", newline="").read()
sys.path.insert(0, HERE)
from verify_oct21_v13 import worker_dir  # noqa: E402

WORKER = worker_dir()


def sub(src, old, new):
    assert src.count(old) == 1, old[:60]
    return src.replace(old, new)


# Page mutants
def no_stamps(src):
    """P1: saves stop stamping changed fields, so an uncheck cannot outrank a legacy checkmark."""
    return sub(src, "if (prev[k] !== cur[k]) (it._ts = it._ts || {})[k] = now;", "if (false) (it._ts = it._ts || {})[k] = now;")


def migration_real_time(src):
    """P2: migrations stamp with the real time, so a device that migrated offline beats an earlier real edit."""
    return sub(src, "save(db, MIGRATION_STAMP); }", "save(db); }")


def modal_writes_all(src):
    """P3: the edit modal writes every form field, so a stale form erases a checkmark from the other PC."""
    return sub(src, "for (const k in data) if (!editBase || JSON.stringify(data[k]) !== JSON.stringify(editBase[k])) changed[k] = data[k];",
               "for (const k in data) changed[k] = data[k];")


def no_boot_stamp(src):
    """P4: boot no longer stamps what an older copy of the page changed."""
    return sub(src, "      lastSaved = fp;\r\n      stampChanges(db);", "      lastSaved = fp;")


# Worker mutants (applied to a copy of the Worker directory)
def legacy_incoming_wins(files):
    """W1: legacy status ties go to the incoming copy, so the desktop's To Do erases the laptop's checkmark."""
    files["merge.js"] = sub(files["merge.js"], "return rb > ra ? b : a;", "return b;")


def item_level(files):
    """W2: merge whole items by newest stamp instead of field by field."""
    files["merge.js"] = sub(files["merge.js"], "export function mergeItem(a, b) {",
                            "export function mergeItem(a, b) { return maxStamp(b) > maxStamp(a) ? b : a;")


def no_auth(files):
    """W3: the Worker stops checking the key."""
    files["worker.js"] = sub(files["worker.js"], "if (!(await keyMatches(auth.replace(/^Bearer /, ''), env.SYNC_KEY)))", "if (false)")


CASES = [
    # Unstamped on both sides, a non-status field keeps the Worker's stored value, so no edit can
    # travel at all: every note test fails, not just the uncheck in S3.
    ("P1 no change stamps", "page", no_stamps, ["[2] migration rewrites are stamped", "[S3] laptop now shows To Do",
                                                "[S4] laptop has both the note and the checkmark",
                                                "[S4] desktop has both the note and the checkmark",
                                                "[S8] stale device keeps the laptop's Exam 3 note",
                                                "[S8] and the laptop still has it after the stale device synced",
                                                "[S8b] its migration does not overwrite the laptop's earlier edit",
                                                "[S8b] the laptop keeps its edit too",
                                                "[S9] laptop keeps the laptop's checkmark and the desktop's note",
                                                "[S9] desktop keeps the laptop's checkmark and the desktop's note",
                                                "[S10] the laptop sees the older page's uncheck"]),
    ("P2 migration stamps real time", "page", migration_real_time, ["[S8b] its migration does not overwrite the laptop's earlier edit",
                                                                    "[S8b] the laptop keeps its edit too"]),
    ("P3 modal writes every field", "page", modal_writes_all, ["[S9] laptop keeps the laptop's checkmark and the desktop's note",
                                                               "[S9] desktop keeps the laptop's checkmark and the desktop's note",
                                                               "[S9] saving through the modal leaves the due date alone"]),
    ("P4 no stamping of older-page edits", "page", no_boot_stamp, ["[S10] the laptop sees the older page's uncheck"]),
    # Incoming-wins also never converges: each device's push flips the legacy status back to its own.
    ("W1 legacy tie to incoming", "worker", legacy_incoming_wins, ["[S2] desktop picks up the laptop's checkmark",
                                                                   "[S2] desktop UI shows it under Completed",
                                                                   "[S2] both copies identical after a round trip",
                                                                   "[S3] laptop now shows To Do"]),
    ("W2 item-level merge", "worker", item_level, ["[S4] laptop has both the note and the checkmark",
                                                    "[S4] desktop has both the note and the checkmark"]),
    ("W3 no auth", "worker", no_auth, ["[S6] rejected, and the page says so", "[S6] rejected device keeps its own state"]),
]


def run(env_extra):
    env = dict(os.environ, PYTHONIOENCODING="utf-8", **env_extra)
    p = subprocess.run([sys.executable, "-P", os.path.join(HERE, "verify_oct21_v13.py")], capture_output=True, env=env)
    return p.returncode, p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace")


def main():
    tmp = tempfile.mkdtemp(prefix="sw-mut13-")
    print("baseline (unmutated page and Worker)")
    rc, out = run({})
    print("  exit %d  |  %s" % (rc, out.strip().splitlines()[-1] if out.strip() else "no output"))
    if rc != 0:
        print("BASELINE FAILED - fix before mutation testing")
        print(out)
        sys.exit(1)

    bad = 0
    for name, kind, fn, expect in CASES:
        tag = name.split()[0]
        env = {}
        if kind == "page":
            d = os.path.join(tmp, tag)
            os.makedirs(d)
            path = os.path.join(d, "index.html")
            io.open(path, "w", encoding="utf-8", newline="").write(fn(SRC))
            env["SCHOOLWORK_PAGE"] = path
        else:
            d = os.path.join(tmp, tag + "-worker")
            shutil.copytree(WORKER, d, ignore=shutil.ignore_patterns(".wrangler", "node_modules", ".dev.vars", "*.py"))
            files = {n: io.open(os.path.join(d, n), encoding="utf-8", newline="").read() for n in ("merge.js", "worker.js")}
            fn(files)
            for n, s in files.items():
                io.open(os.path.join(d, n), "w", encoding="utf-8", newline="").write(s)
            env["SCHOOLWORK_SYNC_WORKER"] = d
        rc, out = run(env)
        failed = [l.strip()[6:].split("  ->")[0].strip() for l in out.splitlines() if l.strip().startswith("FAIL  ")]
        missing = [e for e in expect if e not in failed]
        extra = [f for f in failed if f not in expect]
        ok = rc != 0 and not missing and not extra
        bad += 0 if ok else 1
        print("\n%s  %s (exit %d)" % ("OK " if ok else "BAD", name, rc))
        print("   killed by: " + (", ".join(failed) if failed else "NOTHING"))
        if missing:
            print("   MISSING expected failure(s): " + ", ".join(missing))
        if extra:
            print("   UNEXPECTED failure(s): " + ", ".join(extra))
        if not failed and rc != 0:
            print(out[-1500:])

    print("\n%d/%d mutants killed by exactly the named check(s)" % (len(CASES) - bad, len(CASES)))
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
