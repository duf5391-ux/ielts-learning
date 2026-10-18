// A serializable, optional within-group practice round. The caller owns SRS.
const TYPES=new Set(['meaning','word','recall','spelling']);
const safeId=id=>typeof id==='string'&&id.length>0&&id.length<200&&!['__proto__','prototype','constructor'].includes(id);
const plain=value=>!!value&&typeof value==='object'&&!Array.isArray(value)&&Object.getPrototypeOf(value)===Object.prototype;
const copy=value=>structuredClone(value);
const unique=values=>[...new Set(values)];
const integer=value=>Number.isSafeInteger(value)&&value>=0;
const normalize=value=>String(value||'').normalize('NFKC').trim().toLowerCase()
  .replace(/[’‘]/g,"'").replace(/[‐‑–—]/g,'-').replace(/\s+/g,' ');
const meaningParts=value=>unique(String(value||'').split(/[；;，,、/\n]+/u)
  .map(part=>normalize(part).replace(/^(?:(?:n|v|vt|vi|adj|adv|prep|conj|pron)(?:\.\s*|\s+))+/i,'').replace(/[。.!！?？\s]+/g,''))
  .filter(Boolean));
const overlaps=(a,b)=>a.some(part=>b.includes(part));
function posFamily(value){
  const part=normalize(value).split(/[\s.;；/,]+/)[0];
  if(['v','vt','vi','verb'].includes(part))return 'v';
  return ({noun:'n',adjective:'adj',adverb:'adv',preposition:'prep'})[part]||part;
}
function hash(value){let result=2166136261;for(const character of String(value)){result^=character.codePointAt(0);result=Math.imul(result,16777619);}return (result>>>0).toString(36);}
const text=value=>typeof value==='string'&&value.length<=8000;
const recipeValid=recipe=>Array.isArray(recipe)&&recipe.length>0&&recipe.length<=12&&recipe.every(type=>TYPES.has(type));
const wordsMap=words=>new Map((Array.isArray(words)?words:[]).filter(word=>word&&safeId(word.id)&&typeof word.term==='string'&&word.term.trim()).map(word=>[word.id,word]));

function makeTemplate(word,step,requestedType,words,seed){
  const term=String(word.term),meaning=String(word.meaning||''),pos=String(word.pos||'');
  let type=requestedType,options=[];
  if(type==='meaning'||type==='word'){
    const meanings=meaningParts(meaning),terms=new Set([normalize(term)]),usedMeanings=[...meanings];
    const candidates=words.filter(candidate=>candidate.id!==word.id&&String(candidate.meaning||'').trim())
      .sort((a,b)=>Number(posFamily(b.pos)===posFamily(pos)&&!!posFamily(pos))-Number(posFamily(a.pos)===posFamily(pos)&&!!posFamily(pos))||
        hash(`${seed}:${word.id}:${step}:${a.id}`).localeCompare(hash(`${seed}:${word.id}:${step}:${b.id}`))||a.id.localeCompare(b.id));
    if(meaning.trim())options.push({id:word.id,label:type==='meaning'?meaning:term});
    for(const candidate of candidates){
      if(options.length>=4)break;
      const candidateTerm=normalize(candidate.term),parts=meaningParts(candidate.meaning);
      if(terms.has(candidateTerm)||!parts.length||overlaps(parts,usedMeanings))continue;
      const label=type==='meaning'?String(candidate.meaning):String(candidate.term);
      if(options.some(option=>normalize(option.label)===normalize(label)))continue;
      options.push({id:candidate.id,label});terms.add(candidateTerm);usedMeanings.push(...parts);
    }
    if(!meaning.trim()||options.length<2){type='recall';options=[];}
    else options.sort((a,b)=>hash(`${seed}:option:${word.id}:${step}:${a.id}`).localeCompare(hash(`${seed}:option:${word.id}:${step}:${b.id}`))||a.id.localeCompare(b.id));
  }
  return {wordId:word.id,step,requestedType,type,term,meaning,pos,
    prompt:type==='meaning'||type==='recall'?term:meaning,
    options,correctAnswer:type==='meaning'||type==='word'?word.id:type==='recall'?'known':term,
    acceptedAnswers:type==='spelling'?unique([term,...(Array.isArray(word.acceptedSpellings)?word.acceptedSpellings.filter(text):[])]):[],
    ...(type!==requestedType?{fallbackReason:'insufficient-options'}:{})};
}

