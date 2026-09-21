
/* RECORD-CONCURRENCY-20260920: shared storage protection, no browser data migration. */
(function (root, factory) {
  const api = factory();
  if (typeof module === 'object' && module.exports) module.exports = api;
  else root.IELTSRecordConcurrency = api;
})(typeof window === 'object' ? window : globalThis, function () {
  'use strict';
  const own = (value, key) => Object.prototype.hasOwnProperty.call(value, key);
  const clone = value => JSON.parse(JSON.stringify(value));
  const same = (a, b, key) => own(a, key) === own(b, key) && (!own(a, key) || JSON.stringify(a[key]) === JSON.stringify(b[key]));
  const set = (target, source, key) => {
    if (own(source, key)) Object.defineProperty(target, key, {value: clone(source[key]), writable: true, enumerable: true, configurable: true});
    else delete target[key];
  };
  function create(options) {
    let viewBase = clone(options.initial);
    let pending = {fields: new Set(), snapshots: new Set()};
    const empty = () => ({version: 1, fields: {}, snapshots: {}});
    function read() {
      const raw = options.read();
      return {raw, value: raw === null ? empty() : options.validate(JSON.parse(raw))};
    }
    function save(candidate, changes, retainOnFailure = true) {
      const before = pending;
      pending = {fields: new Set(before.fields), snapshots: new Set(before.snapshots)};
      for (const group of ['fields', 'snapshots']) for (const key of changes[group] || []) pending[group].add(key);
      function fail(reason, extra = {}) {
        if (!retainOnFailure) pending = before;
        return {ok: false, reason, ...extra};
      }
      let remote;
      try { remote = read(); } catch { return fail('external-invalid'); }
      const merged = {...remote.value, fields: {...remote.value.fields}, snapshots: {...remote.value.snapshots}};
      const conflicts = [];
      // Freezing a first answer must use the answers visible in this tab. An
      // unrelated merge may have refreshed state without refreshing controls.
      for (const [key, value] of Object.entries(changes.expectedFields || {})) {
        if (!same(remote.value.fields, viewBase.fields, key) && remote.value.fields[key] !== value) conflicts.push({group: 'fields', key});
      }
      for (const group of ['fields', 'snapshots']) {
        for (const key of pending[group]) {
          const localChanged = !same(candidate[group], viewBase[group], key);
          const remoteChanged = !same(remote.value[group], viewBase[group], key);
          if (localChanged && remoteChanged && !same(candidate[group], remote.value[group], key)) {
            conflicts.push({group, key});
          } else if (localChanged) set(merged[group], candidate[group], key);
        }
      }
      if (conflicts.length) return fail('conflict', {conflicts});
      const raw = JSON.stringify(merged);
      try {
        // A second check also covers a re-entrant storage adapter. localStorage is
        // synchronous, but has no cross-process compare-and-swap transaction.
        if (options.read() !== remote.raw) return fail('changed-again');
        if (raw !== remote.raw) options.write(raw);
        if (options.read() !== raw) return fail('storage');
      } catch { return fail('storage'); }
      const remoteUpdates = JSON.stringify(merged) !== JSON.stringify(candidate);
      for (const group of ['fields', 'snapshots']) {
        for (const key of pending[group]) set(viewBase[group], candidate[group], key);
      }
      pending = {fields: new Set(), snapshots: new Set()};
      return {ok: true, state: merged, remoteUpdates};
    }
    function restore(candidate, expectedRaw) {
      let raw;
      try {
        if (options.read() !== expectedRaw) return {ok: false, reason: 'changed-again'};
        raw = JSON.stringify(candidate);
        options.write(raw);
        if (options.read() !== raw) return {ok: false, reason: 'storage'};
      } catch { return {ok: false, reason: 'storage'}; }
      viewBase = clone(candidate);
      pending = {fields: new Set(), snapshots: new Set()};
      return {ok: true, state: candidate};
    }
    return {save, restore};
  }
  return {create};
});
