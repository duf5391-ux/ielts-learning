// Device appearance is separate from account learning records.
const KEY='word-context:appearance:v1';
export const themes=['blue','coral','mint','amber','berry','lavender'];
const names={blue:'晴空蓝',coral:'珊瑚橙',mint:'薄荷青',amber:'暖琥珀',berry:'莓果红',lavender:'鸢尾紫'};
const periods=[
 {id:'morning',label:'早晨',range:'07–12 点',theme:'blue'},
 {id:'noon',label:'午后',range:'12–15 点',theme:'coral'},
 {id:'afternoon',label:'下午',range:'15–19 点',theme:'mint'},
 {id:'evening',label:'夜间',range:'19–07 点',theme:'amber'}
];
let preference={theme:'blue',automatic:true,style:'clear'},appliedTheme=null,appliedPeriod=null,appearanceDocument=null;
export function appearanceForTime(date=new Date()){
 const hour=date.getHours();
 return {...periods[hour>=7&&hour<12?0:hour>=12&&hour<15?1:hour>=15&&hour<19?2:3]};
}
const status=()=>preference.automatic?`自动 · ${(appliedPeriod||appearanceForTime()).label}`:`已固定 · ${names[appliedTheme||preference.theme]}`;
function apply(){
 const doc=appearanceDocument;if(!doc)return;
 doc.documentElement.dataset.theme=appliedTheme;
 doc.documentElement.dataset.style=preference.style;
 doc.querySelectorAll('[data-style-choice]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.styleChoice===preference.style)));
 doc.querySelectorAll('[data-theme-choice]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.themeChoice===appliedTheme)));
 doc.querySelectorAll('[data-theme-auto]').forEach(input=>input.checked=preference.automatic);
 doc.querySelectorAll('[data-theme-status]').forEach(el=>el.textContent=status());
 doc.querySelectorAll('[data-theme-period]').forEach(el=>el.classList.toggle('active',preference.automatic&&el.dataset.themePeriod===appliedPeriod?.id));
}
// No timer changes the surface while someone is spelling. Pause also holds the color.
export function refreshAppearance(hold=false,date=new Date()){
 if(!appearanceDocument||hold||!preference.automatic)return;
 appliedPeriod=appearanceForTime(date);appliedTheme=appliedPeriod.theme;apply();
}
export function appearanceControl(){
 const active=appliedTheme||(preference.automatic?appearanceForTime().theme:preference.theme);
 return `<details class="appearance"><summary aria-label="配色设置"><span class="appearance-dot" aria-hidden="true"></span><span>外观</span><svg viewBox="0 0 16 16" aria-hidden="true"><path d="m4 6 4 4 4-4"/></svg></summary><div class="appearance-panel"><div class="style-picker"><strong>界面风格</strong><div role="group" aria-label="选择界面风格"><button type="button" data-style-choice="clear" aria-pressed="${preference.style!=="claude"}"><b>清爽</b><small>简洁 · 明快</small></button><button type="button" data-style-choice="claude" aria-pressed="${preference.style==="claude"}"><b>Claude 风格</b><small>暖纸 · 衬线</small></button></div></div><div class="appearance-title"><strong>选一种喜欢的颜色</strong><span data-theme-status role="status">${status()}</span></div><p>浅底色，清楚的文字，一点鲜活的颜色。</p><div class="theme-options" role="group" aria-label="选择配色">${themes.map(theme=>`<button type="button" class="theme-choice" data-theme-choice="${theme}" aria-pressed="${theme===active}"><span class="theme-swatch swatch-${theme}" aria-hidden="true"></span>${names[theme]}<span class="theme-check" aria-hidden="true">✓</span></button>`).join('')}</div><label class="theme-auto"><input type="checkbox" data-theme-auto ${preference.automatic?'checked':''}><span>跟随时段自动换色<small>打开页面或一轮结束后切换，作答中不变。<br>手选颜色会固定为你选的这一套。</small></span></label><div class="theme-schedule" aria-label="自动配色时段">${periods.map(p=>`<div data-theme-period="${p.id}" class="${preference.automatic&&p.id===(appliedPeriod||appearanceForTime()).id?'active':''}"><span class="theme-swatch swatch-${p.theme}" aria-hidden="true"></span><span>${p.label}<small>${p.range}</small></span></div>`).join('')}</div></div></details>`;
}
export function initializeAppearance(doc=document,storage=globalThis.localStorage){
 appearanceDocument=doc;
 try{const saved=JSON.parse(storage.getItem(KEY));if(saved&&themes.includes(saved.theme))preference={theme:saved.theme,automatic:saved.automatic!==false,style:saved.style==='claude'?'claude':'clear'};}catch{}
 appliedPeriod=appearanceForTime();appliedTheme=preference.automatic?appliedPeriod.theme:preference.theme;apply();
 const save=()=>{try{storage.setItem(KEY,JSON.stringify(preference));}catch{}apply();};
 const positionPanel=menu=>{
  if(!menu.open)return;
  const panel=menu.querySelector('.appearance-panel'),anchor=menu.querySelector('summary').getBoundingClientRect(),view=doc.defaultView;
  if(!panel||!view)return;
  const width=Math.min(320,view.innerWidth-32);
  panel.style.width=width+'px';panel.style.right='auto';
  panel.style.left=Math.max(16,Math.min(anchor.right-width,view.innerWidth-width-16))+'px';
  // Keep the trigger accessible; a long menu scrolls within the available side.
  const below=Math.max(0,view.innerHeight-anchor.bottom-26),above=Math.max(0,anchor.top-26);
  const openBelow=below>=Math.min(panel.scrollHeight,240)||below>=above;
  const available=openBelow?below:above;
  panel.style.maxHeight=available+'px';
  panel.style.top=(openBelow?anchor.bottom+10:Math.max(16,anchor.top-10-Math.min(panel.scrollHeight,available)))+'px';
 };
 doc.addEventListener('toggle',event=>{if(event.target.matches?.('.appearance'))positionPanel(event.target);},true);
 doc.defaultView?.addEventListener('resize',()=>doc.querySelectorAll('.appearance[open]').forEach(positionPanel));

 doc.addEventListener('click',event=>{
  const button=event.target.closest('[data-theme-choice]');
  if(button){preference={...preference,theme:button.dataset.themeChoice,automatic:false};appliedTheme=preference.theme;save();}
  const styleButton=event.target.closest('[data-style-choice]');
  if(styleButton){preference.style=styleButton.dataset.styleChoice==='claude'?'claude':'clear';save();positionPanel(styleButton.closest('.appearance'));}
  if(!event.target.closest('.appearance'))doc.querySelectorAll('.appearance[open]').forEach(menu=>menu.open=false);
 });
 doc.addEventListener('change',event=>{if(event.target.matches('[data-theme-auto]')){
  preference.automatic=event.target.checked;preference.theme=appliedTheme;
  if(preference.automatic){appliedPeriod=appearanceForTime();appliedTheme=appliedPeriod.theme;}save();
 }});
 doc.addEventListener('keydown',event=>{if(event.key==='Escape')doc.querySelectorAll('.appearance[open]').forEach(menu=>{menu.open=false;menu.querySelector('summary').focus();});});
}
