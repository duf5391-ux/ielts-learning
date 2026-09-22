"""Conservative HTML controller transform. Does not publish or change save fields.

Run with INPUT OUTPUT to write a separate candidate. transform(html) composes with
the media and workspace transforms; fail closed when an expected source changes.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "content-pipeline/runtime-performance-20260921"
MARKER = 'id="runtime-performance-style"'


def once(text: str, old: str, new: str) -> str:
    count = text.count(old)
    if count != 1:
        raise ValueError(f"Expected one runtime anchor, found {count}: {old[:100]}")
    return text.replace(old, new, 1)


def edit_script(html: str, needle: str, edit) -> str:
    matches = [m for m in re.finditer(r"(<script\b[^>]*>)([\s\S]*?)(</script>)", html)
               if needle in m.group(2)]
    if len(matches) != 1:
        raise ValueError(f"Expected one script containing {needle!r}, found {len(matches)}")
    m = matches[0]
    return html[:m.start(2)] + edit(m.group(2)) + html[m.end(2):]


def core(script: str) -> str:
    start = script.index('function wordCounts()')
    end = script.index('function unlock(id)', start)
    script = script[:start] + r'''// Cached static controls; synchronous record saving below is unchanged.
const wordCountIndex=new Map(),scoreIndex=new Map();
for(const output of $$('[data-wordcount]')){const k=output.dataset.wordcount;if(!wordCountIndex.has(k))wordCountIndex.set(k,[]);wordCountIndex.get(k).push({output,field:$(`[data-save="${k}"]`)});}
for(const control of $$('[data-score]')){const id=control.dataset.score;if(!scoreIndex.has(id))scoreIndex.set(id,{controls:[],output:$('#'+id+'-score'),total:control.dataset.total});scoreIndex.get(id).controls.push(control);}
function wordCounts(key){const groups=key===undefined?wordCountIndex.values():[wordCountIndex.get(key)||[]];for(const rows of groups)for(const {output,field} of rows)output.textContent=((field.value.trim().match(/\S+/g)||[]).length)+' 词（空白分隔计数）';}
function scores(id){const groups=id===undefined?scoreIndex.values():[scoreIndex.get(id)];for(const group of groups)if(group)group.output.textContent=group.controls.filter(n=>n.checked).length+' / '+group.total;}
''' + script[end:]
    return once(script,
        'save({fields:[el.dataset.save]});wordCounts();scores()',
        'save({fields:[el.dataset.save]});wordCounts(el.dataset.save);if(el.dataset.score)scores(el.dataset.score)')


def legacy_navigation(script: str) -> str:
    script = once(script, 'function updateProgress(){const s=stored(),n=',
                  'function updateProgress(){const s=stored(),entries=Object.entries(s.fields),n=')
    script = script.replace('Object.entries(s.fields).some', 'entries.some')
    script = once(script, "document.addEventListener('input',e=>{if(e.target.dataset.save)requestAnimationFrame(updateProgress)});",
                  "let progressPending=false;function queueProgress(){if(progressPending)return;progressPending=true;requestAnimationFrame(()=>{progressPending=false;updateProgress();});}\n document.addEventListener('input',e=>{if(e.target.dataset.save)queueProgress();});")
    return once(script, "if(e.target.closest('[data-freeze]'))requestAnimationFrame(updateProgress)",
                "if(e.target.closest('[data-freeze]'))queueProgress()")


def learning(script: str) -> str:
    script = once(script, 'notificationTimer, drawing = false;', 'notificationTimer, drawing = false;')
    old = "  function unitProgress(u) { return M.progress(u.steps.map(s => s.kind === 'checked' ? !!state.checked[s.key] : s.kind === 'check' ? value(s.key) === true : M.filled(value(s.key)))); }"
    script = once(script, old, '''  // Business visibility only: the startup shell may temporarily hide the whole app.
  const visible = n => !!n && !n.closest('[hidden],[data-la-focus-hidden],.ui-filtered,.la-hidden-legacy');
  const progressCache = new Map();
  function unitProgress(u) {if(!progressCache.has(u.id))progressCache.set(u.id,M.progress(u.steps.map(s => s.kind === 'checked' ? !!state.checked[s.key] : s.kind === 'check' ? value(s.key) === true : M.filled(value(s.key)))));return progressCache.get(u.id);}
  const unitProgressNodes=$$('[data-unit-progress]').map(n=>({n,u:units.get(n.dataset.unitProgress)}));
  const collectionProgressNodes=$$('[data-collection-progress]').map(n=>({n,ids:JSON.parse(n.dataset.collectionProgress).filter(id=>units.has(id))}));
  const gates=$$('[data-answer-gate]'),gateKeys=new Map(gates.map(n=>[n,JSON.parse(n.dataset.answerGate)]));
  const todaySurfaces=[$('#la-today-list'),$('#la-plan-list'),$('#la-resume'),$('#la-today-progress'),...$$('[data-project-progress]')];
''')
    script = once(script, '    state = next; return true;', '    state = next; progressCache.clear(); return true;')
    script = once(script, "    for (const mode of ['study','practice']) {", "    for (const mode of ['study','practice']) {\n      if($('#'+mode).hidden)continue;")
    script = once(script, '  function renderToday() {', '  function renderToday() {\n    if(!todaySurfaces.some(visible))return;')
    a=script.index('  function renderParts() {')
    b=script.index('  function gateValues(keys)', a)
    script=script[:a]+'''  function renderParts() {
    for(const {n,u} of unitProgressNodes)if(u&&visible(n))n.replaceChildren(bar(unitProgress(u),u.progressLabel||'完成'));
    for(const {n,ids} of collectionProgressNodes)if(visible(n))n.replaceChildren(bar(M.progress(ids.map(id=>unitProgress(units.get(id)).percent===100)),'单元'));
  }
'''+script[b:]
    # Every gate has an immutable key list; checking is still synchronous on reveal.
    script=script.replace('JSON.parse(gate.dataset.answerGate)', 'gateKeys.get(gate)')
    script=once(script, "  for(const gate of $$('[data-answer-gate]')) {", "  for(const gate of gates) {")
    script=once(script, "function refreshGates(){for(const gate of $$('[data-answer-gate]'))gate.classList.toggle('la-gate-locked',!canOpen(gate));}",
                "function refreshGates(){for(const gate of gates)if(visible(gate))gate.classList.toggle('la-gate-locked',!canOpen(gate));}")
    script=once(script, '    renderToday();renderParts();\n  }', '    renderToday();renderParts();refreshGates();\n  }')
    a=script.index("  document.addEventListener('input',e=>{const target=e.target;if(!target?.dataset.save||drawing)return;")
    b=script.index("  for(const mode of ['study','practice'])for(const kind", a)
    script=script[:a]+'''  // Coalesce paint work, not persistence. Keep every changed test/part in the batch.
  const dirtyTests=new Set(),dirtyTestParts=new Set();
  function queueViews(target){
    progressCache.clear();
    if(target?.dataset.testAnswer){dirtyTests.add(target.dataset.testAnswer);const part=target.closest('[data-test-part]');if(part)dirtyTestParts.add(part);}
    if(drawing)return;drawing=true;
    requestAnimationFrame(()=>{drawing=false;
      renderParts();refreshGates();renderToday();renderCards();
      const tests=[...dirtyTests],parts=[...dirtyTestParts];dirtyTests.clear();dirtyTestParts.clear();
      for(const id of tests){const out=$('#test-'+id+' [data-test-progress]');if(out)out.replaceChildren(bar(M.progress(Object.values(answerValues(id)).map(M.filled)),'已作答'));}
      for(const part of parts)part.querySelector('[data-test-part-progress]').replaceChildren(bar(M.progress([...part.querySelectorAll('[data-test-answer]')].map(f=>M.filled(f.value))),'已作答'));
    });
  }
  document.addEventListener('input',e=>{if(e.target?.dataset.save)queueViews(e.target);});
'''+script[b:]
    script=once(script, "document.addEventListener('ielts-record-committed',()=>{renderParts();refreshGates();renderToday();renderCards();});",
                "document.addEventListener('ielts-record-committed',()=>queueViews());")
    return once(script, '  renderCards();renderToday();renderParts();refreshGates();renderTests();panelRoute();setInterval(renderClocks,1000);',
                '  renderTests();panelRoute();setInterval(renderClocks,1000);')


def transform(html: str) -> str:
    if MARKER in html:
        return html
    html=edit_script(html, 'function wordCounts(){$$', core)
    html=edit_script(html, 'function updateProgress(){const s=stored()', legacy_navigation)
    html=edit_script(html, 'const index=cards.map(el=>({el,topic:el.dataset.tvTopic',
                     lambda _: (ASSETS/'vocabulary-runtime.js').read_text(encoding='utf-8'))
    html=edit_script(html, '  function unitProgress(u) { return M.progress(', learning)
    return once(html, '</head>', '<style id="runtime-performance-style">#topical-vocabulary:not([data-tv-ready]) .tv-grid{display:none}</style>\n</head>')


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    parser.add_argument('output', type=Path)
    args=parser.parse_args()
    if args.source.resolve()==args.output.resolve():
        raise SystemExit('Use a separate output path; this command does not overwrite its source.')
    output=transform(args.source.read_text(encoding='utf-8'))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(output,encoding='utf-8')
    print(args.output.resolve())


if __name__=='__main__':
    main()
