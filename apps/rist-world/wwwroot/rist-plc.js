(()=>{
 'use strict';

 const PHASE={BOOT:0,TABLETOP:10,SHELL:20,INTERACTION:30,COMPLETE:40};
 const groups={
  tabletop:[
   'back-logout.js?v=2',
   'grid-coordinate-system.js?v=5'
  ],
  shell:[
   'character-board-focus.js?v=7',
   'map-context-sidebar.js?v=5',
   'recursion-layers.js?v=3',
   'mmo-mode.js?v=4',
   'token-game-launcher.js?v=3',
   'start-menu.js?v=2',
   'js/faux-depth.js?v=2'
  ],
  interaction:[
   'card-defaults.js?v=2',
   'portrait-editor-live.js?v=3',
   'card-appearance.js?v=3',
   'mmo-build.js?v=3',
   'asset-credit.js?v=2',
   'cursors-haptics.js?v=2',
   'art-studio.js?v=7',
   'art-surface-controls.js?v=2',
   'sprite-creator.js?v=2'
  ]
 };
 const values={tabletop:PHASE.TABLETOP,shell:PHASE.SHELL,interaction:PHASE.INTERACTION};
 const dependencies={tabletop:null,shell:'tabletop',interaction:'shell'};
 const state={phase:PHASE.BOOT,phaseName:'boot',started:new Set(),completed:new Set(),running:new Map(),loaded:new Map(),errors:[],groups};

 const canonical=src=>new URL(src,document.baseURI).pathname;
 const announce=(kind,name)=>{
  const value=values[name]??state.phase;
  dispatchEvent(new CustomEvent(`rist:phase-${kind}`,{detail:{name,value}}));
  dispatchEvent(new CustomEvent('rist:runtime-phase',{detail:{kind,name,value,completed:[...state.completed]}}));
 };
 const complete=name=>{
  state.completed.add(name);state.phase=values[name]??state.phase;state.phaseName=name;
  document.documentElement.dataset.ristPhase=name;announce('complete',name);
 };
 function loadScript(src){
  const key=canonical(src);if(state.loaded.has(key))return state.loaded.get(key);
  const existing=[...document.scripts].find(script=>{try{return canonical(script.src)===key}catch{return false}});
  if(existing?.dataset.ristLoaded==='1'||existing?.readyState==='complete'){
   existing.dataset.ristLoaded='1';const ready=Promise.resolve(existing);state.loaded.set(key,ready);return ready;
  }
  const task=new Promise(resolve=>{
   const script=existing||document.createElement('script');
   let settled=false;
   const finish=ok=>{
    if(settled)return;settled=true;script.dataset.ristLoaded='1';
    if(!ok){const error={src,key,phase:state.phaseName,time:new Date().toISOString()};state.errors.push(error);console.error('[RIST PLC] module failed',src);dispatchEvent(new CustomEvent('rist:module-error',{detail:error}))}
    resolve(script);
   };
   script.addEventListener('load',()=>finish(true),{once:true});script.addEventListener('error',()=>finish(false),{once:true});
   if(!existing){script.src=src;script.async=false;script.dataset.ristPhaseLoad='1';document.body.appendChild(script)}
   else setTimeout(()=>finish(true),0);
  });
  state.loaded.set(key,task);return task;
 }
 async function ensureGroup(name){
  if(state.completed.has(name))return;if(state.running.has(name))return state.running.get(name);
  const task=(async()=>{const dependency=dependencies[name];if(dependency)await ensureGroup(dependency);state.started.add(name);announce('start',name);for(const src of groups[name]||[])await loadScript(src);complete(name)})();
  state.running.set(name,task);try{await task}finally{state.running.delete(name)}
 }
 async function scanCore(){await ensureGroup('shell')}
 async function scanInteraction(){await ensureGroup('interaction');state.phase=PHASE.COMPLETE;state.phaseName='complete';document.documentElement.dataset.ristPhase='complete';dispatchEvent(new CustomEvent('rist:runtime-phase',{detail:{kind:'complete',name:'complete',value:PHASE.COMPLETE,completed:[...state.completed]}}))}

 const scheduled=new Map();
 function frame(key,callback){if(scheduled.has(key))return;scheduled.set(key,requestAnimationFrame(()=>{scheduled.delete(key);try{callback()}catch(error){console.error('[RIST runtime]',key,error)}}))}
 function signalDom(){frame('dom',()=>document.dispatchEvent(new CustomEvent('rist:dom-change')))}
 function signalViewport(){frame('viewport',()=>document.dispatchEvent(new CustomEvent('rist:viewport-change')))}
 const app=document.querySelector('#app');
 if(app)new MutationObserver(signalDom).observe(app,{subtree:true,childList:true,attributes:true,attributeFilter:['data-pan-x','data-pan-y','data-zoom','data-front-token','data-character','data-shaelvien-ai-authority']});
 addEventListener('resize',signalViewport,{passive:true});addEventListener('orientationchange',signalViewport,{passive:true});
 document.addEventListener('pointermove',e=>{if(e.target instanceof Element&&e.target.closest('.map,.rist-art-studio'))signalViewport()},{capture:true,passive:true});
 document.addEventListener('wheel',e=>{if(e.target instanceof Element&&e.target.closest('.map,.rist-art-studio'))signalViewport()},{capture:true,passive:true});

 const core=()=>void scanCore(),interaction=()=>void scanInteraction();
 addEventListener('rist:app-ready',core,{once:true});setTimeout(core,10000);
 addEventListener('pointerdown',interaction,{once:true,capture:true,passive:true});addEventListener('keydown',interaction,{once:true,capture:true});
 if(!matchMedia('(max-width:800px)').matches){const idle=window.requestIdleCallback||((fn)=>setTimeout(fn,1800));idle(interaction,{timeout:5000})}
 window.RistRuntime={frame,signalDom,signalViewport};window.RistPLC={PHASE,state,ensureGroup,scanCore,scanInteraction,loadScript};
})();
