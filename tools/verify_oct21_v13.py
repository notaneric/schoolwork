# -*- coding: utf-8 -*-
"""Verifies the 2026-10-21 update: the CHEM v13 migration (flag chem1211_oct21_v13) and cross-device sync.

Part A, migration, no sync link. Device states come from the PREVIOUS page (git HEAD):
  [1] fresh device      [2] existing v12 device      [3] v12 device Eric edited
  [4] idempotent reload [5] negative control: v13 flag pre-set, so nothing may be added
  [6] what renders: the Deadline-unknown panel, Resources, Intel

Part B, sync, against the real Worker code running under `wrangler dev` (SYNC_ENDPOINT):
  [S1] negative control: two UNLINKED devices do not share a checkmark (the bug Eric reported)
  [S2] linking: the laptop's legacy checkmark reaches a legacy desktop copy
  [S3] an uncheck made after linking propagates back (stamped beats legacy)
  [S4] two devices edit different fields of one item: both edits survive
  [S5] a delete propagates
  [S6] a wrong key is rejected and leaves both copies alone
  [S7] an unreachable endpoint: offline state, local saves still work
  [S8] a stale v12 device pulls BEFORE migrating, so v13 does not overwrite a note edited elsewhere

Usage:  python tools/verify_oct21_v13.py                      (needs wrangler dev on 127.0.0.1:8787)
        SCHOOLWORK_PAGE=<copy.html> SYNC_ENDPOINT=<url> python tools/verify_oct21_v13.py   (mutation runs)
"""
import functools, http.server, json, os, subprocess, sys, tempfile, threading, urllib.parse
from playwright.sync_api import sync_playwright

KEY = "boris_school_fall2026"
FLAG = "chem1211_oct21_v13"
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PAGE = os.path.abspath(os.environ.get("SCHOOLWORK_PAGE") or os.path.join(REPO, "index.html"))
ENDPOINT = os.environ.get("SYNC_ENDPOINT")       # unset: start a fresh local Worker (empty storage) per run
SYNC_KEY = os.environ.get("SYNC_TEST_KEY", "local-test-key-0123456789abcdef")
DEAD_ENDPOINT = "http://127.0.0.1:9/state"

ADDED = {"chem1211-exam2-review": "2026-10-23T10:00:00-04:00", "chem1211-ch4-part2-hw": None}
OLD_EX3 = "Covers Chapter 6 (composition of substances and solutions)"
NEW_EX3 = "The syllabus says Chapter 6"
OLD_CH6 = "Chapter 6: Composition of Substances and Solutions"
NEW_CH6 = "This Oct 16 date is the syllabus's and it is wrong"
X, Y, Z = "chem1211-knewton-4-1-3", "chem1211-ps5-ch4-part1", "chem1211-ch4-worksheet"

_pass, _fails = 0, []


def ok(name, cond, extra=None):
    global _pass
    if cond:
        _pass += 1
        print("  PASS  " + name)
    else:
        _fails.append(name)
        print("  FAIL  " + name + ("  -> " + json.dumps(extra, ensure_ascii=False)[:300] if extra is not None else ""))


def serve(directory):
    """Serve a directory on 127.0.0.1 so pages load over http (one origin per port, like a real host)."""
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    handler = functools.partial(Quiet, directory=directory)
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return "http://127.0.0.1:%d/" % srv.server_address[1]


def worker_dir():
    """The Worker source lives in the Boris repo, a sibling of Projects/ on both machines."""
    if os.environ.get("SCHOOLWORK_SYNC_WORKER"):
        return os.environ["SCHOOLWORK_SYNC_WORKER"]
    d = REPO
    for _ in range(5):
        d = os.path.dirname(d)
        cand = os.path.join(d, "Boris", "deliverables", "schoolwork-sync")
        if os.path.isfile(os.path.join(cand, "worker.js")):
            return cand
    sys.exit("cannot find deliverables/schoolwork-sync; set SCHOOLWORK_SYNC_WORKER or SYNC_ENDPOINT")


