const { chromium } = require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('fs'), path = require('path'), assert = require('assert');
const { pathToFileURL } = require('url');
const book = 'C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册';
const qa = path.join(__dirname, 'background-expansion-qa');
fs.mkdirSync(qa, { recursive: true });
const units = ['family', 'food', 'travel', 'media'].map(n => JSON.parse(fs.readFileSync(path.join(__dirname, 'expanded-' + n + '.json'), 'utf8')));

(async () => {
  const browser = await chromium.launch({ executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: true });
  const context = await browser.newContext({ viewport: { width: 1380, height: 980 } });
  const page = await context.newPage(), errors = [], checks = [], screenshots = [];
  page.on('pageerror', e => errors.push(e.message));
  const check = async (name, fn) => {
    try { checks.push({ name, pass: true, result: await fn() }); }
    catch (e) { checks.push({ name, pass: false, error: e.message }); }
  };
  const screen = async name => { const file = path.join(qa, name + '.png'); await page.screenshot({ path: file }); screenshots.push(file); };
  const frame = () => page.evaluate(() => new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r))));
  try {
    await page.goto(pathToFileURL(path.join(book, '开始学习.html')).href + '#background');
    await check('four expanded units and all glossary entries are present', async () => {
      assert.equal(await page.locator('#background .background-expanded').count(), 4);
      const glossary = await page.locator('#lookup-glossary').evaluate(e => JSON.parse(e.textContent));
      const stats = [];
      for (const u of units) {
        const unit = page.locator(`[data-enrichment="${u.id}"]`);
        await unit.locator(':scope > summary').click();
        const prose = unit.locator('.background-lesson');
        assert(await prose.isVisible(), u.id);
        const text = await prose.innerText();
        assert(text.length > 5000, `${u.id}: too little content ${text.length}`);
        assert(!/官方|自编|四科|听说读写|核验/.test(text));
        assert.equal(await prose.locator('tbody tr').count(), 16);
        for (const w of u.glossary) {
          const term = w.term.trim().toLowerCase().replace(/\s+/g, ' ');
          assert(glossary[term]?.some(e => e.example === w.example && e.meaning === w.meaning), term);
        }
        const colour = await prose.locator('p').first().evaluate(e => getComputedStyle(e).color);
        assert.equal(colour, 'rgb(173, 36, 48)');
        stats.push({ id: u.id, characters: text.length, glossary: u.glossary.length, colour });
      }
      return stats;
    });
    await check('optional recall opens without an answer', async () => {
      for (const u of units) {
        const unit = page.locator(`[data-enrichment="${u.id}"]`);
        assert.equal(await unit.locator(`[data-save="enrich-${u.id}-answer"]`).inputValue(), '');
        await unit.locator('[data-enrich-freeze]').click();
        assert(await unit.locator('.enrichment-feedback').isVisible());
        assert.equal(await unit.locator(`[data-save="enrich-${u.id}-answer"]`).evaluate(e => e.readOnly), false);
      }
      return { blankAnswersAccepted: 4 };
    });
    await check('existing note keys preserve writing and reload', async () => {
      for (const u of units) await page.locator(`[data-save="enrich-${u.id}-answer"]`).fill('Background QA ' + u.id);
      await frame(); await page.reload(); await frame();
      for (const u of units) {
        assert.equal(await page.locator(`[data-save="enrich-${u.id}-answer"]`).inputValue(), 'Background QA ' + u.id);
        assert(await page.locator(`[data-save="enrich-${u.id}-frozen"]`).isChecked());
      }
      return { savedAndRestored: 4, isolatedContext: true };
    });
    await check('new topic expressions work in the lookup UI', async () => {
      const examples = [];
      for (const u of units) {
        const w = u.glossary[0];
        await page.locator('#lookup-open').click();
        await page.locator('#lookup-input').fill(w.term);
        await page.locator('#lookup-form').evaluate(f => f.requestSubmit());
        const result = await page.locator('#lookup-result').innerText();
        assert(result.includes(w.meaning), `${w.term}: ${result}`);
        assert(!/来源|官方|出处|核验/.test(result));
        examples.push(w.term);
        await page.locator('#lookup-close').click();
      }
      return examples;
    });
    await check('desktop and phone layouts keep content inside the page', async () => {
      const widths = [];
      for (const width of [1380, 390]) {
        await page.setViewportSize({ width, height: width === 390 ? 844 : 980 });
        for (const u of units) {
          const unit = page.locator(`[data-enrichment="${u.id}"]`);
          if (!await unit.evaluate(e => e.open)) await unit.locator(':scope > summary').click();
          await unit.locator(':scope > summary').scrollIntoViewIfNeeded();
          const size = await page.evaluate(() => ({ page: document.documentElement.scrollWidth, viewport: innerWidth }));
          assert(size.page <= size.viewport + 1, `${u.id}: ${JSON.stringify(size)}`);
          const p = unit.locator('.background-lesson p').first();
          const box = await p.boundingBox();
          assert(box.x >= 0 && box.x + box.width <= width + 1);
          if (width === 390) {
            const cells = await unit.locator('.background-lesson tbody tr').first().locator('td').all();
            for (const cell of cells) {
              const cb = await cell.boundingBox();
              assert(cb.x >= 0 && cb.x + cb.width <= width + 1, `${u.id}: word bank cell clipped`);
            }
          }
          widths.push({ id: u.id, width, ...size });
        }
        const first = page.locator(`[data-enrichment="${units[0].id}"]`);
        await first.locator('.background-lesson h3').first().evaluate(e => e.scrollIntoView({ block: 'start' }));
        await screen(width === 390 ? 'mobile-family-background' : 'desktop-family-background');
        const media = page.locator(`[data-enrichment="${units[3].id}"]`);
        await media.locator('.background-lesson h3').filter({ hasText: '情境一' }).evaluate(e => e.scrollIntoView({ block: 'start' }));
        await screen(width === 390 ? 'mobile-media-example' : 'desktop-media-example');
        await media.locator('.background-lesson table').evaluate(e => e.scrollIntoView({ block: 'start' }));
        await screen(width === 390 ? 'mobile-word-bank' : 'desktop-word-bank');
      }
      return widths;
    });
    await check('no browser errors', async () => assert.deepEqual(errors, []));
  } finally {
    const result = { checks, errors, screenshots, passed: checks.filter(c => c.pass).length, failed: checks.filter(c => !c.pass).length, isolatedContext: true };
    fs.writeFileSync(path.join(qa, 'results.json'), JSON.stringify(result, null, 2));
    console.log(JSON.stringify(result, null, 2));
    await context.close(); await browser.close();
    if (result.failed) process.exitCode = 1;
  }
})().catch(e => { console.error(e.stack); process.exitCode = 1; });
