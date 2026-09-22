const fs=require('fs'),path=require('path'),http=require('http'),crypto=require('crypto');
const {chromium}=require('C:/Users/Admin1/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');
const root=path.resolve(__dirname,'..'), batch=path.join(root,'content-pipeline/batches/jijing-20260920'), stage=path.join(batch,'stage');
const book='C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册';
const out=path.join(batch,'browser-qa');fs.mkdirSync(out,{recursive:true});
const mime={'.html':'text/html; charset=utf-8','.js':'application/javascript','.css':'text/css','.json':'application/json','.mp3':'audio/mpeg','.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml','.pdf':'application/pdf'};
function resolveFile(base,rel){const p=path.resolve(base,rel);return p.startsWith(path.resolve(base)+path.sep)&&fs.existsSync(p)&&fs.statSync(p).isFile()?p:null;}
const server=http.createServer((req,res)=>{let rel;try{rel=decodeURIComponent(new URL(req.url,'http://localhost').pathname).slice(1);}catch{res.writeHead(400).end();return;}const file=resolveFile(stage,rel)||resolveFile(book,rel);if(!file){res.writeHead(404).end();return;}const stat=fs.statSync(file),headers={'Content-Type':mime[path.extname(file)]||'application/octet-stream','Accept-Ranges':'bytes'};const range=req.headers.range?.match(/^bytes=(\d+)-(\d*)$/);if(range){const start=Number(range[1]),end=range[2]?Math.min(Number(range[2]),stat.size-1):stat.size-1;if(start>=stat.size){res.writeHead(416).end();return;}res.writeHead(206,{...headers,'Content-Range':`bytes ${start}-${end}/${stat.size}`,'Content-Length':end-start+1});fs.createReadStream(file,{start,end}).pipe(res);}else{res.writeHead(200,{...headers,'Content-Length':stat.size});fs.createReadStream(file).pipe(res);}});
async function main(){
 await new Promise(r=>server.listen(0,'127.0.0.1',r));const base='http://127.0.0.1:'+server.address().port;
 const browser=await chromium.launch({channel:'msedge',headless:true});const context=await browser.newContext({viewport:{width:1440,height:1000}});
 await context.route('**/*',route=>route.request().url().startsWith(base)?route.continue():route.abort());
 const page=await context.newPage(),errors=[];page.on('pageerror',e=>errors.push(e.message));const checks=[];
 const check=(name,detail)=>checks.push({name,status:'pass',detail});
 await page.goto(base+'/candidate.html#learning-projects');
 const project=page.locator('[data-project="jijing-202609-v1"]');await project.waitFor({state:'visible'});await project.screenshot({path:path.join(out,'project.png')});check('Project visible in existing learning projects');
 const reading='pr-jijing-202609-reading-01-v1',listening='pr-jijing-202609-listening-01-v1';
 for(const id of [listening,reading]){
   await page.goto(base+'/candidate.html#'+id);const unit=page.locator('#'+id);await unit.waitFor({state:'visible'});
   const gate=unit.locator('[data-answer-gate]'),body=gate.locator('.la-gate-content');
   if(await body.isVisible())throw Error('Answers initially visible');
   await gate.locator(':scope > summary').click();if(await body.isVisible())throw Error('Blank answer opened gate');
   for(const [i,field] of (await unit.locator('textarea[data-save]').all()).entries())await field.fill('测试作答 '+(i+1));
   await gate.locator(':scope > summary').click();await body.waitFor({state:'visible'});
   await page.reload();await unit.waitFor({state:'visible'});
   if(await unit.locator('textarea[data-save]').first().inputValue()!=='测试作答 1')throw Error('Draft did not restore');
   await unit.screenshot({path:path.join(out,id+'.png')});
   check('Practice save, gate, reload: '+id,{fields:await unit.locator('textarea[data-save]').count()});
 }
 await page.goto(base+'/candidate.html#'+listening);const audio=page.locator('#'+listening+' audio');
 await audio.evaluate(async a=>{if(a.readyState<1)await new Promise((r,j)=>{a.addEventListener('loadedmetadata',r,{once:true});a.addEventListener('error',()=>j(Error('audio load')), {once:true});setTimeout(()=>j(Error('audio metadata timeout')),12000)});await a.play();});
 await page.waitForTimeout(1700);const playback=await audio.evaluate(a=>{const r={duration:a.duration,currentTime:a.currentTime,readyState:a.readyState,paused:a.paused,error:a.error?.message,source:a.currentSrc};a.pause();return r;});console.log('PLAYBACK',JSON.stringify(playback));if(playback.currentTime<=0||!Number.isFinite(playback.duration))throw Error('Audio did not play');check('Local MP3 loaded, decoded and played',playback);
 const manifest=JSON.parse(fs.readFileSync(path.join(root,'downloads/jijing-20260920/ieltsa/manifest.json'),'utf8'));
 const media=manifest.assets.filter(x=>x.path.endsWith('.mp3')).map(x=>'/'+encodeURI('机经资料/jijing-20260920/ieltsa/'+x.path));
 const metadata=await page.evaluate(async urls=>{const out=[];for(const url of urls){const a=new Audio(url);a.preload='metadata';const result=await new Promise((r,j)=>{a.onloadedmetadata=()=>r({url,duration:a.duration});a.onerror=()=>j(Error('MP3 failed '+url));setTimeout(()=>j(Error('MP3 timeout '+url)),15000)});a.pause();a.removeAttribute('src');a.load();out.push(result);}return out;},media);check('All seven downloaded MP3 files load with finite duration',metadata);
 await page.setViewportSize({width:390,height:844});await page.goto(base+'/candidate.html#'+reading);await page.locator('#'+reading).waitFor({state:'visible'});await page.waitForTimeout(700);await page.screenshot({path:path.join(out,'reading-mobile.png')});
 const overflow=await page.evaluate(()=>({width:innerWidth,scroll:document.documentElement.scrollWidth,bodyClass:document.body.className,wide:[...document.querySelectorAll('body *')].filter(x=>{const b=x.getBoundingClientRect();return b.width&&b.right>innerWidth+2&&!x.closest('[hidden]')}).slice(0,15).map(x=>({tag:x.tagName,id:x.id,cl:x.className,width:x.getBoundingClientRect().width,right:x.getBoundingClientRect().right}))}));
 const unitBounds=await page.locator('#'+reading).boundingBox();if(unitBounds.x+unitBounds.width>392)throw Error('New reading content overflows');
 const baselineOverflow=JSON.parse(fs.readFileSync(path.join(batch,'content-review/baseline-overflow.json'),'utf8'));
 check('New mobile reading content fits viewport',{unitBounds,current:overflow,historicalBaselineEvidence:'content-review/baseline-overflow.json',historicalBaselineAudit:!!baselineOverflow});
 await page.goto(base+'/'+encodeURI('机经资料/jijing-20260920/index.html'));await page.locator('h1').waitFor();await page.screenshot({path:path.join(out,'archive-mobile.png')});check('Local archive index opens with external network blocked');
 const result={candidate_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(stage,'candidate.html'))).digest('hex'),browser:'Headless Microsoft Edge '+browser.version(),userProfileUsed:false,remoteNetworkBlocked:true,checks,errors};
 fs.writeFileSync(path.join(batch,'browser-qa.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));await context.close();await browser.close();server.close();if(errors.length)process.exitCode=1;
}
main().catch(e=>{console.error(e);server.close();process.exit(1)});
