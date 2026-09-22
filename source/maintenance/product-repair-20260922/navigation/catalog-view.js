  // Every content row opens the material itself. The index never opens another index card.
  const browseState = {study:new Map(),practice:new Map()};
  const filterNames = ['skill','topic','type','part','search','difficulty','confidence','status'];
  const listPositions = new Map();
  const entryOrigins = new Map();
  const folded = text => String(text||'').normalize('NFKC').toLowerCase().replace(/\s+/g,' ').trim();
  const corpus = new Map(data.units.map(u=>[u.id,folded([u.title,u.topic,u.type,u.description,u.source,document.getElementById(u.id)?.textContent].join(' '))]));
  const sections = [['listening','听力'],['reading','阅读'],['writing1','写作 · Task 1'],['writing2','写作 · Task 2'],['speaking','口语'],['vocabulary','词汇'],['phrases','短语'],['shared','背景与话题']];
  function rememberFilters(mode){browseState[mode].set(scope[mode]||'',Object.fromEntries(filterNames.map(k=>[k,$('#la-'+mode+'-'+k)?.value||''])));}
  function restoreFilters(mode,group){
    scope[mode]=group;const prior=browseState[mode].get(group)||{};
    for(const [suffix,key] of [['topic','topic'],['type','category'],['part','part']]){
      const picker=$('#la-'+mode+'-'+suffix);if(!picker)continue;picker.replaceChildren();const any=el('option','全部');any.value='';picker.append(any);
      for(const choice of [...new Set(data.units.filter(u=>(!group||scopeMatches(u,group))&&(mode==='study'||u.mode==='practice')).map(u=>u[key]).filter(Boolean))].sort()){
        const opt=el('option',choice);opt.value=choice;picker.append(opt);
      }
    }
    for(const key of filterNames){const node=$('#la-'+mode+'-'+key);if(node)node.value=prior[key]||'';}
  }
  document.addEventListener('click',event=>{
    const a=event.target.closest('a[href^="#"]');if(!a)return;
    for(const mode of ['study','practice'])if(!$('#'+mode).hidden){
      rememberFilters(mode);listPositions.set(mode+':'+scope[mode],window.scrollY);
      const target=a.getAttribute('href').slice(1);
      if(units.has(target))entryOrigins.set(target,{hash:location.hash.slice(1)||mode,mode,search:$('#la-'+mode+'-search').value});
    }
  },true);
  function unitCard(u) {
    const n=el('article','','product-content-row');n.dataset.catalogUnit=u.id;
    const content=el('div','','product-row-content'),title=link(u.id,u.title);title.className='product-content-title';content.append(title);
    if(u.id==='topical-vocabulary'&&!$('#study').hidden&&$('#la-study-search').value.trim())title.textContent='在话题词卡中查找：'+$('#la-study-search').value.trim();
    const p=unitProgress(u),meta=[u.mode==='practice'?'练习':'学习',u.skillLabel,u.topic];
    if(u.difficulty?.level)meta.push('难度 '+u.difficulty.level+'/5');
    if(u.referenceConfidence)meta.push('参考置信度'+u.referenceConfidence);
    if(u.source)meta.push(u.source);
    const info=el('p',[...new Set(meta.filter(Boolean))].join(' · '),'product-row-meta');
    if(u.referenceConfidence)info.classList.add('content-entry-metadata');
    info.title=u.difficulty?.reason||u.difficulty?.rationale||'';content.append(info);
    const actions=el('div','','product-row-actions');
    if(p.total)actions.append(el('span',p.done===p.total?'本项已完成':p.done?'已完成 '+p.done+'/'+p.total:'未开始','product-row-state'));
    const add=button(state.today.includes(u.id)?'已选':'＋ 自选',()=>toggleToday(u.id));
    add.setAttribute('aria-label',(state.today.includes(u.id)?'移出自选：':'加入自选：')+u.title);add.setAttribute('aria-pressed',String(state.today.includes(u.id)));actions.append(add);
    n.append(content,actions);return n;
  }
  function renderCards() {
    for(const mode of ['study','practice']) {
      const root=$('#'+mode);if(root.hidden)continue;
      const group=scope[mode],pick=k=>$('#la-'+mode+'-'+k)?.value||'';
      const q=folded(pick('search')),topic=pick('topic'),type=pick('type'),part=pick('part'),difficulty=pick('difficulty'),confidence=pick('confidence'),status=pick('status');
      const filtering=!!(q||topic||type||part||difficulty||confidence||status);
      rememberFilters(mode);
      const all=data.units.filter(u=>(mode==='study'&&q?true:u.mode===mode)&&scopeMatches(u,group));
      const found=all.filter(u=>{
        const p=unitProgress(u),activity=p.done===p.total&&p.total?'done':p.done?'started':'new';
        return(!topic||u.topic===topic)&&(!type||u.category===type)&&(!part||u.part===part)&&(!difficulty||String(u.difficulty?.level||'')===difficulty)&&(!confidence||u.referenceConfidence===confidence)&&(!status||status===activity)&&(!q||q.split(' ').every(term=>(corpus.get(u.id)||'').includes(term)));
      });
      root.querySelector('.la-heading h1').textContent=mode==='study'?'学习':'练习';
      root.querySelector('.la-heading > p:last-child').textContent='';
      $('#la-'+mode+'-progress').hidden=true;
      const search=$('#la-'+mode+'-search');search.placeholder=mode==='study'?'搜索全部内容、题型或话题':'搜索练习题目、题型或话题';
      const crumb=$('#la-'+mode+'-location');crumb.replaceChildren();
      for(const [code,label] of [['','全部'],...sections]){
        if(code&&!data.units.some(u=>u.mode===mode&&scopeMatches(u,code)))continue;
        const a=link(code?mode+'-'+code+'-list':mode,label);a.className='product-scope';if(group===code)a.setAttribute('aria-current','page');crumb.append(a);
      }
      const toolbar=root.querySelector('.la-toolbar');toolbar.hidden=false;
      $('#la-'+mode+'-skill').closest('label').hidden=true;
      const partNode=$('#la-'+mode+'-part');partNode.closest('label').hidden=!!group&&!['listening','speaking'].includes(group);
      const count=$('#la-'+mode+'-count');count.hidden=false;count.textContent=found.length+' 项'+(group?' · '+labelOf(group):'');
      const summary=root.querySelector('.product-filters > summary');summary.textContent='筛选'+([topic,type,part,difficulty,confidence,status].filter(Boolean).length?' · 已选 '+[topic,type,part,difficulty,confidence,status].filter(Boolean).length+' 项':'');
      const cards=$('#la-'+mode+'-cards');cards.replaceChildren();
      function groupRows(label,items,key){if(!items.length)return;const block=el('section','','product-content-group'),h=el('h2',label+' · '+items.length);block.dataset.productGroup=key;block.append(h,...items.map(unitCard));cards.append(block);}
      if(filtering||group)groupRows(q?'搜索结果':group?labelOf(group):'筛选结果',found,'results');
      else {
        const recent=found.filter(u=>/^(jiufen-close-|pr-jiufen-|pr-jijing-)/.test(u.id)).reverse();
        groupRows('新到内容',recent,'recent');
        for(const [code,label] of sections)groupRows(label,found.filter(u=>u.skill===code&&!recent.includes(u)),code);
      }
      if(!found.length){const empty=el('div','','product-empty');empty.append(el('p','没有找到匹配内容。'));empty.append(button('清除筛选与搜索',()=>{for(const k of filterNames){const n=$('#la-'+mode+'-'+k);if(n)n.value='';}renderCards();}));cards.append(empty);}
      for(const id of ['la-'+mode+'-extras','architecture-practice-extras']){const n=$('#'+id);if(n)n.hidden=true;}
      const quick=$('#la-'+mode+'-quick');if(quick)quick.hidden=!!group;
    }
  }
