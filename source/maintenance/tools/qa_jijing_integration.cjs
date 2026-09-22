#!/usr/bin/env node
'use strict';
// Read-only targeted regression: candidate HTML and baseline HTML, in that order.
// Uses the repository's existing isolated Node/linkedom harness; no user browser data.
const fs = require('fs');
const path = require('path');
const assert = require('assert');
const crypto = require('crypto');
const root = path.resolve(__dirname, '..');
const [candidateArg, baselineArg] = process.argv.slice(2);
if (!candidateArg || !baselineArg) {
  console.error('Usage: node tools/qa_jijing_integration.cjs CANDIDATE.html BASELINE.html');
  process.exit(2);
}
const candidate = path.resolve(candidateArg), baseline = path.resolve(baselineArg);
const candidateRaw = fs.readFileSync(candidate), baselineRaw = fs.readFileSync(baseline);
const sha = raw => crypto.createHash('sha256').update(raw).digest('hex');
const prefix = 'pr-jijing-202609-', projectId = 'jijing-202609-v1';
const harnessFile = path.join(root, 'qa_navigation_ui_final.cjs');
const originalHarness = fs.readFileSync(harnessFile, 'utf8');
const boundary = originalHarness.indexOf('const f=boot();');
assert(boundary > 0, 'Existing harness boundary was not found');
let harness = originalHarness.slice(0, boundary);
const sourceDeclaration = /const sourcePath='[^']+';/;
assert(sourceDeclaration.test(harness), 'Existing harness source declaration changed');
harness = harness.replace(sourceDeclaration, () => 'const sourcePath=' + JSON.stringify(candidate) + ';');
const {boot, parseHTML} = new Function('require', harness + '\nreturn {boot,parseHTML};')(require);
const oldDocument = parseHTML(baselineRaw.toString('utf8')).document;
const newDocument = parseHTML(candidateRaw.toString('utf8')).document;
const oldData = JSON.parse(oldDocument.querySelector('#learning-adjust-data').textContent);
const newData = JSON.parse(newDocument.querySelector('#learning-adjust-data').textContent);
const additions = newData.units.filter(u => u.id.startsWith(prefix));
const checks = [];
function check(name, fn) {
  try { checks.push({name, status:'pass', detail:fn()}); }
  catch (error) { checks.push({name, status:'needs_fix', error:error.stack}); }
}
const counts = (doc, selector, attr) => {
  const result = new Map();
  for (const node of doc.querySelectorAll(selector)) {
    const key = node.getAttribute(attr); result.set(key, (result.get(key) || 0) + 1);
  }
  return result;
};
const normalized = value => JSON.parse(JSON.stringify(value));
check('Every old save key and DOM ID survives; all candidate keys and IDs are unique', () => {
  const detail = {};
  for (const [selector, attr] of [['[data-save]','data-save'], ['[id]','id']]) {
    const before = counts(oldDocument, selector, attr), after = counts(newDocument, selector, attr);
    for (const [key,count] of before) assert.equal(after.get(key), count, 'Removed or duplicated '+attr+': '+key);
    for (const [key,count] of after) assert.equal(count, 1, 'Duplicate '+attr+': '+key);
    detail[attr] = {before:before.size, after:after.size};
  }
  return detail;
});
check('Daily feature boundary blocks and state field remain byte-identical', () => {
  for (const key of ['home','style','state','scripts']) {
    const re = new RegExp('<!--DAILY-STUDY-V1:'+key+'-->[\\s\\S]*?<!--/DAILY-STUDY-V1:'+key+'-->', 'g');
    const a = baselineRaw.toString('utf8').match(re) || [], b = candidateRaw.toString('utf8').match(re) || [];
    assert.equal(a.length,1,key+' baseline marker count'); assert.equal(b.length,1,key+' candidate marker count');
    assert.equal(b[0],a[0],key+' block changed');
  }
  assert.equal(newDocument.querySelector('#daily-study-state').outerHTML,oldDocument.querySelector('#daily-study-state').outerHTML);
});
check('Existing navigation records and media references remain unchanged', () => {
  for (const u of oldData.units) assert.deepStrictEqual(newData.units.find(n=>n.id===u.id),u,'Changed legacy unit '+u.id);
  for (const p of oldData.projects) assert.deepStrictEqual(newData.projects.find(n=>n.id===p.id),p,'Changed legacy project '+p.id);
  assert.deepStrictEqual(newData.tests,oldData.tests,'Legacy test contract changed');
  const media = doc => [...doc.querySelectorAll('img[src],audio[src],source[src]')].map(n=>n.tagName+'|'+n.getAttribute('src'));
  const after = media(newDocument);
  for (const value of media(oldDocument)) { const at=after.indexOf(value); assert(at>=0,'Removed media '+value); after.splice(at,1); }
});
check('New project refers to real versioned batch units, with actual answer fields', () => {
  assert(additions.length>0,'No '+prefix+' units registered');
  const project = newData.projects.find(p=>p.id===projectId); assert(project,'Project not registered');
  assert(project.units.length>0,'Project has no activities');
  assert.equal(newDocument.querySelectorAll('[data-project="'+projectId+'"]').length,1);
  const projectNode = newDocument.querySelector('[data-project="'+projectId+'"]');
  assert(projectNode.closest('#learning-projects')); assert(projectNode.querySelector('[data-project-progress]'));
  for (const id of project.units) {
    assert(additions.some(u=>u.id===id),'Project references an unexpected unit '+id);
    assert(projectNode.querySelector('a[href="#'+id+'"]'),'Project link missing '+id);
  }
  for (const u of additions) {
    assert(!oldData.units.some(o=>o.id===u.id),'Batch overwrites a legacy unit '+u.id);
    const n=newDocument.getElementById(u.id); assert(n,'Missing content '+u.id);
    assert.equal(n.getAttribute('data-learning-unit'),u.id);
    assert(n.closest('main>.panel'),'Content is outside a routed panel');
    assert(u.steps.length>0,'No observable completion steps '+u.id);
    for (const step of u.steps) {
      if (step.kind==='checked') assert(newDocument.getElementById(step.key),'Missing answer gate '+step.key);
      else assert(newDocument.querySelector('[data-save="'+step.key+'"]'),'Missing progress field '+step.key);
    }
    assert(project.units.includes(u.id),'New unit omitted from whole-package project '+u.id);
  }
  return {project:projectId,units:additions.map(u=>u.id)};
});
let f;
check('Candidate core and navigation scripts boot with isolated storage', () => {
  f=boot(); return {userStorageRead:false,syntheticStorage:true,harness:'qa_navigation_ui_final.cjs'};
});
function requireFixture(){assert(f,'Candidate boot failed');return f;}
check('Whole-package project and every new unit route to visible content and its category', () => {
  const g=requireFixture(); assert(additions.length>0);
  g.route('#learning-projects'); assert(g.visible(g.q('[data-project="'+projectId+'"]')));
  for(const u of additions){
    g.route('#'+u.mode+'-'+u.skill+'-list');
    assert(g.q('[data-catalog-unit="'+u.id+'"]'),'Unit missing from category '+u.id);
    g.route('#'+u.id); const n=g.document.getElementById(u.id); assert(g.visible(n),'Hidden unit '+u.id);
    assert.equal(g.q('.la-focus-nav a').getAttribute('href'),'#'+u.mode+'-'+u.skill+'-list');
    assert(g.q('#current-page-label').textContent.includes(u.title));
  }
});
const snapshots=new Map(), written=new Map();
let oldWitness;
check('Blank attempts keep answers hidden; entering answers persists under the original recorder', () => {
  const g=requireFixture(); assert(additions.length>0);
  oldWitness=[...oldDocument.querySelectorAll('textarea[data-save]')].find(n=>!n.closest('.la-gate-content'))?.getAttribute('data-save');
  assert(oldWitness,'No old textarea available as preservation witness');
  g.input(oldWitness,'Synthetic legacy answer retained');
  let gateCount=0;
  for(const u of additions){
    g.route('#'+u.id); const node=g.document.getElementById(u.id);
    const gates=[...node.querySelectorAll('[data-answer-gate]')];
    assert(gates.length>0,'No answer gate for '+u.id);
    for(const gate of gates){
      const keys=JSON.parse(gate.dataset.answerGate), content=gate.querySelector('.la-gate-content');
      assert(keys.length>0&&content,'Malformed gate '+gate.id);
      assert(content.hidden,'Answers exposed before attempt '+gate.id);
      g.click(gate.querySelector('summary')); assert(content.hidden,'Blank attempt unlocked answers '+gate.id);
      assert(!g.state().checked[gate.id],'Blank attempt recorded as checked');
      for(const [i,key] of keys.entries()){
        const answer='Synthetic '+u.id+' answer '+(i+1);
        g.input(key,answer); written.set(key,answer);
        assert.equal(JSON.parse(g.storage).fields[key],answer,'Answer was not saved '+key);
      }
      gateCount++;
    }
  }
  assert.equal(JSON.parse(g.storage).fields[oldWitness],'Synthetic legacy answer retained');
  return {gates:gateCount,savedAnswers:written.size};
});
check('Checking captures an immutable first attempt and reveals answer content', () => {
  const g=requireFixture();assert(written.size>0,'No saved batch answers');
  for(const u of additions){
    g.route('#'+u.id);
    for(const gate of g.document.getElementById(u.id).querySelectorAll('[data-answer-gate]')){
      const keys=JSON.parse(gate.dataset.answerGate);
      g.click(gate.querySelector('summary'));
      // linkedom does not implement the browser's native details-summary default action.
      // Replay the default toggle only after the actual click handler has accepted it.
      assert(!gate.querySelector('.la-gate-content').hidden,'Answered gate refused to reveal '+gate.id);
      gate.open=true;gate.dispatchEvent(new g.ctx.Event('toggle'));g.flush();
      const first=g.state().checked[gate.id];assert(first&&first.at,'No saved first-attempt timestamp '+gate.id);
      for(const key of keys)assert.equal(first.answers[key],written.get(key));
      snapshots.set(gate.id,normalized(first));
      const revised='Synthetic revision after first check';g.input(keys[0],revised);written.set(keys[0],revised);
      gate.open=false;g.click(gate.querySelector('summary'));gate.open=true;gate.dispatchEvent(new g.ctx.Event('toggle'));
      assert.deepStrictEqual(normalized(g.state().checked[gate.id]),snapshots.get(gate.id),'First attempt was overwritten '+gate.id);
    }
  }
  return {firstAttempts:snapshots.size};
});
check('Reload restores new drafts, original answers, first attempts and resume navigation', () => {
  const g=requireFixture();assert(snapshots.size>0,'No first attempts to reload');
  const last=g.state().last, storage=g.storage, reloaded=boot({initial:storage,hash:'#study'});
  for(const [key,value] of written)assert.equal(reloaded.q('[data-save="'+key+'"]').value,value,'Lost new answer '+key);
  assert.equal(reloaded.q('[data-save="'+oldWitness+'"]').value,'Synthetic legacy answer retained');
  for(const [key,value] of snapshots)assert.deepStrictEqual(normalized(reloaded.state().checked[key]),value,'Lost first attempt '+key);
  assert(reloaded.q('#la-resume a[href="#'+last+'"]'),'Resume link does not target last batch unit');
  reloaded.route('#'+last);assert(reloaded.visible(reloaded.document.getElementById(last)));
  return {restoredAnswers:written.size,resume:last};
});
check('QA did not mutate either input file', () => {
  assert.equal(sha(fs.readFileSync(candidate)),sha(candidateRaw));
  assert.equal(sha(fs.readFileSync(baseline)),sha(baselineRaw));
});
const out={candidate,baseline,sha256:sha(candidateRaw),baselineSHA256:sha(baselineRaw),method:'Actual candidate core and navigation scripts in the existing Node/linkedom harness with isolated synthetic localStorage. No real browser, layout, audio playback or user data. Read-only input files.',checks,passed:checks.filter(c=>c.status==='pass').length,total:checks.length};
console.log(JSON.stringify(out,null,2));
if(out.passed!==out.total)process.exitCode=1;
