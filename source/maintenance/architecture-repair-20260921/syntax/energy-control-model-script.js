/* Pure session clock: elapsed wall time, never a health score or exam timer. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.IELTSEnergyModel = api;
})(typeof window === 'object' ? window : globalThis, function () {
  'use strict';
  const minutes = [5, 10, 15, 25], rests = [2, 3, 5];
  const initial = () => ({version: 1, mode: 'idle', minutes: 15, rest: 3, remaining: 900000, dueAt: 0, bookmark: null});
  function read(raw, now) {
    if (!raw) return initial();
    const x = JSON.parse(raw);
    if (!x || x.version !== 1 || !['idle','running','paused','due','break','ready'].includes(x.mode) ||
        !minutes.includes(x.minutes) || !rests.includes(x.rest) || !Number.isFinite(x.remaining) || x.remaining < 0 ||
        x.remaining > 25 * 60000 || !Number.isFinite(x.dueAt) || x.dueAt < 0 ||
        (x.bookmark !== null && (!x.bookmark || typeof x.bookmark.hash !== 'string' || typeof x.bookmark.anchor !== 'string' ||
          !Number.isFinite(x.bookmark.y) || x.bookmark.y < 0))) throw Error('休息提醒记录无法读取');
    return tick({...x}, now);
  }
  function left(s, now) { return ['running','break'].includes(s.mode) ? Math.max(0,s.dueAt-now) : s.remaining; }
  function tick(s, now) {
    if ((s.mode === 'running' || s.mode === 'break') && s.dueAt <= now)
      return {...s, mode: s.mode === 'running' ? 'due' : 'ready', remaining: 0, dueAt: 0};
    return s;
  }
  function reduce(s, action, now) {
    s = tick(s, now);
    if (action.type === 'settings' && ['idle','ready'].includes(s.mode)) {
      return {...s, minutes: minutes.includes(action.minutes) ? action.minutes : s.minutes,
        rest: rests.includes(action.rest) ? action.rest : s.rest};
    }
    if (action.type === 'bookmark') return {...s, bookmark: action.bookmark};
    if (action.type === 'start' && ['idle','ready','paused'].includes(s.mode)) {
      const duration = s.mode === 'paused' ? s.remaining : s.minutes * 60000;
      return {...s, mode:'running', dueAt:now+duration, remaining:duration};
    }
    if (action.type === 'pause' && s.mode === 'running') return {...s, mode:'paused',remaining:left(s,now),dueAt:0};
    if (action.type === 'rest' && ['running','paused','due'].includes(s.mode))
      return {...s,mode:'break',remaining:s.rest*60000,dueAt:now+s.rest*60000};
    if (action.type === 'snooze' && s.mode === 'due') return {...s,mode:'running',remaining:3*60000,dueAt:now+3*60000};
    if (action.type === 'stop') return {...s,mode:'idle',remaining:s.minutes*60000,dueAt:0};
    return s;
  }
  return {initial,read,left,tick,reduce};
});