def start_worker():
    """wrangler dev on a free port with a brand-new persistence dir, so every run starts from an empty store."""
    import socket, time, urllib.request
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    state = tempfile.mkdtemp(prefix="sw-sync-")
    npx = "npx.cmd" if os.name == "nt" else "npx"
    proc = subprocess.Popen([npx, "--yes", "wrangler@4", "dev", "--ip", "127.0.0.1", "--port", str(port),
                             "--persist-to", state, "--var", "SYNC_KEY:" + SYNC_KEY],
                            cwd=worker_dir(), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    url = "http://127.0.0.1:%d/state" % port
    for _ in range(120):
        try:
            urllib.request.urlopen(urllib.request.Request(url, method="OPTIONS"), timeout=2)
            return proc, url
        except Exception:
            time.sleep(0.5)
    stop_worker(proc)
    sys.exit("local Worker did not start")


def stop_worker(proc):
    if os.name == "nt":
        subprocess.run(["taskkill", "/T", "/F", "/PID", str(proc.pid)], capture_output=True)
    else:
        proc.kill()


def old_page_dir():
    blob = subprocess.run(["git", "-C", REPO, "show", "HEAD:index.html"], capture_output=True, check=True).stdout
    d = tempfile.mkdtemp(prefix="sw-head-")
    open(os.path.join(d, "index.html"), "wb").write(blob)
    return d


class Device(object):
    def __init__(self, browser, url, state=None, link=None):
        # One isolated context per device: a shared context shares localStorage (S206).
        self.errs = []
        self.ctx = browser.new_context()
        self.page = self.ctx.new_page()
        self.page.on("pageerror", lambda e: self.errs.append(str(e)))
        self.page.on("console", lambda m: self.errs.append(m.text) if m.type == "error" and "Failed to load resource" not in m.text else None)
        self.page.on("dialog", lambda d: d.accept())
        if state is not None:
            self.page.add_init_script("(() => { if (!sessionStorage.getItem('seeded')) { localStorage.setItem(%s, %s); sessionStorage.setItem('seeded','1'); } })()"
                                      % (json.dumps(KEY), json.dumps(state)))
        if link:
            key, endpoint = link
            url = url + "#sync=" + key + "@" + urllib.parse.quote(endpoint, safe="")
        self.page.goto(url)
        self.settle()

    def settle(self):
        # The v12 page has no boot()/Sync; it is settled once loaded.
        self.page.wait_for_function("""() => { try { return document.readyState === 'complete' &&
            (typeof Sync === 'undefined' || (booted && !Sync.inflight)); } catch (e) { return false; } }""", timeout=15000)
        self.page.wait_for_timeout(150)

    def sync(self):
        self.page.evaluate("async () => { clearTimeout(Sync.timer); await Sync.run(); }")
        self.settle()

    def db(self):
        return json.loads(self.page.evaluate("k => localStorage.getItem(k)", KEY))

    def item(self, iid):
        return next((a for a in self.db()["assignments"] if a["id"] == iid), None)

    def view_text(self, view):
        return self.page.evaluate("""v => { setView(v); const t = document.getElementById('content-area').textContent; setView('dashboard'); return t; }""", view)

    def close(self):
        self.ctx.close()


def part_a(browser, old_url, new_url):
    print("\n[0] build a real v12 device state from the previous page (git HEAD)")
    d = Device(browser, old_url)
    s_old = d.db()
    d.close()
    ok("[0] HEAD page is pre-v13", FLAG not in s_old["meta"] and not any(a["id"] in ADDED for a in s_old["assignments"]))

    print("[1] fresh device")
    d = Device(browser, new_url)
    s = d.db()
    ids = {a["id"]: a for a in s["assignments"]}
    ok("[1] flag set", s["meta"].get(FLAG) is True)
    ok("[1] both v13 items seeded with their dates", all(i in ids and ids[i]["dueDate"] == due for i, due in ADDED.items()), {i: ids.get(i, {}).get("dueDate") for i in ADDED})
    topics = {t["id"]: t for t in s["topics"]}
    ok("[1] Ch 4 pt 2 marker on Oct 16", topics.get("chem1211-ch4-2", {}).get("startsDate") == "2026-10-16")
    ok("[1] Ch 6 marker flagged wrong", NEW_CH6 in topics["chem1211-ch6"]["title"])
    ok("[1] Exam 3 note provisional", ids["chem1211-exam3"]["notes"].startswith(NEW_EX3))
    ok("[1] a fresh device stamps nothing", not any("_ts" in a for a in s["assignments"]) and "_deleted" not in s)
    ok("[1] sidebar says not linked", "not linked" in d.page.inner_text("#last-synced"))
    ok("[1] no console errors", not d.errs, d.errs)
    d.close()

    print("[2] existing v12 device")
    d = Device(browser, new_url, json.dumps(s_old))
    s = d.db()
    ids = {a["id"]: a for a in s["assignments"]}
    old_ids = {a["id"]: a for a in s_old["assignments"]}
    ok("[2] v13 items added", all(i in ids for i in ADDED))
    ok("[2] item count grew by exactly 2", len(s["assignments"]) == len(s_old["assignments"]) + 2)
    ok("[2] Ch 6 title migrated", NEW_CH6 in next(t for t in s["topics"] if t["id"] == "chem1211-ch6")["title"])
    ok("[2] Exam 3 note migrated", ids["chem1211-exam3"]["notes"].startswith(NEW_EX3))
    ok("[2] migration rewrites are stamped", "notes" in ids["chem1211-exam3"].get("_ts", {}))
    ok("[2] untouched items carry no stamp", all("_ts" not in ids[i] for i in old_ids if i != "chem1211-exam3"))
    ok("[2] no console errors", not d.errs, d.errs)
    s_v13 = s
    d.close()

    print("[3] v12 device with Eric's own edits")
    edited = json.loads(json.dumps(s_old))
    for a in edited["assignments"]:
        if a["id"] == "chem1211-exam3":
            a["notes"] = "MY OWN NOTE"
        if a["id"] == X:
            a["status"] = "submitted"
    for t in edited["topics"]:
        if t["id"] == "chem1211-ch6":
            t["title"] = "MY CH6"
    d = Device(browser, new_url, json.dumps(edited))
    s = d.db()
    ids = {a["id"]: a for a in s["assignments"]}
    ok("[3] edited Exam 3 note kept", ids["chem1211-exam3"]["notes"] == "MY OWN NOTE")
    ok("[3] edited Ch 6 title kept", next(t for t in s["topics"] if t["id"] == "chem1211-ch6")["title"] == "MY CH6")
    ok("[3] status kept", ids[X]["status"] == "submitted")
    ok("[3] v13 items still added", all(i in ids for i in ADDED))
    d.close()

    print("[4] idempotent reload")
    d = Device(browser, new_url, json.dumps(s_v13))
    d.page.reload()
    d.settle()
    d.page.reload()
    d.settle()
    ok("[4] state unchanged across two reloads", json.dumps(d.db(), sort_keys=True) == json.dumps(s_v13, sort_keys=True))
    d.close()

    print("[5] negative control: flag pre-set")
    gated = json.loads(json.dumps(s_old))
    gated["meta"][FLAG] = True
    d = Device(browser, new_url, json.dumps(gated))
    s = d.db()
    ok("[5] gated device gets no v13 items", not any(a["id"] in ADDED for a in s["assignments"]))
    ok("[5] gated device keeps the old Exam 3 note", next(a for a in s["assignments"] if a["id"] == "chem1211-exam3")["notes"].startswith(OLD_EX3))
    d.close()

    print("[6] what renders")
    d = Device(browser, new_url, json.dumps(s_old))
    dash = d.view_text("dashboard")
    ok("[6] Deadline-unknown panel lists Ch 4 Part 2 homework", "Chapter 4 Part 2 homework on Knewton" in dash)
    res = d.view_text("resources")
    ok("[6] Resources lists Handout 13 and the Oct 19 deck", "13: Lewis structures" in res and "Oct 19: Lewis structures" in res)
    intel = d.view_text("instructors")
    ok("[6] Intel shows EXAM 2 IS BACK and the Oct 21 SCI status", "EXAM 2 IS BACK" in intel and "Oct 21 D2L export (9:42 AM)" in intel)
    ok("[6] no stale Sept 23 SCI status", "Current through the Sept 23" not in intel)
    ok("[6] no console errors", not d.errs, d.errs)
    d.close()
    return s_old


def part_b(browser, new_url, s_old):
    print("\n[S1] negative control: unlinked devices")
    a = Device(browser, new_url, json.dumps(s_old))
    b = Device(browser, new_url, json.dumps(s_old))
    a.page.evaluate("id => toggleDone(id)", X)
    a.page.wait_for_timeout(900)
    b.page.reload()
    b.settle()
    ok("[S1] A sees its own checkmark", a.item(X)["status"] == "submitted")
    ok("[S1] B does NOT see it without a link (the reported bug)", b.item(X)["status"] == "todo")
    a.close()
    b.close()

    print("[S2] link a legacy laptop and a legacy desktop")
    laptop_state = json.loads(json.dumps(s_old))
    for it in laptop_state["assignments"]:
        if it["id"] == X:
            it["status"] = "submitted"
    laptop = Device(browser, new_url, json.dumps(laptop_state), link=(SYNC_KEY, ENDPOINT))
    ok("[S2] setup link stored and stripped from the URL", "#sync" not in laptop.page.url and laptop.page.evaluate("() => !!Sync.cfg()"))
    ok("[S2] laptop reports synced", laptop.page.evaluate("() => Sync.state") == "ok" and "Synced across devices" in laptop.page.inner_text("#last-synced"), laptop.page.inner_text("#last-synced"))
    desk = Device(browser, new_url, json.dumps(s_old), link=(SYNC_KEY, ENDPOINT))
    ok("[S2] desktop picks up the laptop's checkmark", desk.item(X)["status"] == "submitted", desk.item(X)["status"])
    ok("[S2] desktop UI shows it under Completed", desk.page.evaluate("id => isComplete(db.assignments.find(a => a.id === id))", X))
    # Both devices may run v13 themselves (same text, stamps ms apart) when the first device's
    # post-migration push has not landed yet. One more round trip must converge them exactly.
    laptop.sync()
    desk.sync()
    laptop.sync()
    la, de = laptop.db(), desk.db()
    diff = sorted(k for k in set(la) | set(de) if json.dumps(la.get(k), sort_keys=True) != json.dumps(de.get(k), sort_keys=True))
    meta_diff = sorted(k for k in set(la["meta"]) | set(de["meta"]) if la["meta"].get(k) != de["meta"].get(k))
    ex3 = lambda st: next(a for a in st["assignments"] if a["id"] == "chem1211-exam3").get("_ts")
    ok("[S2] both copies identical after a round trip", not diff, {"keys": diff, "meta": meta_diff, "lastSync": [la["meta"].get("lastSync"), de["meta"].get("lastSync")], "ex3_ts": [ex3(la), ex3(de)]})

    print("[S3] uncheck on the desktop propagates to the laptop")
    desk.page.evaluate("id => toggleDone(id)", X)
    desk.page.wait_for_timeout(200)
    desk.sync()
    laptop.sync()
    ok("[S3] laptop now shows To Do", laptop.item(X)["status"] == "todo", laptop.item(X))

    print("[S4] different fields of one item, edited on different devices")
    # Explicit order: the note reaches the Worker first, then the desktop (whose copy still has the
    # old note) sends a later-stamped checkmark. Field-level merge keeps both; item-level would not.
    laptop.page.evaluate("id => { const a = db.assignments.find(x => x.id === id); a.notes = 'EDITED ON LAPTOP'; save(db); }", Y)
    laptop.sync()
    desk.page.evaluate("id => toggleDone(id)", Y)
    desk.page.wait_for_timeout(900)
    desk.sync()
    laptop.sync()
    for dev, nm in ((laptop, "laptop"), (desk, "desktop")):
        it = dev.item(Y)
        ok("[S4] %s has both the note and the checkmark" % nm, it["notes"] == "EDITED ON LAPTOP" and it["status"] == "submitted", {"notes": it["notes"][:30], "status": it["status"]})

    print("[S5] delete propagates")
    laptop.page.evaluate("id => deleteAssignment(id)", Z)
    laptop.sync()
    desk.sync()
    ok("[S5] deleted on the laptop, gone on the desktop", desk.item(Z) is None)

    print("[S6] wrong key")
    before = json.dumps(desk.db(), sort_keys=True)
    bad = Device(browser, new_url, json.dumps(s_old), link=("wrong-key-0123456789abcdef", ENDPOINT))
    ok("[S6] rejected, and the page says so", bad.page.evaluate("() => Sync.state") == "denied" and "rejected" in bad.page.inner_text("#last-synced"))
    ok("[S6] rejected device keeps its own state", bad.item(Z) is not None)
    desk.sync()
    ok("[S6] server state untouched by the rejected device", json.dumps(desk.db(), sort_keys=True) == before)
    bad.close()

    print("[S7] endpoint unreachable")
    off = Device(browser, new_url, json.dumps(s_old), link=(SYNC_KEY, DEAD_ENDPOINT))
    ok("[S7] offline state shown", off.page.evaluate("() => Sync.state") == "offline" and "Offline" in off.page.inner_text("#last-synced"))
    off.page.evaluate("id => toggleDone(id)", X)
    off.page.wait_for_timeout(900)
    ok("[S7] local checkmark still saved", off.item(X)["status"] == "submitted")
    ok("[S7] page still migrated and rendered", off.db()["meta"].get(FLAG) is True and len(off.page.inner_text("#content-area")) > 200)
    off.close()

    print("[S8] stale v12 device pulls before it migrates")
    laptop.page.evaluate("() => { const a = db.assignments.find(x => x.id === 'chem1211-exam3'); a.notes = 'EXAM 3 NOTE EDITED ON LAPTOP'; save(db); }")
    laptop.sync()
    stale = Device(browser, new_url, json.dumps(s_old), link=(SYNC_KEY, ENDPOINT))
    stale.sync()
    ok("[S8] stale device keeps the laptop's Exam 3 note", stale.item("chem1211-exam3")["notes"] == "EXAM 3 NOTE EDITED ON LAPTOP", stale.item("chem1211-exam3")["notes"][:60])
    laptop.sync()
    ok("[S8] and the laptop still has it after the stale device synced", laptop.item("chem1211-exam3")["notes"] == "EXAM 3 NOTE EDITED ON LAPTOP")
    stale.close()

    print("[S8b] stale v12 device whose first pull FAILS, so it migrates on its own")
    lost = Device(browser, new_url, json.dumps(s_old), link=(SYNC_KEY, DEAD_ENDPOINT))
    ok("[S8b] it migrated offline", lost.db()["meta"].get(FLAG) is True and lost.item("chem1211-exam3")["notes"].startswith(NEW_EX3))
    lost.page.evaluate("([k, u]) => localStorage.setItem('boris_school_sync', JSON.stringify({key: k, url: u}))", [SYNC_KEY, ENDPOINT])
    lost.sync()
    laptop.sync()
    ok("[S8b] its migration does not overwrite the laptop's earlier edit", lost.item("chem1211-exam3")["notes"] == "EXAM 3 NOTE EDITED ON LAPTOP", lost.item("chem1211-exam3")["notes"][:60])
    ok("[S8b] the laptop keeps its edit too", laptop.item("chem1211-exam3")["notes"] == "EXAM 3 NOTE EDITED ON LAPTOP")
    lost.close()

    print("[S9] an edit modal left open on the desktop while the laptop checks the item off")
    W = "chem1211-exam2-review"
    desk.page.evaluate("id => openEditModal(id)", W)
    laptop.page.evaluate("id => toggleDone(id)", W)
    laptop.page.wait_for_timeout(900)
    laptop.sync()
    desk.sync()
    desk.page.evaluate("() => { document.getElementById('f-notes').value = 'NOTE FROM DESK MODAL'; saveAssignment(); }")
    desk.sync()
    laptop.sync()
    for dev, nm in ((laptop, "laptop"), (desk, "desktop")):
        it = dev.item(W)
        ok("[S9] %s keeps the laptop's checkmark and the desktop's note" % nm, it["status"] == "submitted" and it["notes"] == "NOTE FROM DESK MODAL", {"status": it["status"], "notes": it["notes"][:30]})
    ok("[S9] saving through the modal leaves the due date alone", desk.item(W)["dueDate"] == "2026-10-23T10:00:00-04:00", desk.item(W)["dueDate"])

    print("[S10] a change written by an older copy of the page (no stamps) still syncs")
    raw = desk.db()
    for it in raw["assignments"]:
        if it["id"] == Y:
            it["status"] = "todo"
    desk.page.evaluate("([k, v]) => localStorage.setItem(k, v)", [KEY, json.dumps(raw)])
    desk.page.reload()
    desk.settle()
    desk.sync()
    laptop.sync()
    ok("[S10] the laptop sees the older page's uncheck", laptop.item(Y)["status"] == "todo", laptop.item(Y)["status"])
    ok("[S8-S10] no console errors on any linked device", not (laptop.errs or desk.errs), laptop.errs + desk.errs)
    laptop.close()
    desk.close()


def main():
    old_url = serve(old_page_dir())
    new_url = serve(os.path.dirname(PAGE)) + os.path.basename(PAGE)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        s_old = part_a(browser, old_url, new_url)
        if os.environ.get("SKIP_SYNC") != "1":
            global ENDPOINT
            proc = None
            if not ENDPOINT:
                proc, ENDPOINT = start_worker()
            try:
                part_b(browser, new_url, s_old)
            finally:
                if proc:
                    stop_worker(proc)
        browser.close()
    print("\n%d passed, %d failed" % (_pass, len(_fails)))
    for f in _fails:
        print("  FAILED: " + f)
    sys.exit(1 if _fails else 0)


if __name__ == "__main__":
    main()
