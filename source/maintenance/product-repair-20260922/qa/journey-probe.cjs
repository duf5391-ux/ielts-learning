const {start,fs,path}=require('./journey-lib.cjs');
(async()=>{const env=await start({packed:process.argv.includes('--packed'),width:process.argv.includes('--mobile')?390:1440});try{
 const p=env.page;await p.goto(env.base+'#study',{waitUntil:'domcontentloaded'});await env.ready();
 const report={errors:env.errors,pages:[]};const record=async name=>{report.pages.push({name,...await env.snapshot()});await env.shot('baseline-'+name+(process.argv.includes('--mobile')?'-mobile':''));};
 await p.locator('#workspace-navigation button').filter({hasText:/^测试$/}).click();await record('tests');
 for(const id of ['practice-reading-list','study-reading-list','study-listening-list','library','personal-materials']){await env.go(id);await record(id);}
 await env.go('guide');await p.locator('[data-ds-skill="reading"]').click();await record('daily-reading-choice');
 await p.locator('#ds-start').click();await record('daily-reading-start');
 fs.writeFileSync(path.join(__dirname,'probe-'+(process.argv.includes('--mobile')?'mobile':'desktop')+'.json'),JSON.stringify(report,null,2));
 console.log(JSON.stringify(report.pages.map(p=>({name:p.name,hash:p.hash,active:p.active,controls:p.controls.filter(x=>!x.text.includes('开发工作台'))})),null,2));
 }finally{await env.close();}})().catch(e=>{console.error(e);process.exitCode=1});
