"""Build chem1211-final-game.html: the cumulative CHEM 1211 final exam study game.

Usage: python tools/final/build_final.py
The engine is the shipped Exam 3 game (chem1211-exam3-game.html), which already carries every
engine edit (open levels, units on the path, caret superscripts, the file:// video fallback).
Its 16 levels, lessons, questions and videos move to levels 17-32 unchanged except for the
"not on Exam 3" notes. Levels 1-16 (Ch 1-4.3) and 33-37 (Ch 7) come from tools/final/parts/.
Every edit is an exact-string substitution that must match once, and the data contract
(contract.mjs) runs last and fails the build on any defect.
"""
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SRC = ROOT / 'chem1211-exam3-game.html'
OUT = ROOT / 'chem1211-final-game.html'
PARTS = HERE / 'parts'
SHIFT = 16
SVG = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">'
DOT = ' fill="currentColor" stroke="none"/>'


def once(s, old, new):
    n = s.count(old)
    assert n == 1, f'expected 1 match, found {n}: {old[:80]!r}'
    return s.replace(old, new)


def block(s, start, end='\n};'):
    a = s.index(start)
    return s[a:s.index(end, a) + len(end)]


t = SRC.read_text(encoding='utf-8')

# 1. split the Exam 3 page into lessons, data and engine
la, lb = t.index('<template id="lesson-1">'), t.index('<script>')
da, db = t.index('// YouTube oEmbed-verified'), t.index('const ICON = {')
e3_lessons, e3_data = t[la:lb], t[da:db]

# Exam 3 notes that name Exam 3; the final excludes the same subsection ("Derivation of Molecular Formula")
e3_lessons = once(e3_lessons, 'Finding a molecular formula from a molar mass is not on Exam 3.',
                  'Finding a molecular formula from a molar mass is not on the final.')
e3_data = once(e3_data, 'is not on Exam 3.', 'is not on the final.')
assert 'Exam 3' not in e3_lessons + e3_data, 'an Exam 3 reference survived'

# 2. lessons: Exam 3's 1-16 become 17-32
old = re.findall(r'<template id="lesson-(\d+)">\n(.*?)\n</template>', e3_lessons, re.S)
assert [int(n) for n, _ in old] == list(range(1, 17)), [n for n, _ in old]
moved = {int(n) + SHIFT: body for n, body in old}


def part_lessons(name, want):
    src = (PARTS / f'{name}-lessons.html').read_text(encoding='utf-8')
    got = {int(n): body for n, body in re.findall(r'<template id="lesson-(\d+)">\n?(.*?)\n?</template>', src, re.S)}
    assert sorted(got) == want, (name, sorted(got))
    return got


lessons = {**part_lessons('u12', list(range(1, 9))), **part_lessons('u34', list(range(9, 17))),
           **moved, **part_lessons('u8', list(range(33, 38)))}
assert sorted(lessons) == list(range(1, 38)), sorted(lessons)
# chip rows holding words, not symbols, overflowed a 320px screen in three columns
for n, cls in ((7, 'names'), (9, 'words')):
    assert lessons[n].count('<div class="els">') == 1, n
    lessons[n] = lessons[n].replace('<div class="els">', f'<div class="els {cls}">')
lessons = {n: re.sub(r'\bZeff\b', 'Z<sub>eff</sub>', body) for n, body in lessons.items()}
lessons_html = ''.join(f'<template id="lesson-{n}">\n{lessons[n].strip(chr(10))}\n</template>\n\n' for n in range(1, 38))

# 3. data: videos, the VSEPR table, levels and questions
vid = block(e3_data, 'const VIDEOS = {')
vid_lines = re.findall(r'^  (\d+): (\{.*\}),$', vid, re.M)
# Exam 3 level 2 (polyatomic ions, now 18) never had a video
assert [int(k) for k, _ in vid_lines] == [1] + list(range(3, 17)), 'Exam 3 videos'
videos = {int(k) + SHIFT: v for k, v in vid_lines}
for name, want in (('u12', range(1, 9)), ('u34', range(9, 17)), ('u8', range(33, 38))):
    got = {int(k): v.rstrip(',') for k, v in re.findall(r'^\s*(\d+): (\{.*\}),?\s*$', (PARTS / f'{name}-videos.js').read_text(encoding='utf-8'), re.M)}
    assert sorted(got) == list(want), (name, sorted(got))
    videos.update(got)
assert sorted(videos) == [n for n in range(1, 38) if n != 18], sorted(videos)

table = block(e3_data, '// [SN, shape', '];')

e3_levels = re.findall(r"^  \{ n: (\d+), (.*) \},$", block(e3_data, 'const LEVELS = [', '\n];'), re.M)
assert len(e3_levels) == 16
UNIT = {'Unit 1': 'Unit 5', 'Unit 2': 'Unit 6', 'Unit 3': 'Unit 7'}
moved_levels = [f"  {{ n: {int(n) + SHIFT}, {re.sub(r'Unit [123]', lambda m: UNIT[m.group(0)], rest)} }},"
                for n, rest in e3_levels]

