"""Build chem1211-exam3-game.html: the approved study-game engine (chem1211-polarity-imf.html)
with the Exam 3 lessons and data from this folder.

Usage: python tools/exam3/build_exam3.py
Every engine edit is an exact-string substitution that must match exactly once, so a drifted
template stops the build instead of shipping a half-patched page. Levels 9-11 reuse the polarity
game's reviewed lessons and questions (old levels 1-5); a few move to the boss pool to keep the
levels short. The data contract (contract.mjs) runs last and fails the build on any defect.
"""
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / 'chem1211-polarity-imf.html'
OUT = ROOT / 'chem1211-exam3-game.html'
SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
DOT = ' fill="currentColor" stroke="none"/>'


def once(s, old, new):
    n = s.count(old)
    assert n == 1, f'expected 1 match, found {n}: {old[:80]!r}'
    return s.replace(old, new)


t = SRC.read_text(encoding='utf-8')
lessons_src = (HERE / 'lessons.html').read_text(encoding='utf-8')
data = (HERE / 'data.js').read_text(encoding='utf-8')

# 1. lessons: new 1-8 and 12-16; 9-11 are the polarity game's lessons 1-5 plus a solubility block
old = dict(re.findall(r'<template id="lesson-(\d)">\n(.*?)\n</template>', t, re.S))
assert sorted(old) == ['1', '2', '3', '4', '5'], sorted(old)
m = re.search(r'<!-- @@EXTRA-11@@ -->\n(.*?)\n<!-- @@END-EXTRA-11@@ -->\n', lessons_src, re.S)
assert m, 'extra-11 block missing'
extra11 = '\n'.join('  ' + ln if ln else ln for ln in m.group(1).split('\n'))
new = {i: b for b, i in re.findall(r'(<template id="lesson-(\d+)">.*?</template>\n)', lessons_src.replace(m.group(0), ''), re.S)}
assert sorted(map(int, new)) == [1, 2, 3, 4, 5, 6, 7, 8, 12, 13, 14, 15, 16], sorted(new)


def tmpl(n, inner):
    return f'<template id="lesson-{n}">\n{inner}\n</template>\n'


lessons = ''.join(new[str(i)] + '\n' for i in range(1, 9))
lessons += tmpl(9, old['1'] + '\n' + old['2']) + '\n'
lessons += tmpl(10, old['3'] + '\n' + old['4']) + '\n'
lessons += tmpl(11, old['5'] + '\n' + extra11) + '\n'
lessons += ''.join(new[str(i)] + '\n' for i in range(12, 17))

# 2. polarity questions: old levels 1-2 -> 9, 3-4 -> 10, 5 -> 11; extras to the boss pool
qa = t.index('const Q = [')
qblock = t[qa:t.index('\n];', qa)]
pol = [ln for ln in qblock.split('\n') if re.match(r'\s*\{ lv: [1-5],', ln)]
assert len(pol) >= 40, len(pol)
REMAP = {'1': '9', '2': '9', '3': '10', '4': '10', '5': '11'}
pol = [re.sub(r'\{ lv: ([1-5]),', lambda mm: '{ lv: ' + REMAP[mm.group(1)] + ',', ln, count=1) for ln in pol]
TO_BOSS = [
    "q: 'In an O-H bond, the partial negative charge",
    "q: 'A bond with an electronegativity difference of 2.5 is'",
    "q: 'Which molecule is polar?'",
    "q: 'SO2 is'",
    "q: 'In a gas, which wins?'",
    "q: 'As the number of electrons in a molecule rises",
    "q: 'Which halogen is a solid at room temperature?'",
    "q: 'As the IMFs in a liquid get stronger",
]
for key in TO_BOSS:
    hits = [i for i, ln in enumerate(pol) if key in ln]
    assert len(hits) == 1, (key, len(hits))
    ln = pol[hits[0]]
    assert 'boss: true' not in ln and "t: 'mc'" in ln, key
    pol[hits[0]] = ln.replace("t: 'mc'", "boss: true, t: 'mc'", 1)

# review S346: the stem handed over the symmetry it tests
bf3 = [i for i, ln in enumerate(pol) if "q: 'BF3 is trigonal planar with three identical B-F bonds. The molecule is'" in ln]
assert len(bf3) == 1, bf3
pol[bf3[0]] = pol[bf3[0]].replace('with three identical B-F bonds. The molecule is', 'and every outer atom is F. The molecule is')

ta = t.index('// [SN, shape')
data = once(data, '// @@TABLE@@', t[ta:t.index('];', ta) + 2])
data = once(data, '  // @@POLARITY_Q@@', '\n'.join(pol))
NL = len(re.findall(r'\{ n: \d+, name:', data))
assert NL == 16, NL

# 3. splice lessons and data into the engine
a, b = t.index('<template id="lesson-1">'), t.index('<script>')
t = t[:a] + lessons + t[b:]
a, b = t.index('// YouTube oEmbed-verified'), t.index('const ICON = {')
t = t[:a] + data.rstrip('\n') + '\n\n' + t[b:]

