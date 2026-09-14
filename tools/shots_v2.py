"""Screenshot every screen state of chem1211-exam1-v2.html at 1280 and 390, then tile them into
contact sheets so the eye pass costs a few images, not twenty."""
import sys, pathlib
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
HTML = pathlib.Path(__file__).resolve().parent.parent / "chem1211-exam1-v2.html"
OUT = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent / "shots"
OUT.mkdir(parents=True, exist_ok=True)

STATES = ["home", "home-terms", "learn-produce", "learn-correct", "learn-wrong", "recall-revealed", "match", "exam", "close"]

with sync_playwright() as p:
    b = p.chromium.launch()
    for W, H, tag in [(1280, 900, "d"), (390, 844, "m")]:
        pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        pg.goto(HTML.as_uri()); pg.wait_for_timeout(500)

        def home():
            pg.evaluate("SES.closed=true; goHome()"); pg.wait_for_timeout(150)

        def learn(stage, wrong=False):
            pg.evaluate("FCH='iso'"); home(); pg.evaluate("enter('learn')"); pg.wait_for_timeout(300)
            if stage == "produce": return
            pg.fill("#learn-input", "gains electrons"); pg.evaluate("setConf('sure'); revealOptions()"); pg.wait_for_timeout(250)
            a = pg.evaluate("lnQ[lnPos].q.a")
            pick = pg.evaluate("lnQ[lnPos].perm.find(i=>i!==%d)" % a) if wrong else a
            pg.evaluate("learnPick(%d)" % pick); pg.wait_for_timeout(500)

        for st in STATES:
            if st == "home": pg.evaluate("FCH='all'"); home(); pg.evaluate("setTab('study')")
            elif st == "home-terms": pg.evaluate("FCH='all'"); home(); pg.evaluate("setTab('terms')")
            elif st == "learn-produce": learn("produce")
            elif st == "learn-correct": learn("graded")
            elif st == "learn-wrong": learn("graded", True)
            elif st == "recall-revealed":
                pg.evaluate("FCH='elem'"); home(); pg.evaluate("enter('recall')"); pg.wait_for_timeout(200)
                pg.fill("#rc-input", "a noble gas"); pg.evaluate("recallReveal()")
            elif st == "match": pg.evaluate("FCH='all'"); home(); pg.evaluate("enter('match')")
            elif st == "exam": pg.evaluate("FCH='all'"); home(); pg.evaluate("enter('exam')")
            elif st == "close":
                pg.evaluate("FCH='elem'"); home(); pg.evaluate("enter('recall')"); pg.wait_for_timeout(200)
                for g in ['got', 'miss', 'got', 'close', 'got', 'miss']:
                    pg.fill("#rc-input", "x"); pg.evaluate("recallReveal()"); pg.wait_for_timeout(40); pg.evaluate("recallGrade(%r)" % g); pg.wait_for_timeout(40)
                pg.evaluate("goHome()")
            pg.wait_for_timeout(900)
            full = st in ("home", "home-terms")
            pg.screenshot(path=str(OUT / f"{tag}-{st}.png"), full_page=full)
            print("  shot", tag, st)
        pg.close()
    b.close()

# ---- contact sheets ----
try:
    from PIL import Image
except ImportError:
    print("PIL missing, no contact sheets"); sys.exit(0)

def sheet(names, tag, cols, cell_w, cell_h, out):
    ims = []
    for n in names:
        im = Image.open(OUT / f"{tag}-{n}.png").convert("RGB")
        im = im.crop((0, 0, im.width, min(im.height, cell_h * im.width // cell_w)))
        im.thumbnail((cell_w, cell_h))
        ims.append((n, im))
    rows = (len(ims) + cols - 1) // cols
    S = Image.new("RGB", (cols * cell_w + (cols + 1) * 8, rows * (cell_h + 22) + 8), (120, 120, 120))
    from PIL import ImageDraw
    d = ImageDraw.Draw(S)
    for i, (n, im) in enumerate(ims):
        x = 8 + (i % cols) * (cell_w + 8); y = 8 + (i // cols) * (cell_h + 22)
        d.text((x + 2, y + 2), n, fill=(255, 255, 255))
        S.paste(im, (x, y + 18))
    S.save(OUT / out)
    print("  sheet", out, S.size)

sheet(["home", "learn-produce", "learn-correct", "learn-wrong"], "d", 2, 640, 450, "sheet-d1.png")
sheet(["recall-revealed", "match", "exam", "close"], "d", 2, 640, 450, "sheet-d2.png")
sheet(["home", "learn-produce", "learn-wrong", "recall-revealed", "match", "close"], "m", 6, 300, 650, "sheet-m.png")
print("done ->", OUT)