function chooseNext(round){
  const pending=round.progress.filter(item=>!item.completed);
  if(!pending.length){round.complete=true;round.question=null;return;}
  const eligible=pending.filter(item=>item.eligibleAfter<=round.turn);
  const spacingLimited=pending.length>1&&!eligible.length;
  const candidates=pending.length===1?pending:eligible.length?eligible:pending;
  const chosen=[...candidates].sort((a,b)=>a.lastTurn-b.lastTurn||round.wordIds.indexOf(a.wordId)-round.wordIds.indexOf(b.wordId))[0];
  const template=round.templates.find(item=>item.wordId===chosen.wordId&&item.step===chosen.step);
  round.question={...copy(template),id:`mixed-${hash(round.seed)}-${round.turn+1}-${hash(chosen.wordId)}-${chosen.step}`,
    turn:round.turn+1,spacingLimited};
  round.complete=false;
}

/** Recipe steps run consecutively for each word; a failure restarts that word.
 * Each presented question and all later templates are saved in the round.
 */
export function createMixedRound(words,wordIds,recipe,seed='mixed'){
  const map=wordsMap(words),ids=unique(Array.isArray(wordIds)?wordIds:[]);
  if(!Array.isArray(wordIds)||wordIds.some(id=>!safeId(id)||!map.has(id))||!recipeValid(recipe)||typeof seed!=='string'||seed.length>500)
    throw new Error('本组练习配置需要有效词条和题型。');
  const round={version:1,seed,recipe:[...recipe],wordIds:ids,
    progress:ids.map(wordId=>({wordId,step:0,completed:false,eligibleAfter:0,lastTurn:-1})),
    templates:ids.flatMap(id=>recipe.map((type,step)=>makeTemplate(map.get(id),step,type,[...map.values()],seed))),
    question:null,feedback:null,attempts:[],turn:0,complete:false};
  chooseNext(round);return round;
}

export function currentMixedQuestion(round){return round?.complete?null:round?.question||null;}

function answerAllowed(question,answer){
  if(question.type==='meaning'||question.type==='word')return answer===null||question.options.some(option=>option.id===answer);
  if(question.type==='recall')return answer==='known'||answer==='forgot';
  return typeof answer==='string'&&answer.length<=8000;
}
function answerCorrect(question,answer,hinted){
  if(hinted)return false;
  if(question.type==='spelling')return question.acceptedAnswers.some(accepted=>normalize(accepted)===normalize(answer));
  return answer===question.correctAnswer;
}

/** answer is an option ID (null means unknown), known/forgot, or spelling text.
 * hinted=true saves the input and counts the attempt as failed. Only NEXT moves.
 */
export function submitMixedAnswer(round,{questionId,answer,hinted=false}={},_words){
  const question=currentMixedQuestion(round);
  if(!question||round.feedback||question.id!==questionId||typeof hinted!=='boolean'||!answerAllowed(question,answer))return round;
  const next=copy(round),correct=answerCorrect(question,answer,hinted),turn=next.turn+1;
  const progress=next.progress.find(item=>item.wordId===question.wordId);
  progress.step=correct?progress.step+1:0;progress.completed=progress.step===next.recipe.length;
  progress.lastTurn=turn;progress.eligibleAfter=correct?turn:turn+2;
  const record={questionId:question.id,wordId:question.wordId,type:question.type,requestedType:question.requestedType,
    step:question.step,turn,correct,selectedAnswer:answer,hinted};
  next.turn=turn;next.attempts.push(copy(record));next.feedback=record;
  return next;
}

export function advanceMixedRound(round,_words){
  if(!round?.feedback||round.complete)return round;
  const next=copy(round);next.feedback=null;chooseNext(next);return next;
}

function validTemplate(template,recipe,ids){
  if(!plain(template)||!ids.has(template.wordId)||!integer(template.step)||template.step>=recipe.length||template.requestedType!==recipe[template.step]||
      !TYPES.has(template.type)||![template.term,template.meaning,template.pos,template.prompt,template.correctAnswer].every(text)||!template.term.trim()||
      !Array.isArray(template.options)||!Array.isArray(template.acceptedAnswers)||template.acceptedAnswers.some(answer=>!text(answer)))return false;
  if(template.type!==template.requestedType&&(template.type!=='recall'||!['meaning','word'].includes(template.requestedType)||template.fallbackReason!=='insufficient-options'))return false;
  if(template.prompt!==(template.type==='meaning'||template.type==='recall'?template.term:template.meaning))return false;
  if(template.type==='meaning'||template.type==='word')return template.options.length>=2&&template.options.length<=4&&template.correctAnswer===template.wordId&&
    template.options.every(option=>plain(option)&&safeId(option.id)&&text(option.label)&&option.label.trim())&&
    unique(template.options.map(option=>option.id)).length===template.options.length&&
    unique(template.options.map(option=>normalize(option.label))).length===template.options.length&&
    template.options.some(option=>option.id===template.correctAnswer&&option.label===(template.type==='meaning'?template.meaning:template.term))&&template.acceptedAnswers.length===0;
  return template.options.length===0&&(template.type==='recall'
    ? template.correctAnswer==='known'&&template.acceptedAnswers.length===0
    : template.correctAnswer===template.term&&template.acceptedAnswers.length>0&&template.acceptedAnswers.includes(template.term));
}

