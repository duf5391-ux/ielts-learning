// Real isolated browser checks for the fixed-snapshot new-content subset.
const fs=require('fs'),path=require('path'),http=require('http'),assert=require('assert'),crypto=require('crypto');
const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const here=__dirname,root=path.resolve(here,'../..'),stage=JSON.parse(fs.readFileSync(path.join(here,'stage-check.json'),'utf8'));
const book=path.dirname(stage.source),candidate=process.argv[2]?path.resolve(process.argv[2]):stage.candidate,units=JSON.parse(fs.readFileSync(path.join(here,'new-units.json'),'utf8')).units;
const reportStem=process.argv[2]?'browser-qa-combined':'browser-qa';
const out=path.join(here,reportStem);fs.mkdirSync(out,{recursive:true});
const mime={'.html':'text/html; charset=utf-8','.js':'application/javascript','.css':'text/css','.json':'application/json','.mp3':'audio/mpeg','.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml'};
function safeFile(dir,rel){const p=path.resolve(dir,rel);return p.startsWith(path.resolve(dir)+path.sep)&&fs.existsSync(p)&&fs.statSync(p).isFile()?p:null;}
const server=http.createServer((req,res)=>{
 let rel;try{rel=decodeURIComponent(new URL(req.url,'http://localhost').pathname).slice(1)}catch{res.writeHead(400).end();return}
 const file=['candidate.html','开始学习.html'].includes(rel)?candidate:safeFile(path.join(here,'assets'),rel)||safeFile(book,rel);
 if(!file){res.writeHead(404).end();return}res.writeHead(200,{'Content-Type':mime[path.extname(file)]||'application/octet-stream'});fs.createReadStream(file).pipe(res);
});
(async()=>{
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const context=await browser.newContext({viewport:{width:1440,height:1000},serviceWorkers:'block'});
 await context.route('**/*',r=>r.request().url().startsWith(base)?r.continue():r.abort());
 const page=await context.newPage(),errors=[],checks=[];page.on('pageerror',e=>errors.push(e.message));
 const check=(name,detail)=>checks.push({name,status:'pass',detail});
 await page.goto(base+'/candidate.html#learning-projects');
 const project=page.locator('[data-project="jiufen-reviewed-20260921-v1"]');await project.waitFor({state:'visible'});
 assert.equal(await project.locator('a[href^="#pr-jiufen-"]').count(),4);await project.screenshot({path:path.join(out,'new-project.png')});check('New-content project visible with four actual new routes');
 for(const u of units){
  await page.goto(base+'/candidate.html#practice-'+u.skill+'-list');await page.locator('[data-catalog-unit="'+u.id+'"]').waitFor({state:'visible'});
  await page.goto(base+'/candidate.html#'+u.id);let unit=page.locator('#'+u.id);await unit.waitFor({state:'visible'});
  assert((await unit.locator('.jj-update-meta').innerText()).includes('新内容'));
  const gate=unit.locator('[data-answer-gate]'),content=gate.locator('.la-gate-content');
  assert(!await content.isVisible());await gate.locator(':scope > summary').click();assert(!await content.isVisible(),'Blank attempt exposed feedback');
  const fields=await unit.locator('textarea[data-save]').all();
  for(let i=0;i<fields.length;i++)await fields[i].fill('合成检查 '+u.id+' '+(i+1));
  await gate.locator(':scope > summary').click();await content.waitFor({state:'visible'});
  await page.reload();unit=page.locator('#'+u.id);await unit.waitFor({state:'visible'});
  assert.equal(await unit.locator('textarea[data-save]').first().inputValue(),'合成检查 '+u.id+' 1');
  check('Category, direct route, blank gate, save, feedback, reload: '+u.id,{fields:fields.length});
 }
 await page.setViewportSize({width:390,height:844});
 for(const u of [units[0],units[1]]){
  await page.goto(base+'/candidate.html#'+u.id);const unit=page.locator('#'+u.id);await unit.waitFor({state:'visible'});
  const bounds=await unit.boundingBox();assert(bounds.x>=-1&&bounds.x+bounds.width<=391,'Mobile unit overflow');
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,'Page overflow');
  await page.screenshot({path:path.join(out,u.skill+'-mobile.png')});check('Mobile content fits: '+u.skill,bounds);
 }
 for(const rel of ['机经资料/jiufen-reviewed-20260921/index.html','机经资料/jijing-20260920/index.html','机经资料/jijing-20260920/writing-task2.html']){
  const response=await page.goto(base+'/'+encodeURI(rel));assert.equal(response.status(),200);await page.locator('h1').waitFor();
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1),false,'Asset page overflows');
  check('Material index opens at mobile width: '+rel);
 }
 assert.equal(errors.length,0,'Browser errors: '+errors.join('; '));
 const report={candidateSha256:crypto.createHash('sha256').update(fs.readFileSync(candidate)).digest('hex'),browser:'Headless Microsoft Edge '+browser.version(),isolatedStorage:true,userProfileUsed:false,remoteNetworkBlocked:true,checks,errors};
 fs.writeFileSync(path.join(here,reportStem+'.json'),JSON.stringify(report,null,2));console.log(JSON.stringify(report,null,2));
 await context.close();await browser.close();server.close();
})().catch(e=>{console.error(e);server.close();process.exit(1)});
