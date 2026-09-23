const { chromium } = require('playwright');
const NEW = 'file:///' + 'C:/Claude Code/Projects/Schoolwork/fall2026/index.html'.replace(/ /g, '%20');
const out = process.argv[2];
(async () => {
  const browser = await chromium.launch();
  for (const theme of ['dark', 'light']) {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 1400 }, deviceScaleFactor: 1 });
    const p = await ctx.newPage();
    await p.goto(NEW);
    await p.waitForTimeout(600);
    if (theme === 'light') {
      await p.evaluate(() => document.documentElement.setAttribute('data-theme', 'light'));
      await p.waitForTimeout(300);
    }
    await p.screenshot({ path: out + '/dash-' + theme + '.png', fullPage: false });
    await ctx.close();
  }
  await browser.close();
  console.log('shots written');
})();
