// Verify the only delta after the full navigation regression: two workspace links.
const fs=require('fs'),assert=require('assert'),crypto=require('crypto');
const hash=x=>crypto.createHash('sha256').update(x).digest('hex');
const root='C:/Users/Admin1/Documents/ChatGPT/ielts/research/';
const previousPath='D:/IELTS-Work/learning-adjust-20260920/开始学习-ui-checked-da07a7ff.html';
const previous=fs.readFileSync(previousPath);
const baseline=JSON.parse(fs.readFileSync(root+'navigation-ui-tests-before-shortcuts-20260920.json','utf8'));
assert.equal(hash(previous),baseline.sha256);
assert.equal(baseline.passed,baseline.total);
const harness=fs.readFileSync('qa_navigation_ui_final.cjs','utf8').split('const f=boot();')[0];
const {boot,sourcePath,raw,html}=new Function('require',harness+'\nreturn {boot,sourcePath,raw,html};')(require);
const checks=[];
function check(name,fn){try{checks.push({name,status:'pass',detail:fn()});}catch(error){checks.push({name,status:'needs_fix',error:error.stack});}}
check('Latest page differs from the fully checked page only by two workspace shortcut cards',()=>{
 const pattern=/<article class="la-card" data-workspace-shortcut="(?:vocabulary-review|sentence-learning)">[\s\S]*?<\/article>/g;
 const added=html.match(pattern)||[];assert.equal(added.length,2);
 assert.equal(html.replace(pattern,''),previous.toString('utf8'));
 return {baselineSHA256:baseline.sha256,addedCards:2,allOtherBytesUnchanged:true};
});
check('Both new workspace shortcuts open visible saved content and preserve Workspace ownership',()=>{
 const f=boot();f.route('#workspace');assert.equal(f.qa('#workspace .la-workspace-grid a').length,8);
 for(const id of ['vocabulary-review','sentence-learning']){
  const a=f.q('[data-workspace-shortcut="'+id+'"] a');assert(f.visible(a));
  f.route(a.getAttribute('href'));const target=f.q('#'+id);assert(f.visible(target),id);
  const panel=target.closest('main>.panel');assert.equal(panel.id,'records');assert(!panel.hidden);
  assert.equal(f.q('[data-go="workspace"]').getAttribute('aria-current'),'page');
  const back=panel.querySelector('a[href="#workspace"]');assert(f.visible(back));
  f.route(back.getAttribute('href'));assert(f.visible(f.q('#workspace')));
 }
 return {workspaceCards:8,verifiedShortcuts:['vocabulary-review','sentence-learning']};
});
const unchanged=checks[0].status==='pass';
const inherited=baseline.checks.map(c=>({...c,validatedOnSHA256:baseline.sha256,scopeUnchanged:unchanged}));
const all=[...inherited,...checks];
const result={sourcePath,sha256:hash(raw),method:'18 full synthetic regressions on the baseline, exact byte equivalence apart from two static shortcut cards, and targeted synthetic routing of both new cards on this SHA. No real browser, layout engine, user localStorage or microphone.',baselineReport:'navigation-ui-tests-before-shortcuts-20260920.json',baselineSHA256:baseline.sha256,checks:all,passed:all.filter(c=>c.status==='pass').length,total:all.length};
fs.writeFileSync(root+'navigation-ui-shortcuts-delta-20260920.json',JSON.stringify({sha256:result.sha256,checks},null,2));
if(unchanged&&checks.every(c=>c.status==='pass'))fs.writeFileSync(root+'navigation-ui-final-tests-20260920.json',JSON.stringify(result,null,2));
console.log(JSON.stringify({sha256:result.sha256,delta:checks,passed:result.passed,total:result.total},null,2));
if(result.passed!==result.total)process.exitCode=1;
