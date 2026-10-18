import {createState, validateState, reconcileCollection, mergeStudyWords} from './engine.js?v=509356376181';
import {config} from './config.js?v=509356376181';

// PostgreSQL jsonb reorders object keys; that is not a competing edit.
const canonical = value => value && typeof value === 'object'
  ? Array.isArray(value) ? '['+value.map(canonical).join(',')+']'
    : '{'+Object.keys(value).sort().map(k=>JSON.stringify(k)+':'+canonical(value[k])).join(',')+'}'
  : JSON.stringify(value);

// Only the account adapter may authorize an authenticated UID. A caller's
// {verified:true} flag alone never grants access. Reducers are synchronous
// and immutable, as in the domain engine. The optional host is for isolated tests.
export function createStore(words, onChange = () => {}, authorize = null, host = globalThis, remote = null, options = {}) {
  let identity = null, state = createState(), revision = 0, healthy = true, generation = 0;
  let chain = Promise.resolve(), disposed = false;
  let syncStatus = {phase:remote?'guest':'local'}, cloudRun = null, syncTimer = null;
  let retryDelay = options.retryMs ?? 3000, queuedSync = false, hydrated = false;
  const later = (fn, ms) => { const timer = (host.setTimeout || globalThis.setTimeout)(fn, ms); timer?.unref?.(); return timer; };
  const cancel = timer => (host.clearTimeout || globalThis.clearTimeout)(timer);
  const keyFor = uid => config.storagePrefix + encodeURIComponent(uid);
  const key = () => identity ? keyFor(identity.uid) : null;
  const protectedMessage = '已有记录无法读取。原记录已保留，请先导出备份。';
  const changedMessage = '账号已切换，本次操作未保存；原账号记录仍保留。';
  function notify(error) { if (!disposed) onChange(state, error); }
  function assertAuthorized(uid) {
    if (disposed) throw new Error('记录连接已关闭');
    if (typeof authorize !== 'function') throw new Error('请先验证网站账号后保存。');
    const result = authorize(uid);
    if (result && typeof result.then === 'function') throw new Error('账号验证尚未完成，请稍后再试。');
    if (result === false) throw new Error('请先验证网站账号后保存。');
  }
  function assertCurrent(uid, expectedGeneration) {
    if (disposed || generation !== expectedGeneration || (identity?.uid || null) !== uid) throw new Error(changedMessage);
    if (uid) assertAuthorized(uid);
  }
  function read(storageKey) {
    const raw = host.localStorage.getItem(storageKey);
    if (raw === null) return {revision: 0, state: createState(), cloudRevision:0, cloudPending:false, conflicts:[]};
    let parsed;
    try { parsed = JSON.parse(raw); } catch { throw new Error(protectedMessage); }
    const value = validateState(parsed?.state);
    if (!value || !Number.isSafeInteger(parsed?.revision) || parsed.revision < 1) throw new Error(protectedMessage);
    const reconciled = reconcileCollection(value, mergeStudyWords(words, value));
    if (!validateState(reconciled, words)) throw new Error(protectedMessage);
    if (parsed.cloudRevision !== undefined && (!Number.isSafeInteger(parsed.cloudRevision) || parsed.cloudRevision < 0) ||
        parsed.cloudPending !== undefined && typeof parsed.cloudPending !== 'boolean' ||
        parsed.conflicts !== undefined && !Array.isArray(parsed.conflicts)) throw new Error(protectedMessage);
    return {...parsed, revision: parsed.revision, state: reconciled,
      cloudRevision:parsed.cloudRevision || 0, cloudPending:parsed.cloudPending ?? true, conflicts:parsed.conflicts || []};
  }
  function checkedReduction(reducer, previous) {
    const next = reducer(previous);
    if (next === previous) return previous;
    // The reducer receives the latest locked state. Its bank, not a stale UI
    // word list, determines which personal identities may be saved or resumed.
    if (!next || typeof next.then === 'function' || !validateState(next, mergeStudyWords(words, next))) throw new Error('本次学习记录格式无效，已有记录未改动。');
    return next;
  }
  function update(reducer) {
    if (typeof reducer !== 'function') return Promise.reject(new Error('学习动作无效。'));
    const owner = identity?.uid || null, expectedGeneration = generation;
    const storageKey = owner ? keyFor(owner) : null;
    const run = async () => {
      assertCurrent(owner, expectedGeneration);
      if (!owner) {
        if (options.canUseGuest?.() === false) throw new Error('正在恢复设备登录，请稍候；确认账号后会自动载入进度。');
        const next = checkedReduction(reducer, state);
        assertCurrent(null, expectedGeneration);
        state = next; notify(); return state;
      }
      if (!healthy) throw new Error('记录保护中，请先导出原始备份。');
      if (remote && !hydrated) {
        await sync(); assertCurrent(owner, expectedGeneration);
        if (!hydrated) throw new Error('正在取回账号进度，请稍候再试；已有记录不会被覆盖。');
      }
      if (!host.navigator?.locks?.request) throw new Error('当前浏览器不支持安全保存，请使用新版浏览器。');
      return host.navigator.locks.request(storageKey + ':write', () => {
        assertCurrent(owner, expectedGeneration);
        let latest;
        try { latest = read(storageKey); }
        catch (error) { healthy = false; notify(error); throw error; }
        const next = checkedReduction(reducer, latest.state);
        assertCurrent(owner, expectedGeneration);
        if (next !== latest.state) {
          if (latest.revision >= Number.MAX_SAFE_INTEGER) throw new Error('记录版本已达到上限，请先导出备份。');
          const envelope = {...latest, revision: latest.revision + 1, savedAt: Date.now(), state: next,
            ...(remote?{cloudPending:true}:{} )};
          assertCurrent(owner, expectedGeneration);
          try { host.localStorage.setItem(storageKey, JSON.stringify(envelope)); }
          catch { throw new Error('本次记录未能保存到本机，请保留此页面后重试。'); }
          revision = envelope.revision;
          if (remote) syncStatus = {phase:'pending'};
        } else revision = latest.revision;
        state = next; notify(); if (remote) scheduleSync(); return state;
      });
    };
    const task = chain.then(run); chain = task.catch(() => {}); return task;
  }
  function setIdentity(session) {
    if (disposed) throw new Error('记录连接已关闭');
    const nextUid = session?.verified === true && typeof session.uid === 'string' && session.uid ? session.uid : null;
    if (nextUid) assertAuthorized(nextUid);
    // Transient authentication checking retains identity in the caller.
    // Repeated verified same-account notifications do not erase the session.
    if (nextUid === (identity?.uid || null)) return state;
    generation++;
    cloudRun = null; cancel(syncTimer); queuedSync = false; retryDelay = options.retryMs ?? 3000; hydrated = false;
    identity = nextUid ? Object.freeze({uid: nextUid}) : null;
    healthy = true; revision = 0;
    try {
      const saved = nextUid ? read(keyFor(nextUid)) : {revision: 0, state: createState()};
      state = saved.state; revision = saved.revision;
      hydrated = saved.revision > 0;
    } catch (error) {state = createState(); healthy = false; notify(error); return state;}
    syncStatus = {phase:nextUid&&remote?'pending':remote?'guest':'local'};
    notify(); if (nextUid && remote) scheduleSync(); return state;
  }
  function onStorage(event) {
    if (disposed || !identity || event.key !== key()) return;
    try { assertAuthorized(identity.uid); } catch { return; }
    try {
      const latest = read(key());
      if (latest.revision > revision) {state = latest.state; revision = latest.revision; notify();}
    } catch (error) {healthy = false; notify(error);}
  }
  host.addEventListener?.('storage', onStorage);
  function scheduleSync(wait = options.debounceMs ?? 250) {
    cancel(syncTimer);
    if (disposed || !remote || !identity || syncStatus.phase === 'conflict') return;
    if (cloudRun) { queuedSync = true; return; }
    syncTimer = later(() => sync().catch(() => {}), wait);
  }
  async function request(uid, action, operation) {
    let timer;
    try { return await Promise.race([remote(uid,action,operation), new Promise((_,reject)=>{
      timer = later(()=>reject(new Error('同步连接暂时超时，将自动重试')), options.requestTimeoutMs ?? 20000);
    })]); } finally { cancel(timer); }
  }
  function checkedCloud(row) {
    if (row === null) return null;
    if (!row || !Number.isSafeInteger(row.revision) || row.revision < 1 || typeof row.operationId !== 'string') throw new Error('云端记录格式异常，本机记录已保留');
    const value = validateState(row.state);
    if (!value) throw new Error('云端记录格式异常，本机记录已保留');
    const next = reconcileCollection(value, mergeStudyWords(words, value));
    if (!validateState(next, words)) throw new Error('云端记录词本不匹配，本机记录已保留');
    return {...row,state:next};
  }
  function sync(resolution = null) {
    if (!remote || !identity || disposed) return Promise.resolve();
    if (cloudRun) return cloudRun;
    cancel(syncTimer); queuedSync = false;
    const uid=identity.uid, epoch=generation, storageKey=keyFor(uid);
    const current=()=>assertCurrent(uid,epoch);
    const status=(phase,extra={})=>{current();if(phase==='synced'){hydrated=true;retryDelay=options.retryMs??3000;}syncStatus={phase,...extra};notify();};
    const task=(async()=>{
      try {
        current(); if (!healthy) throw new Error(protectedMessage);
        status('syncing');
        // Network work has its own cross-tab lock. The write lock only protects
        // local snapshots, so audio completion and answers save immediately.
        await host.navigator.locks.request(storageKey+':sync', async()=>{
          current();
          const cloud=checkedCloud((await request(uid,'read')).current);current();
          const cloudRevision=cloud?.revision||0;
          const persist=(local,next,pending,cloudRev,conflicts=local.conflicts)=>{
            current();
            const envelope={...local,revision:local.revision+1,savedAt:Date.now(),state:next,
              cloudRevision:cloudRev,cloudPending:pending,conflicts};
            host.localStorage.setItem(storageKey,JSON.stringify(envelope));
            // A receipt updates sync metadata; unchanged learning content keeps
            // its identity so the current card and progress stay still.
            if(canonical(state)!==canonical(next))state=next;
            revision=envelope.revision;
          };
          let upload=null;
          await host.navigator.locks.request(storageKey+':write',()=>{
            current();const local=read(storageKey);
            const different=canonical(local.state)!==canonical(cloud?.state);
            const conflict=local.cloudPending && cloudRevision!==local.cloudRevision && different;
            const choice=conflict && resolution?.expectedRevision===cloudRevision ? resolution.choice : null;
            if (conflict && !['local','cloud'].includes(choice)) {status('conflict',{revision:cloudRevision});return;}
            let backups=local.conflicts;
            if (choice) backups=[...backups,{at:Date.now(),source:choice==='local'?'cloud':'local',
              cloudRevision,state:choice==='local'?cloud?.state:local.state}];
            if (choice==='cloud' || !local.cloudPending && cloud && cloudRevision!==local.cloudRevision) {
              if (!choice && options.canRestore?.() === false) { status('download-available'); return; }
              persist(local,cloud.state,false,cloudRevision,backups);status('synced');return;
            }
            if (cloud && !different) {
              if (local.cloudPending || local.cloudRevision!==cloudRevision) persist(local,local.state,false,cloudRevision,backups);
              status('synced');return;
            }
            if (local.cloudPending) {upload={local,backups};return;}
            if (!cloud && local.cloudRevision>0) throw new Error('暂未读到已有云端记录，请重试');
            status('synced');
          });
          if(!upload)return;
          const operationId=(host.crypto||globalThis.crypto).randomUUID();
          const reply=await request(uid,'commit',{expectedRevision:cloudRevision,state:upload.local.state,operationId});current();
          await host.navigator.locks.request(storageKey+':write',()=>{
            current();const latest=read(storageKey);
            if (reply.ok!==true) {const winner=checkedCloud(reply.current);status('conflict',{revision:winner?.revision||0});return;}
            if (!Number.isSafeInteger(reply.revision) || reply.revision!==cloudRevision+1) throw new Error('云端保存回执异常，本机记录已保留');
            const edited=canonical(latest.state)!==canonical(upload.local.state);
            const backups=[...latest.conflicts,...upload.backups.slice(upload.local.conflicts.length)];
            // Acknowledging an older snapshot advances the cloud base while
            // keeping newer local answers queued for the next upload.
            persist(latest,latest.state,edited,reply.revision,backups);
            if(edited){queuedSync=true;status('pending');}else status('synced');
          });
        });
      } catch(error) {
        if (generation===epoch && identity?.uid===uid && !disposed) {
          syncStatus={phase:'offline',message:error.message};notify();
        }
      }
    })();
    cloudRun=task;task.finally(()=>{
      if(cloudRun!==task)return;
      cloudRun=null;
      if(syncStatus.phase==='offline'){const delay=retryDelay;retryDelay=Math.min(retryDelay*2,60000);scheduleSync(delay);}
      else if(queuedSync)scheduleSync();
    });return task;
  }
  const onReturn=()=>{if(remote&&identity&&syncStatus.phase!=='conflict')scheduleSync(0);};
  const onVisible=()=>{if(host.document?.visibilityState!=='hidden')onReturn();};
  host.addEventListener?.('focus',onReturn);host.addEventListener?.('online',onReturn);
  host.document?.addEventListener?.('visibilitychange',onVisible);
  const poll=(host.setInterval||globalThis.setInterval)(()=>{
    if(host.document?.visibilityState!=='hidden'&&host.navigator?.onLine!==false&&syncStatus.phase!=='offline')onReturn();
  },options.pollMs??10000);poll?.unref?.();
  return Object.freeze({
    get state() {return state;}, get identity() {return identity;},
    get syncStatus() {return {...syncStatus};}, sync,
    get writable() {
      if (disposed || !healthy) return false;
      try {if (identity) assertAuthorized(identity.uid); return true;} catch {return false;}
    },
    update, setIdentity,
    exportRaw: () => identity ? host.localStorage.getItem(key()) : JSON.stringify({state}),
    namespace: () => key(),
    dispose() {disposed = true; generation++; cancel(syncTimer);(host.clearInterval||globalThis.clearInterval)(poll);host.document?.removeEventListener?.('visibilitychange',onVisible);host.removeEventListener?.('storage', onStorage);host.removeEventListener?.('focus',onReturn);host.removeEventListener?.('online',onReturn);},
  });
}
