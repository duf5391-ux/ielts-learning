// Animate meaningful state changes only; audio callbacks and text input stay still.
export function initializeMotion(doc=document){
 const root=doc.querySelector('#app');if(!root)return;
 const reduce=matchMedia('(prefers-reduced-motion: reduce)');
 let previousScene='',previousChoices=new Set();
 const respond=()=>{
  const card=root.querySelector('[data-listen-scene]');
  const scene=card?.dataset.listenScene||'';
  if(card&&scene!==previousScene&&!reduce.matches){
   const feedback=card.querySelector('.listen-answer');
   const target=feedback||card;
   target.animate(feedback?[{opacity:.35,transform:'scale(.98)'},{opacity:1,transform:'scale(1)'}]:[{opacity:.35,transform:'translateX(14px)'},{opacity:1,transform:'translateX(0)'}],{duration:feedback?180:230,easing:'cubic-bezier(.16,1,.3,1)'});
  }
  previousScene=scene;
  const checked=new Set();
  root.querySelectorAll('[data-listen-choice]:checked').forEach(input=>{
   checked.add(input.dataset.listenChoice);
   if(!previousChoices.has(input.dataset.listenChoice)&&!reduce.matches)input.animate([{transform:'scale(.8)'},{transform:'scale(1.1)',offset:.65},{transform:'scale(1)'}],{duration:180});
  });
  previousChoices=checked;
 };
 new MutationObserver(respond).observe(root,{childList:true,subtree:true});
}
