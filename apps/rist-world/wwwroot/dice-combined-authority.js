(()=>{
 'use strict';
 const LABELS=['d4','Bonus','Penalty','d6','d8','d10','xd10','d20'];
 let queued=false;
 const q=(s,r=document)=>r?.querySelector(s);
 const qa=(s,r=document)=>[...(r?.querySelectorAll(s)||[])];
 function patch(){
  const root=q('.rist.release-world');
  if(!root?.classList.contains('deck-dice'))return;
  const shell=q(':scope>.release-world-shell',root);
  const row1=q(':scope>.rist-deck-row.row1',shell);
  const row2=q(':scope>.rist-deck-row.row2',shell);
  const art=q('.rist-dice-image-loop',row2);
  if(!row1||!row2||!art)return;
  row1.classList.add('rist-dice-header-merged');
  row2.classList.add('rist-dice-combined-row');
  qa(':scope>.rist-dice-proxy',art).forEach((proxy,index)=>{
   const logical=index%LABELS.length;
   proxy.dataset.loopIndex=String(logical);
   let label=q(':scope>.rist-dice-combined-label',proxy);
   if(!label){
    label=document.createElement('div');
    label.className='rist-dice-combined-label';
    proxy.prepend(label);
   }
   label.textContent=LABELS[logical];
  });
 }
 function queue(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;patch()})}
 function start(){patch();new MutationObserver(queue).observe(document.body,{childList:true,subtree:true});}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