NEW_LEVELS = {
    1: "name: 'Sig figs and scientific notation', icon: 'sig', unit: 'Unit 1', uname: 'Measurements', sub: 'Ch 1, Handouts 2 to 4'",
    2: "name: 'Prefixes and unit conversions', icon: 'ruler'",
    3: "name: 'Density and temperature', icon: 'cube'",
    4: "name: 'Classifying matter and changes', icon: 'states'",
    5: "name: 'Atoms, ions and nuclear symbols', icon: 'atom', unit: 'Unit 2', uname: 'Atoms and the mole', sub: 'Ch 2 and 6.1, Handouts 5 and 6'",
    6: "name: 'Isotopes and average atomic mass', icon: 'iso'",
    7: "name: 'Elements, compounds and the periodic table', icon: 'grid'",
    8: "name: 'Moles, molar mass and Avogadro', icon: 'pile'",
    9: "name: 'Light: wavelength, frequency, energy', icon: 'wave', unit: 'Unit 3', uname: 'Light and electrons', sub: 'Ch 3, Handouts 7 to 11'",
    10: "name: 'Emission spectra, Bohr and Rydberg', icon: 'lines'",
    11: "name: 'Quantum numbers and orbitals', icon: 'orbital'",
    12: "name: 'Electron configurations', icon: 'boxes'",
    13: "name: 'Periodic trends', icon: 'trend'",
    14: "name: 'Ionic and covalent bonds', icon: 'swap', unit: 'Unit 4', uname: 'Bonds and names', sub: 'Ch 4.1 to 4.3, Handout 12'",
    15: "name: 'Naming ionic compounds', icon: 'tag'",
    16: "name: 'Naming molecular compounds', icon: 'prefix'",
    33: "name: 'Balancing equations', icon: 'scale', unit: 'Unit 8', uname: 'Reactions', sub: 'Ch 7, Handouts 18 and 19'",
    34: "name: 'Mole ratios and stoichiometry', icon: 'chain'",
    35: "name: 'Limiting and excess reactants', icon: 'funnel'",
    36: "name: 'Theoretical and percent yield', icon: 'target'",
    37: "name: 'Solution stoichiometry', icon: 'buret'",
}
lv_lines = ([f'  {{ n: {n}, {NEW_LEVELS[n]} }},' for n in range(1, 17)] + moved_levels
            + [f'  {{ n: {n}, {NEW_LEVELS[n]} }},' for n in range(33, 38)])
levels = ('// unit: a header drawn above the level on the path. Every level is open.\nconst LEVELS = [\n'
          + '\n'.join(lv_lines) + '\n];')

qa = e3_data.index('const Q = [')
e3_q = e3_data[qa:e3_data.index('\n];', qa)]
e3_qlines = [ln for ln in e3_q.split('\n') if re.match(r'\s*\{ lv: \d+,', ln)]
e3_qlines = [re.sub(r'\{ lv: (\d+),', lambda m: '{ lv: ' + str(int(m.group(1)) + SHIFT) + ',', ln, count=1) for ln in e3_qlines]


def part_q(name, lo, hi):
    lines = [ln.rstrip() for ln in (PARTS / f'{name}-q.js').read_text(encoding='utf-8').split('\n')]
    qs = [ln for ln in lines if re.match(r'\s*\{ lv: \d+,', ln)]
    stray = [ln for ln in lines if ln.strip() and not ln.strip().startswith('//') and ln not in qs]
    assert not stray, (name, 'lines that are not one-line questions', stray[:3])
    bad = [ln[:60] for ln in qs if not lo <= int(re.search(r'lv: (\d+)', ln).group(1)) <= hi]
    assert not bad, (name, 'question outside its levels', bad[:3])
    return ['  ' + ln.strip() for ln in qs]


def group(lines):
    out, prev = [], None
    for ln in lines:
        lv = int(re.search(r'lv: (\d+)', ln).group(1))
        if prev is not None and lv != prev:
            out.append('')
        out.append(ln if ln.endswith(',') else ln + ',')
        prev = lv
    return out


q_lines = group(part_q('u12', 1, 8) + part_q('u34', 9, 16) + [ln.rstrip() for ln in e3_qlines] + part_q('u8', 33, 37))

