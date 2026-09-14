"""Pass-2 states: full home, terms tab, videos, flashcard back, round-done close, a chapter-filtered home."""
import sys, pathlib
from playwright.sync_api import sync_playwright
from PIL import Image, ImageDraw

sys.stdout.reconfigure(encoding="utf-8")
HTML = pathlib.Path(__file__).resolve().parent.parent / "chem1211-exam1-v2.html"
OUT = pathlib.Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=1)
    pg.goto(HTML.as_uri()); pg.wait_for_timeout(500)
    def home(): pg.evaluate("SES.closed=true; goHome()"); pg.wait_for_timeout(150)

    pg.evaluate("FCH='all'"); home(); pg.evaluate("setTab('study')"); pg.wait_for_timeout(300)
    pg.screenshot(path=str(OUT / "x-home-full.png"), full_page=True)
    pg.evaluate("FCH='mole'"); home(); pg.evaluate("setTab('terms')"); pg.fill("#term-filter", "mol"); pg.wait_for_timeout(300)
    pg.screenshot(path=str(OUT / "x-terms-filtered.png"), full_page=True)
    pg.evaluate("FCH='all'"); home(); pg.evaluate("enter('videos')"); pg.wait_for_timeout(300)
    pg.screenshot(path=str(OUT / "x-videos.png"), full_page=True)
    home(); pg.evaluate("FCH='da'; enter('flash'); fcNav(1); fcFlip()"); pg.wait_for_timeout(700)
    pg.screenshot(path=str(OUT / "x-flash-back.png"))
    pg.evaluate("FCH='sf'"); home(); pg.evaluate("enter('learn')"); pg.wait_for_timeout(200)
    n = pg.evaluate("lnQ.length")
    for i in range(n):
        pg.fill("#learn-input", "x"); pg.evaluate("setConf('guess'); revealOptions()"); pg.wait_for_timeout(60)
        a = pg.evaluate("lnQ[lnPos].q.a")
        pick = a if i % 3 else pg.evaluate("lnQ[lnPos].perm.find(i=>i!==%d)" % a)
        pg.evaluate("learnPick(%d)" % pick); pg.wait_for_timeout(60); pg.evaluate("learnNext()"); pg.wait_for_timeout(80)
    pg.wait_for_timeout(900)
    pg.screenshot(path=str(OUT / "x-round-done.png"))
    b.close()

names = ["x-home-full", "x-terms-filtered", "x-videos", "x-flash-back", "x-round-done"]
cw, ch = 520, 720
ims = []
for n in names:
    im = Image.open(OUT / f"{n}.png").convert("RGB")
    im = im.crop((0, 0, im.width, min(im.height, ch * im.width // cw)))
    im.thumbnail((cw, ch)); ims.append((n, im))
S = Image.new("RGB", (len(ims) * (cw + 8) + 8, ch + 30), (120, 120, 120))
d = ImageDraw.Draw(S)
for i, (n, im) in enumerate(ims):
    x = 8 + i * (cw + 8); d.text((x + 2, 4), n, fill=(255, 255, 255)); S.paste(im, (x, 22))
S.save(OUT / "sheet-x.png"); print("sheet", S.size)
