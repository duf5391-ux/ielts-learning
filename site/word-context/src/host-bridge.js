// Reading/writing and vocabulary share a verified owner on the same origin.
export function installHostBridge({host=globalThis,getOwner,importSeed}) {
  const reply=(data)=>host.parent.postMessage({...data,version:1},host.location.origin);
  const ready=()=>{if(host.parent!==host)reply({type:'ielts-context-vocabulary-ready',owner:getOwner()});};
  const onMessage=async event=>{
    if(host.parent===host || event.source!==host.parent || event.origin!==host.location.origin)return;
    const data=event.data;
    if(data?.type==='ielts-context-vocabulary-hello'){ready();return;}
    if(data?.type!=='ielts-context-vocabulary-import' || data.version!==1 ||
      typeof data.requestId!=='string' || data.requestId.length>150)return;
    const response={type:'ielts-context-vocabulary-result',requestId:data.requestId,expectedOwner:data.expectedOwner};
    try{
      if(!getOwner() || data.expectedOwner!==getOwner())throw Error('请在两个页面登录同一账号后重试。');
      const importedCount=await importSeed(data.seed,data.expectedOwner,data.markUnknown===true);
      if(data.expectedOwner!==getOwner())throw Error('账号已切换，请在当前账号重新同步。');
      reply({...response,ok:true,importedCount});
    }catch(error){reply({...response,ok:false,error:error.message || '收词同步暂未完成，请重试。'});}
  };
  host.addEventListener('message',onMessage);
  return {ready,dispose:()=>host.removeEventListener('message',onMessage)};
}
