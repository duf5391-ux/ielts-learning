"""Patch the local demo's record validation/recovery without rebuilding teaching."""
from pathlib import Path
import re, hashlib, json, sys
sys.stdout.reconfigure(encoding='utf-8')
HERE=Path(__file__).resolve().parent
MAIN=Path('C:/Users/Admin1/Documents/Codex/2026-09-12/referenced-chatgpt-conversation-this-is-an/outputs/IELTS-四科学习册/开始学习.html')
MARK='/* RECORD-SAFETY-20260919 */'

def patch_script(js):
    if MARK in js:return js
    def swap(old,new):
        nonlocal js
        assert js.count(old)==1,old[:100]
        js=js.replace(old,new,1)
    swap("const key='ielts-finished-book-v1';let state={version:1,fields:{},snapshots:{}},storageOK=true;", """/* RECORD-SAFETY-20260919 */
const key='ielts-finished-book-v1';let state={version:1,fields:{},snapshots:{}},storageOK=true,recoveryRaw=null,loadBlocked=false;
const recordObject=x=>x!==null&&typeof x==='object'&&!Array.isArray(x);
const recordFields=x=>recordObject(x)&&Object.values(x).every(v=>typeof v==='string'||typeof v==='boolean'||(typeof v==='number'&&Number.isFinite(v)));
function validateRecord(x){
 if(!recordObject(x)||x.version!==1||!recordFields(x.fields)||!recordObject(x.snapshots))throw Error('学习记录结构不完整');
 const chapters=['reading','writing1','writing2','listening','speaking'];
 for(const [id,snapshot] of Object.entries(x.snapshots))if(!chapters.includes(id)||!recordObject(snapshot)||typeof snapshot.at!=='string'||!recordFields(snapshot.fields))throw Error('首次作答记录格式不符');
 return x;
}
function recordWarning(){return loadBlocked?'已有记录无法读取，已暂停自动保存。请导出文字保留本次输入，并备份原始记录后恢复有效备份。':'当前未能保存，请导出文字或备份学习记录后再刷新。';}""")
    swap("try{const raw=localStorage.getItem(key);if(raw){const x=JSON.parse(raw);if(x.version===1&&x.fields&&x.snapshots)state=x}}catch(e){storageOK=false}", "try{const raw=localStorage.getItem(key);if(raw!==null){recoveryRaw=raw;state=validateRecord(JSON.parse(raw));recoveryRaw=null}}catch(e){storageOK=false;loadBlocked=true}")
    swap("function save(){try{localStorage.setItem(key,JSON.stringify(state));$('#save-status').textContent='文字已保存在当前浏览器'}catch(e){storageOK=false;$('#save-status').textContent='浏览器未允许保存，请导出作答';} }", "function save(){if(loadBlocked){$('#save-status').textContent=recordWarning();return false}try{localStorage.setItem(key,JSON.stringify(state));storageOK=true;$('#save-status').textContent='文字已保存在当前浏览器';return true}catch(e){storageOK=false;$('#save-status').textContent=recordWarning();return false}}")
    swap("restore();if(!storageOK)$('#save-status').textContent='浏览器未允许保存，请及时导出作答';", "restore();if(!storageOK)$('#save-status').textContent=recordWarning();")
    swap("if(!state.snapshots[id])state.snapshots[id]={at:new Date().toISOString(),fields};save();unlock(id);", "if(!state.snapshots[id]){state.snapshots[id]={at:new Date().toISOString(),fields};if(!save()){delete state.snapshots[id];notice(recordWarning());return}}unlock(id);")
    swap("const kind=btn.dataset.export;let content;if(kind==='json')content=JSON.stringify(state,null,2);", "const kind=btn.dataset.export;let content;if(kind==='json'&&recoveryRaw!==null){download(new Blob([recoveryRaw],{type:'application/json'}),'IELTS-异常原始学习记录.json');notice('已导出异常原始记录；本次新输入请另用“导出文字作答”保留。');return}if(kind==='json')content=JSON.stringify(state,null,2);")
    start=js.index("$('#import-state').addEventListener('change'")
    end=js.index('\nconst timers=',start)
    js=js[:start]+"""$('#import-state').addEventListener('change',async e=>{
 const file=e.target.files[0];if(!file)return;
 try{
  const candidate=validateRecord(JSON.parse(await file.text()));
  if((Object.keys(state.fields).length||Object.keys(state.snapshots).length||loadBlocked)&&!confirm('恢复备份会替换当前文字记录。请先导出当前文字及原始记录，确定继续？'))return;
  try{localStorage.setItem(key,JSON.stringify(candidate))}catch(err){notice('备份有效，但浏览器未能写入。当前记录未替换，请先保留导出文件。');return}
  state=candidate;storageOK=true;loadBlocked=false;recoveryRaw=null;location.reload();
 }catch(err){notice('未能恢复：备份格式不完整或含无效字段，当前记录未替换。')}
 finally{e.target.value=''}
});"""+js[end:]
    return js

def apply(page):
    matches=[m for m in re.finditer(r'<script\b[^>]*>(.*?)</script>',page,re.S) if "const key='ielts-finished-book-v1'" in m[1]]
    assert len(matches)==1
    m=matches[0];js=patch_script(m[1]);return page[:m.start(1)]+js+page[m.end(1):]

if __name__=='__main__':
    raw=MAIN.read_bytes();page=raw.decode('utf8');updated=apply(page)
    if updated!=page:
        backup=HERE/'backups'/'开始学习-before-record-safety-20260919.html'
        if not backup.exists():backup.write_bytes(raw)
        tmp=MAIN.with_suffix('.record-safety.tmp');tmp.write_text(updated,encoding='utf8',newline='');tmp.replace(MAIN)
    assert apply(updated)==updated
    out={'changed':updated!=page,'idempotent':True,'before_sha256':hashlib.sha256(raw).hexdigest(),'after_sha256':hashlib.sha256(MAIN.read_bytes()).hexdigest()}
    (HERE/'architecture-audit-qa'/'reliability-patch.json').write_text(json.dumps(out,indent=2),encoding='utf8')
    print(json.dumps(out))
