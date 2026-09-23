/* Close-audit gap: the S162 suite tested a device that already has the v8 items
   (null-dated). It did NOT test a device that has never loaded the S156 build, where
   the v8 migration itself inserts the Alignment row - now from an array whose entry
   already carries the date. That path must also end dated, and the v9 guard must not
   double-handle it. */
const { chromium } = require('playwright');
const KEY = 'boris_school_fall2026';
const NEW = 'file:///' + 'C:/Claude Code/Projects/Schoolwork/fall2026/index.html'.replace(/ /g, '%20');
const OLD = 'file:///' + process.argv[2].replace(/\\/g, '/').replace(/ /g, '%20');
const ID = 'sci2900-alignment';
const EXPECT = '2026-09-22T17:00:00-04:00';
let pass = 0, fail = 0;
const ok = (n, c, x) => c ? (pass++, console.log('  PASS  ' + n)) : (fail++, console.log('  FAIL  ' + n + (x !== undefined ? '  -> ' + JSON.stringify(x) : '')));

(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext();

  // Build a pre-S156 device: load the old page, then strip the v8 flag AND its items.
  let p = await ctx.newPage();
  await p.goto(OLD); await p.waitForTimeout(500);
  const preV8 = await p.evaluate(function (k) {
    const o = JSON.parse(localStorage.getItem(k));
    delete o.meta.fall2026_sept21_v8;
    o.assignments = o.assignments.filter(a => !['sci2900-alignment', 'sci2900-curtain-paper', 'sci2900-path-forward'].includes(a.id));
    localStorage.setItem(k, JSON.stringify(o));
    return localStorage.getItem(k);
  }, KEY);
  await p.close();
  const pre = JSON.parse(preV8);
  ok('PRECONDITION: alignment absent before load', !pre.assignments.some(a => a.id === ID));
  ok('PRECONDITION: v8 flag absent', pre.meta.fall2026_sept21_v8 === undefined);

  p = await ctx.newPage();
  await p.addInitScript(function (a) { localStorage.setItem(a[0], a[1]); }, [KEY, preV8]);
  await p.goto(NEW); await p.waitForTimeout(600);
  const after = JSON.parse(await p.evaluate(k => localStorage.getItem(k), KEY));
  const rows = after.assignments.filter(a => a.id === ID);
  ok('exactly one alignment row (no double insert)', rows.length === 1, rows.length);
  ok('v8 path yields the dated row', rows[0] && rows[0].dueDate === EXPECT, rows[0] && rows[0].dueDate);
  ok('both flags set', after.meta.fall2026_sept21_v8 === true && after.meta.sci2900_alignment_due_v9 === true);
  const od = await p.evaluate(() => {
    const h = [...document.querySelectorAll('.section-header')].find(x => /Overdue/.test(x.textContent));
    if (!h) return null;
    let n = h.nextElementSibling;
    while (n && !n.classList.contains('assignment-list')) n = n.nextElementSibling;
    return n ? n.textContent : null;
  });
  ok('renders under Overdue on this path too', od && /Alignment and Graduate School Readiness/.test(od));

  await b.close();
  console.log('\n  ' + pass + ' passed, ' + fail + ' failed');
  process.exit(fail ? 1 : 0);
})();
