from pathlib import Path
HERE=Path(__file__).resolve().parent
source=(HERE/'qa.cjs').read_text(encoding='utf8')
source=source.replace("'qa-results.json'","'qa-combined.json'")
for name in ['export-new-task.txt','mobile-directory.png','mobile-draft.png','desktop-draft.png']:
 source=source.replace("'"+name+"'","'combined-"+name+"'")
source=source.replace("const report={candidate,candidateSha256:","const report={candidate,candidate_sha256:require('crypto').createHash('sha256').update(bytes).digest('hex'),candidateSha256:")
extra='''
 await check('combined mobile main navigation More → writing catalogue → search independent-living → draft and resume',async p=>{
  await route(p,'study');
  await p.locator('#product-more').click();
  await p.locator('#workspace-navigation [data-go="writing-workbench"]').click();
  await p.locator('.ww-directory').waitFor({state:'visible'});
  assert.equal(await p.locator('.ww-directory-row:visible').count(),32);
  for(const q of questions){const row=p.locator('[data-ww-pick="'+q.id+'"]');const text=await row.textContent();assert(text.includes(q.title),q.id);assert(text.includes(q.source.title),q.id);assert(text.includes('参考置信度：'+q.confidence.split('（')[0]),q.id);}
  await p.locator('#ww-directory-search').fill('独居');
  const id='ww-ieltsa-writing-202609-10-2-reference-v1';
  await p.locator('[data-ww-pick="'+id+'"]').click();
  await field(p,id+'-first').waitFor({state:'visible'});await p.waitForTimeout(150);
  const box=await field(p,id+'-first').boundingBox();assert(box.y>=0&&box.y<844,JSON.stringify(box));
  assert(await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await field(p,id+'-first').fill('COMBINED MOBILE NAVIGATION DRAFT');
  await p.screenshot({path:path.join(__dirname,'combined-mobile-entry-chain.png')});
  await p.reload({waitUntil:'domcontentloaded'});
  assert.equal(await field(p,id+'-first').inputValue(),'COMBINED MOBILE NAVIGATION DRAFT');
  assert(await p.locator('#'+id+'-draft').isVisible());
 },{mobile:true});
'''
source=source.replace(" await check('32 task entries",extra+" await check('32 task entries",1)
(HERE/'qa_combined.cjs').write_text(source,encoding='utf8',newline='')
