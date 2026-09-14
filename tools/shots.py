"""Capture every screen state of the current study set for the design audit,
plus measured facts the eye can't score: contrast pairs, touch targets, fonts."""
import sys, pathlib, json
from playwright.sync_api import sync_playwright

sys.stdout.reconfigure(encoding="utf-8")
HTML = pathlib.Path(r"B:/School/CSU/Fall Semester 2026/CHEM 1211/chem1211-unit1-study.html")
OUT = pathlib.Path(r"C:/Users/notan/AppData/Local/Temp/claude/c--Claude-Code-Boris/8ba021ce-2805-4aac-bcc5-02200582055d/scratchpad/audit")
OUT.mkdir(exist_ok=True)

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1280, "height": 900}, device_scale_factor=1)
    pg.goto(HTML.as_uri()); pg.wait_for_timeout(600)

    def home():
        pg.evaluate("if(typeof goHome==='function') goHome(); else show('home')"); pg.wait_for_timeout(200)

    def shot(name, full=False):
        pg.screenshot(path=str(OUT / f"{name}.png"), full_page=full)
        print("  shot", name)

    shot("01-home", full=True)

    # Learn: produce step, then revealed, then graded
    pg.evaluate("FCH='iso'"); home(); pg.evaluate("enter('learn')"); pg.wait_for_timeout(400)
    shot("02-learn-produce")
    inp = pg.query_selector("#learn-input")
    if inp:
        inp.fill("gains electrons"); inp.press("Enter"); pg.wait_for_timeout(400)
    shot("03-learn-revealed")
    btns = [x for x in pg.query_selector_all("#learn-opts button") if x.is_visible()]
    if btns:
        btns[0].click(); pg.wait_for_timeout(500)
    shot("04-learn-graded")

    pg.evaluate("FCH='elem'"); home(); pg.evaluate("enter('recall')"); pg.wait_for_timeout(400)
    shot("05-recall")
    home(); pg.evaluate("enter('match')"); pg.wait_for_timeout(500)
    shot("06-match")
    pg.evaluate("FCH='all'"); home(); pg.evaluate("enter('exam')"); pg.wait_for_timeout(500)
    shot("07-exam")
    home(); pg.evaluate("enter('flash')"); pg.wait_for_timeout(400)
    shot("08-preview")
    home(); pg.evaluate("enter('videos')"); pg.wait_for_timeout(400)
    shot("09-videos")

    # measured facts
    home()
    facts = pg.evaluate("""(() => {
      const cs = el => getComputedStyle(el);
      const body = cs(document.body);
      const fonts = new Set(); const sizes = {};
      document.querySelectorAll('body *').forEach(e => {
        const s = cs(e); if (s.display==='none') return;
        fonts.add(s.fontFamily.split(',')[0].trim());
        sizes[s.fontSize] = (sizes[s.fontSize]||0)+1;
      });
      const small = [...document.querySelectorAll('button,a,[onclick]')].filter(e => {
        const r = e.getBoundingClientRect(); return r.width>0 && (r.height<44 || r.width<44);
      }).map(e => ({t:(e.innerText||'').trim().slice(0,18), w:Math.round(e.getBoundingClientRect().width), h:Math.round(e.getBoundingClientRect().height)}));
      const focusVisible = [...document.styleSheets].some(ss => { try { return [...ss.cssRules].some(r => /:focus-visible/.test(r.cssText)); } catch(e){ return false; } });
      const anims = [...document.styleSheets].flatMap(ss => { try { return [...ss.cssRules].filter(r => r.type===7).map(r=>r.name); } catch(e){ return []; } });
      const transitions = new Set(); document.querySelectorAll('body *').forEach(e=>{ const t=cs(e).transitionProperty; if(t && t!=='all' && t!=='none') transitions.add(t); });
      const dark = [...document.styleSheets].some(ss => { try { return [...ss.cssRules].some(r => /prefers-color-scheme/.test(r.cssText)); } catch(e){ return false; } });
      const h = [...document.querySelectorAll('h1,h2,h3,h4')].map(e=>e.tagName+':'+cs(e).fontSize+'/'+cs(e).fontWeight);
      return { bodyBg: body.backgroundColor, bodyColor: body.color, fonts:[...fonts], sizes, headings:h,
               smallTargets: small.slice(0,14), smallCount: small.length, focusVisible, keyframes:[...new Set(anims)], transitions:[...transitions], darkMode: dark };
    })()""")
    (OUT / "facts.json").write_text(json.dumps(facts, indent=2), encoding="utf-8")
    print(json.dumps(facts, indent=1)[:1800])

    # mobile
    pg.set_viewport_size({"width": 390, "height": 844})
    home(); pg.wait_for_timeout(300); shot("10-mobile-home", full=True)
    pg.evaluate("FCH='mole'"); pg.evaluate("enter('learn')"); pg.wait_for_timeout(400); shot("11-mobile-learn")
    b.close()
print("done ->", OUT)
