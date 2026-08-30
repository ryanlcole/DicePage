(()=>{
 'use strict';
 const MODES=[
  {key:'test',label:'Test Roll',color:'#c6a400',audience:'self'},
  {key:'public',label:'Public Roll',color:'#0b0f13',audience:'all'},
  {key:'group',label:'Group Roll',color:'#0c4c86',audience:'group+gm'},
  {key:'gm',label:'GM Roll',color:'#b85b12',audience:'self+gm'},
  {key:'gm-discrete',label:'GM Discrete',color:'#8d1818',audience:'self-masked+gm-full'}
 ];
 const MODE_KEY='rist.dice.visibility';
 const SUM_KEY='rist.dice.sum-enabled';
 let mode=localStorage.getItem(MODE_KEY)||'public';
 let sumEnabled=localStorage.getItem(SUM_KEY)!=='false';
 let lastTotal='0';
 function spec(){return MODES.find(x=>x.key===mode)||MODES[1]}
 function isGm(){const role=document.querySelector('#header-slider [aria-label="Role"] small')?.textContent?.trim();return role==='GM'}
 function setMode(next){if(!MODES.some(x=>x.key===next))next='public';mode=next;localStorage.setItem(MODE_KEY,mode);apply();document.dispatchEvent(new CustomEvent('rist:dice-visibility-changed',{detail:state()}))}
 function cycle(){const i=MODES.findIndex(x=>x.key===mode);setMode(MODES[(i+1+MODES.length)%MODES.length].key)}
 function setSumEnabled(enabled){if(!isGm())return false;sumEnabled=!!enabled;localStorage.setItem(SUM_KEY,String(sumEnabled));apply();document.dispatchEvent(new CustomEvent('rist:dice-sum-setting-changed',{detail:{enabled:sumEnabled}}));return true}
 function state(){const s=spec();return{mode:s.key,label:s.label,audience:s.audience,sumEnabled,gm:isGm(),discrete:s.key==='gm-discrete'}}
 function ensureToggle(rail){let btn=rail.querySelector(':scope > .roll-visibility-toggle');if(btn)return btn;btn=document.createElement('button');btn.type='button';btn.className='roll-visibility-toggle';btn.addEventListener('click',cycle);rail.prepend(btn);return btn}
 function publishRollIntent(target){const s=state();document.dispatchEvent(new CustomEvent('rist:dice-roll-intent',{detail:{...s,die:target.getAttribute('aria-label')||'die'}}))}
 function apply(){
  const footer=document.getElementById('footer-slider');const rail=footer?.querySelector('.release-footer-track,.dice-circular-set');if(!footer||!rail)return;
  const s=spec();footer.dataset.rollVisibility=s.key;footer.style.setProperty('--roll-mode-bg',s.color);footer.style.background=s.color;rail.style.background=s.color;
  const btn=ensureToggle(rail);btn.textContent=s.label;btn.title=`${s.label} — tap to change`;btn.setAttribute('aria-label',`${s.label}. Tap to change dice roll visibility.`);btn.dataset.mode=s.key;
  let style=document.getElementById('rist-dice-privacy-style');if(!style){style=document.createElement('style');style.id='rist-dice-privacy-style';style.textContent=`
#footer-slider .roll-visibility-toggle{box-sizing:border-box;flex:0 0 auto;height:74px;min-width:82px;padding:0 9px;border:1px solid #d2b873;border-radius:9px;background:#111920;color:#f4e2ad;font:800 10px/1.15 system-ui;text-align:center;white-space:normal;touch-action:manipulation}
#footer-slider[data-roll-visibility="test"],#footer-slider[data-roll-visibility="test"] .release-footer-track{background:#c6a400!important}
#footer-slider[data-roll-visibility="public"],#footer-slider[data-roll-visibility="public"] .release-footer-track{background:#0b0f13!important}
#footer-slider[data-roll-visibility="group"],#footer-slider[data-roll-visibility="group"] .release-footer-track{background:#0c4c86!important}
#footer-slider[data-roll-visibility="gm"],#footer-slider[data-roll-visibility="gm"] .release-footer-track{background:#b85b12!important}
#footer-slider[data-roll-visibility="gm-discrete"],#footer-slider[data-roll-visibility="gm-discrete"] .release-footer-track{background:#8d1818!important}
#footer-slider[data-roll-visibility="gm-discrete"] .sum{visibility:hidden!important}
#footer-slider[data-roll-visibility="gm-discrete"] .rolled-die-value,#footer-slider[data-roll-visibility="gm-discrete"] [data-roll-value]{visibility:hidden!important}
`;document.head.appendChild(style)}
  const sum=footer.querySelector('.sum');if(sum)sum.hidden=!sumEnabled||s.key==='gm-discrete';
 }
 function bindRollClicks(){const footer=document.getElementById('footer-slider');if(!footer||footer.dataset.privacyRollBound==='1')return;footer.dataset.privacyRollBound='1';footer.addEventListener('click',e=>{const t=e.target instanceof Element?e.target.closest('.die-button'):null;if(t)publishRollIntent(t)},true)}
 function watchTotal(){const footer=document.getElementById('footer-slider');const total=footer?.querySelector('.sum span:last-child');if(!total)return;const next=total.textContent?.trim()||'0';if(next===lastTotal)return;lastTotal=next;const s=state();document.dispatchEvent(new CustomEvent('rist:dice-roll-result',{detail:{...s,total:s.discrete?null:Number(next),maskedForUser:s.discrete}}))}
 function refresh(){apply();bindRollClicks();watchTotal()}
 let queued=false;function queue(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;refresh()})}
 const observer=new MutationObserver(queue);
 function start(){refresh();observer.observe(document.body,{childList:true,subtree:true,characterData:true});addEventListener('resize',queue,{passive:true})}
 window.RistDicePrivacy={modes:MODES,state,setMode,cycle,setSumEnabled,isGm,refresh};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
