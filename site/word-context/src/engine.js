/**
 * Independent, word-level learning domain. No DOM, storage, host-site or network code.
 * Intervals below are an explicit local approximation, NOT BBDC's private algorithm.
 * New forgotten words stay in learning; admitted forgotten reviews = 10 minutes.
 * Successive remembered reviews = 1/3/7/14/30/60 days.
 * Spelling can admit an encountered word, but does not replace an existing schedule.
 */
import {normalizeLookupTerm, personalWordId as lookupPersonalWordId} from './lookup.js?v=509356376181';
import {validateListening} from './listening.js?v=509356376181';
import {getDailyPlan,ensureDailyPlan,validDailyPlan} from './daily-plan.js?v=509356376181';
export {getDailyPlan,ensureDailyPlan} from './daily-plan.js?v=509356376181';
import {createMixedRound,currentMixedQuestion,submitMixedAnswer,advanceMixedRound,validateMixedRound} from './mixed-practice.js?v=509356376181';

export const SCHEMA_VERSION = 1;
export const DEFAULT_SETTINGS = Object.freeze({
  newPerDay: 25, groupSize: 10, spellAfterLearn: true, spellAfterReview: false,
  learningPlanVersion: 1, studyTopic: '', mixedPractice:true,
  voice: 'en-GB', autoSpeak: false,
});
export const REVIEW_INTERVAL_DAYS = Object.freeze([1, 3, 7, 14, 30, 60]);
const DAY = 86400000;
const MODES = new Set(['learn', 'review', 'practice', 'spelling', 'dictation']);
export const isSpellingMode = mode => mode === 'spelling' || mode === 'dictation';
const PHASES = new Set(['memory', 'mixed', 'spelling', 'spelling-result', 'complete']);
const validRecipe = recipe => Array.isArray(recipe) && recipe.length>0 && recipe.length<=4 && unique(recipe).length===recipe.length && recipe.every(type=>['meaning','word','spelling','recall'].includes(type));
const STATUSES = new Set(['learning', 'review', 'familiar']);
const forbiddenKeys = new Set(['__proto__', 'prototype', 'constructor']);
const safeId = value => typeof value === 'string' && value.length > 0 && value.length < 200 && !forbiddenKeys.has(value);
const copy = value => structuredClone(value);
const unique = values => [...new Set(values)];
const time = value => {
  const result = value instanceof Date ? value.getTime() : typeof value === 'string' ? Date.parse(value) : Number(value);
  return Number.isFinite(result) ? result : Date.now();
};
const integer = (value, min, max, fallback) => Number.isFinite(Number(value))
  ? Math.max(min, Math.min(max, Math.floor(Number(value)))) : fallback;
