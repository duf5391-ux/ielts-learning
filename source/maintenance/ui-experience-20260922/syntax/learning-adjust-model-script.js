/* Small, storage-independent rules used by the learning UI. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.IELTSLearning = api;
})(typeof window === 'object' ? window : globalThis, function () {
  'use strict';
  const object = x => x && typeof x === 'object' && !Array.isArray(x);
  const initial = () => ({version: 1, today: [], last: '', checked: {}, tests: {}, mock: null});
  function read(raw) {
    if (!raw) return initial();
    const s = JSON.parse(raw);
    if (!object(s) || s.version !== 1 || !Array.isArray(s.today) || s.today.length > 500 ||
        s.today.some(x => typeof x !== 'string') || typeof s.last !== 'string' ||
        !object(s.checked) || !object(s.tests) || (s.mock !== null && !object(s.mock))) throw Error('学习安排记录格式不正确');
    for (const v of Object.values(s.checked)) {
      if (!object(v) || typeof v.at !== 'string' || !object(v.answers) || Object.values(v.answers).some(x => typeof x !== 'string')) throw Error('首答记录格式不正确');
    }
    for (const t of Object.values(s.tests)) {
      if (!object(t) || !['queued','running','submitted'].includes(t.status) || !Number.isFinite(t.start) ||
          !Number.isFinite(t.duration) || !object(t.answers) || !Array.isArray(t.history) ||
          Object.values(t.answers).some(v => typeof v !== 'string') ||
          t.history.some(h => !object(h) || !['running','submitted'].includes(h.status) || !Number.isFinite(h.start) || !object(h.answers) || Object.values(h.answers).some(v=>typeof v!=='string')) ||
          (t.status==='submitted' && !Number.isFinite(t.submittedAt))) throw Error('测试记录格式不正确');
    }
    if (s.mock && (!Number.isFinite(s.mock.start) || !Array.isArray(s.mock.parts) || s.mock.parts.some(x => !['listening','reading','writing','speaking'].includes(x)))) throw Error('套题记录格式不正确');
    return s;
  }
  const filled = value => typeof value === 'string' && value.trim().length > 0;
  function progress(values) { const total = values.length, done = values.filter(Boolean).length; return {done,total,percent: total ? Math.round(done/total*100) : 0}; }
  function canCheck(keys, values) { return keys.length > 0 && keys.every(k => filled(values[k])); }
  function check(state, id, keys, values, at) {
    if (!canCheck(keys, values)) throw Error('先作答；不会的题可填写“暂时不会”。');
    if (state.checked[id]) return state;
    return {...state,checked:{...state.checked,[id]:{at,answers:Object.fromEntries(keys.map(k=>[k,values[k]]))}}};
  }
  const normal = value => String(value || '').normalize('NFKC').trim().toLowerCase().replace(/[’‘]/g,"'").replace(/\s+/g,' ');
  function score(answers, key) {
    const rows = Object.entries(key).map(([q, acceptable]) => ({q,answer:answers[q] || '',expected:acceptable.join(' / '),correct:acceptable.some(v => normal(v) === normal(answers[q]))}));
    return {correct:rows.filter(r=>r.correct).length,verified:rows.length,rows};
  }
  function startTest(state, id, now, duration, replace = false) {
    const old = state.tests[id];
    if (old && old.status === 'running' && !replace) return state;
    const history = old ? old.status==='queued' ? old.history : [...old.history, {status:old.status,start:old.start,submittedAt:old.submittedAt || null,answers:old.answers}] : [];
    return {...state,tests:{...state.tests,[id]:{status:'running',start:now,duration,answers:{},history}}};
  }
  function submitTest(state, id, answers, now) {
    const t = state.tests[id]; if (!t || t.status !== 'running') throw Error('请先开始本次测试');
    return {...state,tests:{...state.tests,[id]:{...t,status:'submitted',submittedAt:now,answers:{...answers}}}};
  }
  function queueMock(state, answers, now) {
    const ids=['listening','reading','writing','speaking'],tests={...state.tests};
    for(const id of ids){const old=tests[id];const history=old ? [...old.history] : [];if(old&&old.status!=='queued')history.push({status:old.status,start:old.start,submittedAt:old.submittedAt||null,answers:old.status==='running'?{...answers[id]}:{...old.answers}});tests[id]={status:'queued',start:0,duration:0,answers:{},history};}
    return {...state,mock:{start:now,parts:ids},tests};
  }
  return {initial,read,filled,progress,canCheck,check,normal,score,startTest,submitTest,queueMock};
});
