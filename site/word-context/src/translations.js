// One offline catalog, keyed by exact displayed English. No network translation,
// learning-state writes or guessed fallback to another sentence's translation.
export function createTranslations(load = async () => {
  const response = await fetch(new URL('../data/translations.json', import.meta.url));
  if (!response.ok) throw new Error('译文暂时没加载成功，请再试一次');
  return response.json();
}) {
  let catalog, pending;
  async function lookup(text) {
    if (!catalog) {
      if (!pending) pending = Promise.resolve().then(load).then(data => {
        if (data?.schemaVersion !== 1 || !data.entries || typeof data.entries !== 'object') throw new Error('译文文件格式无效');
        catalog = data.entries;
      }).finally(() => { pending = null; });
      await pending;
    }
    const entry = Object.hasOwn(catalog, text) ? catalog[text] : null;
    return entry && typeof entry.zh === 'string' && entry.zh.trim() ? entry : null;
  }
  return {lookup};
}

// Temporary reveal state belongs to the currently visible card, not to progress.
// A late load cannot reveal a previous word or another account's card.
export function createTranslationView(catalog, changed = () => {}) {
  let view = {key:null,text:'',open:false,status:'idle',entry:null,error:null};
  function select(key, text) {
    if (view.key !== key || view.text !== text) view = {key,text,open:false,status:'idle',entry:null,error:null};
    return view;
  }
  async function toggle(key, text) {
    const selected = select(key,text);
    selected.open = !selected.open;
    if (!selected.open || selected.status === 'ready' || selected.status === 'missing' || selected.status === 'loading') {changed();return;}
    selected.status = 'loading'; selected.error = null; changed();
    try {
      const entry = await catalog.lookup(text);
      if (view !== selected) return;
      selected.entry = entry; selected.status = entry ? 'ready' : 'missing';
    } catch (error) {
      if (view !== selected) return;
      selected.status = 'error'; selected.error = error.message || '译文加载失败';
    }
    changed();
  }
  return {select,toggle};
}
