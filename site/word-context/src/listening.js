// Selection belongs to the existing account state. It is not a mastery judgement.
const unique = xs => [...new Set(xs)];
const nextSelectionPage = (selection,catalog) => {
  const screened=new Set([...selection.reviewedIds,...selection.selectedIds]);
  const ids=catalog.filter(w=>!screened.has(w.id)).slice(0,10).map(w=>w.id);
  return ids.length?{ids,selectedIds:[]}:null;
};
const validId = id => typeof id === 'string' && /^listen-[a-f0-9]{16}$/.test(id);
export const emptyListening = () => ({selectedIds:[],reviewedIds:[],imports:[],draft:null});
export function validateListening(value) {
  if(value===undefined)return emptyListening();
  if(!value||typeof value!=='object'||Array.isArray(value))return null;
  for(const key of ['selectedIds','reviewedIds'])if(!Array.isArray(value[key])||value[key].some(id=>!validId(id))||unique(value[key]).length!==value[key].length)return null;
  if(!Array.isArray(value.imports)||value.imports.some(id=>typeof id!=='string'||id.length>100))return null;
  if(value.draft!==null&&(!value.draft||!Array.isArray(value.draft.ids)||!Array.isArray(value.draft.selectedIds)||
    !value.draft.ids.length||value.draft.ids.length>20||value.draft.ids.some(id=>!validId(id)||value.reviewedIds.includes(id))||
    unique(value.draft.ids).length!==value.draft.ids.length||unique(value.draft.selectedIds).length!==value.draft.selectedIds.length||
    value.draft.selectedIds.some(id=>!value.draft.ids.includes(id))))return null;
  return structuredClone(value);
}
export function importListening(state,seed,catalog,now=Date.now()) {
  const current=validateListening(state.listening);if(!current)throw Error('听力词本记录无效，原记录保留');
  if(!seed||typeof seed.id!=='string'||seed.id.length>100||!Array.isArray(seed.selectedIds)||!Array.isArray(seed.reviewedIds))throw Error('勾选记录不完整');
  if(current.imports.includes(seed.id))return state;
  const allowed=new Set(catalog.map(w=>w.id));
  if([...seed.selectedIds,...seed.reviewedIds].some(id=>!allowed.has(id)))throw Error('勾选记录与词表不对应');
  const next=structuredClone(state),l=current;
  l.selectedIds=unique([...l.selectedIds,...seed.selectedIds]);
  l.reviewedIds=unique([...l.reviewedIds,...seed.reviewedIds,...seed.selectedIds]);
  l.imports.push(seed.id);
  if(l.draft){l.draft.ids=l.draft.ids.filter(id=>!l.reviewedIds.includes(id));l.draft.selectedIds=l.draft.selectedIds.filter(id=>l.draft.ids.includes(id));if(!l.draft.ids.length)l.draft=null;}
  next.listening=l;next.updatedAt=now;return next;
}
export function listeningSelection(state,catalog,action,now=Date.now()) {
  const l=validateListening(state.listening);if(!l)throw Error('听力词本记录无效，原记录保留');
  const allowed=new Set(catalog.map(w=>w.id));
  if(action.type==='open'){
    if(l.draft)return state;
    l.draft=nextSelectionPage(l,catalog);
    if(!l.draft)return state;
  }else if(action.type==='toggle'){
    if(!l.draft?.ids.includes(action.id)||!allowed.has(action.id))return state;
    l.draft.selectedIds=action.checked?unique([...l.draft.selectedIds,action.id]):l.draft.selectedIds.filter(id=>id!==action.id);
  }else if(action.type==='confirm'){
    if(!l.draft)return state;
    // A concurrent window may already have confirmed a different page.
    if(JSON.stringify(action.ids)!==JSON.stringify(l.draft.ids))return state;
    l.selectedIds=unique([...l.selectedIds,...l.draft.selectedIds]);
    l.reviewedIds=unique([...l.reviewedIds,...l.draft.ids]);
    l.draft=action.continue===true?nextSelectionPage(l,catalog):null;
  }else return state;
  return {...structuredClone(state),listening:l,updatedAt:now};
}
export function dictationQueue(state,catalog,now=Date.now(),newLimit=10,kind='new') {
  const selected=new Set(state.listening?.selectedIds||[]);
  const list=catalog.filter(w=>selected.has(w.id)&&(kind==='new'?!state.progress[w.id]?.spellingAttempts:state.progress[w.id]?.spellingAttempts>0));
  if(kind==='new')return list.sort((a,b)=>state.listening.selectedIds.indexOf(a.id)-state.listening.selectedIds.indexOf(b.id)).slice(0,newLimit);
  // Review is the complete due queue; new-word batch size never caps it.
  const due=list.filter(w=>state.progress[w.id].status!=='familiar'&&Number.isFinite(state.progress[w.id].dueAt)&&state.progress[w.id].dueAt<=now);
  return due.sort((a,b)=>{
    const ap=state.progress[a.id],bp=state.progress[b.id];
    return Number(bp.lastGrade==='forgot')-Number(ap.lastGrade==='forgot')||(ap.dueAt??Infinity)-(bp.dueAt??Infinity)||state.listening.selectedIds.indexOf(a.id)-state.listening.selectedIds.indexOf(b.id);
  });
}