data = ('// YouTube oEmbed-verified (levels 17-32 on 2026-11-16, the rest on 2026-11-25): { id, title, ch, dur, note?, alt? }\n'
        'const VIDEOS = {\n' + '\n'.join(f'  {k}: {videos[k]},' for k in sorted(videos)) + '\n};\n\n'
        + table + '\n\n' + levels + '\n\n'
        '// mc: a[0] is correct (options shuffle on screen). type: re tests the normalized answer.\n'
        '// boss: true keeps a question out of its level and in the boss pool only.\n'
        '// Charges and exponents use ^ (SO4^2-, 10^6); the page renders them as superscripts.\n'
        'const Q = [\n' + '\n'.join(q_lines) + '\n];\n\n')

t = t[:la] + lessons_html + t[lb:da] + data + t[db:]

# 4. engine edits
BOSS_N, BOSS_MIN = 20, 40
E = [
    ('<title>CHEM 1211 Exam 3</title>', '<title>CHEM 1211 Final Exam</title>'),
    ("const KEY = 'chem1211e3_game_v1';\nconst BOSS_N = 10, BOSS_SECS = 300;",
     f"const KEY = 'chem1211fin_game_v1';\n// the boss round runs at the final's pace: about 2 minutes a question\nconst BOSS_N = {BOSS_N}, BOSS_SECS = {BOSS_MIN * 60};"),
    ('<h1>Exam 3 study game</h1><p class="when">Wed Nov 18, 10:00, LDSC 210</p><p class="hint">Every level is open. Jump to any topic, starting with the one you know least.</p>',
     '<h1>Final exam study game</h1><p class="when">Mon Dec 7, 10:15 to 12:15, LDSC 210</p><p class="hint">Cumulative and all multiple choice. Every level is open, so start with the unit you know least. The boss round runs at exam pace.</p>'),
    ("' + BOSS_N + ' questions, 5 minutes</div>'", "' + BOSS_N + ' questions, ' + BOSS_SECS / 60 + ' minutes</div>'"),
    ("<h1 class=\"lvl\">' + BOSS_N + ' questions, 5 minutes</h1>", "<h1 class=\"lvl\">' + BOSS_N + ' questions, ' + BOSS_SECS / 60 + ' minutes</h1>"),
    # Ch 7 formulas: a digit after a closing parenthesis is a subscript too, as in Pb(NO3)2 and Ca(OH)2,
    # and a typed "->" shows as one arrow that cannot break across lines on a phone
    (r"acceptNode: n => /[A-Z][a-z]?\d|\^/.test(n.nodeValue)",
     r"acceptNode: n => /[A-Z][a-z]?\d|\^|\)\d|->|\w - [\w(]/.test(n.nodeValue)"),
    ('</style>', """  .els.words { grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); }
  .els.words .el b { font-size: 18px; }
  .els.names { grid-template-columns: repeat(auto-fill, minmax(84px, 1fr)); }
  .els.names .el span { font-size: 12px; }
  sub, sup { line-height: 0; }
  .stop .label { text-wrap: balance; }
</style>"""),
    # no line break inside 6.626 x 10^-34, between a coefficient and its formula (3 H2), or a number,
    # its unit and the formula (70.4 g NH3); a spaced minus becomes a real minus that cannot end a line
    (r"t.innerHTML = esc(n.nodeValue).replace(",
     r"t.innerHTML = esc(n.nodeValue).replace(/(\d) ([x×]) 10\^/g, '$1\u00a0$2\u00a010^').replace(/(^|[\s(+;])(\d+) (?=\(?[A-Z])/g, '$1$2\u00a0').replace(/(\d) (g|mg|kg|mol|mL|L|M|J|nm|cm|m) (?=\(?[A-Z])/g, '$1\u00a0$2\u00a0').replace(/(\w) - (?=[\w(])/g, '$1 −\u00a0').replace("),
    (r".replace(/([A-Z][a-z]?)(\d+)/g, '$1<sub>$2</sub>');",
     r".replace(/<sup>([^<]*?)-/g, '<sup>$1−').replace(/([A-Z][a-z]?)(\d+)/g, '$1<sub>$2</sub>').replace(/\)(\d+)/g, ')<sub>$1</sub>').replace(/-&gt;/g, '→');"),
]
for o, n in E:
    t = once(t, o, n)
t = once(t, "const norm = s => String(s).trim().toLowerCase().replace(/[\\s\\-‐-―−_]/g, '').replace(/\\.$/, '');", "// a minus sign that starts a number (-233, 10^-23) is kept, so a sign or exponent slip is marked wrong;\n// a hyphen inside a word or name (carbon-12, Cu-63) is still dropped\nconst norm = s => String(s).trim().toLowerCase().replace(/(^|[^a-z0-9])[-−](?=\\d)/g, '$1\\u0001').replace(/[\\s\\-‐-―−_]/g, '').replace(/\\u0001/g, '-').replace(/\\.$/, '');")
m = re.findall(r'<small>/(\d+)</small>', t)
assert m == ['48'], m
t = once(t, '<small>/48</small>', f'<small>/{37 * 3}</small>')

