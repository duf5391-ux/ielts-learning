(() => {
  'use strict';
  document.addEventListener('click',event=>{
    const link=event.target.closest('[data-prereq-word]');if(!link)return;
    const field=document.querySelector('[data-save="prereq-vocab-terms"]');if(!field)return;
    const entry=link.dataset.prereqWord+' — '+link.dataset.prereqMeaning;
    if(!field.value.split('\n').includes(entry)){
      field.value+=(field.value.trim()?'\n':'')+entry;
      field.dispatchEvent(new Event('input',{bubbles:true}));
    }
    const status=document.getElementById('prereq-vocab-status');
    if(status)status.textContent='已加入 '+link.dataset.prereqWord+'；已有词条、句子和修订记录保留。';
  });
})();
