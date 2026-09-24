# -*- coding: utf-8 -*-
"""Verify the v10 migration: CHEM 1211 Chapter 3 Part 2 homework (due Mon Oct 5).

State is produced by the OLD page (git show HEAD~1:index.html), never hand-built
JSON - a hand-built fixture proves the migration works on a shape that no device
has. Covers four device states plus a negative control:

  fresh      no localStorage at all -> seed() must carry the new items
  v9         state written by the pre-patch page -> migrate() must add them
  edited     v9 state with Eric's own edits on the exact fields v10 rewrites
  idempotent the v9 device reloaded twice -> nothing duplicates or drifts
  control    a v9 state with the v10 flag pre-set -> migration must NOT run

Usage:  python tools/verify_v10_ch3part2.py <old_index.html> [new_index.html]
"""
import json
import pathlib
import sys

from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")

KEY = "boris_school_fall2026"
FLAG = "chem1211_ch3_part2_v10"
NEW_IDS = ["chem1211-knewton-3-4-7", "chem1211-ps3-part2"]
DUE = "2026-10-05T23:59:00-04:00"

OLD = pathlib.Path(sys.argv[1]).resolve()
NEW = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "index.html").resolve()

failures = []
checks = 0


def ck(cond, label):
    global checks
    checks += 1
    if not cond:
        failures.append(label)
    print(("  ok   " if cond else "  FAIL ") + label)


def read_db(page):
    return json.loads(page.evaluate("localStorage.getItem('%s')" % KEY))


def load(page, url, state=None):
    """Seed localStorage on the right origin BEFORE the page's scripts run."""
    page.goto(url)
    if state is None:
        page.evaluate("localStorage.removeItem('%s')" % KEY)
    else:
        page.evaluate("s => localStorage.setItem('%s', s)" % KEY, json.dumps(state))
    page.reload()
    page.wait_for_timeout(250)
    return read_db(page)


def find(db, iid, coll="assignments"):
    return next((x for x in db[coll] if x["id"] == iid), None)