ICONS = {
    'sig': f'<circle cx="6.5" cy="12" r="3.6"/><circle cx="17.5" cy="12" r="3.6"/><circle cx="12" cy="16.4" r="1.2"{DOT}',
    'ruler': '<rect x="2.5" y="8" width="19" height="8" rx="1.5"/><path d="M6.5 8v3M10.5 8v4.5M14.5 8v3M18.5 8v4.5"/>',
    'cube': '<path d="M12 3 4 7v10l8 4 8-4V7z"/><path d="M4 7l8 4 8-4M12 11v10"/>',
    'states': '<rect x="3" y="12.5" width="7.5" height="7.5" rx="1"/><path d="M17 11c2.2 2.8 3.5 4.6 3.5 6a3.5 3.5 0 0 1-7 0c0-1.4 1.3-3.2 3.5-6z"/><path d="M5 5h.01M9 3.5h.01M13 5.5h.01"/>',
    'atom': f'<circle cx="12" cy="12" r="1.8"{DOT}<ellipse cx="12" cy="12" rx="9.5" ry="3.8"/><ellipse cx="12" cy="12" rx="9.5" ry="3.8" transform="rotate(60 12 12)"/><ellipse cx="12" cy="12" rx="9.5" ry="3.8" transform="rotate(120 12 12)"/>',
    'iso': '<path d="M3.5 20.5h17M7.5 20.5V9M12 20.5V4.5M16.5 20.5v-6"/>',
    'grid': '<rect x="3" y="4" width="4" height="4"/><rect x="17" y="4" width="4" height="4"/><rect x="3" y="10" width="18" height="10" rx="1"/><path d="M9 10v10M15 10v10M3 15h18"/>',
    'pile': '<circle cx="7.5" cy="16" r="3.4"/><circle cx="16.5" cy="16" r="3.4"/><circle cx="12" cy="8.5" r="3.4"/>',
    'wave': '<path d="M2.5 12c1.6-4.5 3.2-4.5 4.8 0s3.2 4.5 4.8 0 3.2-4.5 4.8 0 3.2 4.5 4.8 0"/>',
    'lines': '<rect x="3" y="5" width="18" height="14" rx="1.5"/><path d="M7.5 5v14M10.5 5v14M16 5v14"/>',
    'orbital': '<ellipse cx="12" cy="7.3" rx="3.4" ry="4.6"/><ellipse cx="12" cy="16.7" rx="3.4" ry="4.6"/>',
    'boxes': '<rect x="2.5" y="8" width="6.3" height="8"/><rect x="8.8" y="8" width="6.3" height="8"/><rect x="15.1" y="8" width="6.3" height="8"/><path d="M5.6 14.5v-5M4.4 10.7l1.2-1.2 1.2 1.2M11.9 14.5v-5M10.7 10.7l1.2-1.2 1.2 1.2"/>',
    'trend': '<path d="M4 20 20 4M20 4h-7M20 4v7"/>',
    'swap': '<circle cx="5.5" cy="12" r="3"/><circle cx="18.5" cy="12" r="3"/><path d="M9.5 9.5h5l-2-2M14.5 14.5h-5l2 2"/>',
    'tag': f'<path d="M3 12V3.5h8.5L21 13l-8 8z"/><circle cx="7.5" cy="8" r="1.4"{DOT}',
    'prefix': '<path d="M4 6h16M4 12h10M4 18h13"/>',
    'scale': '<path d="M12 4v16M7 20h10M5 7h14"/><path d="M5 7 2.5 13h5zM19 7l-2.5 6h5z"/>',
    'chain': '<circle cx="5" cy="12" r="2.6"/><circle cx="19" cy="12" r="2.6"/><path d="M8.2 12h7.6M13 9l2.8 3-2.8 3"/>',
    'funnel': '<path d="M3.5 4h17l-6.5 8v6.5l-4 2V12z"/>',
    'target': f'<circle cx="12" cy="12" r="8.6"/><circle cx="12" cy="12" r="4.6"/><circle cx="12" cy="12" r="1.3"{DOT}',
    'buret': '<path d="M9.5 2.5h5M10.5 2.5v12l1.5 2.6 1.5-2.6v-12M10.5 7h3"/><path d="M6 21.5h12"/>',
}
t = once(t, "  watch: '<svg", ''.join(f"  {k}: '{SVG}{v}</svg>',\n" for k, v in ICONS.items()) + "  watch: '<svg")

OUT.write_text(t, encoding='utf-8', newline='\n')
print(f'wrote {OUT.name} ({len(t.encode("utf-8")):,} bytes)')
r = subprocess.run(['node', str(HERE / 'contract.mjs'), str(OUT)], capture_output=True, text=True, encoding='utf-8')
print(r.stdout.strip() or r.stderr.strip())
sys.exit(r.returncode)
