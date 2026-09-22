(()=>{
const input=document.getElementById('qt-search');
const norm=t=>t.toLowerCase().normalize('NFKC').replace(/[’‘]/g,"'").replace(/\s+/g,' ').trim();
const rows=[...document.querySelectorAll('[data-text-target]')].map(row=>({row,text:norm(document.getElementById(row.dataset.textTarget).querySelector('.qt-body').textContent+' '+row.textContent)}));
input.addEventListener('input',()=>{const words=norm(input.value).split(' ').filter(Boolean);let n=0;for(const item of rows){const match=words.every(w=>item.text.includes(w));item.row.hidden=!match;if(match)n++;}document.getElementById('qt-count').textContent=n+' / '+rows.length+' 组题目';document.getElementById('qt-empty').hidden=n>0;});
})();