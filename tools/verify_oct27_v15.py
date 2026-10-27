"""v15 (D2L-only cards, In person badge) check. Old-page states come from git HEAD; one context per device.
Usage: python tools/verify_oct27_v15.py   (SCHOOLWORK_PAGE=<copy> to test a mutant)"""
import json, os, subprocess, sys, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify_oct21_v13 as base  # noqa: E402
from verify_oct21_v13 import Device, ok, serve  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

FLAG = "d2l_only_v15"
REMOVED = ['chem1211-knewton-access', 'chem1211-elements-1-36', 'chem1211-ch2-worksheet', 'chem1211-ch3-worksheet',
           'chem1211-ch4-worksheet', 'chem1211-exam1-review', 'chem1211-exam2-review', 'chem1211-ch3-video-assignment',
           'chem1211-practice-quiz', 'sci2900-syllabus-ask', 'sci2900-journal2', 'sci2900-journal3', 'sci2900-path-forward']
INPERSON = {'chem1211-exam1', 'chem1211-exam2', 'chem1211-exam3', 'chem1211-final', 'sci2900-final', 'sci2900-oral-presentation'}
TALK = 'sci2900-oral-presentation'
MINE = 'my-own-card'


def old_dir():
    blob = subprocess.run(["git", "-C", base.REPO, "show", "HEAD:index.html"], capture_output=True, check=True).stdout
    d = tempfile.mkdtemp(prefix="sw-v14-")
    open(os.path.join(d, "index.html"), "wb").write(blob)
    return d


def ids(s):
    return {a["id"]: a for a in s["assignments"]}


def rendered(d):
    """ids of list-view rows showing the In person badge, and the ids of all rows"""
    return d.page.evaluate("""() => { setView('assignments'); const out = {inp: [], all: []};
      document.querySelectorAll('.assignment-row').forEach(r => {
        const m = (r.getAttribute('onclick') || '').match(/'([^']+)'/);
        const id = m ? m[1] : null; out.all.push(id);
        if (r.querySelector('.type-badge.in-person')) out.inp.push(id); });
      return out; }""")


def main():
    old = serve(old_dir())
    new = serve(os.path.dirname(base.PAGE)) + os.path.basename(base.PAGE)
    with sync_playwright() as p:
        b = p.chromium.launch()
        d = Device(b, old)
        s14 = d.db()
        d.close()
        ok("[0] HEAD page state predates v15", FLAG not in s14["meta"] and all(i in ids(s14) for i in REMOVED))
        n_old = len(s14["assignments"])

        print("[1] fresh device")
        d = Device(b, new)
        s = d.db()
        fresh = set(ids(s))
        ok("[1] flag set", s["meta"].get(FLAG) is True)
        ok("[1] 13 ids absent", not any(i in fresh for i in REMOVED), [i for i in REMOVED if i in fresh])
        ok("[1] exactly 25 seeded cards remain", len(fresh) == 25, len(fresh))
        ok("[1] other seeded ids all present", set(ids(s14)) - set(REMOVED) == fresh)
        ok("[1] presentation type is 'presentation'", ids(s)[TALK]["type"] == "presentation", ids(s)[TALK]["type"])
        r = rendered(d)
        ok("[1] exactly the 6 in-person ids render the badge", set(r["inp"]) == INPERSON and len(r["inp"]) == 6, r["inp"])
        txt = d.page.text_content(".assignment-row .in-person")
        ok("[1] badge text reads 'In person'", txt == "In person", txt)
        d.page.evaluate("id => openEditModal(id)", TALK)
        ok("[1] modal shows presentation selected", d.page.eval_on_selector("#f-type", "e => e.value") == "presentation")
        d.page.evaluate("() => { document.getElementById('f-notes').value = 'edited'; saveAssignment(); }")
        a = ids(d.db())[TALK]
        ok("[1] modal round trip keeps type presentation", a["type"] == "presentation" and a["notes"] == "edited", a["type"])
        ok("[1] no console errors", not d.errs, d.errs)
        d.close()

        print("[2] existing device from HEAD page")
        d = Device(b, new, json.dumps(s14))
        s = d.db()
        e = ids(s)
        ok("[2] 13 ids absent", not any(i in e for i in REMOVED))
        ok("[2] 25 remain (38 - 13)", len(e) == 25 and n_old == 38, (len(e), n_old))
        ok("[2] same id set as fresh device", set(e) == fresh)
        ok("[2] presentation retyped", e[TALK]["type"] == "presentation")
        r = rendered(d)
        ok("[2] exactly the 6 render In person", set(r["inp"]) == INPERSON, r["inp"])
        ok("[2] no removed card in the list", not (set(r["all"]) & set(REMOVED)))
        ok("[2] no console errors", not d.errs, d.errs)
        s15 = s
        d.close()

        print("[3] Eric's edits: removed card status, own card, presentation notes")
        ed = json.loads(json.dumps(s14))
        for a in ed["assignments"]:
            if a["id"] == "chem1211-practice-quiz":
                a["status"] = "submitted"
            if a["id"] == TALK:
                a["notes"] = "MY TALK NOTES"
        ed["assignments"].append({"id": MINE, "title": "Mine", "courseId": "chem1211", "type": "exam", "dueDate": "2026-12-01T09:00:00-05:00",
                                  "priority": "low", "status": "todo", "weight": None, "notes": "x"})
        d = Device(b, new, json.dumps(ed))
        s = d.db()
        e = ids(s)
        ok("[3] edited removed card still removed", "chem1211-practice-quiz" not in e)
        ok("[3] own card survives untouched", e.get(MINE, {}).get("notes") == "x" and e[MINE]["title"] == "Mine")
        ok("[3] presentation notes kept, type retyped", e[TALK]["notes"] == "MY TALK NOTES" and e[TALK]["type"] == "presentation")
        ok("[3] own exam card renders In person", MINE in rendered(d)["inp"])
        ok("[3] 26 cards (25 + mine)", len(e) == 26, len(e))
        d.close()

        print("[3b] talk already set to another type by Eric")
        ed = json.loads(json.dumps(s14))
        for a in ed["assignments"]:
            if a["id"] == TALK:
                a["type"] = "project"
        d = Device(b, new, json.dumps(ed))
        ok("[3b] non-'assignment' type left alone", ids(d.db())[TALK]["type"] == "project")
        d.close()

        print("[4] idempotent double reload")
        d = Device(b, new, json.dumps(s15))
        d.page.reload(); d.settle(); d.page.reload(); d.settle()
        ok("[4] state unchanged", json.dumps(d.db(), sort_keys=True) == json.dumps(s15, sort_keys=True))
        d.close()

        print("[5] negative control: flag preset on old state")
        g = json.loads(json.dumps(s14))
        g["meta"][FLAG] = True
        d = Device(b, new, json.dumps(g))
        e = ids(d.db())
        ok("[5] all 13 cards still present", all(i in e for i in REMOVED) and len(e) == 38, len(e))
        ok("[5] presentation still 'assignment'", e[TALK]["type"] == "assignment")
        ok("[5] only 5 render In person (talk not retyped)", set(rendered(d)["inp"]) == INPERSON - {TALK}, rendered(d)["inp"])
        d.close()
        b.close()
    print("\n%d passed, %d failed" % (base._pass, len(base._fails)))
    for f in base._fails:
        print("  FAILED: " + f)
    sys.exit(1 if base._fails else 0)


if __name__ == "__main__":
    main()
