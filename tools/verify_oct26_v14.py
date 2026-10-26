"""v14 (Oct 26 CHEM export) migration check, built on the v13 harness helpers.

Device states are produced by the real previous pages, never hand-built:
  v13 state = git HEAD page, v12 state = HEAD~1 page. One isolated browser context per device (S206).
Sync is untouched by v14 except the MIGRATION_STAMP bump, which [2] checks directly.

Usage:  python tools/verify_oct26_v14.py          (SCHOOLWORK_PAGE=<copy> to test a mutant)
"""
import json, os, subprocess, sys, tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify_oct21_v13 as base  # noqa: E402
from verify_oct21_v13 import Device, ok, serve  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

FLAG = "chem1211_oct26_v14"
HW = "chem1211-ch4-part2-hw"
HW_DUE = "2026-11-02T23:59:00-05:00"
ADDED = {"chem1211-practice-quiz": "2026-10-26T10:00:00-04:00",
         "chem1211-inclass-quizzes": "2026-11-30T10:00:00-05:00",
         "chem1211-ps-ch4-part2": HW_DUE}
OLD_HW_TITLE = "Chapter 4 Part 2 homework on Knewton (not announced yet)"
NEW_HW_TITLE = "Knewton 4.4 – 4.9: Chapter 4 Part 2"
NEW_CH42 = "Oct 23 (Handout 14"
NEW_CH7 = "This Oct 26 date is the syllabus's and it is wrong"
NEW_EX3 = "Through Fri Oct 23 the class was still in Chapter 4 Part 2"
OLD_EX3 = "The syllabus says Chapter 6"


def page_dir(rev):
    blob = subprocess.run(["git", "-C", base.REPO, "show", rev + ":index.html"], capture_output=True, check=True).stdout
    d = tempfile.mkdtemp(prefix="sw-" + rev.replace("~", "-") + "-")
    open(os.path.join(d, "index.html"), "wb").write(blob)
    return d


def by_id(s, coll="assignments"):
    return {a["id"]: a for a in s[coll]}


