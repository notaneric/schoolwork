"""Assert every Resources file link in index.html resolves on disk.

S156 added four SCI 2900 Resource entries whose files were never extracted from
the D2L zip, so they were dead links to the very handouts Eric needed. Run this
after any edit to a COURSE_FILES block.
"""
import io, re, os, sys

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
        if not os.path.isfile(os.path.join(base, f)):
            missing += 1
            print('MISSING  [%s]  %s' % (base.rstrip('/').split('/')[-1], f))

print('\n%d file links checked, %d missing' % (total, missing))
sys.exit(1 if missing else 0)
