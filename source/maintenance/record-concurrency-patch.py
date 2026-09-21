"""Apply this transform to the latest book in memory; never write the formal book.

CLI writes a separate candidate and fails if its target is the formal source.
Integration API: patched_html = patch_html(current_html).
"""
from pathlib import Path
import argparse, re

ROOT = Path(__file__).resolve().parent
MODEL = ROOT / 'record-concurrency-model.js'
FORMAL = Path(r'C:\Users\Admin1\Documents\Codex\2026-09-12\referenced-chatgpt-conversation-this-is-an\outputs\IELTS-四科学习册\开始学习.html')

def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('Expected one current core fragment: ' + old[:100])
    return text.replace(old, new, 1)

def patch_html(html):
    if 'id="record-concurrency-model-script"' in html:
        raise ValueError('Record concurrency patch already present; review before reapplying')
    matches = [m for m in re.finditer(r'<script\b[^>]*>(.*?)</script>', html, re.S) if '/* RECORD-SAFETY-20260919 */' in m.group(1)]
    if len(matches) != 1: raise ValueError('Expected exactly one current main record script')
    match = matches[0]; core = match.group(1)
    # Callers integrating actual bytes may retain CRLF, while read_text uses
    # universal newlines. Normalize only this script for matching, then restore.
    newline = '\r\n' if '\r\n' in core else '\n'
    core = core.replace('\r\n', '\n')
    core = replace_once(core, "storageOK=true,recoveryRaw=null,loadBlocked=false;", "storageOK=true,recoveryRaw=null,loadBlocked=false,recordSaveIssue='';")
    core = replace_once(core, ":'当前未能保存，请导出文字或备份学习记录后再刷新。';}", ":recordSaveIssue||'当前未能保存，请导出文字或备份学习记录后再刷新。';}")
    old_save = "function save(){if(loadBlocked){$('#save-status').textContent=recordWarning();return false}try{const raw=JSON.stringify(state);localStorage.setItem(key,raw);if(localStorage.getItem(key)!==raw)throw Error('Record write was not retained');storageOK=true;$('#save-status').textContent='文字已保存在当前浏览器';return true}catch(e){storageOK=false;$('#save-status').textContent=recordWarning();return false}}"
    new_save = """const recordConcurrency=window.IELTSRecordConcurrency.create({initial:state,read:()=>localStorage.getItem(key),write:raw=>localStorage.setItem(key,raw),validate:validateRecord});
function concurrencyWarning(reason){return reason==='conflict'?'另一页面修改了同一项，本页新输入未能保存。请先导出文字或备份本页草稿，再刷新核对；其他页面的记录未被覆盖。':reason==='changed-again'?'另一页面刚更新了记录，本次未能保存且没有覆盖它。请先导出本页草稿，再重试或刷新核对。':reason==='external-invalid'?'其他页面的记录已变更且无法读取，本页没有覆盖它。请先导出本页草稿，再检查学习记录备份。':'当前未能保存，请导出文字或备份学习记录后再刷新。';}
function save(changes,retainOnFailure=true){
 if(loadBlocked){$('#save-status').textContent=recordWarning();return false}
 const result=recordConcurrency.save(state,changes,retainOnFailure);
 if(!result.ok){storageOK=false;recordSaveIssue=concurrencyWarning(result.reason);$('#save-status').textContent=recordWarning();return false}
 state=result.state;storageOK=true;recordSaveIssue='';$('#save-status').textContent=result.remoteUpdates?'本次文字已保存；另一页面的更新已保留，刷新可载入。':'文字已保存在当前浏览器';return true;
}"""
    core = replace_once(core, old_save, new_save)
    core = replace_once(core, "if(!save()){state=previous;return false}", "if(!save({fields:Object.keys(values)},false)){state=previous;return false}")
    core = replace_once(core, "el.type==='checkbox'?el.checked:el.value;save();wordCounts();scores()", "el.type==='checkbox'?el.checked:el.value;save({fields:[el.dataset.save]});wordCounts();scores()")
    core = replace_once(core, "const id=freeze.dataset.freeze;const fields={};", "const id=freeze.dataset.freeze;if(state.snapshots[id]&&!freeze.disabled){recordSaveIssue='另一页面已保留这组首答，本页未能重新提交。请先导出本页草稿，再刷新核对原稿。';$('#save-status').textContent=recordSaveIssue;notice(recordSaveIssue);return}const fields={};")
    core = replace_once(core, "if(!save()){delete state.snapshots[id];notice(recordWarning());return}", "if(!save({snapshots:[id],expectedFields:fields},false)){delete state.snapshots[id];notice(recordWarning());return}")
    old_import = """  if((Object.keys(state.fields).length||Object.keys(state.snapshots).length||loadBlocked)&&!confirm('恢复备份会替换当前文字记录。请先导出当前文字及原始记录，确定继续？'))return;
  try{localStorage.setItem(key,JSON.stringify(candidate))}catch(err){notice('备份有效，但浏览器未能写入。当前记录未替换，请先保留导出文件。');return}
  state=candidate;storageOK=true;loadBlocked=false;recoveryRaw=null;location.reload();"""
    new_import = """  let observed;try{observed=localStorage.getItem(key)}catch(err){notice('当前无法读取浏览器记录，未恢复备份。请先保留本页草稿和备份文件。');return}
  if((Object.keys(state.fields).length||Object.keys(state.snapshots).length||loadBlocked||observed!==null)&&!confirm('恢复备份会替换此浏览器的当前文字记录，包括其他页面刚保存的内容。请先导出本页草稿及当前记录，确定继续？'))return;
  const restored=recordConcurrency.restore(candidate,observed);
  if(!restored.ok){recordSaveIssue=concurrencyWarning(restored.reason);$('#save-status').textContent=recordWarning();notice(recordSaveIssue);return}
  state=candidate;storageOK=true;loadBlocked=false;recoveryRaw=null;recordSaveIssue='';location.reload();"""
    core = replace_once(core, old_import, new_import)
    opening = match.group(0)[:match.group(0).index('>')+1]
    core = core.replace('\n', newline)
    model = ('<script id="record-concurrency-model-script">\n' + MODEL.read_text(encoding='utf-8').rstrip() + '\n</script>\n').replace('\n', newline)
    return html[:match.start()] + model + opening + core + '</script>' + html[match.end():]

if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--source',type=Path,default=FORMAL);ap.add_argument('--output',type=Path,required=True);args=ap.parse_args()
    if args.output.resolve() in (FORMAL.resolve(),args.source.resolve()): raise SystemExit('Write a separate candidate; formal/source overwrite prohibited')
    result=patch_html(args.source.read_text(encoding='utf-8'))
    args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(result,encoding='utf-8');print(args.output)