def main():
    v13_url = serve(page_dir("HEAD"))
    v12_url = serve(page_dir("HEAD~1"))
    new_url = serve(os.path.dirname(base.PAGE)) + os.path.basename(base.PAGE)
    with sync_playwright() as p:
        browser = p.chromium.launch()

        print("\n[0] real device states from the previous pages")
        d = Device(browser, v13_url); s13 = d.db(); d.close()
        d = Device(browser, v12_url); s12 = d.db(); d.close()
        ok("[0] HEAD page is v13, pre-v14", s13["meta"].get("chem1211_oct21_v13") is True and FLAG not in s13["meta"])
        ok("[0] v13 state has the undated placeholder", by_id(s13)[HW]["dueDate"] is None and by_id(s13)[HW]["title"] == OLD_HW_TITLE)
        ok("[0] HEAD~1 page is pre-v13", "chem1211_oct21_v13" not in s12["meta"] and HW not in by_id(s12))

        print("[1] fresh device")
        d = Device(browser, new_url); s = d.db(); ids = by_id(s); tp = by_id(s, "topics")
        ok("[1] flag set", s["meta"].get(FLAG) is True)
        ok("[1] three v14 items seeded with their dates", all(ids.get(i, {}).get("dueDate") == due for i, due in ADDED.items()), {i: ids.get(i, {}).get("dueDate") for i in ADDED})
        ok("[1] Ch 4 Part 2 homework dated Nov 2", ids[HW]["dueDate"] == HW_DUE and ids[HW]["title"].startswith(NEW_HW_TITLE))
        ok("[1] Quizzes marker on Oct 26", tp.get("chem1211-quizzes", {}).get("startsDate") == "2026-10-26")
        ok("[1] Ch 7 and Ch 4 pt 2 markers current", NEW_CH7 in tp["chem1211-ch7"]["title"] and NEW_CH42 in tp["chem1211-ch4-2"]["title"])
        ok("[1] Exam 3 note current", NEW_EX3 in ids["chem1211-exam3"]["notes"])
        ok("[1] a fresh device stamps nothing", not any("_ts" in a for a in s["assignments"]) and "_deleted" not in s)
        ok("[1] no console errors", not d.errs, d.errs)
        d.close()

        print("[2] existing v13 device")
        d = Device(browser, new_url, json.dumps(s13)); s = d.db(); ids = by_id(s); tp = by_id(s, "topics")
        ok("[2] v14 items added", all(i in ids for i in ADDED))
        ok("[2] item count grew by exactly 3", len(s["assignments"]) == len(s13["assignments"]) + 3)
        hw = ids[HW]
        ok("[2] placeholder dated, retitled, raised to high", hw["dueDate"] == HW_DUE and hw["title"].startswith(NEW_HW_TITLE) and hw["priority"] == "high", hw)
        ok("[2] placeholder notes rewritten", "due Mon Nov 2 at 11:59 PM" in hw["notes"])
        ok("[2] Ch 7, Ch 4 pt 2 and Quizzes markers", NEW_CH7 in tp["chem1211-ch7"]["title"] and NEW_CH42 in tp["chem1211-ch4-2"]["title"] and "chem1211-quizzes" in tp)
        ok("[2] Exam 3 note migrated", NEW_EX3 in ids["chem1211-exam3"]["notes"])
        ok("[2] rewrites stamped at MIGRATION_STAMP 14", hw.get("_ts", {}).get("dueDate") == 14 and ids["chem1211-exam3"].get("_ts", {}).get("notes") == 14, hw.get("_ts"))
        untouched = [i for i in by_id(s13) if i not in (HW, "chem1211-exam3")]
        ok("[2] untouched items carry no stamp", all("_ts" not in ids[i] for i in untouched))
        ok("[2] no console errors", not d.errs, d.errs)
        s14 = s
        d.close()

        print("[3] v13 device with Eric's own edits")
        ed = json.loads(json.dumps(s13))
        for a in ed["assignments"]:
            if a["id"] == HW:
                a.update(title="MY TITLE", dueDate="2026-10-30T23:59:00-04:00", notes="MY NOTE", status="in-progress")
            if a["id"] == "chem1211-exam3":
                a["notes"] = "MY EXAM NOTE"
        for t in ed["topics"]:
            if t["id"] == "chem1211-ch7":
                t["title"] = "MY CH7"
        d = Device(browser, new_url, json.dumps(ed)); s = d.db(); ids = by_id(s)
        hw = ids[HW]
        ok("[3] edited title, date, notes and status kept", (hw["title"], hw["dueDate"], hw["notes"], hw["status"]) == ("MY TITLE", "2026-10-30T23:59:00-04:00", "MY NOTE", "in-progress"), hw)
        ok("[3] edited Exam 3 note kept", ids["chem1211-exam3"]["notes"] == "MY EXAM NOTE")
        ok("[3] edited Ch 7 title kept", by_id(s, "topics")["chem1211-ch7"]["title"] == "MY CH7")
        ok("[3] v14 items still added", all(i in ids for i in ADDED))
        d.close()

        print("[4] idempotent reload")
        d = Device(browser, new_url, json.dumps(s14))
        d.page.reload(); d.settle(); d.page.reload(); d.settle()
        ok("[4] state unchanged across two reloads", json.dumps(d.db(), sort_keys=True) == json.dumps(s14, sort_keys=True))
        d.close()

        print("[5] negative control: v14 flag pre-set on a v13 device")
        g = json.loads(json.dumps(s13)); g["meta"][FLAG] = True
        d = Device(browser, new_url, json.dumps(g)); s = d.db(); ids = by_id(s)
        ok("[5] gated device gets no v14 items", not any(i in ids for i in ADDED))
        ok("[5] gated device keeps the undated placeholder and old Exam 3 note", ids[HW]["dueDate"] is None and ids["chem1211-exam3"]["notes"].startswith(OLD_EX3))
        d.close()

        print("[6] v12 device that skipped the Oct 21 build")
        d = Device(browser, new_url, json.dumps(s12)); s = d.db(); ids = by_id(s); tp = by_id(s, "topics")
        ok("[6] both flags set", s["meta"].get("chem1211_oct21_v13") is True and s["meta"].get(FLAG) is True)
        ok("[6] lands on the dated homework and all v14 items", ids.get(HW, {}).get("dueDate") == HW_DUE and all(i in ids for i in ADDED))
        ok("[6] Exam 3 note reaches v14 through v13", NEW_EX3 in ids["chem1211-exam3"]["notes"])
        ok("[6] Ch 4 pt 2 marker current", NEW_CH42 in tp["chem1211-ch4-2"]["title"])
        d.close()

        print("[7] what renders")
        d = Device(browser, new_url, json.dumps(s13))
        dash = d.view_text("dashboard")
        ok("[7] dashboard shows the Practice In-Class Quiz", "Practice In-Class Quiz in D2L" in dash)
        ok("[7] the undated placeholder is gone from the dashboard", OLD_HW_TITLE not in dash)
        cal = d.view_text("calendar")
        ok("[7] calendar shows the Quizzes marker", "Quizzes" in cal)
        res = d.view_text("resources")
        ok("[7] Resources: quiz sheet, Handout 14, Oct 21 and Oct 23 decks",
           all(x in res for x in ("In-Class Quiz Information", "14: Molecular geometry", "Oct 21: Homework dated Nov 2", "Oct 23: Quiz rules again")))
        intel = d.view_text("instructors")
        ok("[7] Intel: DAILY QUIZ, both Oct 26 statuses", all(x in intel for x in ("DAILY QUIZ", "Oct 26 D2L export (8:33 AM)", "Oct 26 D2L export (8:36 AM)")))
        ok("[7] no stale 'no homework date' line in Intel", "No homework date announced through the Oct 19 slides" not in intel)
        ok("[7] no console errors", not d.errs, d.errs)
        d.close()
        browser.close()
    print("\n%d passed, %d failed" % (base._pass, len(base._fails)))
    for f in base._fails:
        print("  FAILED: " + f)
    sys.exit(1 if base._fails else 0)


if __name__ == "__main__":
    main()
