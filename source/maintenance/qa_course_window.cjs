/* Isolated browser acceptance checks for the custom staged learning window. */
const { chromium } = require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const fs = require('fs');
const path = require('path');
const assert = require('assert/strict');
const { pathToFileURL } = require('url');

const root = __dirname;
const out = path.join(root, 'course-window-qa');
fs.mkdirSync(out, { recursive: true });
const stages = ['baseline', 'understand', 'guided', 'transfer', 'delayed'];
const clone = value => JSON.parse(JSON.stringify(value));
const payload = JSON.parse(fs.readFileSync(path.join(root, 'course-window-seed.json'), 'utf8'));
const css = fs.readFileSync(path.join(root, 'course-window.css'), 'utf8');
const js = fs.readFileSync(path.join(root, 'course-window.js'), 'utf8');
const fixture = path.join(out, 'fixture.html');
fs.writeFileSync(fixture, '<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Course window QA</title><style>body{margin:0;padding:16px;background:#f5f3eb;font-family:Arial,sans-serif;color:#263a32}*{box-sizing:border-box}</style><style>' + css + '</style></head><body><section id="course-window"><div id="course-window-app"></div></section><script id="course-window-data" type="application/json">' + JSON.stringify(payload).replace(/</g, '\\u003c') + '</script><script>' + js + '</script></body></html>');

const checks = [];
const upload = (page, value) => page.locator('#cw-import-file').setInputFiles({ name: 'course-qa.json', mimeType: 'application/json', buffer: Buffer.from(typeof value === 'string' ? value : JSON.stringify(value)) });
const state = page => page.evaluate(() => window.IELTSCourseWindow.getState());
const storage = page => page.evaluate(() => Object.fromEntries(Object.keys(localStorage).map(k => [k, localStorage.getItem(k)])));
const openIntake = async page => { if (!await page.locator('.cw-intake').evaluate(node => node.open)) await page.locator('.cw-intake > summary').click(); };
const downloadText = async (page, selector) => {
  const [download] = await Promise.all([page.waitForEvent('download'), page.locator(selector).click()]);
  return fs.readFileSync(await download.path(), 'utf8');
};

