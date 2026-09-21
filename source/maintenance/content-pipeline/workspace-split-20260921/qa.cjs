'use strict';
// Actual book scripts in the existing isolated DOM harness. No browser storage.
// Usage: node qa.cjs [candidate.html] [baseline.html] [report.json]
const fs = require('fs'), path = require('path'), assert = require('assert'), crypto = require('crypto');
const root = path.resolve(__dirname, '../..');
const candidate = path.resolve(process.argv[2] || path.join(__dirname, 'candidate.html'));
const baseline = path.resolve(process.argv[3] || 'C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html');
const report = path.resolve(process.argv[4] || path.join(__dirname, 'qa.json'));
const raw = fs.readFileSync(candidate, 'utf8'), before = fs.readFileSync(baseline, 'utf8');
const sha = x => crypto.createHash('sha256').update(x).digest('hex');
let harness = fs.readFileSync(path.join(root, 'qa_navigation_ui_final.cjs'), 'utf8');
const boundary = harness.indexOf('const f=boot();');
assert(boundary > 0);
harness = harness.slice(0, boundary).replace(/const sourcePath='[^']+';/, () => 'const sourcePath=' + JSON.stringify(candidate) + ';');
const { boot, parseHTML } = new Function('require', harness + '\nreturn {boot, parseHTML};')(require);
const original = parseHTML(before).document, updated = parseHTML(raw).document;
const checks = [];
function check(name, fn) { try { checks.push({name, status:'pass', detail:fn()}); } catch(error) { checks.push({name, status:'needs_fix', error:error.stack}); } }
const attributes = (doc, selector, attr) => [...doc.querySelectorAll(selector)].map(n => n.getAttribute(attr));

check('Every original save field and ID survives without duplication', () => {
  for (const [selector, attr] of [['[data-save]','data-save'],['[id]','id']]) {
    const old = attributes(original, selector, attr), current = attributes(updated, selector, attr);
    assert.equal(new Set(current).size, current.length, 'Duplicate ' + attr);
    for(const value of old) assert(current.includes(value), 'Missing ' + attr + ' ' + value);
    if(attr === 'data-save') assert.deepStrictEqual(current, old);
  }
  return {fields:updated.querySelectorAll('[data-save]').length, originalIds:original.querySelectorAll('[id]').length};
});
check('Learning contracts and all daily feature boundaries are unchanged', () => {
  for(const id of ['learning-adjust-data','daily-study-catalog','daily-study-state','record-concurrency-model-script','energy-control-script','health-study-bridge-script','health-study-ui-script'])
    assert.equal(updated.getElementById(id).outerHTML, original.getElementById(id).outerHTML, id);
  for(const key of ['home','style','state','scripts']) {
    const re = new RegExp('<!--DAILY-STUDY-V1:'+key+'-->[\\s\\S]*?<!--/DAILY-STUDY-V1:'+key+'-->', 'g');
    assert.deepStrictEqual(raw.match(re),before.match(re),key);
  }
});
check('Five independent top-level destinations retain Study, Practice and Tests ordering', () => {
  assert.deepStrictEqual(attributes(updated, '#workspace-navigation nav [data-go]', 'data-go'), ['study','practice','tests','workspace','development']);
  assert.deepStrictEqual([...updated.querySelectorAll('#workspace-navigation nav [data-go]')].map(n=>n.textContent.trim()), ['学习','练习','测试','学习工作台','开发工作台']);
  assert.equal(updated.querySelector('#workspace h1').textContent, '学习工作台');
  assert.equal(updated.querySelector('#development h1').textContent, '开发工作台');
  assert(updated.querySelector('main > #development'));
});
check('All eight old workspace destinations survive and development links are public only', () => {
  const selector = '#workspace .la-workspace-grid a';
  const links = attributes(updated, selector, 'href');
  assert.deepStrictEqual(links, attributes(original, selector, 'href'));
  assert.equal(links.length, 8);
  for(const href of links) assert(updated.getElementById(href.slice(1)),href);
  const dev = updated.querySelector('#development');
  assert.equal(dev.querySelectorAll('[data-save],input,textarea,iframe').length,0);
  assert.deepStrictEqual(attributes(dev, 'a', 'href'), ['https://github.com/duf5391-ux/ielts-learning','https://github.com/duf5391-ux/ielts-learning/actions']);
  for(const a of dev.querySelectorAll('a')) assert.equal(a.getAttribute('rel'),'noopener noreferrer');
  return {learningDestinations:links, developmentDestinations:2};
});
let f;
check('New and legacy routes show separate pages, current navigation and full-width state', () => {
  f = boot();
  for(const [id,title,wide] of [['workspace','学习工作台',true],['development','开发工作台',true],['tests','测试',false],['study','学习',false]]) {
    f.route('#'+id);
    assert.equal(f.q('main > .panel:not([hidden])').id,id);
    assert.equal(f.q('#workspace-navigation [aria-current="page"]').dataset.go,id);
    assert.equal(f.q('#current-page-label').textContent,title);
    assert.equal(f.document.body.classList.contains('ws-wide'),wide);
  }
  f.click(f.q('[data-go="development"]'));
  assert.equal(f.ctx.location.hash,'development');
  f.route('#development');
  assert(f.visible(f.q('#development')));
  assert(!f.visible(f.q('#workspace')));
});
check('All existing workspace tools open through their original routes', () => {
  for(const a of f.qa('#workspace .la-workspace-grid a')) {
    const href = a.getAttribute('href'), node = f.document.getElementById(href.slice(1));
    f.route(href); assert(f.visible(node),href);
    const owner = node.closest('main > .panel').dataset.laOwner;
    assert.equal(f.q('#workspace-navigation [aria-current="page"]').dataset.go,owner,href);
  }
  for(const id of ['test-listening','test-reading','test-writing','test-speaking']) {
    f.route('#'+id); assert(f.visible(f.q('#'+id)),id);
    assert.equal(f.q('#workspace-navigation [aria-current="page"]').dataset.go,'tests');
  }
});
check('Learning records survive navigation between both workbenches and simulated reload', () => {
  const key = 'pr-jijing-202609-listening-01-v1-q1';
  const input = f.q('[data-save="'+key+'"]') || f.q('#pr-jijing-202609-listening-01-v1 [data-save]');
  assert(input);
  const actualKey = input.dataset.save;
  f.input(actualKey,'synthetic retained answer'); f.flush();
  const stored = f.storage;
  f.route('#workspace'); f.route('#development');
  assert.equal(f.storage,stored,'Workbench navigation changed saved answers');
  const restored = boot({initial:stored,hash:'#development'});
  assert.equal(restored.q('[data-save="'+actualKey+'"]').value,'synthetic retained answer');
  assert.equal(restored.q('#workspace-navigation [aria-current="page"]').dataset.go,'development');
  return {syntheticStorageOnly:true};
});
const result = {candidate,baseline,sha256:sha(raw),baselineSha256:sha(before),method:'Existing Node/linkedom harness; actual core/navigation scripts with isolated synthetic records. No real browser, layout engine, user storage or microphone.',passed:checks.filter(c=>c.status==='pass').length,total:checks.length,checks};
fs.writeFileSync(report, JSON.stringify(result,null,2));
console.log(JSON.stringify(result,null,2));
if(result.passed !== result.total) process.exitCode=1;
