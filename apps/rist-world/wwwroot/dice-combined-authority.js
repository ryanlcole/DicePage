(()=>{
 'use strict';
 const LABELS=['d4','Bonus','Penalty','d6','d8','d10','xd10','d20'];
 let queued=false;
 const q=(s,r=document)=>r?.querySelector(s);
 const qa=(s,r=document)=>[...(r?.querySelectorAll(s)||[])];
 function rolledValue(el){
  const title=(el.getAttribute('title')||'').trim();
  if(/\brolling$/i.test(title))return el.classList.contains('die-d10-inverse')?10:0;
  const match=title.match(/(-?\d+)\s*$/);return match?Number(match[1]):0;
 }
 function correctedTotal(){
  const rolls=qa('.world-stage .rolled-die');
  let base=0;const multipliers=[];
  rolls.forEach(el=>{const value=rolledValue(el);if(el.classList.contains('die-d10-inverse'))multipliers.push(value===0?10:value);else base+=value});
  return multipliers.reduce((total,m)=>total*m,base);
 }
 function paintTotal(root){
  const actions=q('.rist-deck-row.row3 .rist-deck-actions',root);if(!actions)return;
  const sum=qa('button',actions).find(b=>/^SUM\b/i.test((b.textContent||'').trim()));if(!sum)return;
  sum.textContent=`SUM ${correctedTotal()}`;
  sum.title='xd10 multiplies the sum of all other dice; 0 = ×10';
 }
 function patch(){
  const root=q('.rist.release-world');if(!root?.classList.contains('deck-dice'))return;
  const shell=q(':scope>.release-world-shell',root),row1=q(':scope>.rist-deck-row.row1',shell),row2=q(':scope>.rist-deck-row.row2',shell),art=q('.rist-dice-image-loop',row2);
  if(!row1||!row2||!art)return;
  row1.classList.add('rist-dice-header-merged');row2.classList.add('rist-dice-combined-row');
  qa(':scope>.rist-dice-proxy',art).forEach((proxy,index)=>{
   const logical=index%LABELS.length;proxy.dataset.loopIndex=String(logical);
   let label=q(':scope>.rist-dice-combined-label',proxy);if(!label){label=document.createElement('div');label.className='rist-dice-combined-label';proxy.prepend(label)}
   label.textContent=LABELS[logical];
  });
  paintTotal(root);
 }
 function queue(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;patch()})}
 function start(){patch();new MutationObserver(queue).observe(document.body,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['title','class']});}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();