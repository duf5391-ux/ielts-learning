// Persist one allocation per visited study date. Unused places carry forward.
const dayOf = value => {
  const d = new Date(value);
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
};
const safeId = id => typeof id === 'string' && id.length > 0 && id.length < 200 && !['__proto__','prototype','constructor'].includes(id);
export function validDailyPlan(plan) {
  return plan === undefined || !!plan && typeof plan === 'object' &&
    /^\d{4}-\d{2}-\d{2}$/.test(plan.day) && dayOf(new Date(plan.day+'T12:00:00')) === plan.day &&
    Number.isSafeInteger(plan.target) && plan.target >= 1 && plan.target <= 300 &&
    Number.isSafeInteger(plan.carried) && plan.carried >= 0 &&
    Array.isArray(plan.wordIds) && plan.wordIds.every(safeId) && new Set(plan.wordIds).size === plan.wordIds.length &&
    Array.isArray(plan.beforeIds) && plan.beforeIds.every(safeId) && new Set(plan.beforeIds).size === plan.beforeIds.length;
}
const beforeDay = (state,ids,day) => ids.filter(id => Number.isFinite(state.progress[id]?.introducedAt) && dayOf(state.progress[id].introducedAt) < day);
const learnedIn = (state, ids, plan) => {const before=new Set(plan.beforeIds);return ids.filter(id => {
  const p=state.progress[id];
  return p && p.status !== 'familiar' && Number.isFinite(p.introducedAt) && !before.has(id);
}).length;};

export function getDailyPlan(state, now=Date.now(), wordIds) {
  const today=dayOf(now), saved=state.dailyPlan;
  const ids=[...new Set([...(saved?.wordIds || []), ...(wordIds || saved?.wordIds || state.session?.plan?.dailyWordIds || Object.keys(state.progress)), ...Object.keys(state.wordBank || {})])];
  let plan=saved;
  if(plan){
    // Undoing a first encounter from an earlier day restores that owed place.
    const beforeIds=plan.beforeIds.filter(id=>Number.isFinite(state.progress[id]?.introducedAt));
    if(beforeIds.length!==plan.beforeIds.length)plan={...plan,beforeIds,carried:plan.carried+plan.beforeIds.length-beforeIds.length};
  }
  if (!plan) {
    // Old records can establish the latest planned study day without inventing
    // allocations for every date since account creation.
    const scope=new Set(ids),dates=ids.map(id=>state.progress[id]?.introducedAt).filter(Number.isFinite);
    for(const e of state.history)if(e.mode==='learn' && Number.isFinite(e.at) && (scope.has(e.wordId) || e.wordIds?.some(id=>scope.has(id))))dates.push(e.at);
    const session=state.session;
    const prior=session?.mode==='learn' && Number.isFinite(session.startedAt) && session.queue.some(id=>scope.has(id))
      ? dayOf(session.startedAt) : dates.length ? dayOf(dates.reduce((latest,at)=>Math.max(latest,at),-Infinity)) : today;
    const day=prior < today ? prior : today;
    plan={day, target:state.settings.newPerDay, carried:0, wordIds:ids,beforeIds:beforeDay(state,ids,day)};
  }
  if (plan.day < today) {
    const before=new Set(plan.beforeIds);
    const priorLearned=ids.filter(id=>!before.has(id) && state.progress[id]?.status!=='familiar' &&
      Number.isFinite(state.progress[id]?.introducedAt) && dayOf(state.progress[id].introducedAt)<today).length;
    plan={day:today,target:state.settings.newPerDay,
      carried:Math.max(0,plan.carried+plan.target-priorLearned),wordIds:ids,
      beforeIds:beforeDay(state,ids,today)};
  } else {
    plan={...plan,wordIds:ids,target:plan.day===today ? state.settings.newPerDay : plan.target};
  }
  const learned=learnedIn(state,ids,plan), total=plan.carried+plan.target;
  return {...plan,learned,total,remaining:Math.max(0,total-learned)};
}

export function ensureDailyPlan(state, now=Date.now(), wordIds) {
  const {learned,total,remaining,...plan}=getDailyPlan(state,now,wordIds);
  if(JSON.stringify(state.dailyPlan)===JSON.stringify(plan))return state;
  return {...state,dailyPlan:plan,updatedAt:Number(now)};
}
