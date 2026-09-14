# CHEM 1211 Exam 1 Study Set: redesign spec (S137, 2026-09-10)

Eric's decisions (AskUserQuestion, 2026-09-10 ~21:40): **everything tonight**, **warm paper + one
confident accent**, **glossary behind a Key terms tab**. Exam: Fri 2026-09-11 10:00, so the build
must be verified and redeployed the same night.

Audit snapshot: `C:\Claude Code\Boris\.impeccable\critique\2026-09-10T21-39-06Z__chem1211-unit1-study-html.md`
(30/40, 0 P0, 4 P1). Read it first; this spec is the fix list for it.

## Files

| What | Path |
|---|---|
| Deployed (3 sha256-identical copies) | `B:\School\CSU\Fall Semester 2026\CHEM 1211\chem1211-unit1-study.html`, `C:\Claude Code\Projects\Schoolwork\fall2026\chem1211-unit1-study.html`, `C:\Claude Code\Projects\Schoolwork\output\chem1211-unit1-study.html` |
| Pristine pre-S137 backup (51 Q, old design) | `...CHEM 1211\chem1211-unit1-study.html.bak-S137` |
| Verification tooling (copied from the S137 scratchpad) | `C:\Claude Code\Projects\Schoolwork\fall2026\tools\` (`verify_chem.py` 73 checks, `interact2.py` real click-through, `deploy_chem.py`, `shots.py`). Each has a path constant at the top; repoint `HTML`/`SRC` to the working file before running. |
| Engine + design contract | `C:\Claude Code\Boris\deliverables\econ1101-exam3-study\STUDY-SET-SPEC.md` |

Work on a COPY (e.g. `chem1211-exam1-v2.html`), never edit the deployed file in place. Deploy only after the
whole verification contract below passes.

## Hard constraints (do not touch)

- The engine and its data: `Q` (118), `GLOSSARY` (94), `CHAPTERS` (15), the mastery mechanic (2 correct incl. 1
  produced), interleaving, confidence capture, honest progress. **Never re-gamify**: no points, streaks, badges.
- `SHORT` stays derived: `const SHORT = Object.fromEntries(CHAPTERS.map(c=>[c.id,c.short]));`
- All copy in the produce nudge and feedback stays; only its container changes.
- The 3D raised button is the signature. Keep the mechanic (solid + bottom shadow, press = translateY); recolour it.
- Single offline file, no external requests, works over `file://` and in Opera GX.

## Direction: warm paper, one confident accent (product register)

Scene: Eric, 11pm, desk lamp, 27-inch monitor, reading formulas with sub- and superscripts. Paper, not void.

