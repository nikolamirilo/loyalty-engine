/* Checks a built docs site in a real browser (Playwright + Chromium).

     node <skill>/scripts/check.js <site-dir> [--snap page-id,page-id]

   For every page, at desktop (1280 px) and phone (390 px) width, it reports: script errors, sideways
   scrolling, missing screens, images or other elements that stay pinned while scrolling, and broken
   links between pages. It also checks that checklist ticks survive a reload, that the overlay on a
   screen appears only while a number is hovered, and that search finds the first page. With --snap
   it saves screenshots of those pages in light and dark themes to <site-dir>/dist/snaps/.
   Exit code 1 when anything fails. */
const path = require('path');
const fs = require('fs');

function loadPlaywright() {
  const tries = [process.env.PLAYWRIGHT_MODULE, 'playwright', 'playwright-core', '@playwright/test', '/opt/node-tools/node_modules/playwright'].filter(Boolean);
  for (const t of tries) { try { return require(t); } catch (e) {} }
  console.error('Playwright not found. Install it (npm i -D playwright) or set PLAYWRIGHT_MODULE to its folder.');
  process.exit(2);
}

(async () => {
  const site = path.resolve(process.argv[2] || '.');
  const snapArg = process.argv.indexOf('--snap');
  const snaps = snapArg > 0 ? (process.argv[snapArg + 1] || '').split(',').filter(Boolean) : [];
  const file = path.join(site, 'dist', 'preview.html');
  if (!fs.existsSync(file)) { console.error('Build first: ' + file + ' is missing'); process.exit(2); }
  const url = 'file://' + file;
  const { chromium } = loadPlaywright();
  const exe = fs.existsSync('/opt/pw-browsers/chromium') && !process.env.PLAYWRIGHT_BROWSERS_PATH ? '/opt/pw-browsers/chromium' : undefined;
  let b;
  try { b = await chromium.launch(); } catch (e) { b = await chromium.launch(exe ? { executablePath: exe } : {}); }
  const problems = [];

  for (const w of [1280, 390]) {
    const p = await b.newPage({ viewport: { width: w, height: 860 } });
    const errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    await p.goto(url); await p.waitForTimeout(600);
    const ids = await p.evaluate(() => [...document.querySelectorAll('.page')].map(x => x.id));
    for (const id of ids) {
      await p.evaluate(i => { location.hash = i; }, id); await p.waitForTimeout(120);
      const r = await p.evaluate(() => {
        const pg = document.querySelector('.page.on');
        return {
          overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
          missing: [...pg.querySelectorAll('.note.warn')].filter(n => n.textContent.startsWith('[screen')).map(n => n.textContent),
          sticky: [...pg.querySelectorAll('*')].filter(el => getComputedStyle(el).position === 'sticky').map(el => el.className || el.tagName),
        };
      });
      if (r.overflow > 0) problems.push(`${w}px ${id}: page scrolls sideways by ${r.overflow}px`);
      if (r.missing.length) problems.push(`${w}px ${id}: missing ${r.missing.join(', ')}`);
      if (r.sticky.length) problems.push(`${w}px ${id}: pinned while scrolling: ${r.sticky.join(', ')}`);
    }
    if (errs.length) problems.push(`${w}px script errors: ${[...new Set(errs)].slice(0, 5).join(' | ')}`);
    if (w === 1280) {
      const broken = await p.evaluate(() => [...new Set([...document.querySelectorAll('a[href^="#"]')].map(a => a.getAttribute('href').slice(1)).filter(h => h && !document.getElementById(h)))]);
      if (broken.length) problems.push('links to missing pages or sections: ' + broken.join(', '));
      const dashes = await p.evaluate(() => { const t = document.body.innerText; return { em: (t.match(/—/g) || []).length, en: (t.match(/–/g) || []).length }; });
      if (dashes.em || dashes.en) problems.push(`em dashes ${dashes.em}, en dashes ${dashes.en}: rewrite those sentences`);
      // checklist ticks survive a reload
      const ck = await p.evaluate(() => { const pg = document.querySelector('.page[data-check]'); return pg ? pg.id : null; });
      if (ck) {
        await p.evaluate(i => { localStorage.clear(); location.hash = i; }, ck); await p.reload(); await p.waitForTimeout(500);
        await p.evaluate(i => { location.hash = i; }, ck); await p.waitForTimeout(200);
        const t = (await p.$$(`#${ck} .steps>li .tick`))[0];
        if (t) {
          await t.scrollIntoViewIfNeeded(); await t.click(); await p.waitForTimeout(150);
          await p.reload(); await p.waitForTimeout(600);
          await p.evaluate(i => { location.hash = i; }, ck); await p.waitForTimeout(200);
          const kept = await p.evaluate(i => document.querySelectorAll(`#${i} .steps>li.ticked`).length, ck);
          if (kept !== 1) problems.push(`checklist on ${ck}: a ticked step was not kept after reload`);
        }
      }
      // the overlay shows only while a number is hovered
      const shotPage = await p.evaluate(() => { const f = [...document.querySelectorAll('.page figure.shot:not(.anim)')].find(f => f.querySelector('[data-hz]')); return f ? f.closest('.page').id : null; });
      if (shotPage) {
        await p.evaluate(i => { location.hash = i; }, shotPage); await p.waitForTimeout(400);
        const fig = await p.evaluateHandle(() => [...document.querySelectorAll('.page.on figure.shot:not(.anim)')].find(f => f.querySelector('[data-hz]')));
        await fig.asElement().scrollIntoViewIfNeeded(); await p.waitForTimeout(300);
        const fr = await (await fig.asElement().$('.frame')).boundingBox();
        await p.mouse.move(fr.x + 6, fr.y + fr.height - 6); await p.waitForTimeout(100);
        const onBlank = await p.evaluate(() => !!document.querySelector('.page.on figure.shot.focus'));
        const mk = await fig.asElement().$('.mk');
        let onNumber = true;
        if (mk) { const mb = await mk.boundingBox(); await p.mouse.move(mb.x + mb.width / 2, mb.y + mb.height / 2); await p.waitForTimeout(150); onNumber = await p.evaluate(() => !!document.querySelector('.page.on figure.shot.focus')); }
        if (onBlank) problems.push(`${shotPage}: the screen overlay shows without hovering a number`);
        if (!onNumber) problems.push(`${shotPage}: hovering a number on the screen does not highlight its spot`);
      }
      // search finds the first page by its title
      const first = await p.evaluate(() => document.querySelector('.page').dataset.title);
      await p.keyboard.press('Escape'); await p.click('#searchBtn'); await p.fill('#q', first.slice(0, 12)); await p.waitForTimeout(200);
      const found = await p.evaluate(() => document.querySelectorAll('#res a').length);
      if (!found) problems.push('search finds nothing for the first page title');
      await p.keyboard.press('Escape');
    }
    await p.close();
  }

  if (snaps.length) {
    const out = path.join(site, 'dist', 'snaps'); fs.mkdirSync(out, { recursive: true });
    for (const theme of ['light', 'dark']) {
      const p = await b.newPage({ viewport: { width: 1280, height: 900 } });
      await p.goto(url); await p.waitForTimeout(500);
      await p.evaluate(t => { const btn = document.querySelector('[data-set-theme="' + t + '"]'); if (btn) btn.click(); }, theme);
      for (const id of snaps) {
        await p.evaluate(i => { location.hash = i; }, id); await p.waitForTimeout(500);
        await p.screenshot({ path: path.join(out, `${id}-${theme}.png`), fullPage: true });
      }
      await p.close();
    }
    console.log('screenshots in ' + out);
  }
  await b.close();
  if (problems.length) { console.log('PROBLEMS:\n- ' + problems.join('\n- ')); process.exit(1); }
  console.log('All checks passed.');
})();
