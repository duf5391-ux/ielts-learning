const {start,fs,path}=require('./journey-lib.cjs');
(async()=>{const env=await start({packed:process.argv.includes('--packed'),width:process.argv.includes('--mobile')?390:1440});try{
 await env.page.goto(env.base+'#guide',{waitUntil:'domcontentloaded'});await env.ready();
 const report={errors:env.errors,pages:[]};
 for(const id of ['guide','study','practice','test','workspace','plan','records']){await env.go(id);report.pages.push(await env.snapshot());await env.shot('baseline-'+(process.argv.includes('--mobile')?'mobile':'desktop')+'-'+id);}
 fs.writeFileSync(path.join(__dirname,'inspect-'+(process.argv.includes('--mobile')?'mobile':'desktop')+'.json'),JSON.stringify(report,null,2));
 console.log(report.pages.map(p=>({hash:p.hash,active:p.active.map(x=>({id:x.id,text:x.text.slice(0,11000)})),overflow:p.overflow})));
 }finally{await env.close();}})().catch(e=>{console.error(e);process.exitCode=1});
