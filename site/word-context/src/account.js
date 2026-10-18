/* Standalone authentication only. No old learning controllers or progress keys.
 * SDK v3.10.0 configuration matches the existing site's published configuration.
 * Authentication storage is shared on the same origin; learning storage is not.
 */
export const SITE_ACCOUNT_CONFIG = Object.freeze({
  envId: 'ielts-learning-d5gnsv9d5e3b32220',
  region: 'ap-shanghai',
  publicKey: 'eyJhbGciOiJSUzI1NiIsImtpZCI6ImMyY2VmOWEzLTRhZTYtNGVhZi1hMDIyLTExZTRjZDA0NjA3MSJ9.eyJpc3MiOiJodHRwczovL2llbHRzLWxlYXJuaW5nLWQ1Z25zdjlkNWUzYjMyMjIwLmFwLXNoYW5naGFpLnRjYi1hcGkudGVuY2VudGNsb3VkYXBpLmNvbSIsInN1YiI6ImFub24iLCJhdWQiOiJpZWx0cy1sZWFybmluZy1kNWduc3Y5ZDVlM2IzMjIyMCIsImV4cCI6NDA5Mzc2NzAyNiwiaWF0IjoxNzkwMDgzODI2LCJub25jZSI6IklZR0dGaEdOUlRDbnRUbGN3R0dpb3ciLCJhdF9oYXNoIjoiSVlHR0ZoR05SVENudFRsY3dHR2lvdyIsIm5hbWUiOiJBbm9ueW1vdXMiLCJzY29wZSI6ImFub255bW91cyIsInByb2plY3RfaWQiOiJpZWx0cy1sZWFybmluZy1kNWduc3Y5ZDVlM2IzMjIyMCIsIm1ldGEiOnsicGxhdGZvcm0iOiJQdWJsaXNoYWJsZUtleSJ9LCJyb2xlIjoiYW5vbiIsImlzX2Fub255bW91cyI6dHJ1ZSwiYXBwX21ldGFkYXRhIjp7InByb3ZpZGVyIjoiYW5vbnltb3VzIiwicHJvdmlkZXJzIjpbImFub255bW91cyJdfSwidXNlcl9tZXRhZGF0YSI6eyJuYW1lIjoiQW5vbnltb3VzIn0sInVzZXJfdHlwZSI6IiIsImNsaWVudF90eXBlIjoiY2xpZW50X3VzZXIiLCJpc19zeXN0ZW1fYWRtaW4iOmZhbHNlfQ.nMU30HOsWXMWWUP8dvATHSlpDaDY1VivTjnzUod7VWuf8zPekVd9IaI8b0djSP8SHc6uL9HQkhiIGtXLAGbvFguo6ejdNZzH1om43tqyIGUiCqnykmuMkibmq2MPK9VrTJl4h8BIo7lpd7nd0KnzLHEiGYCRO_tYet1bM6lExHiA7fBu95A3KV-fCXSKWPx2kb3Xdmc_rNgGrcMWd8ky0bI6prESurVbYX-dlDNoHhStarvxUrKQIZYFZ1nSXYY7YyN-nR0rZSEvTmNcfKcjMlqcEny1nTac-_9IoKIOR2tKWcC_LeOwsXheZFxanxnQV6_QvvHubasV9ytaKAfVRg',
  registrationEnabled: true,
});

const AUTH_LOCK = 'ielts-auth-session-v1';
const AUTH_EPOCH = 'ielts-auth-transition-v1';
const IDENTITY_EVENTS = new Set(['SIGNED_IN', 'SIGNED_OUT', 'USER_UPDATED', 'PASSWORD_RECOVERY', 'BIND_IDENTITY']);
const hex = value => Array.from(new TextEncoder().encode(value), byte => byte.toString(16).padStart(2, '0')).join('');
export const accountOwner = (envId, uid) => `cb1:${hex(envId)}:${hex(uid)}`;

export function normalizePhone(value) {
  const phone = String(value ?? '').trim().replace(/[\s()-]/g, '').replace(/^(?:\+86|0086)/, '');
  if (!/^1[3-9]\d{9}$/.test(phone)) throw new Error('请输入正确的 11 位中国大陆手机号');
  return phone;
}