# 4. engine edits
E = [
    ('<title>Polarity and IMFs</title>', '<title>CHEM 1211 Exam 3</title>'),
    ('<small>/15</small>', f'<small>/{NL * 3}</small>'),
    ("const KEY = 'chem1211q3_game_v1';", "const KEY = 'chem1211e3_game_v1';\nconst BOSS_N = 10, BOSS_SECS = 300;"),
    # Nov 16 revision: no gating. Every level and the boss round are open from the start, so any
    # topic can be studied first; stars still record progress.
    ('const unlocked = n => n === 1 || (S.stars[n - 1] || 0) > 0;',
     '// every level and the boss round are open from the start; stars only record progress\nconst unlocked = () => true;'),
    ('const bossUnlocked = () => LEVELS.every(l => (S.stars[l.n] || 0) > 0);', 'const bossUnlocked = () => true;'),
    ('off = [0, -60, 0, 60, 0];', 'off = [0, -60, 0, 60];'),
    ('<h1>Polarity and IMFs</h1><p class="when">Oct 26 and Oct 28 lectures</p></header>',
     '<h1>Exam 3 study game</h1><p class="when">Wed Nov 18, 10:00, LDSC 210</p><p class="hint">Every level is open. Jump to any topic, starting with the one you know least.</p></header>'),
    ("""h += '<div class="stop" style="--x:' + off[i] + 'px">""",
     """h += (l.unit ? '<div class="unit"><small>' + l.unit + '</small><b>' + l.uname + '</b><span>' + l.sub + '</span></div>' : '') +
      '<div class="stop" style="--x:' + off[i % off.length] + 'px">"""),
    ("<small>Boss round</small>3-minute quiz</div>'", "<small>Boss round</small>' + BOSS_N + ' questions, 5 minutes</div>'"),
    ("""'<div class="best">Best: ' + S.boss + ' of 6</div>'""", """'<div class="best">Best: ' + S.boss + ' of ' + BOSS_N + '</div>'"""),
    ("toast('Clear all five levels first');", "toast('Clear all ' + LEVELS.length + ' levels first');"),
    ("""'<p class="kicker">Level ' + n + ' of 5</p>""", """'<p class="kicker">Level ' + n + ' of ' + LEVELS.length + '</p>"""),
    ('  if (n === 2) {', "  if ($('#pol')) {"),
    ("""  document.querySelectorAll('.vid').forEach(b => b.onclick = () => {
    const f = document.createElement('iframe');""",
     """  document.querySelectorAll('.vid').forEach(b => b.onclick = () => {
    // YouTube refuses embeds on a file:// page (Error 153: no referrer), so a local copy opens the video on YouTube instead
    if (location.protocol === 'file:') return void window.open('https://www.youtube.com/watch?v=' + encodeURIComponent(b.dataset.id), '_blank', 'noopener');
    const f = document.createElement('iframe');"""),
    ("""<h1 class="lvl">3-minute quiz</h1>""", """<h1 class="lvl">' + BOSS_N + ' questions, 5 minutes</h1>"""),
    (r"""'<p>6 questions from all five levels, 15 XP each.""", r"""'<p>' + BOSS_N + ' multiple-choice questions from all ' + LEVELS.length + ' levels, 15 XP each."""),
    ("""'<p><b>Best: ' + S.boss + ' of 6</b></p>'""", """'<p><b>Best: ' + S.boss + ' of ' + BOSS_N + '</b></p>'"""),
    ('(boss.left / 180 * 100)', '(boss.left / BOSS_SECS * 100)'),
    ('shuffle(pool).slice(0, 6), i: 0, right: 0, left: 180,', 'shuffle(pool).slice(0, BOSS_N), i: 0, right: 0, left: BOSS_SECS,'),
    ("topbar(boss.left / 180, (boss.i + 1) + '/6')", "topbar(boss.left / BOSS_SECS, (boss.i + 1) + '/' + BOSS_N)"),
    ("""'<h2>' + r + ' of 6 right</h2>'""", """'<h2>' + r + ' of ' + BOSS_N + ' right</h2>'"""),
    ("'Best: ' + S.boss + ' of 6') + '</p>'", "'Best: ' + S.boss + ' of ' + BOSS_N) + '</p>'"),
    ('if (r >= 5) celebrate();', 'if (r >= BOSS_N - 1) celebrate();'),
    ("acceptNode: n => /[A-Z][a-z]?\\d/.test(n.nodeValue) && !n.parentElement.closest('sub, script, style')",
     "acceptNode: n => /[A-Z][a-z]?\\d|\\^/.test(n.nodeValue) && !n.parentElement.closest('sub, sup, script, style')"),
    ("t.innerHTML = esc(n.nodeValue).replace(/([A-Z][a-z]?)(\\d+)/g, '$1<sub>$2</sub>');",
     "t.innerHTML = esc(n.nodeValue).replace(/\\^(\\d*[+\\-−])(?!\\d)/g, '<sup>$1</sup>').replace(/\\^([+\\-−]?\\d+)/g, '<sup>$1</sup>').replace(/([A-Z][a-z]?)(\\d+)/g, '$1<sub>$2</sub>');"),
    ('// formulas: a capital letter (plus optional lowercase) followed by digits gets the digits as a subscript',
     '// formulas: a capital letter (plus optional lowercase) followed by digits gets the digits as a subscript;\n// a caret marks a charge or exponent (SO4^2-, Cr^3+, 10^6) and becomes a superscript'),
    ('.path { display: flex; flex-direction: column; align-items: center; padding: 58px 0 4px; }',
     '.path { display: flex; flex-direction: column; align-items: center; padding: 26px 0 4px; }'),
    ('</style>', """  .hint { margin: 8px auto 0; max-width: 34em; color: var(--muted); font-size: 15px; }
  .unit { align-self: stretch; margin: 0 0 64px; padding-top: 18px; text-align: center; border-top: 2px solid var(--line); }
  .unit:first-child { padding-top: 0; border-top: 0; }
  .unit small { display: block; font-size: 12px; font-weight: 800; letter-spacing: .08em; text-transform: uppercase; color: var(--green); }
  .unit b { display: block; margin-top: 2px; font-size: 20px; line-height: 1.25; }
  .unit span { display: block; margin-top: 2px; font-size: 14px; font-weight: 600; color: var(--muted); }
  .eq { margin: 0 0 12px; text-align: center; font-size: 17px; font-weight: 800; line-height: 1.4; }
  .stop .label { max-width: 200px; }
  @media (max-width: 400px) { .stop { transform: translateX(calc(var(--x, 0px) * .6)); } }
</style>"""),
]
for o, n in E:
    t = once(t, o, n)