async function run(browser, name, fn, viewport = { width: 1440, height: 1100 }) {
  const context = await browser.newContext({ acceptDownloads: true, viewport });
  const page = await context.newPage();
  page.setDefaultTimeout(7000);
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('dialog', dialog => dialog.accept());
  try {
    await page.goto(pathToFileURL(fixture).href, { waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => window.IELTSCourseWindow);
    await fn(page);
    assert.deepEqual(errors, [], 'No uncaught browser errors');
    checks.push({ name, pass: true });
  } catch (error) {
    const png = name.replace(/[^a-z0-9]+/gi, '-').slice(0, 70) + '-failure.png';
    await page.screenshot({ path: path.join(out, png), fullPage: true, animations: 'disabled' }).catch(() => {});
    checks.push({ name, pass: false, error: error.stack, browserErrors: errors });
  } finally {
    await context.close();
  }
}

async function contentCheck() {
  assert.equal(payload.version, 1);
  assert(payload.courses.length > 0, 'Example course exists');
  for (const course of payload.courses) {
    assert.equal(course.status, 'sample', 'Example clearly marked as sample');
    assert.deepEqual(course.stages.map(stage => stage.id), stages);
    const sourceIds = new Set(course.items.map(item => item.id));
    assert(course.examAlignment, 'The other side of fitting is the examination');
    const criterionIds = new Set(course.examAlignment.criteria.map(criterion => criterion.id));
    const officialIds = new Set(course.examAlignment.sources.map(source => source.id));
    assert(course.examAlignment.gaps.length > 0, 'Exam requirements not covered by these materials are explicit');
    for (const criterion of course.examAlignment.criteria) {
      assert(criterion.requirement);
      assert(criterion.sourceIds.every(id => officialIds.has(id)), 'Exam requirement links resolve to official sources');
    }
    const examCoverage = new Set();
    const coverage = new Set();
    const taskIds = new Set();
    for (const stage of course.stages) {
      assert(stage.tasks.length > 0, 'Each learning window contains actionable work');
      for (const task of stage.tasks) {
        assert(!taskIds.has(task.id), 'Task IDs unique within course');
        taskIds.add(task.id);
        assert(task.targets.length > 0);
        for (const id of task.targets) {
          assert(sourceIds.has(id), 'Every task traces back to an input material point');
          coverage.add(id);
        }
        assert(task.reference && task.explanation && task.rubric.length, 'Every task has explanation and concrete check criteria');
        assert(task.examUse && task.examTargets.length, 'Every task explains its examination use');
        for (const id of task.examTargets) {
          assert(criterionIds.has(id), 'Every task points to an actual exam requirement');
          examCoverage.add(id);
        }
        assert.equal(task.practiceMode, 'micro', 'Sample partial tasks are labeled as partial practice');
        if (task.type === 'choice') assert(task.options.some(option => option.id === task.answer));
      }
    }
    assert.deepEqual([...coverage].sort(), [...sourceIds].sort(), 'Every input point has practice coverage');
    assert.deepEqual([...examCoverage].sort(), [...criterionIds].sort(), 'Every targeted exam requirement maps back to specific practice');
    const transfer = course.stages.find(stage => stage.id === 'transfer');
    assert(transfer.tasks.some(task => task.examTargets.includes('task-response') && /agree or disagree/.test(task.prompt)), 'Independent transfer yields an artifact answering an exam-style prompt');
  }
}

async function main() {
  try { await contentCheck(); checks.push({ name: 'source material and practice bidirectional coverage', pass: true }); }
  catch (error) { checks.push({ name: 'source material and practice bidirectional coverage', pass: false, error: error.stack }); }
  const browser = await chromium.launch({ executablePath: 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe', headless: true });
  try {
    await run(browser, 'fixture boot and desktop screenshot', async page => {
      assert(await page.locator('#course-window-app').innerText());
      const runtimeCourse = await page.evaluate(() => window.IELTSCourseWindow.getCourses()[0]);
      assert.deepEqual(runtimeCourse, payload.courses[0], 'Runtime validation preserves the authored curriculum and all provenance metadata');
      await page.screenshot({ path: path.join(out, 'desktop.png'), fullPage: true, animations: 'disabled' });
    });
    await run(browser, 'raw intake stays pending and exports a faithful design brief', async page => {
      const before = await page.evaluate(() => window.IELTSCourseWindow.getCourses().length);
      await openIntake(page);
      await page.locator('#cw-intake-title').fill('我的因果词汇');
      await page.locator('#cw-intake-raw').fill('contribute to + noun / -ing\nMy raw source stays intact.');
      await page.locator('#cw-intake-requirement').fill('我要在 IELTS Task 2 中支持一个相关观点。');
      await page.locator('#cw-intake-minutes').selectOption('5');
      await page.locator('#cw-intake-save').click();
      let saved = await state(page);
      assert.equal(saved.drafts.length, 1);
      assert.equal(saved.drafts[0].status, 'pending');
      assert.equal(saved.drafts[0].minutes, 5);
      assert.equal(await page.evaluate(() => window.IELTSCourseWindow.getCourses().length), before, 'Saving raw input does not fake generated lessons');
      assert((await page.locator('#cw-workspace').innerText()).includes('待设计'));
      const brief = await downloadText(page, '#cw-export-brief');
      assert(brief.includes('My raw source stays intact.'));
      assert(brief.includes('我要在 IELTS Task 2 中支持一个相关观点。'));
      assert(brief.includes('考试'), 'The design brief covers the examination side of fitting');
      const backup = JSON.parse(await downloadText(page, '#cw-export-backup'));
      assert.equal(backup.drafts[0].raw, saved.drafts[0].raw);
      await page.reload({ waitUntil: 'domcontentloaded' });
      saved = await state(page);
      assert.equal(saved.drafts[0].title, '我的因果词汇');
      assert((await page.locator('#cw-workspace').innerText()).includes('My raw source stays intact.'));
    });
    await run(browser, 'one visible stage and material to exam map', async page => {
      const course = payload.courses[0];
      for (const stage of course.stages) {
        await page.locator('[data-cw-stage="' + stage.id + '"]').click();
        assert.equal(await page.locator('.cw-stage-content').count(), 1);
        assert.equal(await page.locator('[data-cw-stage][aria-current="step"]').getAttribute('data-cw-stage'), stage.id);
        assert.deepEqual(await page.locator('.cw-stage-content [data-cw-task]').evaluateAll(nodes => nodes.map(node => node.dataset.cwTask)), stage.tasks.map(task => task.id));
        if (['baseline', 'transfer', 'delayed'].includes(stage.id)) {
          const trace = await page.locator('.cw-stage-content .cw-targets').allInnerTexts();
          for (const text of trace) for (const item of course.items) assert(!text.includes(item.text), 'Before answering, tracing labels do not reveal target expressions as answer hints');
        }
      }
      await page.locator('#cw-fit-map > summary').click();
      const map = await page.locator('#cw-fit-map').innerText();
      for (const item of course.items) assert(map.includes(item.text));
      for (const criterion of course.examAlignment.criteria) assert(map.includes(criterion.label), 'Exam criteria link back to materials and practice');
      assert(map.includes(course.examAlignment.gaps[0]), 'Uncovered exam demands are visible');
      await page.locator('[data-cw-map-task="baseline-survey-choice"]').first().click();
      assert.equal(await page.locator('[data-cw-stage][aria-current="step"]').getAttribute('data-cw-stage'), 'baseline');
      assert.equal(await page.locator('.cw-reference').count(), 0, 'Map navigation does not reveal answers');
    });
    await run(browser, 'choice draft reload frozen submission and retry preserve first attempt', async page => {
      const id = 'baseline-survey-choice';
      await page.locator('[data-cw-answer="' + id + '"]').selectOption('b');
      await page.reload({ waitUntil: 'domcontentloaded' });
      assert.equal(await page.locator('[data-cw-answer="' + id + '"]').inputValue(), 'b');
      await page.locator('[data-cw-submit="' + id + '"]').click();
      let saved = await state(page);
      assert.equal(saved.attempts.length, 1);
      assert.equal(saved.attempts[0].correct, true);
      const frozen = clone(saved.attempts[0]);
      const card = page.locator('[data-cw-task="' + id + '"]');
      assert.equal(await card.locator('[data-cw-answer]').count(), 0, 'Frozen response is not editable');
      await card.locator('[data-cw-assessment="independent"]').click();
      await card.getByRole('button', { name: '再试一次（保留这次提交）' }).click();
      await page.locator('[data-cw-answer="' + id + '"]').selectOption('a');
      await page.locator('[data-cw-submit="' + id + '"]').click();
      saved = await state(page);
      assert.equal(saved.attempts.length, 2);
      assert.deepEqual(saved.attempts[0], frozen);
      assert.equal(saved.attempts[1].correct, false);
      assert.equal(saved.attempts[1].priorExposure, true);
      await page.reload({ waitUntil: 'domcontentloaded' });
      assert.deepEqual((await state(page)).attempts, saved.attempts);
    });
    await run(browser, 'text remains self assessment and independent result schedules delayed practice', async page => {
      const id = 'transfer-garden-report';
      await page.locator('[data-cw-stage="transfer"]').click();
      await page.locator('[data-cw-answer="' + id + '"]').fill('QA arbitrary prose: presence of associated with does not prove semantic correctness.');
      await page.locator('[data-cw-submit="' + id + '"]').click();
      let saved = await state(page);
      assert.equal(saved.attempts[0].correct, null, 'Text has no fabricated objective score');
      const card = page.locator('[data-cw-task="' + id + '"]');
      assert((await card.innerText()).includes('文字作答不自动判分'));
      assert(await card.locator('.cw-reference').isVisible());
      assert.equal(await card.locator('.cw-reference li').count(), payload.courses[0].stages.find(stage => stage.id === 'transfer').tasks[0].rubric.length);
      await card.locator('[data-cw-assessment="independent"]').click();
      const next = await page.locator('.cw-next').innerText();
      assert(next.includes('隔日'));
      assert(next.includes('不代表掌握'));
      await page.locator('.cw-next').getByRole('button', { name: '进入建议阶段 →' }).click();
      assert.equal(await page.locator('[data-cw-stage][aria-current="step"]').getAttribute('data-cw-stage'), 'delayed');
      await page.locator('[data-cw-answer="delayed-factor-choice"]').selectOption('a');
      await page.locator('[data-cw-submit="delayed-factor-choice"]').click();
      assert((await page.locator('.cw-next').innerText()).includes('同一天'), 'Immediate delayed task is not misreported as retention');
      saved = await state(page);
      assert.equal(saved.feedback[0].value, 'independent');
      const exported = JSON.parse(await downloadText(page, '#cw-export-backup'));
      assert.deepEqual(exported.attempts, saved.attempts);
      assert.deepEqual(exported.feedback, saved.feedback);
    });
    await run(browser, 'viewed reference and source support survive reload and submission', async page => {
      const id = 'baseline-event-text';
      await page.locator('[data-cw-reveal="' + id + '"]').click();
      await page.reload({ waitUntil: 'domcontentloaded' });
      assert(await page.locator('[data-cw-task="' + id + '"] .cw-reference').isVisible());
      await page.locator('[data-cw-answer="' + id + '"]').fill('The blocked sensor led to the conveyor belt stopping.');
      await page.locator('[data-cw-support="' + id + '"]').selectOption('independent');
      await page.locator('[data-cw-submit="' + id + '"]').click();
      let saved = await state(page);
      assert.equal(saved.attempts[0].revealed, true);
      assert.equal(saved.attempts[0].support, 'reference', 'Previously revealed answer cannot become an unsupported attempt by changing the dropdown');
      assert(saved.exposures.some(exposure => exposure.taskId === id && exposure.kind === 'reference'));
      const other = 'baseline-survey-choice';
      await page.locator('[data-cw-task="' + other + '"]').getByRole('button', { name: '查看对应讲解（计为看过提示）' }).click();
      await page.locator('[data-cw-answer="' + other + '"]').selectOption('b');
      await page.locator('[data-cw-submit="' + other + '"]').click();
      saved = await state(page);
      assert.equal(saved.attempts[1].sourceSeen, true);
      assert.equal(saved.attempts[1].support, 'reference');
      assert((await page.locator('.cw-next').innerText()).includes('不能代表独立'));
    });
    await run(browser, 'corrupt local storage is preserved and raw export is exact', async page => {
      const raw = '{broken course-window original data';
      await page.evaluate(value => localStorage.setItem(window.IELTSCourseWindow.storageKey, value), raw);
      await page.reload({ waitUntil: 'domcontentloaded' });
      assert((await page.locator('#cw-message').innerText()).includes('暂停保存'));
      await openIntake(page);
      await page.locator('#cw-intake-raw').fill('This input must not overwrite corrupt stored data.');
      await page.locator('#cw-intake-save').click();
      assert.equal((await storage(page))['ielts-course-window-v1'], raw);
      assert.equal(await downloadText(page, '#cw-export-raw'), raw);
      assert.equal(await page.locator('#cw-intake-raw').inputValue(), 'This input must not overwrite corrupt stored data.');
    });
    await run(browser, 'valid backup recovers corrupt storage while preserving original raw data', async page => {
      const backup = JSON.parse(await downloadText(page, '#cw-export-backup'));
      const raw = '{broken recovery marker';
      await page.evaluate(value => localStorage.setItem(window.IELTSCourseWindow.storageKey, value), raw);
      await page.reload({ waitUntil: 'domcontentloaded' });
      await upload(page, backup);
      await page.waitForFunction(value => localStorage.getItem(window.IELTSCourseWindow.storageKey) !== value, raw);
      await openIntake(page);
      await page.locator('#cw-intake-title').fill('Recovery edit');
      await page.locator('#cw-intake-raw').fill('Recovered editable course window');
      await page.locator('#cw-intake-save').click();
      assert((await state(page)).drafts.some(draft => draft.title === 'Recovery edit'));
      const saved = await storage(page);
      assert(Object.entries(saved).some(([key, value]) => key !== 'ielts-course-window-v1' && value === raw), 'Exact corrupt raw data remains preserved in a separate recovery key');
      assert.notEqual(saved['ielts-course-window-v1'], raw);
    });
    await run(browser, 'failed browser storage write leaves existing state and import candidate unchanged', async page => {
      await openIntake(page);
      await page.locator('#cw-intake-title').fill('Saved original');
      await page.locator('#cw-intake-raw').fill('Original material');
      await page.locator('#cw-intake-save').click();
      const previousState = await state(page);
      const previousStorage = await storage(page);
      const course = clone(payload.courses[0]); course.id = 'qa-quota-import'; course.status = 'ready';
      await page.evaluate(() => { window.courseQASetItem = Storage.prototype.setItem; Storage.prototype.setItem = function () { throw new DOMException('Quota', 'QuotaExceededError'); }; });
      await upload(page, { version: 1, courses: [course] });
      await page.waitForFunction(() => document.getElementById('cw-message').textContent.includes('未导入'));
      assert.deepEqual(await state(page), previousState);
      assert.deepEqual(await storage(page), previousStorage);
      await page.evaluate(() => { Storage.prototype.setItem = window.courseQASetItem; });
      await upload(page, { version: 1, courses: [course] });
      await page.waitForFunction(() => window.IELTSCourseWindow.getState().courses.some(course => course.id === 'qa-quota-import'));
    });
    await run(browser, 'valid authored course import and invalid package rejection', async page => {
      const course = clone(payload.courses[0]);
      course.id = 'qa-imported-course';
      course.title = 'QA 导入课程';
      course.status = 'ready';
      const valid = { version: 1, courses: [course] };
      await upload(page, valid);
      await page.waitForFunction(() => JSON.stringify(window.IELTSCourseWindow.getState()).includes('qa-imported-course'));
      const saved = await storage(page);
      const invalids = [
        '{broken',
        { version: 1, courses: null },
        { version: 1, courses: [course, course] },
      ];
      const badTarget = clone(valid); badTarget.courses[0].stages[0].tasks[0].targets = ['missing-material']; invalids.push(badTarget);
      const badAnswer = clone(valid); badAnswer.courses[0].stages[0].tasks[0].answer = 'missing-option'; invalids.push(badAnswer);
      const noRubric = clone(valid); noRubric.courses[0].stages[0].tasks[0].rubric = []; invalids.push(noRubric);
      const badStages = clone(valid); badStages.courses[0].stages.reverse(); invalids.push(badStages);
      const badExamTarget = clone(valid); badExamTarget.courses[0].stages[0].tasks[0].examTargets = ['nonexistent-criterion']; invalids.push(badExamTarget);
      const badSource = clone(valid); badSource.courses[0].examAlignment.criteria[0].sourceIds = ['nonexistent-source']; invalids.push(badSource);
      const badUrl = clone(valid); badUrl.courses[0].examAlignment.sources[0].url = 'javascript:window.courseQAXSS=true'; invalids.push(badUrl);
      const badTaskSource = clone(valid); badTaskSource.courses[0].stages.find(stage => stage.id === 'transfer').tasks[1].materialSourceIds = ['missing-official-task']; invalids.push(badTaskSource);
      for (const invalid of invalids) {
        await page.locator('#cw-import-file').setInputFiles([]);
        await upload(page, invalid);
        await page.waitForTimeout(120);
        assert.deepEqual(await storage(page), saved, 'Malformed import leaves the saved record untouched');
        assert((await page.locator('#cw-message').innerText()).trim(), 'Validation gives an actionable message');
      }
      await page.reload({ waitUntil: 'domcontentloaded' });
      assert(JSON.stringify(await state(page)).includes('qa-imported-course'), 'Authored course survives reload');
    });
    await run(browser, 'imported strings remain inert text', async page => {
      const course = clone(payload.courses[0]);
      course.id = 'qa-xss-course';
      course.status = 'ready';
      const attack = '<img src=x onerror="window.courseQAXSS=true"><svg onload="window.courseQAXSS=true">';
      course.title = attack;
      course.sourceText = attack;
      course.items[0].text = attack;
      course.stages[0].tasks[0].prompt = attack;
      await upload(page, { version: 1, courses: [course] });
      await page.waitForFunction(() => JSON.stringify(window.IELTSCourseWindow.getState()).includes('qa-xss-course'));
      assert.equal(await page.evaluate(() => Boolean(window.courseQAXSS)), false);
      assert.equal(await page.locator('#course-window-app img[src="x"],#course-window-app svg[onload]').count(), 0);
      await page.reload({ waitUntil: 'domcontentloaded' });
      assert.equal(await page.evaluate(() => Boolean(window.courseQAXSS)), false);
    });
    await run(browser, '390px mobile layout has no horizontal overflow', async page => {
      const width = await page.evaluate(() => ({ viewport: innerWidth, document: document.documentElement.scrollWidth }));
      assert(width.document <= width.viewport + 1, JSON.stringify(width));
      await page.screenshot({ path: path.join(out, 'mobile.png'), fullPage: true, animations: 'disabled' });
    }, { width: 390, height: 844 });
    await run(browser, 'official task provenance is retained rendered and exported with adaptation boundary', async page => {
      const task = payload.courses[0].stages.flatMap(stage => stage.tasks).find(task => task.materialSourceIds?.length);
      assert(task, 'At least one task uses an identified official task as teaching material');
      await page.locator('[data-cw-stage="transfer"]').click();
      const card = page.locator('[data-cw-task="' + task.id + '"]');
      for (const id of task.materialSourceIds) {
        const source = payload.courses[0].examAlignment.sources.find(source => source.id === id);
        assert(source);
        assert.equal(await card.locator('.cw-task-provenance a').filter({ hasText: source.title }).getAttribute('href'), source.url);
      }
      assert((await card.locator('.cw-task-provenance').innerText()).includes(task.adaptationNote));
      const exported = JSON.parse(await downloadText(page, '#cw-export-backup'));
      const exportedTask = exported.courses[0].stages.flatMap(stage => stage.tasks).find(t => t.id === task.id);
      assert.deepEqual(exportedTask.materialSourceIds, task.materialSourceIds);
      assert.equal(exportedTask.adaptationNote, task.adaptationNote);
      await page.screenshot({ path: path.join(out, 'official-transfer.png'), fullPage: true, animations: 'disabled' });
    });
    if (process.argv.includes('--main')) await run(browser, 'integrated book navigation intake and preserved field inventory', async page => {
      const report = JSON.parse(fs.readFileSync(path.join(out, 'integration.json'), 'utf8'));
      const mainPath = report.main || 'C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html';
      await page.goto(pathToFileURL(mainPath).href, { waitUntil: 'domcontentloaded' });
      await page.locator('button[data-go="course-window"]').click();
      assert(await page.locator('#course-window').isVisible());
      assert.equal(await page.locator('[data-save]').count(), report.preserved_fields);
      assert.equal(await page.locator('img,audio,source').evaluateAll(nodes => nodes.filter(node => !node.closest('.zoom-dialog')).length), report.preserved_media, 'Original media survive; the existing zoom script creates one empty helper image at runtime');
      const ids = await page.locator('[id]').evaluateAll(elements => elements.map(element => element.id));
      assert.equal(ids.length, new Set(ids).size, 'Integrated IDs remain unique');
      await openIntake(page);
      await page.locator('#cw-intake-title').fill('QA integrated material');
      await page.locator('#cw-intake-raw').fill('contribute to + noun / -ing');
      await page.locator('#cw-intake-requirement').fill('在 Task 2 正确解释原因及限制');
      await page.locator('#cw-intake-save').click();
      assert(JSON.stringify(await state(page)).includes('QA integrated material'));
      await page.screenshot({ path: path.join(out, 'main-desktop.png'), fullPage: true, animations: 'disabled' });
      await page.setViewportSize({ width: 390, height: 844 });
      assert(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth + 1));
      await page.screenshot({ path: path.join(out, 'main-mobile.png'), fullPage: true, animations: 'disabled' });
    });
  } finally { await browser.close(); }
  const result = { scope: 'Temporary isolated browser profiles; no real browser profile or personal progress modified', generatedAt: new Date().toISOString(), checks };
  fs.writeFileSync(path.join(out, 'results.json'), JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 2));
  if (checks.some(check => !check.pass)) process.exitCode = 1;
}
main().catch(error => { console.error(error); process.exitCode = 1; });
