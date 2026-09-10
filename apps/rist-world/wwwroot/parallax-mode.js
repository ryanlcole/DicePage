(()=>{
 'use strict';

 const PREF_KEY='rist.parallax.enabled.v1';
 const DEPTH_KEY='rist.parallax.tier-depths.v1';
 const DEFAULT_DEPTHS={0:0.15,1:0.55,2:0.95,3:1.25};
 const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));

 function loadPref(){
  try{return localStorage.getItem(PREF_KEY)!=='off';}catch{return true;}
 }
 function savePref(enabled){try{localStorage.setItem(PREF_KEY,enabled?'on':'off');}catch{}}
 function loadDepths(){
  try{
   const parsed=JSON.parse(localStorage.getItem(DEPTH_KEY)||'{}');
   return {...DEFAULT_DEPTHS,...parsed};
  }catch{return {...DEFAULT_DEPTHS};}
 }
 function saveDepths(depths){try{localStorage.setItem(DEPTH_KEY,JSON.stringify(depths));}catch{}}

 const state={enabled:loadPref(),active:false,depths:loadDepths(),knownTiers:new Set([0,1,2,3])};

 function studio(){return document.querySelector('.worldbuilder-studio');}
 function landing(){return document.querySelector('.launcher-hub');}
 function rail(){return studio()?.querySelector('.studio-command-rail');}
 function viewer(){return studio()?.querySelector('.studio-viewer-canvas');}

 function depthForTier(tier){
  const key=String(Math.max(0,Number(tier)||0));
  const value=Number(state.depths[key]);
  return Number.isFinite(value)?clamp(value,0,2):1;
 }

 function announceChange(){
  window.dispatchEvent(new CustomEvent('rist-parallax-settings',{detail:{enabled:state.enabled,active:state.active,depths:{...state.depths}}}));
 }

 window.ristParallax={
  isEnabled:()=>state.enabled,
  isWorldBuilderActive:()=>state.active,
  depthForTier,
  getTierDepths:()=>({...state.depths}),
  setEnabled(enabled){state.enabled=!!enabled;savePref(state.enabled);sync();announceChange();return state.enabled;},
  setTierDepth(tier,value){state.depths[String(Math.max(0,Number(tier)||0))]=clamp(Number(value)||0,0,2);saveDepths(state.depths);renderDepthPanel();announceChange();return depthForTier(tier);}
 };

 function ensureStyle(){
  if(document.getElementById('rist-parallax-mode-style'))return;
  const style=document.createElement('style');
  style.id='rist-parallax-mode-style';
  style.textContent=`
   .wb-parallax-active .studio-workbench{pointer-events:none;opacity:.55}
   .wb-parallax-active .world-stage .tile-cell{pointer-events:none!important;cursor:default!important}
   .wb-parallax-active .studio-command-rail button:not([data-wb-parallax="true"]):not(.publish){pointer-events:none;opacity:.38}
   .studio-command-rail .wb-parallax-command{box-sizing:border-box;flex:0 0 auto;height:48px;min-width:104px;padding:4px 12px;display:grid;place-items:center;gap:2px;border:1px solid #4b5f69;border-radius:9px;background:#0d171e;color:#d4dde1;touch-action:manipulation}
   .studio-command-rail .wb-parallax-command strong{font:900 12px/1 system-ui;color:#f0ddb0}
   .studio-command-rail .wb-parallax-command small{font:800 7px/1 system-ui;letter-spacing:.06em;text-transform:uppercase;color:#8fa5b0}
   .studio-command-rail .wb-parallax-command.active{border-color:#d0aa56;background:#201b10}
   .wb-parallax-panel{position:absolute;z-index:95;left:50%;top:12px;transform:translateX(-50%);box-sizing:border-box;width:min(92%,520px);max-height:70%;overflow:auto;padding:10px;border:1px solid #846c39;border-radius:10px;background:#081117e8;color:#e8dec5;box-shadow:0 8px 26px #000b;backdrop-filter:blur(5px)}
   .wb-parallax-panel header{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px}.wb-parallax-panel header strong{color:#e5c878;font:900 12px/1 system-ui;letter-spacing:.08em}.wb-parallax-panel header small{color:#91a4ae;font:700 9px/1.3 system-ui;text-align:right}
   .wb-tier-depth{display:grid;grid-template-columns:64px minmax(0,1fr) 46px;align-items:center;gap:8px;padding:7px 0;border-top:1px solid #283840}.wb-tier-depth label{font:900 10px/1 system-ui;color:#d9c690}.wb-tier-depth output{font:800 9px/1 system-ui;color:#a9bbc4;text-align:right}.wb-tier-depth input{width:100%}
   .launcher-secondary .rist-parallax-toggle{border-color:#5f6f77}.launcher-secondary .rist-parallax-toggle.parallax-on{border-color:#8e7440;color:#f1ddb0}
  `;
  document.head.appendChild(style);
 }

 function ensureLandingToggle(){
  const host=landing()?.querySelector('.launcher-secondary');
  if(!host)return null;
  let button=host.querySelector('[data-rist-parallax-toggle="true"]');
  if(button)return button;
  button=document.createElement('button');
  button.type='button';
  button.className='rist-parallax-toggle';
  button.dataset.ristParallaxToggle='true';
  button.addEventListener('click',()=>{state.enabled=!state.enabled;savePref(state.enabled);sync();announceChange();});
  host.appendChild(button);
  return button;
 }

 function ensureParallaxButton(){
  const host=rail();
  if(!host)return null;
  let button=host.querySelector('[data-wb-parallax="true"]');
  if(button)return button;
  button=document.createElement('button');
  button.type='button';
  button.className='wb-parallax-command';
  button.dataset.wbParallax='true';
  button.innerHTML='<strong>Parallax</strong><small>Off</small>';
  button.addEventListener('click',()=>{
   state.active=!state.active;
   if(state.active){
    const zLock=[...host.querySelectorAll('button')].find(b=>b.querySelector('strong')?.textContent?.trim()==='Z-Lock');
    if(zLock?.querySelector('small')?.textContent?.trim()==='Unlocked')zLock.click();
   }
   sync();announceChange();
  });
  const view=[...host.querySelectorAll('button')].find(b=>b.querySelector('strong')?.textContent?.trim()==='View');
  if(view)view.insertAdjacentElement('afterend',button);else host.appendChild(button);
  return button;
 }

 function renderDepthPanel(){
  const host=viewer();
  if(!host)return;
  host.querySelector(':scope > .wb-parallax-panel')?.remove();
  if(!state.active)return;
  const panel=document.createElement('section');
  panel.className='wb-parallax-panel';
  panel.setAttribute('aria-label','Parallax tier depth controls');
  const status=state.enabled?'DEVICE PARALLAX ON':'DEVICE PARALLAX OFF';
  panel.innerHTML=`<header><strong>PARALLAX</strong><small>${status}<br>Adjust visual depth by Tier</small></header>`;
  [...state.knownTiers].sort((a,b)=>a-b).forEach(tier=>{
   const row=document.createElement('div');row.className='wb-tier-depth';
   const value=depthForTier(tier);
   row.innerHTML=`<label>Tier ${tier}</label><input type="range" min="0" max="2" step="0.05" value="${value}"><output>${value.toFixed(2)}×</output>`;
   const input=row.querySelector('input');const output=row.querySelector('output');
   input.addEventListener('input',()=>{
    const next=clamp(Number(input.value)||0,0,2);
    state.depths[String(tier)]=next;output.textContent=`${next.toFixed(2)}×`;saveDepths(state.depths);announceChange();
   });
   panel.appendChild(row);
  });
  host.appendChild(panel);
 }

 function sync(){
  ensureStyle();
  const toggle=ensureLandingToggle();
  if(toggle){toggle.classList.toggle('parallax-on',state.enabled);toggle.innerHTML=`<span>◫</span>PARALLAX ${state.enabled?'ON':'OFF'}`;}
  const root=studio();
  if(!root){state.active=false;return;}
  root.classList.toggle('wb-parallax-active',state.active);
  const button=ensureParallaxButton();
  if(button){button.classList.toggle('active',state.active);button.querySelector('small').textContent=state.active?(state.enabled?'On':'User Off'):'Off';}
  renderDepthPanel();
 }

 window.addEventListener('rist-depth-visuals',event=>{
  const visuals=Array.isArray(event.detail)?event.detail:[];
  for(const visual of visuals){const tier=Number(visual.tierIndex??visual.TierIndex);if(Number.isFinite(tier)&&tier>=0)state.knownTiers.add(tier);}
  if(state.active)renderDepthPanel();
 });

 const observer=new MutationObserver(()=>sync());
 document.addEventListener('DOMContentLoaded',()=>{ensureStyle();sync();observer.observe(document.body,{childList:true,subtree:true});});
 if(document.readyState!=='loading'){ensureStyle();sync();observer.observe(document.body,{childList:true,subtree:true});}
})();