function unwrap(result) {
  if (result?.error) throw new Error(result.error.message || '账号服务暂时不可用');
  if (!result || !result.data || typeof result.data !== 'object') throw new Error('账号服务返回格式无效');
  return result.data;
}

export function createAccount(options = {}) {
  const host = options.host || globalThis;
  const config = options.config || SITE_ACCOUNT_CONFIG;
  const now = options.now || Date.now;
  const listeners = new Set();
  const cooldowns = new Map();
  let snapshot = Object.freeze({status: 'checking', user: null, revision: 0, error: null});
  let active = true, busy = false, challenge = null, challengeVersion = 0, verificationVersion = 0;
  let auth = null, app = null, subscription = null, setupError = null, verifiedEpoch = null;
  let refreshQueued = false, retryTimer = null, retryDelay = options.retryMs ?? 3000;
  const later = (fn, ms) => { const timer = (host.setTimeout || globalThis.setTimeout)(fn, ms); timer?.unref?.(); return timer; };
  const clearRetry = () => { (host.clearTimeout || globalThis.clearTimeout)(retryTimer); retryTimer = null; };
  function retryRefresh() {
    clearRetry();
    if (!active || setupError) return;
    retryTimer = later(() => { retryTimer = null; queueRefresh(); }, retryDelay);
    retryDelay = Math.min(retryDelay * 2, 60000);
  }
  async function readSession(operation) {
    let timer;
    try { return await Promise.race([operation(), new Promise((_,reject)=>{
      timer = later(()=>reject(new Error('账号连接暂时超时，正在自动重试')),options.requestTimeoutMs??20000);
    })]); } finally { (host.clearTimeout||globalThis.clearTimeout)(timer); }
  }

  function publish(status, user = null, error = null) {
    if (!active) return snapshot;
    snapshot = Object.freeze({status, user, revision: snapshot.revision + 1, error});
    for (const listener of listeners) {
      try { listener(snapshot); } catch (error) { host.console?.error?.('Account subscriber failed', error); }
    }
    return snapshot;
  }
  function assertActive() { if (!active) throw new Error('账号连接已关闭'); }
  function epoch() { return host.localStorage?.getItem(AUTH_EPOCH) || ''; }
  function advanceEpoch() {
    if (!host.localStorage || !host.crypto?.randomUUID) throw new Error('当前浏览器无法安全地切换账号');
    const value = host.crypto.randomUUID();
    host.localStorage.setItem(AUTH_EPOCH, value);
    if (epoch() !== value) throw new Error('账号切换未能确认，请重试');
    return value;
  }
  function cancelCode() { challengeVersion++; challenge = null; }
  function invalidate() {
    verificationVersion++;
    verifiedEpoch = null;
    publish('checking');
  }
  function queueRefresh() {
    if (!active || busy || refreshQueued) return;
    refreshQueued = true;
    // Provider callbacks may run while its auth lock is held. Re-enter on the
    // next task rather than awaiting another auth operation inside that lock.
    (host.setTimeout || globalThis.setTimeout)(() => {
      refreshQueued = false;
      if (active && !busy) refresh().catch(() => {});
    }, 0);
  }
  function userIdentity(user) {
    if (!user || typeof user.id !== 'string' || !user.id || user.id.length > 512 || user.is_anonymous === true || (!user.phone && !user.email)) {
      throw new Error('请使用网站的已验证手机或邮箱账号登录');
    }
    let phone = null;
    if (user.phone) {
      try { phone = normalizePhone(user.phone); }
      catch {
        phone = String(user.phone).replace(/[\s()-]/g, '');
        if (!/^\+[1-9]\d{6,14}$/.test(phone)) throw new Error('认证手机号格式无效');
      }
    }
    const email = typeof user.email === 'string' ? user.email : null;
    return Object.freeze({
      id: user.id, uid: user.id, provider: 'cloudbase', owner: accountOwner(config.envId, user.id),
      phone, email, displayName: phone ? `${phone.slice(0, 3)}****${phone.slice(-4)}` : email,
    });
  }

  async function refresh(expectedPhone = null) {
    assertActive();
    const ticket = ++verificationVersion;
    let startedEpoch;
    // A foreground verification is not a logout. Keep the verified account
    // visible while the SDK refreshes its own persistent session.
    const previous = snapshot.user;
    publish('checking', previous);
    const unchanged = () => {
      assertActive();
      if (ticket !== verificationVersion || epoch() !== startedEpoch) throw new Error('账号已在其他页面变化，请重新确认');
    };
    try {
      startedEpoch = epoch();
      if (setupError) throw setupError;
      const initial = unwrap(await readSession(()=>auth.getSession()));
      unchanged();
      if (!initial.session) {
        clearRetry(); retryDelay = options.retryMs ?? 3000;
        verifiedEpoch = null;
        if (expectedPhone) throw new Error('账号验证尚未完成');
        return publish('guest');
      }
      // getUser(true) asks the provider to validate the session. A cached UID alone is never accepted.
      const user = userIdentity(unwrap(await readSession(()=>auth.getUser(true))).user);
      unchanged();
      const before = initial.session.user?.id || initial.session.sub || initial.user?.id;
      const final = unwrap(await readSession(()=>auth.getSession()));
      unchanged();
      const after = final.session?.user?.id || final.session?.sub || final.user?.id;
      if (!before || !after || before !== user.uid || after !== user.uid) throw new Error('账号会话发生变化，请重新登录');
      if (expectedPhone && user.phone !== expectedPhone) throw new Error('当前登录的手机号已经变化，请重新登录');
      verifiedEpoch = startedEpoch;
      clearRetry(); retryDelay = options.retryMs ?? 3000;
      return publish('signed-in', user);
    } catch (error) {
      if (active && ticket === verificationVersion) {
        verifiedEpoch = null;
        const result = publish('unavailable', null, error.message || '暂时无法确认登录状态');
        retryRefresh(); return result;
      }
      return snapshot;
    }
  }

  async function guarded(operation) {
    assertActive();
    if (setupError) throw setupError;
    if (busy) throw new Error('账号操作正在进行，请稍候');
    if (!host.navigator?.locks?.request) throw new Error('当前浏览器暂不支持安全的账号切换，请更新浏览器后重试');
    busy = true;
    try {
      return await host.navigator.locks.request(AUTH_LOCK, {mode: 'exclusive', ifAvailable: true}, async lock => {
        if (!lock) throw new Error('另一页面正在验证账号，请稍后重试');
        return await operation();
      });
    } finally { busy = false; }
  }
  function retryAfter(phone) {
    return Math.max(0, Math.ceil(((cooldowns.get(normalizePhone(phone)) || 0) - now()) / 1000));
  }
  async function sendCode(value) {
    const phone = normalizePhone(value);
    return guarded(async () => {
      const remaining = retryAfter(phone);
      if (remaining) throw new Error(`请在 ${remaining} 秒后重新获取验证码`);
      cancelCode();
      const version = challengeVersion, startedEpoch = epoch();
      cooldowns.set(phone, now() + 60000);
      const data = unwrap(await auth.signInWithOtp({phone, options: {shouldCreateUser: config.registrationEnabled === true}}));
      assertActive();
      if (version !== challengeVersion || startedEpoch !== epoch()) throw new Error('账号已变化，请重新获取验证码');
      if (typeof data.verifyOtp !== 'function') throw new Error('短信验证码登录暂不可用');
      challenge = {version, phone, epoch: startedEpoch, verifyOtp: data.verifyOtp};
      return Object.freeze({phone, maskedPhone: `${phone.slice(0, 3)}****${phone.slice(-4)}`, retryAfter: retryAfter(phone)});
    });
  }
  async function verifyCode(value) {
    const code = String(value ?? '').trim();
    if (!/^\d{4,8}$/.test(code)) throw new Error('请输入短信中的数字验证码');
    return guarded(async () => {
      const pending = challenge;
      if (!pending || pending.version !== challengeVersion || pending.epoch !== epoch()) {
        cancelCode();
        throw new Error('验证码步骤已失效，请重新发送');
      }
      pending.epoch = advanceEpoch();
      invalidate();
      try {
        unwrap(await pending.verifyOtp({token: code}));
        assertActive();
        if (pending !== challenge || pending.epoch !== epoch()) throw new Error('账号已变化，请重新登录');
        const result = await refresh(pending.phone);
        if (result.status !== 'signed-in') throw new Error(result.error || '账号验证尚未完成');
        cancelCode();
        return result;
      } catch (error) {
        await refresh();
        throw error;
      }
    });
  }
  async function logout() {
    return guarded(async () => {
      cancelCode();
      advanceEpoch();
      invalidate();
      try {
        unwrap(await auth.signOut());
        return await refresh();
      } catch (error) { await refresh(); throw error; }
    });
  }
  function assertIdentity(uid) {
    assertActive();
    if (!uid || snapshot.status !== 'signed-in' || snapshot.user?.uid !== uid || verifiedEpoch !== epoch()) {
      throw new Error('登录状态已变化，请重新登录后保存；原账号记录仍保留');
    }
    return snapshot.user;
  }
  const onStorage = event => {
    if (event.key === AUTH_EPOCH) { cancelCode(); invalidate(); queueRefresh(); }
  };
  const onReturn = () => queueRefresh();
  const onVisible = () => { if (host.document?.visibilityState !== 'hidden') queueRefresh(); };
  try {
    const sdk = options.sdk || host.IELTSCloudBaseSDK;
    if (!sdk?.init) throw new Error('账号组件未能载入，请刷新后重试');
    if (!config.envId || !config.region || !config.publicKey) throw new Error('网站账号配置不完整');
    app = sdk.init({env: config.envId, region: config.region, accessKey: config.publicKey, persistence: 'local', auth: {detectSessionInUrl: false}});
    auth = app.auth;
    if (!auth || ['getSession', 'getUser', 'signInWithOtp', 'signOut', 'onAuthStateChange'].some(key => typeof auth[key] !== 'function')) {
      throw new Error('需要网站当前的 CloudBase v3 账号组件');
    }
    subscription = auth.onAuthStateChange((event, session) => {
      if (!active || busy) return;
      if (IDENTITY_EVENTS.has(event)) {
        cancelCode(); invalidate(); queueRefresh();
      } else if (event === 'TOKEN_REFRESHED' && snapshot.user && (session?.user?.id || session?.sub) !== snapshot.user.uid) {
        cancelCode(); invalidate(); queueRefresh();
      }
    });
  } catch (error) { setupError = error; }
  host.addEventListener?.('storage', onStorage);
  host.addEventListener?.('focus', onReturn);
  host.addEventListener?.('online', onReturn);
  host.document?.addEventListener?.('visibilitychange', onVisible);
  const ready = refresh();
  async function wordCloud(uid, action, operation = {}) {
    assertIdentity(uid);
    if (!app?.rdb || !['read','commit'].includes(action)) throw new Error('账号云端保存暂不可用');
    const parameters = {expected_subject:uid};
    if (action === 'commit') Object.assign(parameters, {expected_revision:operation.expectedRevision,
      record_state:operation.state, operation_id:operation.operationId});
    const reply = await app.rdb().rpc('word_context_' + action, parameters);
    assertIdentity(uid);
    if (reply?.error || !reply?.data) throw new Error('云端暂未同步，记录已保留在本机，请稍后重试');
    return reply.data;
  }
  return Object.freeze({
    ready, getSession: () => snapshot, refresh, sendCode, verifyCode, cancelCode, retryAfter, logout, assertIdentity, wordCloud,
    // The function does not expose tokens, SDK objects, or old progress APIs.
    subscribe(listener) { assertActive(); listeners.add(listener); listener(snapshot); return () => listeners.delete(listener); },
    dispose() {
      active = false; cancelCode(); verificationVersion++; clearRetry(); listeners.clear();
      subscription?.data?.subscription?.unsubscribe?.();
      host.removeEventListener?.('storage', onStorage);
      host.removeEventListener?.('focus', onReturn);
      host.removeEventListener?.('online', onReturn);
      host.document?.removeEventListener?.('visibilitychange', onVisible);
    },
  });
}
