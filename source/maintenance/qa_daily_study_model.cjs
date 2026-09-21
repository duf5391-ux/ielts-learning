const assert = require('node:assert/strict');
const M = require('./daily-study-model.js');
let checks = 0;
function test(name, fn) { fn(); checks++; process.stdout.write('PASS ' + name + '\n'); }
const catalog = ['listening', 'reading', 'speaking', 'writing', 'review'].map(skill => ({
  skill, label: skill, title: skill + '练习', stages: Array.from({length: 4}, (_, i) => ({
    title: 'stage ' + i, instruction: {15: 'short', 30: 'regular', 60: 'full'}, target: '#' + skill + i
  }))
}));
const prefs = (minutes = 30, skills = []) => ({minutes, skills});
const proposal = (minutes = 30, skills = []) => M.plan(prefs(minutes, skills), catalog, [], 100);
const begin = () => M.start(M.initial(), proposal(), 100);
function finish(state) { while (state.session.status !== 'completed') state = M.advance(state, 200); return state; }
function deepFreeze(value) { if (value && typeof value === 'object') { Object.values(value).forEach(deepFreeze); Object.freeze(value); } return value; }

test('all supported selections preserve their full time budget and choose the right instruction', () => {
  for (const minutes of [15, 30, 60]) for (let n = 1; n <= ({15: 1, 30: 2, 60: 4})[minutes]; n++) {
    const plan = proposal(minutes, catalog.slice(0, n).map(x => x.skill));
    assert.equal(plan.steps.reduce((sum, step) => sum + step.minutes, 0), minutes);
    assert.equal(plan.steps.length, n * 4);
    assert.equal(plan.steps[0].instruction, minutes / n >= 60 ? 'full' : minutes / n >= 30 ? 'regular' : 'short');
    assert.equal(new Set(plan.steps.map(x => x.id)).size, plan.steps.length);
  }
  assert.deepEqual(proposal(60, ['listening', 'reading', 'speaking']).steps.slice(0, 4).map(x => x.minutes), [3, 10, 5, 2]);
});
test('selection capacity, unknown skills and duplicates are rejected without silently dropping choices', () => {
  for (const [minutes, selected] of [[15, ['reading', 'writing']], [30, ['reading', 'writing', 'speaking']], [60, catalog.map(x => x.skill)], [30, ['missing']], [30, ['reading', 'reading']]]) {
    assert.throws(() => proposal(minutes, selected));
  }
  assert.throws(() => proposal(20));
  assert.deepEqual(proposal(30, ['writing', 'reading']).skills, ['reading', 'writing']);
});
test('material targets use each skill budget and support a complete custom skill catalog', () => {
  const modules = ['listening', 'reading', 'writing1', 'writing2', 'speaking', 'vocabulary', 'background'].map(skill => ({
    skill, label: skill, title: skill, stages: catalog[0].stages.map(stage => ({...stage, target: {15: '#' + skill + '-short', 30: '#' + skill + '-medium', 60: '#' + skill + '-long'}}))
  }));
  assert.equal(M.plan(prefs(60, ['writing2']), modules, []).steps[0].target, '#writing2-long');
  assert.equal(M.plan(prefs(60, ['speaking', 'vocabulary']), modules, []).steps[4].target, '#vocabulary-medium');
  const three = M.plan(prefs(60, ['writing1', 'writing2', 'background']), modules, []);
  assert.equal(three.steps[8].target, '#background-short');
  assert.deepEqual(three.skills, ['writing1', 'writing2', 'background']);
});
test('first automatic plan avoids assumptions about legacy history and later plans use actual records', () => {
  const first = proposal();
  assert.equal(first.reason, '先从listening开始；也可以按你的需要换板块。');
  assert.doesNotMatch(first.reason, /没有学习记录|薄弱|弱项|错题|目标分/);
  assert.deepEqual(first.skills, ['listening']);
  const second = M.plan(prefs(), catalog, [{skills: ['listening'], feedback: 'okay'}]);
  assert.deepEqual(second.skills, ['reading']);
  const retry = M.plan(prefs(), catalog, [{skills: ['speaking'], feedback: 'retry'}]);
  assert.deepEqual(retry.skills, ['speaking']);
  assert.match(retry.reason, /还想再练/);
  const resolved = M.plan(prefs(), catalog, [{skills: ['speaking'], feedback: 'retry'}, {skills: ['speaking'], feedback: 'okay'}]);
  assert.deepEqual(resolved.skills, ['listening']);
});
test('paused and closed time never counts; serialization preserves the next step and elapsed time', () => {
  let state = M.tick(begin(), 2500);
  state = M.advance(state, 300);
  state = M.tick(state, 1250);
  state = M.pause(state, 500);
  const paused = JSON.stringify(state);
  assert.deepEqual(M.tick(state, 86400000), state);
  const restored = M.read(paused);
  state = M.resume(restored, 86400500);
  assert.equal(state.session.index, 1);
  assert.equal(state.session.elapsedMs, 3750);
  assert.equal(state.session.stepElapsedMs, 1250);
  assert.equal(state.session.startedAt, 100);
  assert.deepEqual(state.session.completed, ['listening-1']);
  assert.equal(M.remaining(state), 1499);
});
test('remaining time retains future steps if the current step runs over', () => {
  const state = M.tick(begin(), 600000);
  assert.equal(M.remaining(state), 1500);
  assert.equal(M.remaining(M.initial()), 0);
  assert.equal(M.remaining(finish(state)), 0);
});
test('completion archives exactly once and feedback synchronizes both snapshots', () => {
  const state = finish(begin());
  assert.equal(state.session.index, 4);
  assert.equal(state.session.completed.length, 4);
  assert.equal(state.history.length, 1);
  assert.deepEqual(state.history[0], state.session);
  assert.notEqual(state.history[0], state.session);
  assert.throws(() => M.advance(state, 300));
  const feedback = M.feedback(state, 'retry', '需要再听一遍');
  assert.deepEqual(feedback.history[0], feedback.session);
  assert.equal(state.session.feedback, null);
  assert.equal(feedback.session.note, '需要再听一遍');
  assert.deepEqual(M.read(JSON.stringify(feedback)), feedback);
  assert.throws(() => M.feedback(begin(), 'okay', 'too early'));
});
test('starting again cannot overwrite unfinished work; completed sessions can start fresh', () => {
  const active = begin();
  assert.throws(() => M.start(active, proposal(), 400));
  assert.throws(() => M.start(M.pause(active), proposal(), 400));
  const finished = finish(active);
  const next = M.start(finished, proposal(15, ['reading']), 100);
  assert.notEqual(next.session.id, finished.session.id);
  assert.equal(next.session.index, 0);
  assert.equal(next.history.length, 1);
  assert.deepEqual(next.session.skills, ['reading']);
});
test('ending active or paused study retains its actual progress and allows a different plan', () => {
  const existing = finish(begin());
  const oldHistory = JSON.stringify(existing.history);
  for (const paused of [false, true]) {
    let state = M.start(existing, proposal(30, ['reading']), 400);
    state = M.advance(M.tick(state, 2000), 410);
    state = M.tick(state, 4500);
    state = {...state, session: {...state.session, note: '停在第二步，已找到定位句'}};
    if (paused) state = M.pause(state);
    deepFreeze(state);
    const ended = M.end(state, 500);
    assert.equal(ended.session.status, 'ended');
    assert.equal(ended.session.completedAt, 500);
    for (const key of ['id', 'index', 'completed', 'elapsedMs', 'stepElapsedMs', 'note', 'startedAt']) assert.deepEqual(ended.session[key], state.session[key]);
    assert.equal(ended.session.index, 1);
    assert.equal(ended.session.stepElapsedMs, 4500);
    assert.equal(ended.history.length, 2);
    assert.deepEqual(ended.history[1], ended.session);
    assert.notEqual(ended.history[1], ended.session);
    assert.equal(JSON.stringify(ended.history.slice(0, 1)), oldHistory);
    assert.equal(M.remaining(ended), 0);
    assert.deepEqual(M.tick(ended, 900000), ended);
    assert.deepEqual(M.read(JSON.stringify(ended)), ended);
    assert.throws(() => M.end(ended, 501));
    assert.throws(() => M.resume(ended));
    assert.throws(() => M.pause(ended));
    assert.throws(() => M.advance(ended, 501));
    const next = M.start(ended, proposal(15, ['speaking']), 600);
    assert.equal(next.session.status, 'active');
    assert.equal(next.session.index, 0);
    assert.equal(next.session.elapsedMs, 0);
    assert.deepEqual(next.session.skills, ['speaking']);
    assert.deepEqual(next.history, ended.history);
  }
  assert.throws(() => M.end(M.initial(), 500));
  assert.throws(() => M.end(existing, 500));
});
test('ended sessions affect automatic planning only after explicit feedback', () => {
  const ended = M.end(begin(), 500);
  const ignored = M.plan(prefs(), catalog, ended.history);
  assert.deepEqual(ignored.skills, ['listening']);
  assert.equal(ignored.reason, proposal().reason);
  for (const value of ['okay', 'skip', 'retry']) {
    const recorded = M.feedback(ended, value, '用户主动选择');
    assert.equal(recorded.session.status, 'ended');
    assert.deepEqual(recorded.history[0], recorded.session);
    const next = M.plan(prefs(), catalog, recorded.history);
    assert.deepEqual(next.skills, [value === 'retry' ? 'listening' : 'reading']);
    M.read(JSON.stringify(recorded));
  }
  assert.equal(ended.session.feedback, null);
  const priorRetry = [{skills: ['listening'], feedback: 'retry', status: 'completed'}, ...ended.history];
  assert.match(M.plan(prefs(), catalog, priorRetry).reason, /还想再练/);
});
test('ended history shares the thirty-session limit and rejects inconsistent snapshots', () => {
  let state = M.initial();
  for (let i = 0; i < 33; i++) state = M.end(M.start(state, proposal(), i + 1), i + 100);
  assert.equal(state.history.length, 30);
  assert.equal(state.history[0].startedAt, 4);
  assert.equal(state.history[29].startedAt, 33);
  M.read(JSON.stringify(state));
  const corruptions = [
    s => { delete s.session.completedAt; },
    s => { s.session.index = s.session.steps.length; s.session.completed = s.session.steps.map(step => step.id); },
    s => { s.session.stepElapsedMs = s.session.elapsedMs + 1; },
    s => { s.history[0].note = 'different'; }
  ];
  for (const change of corruptions) { const s = M.end(begin(), 500); change(s); assert.throws(() => M.read(JSON.stringify(s))); }
});
test('history retains the latest thirty complete sessions', () => {
  let state = M.initial();
  for (let i = 0; i < 33; i++) state = finish(M.start(state, proposal(), i + 1));
  assert.equal(state.history.length, 30);
  assert.equal(state.history[0].startedAt, 4);
  assert.equal(state.history[29].startedAt, 33);
  M.read(JSON.stringify(state));
});
test('mutations preserve frozen input, and read returns an independent object', () => {
  const frozen = deepFreeze(begin());
  const before = JSON.stringify(frozen);
  M.tick(frozen, 100);
  M.pause(frozen);
  M.advance(frozen, 200);
  assert.equal(JSON.stringify(frozen), before);
  const restored = M.read(frozen);
  restored.session.steps[0].title = 'changed';
  assert.notEqual(frozen.session.steps[0].title, restored.session.steps[0].title);
  const p = deepFreeze(proposal());
  const newState = M.start(M.initial(), p, 300);
  newState.session.steps[0].title = 'changed';
  assert.notEqual(p.steps[0].title, newState.session.steps[0].title);
});
test('corrupt records fail loudly instead of being replaced with a fresh state', () => {
  assert.deepEqual(M.read(null), M.initial());
  assert.deepEqual(M.read(undefined), M.initial());
  for (const raw of ['', '{', 'null', '[]', 'false', '{}']) assert.throws(() => M.read(raw));
  const corruptions = [
    s => { s.version = 2; },
    s => { s.preferences.minutes = 20; },
    s => { s.preferences.skills = ['reading', 'reading']; },
    s => { s.session.steps[1].id = s.session.steps[0].id; },
    s => { s.session.index = 1; },
    s => { s.session.index = -1; },
    s => { s.session.index = 4; },
    s => { s.session.completed = ['wrong']; },
    s => { s.session.elapsedMs = -1; },
    s => { s.session.stepElapsedMs = 1; },
    s => { s.session.startedAt = 'bad date'; },
    s => { s.session.status = 'completed'; },
    s => { s.session.note = null; },
    s => { s.session.feedback = 'okay'; },
    s => { s.session.steps[0].minutes = 1; },
    s => { s.session.steps[0].skill = 'wrong'; },
    s => { s.history.push({...s.session}); },
    s => { delete s.session; }
  ];
  for (const change of corruptions) { const s = begin(); change(s); assert.throws(() => M.read(JSON.stringify(s))); }
  const s = begin(); s.session.elapsedMs = Infinity; assert.throws(() => M.read(s));
  const done = finish(begin()); done.history[0].feedback = 'retry'; assert.throws(() => M.read(done));
  const duplicated = finish(begin()); duplicated.history.push({...duplicated.history[0]}); assert.throws(() => M.read(duplicated));
  for (const ms of [-1, Infinity, NaN, '1']) assert.throws(() => M.tick(begin(), ms));
});
process.stdout.write(checks + ' daily study model checks passed\n');
