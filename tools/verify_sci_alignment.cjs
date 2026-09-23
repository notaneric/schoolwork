const { chromium } = require('playwright');
const KEY = 'boris_school_fall2026';
const NEW = 'file:///' + 'C:/Claude Code/Projects/Schoolwork/fall2026/index.html'.replace(/ /g, '%20');
const OLD = 'file:///' + process.argv[2].replace(/\\/g, '/').replace(/ /g, '%20');
const ID = 'sci2900-alignment';
const EXPECT = '2026-09-22T17:00:00-04:00';

let pass = 0, fail = 0;
function ok(name, cond, extra) {
  if (cond) { pass++; console.log('  PASS  ' + name); }
  else { fail++; console.log('  FAIL  ' + name + (extra !== undefined ? ('  -> ' + JSON.stringify(extra)) : '')); }
}

async function loadWith(ctx, url, state) {
  const page = await ctx.newPage();
  if (state !== null) {
    await page.addInitScript(function (arg) { localStorage.setItem(arg[0], arg[1]); }, [KEY, state]);
  }
  await page.goto(url);
  await page.waitForTimeout(500);
  return page;
}
const dump = p => p.evaluate(k => localStorage.getItem(k), KEY);
async function item(p) {
  return JSON.parse(await dump(p)).assignments.find(a => a.id === ID);
}
function sectionBody(p, re) {
  return p.evaluate(function (src) {
    const rx = new RegExp(src);
    const hs = Array.from(document.querySelectorAll('.section-header'));
    const h = hs.find(x => rx.test(x.textContent));
    if (!h) return null;
    let n = h.nextElementSibling;
    while (n && !n.classList.contains('assignment-list')) n = n.nextElementSibling;
    return n ? n.textContent : null;
  }, re);
}

