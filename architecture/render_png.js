const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [svgPath, pngPath] = process.argv.slice(2);
  const svg = fs.readFileSync(svgPath, 'utf8');
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1680, height: 1070 }, deviceScaleFactor: 2 });
  await page.setContent(`<html><body style="margin:0">${svg}</body></html>`);
  await page.evaluate(() => document.fonts.ready);
  await page.locator('svg').screenshot({ path: pngPath });
  await browser.close();
})();