const wordMap = words => new Map((Array.isArray(words) ? words : []).filter(w => w && safeId(w.id)).map(w => [w.id, w]));
const BANK_SOURCES = new Set(['local-dictionary', 'target303', 'unavailable', 'user']);
const BANK_TOKEN = /^[\p{L}\p{M}]+(?:['-][\p{L}\p{M}]+)*$/u;
export const normalizeBankTerm = normalizeLookupTerm;
export const personalWordId = lookupPersonalWordId;
const plain = value => !!value && typeof value === 'object' && !Array.isArray(value) && Object.getPrototypeOf(value) === Object.prototype;
const textField = (value, max) => typeof value === 'string' && value.length <= max;

function bankWord(value) {
  if (!plain(value) || !safeId(value.id) || !textField(value.term, 100) || !BANK_TOKEN.test(value.term) ||
      value.term !== normalizeBankTerm(value.term) || !textField(value.meaning, 8000) || !textField(value.pos, 100) ||
      !textField(value.phonetic, 300) || !BANK_SOURCES.has(value.dictionarySource) || typeof value.unresolved !== 'boolean') return null;
  if (value.baseWordId !== null && (!safeId(value.baseWordId) || value.baseWordId.startsWith('pw-') ||
      value.id !== value.baseWordId || value.dictionarySource !== 'target303')) return null;
  if (value.baseWordId === null && (value.id !== personalWordId(value.term) || value.dictionarySource === 'target303')) return null;
  for (const name of ['forms', 'acceptedSpellings']) {
    if (!Array.isArray(value[name]) || value[name].length > 100 || value[name].some(v => !textField(v, 100) || !BANK_TOKEN.test(normalizeBankTerm(v))) ||
        unique(value[name]).length !== value[name].length) return null;
  }
  if (value.ready !== undefined && typeof value.ready !== 'boolean') return null;
  return {id:value.id, baseWordId:value.baseWordId, term:value.term, meaning:value.meaning, pos:value.pos, phonetic:value.phonetic,
    forms:[...value.forms], acceptedSpellings:[...value.acceptedSpellings], dictionarySource:value.dictionarySource,
    unresolved:value.unresolved, ready:value.ready === true};
}
function bankOrigin(value) {
  if (!plain(value) || !safeId(value.paragraphId) || value.articleId !== undefined && !safeId(value.articleId) ||
      !Number.isSafeInteger(value.start) || !Number.isSafeInteger(value.end) || value.start < 0 || value.end <= value.start ||
      value.end > 1000000 || !textField(value.text, 300) || !value.text || value.end - value.start !== value.text.length ||
      value.sourceLabel !== undefined && !textField(value.sourceLabel, 500) ||
      value.context !== undefined && !textField(value.context, 4000) ||
      value.sourceRoute !== undefined && !textField(value.sourceRoute, 300)) return null;
  return {paragraphId:value.paragraphId, ...(value.articleId === undefined ? {} : {articleId:value.articleId}),
    start:value.start, end:value.end, text:value.text, ...(value.sourceLabel === undefined ? {} : {sourceLabel:value.sourceLabel}),
    ...(value.context === undefined ? {} : {context:value.context}), ...(value.sourceRoute === undefined ? {} : {sourceRoute:value.sourceRoute})};
}
const originKey = value => JSON.stringify([value.paragraphId, value.articleId || '', value.start, value.end, value.text]);

/** Merge a checked list into the existing bank without restarting learned words.
 * The import provenance is an ordinary bank origin; no separate import store.
 */
export function importWordBank(state, rows, words, now=Date.now()) {
  if(!Array.isArray(rows)||!rows.length||rows.length>500)throw new Error('勾选词表不完整。');
  const map=wordMap(mergeStudyWords(words,state)),seen=new Set();
  for(const row of rows){
    const entry=bankWord(row?.entry),origin=bankOrigin(row?.origin);
    if(!entry||!origin||seen.has(entry.id)||!origin.paragraphId.startsWith('import:')||
        entry.baseWordId&&(!map.has(entry.baseWordId)||map.get(entry.baseWordId).meaning!==entry.meaning||normalizeBankTerm(map.get(entry.baseWordId).term)!==entry.term)||
        !entry.baseWordId&&[...map.values()].some(w=>!w.id.startsWith('pw-')&&normalizeBankTerm(w.term)===entry.term))
      throw new Error('勾选词表与当前词本不对应，原记录未改动。');
    seen.add(entry.id);
  }
  let next=state;const at=time(now);
  for(const {entry,origin} of rows){
    const prior=next.wordBank?.[entry.id];
    if(prior){
      if(prior.origins.some(o=>originKey(o)===originKey(origin)))continue;
      next=copy(next);next.wordBank[entry.id].origins.push(copy(origin));next.updatedAt=at;
      continue;
    }
    const progress=next.progress[entry.id],known=progress?.status==='familiar';
    const added=act(next,{type:known?'MARK_KNOWN':'MARK_UNKNOWN',entry,origin},words,at);
    if(added===next)throw new Error(`未能加入 ${entry.term}，原记录未改动。`);
    next=added;
    if(progress){
      next.progress[entry.id]=copy(progress);
      next.wordBank[entry.id].pending=!known&&!Number.isFinite(progress.introducedAt);
    }
  }
  return next;
}

/** Explicit unfamiliar marks from reading/writing use the same bank and schedule.
 * An import origin identifies one user action, so delivery retries keep progress.
 */
export function importMarkedBank(state, rows, words, now=Date.now()) {
  const merged=rows.map(row=>{
    const prior=state.wordBank?.[row.entry?.id];if(!prior)return row;
    const preserveMeaning=!!prior.meaning.trim() && (row.providedMeaning===false || !row.entry.meaning.trim());
    const meaning=preserveMeaning?prior.meaning:row.entry.meaning;
    return {...row,entry:{...row.entry,meaning,unresolved:!meaning.trim(),
      dictionarySource:preserveMeaning?prior.dictionarySource:row.entry.dictionarySource,
      ready:!!meaning.trim() && (row.entry.ready || prior.ready)}};
  });
  let next=importWordBank(state,merged,words,now);
  for(const {entry,origin} of merged){
    if(state.wordBank?.[entry.id]?.origins.some(o=>originKey(o)===originKey(origin)))continue;
    next=act(next,{type:'MARK_UNKNOWN',entry,origin},words,now);
  }
  return next;
}

function validBank(value, baseWords) {
  if (!plain(value)) return false;
  const base = wordMap(baseWords);
  return Object.entries(value).every(([id, entry]) => {
    if (!safeId(id) || !bankWord(entry) || id !== entry.id || !['unknown','known'].includes(entry.label) ||
        typeof entry.ready !== 'boolean' || typeof entry.pending !== 'boolean' || entry.label === 'known' && entry.pending ||
        !Number.isFinite(entry.addedAt) || !Number.isFinite(entry.markedAt) || entry.markedAt < entry.addedAt ||
        entry.markedInSessionId !== null && !safeId(entry.markedInSessionId) ||
        entry.markedGroupIndex !== null && (!Number.isSafeInteger(entry.markedGroupIndex) || entry.markedGroupIndex < 0) ||
        (entry.markedInSessionId === null) !== (entry.markedGroupIndex === null) ||
        !Array.isArray(entry.origins) || !entry.origins.length || entry.origins.some(o=>!bankOrigin(o)) ||
        unique(entry.origins.map(originKey)).length !== entry.origins.length) return false;
    return !entry.baseWordId || !base.has(entry.baseWordId) || normalizeBankTerm(base.get(entry.baseWordId).term) === entry.term;
  });
}

/** Bank metadata stays in this account's ordinary state; passages are rebuilt by the corpus adapter. */
export function mergeStudyWords(baseWords, state) {
  const map = wordMap(baseWords);
  if (!validBank(state.wordBank || {}, baseWords)) return [...map.values()];
  for (const entry of Object.values(state.wordBank || {})) {
    // A removed base collection remains historical; only a validated personal ID
    // may add a new study identity without being present in the loaded base.
    if (entry.baseWordId) continue;
    const existing = map.get(entry.id);
    map.set(entry.id, {...entry, topic:'个人生词', topics:[], collocations:[], passages:[], ...existing,
      term:entry.term, meaning:entry.meaning, pos:entry.pos, phonetic:entry.phonetic,
      forms:[...entry.forms], acceptedSpellings:[...entry.acceptedSpellings]});
  }
  return [...map.values()];
}
/** Personal-word priority uses the same full-corpus lexical counts for every entry.
 * Counts are derived by the corpus adapter, never copied into account state.
 * Missing statistics sort last; timestamps provide stable ties, not priority.
 */
function bankFrequency(word) {
  const f = word?.lexicalFrequency;
  return f && Number.isFinite(f.articleCount) && f.articleCount >= 0 &&
    Number.isFinite(f.totalOccurrences) && f.totalOccurrences >= 0 ? f : null;
}
export function compareBankWords(a, b) {
  const af = bankFrequency(a), bf = bankFrequency(b), ae = a?.bankEntry || a, be = b?.bankEntry || b;
  return Number(!!bf) - Number(!!af) ||
    (bf?.totalOccurrences || 0) - (af?.totalOccurrences || 0) ||
    (bf?.articleCount || 0) - (af?.articleCount || 0) ||
    (ae?.markedAt || 0) - (be?.markedAt || 0) ||
    (ae?.addedAt || 0) - (be?.addedAt || 0) || String(a?.id || '').localeCompare(String(b?.id || ''));
}
const pendingBankWord = (state, word) => state.wordBank?.[word.id]?.label === 'unknown' && state.wordBank[word.id].pending === true;
/** Rank the personal backlog; leave the ordinary book/topic order stable. */
export function prioritizeBankWords(state, words) {
  return [...words].sort((a,b)=>Number(pendingBankWord(state,b))-Number(pendingBankWord(state,a)) ||
    (pendingBankWord(state,a) && pendingBankWord(state,b) ? compareBankWords({...a,bankEntry:state.wordBank[a.id]}, {...b,bankEntry:state.wordBank[b.id]}) : 0));
}
/** One eligibility and ordering policy shared by start and group transitions. */
function admitBankWords(state, words) {
  return prioritizeBankWords(state, words).filter(word => !pendingBankWord(state,word) ||
    state.wordBank[word.id].ready && state.wordBank[word.id].meaning.trim() && word.passages?.length);
}
export function getBankPending(state, words = []) {
  const map = wordMap(words);
  return Object.values(state.wordBank || {}).filter(e=>e.label === 'unknown' && e.pending)
    .sort((a,b)=>compareBankWords({...map.get(a.id),id:a.id,bankEntry:a}, {...map.get(b.id),id:b.id,bankEntry:b}));
}
const calendarDay = value => {
  const d = new Date(value);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
};

function settingsFrom(value = {}) {
  return {
    newPerDay: integer(!value.learningPlanVersion && value.newPerDay === 20 ? 25 : value.newPerDay, 1, 300, DEFAULT_SETTINGS.newPerDay),
    learningPlanVersion: 1, mixedPractice:value.mixedPractice !== false,
    studyTopic: typeof value.studyTopic === 'string' && value.studyTopic.length <= 100 ? value.studyTopic : '',
    groupSize: integer(value.groupSize, 1, 50, DEFAULT_SETTINGS.groupSize),
    spellAfterLearn: typeof value.spellAfterLearn === 'boolean' ? value.spellAfterLearn : true,
    spellAfterReview: typeof value.spellAfterReview === 'boolean' ? value.spellAfterReview : false,
    voice: value.voice === 'en-US' ? 'en-US' : 'en-GB',
    autoSpeak: typeof value.autoSpeak === 'boolean' ? value.autoSpeak : false,
  };
}

export function createState(now = Date.now()) {
  const at = time(now);
  return { schemaVersion: SCHEMA_VERSION, createdAt: at, updatedAt: at, sequence: 0,
    settings: { ...DEFAULT_SETTINGS }, progress: {}, favorites: [], notes: {}, wordBank: {}, history: [], parkedSessions: [], session: null };
}

function progressFor(state, id) { return state.progress[id] || null; }
const finalAnswers = s => [...new Map(s.answers.map(answer => [answer.wordId, answer])).values()];
const memoryCompleted = s => finalAnswers(s).filter(a => !s.retryQueue?.some(r => r.wordId === a.wordId)).length;
const promptToken = s => `${s.id}:${s.answers.length}:${s.index}:${s.retryWordId || ''}${s.phase==='mixed'?':'+currentMixedQuestion(s.mixedRound)?.id:''}`;
function isNew(state, id) {
  const p = progressFor(state, id);
  return !p || p.status !== 'familiar' && !Number.isFinite(p.introducedAt);
}
export function newWords(state, words) {
  return [...wordMap(words).values()].filter(word => isNew(state, word.id));
}
// Encountering a new word saves progress; completing recall (or an actual
// spelling attempt) admits it to spaced review. Relearning does not revoke
// an existing admission. Derive this from existing evidence, without a second ledger.
function reviewReady(state, id) {
  const p = state.progress[id];
  if(p?.mixedRequired && !Number.isFinite(p.mixedCompletedAt))return false;
  return !!p && (p.status === 'review' || p.stage > 0 || p.knownCount > 0 || p.reviewCount > 0 ||
    state.history.some(e=>e.wordId===id && e.type==='spelling' && !e.skipped && !e.undone));
}
export function unfinishedWords(state, words) {
  return [...wordMap(words).values()].filter(w=>state.progress[w.id]?.status !== 'familiar' &&
    Number.isFinite(state.progress[w.id]?.introducedAt) && !reviewReady(state,w.id));
}
function eventId(state, prefix, now) { return `${prefix}-${now.toString(36)}-${++state.sequence}`; }

export function dueWords(state, words, now = Date.now()) {
  const at = time(now);
  return [...wordMap(words).values()].filter(word => {
    const p = progressFor(state, word.id);
    return p && p.status !== 'familiar' && reviewReady(state,word.id) && Number.isFinite(p.introducedAt) && Number.isFinite(p.dueAt) && p.dueAt <= at;
  }).sort((a, b) => state.progress[a.id].dueAt - state.progress[b.id].dueAt || a.id.localeCompare(b.id));
}

export function getStats(state, words, now = Date.now()) {
  const map = wordMap(words), ids = [...map.keys()], day = calendarDay(time(now));
  const values = ids.map(id => state.progress[id]).filter(Boolean);
  const todayMemory = state.history.filter(e => e.type === 'memory' && !e.undone && calendarDay(e.at) === day && map.has(e.wordId));
  const todaySpelling = state.history.filter(e => e.type === 'spelling' && calendarDay(e.at) === day && map.has(e.wordId));
  const learned = values.filter(p => Number.isFinite(p.introducedAt)).length;
  const familiar = values.filter(p => p.status === 'familiar').length;
  const todayLearned = values.filter(p => p.status !== 'familiar' && Number.isFinite(p.introducedAt) && calendarDay(p.introducedAt) === day).length;
  const mastered = values.filter(p => p.status === 'familiar' || p.stage >= 4).length;
  const session = state.session;
  const sessionCompleted = session ? isSpellingMode(session.mode)
    ? session.phase === 'complete' ? session.queue.length : session.spellingIndex + (session.spellingRevealed ? 1 : 0)
    : memoryCompleted(session) : 0;
  return { total: ids.length, newRemaining: ids.filter(id => isNew(state, id)).length, learned,
    familiar, mastered, due: dueWords(state, words, now).length, todayLearned,
    unfinished:unfinishedWords(state,words).length,
    todayCompleted:values.filter(p=>p.status!=='familiar' && Number.isFinite(p.mixedRequired?p.mixedCompletedAt:p.introducedAt) && calendarDay(p.mixedRequired?p.mixedCompletedAt:p.introducedAt)===day).length,
    todayReviewed: unique(todayMemory.filter(e => e.mode === 'review').map(e => e.wordId)).length,
    todayPracticed: unique(todayMemory.filter(e => e.mode === 'practice').map(e => e.wordId)).length,
    todayMemoryCount: todayMemory.length,
    todaySpellingCount: todaySpelling.length,
    todaySpellingCorrect: todaySpelling.filter(e => e.correct).length,
    favorites: state.favorites.filter(id => map.has(id)).length,
    notes: Object.keys(state.notes).filter(id => map.has(id) && state.notes[id].trim()).length,
    completedSessions: state.history.filter(e => e.type === 'session' && e.outcome === 'complete' && e.wordIds?.some(id => map.has(id))).length,
    dailyNewRemaining: getDailyPlan(state,now,ids).remaining,
    dailyPlan: getDailyPlan(state,now,ids),
    completionPercent: ids.length ? Math.round((ids.length - ids.filter(id => isNew(state, id)).length) / ids.length * 100) : 0,
    session: session ? { mode: session.mode, phase: session.phase, total: session.queue.length,
      completed: sessionCompleted, remaining: Math.max(0, session.queue.length - sessionCompleted), paused: session.paused } : null,
  };
}

function initialSession(state, queue, mode, at) {
  return { id: eventId(state, 'session', at), mode, queue, index: 0, groupIndex: 0, browseIndex: null,
    passageIndex: 0, revealed: false, pendingGrade: null, retryQueue: [], retryWordId: null,
    phase: mode === 'spelling' ? 'spelling' : 'memory',
    paused: false, startedAt: at, completedAt: null, lastActionAt: at, correctableEventId: null,
    groupWordIds: [], answers: [], spellingQueue: isSpellingMode(mode) ? [...queue] : [],
    spellingIndex: 0, spellingInput: '', spellingHinted: false, hintLevel: 0,
    spellingRevealed: false, spellResults: [], spellingRounds: [], spellingRound: 0,
    spellingAttempts: [], emptyReason: null, summary: null,
    // Freeze the learning plan for this run so editing settings cannot change a group mid-way.
    plan: { groupSize: mode === 'review' ? Math.max(1, queue.length) : state.settings.groupSize,
      spellAfter: mode === 'learn' ? state.settings.spellAfterLearn : mode === 'review' ? state.settings.spellAfterReview : false },
  };
}

function finishSession(state, at, emptyReason = null) {
  const s = state.session;
  if (!s || s.completedAt !== null) return;
  s.phase = 'complete'; s.paused = false; s.browseIndex = null; s.completedAt = at;
  s.emptyReason = emptyReason;
  const summary = { id: eventId(state, 'result', at), type: 'session', sessionId: s.id,
    mode: s.mode, at, startedAt: s.startedAt, outcome: 'complete', wordIds: [...s.queue],
    studied: s.mode === 'dictation' ? s.index : finalAnswers(s).length, known: finalAnswers(s).filter(a => a.grade === 'known').length,
    forgot: finalAnswers(s).filter(a => a.grade === 'forgot').length,
    spellingAttempts: s.spellingAttempts.length,
    spellingCorrect: s.spellingAttempts.filter(a => a.correct).length, emptyReason,
    ...(s.mixedAttempts ? {mixedAttempts:copy(s.mixedAttempts),mixedCorrect:s.mixedAttempts.filter(a=>a.correct).length} : {}) };
  s.summary = copy(summary);
  // An empty queue is an informative state, not a completed learning achievement.
  if (!emptyReason) state.history.push(summary);
}

// A page visit is not an unfinished task; the final result is not another task.
export function getSessionStatus(state) {
  const s=state.session;
  if(!s)return 'none';
  if(s.phase==='complete')return 'complete';
  if(s.phase==='spelling-result'&&!s.retryQueue?.length&&
    (isSpellingMode(s.mode)||s.index>=s.queue.length))return 'complete';
  const worked=s.index>0||s.answers.length>0||s.spellingAttempts.length>0||
    s.revealed||s.pendingGrade||s.spellingInput.trim()||s.spellingHinted||s.audioHeard||s.passageIndex>0;
  return worked?'pending':'unstarted';
}

export function startSession(state, words, mode = 'learn', now = Date.now(), options = {}) {
  if (!MODES.has(mode)) return state;
  if(mode==='learn')state=ensureDailyPlan(state,time(now),options.dailyWordIds || [...wordMap(words).keys()]);
  if (getSessionStatus(state) === 'pending') return state;
  const at = time(now), next = copy(state), map = wordMap(words);
  if(next.session?.phase==='spelling-result')finishSession(next,at);
  let queue = [...map.keys()];
  if (mode === 'learn') {
    const allowance = getDailyPlan(state,at).remaining;
    const pending = new Set(getBankPending(state).map(e=>e.id));
    const unfinished = new Set(unfinishedWords(state, words).map(w=>w.id));
    queue = queue.filter(id => state.progress[id]?.status !== 'familiar' && (isNew(state, id) || unfinished.has(id) || pending.has(id)));
    queue = admitBankWords(state, queue.map(id=>map.get(id))).map(w=>w.id);
    let newCount = 0;
    queue = queue.filter(id=>!isNew(state,id) || newCount++ < allowance);
  } else if (mode === 'practice') queue = admitBankWords(state, words).map(w=>w.id);
  else if (mode === 'review') queue = dueWords(state, words, at).map(w => w.id);
  next.session = initialSession(next, queue, mode, at);
  if(mode==='learn' && validRecipe(options.mixedRecipe)){next.session.plan.mixedRecipe=[...options.mixedRecipe];next.session.plan.spellAfter=false;next.session.mixedAttempts=[];}
  if(mode==='dictation')next.session.plan.listeningKind=options.listeningKind==='review'?'review':'new';
  next.session.plan.dailyWordIds = options.dailyWordIds ? unique(options.dailyWordIds) : null;
  if (mode === 'learn' && options.refillSkipped) next.session.plan.newWordCandidates = [...map.keys()];
  next.updatedAt = at;
  if (!queue.length) finishSession(next, at, mode === 'review' ? 'nothing-due' : mode === 'learn' ? 'daily-plan-complete' : 'no-words');
  return next;
}

/** A retrieval result is one session; no fixed word/paragraph count or reading gate. */
export function startGroupedSession(state, allWords, group, mode = 'learn', now = Date.now()) {
  if (!group || !safeId(group.id) || !Array.isArray(group.paragraphIds)) return state;
  const ids = group.selectedWordIds || group.wordIds;
  if (!Array.isArray(ids)) return state;
  const map = wordMap(allWords), selected = unique(ids).filter(id => map.has(id)).map(id => map.get(id));
  const paragraphs = unique(group.paragraphIds.filter(safeId));
  if (!selected.length || mode !== 'spelling' && !paragraphs.length) return state;
  const next = startSession(state, selected, mode, now, { dailyWordIds: [...map.keys()], refillSkipped:group.refillSkipped === true, mixedRecipe:group.mixedRecipe });
  if (next === state || next.session?.id === state.session?.id || next.session.phase === 'complete' || mode === 'spelling') return next;
  next.session.context = { groupId: group.id, title: String(group.title || group.label || ''),
    paragraphIds: paragraphs, index: 0, ...(typeof group.topic === 'string' ? {topic:group.topic} : {}) };
  return next;
}

function resetPrompt(s) {
  s.passageIndex = 0; s.revealed = false; s.pendingGrade = null; s.browseIndex = null;
  if (s.context) delete s.context.scroll;
}
function resetSpellingPrompt(s) {
  s.spellingInput = ''; s.spellingHinted = false; s.hintLevel = 0; s.spellingRevealed = false;
  if(s.mode==='dictation')s.audioHeard=false;
}
function clearSpellingGroup(s) {
  s.spellingQueue = []; s.spellingIndex = 0; s.spellResults = [];
  s.spellingRounds = []; s.spellingRound = 0; resetSpellingPrompt(s);
}
function finishMemoryGroup(state, at, map) {
  const s=state.session;
  if(s.plan.mixedRecipe){
    const ids=s.groupWordIds.filter(id=>state.progress[id]?.status!=='familiar');
    const scope=s.plan.dailyWordIds ? new Set([...s.plan.dailyWordIds,...Object.keys(state.wordBank || {})]) : null;
    const pool=[...map.values()].filter(w=>!scope || scope.has(w.id));
    if(ids.length){s.mixedRound=createMixedRound(pool,ids,s.plan.mixedRecipe,`${s.id}-${s.groupIndex}`);s.phase='mixed';s.browseIndex=null;s.mixedInput='';s.mixedRevealed=false;return;}
  }
  startSpellingGroup(state,at,map);
}
function startSpellingGroup(state, at, map) {
  const s = state.session;
  s.phase = 'spelling'; s.spellingQueue = s.groupWordIds.filter(id=>state.progress[id]?.status !== 'familiar'); s.spellingIndex = 0;
  s.spellResults = []; s.spellingRounds = []; s.spellingRound = 0; s.browseIndex = null;
  resetSpellingPrompt(s);
  if (!s.spellingQueue.length) continueMemory(state, at, map);
}
function skipFamiliarAhead(state) {
  const s = state.session;
  // Remove only the next unanswered prompt. Answer/history identities are immutable.
  while (s.index < s.queue.length && state.progress[s.queue[s.index]]?.status === 'familiar') s.queue.splice(s.index, 1);
}
function removeFamiliarRetries(state) {
  const s = state.session;
  s.retryQueue = (s.retryQueue || []).filter(r => state.progress[r.wordId]?.status !== 'familiar');
  if (!s.retryQueue.some(r => r.wordId === s.retryWordId)) s.retryWordId = null;
}
function refillNewWords(state, at, map) {
  const s = state.session;
  if (s.mode !== 'learn' || !s.plan.newWordCandidates) return;
  const reserved = s.queue.slice(s.index).filter(id=>isNew(state,id)).length;
  let remaining = Math.max(0, getDailyPlan(state,at,s.plan.dailyWordIds || undefined).remaining - reserved);
  for (const id of s.plan.newWordCandidates) {
    if (!remaining) break;
    if (s.queue.includes(id) || !isNew(state,id) || !map.get(id)?.passages?.length) continue;
    s.queue.push(id); remaining--;
  }
}
function advanceMemory(state, at, map) {
  const s = state.session;
  removeFamiliarRetries(state); skipFamiliarAhead(state);
  refillNewWords(state, at, map);
  const boundary = s.groupWordIds.filter(id=>state.progress[id]?.status !== 'familiar').length >= s.plan.groupSize || s.index >= s.queue.length;
  const retry = s.retryQueue.find(r => r.afterAttempt <= s.answers.length) || (boundary ? s.retryQueue[0] : null);
  s.retryWordId = retry?.wordId || null;
  if (retry) return;
  if (!boundary) return;
  if ((s.plan.mixedRecipe || s.plan.spellAfter) && s.groupWordIds.some(id => state.progress[id]?.status !== 'familiar')) finishMemoryGroup(state, at, map);
  else if (s.index >= s.queue.length) finishSession(state, at, s.answers.length ? null : 'no-words');
  else {
    s.groupIndex = (s.groupIndex || 0) + 1; s.groupWordIds = [];
    insertPendingAtBoundary(state, map, at);
    if (s.index >= s.queue.length) finishSession(state, at);
  }
}
function insertPendingAtBoundary(state, map, at) {
  const s = state.session;
  if (!['learn','practice'].includes(s.mode) || s.index >= s.queue.length) return;
  const pending = getBankPending(state, [...map.values()]).filter(e=>e.ready && e.meaning.trim() && !s.queue.includes(e.id) &&
    state.progress[e.id]?.status !== 'familiar' && map.get(e.id)?.passages?.length &&
    (!s.context?.topic || map.get(e.id).passages.some(p=>p.topics?.includes(s.context.topic))));
  let allowance = getDailyPlan(state,at,s.plan.dailyWordIds || undefined).remaining;
  const candidates = admitBankWords(state,
    [...s.queue.slice(s.index), ...pending.map(e=>e.id)].map(id=>map.get(id))).map(w=>w.id);
  const remaining = candidates.filter(id=>{
    if (state.progress[id]?.status === 'familiar') return false;
    if (s.mode !== 'learn' || !isNew(state,id)) return true;
    if (!allowance) return false;
    allowance--; return true;
  });
  s.queue = [...s.queue.slice(0,s.index), ...remaining];
}
function continueMemory(state, at, map) {
  const s = state.session;
  delete s.mixedRound;delete s.mixedInput;delete s.mixedRevealed;
  skipFamiliarAhead(state); removeFamiliarRetries(state);
  refillNewWords(state, at, map);
  // Legacy saves can already be answering spelling after a forgotten grade.
  // Finish that saved response first; the next memory group resolves its retries.
  if (!isSpellingMode(s.mode) && s.retryQueue.length) {
    s.groupIndex = (s.groupIndex || 0) + 1;
    s.phase = 'memory'; s.groupWordIds = unique(s.retryQueue.map(r=>r.wordId));
    clearSpellingGroup(s); resetPrompt(s);
    s.retryWordId = s.retryQueue[0].wordId;
    return;
  }
  if (isSpellingMode(s.mode) || s.index >= s.queue.length) { finishSession(state, at); return; }
  s.groupIndex = (s.groupIndex || 0) + 1;
  insertPendingAtBoundary(state, map, at);
  s.phase = 'memory'; s.groupWordIds = []; clearSpellingGroup(s); resetPrompt(s);
  if (s.index >= s.queue.length) finishSession(state, at);
}

function canCorrectLast(state) {
  const s = state.session;
  if (!s || s.paused || !s.answers.length || s.phase === 'complete' || s.phase === 'spelling-result') return false;
  if (s.phase === 'mixed') return false;
  if (s.phase === 'spelling' && (s.spellingAttempts.some(a => s.groupWordIds.includes(a.wordId)) || s.spellingInput || s.spellingHinted)) return false;
  const answer = s.answers.at(-1);
  if (s.spellingAttempts.some(attempt => attempt.wordId === answer.wordId) || s.mixedAttempts?.some(attempt=>attempt.wordId===answer.wordId)) return false;
  return s.correctableEventId === answer.eventId && state.progress[answer.wordId]?.lastEventId === answer.eventId;
}

export function currentWordId(state) {
  const s = state.session;
  if (!s || s.phase === 'complete' || s.phase === 'spelling-result') return null;
  if (s.phase === 'spelling') return s.spellingQueue[s.spellingIndex] || null;
  if (s.phase === 'mixed') return currentMixedQuestion(s.mixedRound)?.wordId || null;
  if (s.browseIndex !== null) return s.queue[s.browseIndex] || null;
  return s.retryWordId || s.queue[s.index] || null;
}

export function getCurrentView(state, words) {
  const s = state.session, wordId = currentWordId(state);
  const isBrowsing = s?.browseIndex !== null && s?.browseIndex !== undefined;
  const isRetry = !!s?.retryWordId && !isBrowsing && s.phase === 'memory';
  return { wordId, word: wordMap(words).get(wordId) || null, phase: s?.phase || null,
    index: s ? s.phase === 'spelling' ? s.spellingIndex : isBrowsing ? s.browseIndex : isRetry ? s.queue.indexOf(wordId) : s.index : 0,
    isBrowsing, isRetry, promptToken: s ? promptToken(s) : null, memoryCompleted: s ? memoryCompleted(s) : 0,
    memoryRemaining: s ? Math.max(0, s.queue.length - memoryCompleted(s)) : 0,
    pendingGrade: s?.pendingGrade || null,
    answer: isBrowsing ? s.answers.findLast(a => a.wordId === wordId) || null : null,
    canCorrectLast: canCorrectLast(state), revealed: isBrowsing || !!s?.revealed,
    spellingResult: s?.spellingRevealed ? s.spellResults.at(-1) || null : null };
}

function newProgress() {
  return { status: 'learning', introducedAt: null, lastStudiedAt: null, dueAt: null, stage: 0,
    learningCount: 0, reviewCount: 0, practiceCount: 0, knownCount: 0, forgotCount: 0,
    spellingAttempts: 0, spellingCorrect: 0, lastGrade: null, lastEventId: null };
}

function gradeMemory(state, grade, wordId, at, map, passageId) {
  const s = state.session, beforeProgress = state.progress[wordId] ? copy(state.progress[wordId]) : null;
  const p = { ...newProgress(), ...beforeProgress }, id = eventId(state, 'memory', at);
  if (p.introducedAt === null) p.introducedAt = at;
  if(s.mode==='learn'){p.mixedRequired=!!s.plan.mixedRecipe;if(p.mixedRequired)p.mixedCompletedAt=null;}
  p.lastStudiedAt = at; p.lastGrade = grade; p.lastEventId = id;
  p[grade === 'known' ? 'knownCount' : 'forgotCount'] += 1;
  p[s.mode === 'review' ? 'reviewCount' : s.mode === 'practice' ? 'practiceCount' : 'learningCount'] += 1;
  // An explicit practice does not revoke the user's "already familiar" choice.
  if (p.status !== 'familiar') {
    const retainSchedule=s.mode==='learn' && grade==='known' && beforeProgress?.mixedRequired &&
      !Number.isFinite(beforeProgress.mixedCompletedAt) && Number.isFinite(beforeProgress.dueAt);
    p.stage = grade === 'known' ? retainSchedule ? p.stage : Math.min(REVIEW_INTERVAL_DAYS.length, p.stage + 1) : 0;
    p.status = grade === 'known' ? 'review' : 'learning';
    p.dueAt = retainSchedule ? beforeProgress.dueAt : grade === 'known' ? at + REVIEW_INTERVAL_DAYS[Math.max(0, p.stage - 1)] * DAY :
      reviewReady(state,wordId) ? at + 600000 : null;
  }
  state.progress[wordId] = p;
  const bank = state.wordBank?.[wordId], beforeBankEntry = bank ? copy(bank) : null;
  if (bank?.pending && (bank.markedInSessionId !== s.id || s.groupIndex > bank.markedGroupIndex)) bank.pending = false;
  const answer = { eventId: id, wordId, grade, at, index: s.queue.indexOf(wordId), beforeProgress, beforeBankEntry,
    afterProgress: copy(p), passageIndex: s.passageIndex, ...(passageId ? {passageId} : {}),
    beforeQueue:[...s.queue], beforeGroupIndex:s.groupIndex || 0, beforeGroupWordIds:[...s.groupWordIds],
    beforeSessionIndex:s.index, beforeRetryQueue:copy(s.retryQueue || []), beforeRetryWordId:s.retryWordId || null,
    beforePendingGrade:s.pendingGrade || null };
  s.answers.push(answer); s.correctableEventId = id;
  state.history.push({ id, type: 'memory', sessionId: s.id, mode: s.mode, wordId, grade, at, undone: false, ...(passageId ? {passageId} : {}) });
  if (!s.groupWordIds.includes(wordId)) s.groupWordIds.push(wordId);
  if (!s.retryWordId) s.index += 1;
  s.retryQueue = (s.retryQueue || []).filter(r => r.wordId !== wordId);
  if (grade === 'forgot' && p.status !== 'familiar') s.retryQueue.push({wordId, afterAttempt:s.answers.length + 2});
  s.retryWordId = null; resetPrompt(s); advanceMemory(state, at, map);
}

export function normalizeSpelling(value) {
  return String(value || '').normalize('NFKC').trim().toLocaleLowerCase('en-US')
    .replace(/[’‘]/g, "'").replace(/[‐‑–—]/g, '-').replace(/\s+/g, ' ');
}

function submitSpelling(state, word, at, skipped = false) {
  const s = state.session;
  if (s.spellingRevealed) return;
  // Only explicit, editorially checked orthographic aliases qualify. Inflections
  // and example forms are not accepted unless they are deliberately on this list.
  const spellings = [word.term, ...(Array.isArray(word.acceptedSpellings) ? word.acceptedSpellings.filter(value => typeof value === 'string' && value.trim()) : [])];
  const matched = !skipped && spellings.some(value => normalizeSpelling(s.spellingInput) === normalizeSpelling(value));
  const result = { id: eventId(state, 'spelling', at), type: 'spelling', sessionId: s.id,
    mode: s.mode, wordId: word.id, at, input: s.spellingInput, matched,
    correct: matched && !s.spellingHinted, hinted: s.spellingHinted, skipped, round: s.spellingRound };
  s.spellResults.push(result); s.spellingAttempts.push(copy(result)); s.spellingRevealed = true;
  state.history.push(copy(result));
  if(s.mode==='dictation'){
    const p={...newProgress(),...state.progress[word.id]};
    if(p.introducedAt===null)p.introducedAt=at;
    p.lastStudiedAt=at;p.lastEventId=result.id;p.lastGrade=result.correct?'known':'forgot';
    p.spellingAttempts++;if(result.correct)p.spellingCorrect++;
    // Repeating the same successful word today does not advance several intervals.
    const advancedEarlier=state.history.some(e=>e.id!==result.id&&e.mode==='dictation'&&e.wordId===word.id&&e.correct&&calendarDay(e.at)===calendarDay(at));
    if(result.correct){if(!advancedEarlier)p.stage=Math.min(REVIEW_INTERVAL_DAYS.length,p.stage+1);p.status='review';p.dueAt=at+REVIEW_INTERVAL_DAYS[Math.max(0,p.stage-1)]*DAY;}
    else{p.stage=0;p.status='learning';p.dueAt=at+DAY;}
    state.progress[word.id]=p;return;
  }
  // Spelling-only practice must not introduce new words or start a memory schedule.
  const p = state.progress[word.id];
  if (p) {
    p.spellingAttempts += 1; if (result.correct) p.spellingCorrect += 1;
    if (!skipped && p.status !== 'familiar' && Number.isFinite(p.introducedAt) && p.dueAt === null) {
      p.status = 'review'; p.dueAt = at + (result.correct ? DAY : 600000);
    }
  }
}

/** All actions return the original state on a rejected/no-op action. */
export function act(state, action, words, now = Date.now()) {
  if (!action || typeof action.type !== 'string') return state;
  const at = time(now), map = wordMap(mergeStudyWords(words, state)), id = action.wordId;
  if(state.dailyPlan || state.session?.mode==='learn')state=ensureDailyPlan(state,at);
  let next;
  if (action.type === 'DISMISS_CURRENT') {
    const s = state.session;
    if (!s || s.mode==='dictation' || action.sessionId !== s.id || s.phase !== 'memory' || s.paused || s.browseIndex !== null ||
        id !== currentWordId(state) || !map.has(id) || action.promptToken && action.promptToken !== promptToken(s)) return state;
    const familiar = act(state, {type:'FAMILIAR', wordId:id, value:true}, words, at);
    return act(familiar, {type:'SKIP_KNOWN', wordId:id, sessionId:s.id}, words, at);
  } else if (action.type === 'MARK_UNKNOWN' || action.type === 'MARK_KNOWN') {
    const entry = bankWord(action.entry), origin = bankOrigin(action.origin);
    if (!entry || !origin) return state;
    if (entry.baseWordId && (!map.has(entry.baseWordId) || normalizeBankTerm(map.get(entry.baseWordId).term) !== entry.term ||
        map.get(entry.baseWordId).meaning !== entry.meaning)) return state;
    if (!entry.baseWordId && [...map.values()].some(w=>!w.id.startsWith('pw-') && normalizeBankTerm(w.term) === entry.term)) return state;
    const label = action.type === 'MARK_KNOWN' ? 'known' : 'unknown', prior = state.wordBank?.[entry.id];
    const origins = prior ? copy(prior.origins) : [];
    if (!origins.some(o=>originKey(o) === originKey(origin))) origins.push(origin);
    if (prior && prior.label === label && (label === 'known' || prior.pending) &&
        JSON.stringify(bankWord(prior)) === JSON.stringify(entry) && JSON.stringify(origins) === JSON.stringify(prior.origins)) return state;
    next = copy(state); next.wordBank ||= {};
    const active = next.session && next.session.phase !== 'complete' ? next.session : null;
    next.wordBank[entry.id] = {...entry, label, origins, addedAt:prior?.addedAt ?? at,
      markedAt:Math.max(at, prior?.addedAt ?? at), pending:label === 'unknown',
      markedInSessionId:active?.id || null, markedGroupIndex:active ? active.groupIndex || 0 : null};
    const p = next.progress[entry.id], event = eventId(next, 'word-label', at);
    if (label === 'known') next.progress[entry.id] = p?.status === 'familiar' ? {...p, lastEventId:event} : {
      ...newProgress(), ...p, status:'familiar', dueAt:null, familiarAt:at, lastEventId:event, beforeFamiliar:p ? copy(p) : null};
    else next.progress[entry.id] = {...newProgress(), ...p, status:'learning', stage:0,
      dueAt:Number.isFinite(p?.introducedAt) ? at : null, lastEventId:event, beforeFamiliar:null,
      ...(p?.mixedRequired ? {mixedCompletedAt:null} : {})};
    next.history.push({id:event, type:'word-label', wordId:entry.id, label, at});
  } else if (action.type === 'SETTINGS') {
    next = copy(state); next.settings = settingsFrom({ ...state.settings, ...action.patch });
  } else if (action.type === 'FAVORITE' && map.has(id)) {
    next = copy(state); next.favorites = state.favorites.includes(id) ? state.favorites.filter(v => v !== id) : [...state.favorites, id];
  } else if (action.type === 'NOTE' && map.has(id)) {
    next = copy(state); const note = String(action.text || '').slice(0, 8000).trim();
    if (note) next.notes[id] = note; else delete next.notes[id];
  } else if (action.type === 'FAMILIAR' && map.has(id) && typeof action.value === 'boolean') {
    if (state.wordBank?.[id]) return act(state, {type:action.value ? 'MARK_KNOWN' : 'MARK_UNKNOWN',
      entry:state.wordBank[id], origin:state.wordBank[id].origins[0]}, words, now);
    const current = state.progress[id];
    if (action.value === (current?.status === 'familiar')) return state;
    next = copy(state);
    if (action.value) next.progress[id] = { ...newProgress(), ...current, status: 'familiar', dueAt: null,
      familiarAt: at, lastEventId: eventId(next, 'familiar', at), beforeFamiliar: current ? copy(current) : null };
    else if (current.beforeFamiliar) next.progress[id] = copy(current.beforeFamiliar);
    else if (current.introducedAt !== null) next.progress[id] = { ...current, status: 'learning', stage: 0, dueAt: at, beforeFamiliar: null };
    else delete next.progress[id];
  } else if (action.type === 'CLOSE_SESSION') {
    if (!state.session) return state;
    next = copy(state);
    if (next.session.phase !== 'complete') next.history.push({ id: eventId(next, 'close', at), type: 'session',
      sessionId: next.session.id, mode: next.session.mode, at, startedAt: next.session.startedAt,
      outcome: 'closed', wordIds: [...next.session.queue], studied: finalAnswers(next.session).length,
      ...(next.session.mixedAttempts ? {mixedAttempts:copy(next.session.mixedAttempts)} : {}) });
    next.session = null;
  } else {
    const original = state.session;
    if (!original) return state;
    if (action.sessionId && action.sessionId !== original.id) return state;
    if (action.type === 'PAUSE') {
      if (original.paused || original.phase === 'complete') return state;
      next = copy(state);
      if(getSessionStatus(state)==='complete')finishSession(next,at);
      else next.session.paused = true;
    } else if (action.type === 'RESUME') {
      if (original.phase === 'complete') return state;
      next = copy(state); next.session.paused = false;
      if(next.session.mode==='learn')refillNewWords(next,at,map);
      if(!original.paused && next.session.queue.length===original.queue.length)return state;
    } else {
      if (original.paused || original.phase === 'complete') return state;
      const activeId = currentWordId(state);
      // Word id/phase guards make repeated click handlers and stale prompt events harmless.
      if (id && id !== activeId && action.type !== 'CORRECT_LAST') return state;
      if (action.promptToken && action.promptToken !== promptToken(original)) return state;
      next = copy(state); const s = next.session;
      if(s.mode==='dictation'&&['MEMORY_CHOICE','GRADE','PREVIOUS','REVEAL','SKIP_KNOWN','RETRY_WRONG'].includes(action.type))return state;
      switch (action.type) {
        case 'MIXED_INPUT':
          if(s.phase!=='mixed' || s.mixedRound.feedback)return state;
          s.mixedInput=String(action.value || '').slice(0,200);break;
        case 'MIXED_REVEAL':
          if(s.phase!=='mixed' || s.mixedRound.feedback || !['recall','spelling'].includes(currentMixedQuestion(s.mixedRound)?.type))return state;
          s.mixedRevealed=true;break;
        case 'MIXED_ANSWER': {
          if(s.phase!=='mixed' || s.mixedRound.feedback)return state;
          const q=currentMixedQuestion(s.mixedRound);
          if(action.questionId!==q?.id || q.type==='recall' && !s.mixedRevealed)return state;
          const answer=q.type==='spelling'?s.mixedInput:action.answer;
          const round=submitMixedAnswer(s.mixedRound,{questionId:q.id,answer,hinted:q.type==='spelling'&&s.mixedRevealed},[...map.values()]);
          if(round===s.mixedRound || !round.feedback)return state;
          s.mixedRound=round;
          const attempt={...copy(round.feedback),at,questionId:q.id};s.mixedAttempts.push(attempt);
          const progress=next.progress[q.wordId];
          if(round.progress.find(p=>p.wordId===q.wordId)?.completed && progress)progress.mixedCompletedAt=at;
          if(q.type==='spelling' && progress){
            const spelling={id:eventId(next,'spelling',at),type:'spelling',sessionId:s.id,mode:s.mode,wordId:q.wordId,at,input:s.mixedInput,correct:attempt.correct,hinted:attempt.hinted,round:s.groupIndex,mixed:true};
            next.history.push(spelling);s.spellingAttempts.push(copy(spelling));progress.spellingAttempts++;if(attempt.correct)progress.spellingCorrect++;
          }
          if(!attempt.correct){const p=next.progress[q.wordId];if(p && p.status!=='familiar'){p.stage=0;p.status='learning';p.dueAt=at+600000;p.lastStudiedAt=at;}}
          break;
        }
        case 'MIXED_NEXT':
          if(s.phase!=='mixed' || !s.mixedRound.feedback || action.questionId!==currentMixedQuestion(s.mixedRound)?.id)return state;
          s.mixedRound=advanceMixedRound(s.mixedRound,[...map.values()]);s.mixedInput='';s.mixedRevealed=false;
          if(s.mixedRound.complete)continueMemory(next,at,map);
          break;
        case 'DICTATION_LEARN_NEXT':
          if(s.mode!=='dictation'||s.phase!=='memory'||action.sessionId!==s.id||id!==activeId)return state;
          s.index++;resetPrompt(s);
          if(s.index>=s.queue.length){s.phase='spelling';s.spellingIndex=0;resetSpellingPrompt(s);}
          break;
        case 'DICTATION_HEARD':
          if(s.mode!=='dictation'||s.phase!=='spelling'||s.spellingRevealed||action.sessionId!==s.id||
            action.round!==s.spellingRound||action.spellingIndex!==s.spellingIndex)return state;
          s.audioHeard=true;break;
        case 'CONTEXT_PASSAGE':
          if (s.phase !== 'memory' || !s.context) return state;
          if (action.index !== undefined) s.context.index = integer(action.index, 0, s.context.paragraphIds.length - 1, 0);
          if (action.scroll && safeId(action.scroll.paragraphId) && action.scroll.wordId === activeId) {
            s.context.scroll = {wordId: activeId, paragraphId: action.scroll.paragraphId,
              offset: integer(action.scroll.offset, -1000, 50000, 0), revealed: !!s.revealed};
          }
          break;
        case 'PASSAGE': {
          if (s.phase !== 'memory') return state;
          const count = map.get(activeId)?.passages?.length || 1;
          s.passageIndex = integer(action.index, 0, count - 1, 0);
          if (s.context) delete s.context.scroll;
          break;
        }
        case 'MEMORY_CHOICE':
          if (action.sessionId !== s.id || s.phase !== 'memory' || s.browseIndex !== null || (s.revealed && !s.pendingGrade) ||
              id !== activeId || !['known','forgot'].includes(action.grade)) return state;
          s.revealed = true; s.pendingGrade = action.grade; break;
        case 'REVEAL':
          if (s.phase !== 'memory' || s.browseIndex !== null || s.revealed) return state;
          s.revealed = true; s.pendingGrade = null; break;
        case 'GRADE':
          if (s.phase !== 'memory' || s.browseIndex !== null || !s.revealed || id !== activeId || !map.has(id) || !['known', 'forgot'].includes(action.grade)) return state;
          gradeMemory(next, action.grade, id, at, map,
            map.get(id).passages?.some(p => p.id === action.passageId) ? action.passageId : null); break;
        case 'SKIP_KNOWN':
          if (s.phase !== 'memory' || s.browseIndex !== null || next.progress[activeId]?.status !== 'familiar') return state;
          removeFamiliarRetries(next); resetPrompt(s); advanceMemory(next, at, map);
          break;
        case 'PREVIOUS': {
          if (s.phase !== 'memory' || !s.index) return state;
          s.browseIndex = Math.max(0, (s.browseIndex === null ? s.index : s.browseIndex) - 1);
          s.passageIndex = s.answers.find(a => a.index === s.browseIndex)?.passageIndex || 0; break;
        }
        case 'RETURN_CURRENT':
          if (s.browseIndex === null) return state;
          s.browseIndex = null; s.passageIndex = 0; break;
        case 'CORRECT_LAST': {
          if (!canCorrectLast(state)) return state;
          const last = s.answers.pop();
          if (action.eventId && action.eventId !== last.eventId) return state;
          if (last.beforeProgress) next.progress[last.wordId] = copy(last.beforeProgress); else delete next.progress[last.wordId];
          if (last.beforeBankEntry) next.wordBank[last.wordId] = copy(last.beforeBankEntry);
          const event = next.history.find(e => e.id === last.eventId); if (event) { event.undone = true; event.correctedAt = at; }
          s.index = last.beforeSessionIndex ?? last.index; s.phase = 'memory'; s.browseIndex = null; s.correctableEventId = null;
          s.passageIndex = last.passageIndex; s.revealed = true;
          s.retryQueue = copy(last.beforeRetryQueue || []); s.retryWordId = last.beforeRetryWordId || null;
          s.pendingGrade = last.beforePendingGrade || null;
          if (last.beforeQueue) s.queue = [...last.beforeQueue];
          s.groupIndex = last.beforeGroupIndex ?? s.groupIndex;
          s.groupWordIds = last.beforeGroupWordIds ? [...last.beforeGroupWordIds] : s.groupWordIds.filter(wordId => wordId !== last.wordId);
          clearSpellingGroup(s); break;
        }
        case 'SPELL_INPUT':
          if (s.phase !== 'spelling' || s.spellingRevealed) return state;
          s.spellingInput = String(action.value || '').slice(0, 200); break;
        case 'SPELL_HINT':
          if (s.phase !== 'spelling' || s.spellingRevealed) return state;
          if(s.mode==='dictation')return state;
          s.spellingHinted = true; s.hintLevel = Math.min((map.get(activeId)?.term?.length || 1), s.hintLevel + 1); break;
        case 'SPELL_SUBMIT':
        case 'SPELL_SKIP':
          if (s.phase !== 'spelling' || s.spellingRevealed || !map.has(activeId)) return state;
          if (action.type === 'SPELL_SUBMIT' && !s.spellingInput.trim()) return state;
          if(s.mode==='dictation'&&!s.audioHeard)return state;
          submitSpelling(next, map.get(activeId), at, action.type === 'SPELL_SKIP'); break;
        case 'SPELL_NEXT':
          if (s.phase !== 'spelling' || !s.spellingRevealed) return state;
          s.spellingIndex += 1; resetSpellingPrompt(s);
          if (!isSpellingMode(s.mode)) while (s.spellingIndex < s.spellingQueue.length && next.progress[s.spellingQueue[s.spellingIndex]]?.status === 'familiar') s.spellingQueue.splice(s.spellingIndex,1);
          if (s.spellingIndex >= s.spellingQueue.length) {
            s.phase = 'spelling-result'; s.spellingRounds.push(copy(s.spellResults));
            if(s.mode==='dictation'){
              finishSession(next,at);
            }
          }
          break;
        case 'RETRY_WRONG': {
          if (s.phase !== 'spelling-result') return state;
          const wrongIds = unique(s.spellResults.filter(result => !result.correct).map(result => result.wordId));
          if (!wrongIds.length) return state;
          s.spellingQueue = wrongIds; s.spellingIndex = 0; s.spellResults = []; s.spellingRound += 1;
          s.phase = 'spelling'; resetSpellingPrompt(s); break;
        }
        case 'CONTINUE':
          if (s.phase !== 'spelling-result') return state;
          continueMemory(next, at, map); break;
        default: return state;
      }
    }
    if (next.session) next.session.lastActionAt = at;
  }
  if (!next) return state;
  next.updatedAt = at;
  return next.dailyPlan || next.session?.mode==='learn' ? ensureDailyPlan(next,at) : next;
}

/** Return a normalized copy, or null for an invalid/incompatible save; never mutate input. */
export function validateState(value, words) {
  if (!value || typeof value !== 'object' || value.schemaVersion !== SCHEMA_VERSION ||
      !value.progress || typeof value.progress !== 'object' || Array.isArray(value.progress) ||
      !Array.isArray(value.history) || !Array.isArray(value.favorites) ||
      !value.notes || typeof value.notes !== 'object' || Array.isArray(value.notes)) return null;
  try {
    const bank = value.wordBank === undefined ? {} : value.wordBank;
    if (!validBank(bank, words)) return null;
    const validIds = words ? new Set(wordMap(mergeStudyWords(words, {...value, wordBank:bank})).keys()) : null;
    // A collection is a view over the user's record, not permission to erase
    // words from older collections. Only the live session requires loaded words.
    const accepted = safeId;
    const sessionAccepted = id => safeId(id) && (!validIds || validIds.has(id));
    if(!validDailyPlan(value.dailyPlan))return null;
    const next = copy(value);
    const listening=validateListening(value.listening);if(!listening)return null;
    if(value.listening!==undefined)next.listening=listening;
    next.wordBank = copy(bank);
    next.settings = settingsFrom(value.settings);
    next.sequence = integer(value.sequence, 0, Number.MAX_SAFE_INTEGER, 0);
    next.createdAt = Number.isFinite(value.createdAt) ? value.createdAt : 0;
    next.updatedAt = Number.isFinite(value.updatedAt) ? value.updatedAt : next.createdAt;
    next.progress = {};
    for (const [id, p] of Object.entries(value.progress)) {
      if (!accepted(id)) continue;
      if (!p || typeof p !== 'object' || !STATUSES.has(p.status)) return null;
      const normalized = { ...newProgress(), ...copy(p) };
      if(normalized.mixedRequired!==undefined && typeof normalized.mixedRequired!=='boolean' ||
        normalized.mixedCompletedAt!==undefined && normalized.mixedCompletedAt!==null && !Number.isFinite(normalized.mixedCompletedAt))return null;
      for (const key of ['introducedAt', 'lastStudiedAt', 'dueAt']) if (normalized[key] !== null && !Number.isFinite(normalized[key])) return null;
      for (const key of ['learningCount', 'reviewCount', 'practiceCount', 'knownCount', 'forgotCount', 'spellingAttempts', 'spellingCorrect'])
        normalized[key] = integer(normalized[key], 0, Number.MAX_SAFE_INTEGER, 0);
      normalized.stage = integer(normalized.stage, 0, REVIEW_INTERVAL_DAYS.length, 0);
      next.progress[id] = normalized;
    }
    for (const entry of Object.values(next.wordBank)) {
      if (entry.label === 'known' && next.progress[entry.id]?.status !== 'familiar' ||
          entry.label === 'unknown' && next.progress[entry.id]?.status === 'familiar') return null;
    }
    next.favorites = unique(value.favorites.filter(accepted)); next.notes = {};
    for (const [id, note] of Object.entries(value.notes)) if (accepted(id) && typeof note === 'string' && note.trim()) next.notes[id] = note.slice(0, 8000);
    if (!next.history.every(e => e && typeof e === 'object' && ['memory', 'spelling', 'session','word-label'].includes(e.type) && Number.isFinite(e.at) &&
      (e.type !== 'word-label' || safeId(e.wordId) && ['unknown','known'].includes(e.label)))) return null;
    if (next.session !== null) {
      const s = next.session;
      if (s && s.groupIndex === undefined) s.groupIndex = Math.max(0, Math.floor((s.index - (s.phase === 'memory' ? 0 : 1)) / (s.plan?.groupSize || 1)));
      if (!s || !safeId(s.id) || !MODES.has(s.mode) || !PHASES.has(s.phase) || !Array.isArray(s.queue) ||
          s.queue.some(id => !sessionAccepted(id)) || unique(s.queue).length !== s.queue.length ||
          !Number.isInteger(s.index) || s.index < 0 || s.index > s.queue.length ||
          !Array.isArray(s.answers) || !Array.isArray(s.groupWordIds) || !Array.isArray(s.spellingQueue) ||
          !Array.isArray(s.spellResults) || !Array.isArray(s.spellingAttempts) || !Array.isArray(s.spellingRounds) ||
          !s.plan || !Number.isInteger(s.plan.groupSize) || s.plan.groupSize < 1 ||
          !Number.isSafeInteger(s.groupIndex) || s.groupIndex < 0 ||
          s.plan.dailyWordIds != null && (!Array.isArray(s.plan.dailyWordIds) || s.plan.dailyWordIds.some(id=>!safeId(id))) ||
          s.plan.newWordCandidates != null && (!Array.isArray(s.plan.newWordCandidates) || s.plan.newWordCandidates.some(id=>!safeId(id)) || unique(s.plan.newWordCandidates).length !== s.plan.newWordCandidates.length) ||
          !Number.isInteger(s.spellingIndex) || s.spellingIndex < 0 || s.spellingIndex > s.spellingQueue.length ||
          typeof s.paused !== 'boolean' || typeof s.revealed !== 'boolean') return null;
      if(s.plan.mixedRecipe!==undefined && !validRecipe(s.plan.mixedRecipe))return null;
      if(s.mixedAttempts!==undefined && (!Array.isArray(s.mixedAttempts) || s.mixedAttempts.some(a=>!a || !s.queue.includes(a.wordId) || !Number.isFinite(a.at) || typeof a.correct!=='boolean') || unique(s.mixedAttempts.map(a=>a.questionId)).length!==s.mixedAttempts.length))return null;
      if(s.phase==='mixed' && (!s.plan.mixedRecipe || !Array.isArray(s.mixedAttempts) || !validateMixedRound(s.mixedRound,s.queue) || typeof s.mixedInput!=='string' || s.mixedInput.length>200 || typeof s.mixedRevealed!=='boolean'))return null;
      if(s.phase==='mixed' && (JSON.stringify(s.plan.mixedRecipe)!==JSON.stringify(s.mixedRound.recipe) || s.mixedRound.wordIds.some(id=>!s.groupWordIds.includes(id))))return null;
      if (s.pendingGrade === undefined) s.pendingGrade = null;
      if (s.pendingGrade !== null && (!['known','forgot'].includes(s.pendingGrade) || !s.revealed)) return null;
      if (s.retryQueue === undefined && s.retryWordId === undefined) {
        // Old unfinished rounds may have moved on after a forgotten answer.
        // Preserve all recorded attempts, but require recognition before completion.
        s.retryQueue = s.phase === 'complete' || isSpellingMode(s.mode) ? [] : finalAnswers(s)
          .filter(a => a.grade === 'forgot' && next.progress[a.wordId]?.status !== 'familiar')
          .map(a => ({wordId:a.wordId, afterAttempt:s.answers.length}));
        // Preserve an old in-flight spelling answer/result exactly as saved.
        // CONTINUE consumes this same retryQueue at the next safe group boundary.
        s.retryWordId = s.phase === 'memory' ? s.retryQueue[0]?.wordId || null : null;
        if (s.retryWordId) {
          s.phase = 'memory'; s.completedAt = null;
          s.groupWordIds = unique([...s.groupWordIds, ...s.retryQueue.map(r=>r.wordId)]);
          clearSpellingGroup(s); resetPrompt(s);
        }
      }
      if (!Array.isArray(s.retryQueue) || s.retryQueue.some(r => !r || !s.queue.includes(r.wordId) ||
          !Number.isSafeInteger(r.afterAttempt) || r.afterAttempt < 0 ||
          !s.answers.some(a=>a.wordId === r.wordId)) ||
          unique(s.retryQueue.map(r=>r.wordId)).length !== s.retryQueue.length ||
          s.retryWordId !== null && (!safeId(s.retryWordId) || !s.retryQueue.some(r=>r.wordId === s.retryWordId)) ||
          s.phase !== 'memory' && s.retryWordId !== null ||
          (s.phase === 'complete' || isSpellingMode(s.mode)) && s.retryQueue.length) return null;
      if ([...s.groupWordIds, ...s.spellingQueue].some(id => !s.queue.includes(id)) ||
          unique(s.groupWordIds).length !== s.groupWordIds.length ||
          unique(s.spellingQueue).length !== s.spellingQueue.length ||
          s.answers.some(a => !a || !safeId(a.eventId) || !s.queue.includes(a.wordId) || !['known', 'forgot'].includes(a.grade)) ||
          unique(s.answers.map(a => a.eventId)).length !== s.answers.length ||
          s.browseIndex !== null && (!Number.isInteger(s.browseIndex) || s.browseIndex < 0 || s.browseIndex >= s.index) ||
          s.phase === 'memory' && s.index >= s.queue.length && !s.retryWordId ||
          s.phase === 'spelling' && s.spellingIndex >= s.spellingQueue.length) return null;
      s.passageIndex = integer(s.passageIndex, 0, 1000, 0);
      s.spellingInput = String(s.spellingInput || '').slice(0, 200);
      s.hintLevel = integer(s.hintLevel, 0, 200, 0);
      if (typeof s.spellingHinted !== 'boolean' || typeof s.spellingRevealed !== 'boolean') return null;
      if(s.mode==='dictation'&&s.audioHeard!==undefined&&typeof s.audioHeard!=='boolean')return null;
      if (s.context !== undefined && s.context !== null) {
        const context = s.context;
        if (!context || !safeId(context.groupId) || typeof context.title !== 'string' ||
            context.topic !== undefined && (typeof context.topic !== 'string' || context.topic.length > 100) ||
            !Array.isArray(context.paragraphIds) || !context.paragraphIds.length ||
            context.paragraphIds.some(id => !safeId(id)) || unique(context.paragraphIds).length !== context.paragraphIds.length ||
            !Number.isInteger(context.index) || context.index < 0 || context.index >= context.paragraphIds.length) return null;
        if (context.scroll && (!s.queue.includes(context.scroll.wordId) || !safeId(context.scroll.paragraphId) ||
            !Number.isInteger(context.scroll.offset) || context.scroll.offset < -1000 || context.scroll.offset > 50000 ||
            typeof context.scroll.revealed !== 'boolean')) return null;
      }
    }
    if (next.parkedSessions === undefined) next.parkedSessions = [];
    if (!Array.isArray(next.parkedSessions)) return null;
    for (const parked of next.parkedSessions) {
      if (!parked || parked.reason !== 'collection-changed' || !Number.isFinite(parked.parkedAt) ||
          !Array.isArray(parked.missingWordIds) || parked.missingWordIds.some(id => !safeId(id))) return null;
      const archived = validateState({ ...createState(next.updatedAt), session: parked.session });
      if (!archived?.session) return null;
      parked.session = archived.session;
    }
    return next;
  } catch { return null; }
}

/** Keep old words and complete session snapshots when a different collection loads.
 * This is a pure, idempotent read-time reconciliation. Storage persists it only
 * together with a later authorized user action; the original cache is not cleared.
 */
export function reconcileCollection(state, words, now = state.updatedAt) {
  if (!state.session) return state;
  const map = wordMap(mergeStudyWords(words, state)), missingWordIds = state.session.queue.filter(id => !map.has(id));
  if (!missingWordIds.length) return state;
  const next = copy(state), s = next.session, at = time(now);
  next.parkedSessions ||= [];
  if (!next.parkedSessions.some(parked => parked.session.id === s.id)) next.parkedSessions.push({
    reason: 'collection-changed', parkedAt: at, missingWordIds: unique(missingWordIds), session: copy(s),
  });
  if (s.phase !== 'complete' && !next.history.some(event => event.type === 'session' && event.sessionId === s.id)) {
    next.history.push({ id: `archive-${s.id}`, type: 'session', sessionId: s.id,
      mode: s.mode, at, startedAt: s.startedAt, outcome: 'archived', reason: 'collection-changed',
      wordIds: [...s.queue], studied: finalAnswers(s).length, known: finalAnswers(s).filter(answer => answer.grade === 'known').length,
      forgot: finalAnswers(s).filter(answer => answer.grade === 'forgot').length,
      spellingAttempts: s.spellingAttempts.length, spellingCorrect: s.spellingAttempts.filter(answer => answer.correct).length });
  }
  next.session = null;
  return next;
}
