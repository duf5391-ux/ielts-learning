/* Storage-independent daily study planning and resumable session rules. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.IELTSDailyStudy = api;
})(typeof window === 'object' ? window : globalThis, function () {
  'use strict';
  const DURATIONS = [15, 30, 60];
  const CAPACITY = {15: 1, 30: 2, 60: 4};
  const ALLOCATIONS = {15: [2, 8, 4, 1], 20: [3, 10, 5, 2], 30: [5, 15, 8, 2], 60: [5, 35, 16, 4]};
  const FEEDBACK = ['retry', 'okay', 'skip'];
  const terminal = status => status === 'completed' || status === 'ended';
  const object = value => value !== null && typeof value === 'object' && !Array.isArray(value);
  const text = value => typeof value === 'string' && value.trim().length > 0;
  const nonnegative = value => Number.isFinite(value) && value >= 0;
  const clone = value => JSON.parse(JSON.stringify(value));
  const timestamp = value => (nonnegative(value) || (text(value) && Number.isFinite(Date.parse(value))));
  function requireThat(condition, message) { if (!condition) throw Error(message); }
  function strings(value, allowEmpty) {
    return Array.isArray(value) && (allowEmpty || value.length > 0) && value.every(text) && new Set(value).size === value.length;
  }
  function preferences(value) {
    requireThat(object(value) && DURATIONS.includes(value.minutes) && strings(value.skills, true), '学习偏好记录格式不正确');
    requireThat(value.readingCase === undefined || text(value.readingCase), '阅读材料选择格式不正确');
    requireThat(value.skills.length <= CAPACITY[value.minutes], value.minutes + ' 分钟最多选择 ' + CAPACITY[value.minutes] + ' 个板块');
  }
  function validatePlan(value) {
    requireThat(object(value) && DURATIONS.includes(value.minutes) && strings(value.skills, false) && text(value.reason), '学习安排格式不正确');
    requireThat(value.skills.length <= CAPACITY[value.minutes], '所选板块超过本次时长允许的数量');
    requireThat(Array.isArray(value.steps) && value.steps.length >= value.skills.length, '学习步骤数量不正确');
    const ids = new Set();
    const groups = [];
    value.steps.forEach((step, index) => {
      requireThat(object(step) && text(step.id) && !ids.has(step.id) && text(step.title) && text(step.instruction) && text(step.target) && Number.isInteger(step.minutes) && step.minutes > 0, '学习步骤记录格式不正确');
      if (groups[groups.length - 1] !== step.skill) groups.push(step.skill);
      ids.add(step.id);
    });
    requireThat(JSON.stringify(groups) === JSON.stringify(value.skills), '学习步骤与所选板块不一致');
    requireThat(value.steps.reduce((sum, step) => sum + step.minutes, 0) === value.minutes, '学习步骤总时长不正确');
  }
  function validateSession(value, historyEntry) {
    validatePlan(value);
    requireThat(text(value.id) && ['active', 'paused', 'completed', 'ended'].includes(value.status) && timestamp(value.startedAt), '学习进度记录格式不正确');
    requireThat(Number.isInteger(value.index) && value.index >= 0 && value.index <= value.steps.length && strings(value.completed, true), '学习步骤进度不正确');
    requireThat(value.completed.length === value.index && value.completed.every((id, index) => id === value.steps[index].id), '已完成步骤与当前进度不一致');
    requireThat(nonnegative(value.elapsedMs) && nonnegative(value.stepElapsedMs) && value.stepElapsedMs <= value.elapsedMs, '学习计时记录格式不正确');
    requireThat(typeof value.note === 'string' && (value.feedback === null || FEEDBACK.includes(value.feedback)), '学习反馈记录格式不正确');
    if (value.status === 'completed') {
      requireThat(value.index === value.steps.length && timestamp(value.completedAt) && value.stepElapsedMs === 0, '完成记录与学习进度不一致');
    } else if (value.status === 'ended') {
      requireThat(value.index < value.steps.length && timestamp(value.completedAt), '提前结束记录与学习进度不一致');
    } else {
      requireThat(!historyEntry && value.index < value.steps.length && value.feedback === null && !Object.prototype.hasOwnProperty.call(value, 'completedAt'), '进行中的学习记录不正确');
    }
  }
  function validateState(state) {
    requireThat(object(state) && state.version === 1, '学习记录版本或格式不正确');
    preferences(state.preferences);
    requireThat(Array.isArray(state.history) && state.history.length <= 30, '学习历史记录格式不正确');
    const ids = new Set();
    state.history.forEach(session => {
      validateSession(session, true);
      requireThat(!ids.has(session.id), '学习历史存在重复记录');
      ids.add(session.id);
    });
    if (state.session !== null) {
      validateSession(state.session, false);
      if (terminal(state.session.status)) {
        const archived = state.history.find(session => session.id === state.session.id);
        requireThat(archived && JSON.stringify(archived) === JSON.stringify(state.session), '当前结束记录与学习历史不一致');
      } else requireThat(!ids.has(state.session.id), '进行中的学习已存在于归档历史');
    }
    return state;
  }
  function initial() { return {version: 1, preferences: {minutes: 30, skills: []}, session: null, history: []}; }
  function read(raw) {
    if (raw === null || raw === undefined) return initial();
    let parsed;
    try { parsed = typeof raw === 'string' ? JSON.parse(raw) : raw; }
    catch (_) { throw Error('学习记录无法读取，请先保留原记录再处理'); }
    validateState(parsed);
    return clone(parsed);
  }
  function forDuration(value, minutes, label) {
    if (text(value)) return value;
    requireThat(object(value), '学习步骤缺少' + label);
    const key = Object.keys(value).filter(key => /^\d+$/.test(key) && Number(key) <= minutes).sort((a, b) => Number(b) - Number(a))[0];
    requireThat(key !== undefined && text(value[key]), '学习步骤缺少对应时长的' + label);
    return value[key];
  }
  function plan(prefs, catalog, history, now) {
    preferences(prefs);
    requireThat(Array.isArray(catalog) && catalog.length > 0, '暂时没有可安排的学习板块');
    requireThat(Array.isArray(history), '学习历史记录格式不正确');
    const catalogIds = new Set();
    catalog.forEach(item => {
      requireThat(object(item) && text(item.skill) && !catalogIds.has(item.skill) && text(item.label) && text(item.title) && Array.isArray(item.stages) && item.stages.length > 0, '学习板块配置不正确');
      item.stages.forEach(stage => requireThat(object(stage) && text(stage.title) && (text(stage.target) || object(stage.target)) && (text(stage.instruction) || object(stage.instruction)), '学习板块步骤配置不正确'));
      catalogIds.add(item.skill);
    });
    requireThat(prefs.skills.every(skill => catalogIds.has(skill)), '所选学习板块不存在');
    // Full stored session snapshots and concise planner history are both accepted.
    history.forEach(session => requireThat(object(session) && strings(session.skills, false) && (session.feedback === null || FEEDBACK.includes(session.feedback)) && (session.status === undefined || terminal(session.status)), '学习历史记录格式不正确'));
    let selected, reason;
    if (prefs.skills.length) {
      selected = catalog.filter(item => prefs.skills.includes(item.skill));
      reason = '按你选择的板块安排，材料精读和写作前置计入本次用时。';
    } else {
      // A later result on a skill supersedes an older request to repeat it.
      const latest = new Map();
      for (let i = history.length - 1; i >= 0; i--) {
        if (history[i].status === 'ended' && history[i].feedback === null) continue;
        history[i].skills.forEach(skill => { if (catalogIds.has(skill) && !latest.has(skill)) latest.set(skill, {index: i, feedback: history[i].feedback}); });
      }
      const retry = catalog.filter(item => latest.get(item.skill)?.feedback === 'retry').sort((a, b) => latest.get(b.skill).index - latest.get(a.skill).index)[0];
      const next = retry || catalog.slice().sort((a, b) => (latest.get(a.skill)?.index ?? -1) - (latest.get(b.skill)?.index ?? -1))[0];
      selected = [next];
      reason = retry ? '上次你选择了「还想再练」，今天继续巩固' + next.label + '。' : latest.size ? '根据学习记录和反馈轮换，今天练习' + next.label + '。' : '先从' + next.label + '开始；也可以按你的需要换板块。';
    }
    const perSkill = prefs.minutes / selected.length;
    const allocation = ALLOCATIONS[perSkill];
    requireThat(allocation, '当前时长无法分配到所选板块');
    let reading = null;
    selected = selected.map(item => {
      if (item.skill !== 'reading' || !item.variants?.length) return item;
      let choices = item.variants.filter(v => v.minMinutes <= perSkill);
      const writingSkills=selected.filter(s=>s.skill.startsWith('writing')).map(s=>s.skill);
      if(!prefs.readingCase&&writingSkills.length){
        const paired=choices.filter(v=>v.writingTargets?.some(w=>writingSkills.includes(w.skill)));
        if(paired.length)choices=paired;
      }
      requireThat(choices.length > 0, '这段时间不足以安排完整阅读与精读，请增加用时');
      if (prefs.readingCase) {
        reading = choices.find(v => v.id === prefs.readingCase);
        requireThat(reading, '所选阅读材料需要更多时间，请增加用时或更换材料');
      } else {
        const previous = history.slice().reverse().find(s => s.steps?.some(step => step.materialCaseId));
        const previousId = previous?.steps.find(step => step.materialCaseId)?.materialCaseId;
        const index = choices.findIndex(v => v.id === previousId);
        reading = choices[previous?.feedback === 'retry' && index >= 0 ? index : (index + 1) % choices.length];
      }
      requireThat(text(reading.id) && Array.isArray(reading.stages) && reading.stages.length > 0, '阅读材料配置不完整');
      return {...item, ...reading, skill: item.skill, materialCaseId: reading.id};
    });
    if (reading) selected = selected.map(item => {
      if (!['writing1','writing2'].includes(item.skill)) return item;
      const target = reading.writingTargets.find(w => w.skill === item.skill);
      if (!target) return item;
      const output = item.skill === 'writing2'
        ? (perSkill <= 20 ? '围绕本题写一个展开充分的主体段，约80–100词。' : perSkill <= 30 ? '围绕本题写两个主体段，约180–220词。' : '围绕本题完成250词以上的文章。')
        : (perSkill <= 20 ? '看图写概览和一组关键细节，暂不要求完整作文。' : '依据图表完成150词以上的文章。');
      return {...item, writingCaseId: target.id, readingSourceId: reading.id, stages: [
        {title: (item.skill === 'writing2' ? 'Task 2' : 'Task 1')+' · '+target.title, target: target.primerTarget, instruction: '先看刚才阅读材料中适合本题的表达与例句，再读下方题目。'+output, weight: 0.8},
        {title: '读自己的文字，修改表达', target: target.target, instruction: '通读自己的文字，检查词义、搭配和句子是否准确表达了本意；需要时回看题目前的词句。', weight: 0.2}
      ]};
    });
    function minutesFor(item) {
      if (item.stages.length === 4 && !item.stages.some(s => s.weight)) return allocation;
      const weights = item.stages.map(s => Number(s.weight) || 1), total = weights.reduce((a,b)=>a+b,0);
      requireThat(item.stages.length <= perSkill, '本次内容过多，请增加时间');
      const result = weights.map(w => 1 + Math.floor((perSkill-item.stages.length)*w/total));
      for(let i=0, left=perSkill-result.reduce((a,b)=>a+b,0);left>0;i++,left--)result[i%result.length]++;
      return result;
    }
    const result = {
      minutes: prefs.minutes,
      skills: selected.map(item => item.skill),
      reason,
      steps: selected.flatMap(item => item.stages.map((stage, index) => ({
        id: item.skill + '-' + (index + 1), skill: item.skill, title: stage.title,
        instruction: forDuration(stage.instruction, perSkill, '说明'), target: forDuration(stage.target, perSkill, '材料入口'), minutes: minutesFor(item)[index],
        ...(item.materialCaseId ? {materialCaseId:item.materialCaseId} : {}),
        ...(item.writingCaseId ? {writingCaseId:item.writingCaseId,readingSourceId:item.readingSourceId} : {})
      })))
    };
    validatePlan(result);
    return result;
  }
  function start(state, proposal, now) {
    validateState(state);
    validatePlan(proposal);
    requireThat(timestamp(now), '开始时间格式不正确');
    requireThat(!state.session || terminal(state.session.status), '请先完成或结束当前学习，不能覆盖未完成进度');
    const base = 'study-' + String(now).replace(/[^a-zA-Z0-9]/g, '-');
    const ids = new Set(state.history.map(session => session.id));
    let id = base, suffix = 1;
    while (ids.has(id)) id = base + '-' + suffix++;
    return {...state, session: {...clone(proposal), id, index: 0, completed: [], status: 'active', startedAt: now, elapsedMs: 0, stepElapsedMs: 0, note: '', feedback: null}};
  }
  function advance(state, now) {
    validateState(state);
    requireThat(state.session && state.session.status === 'active', '请先开始或继续学习');
    requireThat(timestamp(now), '完成时间格式不正确');
    const old = state.session;
    const session = {...old, completed: [...old.completed, old.steps[old.index].id], index: old.index + 1, stepElapsedMs: 0};
    if (session.index < session.steps.length) return {...state, session};
    session.status = 'completed';
    session.completedAt = now;
    return {...state, session, history: [...state.history, clone(session)].slice(-30)};
  }
  function pause(state) {
    validateState(state);
    requireThat(state.session && !terminal(state.session.status), '没有可暂停的学习');
    return {...state, session: {...state.session, status: 'paused'}};
  }
  function resume(state) {
    validateState(state);
    requireThat(state.session && !terminal(state.session.status), '没有可继续的学习');
    return {...state, session: {...state.session, status: 'active'}};
  }
  function end(state, now) {
    validateState(state);
    requireThat(state.session && !terminal(state.session.status), '没有可结束的学习');
    requireThat(timestamp(now), '结束时间格式不正确');
    const session = {...state.session, status: 'ended', completedAt: now};
    return {...state, session, history: [...state.history, clone(session)].slice(-30)};
  }
  function tick(state, milliseconds) {
    validateState(state);
    requireThat(nonnegative(milliseconds), '学习计时增量必须是非负有限数');
    if (!state.session || state.session.status !== 'active' || milliseconds === 0) return state;
    const elapsedMs = state.session.elapsedMs + milliseconds;
    const stepElapsedMs = state.session.stepElapsedMs + milliseconds;
    requireThat(nonnegative(elapsedMs) && nonnegative(stepElapsedMs), '学习计时超出范围');
    return {...state, session: {...state.session, elapsedMs, stepElapsedMs}};
  }
  function feedback(state, value, note) {
    validateState(state);
    requireThat(state.session && terminal(state.session.status), '请完成或结束本次学习后再记录反馈');
    requireThat(FEEDBACK.includes(value) && typeof note === 'string', '学习反馈格式不正确');
    const session = {...state.session, feedback: value, note};
    return {...state, session, history: state.history.map(old => old.id === session.id ? clone(session) : old)};
  }
  function remaining(state) {
    validateState(state);
    if (!state.session || terminal(state.session.status)) return 0;
    const session = state.session;
    // Running over one step does not consume the recommended time for later steps.
    const current = Math.max(0, session.steps[session.index].minutes * 60 - session.stepElapsedMs / 1000);
    const later = session.steps.slice(session.index + 1).reduce((sum, step) => sum + step.minutes * 60, 0);
    return Math.ceil(current + later);
  }
  return {initial, read, plan, start, advance, pause, resume, end, tick, feedback, remaining};
});
