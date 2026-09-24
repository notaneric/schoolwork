"""Assert every Resources file link in index.html resolves on disk.

S156 added four SCI 2900 Resource entries whose files were never extracted from
the D2L zip, so they were dead links to the very handouts Eric needed. Run this
after any edit to a COURSE_FILES block.

The bases are written for the desktop (B:). On any other machine, rewrite the
prefix rather than editing index.html:
  --remap "B:/School/CSU/Fall Semester 2026=C:/Eric/School/CSU Stuff/Fall Semester 2026"
"""
import io, re, os, sys

REMAP = []
for _i, _a in enumerate(sys.argv):
    if _a == '--remap' and _i + 1 < len(sys.argv):
        _o, _, _n = sys.argv[_i + 1].partition('=')
        REMAP.append((_o, _n))

BS = chr(92)
s = io.open('index.html', encoding='utf-8').read()

blocks = [(m.start(), m.group(1)) for m in re.finditer(r"base:\s*'([^']+)'", s)]
if not blocks:
    sys.exit('no COURSE_FILES base found - did the structure change?')
ends = [b[0] for b in blocks[1:]] + [len(s)]

pat = re.compile("file:\\s*'((?:[^'" + BS + BS + "]|" + BS + BS + ".)*)'")
total = missing = 0
for (start, base), end in zip(blocks, ends):
    seg = s[start:end]
    for fm in pat.finditer(seg):
        f = fm.group(1).encode().decode('unicode_escape')
        total += 1
        b = base
        for o, n in REMAP:
            if b.startswith(o):
                b = n + b[len(o):]
        if not os.path.isfile(os.path.join(b, f)):
            missing += 1
            print('MISSING  [%s]  %s' % (base.rstrip('/').split('/')[-1], f))

print('\n%d file links checked, %d missing' % (total, missing))
sys.exit(1 if missing else 0)
