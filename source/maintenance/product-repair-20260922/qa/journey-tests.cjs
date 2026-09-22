const {start,fs,path}=require('./journey-lib.cjs');
(async()=>{const env=await start({packed:process.argv.includes('--packed'),width:process.argv.includes('--mobile')?390:1440});try{
 const p=env.page;await p.goto(env.base+'#tests',{waitUntil:'domcontentloaded'});await env.ready();
 const report={errors:env.errors,pages:[]};const record=async name=>{report.pages.push({name,...await env.snapshot()});await env.shot('baseline-'+name+(process.argv.includes('--mobile')?'-mobile':''));};
 for(const id of ['test-reading','test-listening','test-writing','test-speaking']){await env.go(id);await p.locator('#'+id+' button').filter({hasText:'开始本次测试'}).click();await record(id);}
 const targets=await p.evaluate(()=>[...document.querySelectorAll('[data-go]')].map(x=>({text:x.textContent,route:x.dataset.go})));report.targets=targets;
 fs.writeFileSync(path.join(__dirname,'tests-inspection.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify(report.pages.map(p=>({name:p.name,hash:p.hash,active:p.active,controls:p.controls.filter(x=>x.id||x.href&&!['#study','#guide','#plan','#records'].includes(x.href))})),null,2));
 }finally{await env.close();}})().catch(e=>{console.error(e);process.exitCode=1});