with sync_playwright() as p:
    browser = p.chromium.launch()
    errors = []
    page = browser.new_page()
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("pageerror", lambda e: errors.append(str(e)))

    # ---- capture real v9 state from the OLD page -----------------------------
    print("\n[v9 capture] state written by the pre-patch page")
    v9 = load(page, OLD.as_uri(), state=None)
    ck(find(v9, NEW_IDS[0]) is None, "old page does not already carry knewton-3-4-7")
    ck(v9["meta"].get(FLAG) is None, "old page does not set the v10 flag")
    v9_ps3_notes = find(v9, "chem1211-ps3-part1")["notes"]
    v9_ch4_title = find(v9, "chem1211-ch4", "topics")["title"]
    v9_exam2_notes = find(v9, "chem1211-exam2")["notes"]
    ck("expect Chapter 10" not in v9_exam2_notes, "old page's Exam 2 card lacks the scope warning")
    v9_counts = (len(v9["assignments"]), len(v9["topics"]))

    # ---- fresh device --------------------------------------------------------
    print("\n[fresh] no stored state")
    fresh = load(page, NEW.as_uri(), state=None)
    for iid in NEW_IDS:
        it = find(fresh, iid)
        ck(it is not None, "fresh: %s present" % iid)
        ck(it and it["dueDate"] == DUE, "fresh: %s due %s" % (iid, DUE))
        ck(it and it["status"] == "todo", "fresh: %s status todo" % iid)
    ck("Mon Oct 5" in find(fresh, "chem1211-ps3-part1")["notes"],
       "fresh: Part 1 problem set names the Oct 5 Part 2 date")
    ck("Oct 5" in find(fresh, "chem1211-ch3-2", "topics")["title"],
       "fresh: Ch 3 Part 2 marker names Oct 5")
    ck("no homework date" not in find(fresh, "chem1211-ch3-2", "topics")["title"].lower(),
       "fresh: the 'no homework date' sentence is gone")

    # ---- v9 device -----------------------------------------------------------
    print("\n[v9 -> v10] migration on real pre-patch state")
    mig = load(page, NEW.as_uri(), state=v9)
    ck(mig["meta"].get(FLAG) is True, "v9: flag set")
    for iid in NEW_IDS:
        it = find(mig, iid)
        ck(it is not None, "v9: %s added" % iid)
        ck(it and it["dueDate"] == DUE, "v9: %s due %s" % (iid, DUE))
    ck(len(mig["assignments"]) == v9_counts[0] + 2, "v9: exactly 2 assignments added")
    ck(len(mig["topics"]) == v9_counts[1], "v9: no topics added")
    ck("Mon Oct 5" in find(mig, "chem1211-ps3-part1")["notes"], "v9: Part 1 notes rewritten")
    ck("Oct 5" in find(mig, "chem1211-ch3-2", "topics")["title"], "v9: Ch 3 Part 2 title rewritten")
    ck("our placeholder rather than his date" in find(mig, "chem1211-ch4", "topics")["title"],
       "v9: Ch 4 title rewritten")
    ck(find(mig, "chem1211-ch4", "topics")["startsDate"] == "2026-10-02",
       "v9: Ch 4 date left where it was (no new guess)")
    ck("expect Chapter 10 to be the part that goes" in find(mig, "chem1211-exam2")["notes"],
       "v9: Exam 2 card carries the Sep 23 scope warning")
    ck(find(mig, "chem1211-exam2")["dueDate"] == "2026-10-14T10:00:00-04:00",
       "v9: Exam 2 date untouched")

    # ---- idempotency ---------------------------------------------------------
    print("\n[idempotent] two more reloads on the migrated device")
    page.reload(); page.wait_for_timeout(200)
    page.reload(); page.wait_for_timeout(200)
    again = read_db(page)
    ck(len(again["assignments"]) == len(mig["assignments"]), "idempotent: assignment count stable")
    ck(len([a for a in again["assignments"] if a["id"] == NEW_IDS[0]]) == 1,
       "idempotent: no duplicate knewton-3-4-7")

    # ---- user-edited device --------------------------------------------------
    print("\n[edited] Eric's own edits on the very fields v10 rewrites")
    edited = json.loads(json.dumps(v9))
    find(edited, "chem1211-ps3-part1")["notes"] = "MY OWN NOTE - do not touch"
    find(edited, "chem1211-ps3-part1")["status"] = "done"
    find(edited, "chem1211-exam2")["notes"] = "MY OWN EXAM 2 NOTE"
    find(edited, "chem1211-ch4", "topics")["title"] = "MY OWN TITLE"
    find(edited, "chem1211-ch4", "topics")["startsDate"] = "2026-09-30"
    ed = load(page, NEW.as_uri(), state=edited)
    ck(find(ed, "chem1211-ps3-part1")["notes"] == "MY OWN NOTE - do not touch",
       "edited: hand-written notes survive")
    ck(find(ed, "chem1211-ps3-part1")["status"] == "done", "edited: status survives")
    ck(find(ed, "chem1211-exam2")["notes"] == "MY OWN EXAM 2 NOTE", "edited: Exam 2 notes survive")
    ck(find(ed, "chem1211-ch4", "topics")["title"] == "MY OWN TITLE", "edited: topic title survives")
    ck(find(ed, "chem1211-ch4", "topics")["startsDate"] == "2026-09-30", "edited: topic date survives")
    for iid in NEW_IDS:
        ck(find(ed, iid) is not None, "edited: %s still added" % iid)

    # ---- negative control ----------------------------------------------------
    print("\n[control] flag already set -> migration must be a no-op")
    gated = json.loads(json.dumps(v9))
    gated["meta"][FLAG] = True
    g = load(page, NEW.as_uri(), state=gated)
    ck(find(g, NEW_IDS[0]) is None, "control: gated device gets no new item")
    ck(find(g, "chem1211-ps3-part1")["notes"] == v9_ps3_notes, "control: notes untouched")
    ck(find(g, "chem1211-ch4", "topics")["title"] == v9_ch4_title, "control: topic title untouched")
    ck(find(g, "chem1211-exam2")["notes"] == v9_exam2_notes, "control: Exam 2 notes untouched")

    # ---- every view renders --------------------------------------------------
    print("\n[views] each view opens, and the new work is actually rendered")
    load(page, NEW.as_uri(), state=v9)
    seen = {}
    for vid in ["dashboard", "list", "calendar", "courses", "instructors", "resources"]:
        btn = page.query_selector("#nav-" + vid)
        ck(btn is not None, "view %s: nav button exists" % vid)
        if not btn:
            continue
        btn.click()
        page.wait_for_timeout(200)
        ck(page.evaluate("currentView") == vid, "view %s: actually switched" % vid)
        seen[vid] = page.inner_text("body")

    # The point of a dated item is that it renders in the views that show time.
    ck("Knewton 3.4" in seen.get("list", ""), "list: the Part 2 section assignment is listed")
    ck("Problem Set (Chapter 3 Part 2)" in seen.get("list", ""), "list: the Part 2 problem set is listed")
    # The calendar opens on the current month, so step to October and look there.
    page.query_selector("#nav-calendar").click()
    page.wait_for_timeout(150)
    page.evaluate("calNav(1)")
    page.wait_for_timeout(200)
    oct_txt = page.inner_text("body")
    ck("October" in oct_txt, "calendar: steps forward to October")
    ck("Problem Set (Chapter 3 Part 2)" in oct_txt or "Knewton 3.4" in oct_txt,
       "calendar: the Oct 5 Part 2 work lands on the October grid")
    ck("DUE OCT 5" in seen.get("instructors", ""), "instructors: the DUE OCT 5 alert renders")
    ck("Handout 10" in seen.get("instructors", ""), "instructors: the handout-numbering warning renders")
    ck("Orbital diagrams and electron configurations" in seen.get("resources", ""),
       "resources: Handout 10 is in the pinned Part 2 group")
    ck("Orbital diagrams & electron configurations" in seen.get("resources", ""),
       "resources: Handout 10 is in the Handouts group")
    ck("at-home problems" in seen.get("resources", ""),
       "resources: Handout 9 is in the pinned Part 2 group")
    # The group label is CSS-uppercased in the rendered view, so compare case-insensitively.
    ck("chapter 3 part 2: homework due mon oct 5" in seen.get("resources", "").lower(),
       "resources: the pinned group is labelled with the Oct 5 deadline")
    ck("Sep 23" in seen.get("resources", ""), "resources: the Sep 23 deck is listed")

    ck(not errors, "no console or page errors (%d)" % len(errors))
    for e in errors[:5]:
        print("     ! " + e)
    browser.close()

print("\n%d checks, %d failed" % (checks, len(failures)))
for f in failures:
    print("  FAILED: " + f)
sys.exit(1 if failures else 0)