ICONS = {
    'dots': f'<circle cx="12" cy="12" r="4.2"/><circle cx="12" cy="3.6" r="1.3"{DOT}<circle cx="12" cy="20.4" r="1.3"{DOT}<circle cx="3.6" cy="12" r="1.3"{DOT}<circle cx="20.4" cy="12" r="1.3"{DOT}',
    'ion': '<path d="M5 4.5H3.5v15H5M19 4.5h1.5v15H19"/><path d="M12 8.5v7M8.5 12h7"/>',
    'dbl': '<circle cx="5" cy="12" r="3"/><circle cx="19" cy="12" r="3"/><path d="M8.5 9.8h7M8.5 14.2h7"/>',
    'expand': '<circle cx="12" cy="12" r="2.8"/><path d="M12 9.2V3M12 14.8V21M9.2 12H3M14.4 10.6l5.4-3.1M14.4 13.4l5.4 3.1"/>',
    'fc': '<circle cx="10" cy="13.5" r="6"/><circle cx="18.5" cy="5.5" r="3.4"/><path d="M17 5.5h3"/>',
    'tetra': '<path d="M12 3 3.5 18.5h17z"/><path d="M12 3v10.5M3.5 18.5 12 13.5l8.5 5"/>',
    'octa': '<circle cx="12" cy="12" r="2.4"/><path d="M12 9.6V3M12 14.4V21M9.6 12H3M14.4 12H21M10.3 10.3 6.2 6.2M13.7 13.7l4.1 4.1"/>',
    'pct': '<path d="M18.5 5.5l-13 13"/><circle cx="7" cy="7" r="2.6"/><circle cx="17" cy="17" r="2.6"/>',
    'ratio': f'<path d="M5 12h14"/><circle cx="12" cy="6.5" r="1.7"{DOT}<circle cx="12" cy="17.5" r="1.7"{DOT}',
    'flask': '<path d="M9.5 3h5M10.5 3v6.2L5 19.4c-.4.8.1 1.6 1 1.6h12c.9 0 1.4-.8 1-1.6L13.5 9.2V3"/><path d="M7.4 15h9.2"/>',
    'drop': '<path d="M12 3.5c3.6 4.5 6 7.8 6 10.8a6 6 0 0 1-12 0c0-3 2.4-6.3 6-10.8z"/>',
    'dilute': '<path d="M6 9v10a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V9"/><path d="M6 15h12"/><path d="M12 2.5c1.3 1.6 2.1 2.8 2.1 3.8a2.1 2.1 0 0 1-4.2 0c0-1 .8-2.2 2.1-3.8z"/>',
}
t = once(t, "  watch: '<svg", ''.join(f"  {k}: '{SVG}{v}</svg>',\n" for k, v in ICONS.items()) + "  watch: '<svg")

OUT.write_text(t, encoding='utf-8', newline='\n')
print(f'wrote {OUT.name} ({len(t.encode("utf-8")):,} bytes)')
r = subprocess.run(['node', str(HERE / 'contract.mjs'), str(OUT)], capture_output=True, text=True, encoding='utf-8')
print(r.stdout.strip() or r.stderr.strip())
sys.exit(r.returncode)
