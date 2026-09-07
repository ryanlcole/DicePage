(()=>{
 'use strict';
 const LABELS={d4:'d4','d5-bonus':'d5','d5-penalty':'-d5',d6:'d6',d8:'d8',d10:'d10','d10-inverse':'xd10',d12:'d12',d20:'d20'};
 let queued=false;
 const q=(s,r=document)=>r?.querySelector(s);
 const qa=(s,r=document)=>[...(r?.querySelectorAll(s)||[])];
 function dieKey(el){const sprite=el?.matches?.('.die-sprite')?el:el?.querySelector?.('.die-sprite');if(!sprite)return '';const cls=[...sprite.classList].find(c=>/^die-d/.test(c)&&c!=='die-sprite');return cls?cls.replace(/^die-/,''):''}
 function ensureClear(root){
  const actions=q('.rist-deck-row.row3 .rist-deck-actions',root);if(!actions)return null;
  qa('.rist-dice-sum-result',actions).forEach(el=>el.remove());
  qa('button,output,.sum',actions).forEach(el=>{if(/^SUM\b/i.test((el.textContent||'').trim()))el.remove()});
  let clear=q('.rist-dice-clear-action',actions);
  if(clear)return clear;
  clear=document.createElement('button');
  clear.type='button';
  clear.className='rist-dice-clear-action';
  clear.textContent='Clear Dice';
  clear.setAttribute('aria-label','Clear dice from the map');
  clear.addEventListener('click',event=>{
   event.preventDefault();event.stopPropagation();
   q('#footer-slider .clear-dice')?.click();
  });
  actions.prepend(clear);
  return clear;
 }
 function patch(){const root=q('.rist.release-world');if(!root?.classList.contains('deck-dice'))return;const shell=q(':scope>.release-world-shell',root),row1=q(':scope>.rist-deck-row.row1',shell),row2=q(':scope>.rist-deck-row.row2',shell),art=q('.rist-dice-image-loop',row2);if(!row1||!row2||!art)return;row1.classList.add('rist-dice-header-merged');row2.classList.add('rist-dice-combined-row');qa(':scope>.rist-dice-proxy',art).forEach(proxy=>{const key=dieKey(proxy);if(!key)return;proxy.dataset.dieKey=key;let label=q(':scope>.rist-dice-combined-label',proxy);if(!label){label=document.createElement('div');label.className='rist-dice-combined-label';proxy.prepend(label)}label.textContent=LABELS[key]||key});ensureClear(root)}
 function queue(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;patch()})}
 function start(){patch();new MutationObserver(queue).observe(document.body,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['title','class','data-value','data-roll-value','data-die-result','aria-valuenow','aria-label']});document.addEventListener('rist:dice-roll-result',queue);document.addEventListener('rist:dice-roll-intent',()=>setTimeout(queue,0))}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