(async () => {
  const browser = await chromium.launch();

  console.log('\n[1] Fresh device (no localStorage)');
  let ctx = await browser.newContext();
  let p = await loadWith(ctx, NEW, null);
  let a = await item(p);
  ok('alignment exists', !!a);
  ok('due date is Sept 22 5pm', a.dueDate === EXPECT, a.dueDate);
  ok('title carries the D2L name', /Alignment and Graduate School Readiness/.test(a.title), a.title);
  let od = await sectionBody(p, 'Overdue');
  ok('Overdue section rendered', od !== null);
  ok('alignment listed under Overdue', od && /Alignment and Graduate School Readiness/.test(od), (od || '').slice(0, 200));
  await ctx.close();

  console.log('\n[2] Existing device (state produced by the pre-change page)');
  ctx = await browser.newContext();
  let pOld = await loadWith(ctx, OLD, null);
  const oldState = await dump(pOld);
  const oldItem = JSON.parse(oldState).assignments.find(x => x.id === ID);
  ok('PRECONDITION: old page really leaves dueDate null', oldItem.dueDate === null, oldItem.dueDate);
  ok('PRECONDITION: old page has no v9 flag', JSON.parse(oldState).meta.sci2900_alignment_due_v9 === undefined);
  await pOld.close();
  p = await loadWith(ctx, NEW, oldState);
  a = await item(p);
  ok('migration set the date', a.dueDate === EXPECT, a.dueDate);
  ok('migration retitled it', /Alignment and Graduate School Readiness/.test(a.title), a.title);
  ok('notes mention PAST DUE', /PAST DUE/.test(a.notes));
  const migrated = await dump(p);
  ok('v9 flag set', JSON.parse(migrated).meta.sci2900_alignment_due_v9 === true);
  await ctx.close();

  console.log('\n[3] Idempotency (double reload)');
  ctx = await browser.newContext();
  p = await loadWith(ctx, NEW, migrated);
  const r1 = await dump(p); await p.close();
  p = await loadWith(ctx, NEW, r1);
  const r2 = await dump(p);
  ok('exactly one alignment row', JSON.parse(r1).assignments.filter(x => x.id === ID).length === 1);
  const strip = s => { const o = JSON.parse(s); delete o.meta.lastSync; return JSON.stringify(o); };
  ok('state stable across reloads', strip(r1) === strip(r2));
  await ctx.close();

  console.log('\n[4] User-edited (Eric set his own date before the update landed)');
  ctx = await browser.newContext();
  pOld = await loadWith(ctx, OLD, null);
  const edited = await pOld.evaluate(function (arg) {
    const o = JSON.parse(localStorage.getItem(arg[0]));
    const t = o.assignments.find(x => x.id === arg[1]);
    t.dueDate = '2026-10-01T12:00:00-04:00';
    t.notes = 'MY OWN NOTE';
    localStorage.setItem(arg[0], JSON.stringify(o));
    return localStorage.getItem(arg[0]);
  }, [KEY, ID]);
  await pOld.close();
  p = await loadWith(ctx, NEW, edited);
  a = await item(p);
  ok('Eric date survives', a.dueDate === '2026-10-01T12:00:00-04:00', a.dueDate);
  ok('Eric note survives', a.notes === 'MY OWN NOTE', a.notes);
  await ctx.close();

  console.log('\n[5] Negative control (v9 flag already set, date still null)');
  ctx = await browser.newContext();
  pOld = await loadWith(ctx, OLD, null);
  const preflagged = await pOld.evaluate(function (arg) {
    const o = JSON.parse(localStorage.getItem(arg[0]));
    o.meta.sci2900_alignment_due_v9 = true;
    localStorage.setItem(arg[0], JSON.stringify(o));
    return localStorage.getItem(arg[0]);
  }, [KEY]);
  await pOld.close();
  p = await loadWith(ctx, NEW, preflagged);
  a = await item(p);
  ok('date stays null when guard pre-set (proves the assertion reads the migration, not the seed)', a.dueDate === null, a.dueDate);
  await ctx.close();

  console.log('\n[6] Deadline-unknown panel');
  ctx = await browser.newContext();
  p = await loadWith(ctx, NEW, null);
  const panel = await sectionBody(p, 'Deadline unknown');
  ok('panel present', panel !== null);
  ok('lists the Curtain Paper', panel && /Curtain Paper/.test(panel));
  ok('lists The Path Forward', panel && /Path Forward/.test(panel));
  ok('does NOT list the now-dated Alignment', panel && !/Alignment and Graduate School Readiness/.test(panel));
  const allDated = await p.evaluate(function (arg) {
    const o = JSON.parse(localStorage.getItem(arg[0]));
    o.assignments.forEach(x => { if (!x.dueDate) x.dueDate = '2026-11-01T12:00:00-04:00'; });
    localStorage.setItem(arg[0], JSON.stringify(o));
    return localStorage.getItem(arg[0]);
  }, [KEY]);
  await p.close();
  p = await loadWith(ctx, NEW, allDated);
  const gone = await sectionBody(p, 'Deadline unknown');
  ok('NEGATIVE: panel disappears when nothing is undated (proves it can fail)', gone === null, gone);
  await ctx.close();

  console.log('\n[7] Console health');
  ctx = await browser.newContext();
  const errs = [];
  const p7 = await ctx.newPage();
  p7.on('pageerror', e => errs.push(String(e)));
  p7.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  await p7.goto(NEW);
  await p7.waitForTimeout(700);
  for (const v of ['list', 'calendar', 'dashboard']) {
    await p7.evaluate(vv => { if (window.switchView) switchView(vv); }, v).catch(() => {});
    await p7.waitForTimeout(250);
  }
  ok('no console/page errors across views', errs.length === 0, errs.slice(0, 3));
  await ctx.close();

  await browser.close();
  console.log('\n================  ' + pass + ' passed, ' + fail + ' failed  ================');
  process.exit(fail ? 1 : 0);
})();