/** Returns a validated clone or null. queue is the containing session's IDs. */
export function validateMixedRound(round,queue){
  try{
    if(!plain(round)||round.version!==1||typeof round.seed!=='string'||round.seed.length>500||!recipeValid(round.recipe)||
        !Array.isArray(round.wordIds)||round.wordIds.some(id=>!safeId(id))||unique(round.wordIds).length!==round.wordIds.length||
        !Array.isArray(round.progress)||!Array.isArray(round.templates)||!Array.isArray(round.attempts)||!integer(round.turn)||
        round.turn!==round.attempts.length||typeof round.complete!=='boolean')return null;
    const ids=new Set(round.wordIds),allowed=Array.isArray(queue)?new Set(queue):null;
    if(allowed&&round.wordIds.some(id=>!allowed.has(id))||round.progress.length!==ids.size||
        round.progress.some((item,index)=>!plain(item)||item.wordId!==round.wordIds[index]||!integer(item.step)||item.step>round.recipe.length||
          item.completed!==(item.step===round.recipe.length)||!integer(item.eligibleAfter)||!Number.isInteger(item.lastTurn)||item.lastTurn< -1||item.lastTurn>round.turn)||
        round.templates.length!==ids.size*round.recipe.length||round.templates.some(template=>!validTemplate(template,round.recipe,ids)))return null;
    const templates=new Map(round.templates.map(template=>[`${template.wordId}\0${template.step}`,template]));
    if(templates.size!==round.templates.length)return null;
    const derived=new Map(round.wordIds.map(wordId=>[wordId,{wordId,step:0,completed:false,eligibleAfter:0,lastTurn:-1}]));
    const questionIds=new Set();
    for(let index=0;index<round.attempts.length;index++){
      const attempt=round.attempts[index],progress=derived.get(attempt?.wordId),template=templates.get(`${attempt?.wordId}\0${attempt?.step}`);
      if(!plain(attempt)||!progress||progress.completed||!template||attempt.turn!==index+1||attempt.step!==progress.step||
          typeof attempt.questionId!=='string'||questionIds.has(attempt.questionId)||attempt.type!==template.type||attempt.requestedType!==template.requestedType||
          typeof attempt.correct!=='boolean'||typeof attempt.hinted!=='boolean'||!answerAllowed(template,attempt.selectedAnswer)||
          attempt.correct!==answerCorrect(template,attempt.selectedAnswer,attempt.hinted))return null;
      const expectedId=`mixed-${hash(round.seed)}-${index+1}-${hash(attempt.wordId)}-${attempt.step}`;
      if(attempt.questionId!==expectedId)return null;
      questionIds.add(attempt.questionId);progress.step=attempt.correct?progress.step+1:0;
      progress.completed=progress.step===round.recipe.length;progress.lastTurn=index+1;
      progress.eligibleAfter=attempt.correct?index+1:index+3;
    }
    if(round.progress.some(progress=>Object.keys(derived.get(progress.wordId)).some(key=>progress[key]!==derived.get(progress.wordId)[key])))return null;
    const allComplete=round.progress.every(item=>item.completed);
    if(round.complete)return allComplete&&round.question===null&&round.feedback===null?copy(round):null;
    const question=round.question,template=templates.get(`${question?.wordId}\0${question?.step}`);
    if(!template||!plain(question)||typeof question.spacingLimited!=='boolean'||!integer(question.turn)||
        question.id!==`mixed-${hash(round.seed)}-${question.turn}-${hash(question.wordId)}-${question.step}`||
        Object.keys(template).some(key=>JSON.stringify(question[key])!==JSON.stringify(template[key])))return null;
    if(round.feedback===null){
      const progress=derived.get(question.wordId);
      if(allComplete||progress.completed||question.step!==progress.step||question.turn!==round.turn+1)return null;
    }else{
      const last=round.attempts.at(-1);
      if(!last||!plain(round.feedback)||question.id!==last.questionId||question.turn!==round.turn||
          Object.keys(last).some(key=>round.feedback[key]!==last[key])||Object.keys(round.feedback).some(key=>round.feedback[key]!==last[key]))return null;
    }
    return copy(round);
  }catch{return null;}
}
