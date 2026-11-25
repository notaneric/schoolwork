// Data contract for chem1211-final-game.html (cloned from tools/exam3/contract.mjs).
// Usage: node tools/final/contract.mjs <page.html>
// Added for the final: every level has a video, no text names Exam 3, the boss pool can fill a round.
// Failing control: every run also checks four planted defects (a position-naming explanation, a
// typed regex that rejects its own answer, a stray caret, a duplicate option) and fails the run if
// any one of them (or a level stripped of its video) slips through, so a contract that has gone blind cannot report OK.
import fs from 'fs';

const html = fs.readFileSync(process.argv[2], 'utf8');
const js = html.slice(html.indexOf('<script>') + 8, html.lastIndexOf('</script>'));
const a = js.indexOf('// YouTube oEmbed-verified'), b = js.indexOf('const ICON = {');
const load = () => new Function(js.slice(a, b) + '\nreturn { VIDEOS, TABLE, LEVELS, Q };')();
const norm = new Function(js.match(/const norm = .*;/)[0] + '\nreturn norm;')();
const ICON = new Function(js.slice(b, js.indexOf('\n};', b) + 3) + '\nreturn ICON;')();
const POS = /\b(option|choice)\s*[A-D1-4]\b|\b(first|second|third|fourth|last) (option|choice|answer)\b|\([a-d]\)/i;
const CARET = /\^(?!(\d*[+\-−](?!\d)|[+\-−]?\d+))/;

function check({ VIDEOS, LEVELS, Q }) {
  const fails = [], ok = (c, m) => { if (!c) fails.push(m); };
  LEVELS.forEach((l, i) => {
    ok(l.n === i + 1, `level ${i + 1} is numbered ${l.n}`);
    ok(ICON[l.icon], `level ${l.n}: icon ${l.icon} missing`);
    ok(html.includes(`<template id="lesson-${l.n}">`), `level ${l.n}: lesson template missing`);
  });
  for (const [k, v] of Object.entries(VIDEOS)) {
    ok(LEVELS.some(l => l.n === +k), `video for unknown level ${k}`);
    ok(/^[\w-]{11}$/.test(v.id) && (!v.alt || /^[\w-]{11}$/.test(v.alt.id)), `level ${k}: malformed video id`);
  }
  const seen = new Set();
  Q.forEach((q, i) => {
    const tag = `Q${i} (lv ${q.lv}) "${q.q.slice(0, 44)}"`;
    ok(LEVELS.some(l => l.n === q.lv), `${tag}: unknown level`);
    ok(!seen.has(q.q), `${tag}: duplicate stem`); seen.add(q.q);
    ok(q.why && q.why.length > 10, `${tag}: missing explanation`);
    ok(!POS.test(q.why), `${tag}: explanation names an option by position`);
    if (q.t === 'mc') {
      ok(Array.isArray(q.a) && q.a.length === 4, `${tag}: needs 4 options`);
      ok(new Set(q.a).size === q.a.length, `${tag}: duplicate options`);
    } else {
      ok(q.t === 'type' && q.ans && q.re, `${tag}: typed question needs ans and re`);
      ok(!q.boss, `${tag}: boss-only typed question is unreachable`);
      ok(new RegExp(q.re).test(norm(q.ans)), `${tag}: re rejects its own answer`);
    }
    const text = [q.q, q.why, q.ans || '', ...(q.a || [])].join(' ');
    ok(!/[—·]/.test(text), `${tag}: em dash or middot`);
    ok(!CARET.test(text), `${tag}: stray caret`);
  });
  // level 18 (polyatomic ions) came from Exam 3 without a video; every other level needs one
  LEVELS.forEach(l => ok(VIDEOS[l.n] || l.n === 18, `level ${l.n}: no video`));
  const bossPool = Q.filter(q => q.t === 'mc').length;
  ok(bossPool >= 60, `boss pool has only ${bossPool} multiple-choice questions`);
  LEVELS.forEach(l => {
    const n = Q.filter(q => q.lv === l.n && !q.boss).length;
    ok(n >= 8 && n <= 16, `level ${l.n}: ${n} level questions (want 8 to 16)`);
  });
  return fails;
}

const real = load();
const fails = check(real);
const lessons = html.slice(html.indexOf('<template id="lesson-1">'), html.indexOf('<script>'));
if (/[—·]/.test(lessons)) fails.push('lessons: em dash or middot');
if (CARET.test(lessons.replace(/<[^>]+>/g, ''))) fails.push('lessons: stray caret');
if (/Exam 3/.test(html.slice(0, html.indexOf('const ICON = {')))) fails.push('page text still names Exam 3');

const PLANTS = [
  ['explanation names an option by position', d => { d.Q[0].why = 'Pick the second option, because it is right.'; }],
  ['re rejects its own answer', d => { const q = d.Q.find(x => x.t === 'type'); q.re = '^nope$'; }],
  ['stray caret', d => { d.Q[1].why += ' Charge ^x.'; }],
  ['duplicate options', d => { const q = d.Q.find(x => x.t === 'mc'); q.a[1] = q.a[0]; }],
  ['no video', d => { delete d.VIDEOS[d.LEVELS[0].n]; }],
];
for (const [want, plant] of PLANTS) {
  const d = load(); plant(d);
  if (!check(d).some(f => f.includes(want))) fails.push(`CONTROL: planted "${want}" was not caught`);
}

const { LEVELS, Q, VIDEOS } = real;
console.log(`levels ${LEVELS.length}, questions ${Q.length} (${Q.filter(q => q.t === 'type').length} typed, ${Q.filter(q => q.boss).length} boss-only), videos ${Object.keys(VIDEOS).length}`);
console.log('per level ' + LEVELS.map(l => l.n + ':' + Q.filter(q => q.lv === l.n && !q.boss).length).join(' '));
if (fails.length) { console.log(`FAIL ${fails.length}`); fails.forEach(f => console.log('  ' + f)); process.exit(1); }
console.log(`contract OK (${PLANTS.length}/${PLANTS.length} planted defects caught)`);