// Audio provenance belongs to the content manifest, never to account progress.
// Stable word IDs keep old sessions valid when a recording is replaced.
export function withListeningAudio(catalog,manifest) {
  if(!manifest||!Array.isArray(manifest.files))throw Error('听力音源信息暂未加载，请刷新重试。');
  const files=new Map(manifest.files.map(file=>[file.id,file]));
  return catalog.map(word=>{
    const file=files.get(word.id),kind=file?.kind||manifest.kind,locale=file?.locale||manifest.locale;
    if(!file||file.term!==word.term||!/^[a-f0-9]{64}$/i.test(file.sha256||'')||
      !['dictionary-human','offline-synthetic','neural-synthetic'].includes(kind)||!/^en-(GB|US)$/.test(locale||''))
      throw Error('听力词条与音源信息不一致，请刷新重试。');
    const accent=locale==='en-GB'?'英式':'美式';
    return {...word,audio:{kind,locale,sha256:file.sha256,
      label:kind==='dictionary-human'?`剑桥词典 · ${accent}真人`:kind==='neural-synthetic'?(file.voice==='en-GB-SoniaNeural'?'英式 Sonia · 合成音':`${accent}合成音`):'原合成音 · 词典录音待补'}};
  });
}

// Require an English system voice, report failure, and invalidate stale playback.
export function createPronunciation(host=globalThis) {
  let generation=0,active=null,media=null;
  function cancel(error=new Error('已停止播放')){generation++;active?.reject(error);active=null;if(media){media.onended=null;media.onerror=null;media.pause();media.removeAttribute?.('src');media.load?.();media=null;}host.speechSynthesis?.cancel();}
  async function play(text,language='en-GB',audioURL=null){
    cancel();const owner=generation;
    if(audioURL&&!host.Audio)throw Error('当前浏览器不支持录音播放，请换用支持音频的浏览器');
    if(audioURL&&host.Audio){
      const audio=media=new host.Audio(audioURL);audio.preload='auto';
      return new Promise((resolve,reject)=>{
        const fail=message=>{if(owner!==generation)return;cancel(new Error(message));};
        const timer=setTimeout(()=>fail('音频加载超时，请重播'),20000);
        active={reject:error=>{clearTimeout(timer);reject(error);}};
        audio.onended=()=>{clearTimeout(timer);if(owner===generation){active=null;media=null;resolve();}};
        audio.onerror=()=>fail('音频暂时未能播放，请重播；本题还未计分');
        try{Promise.resolve(audio.play()).catch(()=>fail('音频未能开始，请点击播放发音重试'));}catch{fail('音频未能开始，请点击播放发音重试');}
      });
    }
    const synth=host.speechSynthesis;
    if(!synth||!host.SpeechSynthesisUtterance)throw Error('当前浏览器不支持发音，请换用支持英语语音的浏览器');
    let voices=synth.getVoices();
    if(!voices.length)await new Promise(resolve=>{const done=()=>{clearTimeout(timer);synth.removeEventListener?.('voiceschanged',done);resolve();};const timer=setTimeout(done,1500);synth.addEventListener?.('voiceschanged',done);});
    if(owner!==generation)throw Error('已停止播放');
    voices=synth.getVoices();const voice=voices.find(v=>v.lang.toLowerCase()===language.toLowerCase())||voices.find(v=>/^en[-_]/i.test(v.lang));
    if(!voice)throw Error('没有可用的英语发音，请在设备语音设置中添加英语语音后重试');
    return new Promise((resolve,reject)=>{
      const u=new host.SpeechSynthesisUtterance(text);u.lang=voice.lang;u.voice=voice;u.rate=.85;
      const timer=setTimeout(()=>{if(owner===generation)cancel(new Error('发音超时，请重播'));},20000);
      active={reject:error=>{clearTimeout(timer);reject(error);}};
      u.onend=()=>{clearTimeout(timer);if(owner===generation){active=null;resolve();}};
      u.onerror=()=>{clearTimeout(timer);if(owner===generation){active=null;reject(new Error('发音失败，请重播；未计入听写成绩'));}};
      synth.speak(u);
    });
  }
  return {play,cancel};
}