**Tokens (OKLCH-derived, warm hue ~70-80; never #000/#fff):**

| Token | Value | Use |
|---|---|---|
| `--canvas` | `#F7F6F2` | page |
| `--surface` | `#FDFCF9` | cards, inputs |
| `--surface-2` | `#F1EFE9` | secondary panels, chips at rest |
| `--ink` | `#1F1E1B` | headings, answers |
| `--body` | `#3D3B36` | body text |
| `--muted` | `#6A675F` | captions (5.4:1 on surface; the old `#7E88A3` was 3.5:1) |
| `--line` | `#E5E1D8` / strong `#D3CEC3` | hairlines |
| `--accent` | `#3F46DF`, pressed `#2B30B4`, soft `#EEEFFC` | primary action, current pile, selection ONLY |
| `--success` | text `#1E6F45`, fill `#E5F3EA` | mastered, correct |
| `--warn` | text `#7F5300`, fill `#FBEFD3` | still learning (amber TEXT on tint, never white-on-amber) |
| `--danger` | text `#A1301F`, fill `#FBE9E4` | wrong pick |
| shadows | `0 1px 2px rgba(31,30,27,.06)`, raised `0 6px 16px rgba(31,30,27,.10)` | warm-tinted, never neutral black |
| radii | 8 buttons, 12 cards, 16 sheets; 4px base grid | |

**Type:** one family, `Inter, "Segoe UI", system-ui, sans-serif` (Inter via system if present; no webfont fetch).
Scale 48 / 32 / 24 / 18 / 16 / 14 / 13 (1.25 steps). Headings 700 with `-0.02em` tracking. Body 16. Nothing
below 13px. Kill the 22-size scatter: every size maps to the scale.

**Layout:** the card owns the viewport. Learn/Recall cards `max-width: 720px`, generous top rhythm, vary
spacing (the old build used the same padding everywhere). No nested cards anywhere.

## The seven changes (map to audit P1/P2)

1. **Hierarchy of moment (P1).** Apply the scale; the question is 24px, options 16px, kicker 13px caps with
   tracking. Card sits in the upper third with intent, not centred in a void.
2. **Visible progress (P1).** Replace the empty hairline with three **piles** in the Learn header: Remaining /
   Still learning / Mastered, each a small stacked-card glyph with its count in 24px; the strip fills from the
   first answer (accent -> warn -> success). Home KPI "recalled from cold" becomes the hero number (48px).
3. **Accessibility (P1).** Every body-size text >= 4.5:1 (use the tokens above). Add `:focus-visible` rings
   (2px accent, 2px offset); remove both `outline:none`. Add `@media (prefers-reduced-motion: reduce)` that
   disables shake/pop/rise/confetti. Chips >= 44px tall on touch.
4. **Feedback state (P1).** ONE surface. On grade: the correct option gets the only saturated treatment
   (success fill + check glyph, 250ms checkmark draw, ease-out-quart); a wrong pick gets a hairline in danger
   and a strike, quieter than the truth. Explanation below in body type; the math block is a monospace
   paragraph on `--surface-2`, not a boxed card; "You answered" and "Review: Handout 5, Q5" are inline lines.
5. **Home as launcher (P2).** Hero number + one sentence; modes as a differentiated LIST, not an identical grid:
   Recall and Learn are large primary rows, Mixed Exam and Videos secondary, Preview/Match a small warm-up
   row. Chapter chips stay but condensed (two rows max on desktop). **Key terms move behind a tab**
   (`Key terms (94)`), with a filter box.
6. **Icons + palette (P2).** Replace the six emoji with one inline-SVG line-icon set (1.5px stroke, same
   grid). Apply the warm tokens everywhere; recolour the raised button to `--accent`.
7. **Session close (P2).** When a Learn/Recall round ends (or on "<- Set" after >= 5 answers), show a summary
   card before home: "Recalled N from cold", "Still learning: M", "Weakest chapter: X (start here next)". One
   button back. This is the only place delight is spent (a single checkmark/pile animation, < 1s).

Motion everywhere else: 150-250ms, `cubic-bezier(.25,1,.5,1)`, state changes only.

## Verification contract (all must pass before deploy)

1. `node --check` on the extracted `<script>`.
2. `tools/verify_chem.py` (repointed): 73/73, Q=118, GLOSSARY=94, CHAPTERS=15, no sparse holes, every
   chapter label resolves, no literal "undefined", 0 console errors, no h-scroll at 390px.
3. `tools/interact2.py`: Learn produce -> reveal -> grade renders feedback; Match 12 tiles via `enter('match')`.
4. New checks to add: every text node < 18.66px has contrast >= 4.5:1 against its rendered background;
   `:focus-visible` rule exists and `outline:none` count is 0; `prefers-reduced-motion` rule exists; no element
   has emoji-only text in a `.mode-ico`; no `.card` inside a `.card`; interactive targets >= 44px at 390px;
   home `scrollHeight` < 2 viewports with the terms tab closed.
5. Screenshots at 1280 and 390 of: home, learn produce, learn graded (correct AND wrong), recall, match,
   exam, session-close. Look at them. Minimum two build->screenshot->fix passes.
6. Deploy with `tools/deploy_chem.py` (repointed) to the 3 locations; re-read and sha256-match.
7. Open in **Opera GX only** (`C:\Users\notan\AppData\Local\Programs\Opera GX\opera.exe` + `as_uri()`),
   once, then stop. Never Invoke-Item (`.html` is bound to Internet Explorer on this machine).

## Known content notes (do not "fix" these)

Dr. Meyers' Chapter 2 key is internally inconsistent in three places (Cu-63, Ar-36, H3PO4 molar mass).
The questions deliberately key HIS printed values and flag the discrepancy in the explanation. Leave them.
