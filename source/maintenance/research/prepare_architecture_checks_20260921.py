from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'architecture-repair-20260921/qa.cjs'
s=p.read_text(encoding='utf8')
s=s.replace("const target=process.argv[2]||'candidate',live=", "const target=process.argv[2]||'candidate',combined=target==='combined',candidateFile=combined?'combined.html':'candidate.html',assetRoot=path.resolve(here,'../content-pipeline/batches/jiufen-jijing-20260921/reviewed-assets'),live=")
s=s.replace("target==='candidate'?null:path.resolve(target)","(target==='candidate'||combined)?null:path.resolve(target)")
s=s.replace("path.join(here,'candidate.html')","path.join(here,candidateFile)")
s=s.replace(":path.resolve(book,rel);const allowed",":fs.existsSync(path.join(assetRoot,rel))?path.join(assetRoot,rel):path.resolve(book,rel);const allowed")
s=s.replace("file.startsWith(allowed+'/')","file.startsWith(allowed+'/')||file.startsWith(assetRoot+path.sep)")
s=s.replace(".count(),3368)",".count(),target==='candidate'?3368:3371)")
s=s.replace("live?'live':target==='candidate'?'candidate':'packed'","live?'live':combined?'combined':target==='candidate'?'candidate':'packed'")
s=s.replace("assert.deepEqual(errors,[]);await context.close();", """if(combined||live||target!=='candidate'){
 const pkg=JSON.parse(fs.readFileSync(path.join(assetRoot,'../cleaned-luna-20260921/reviewed-package.json'),'utf8'));
 for(const u of pkg.units){
  for(const skill of ['reading','shared']){
   await go(page,'study-'+skill+'-list');const card=page.locator('[data-catalog-unit="'+u.id+'"]');
   assert(await card.isVisible());assert.match(await card.locator('.content-entry-metadata').innerText(),/4\\/5.*置信度低.*九分学长/);
   await card.locator('a[href="#'+u.id+'"]').first().click();await page.waitForTimeout(100);
   assert.equal(await page.locator('.la-focus-nav a').getAttribute('href'),'#study-'+skill+'-list');
  }
  const unit=page.locator('#'+u.id);assert.equal(await unit.locator('.content-entry-metadata').count(),0);
  assert.match(await unit.innerText(),/读懂这一段/);await unit.locator('details summary').click();
  const href=await unit.locator('details a').getAttribute('href');const response=await context.request.get(new URL(href,base).href);assert.equal(response.status(),200);
  const original=await response.text();assert(original.includes(u.sourceTitle));assert(original.includes(u.id));
  await unit.locator('input[type=checkbox]').check();await page.reload({waitUntil:'domcontentloaded'});await ready(page);assert(await page.locator('#'+u.id+' input[type=checkbox]').isChecked());
 }
 add('三份精读从阅读和背景共用同一单元，入口标注、上下文、全文和保存恢复通过');
 await go(page,pkg.units[0].id);await page.screenshot({path:path.join(here,'combined-reading-mobile.png'),fullPage:true});
}
assert.deepEqual(errors,[]);await context.close();""")
p.write_text(s,encoding='utf8')
# Health checks against the same assembled candidate; existing behavioral checks
# retained; only expected extra fields/units change.
p=ROOT/'feature-fixes-20260921/qa_release.cjs';s=p.read_text(encoding='utf8')
s=s.replace('.count(),3368)','.count(),3371)').replace('.count(),224)','.count(),227)')
s=s.replace('All 3368 saved fields and 224 learning units assembled','All 3371 saved fields and 227 learning units assembled')
(ROOT/'architecture-repair-20260921/qa_health.cjs').write_text(s,encoding='utf8')
# Make the additional tensor layers visible and inspectable.
p=ROOT/'research/build_content_tensor_20260921.py';s=p.read_text(encoding='utf8')
s=s.replace("entry:'#73cce6'}", "entry:'#73cce6',record:'#c799e8',exposure:'#ecad88',artifact:'#87b2bd'}")
s=s.replace("entry:'现有入口'}", "entry:'现有入口',record:'记录绑定 / 契约',exposure:'曝光契约',artifact:'派生物件'}")
s=s.replace("new Set(['root','source','fragment','activity','entry'])", "new Set(['root','source','fragment','activity','entry','record','exposure','artifact'])")
s=s.replace('activity:240,entry:410','activity:240,entry:410,record:600,exposure:740,artifact:-80')
p.write_text(s,encoding='utf8')
# Preserve collaborator input; root review fixes an actual numeric error.
p=ROOT/'content-pipeline/batches/jiufen-jijing-20260921/cleaned-luna-20260921/listening-reviewed.json';d=json.loads(p.read_text(encoding='utf8'))
for u in d['units']:
 u['unitDifficulty'].update(assessor='Luna; root text review',version=1,basis='transcript and task only; audio delivery difficulty unknown')
 u['useStatus'].update(partialTest='blocked-pending-answer-audio-and-exposure-validation')
 if u['sourceId']=='2033383348044922882':
  q=u['questions'][1];q.update(answer='077896245',acceptableVariants=['077896245'],reviewStatus='transcript-supported-reference-audio-unverified')
  q['explanation']='zero double seven means 0-7-7, followed by 896245. The prior 007896245 was a normalization error. Original audio still requires listening.'
  u['questions'][0]['acceptableVariants']=['Elsinore']
d['rootReview']={'status':'text-reviewed-audio-pending','correction':'Lifeguard Q2: 007896245 -> 077896245; spoken-out multiword answer is not an acceptable one-number written response','autoScoring':False,'testEligible':False}
(p.parent/'listening-root-reviewed.json').write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
task=ROOT/'research/kimi-content-quality-task-20260921.json';d=json.loads(task.read_text());d.update(status='completed',executor='kimi-app',verifiedModel='k3-agent',reviewRead=True);task.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8')
