const {start,fs,path}=require('./journey-lib.cjs'),assert=require('node:assert/strict');
(async()=>{const result={checks:[]};for(const fail of [false,true]){const env=await start({packed:true,width:390,delay:120,failOnce:fail?'content.':null});try{
 await env.context.addInitScript(()=>{if(!localStorage.getItem('journey-seed')){localStorage.setItem('journey-seed','1');localStorage.setItem('ielts-finished-book-v1',JSON.stringify({version:1,fields:{'workspace-reflection':'progressive isolated old record'},snapshots:{}}));}});
 const p=env.page;await p.goto(env.base+'#records',{waitUntil:'domcontentloaded'});await p.locator('#ielts-progressive-boot').waitFor();
 const before=await p.evaluate(()=>localStorage.getItem('ielts-finished-book-v1'));const choices=await p.locator('[data-pb-route]').evaluateAll(ns=>ns.map(n=>({route:n.dataset.pbRoute,text:n.innerText})));
 if(fail){await p.locator('#ielts-progressive-retry').waitFor({state:'visible'});assert.equal(await p.evaluate(()=>localStorage.getItem('ielts-finished-book-v1')),before);await env.shot('progressive-controlled-failure-mobile');await p.locator('#ielts-progressive-retry').click();}
 else {await p.locator('[data-pb-route="#practice"]').click();}
 await env.ready();assert.equal(await p.locator('[data-save="workspace-reflection"]').inputValue(),'progressive isolated old record');assert.equal(new URL(p.url()).hash,fail?'#records':'#practice');assert.equal(await p.locator('[data-save]').count(),3371);
 result.checks.push({name:fail?'controlled chunk failure preserves old record; reload restores deep link':'choice made during loading opens requested section after initialization',pass:true,choices,route:new URL(p.url()).hash,errors:env.errors});
 }catch(e){result.checks.push({fail,error:e.stack});process.exitCode=1;}finally{await env.close();}}
 fs.writeFileSync(path.join(__dirname,'progressive-results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result,null,2));})();
