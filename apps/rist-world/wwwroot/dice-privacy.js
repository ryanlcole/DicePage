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
 let fallbackMode=localStorage.getItem(MODE_KEY)||'public';
 let fallbackSum=localStorage.getItem(SUM_KEY)!=='false';
 let lastTotal='0',lastMode='',lastSum=null;
 function footer(){return document.getElementById('footer-slider')}
 function currentMode(){const dom=footer()?.dataset.rollVisibility;return MODES.some(x=>x.key===dom)?dom:fallbackMode}
 function currentSum(){const dom=footer()?.dataset.sumEnabled;if(dom==='true')return true;if(dom==='false')return false;return fallbackSum}
 function spec(){const mode=currentMode();return MODES.find(x=>x.key===mode)||MODES[1]}
 function isGm(){const role=document.querySelector('#header-slider [aria-label="Role"] small')?.textContent?.trim();return role==='GM'}
 function setMode(next){if(!MODES.some(x=>x.key===next))next='public';fallbackMode=next;localStorage.setItem(MODE_KEY,next);const native=footer()?.querySelector('.roll-visibility-toggle[data-native-roll-mode="true"]');if(native){const desired=MODES.findIndex(x=>x.key===next);const current=MODES.findIndex(x=>x.key===currentMode());let clicks=(desired-current+MODES.length)%MODES.length;while(clicks-->0)native.click();return}apply()}
 function cycle(){const mode=currentMode(),i=MODES.findIndex(x=>x.key===mode);setMode(MODES[(i+1+MODES.length)%MODES.length].key)}
 function setSumEnabled(enabled){if(!isGm())return false;enabled=!!enabled;fallbackSum=enabled;localStorage.setItem(SUM_KEY,String(enabled));const native=footer()?.querySelector('[data-native-sum-toggle="true"]');if(native&&currentSum()!==enabled){native.click();return true}apply();return true}
 function state(){const s=spec();return{mode:s.key,label:s.label,audience:s.audience,sumEnabled:currentSum(),gm:isGm(),discrete:s.key==='gm-discrete'}}
 function ensureToggle(rail){let btn=rail.querySelector(':scope > .roll-visibility-toggle');if(btn)return btn;btn=document.createElement('button');btn.type='button';btn.className='roll-visibility-toggle';btn.addEventListener('click',cycle);rail.prepend(btn);return btn}
 function publishRollIntent(target){const s=state();document.dispatchEvent(new CustomEvent('rist:dice-roll-intent',{detail:{...s,die:target.getAttribute('aria-label')||'die'}}))}
 function applyDiscreteMask(s){const masked=s.key==='gm-discrete'&&!isGm();document.body.classList.toggle('rist-gm-discrete-mask',masked);if(masked){document.querySelectorAll('.world-stage .rolled-die').forEach(die=>{die.setAttribute('title','Discrete roll');die.setAttribute('aria-label','Discrete dice roll result hidden from player')})}}
 function apply(){
  const shell=footer(),rail=shell?.querySelector('.release-footer-track,.dice-circular-set');if(!shell||!rail)return;
  const s=spec(),sumEnabled=currentSum();fallbackMode=s.key;fallbackSum=sumEnabled;localStorage.setItem(MODE_KEY,s.key);localStorage.setItem(SUM_KEY,String(sumEnabled));shell.style.setProperty('--roll-mode-bg',s.color);shell.style.background=s.color;rail.style.background=s.color;
  const btn=ensureToggle(rail);if(btn.dataset.nativeRollMode!=='true'){btn.textContent=s.label;btn.title=`${s.label} — tap to change`;btn.setAttribute('aria-label',`${s.label}. Tap to change dice roll visibility.`)}btn.dataset.mode=s.key;
  let style=document.getElementById('rist-dice-privacy-style');if(!style){style=document.createElement('style');style.id='rist-dice-privacy-style';style.textContent=`
#footer-slider .roll-visibility-toggle{box-sizing:border-box;flex:0 0 auto;height:74px;min-width:82px;padding:0 9px;border:1px solid #d2b873;border-radius:9px;background:#111920;color:#f4e2ad;font:800 10px/1.15 system-ui;text-align:center;white-space:normal;touch-action:manipulation}
#footer-slider[data-roll-visibility="test"],#footer-slider[data-roll-visibility="test"] .release-footer-track{background:#c6a400!important}
#footer-slider[data-roll-visibility="public"],#footer-slider[data-roll-visibility="public"] .release-footer-track{background:#0b0f13!important}
#footer-slider[data-roll-visibility="group"],#footer-slider[data-roll-visibility="group"] .release-footer-track{background:#0c4c86!important}
#footer-slider[data-roll-visibility="gm"],#footer-slider[data-roll-visibility="gm"] .release-footer-track{background:#b85b12!important}
#footer-slider[data-roll-visibility="gm-discrete"],#footer-slider[data-roll-visibility="gm-discrete"] .release-footer-track{background:#8d1818!important}
.rist-gm-discrete-mask .world-stage .rolled-die{filter:blur(9px) saturate(.45)!important;transform:scale(.94)!important}
`;document.head.appendChild(style)}
  const sum=shell.querySelector('.sum');if(sum)sum.hidden=!sumEnabled||s.key==='gm-discrete';
  applyDiscreteMask(s);
  if(lastMode!==s.key){lastMode=s.key;document.dispatchEvent(new CustomEvent('rist:dice-visibility-changed',{detail:state()}))}
  if(lastSum!==sumEnabled){lastSum=sumEnabled;document.dispatchEvent(new CustomEvent('rist:dice-sum-setting-changed',{detail:{enabled:sumEnabled}}))}
 }
 function bindRollClicks(){const shell=footer();if(!shell||shell.dataset.privacyRollBound==='1')return;shell.dataset.privacyRollBound='1';shell.addEventListener('click',e=>{const t=e.target instanceof Element?e.target.closest('.die-button'):null;if(t)publishRollIntent(t)},true)}
 function watchTotal(){const shell=footer(),total=shell?.querySelector('.sum span:last-child');if(!total)return;const next=total.textContent?.trim()||'0';if(next===lastTotal)return;lastTotal=next;const s=state();document.dispatchEvent(new CustomEvent('rist:dice-roll-result',{detail:{...s,total:s.discrete?null:Number(next),maskedForUser:s.discrete}}))}
 function refresh(){apply();bindRollClicks();watchTotal()}
 let queued=false;function queue(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;refresh()})}
 const observer=new MutationObserver(queue);
 function start(){refresh();observer.observe(document.body,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['data-roll-visibility','data-sum-enabled']});addEventListener('resize',queue,{passive:true})}
 window.RistDicePrivacy={modes:MODES,state,setMode,cycle,setSumEnabled,isGm,refresh};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
