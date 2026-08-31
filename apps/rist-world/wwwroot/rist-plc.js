(()=>{
 'use strict';

 const PHASE={BOOT:0,TABLETOP:10,SHELL:20,INTERACTION:30,COMPLETE:40};
 const groups={
  tabletop:[
   'back-logout.js?v=2',
   'grid-coordinate-system.js?v=5'
  ],
  shell:[
   'map-context-sidebar.js?v=5',
   'recursion-layers.js?v=5',
   'mmo-mode.js?v=6',
   'token-game-launcher.js?v=3',
   'start-menu.js?v=2',
   'js/faux-depth.js?v=3'
  ],
  interaction:[
   'portrait-editor-live.js?v=3',
   'card-appearance.js?v=3',
   'mmo-build.js?v=3',
   'asset-credit.js?v=2',
   'cursors-haptics.js?v=2',
   'art-studio.js?v=7',
   'art-surface-controls.js?v=2',
   'sprite-creator.js?v=3'
  ]
 };
 const styles={
  tabletop:['css/button-artwork-fit.css?v=1'],
  shell:['css/character-universal.css?v=universal-badge-1'],
  interaction:[
   'css/art-studio.css?v=20260829-consolidated-1',
   'css/art-surface-controls.css?v=1',
   'css/asset-credit.css?v=1'
  ]
 };
 const values={tabletop:PHASE.TABLETOP,shell:PHASE.SHELL,interaction:PHASE.INTERACTION};
 const dependencies={tabletop:null,shell:'tabletop',interaction:'shell'};
 const state={phase:PHASE.BOOT,phaseName:'boot',started:new Set(),completed:new Set(),running:new Map(),loaded:new Map(),errors:[],groups,styles};

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
 function recordFailure(src,key,type){
  const error={src,key,type,phase:state.phaseName,time:new Date().toISOString()};
  state.errors.push(error);console.error(`[RIST PLC] ${type} failed`,src);dispatchEvent(new CustomEvent('rist:module-error',{detail:error}));
 }
 function loadScript(src){
  const path=canonical(src),key=`script:${path}`;if(state.loaded.has(key))return state.loaded.get(key);
  const existing=[...document.scripts].find(script=>{try{return canonical(script.src)===path}catch{return false}});
  if(existing?.dataset.ristLoaded==='1'||existing?.readyState==='complete'){
   existing.dataset.ristLoaded='1';const ready=Promise.resolve(existing);state.loaded.set(key,ready);return ready;
  }
  const task=new Promise(resolve=>{
   const script=existing||document.createElement('script');let settled=false;
   const finish=ok=>{if(settled)return;settled=true;script.dataset.ristLoaded='1';if(!ok)recordFailure(src,key,'script');resolve(script)};
   script.addEventListener('load',()=>finish(true),{once:true});script.addEventListener('error',()=>finish(false),{once:true});
   if(!existing){script.src=src;script.async=false;script.dataset.ristPhaseLoad='1';document.body.appendChild(script)}
   else setTimeout(()=>finish(true),0);
  });
  state.loaded.set(key,task);return task;
 }
 function loadStyle(src){
  const path=canonical(src),key=`style:${path}`;if(state.loaded.has(key))return state.loaded.get(key);
  const existing=[...document.querySelectorAll('link[rel="stylesheet"]')].find(link=>{try{return canonical(link.href)===path}catch{return false}});
  if(existing?.sheet){existing.dataset.ristLoaded='1';const ready=Promise.resolve(existing);state.loaded.set(key,ready);return ready}
  const task=new Promise(resolve=>{
   const link=existing||document.createElement('link');let settled=false;
   const finish=ok=>{if(settled)return;settled=true;link.dataset.ristLoaded='1';if(!ok)recordFailure(src,key,'style');resolve(link)};
   link.addEventListener('load',()=>finish(true),{once:true});link.addEventListener('error',()=>finish(false),{once:true});
   if(!existing){link.rel='stylesheet';link.href=src;link.dataset.ristPhaseLoad='1';document.head.appendChild(link)}
   else setTimeout(()=>finish(!!link.sheet),0);
  });
  state.loaded.set(key,task);return task;
 }
 async function ensureGroup(name){
  if(state.completed.has(name))return;if(state.running.has(name))return state.running.get(name);
  const task=(async()=>{
   const dependency=dependencies[name];if(dependency)await ensureGroup(dependency);
   state.started.add(name);announce('start',name);
   await Promise.all((styles[name]||[]).map(loadStyle));
   for(const src of groups[name]||[])await loadScript(src);
   complete(name);
  })();
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

 const motion={requested:false,attached:false,promise:null};
 function attachOrientation(){
  if(motion.attached)return;motion.attached=true;
  addEventListener('deviceorientation',event=>{
   const detail={
    alpha:Number.isFinite(event.alpha)?event.alpha:0,
    beta:Number.isFinite(event.beta)?event.beta:0,
    gamma:Number.isFinite(event.gamma)?event.gamma:0,
    absolute:!!event.absolute
   };
   dispatchEvent(new CustomEvent('rist:orientation',{detail}));
  },{passive:true});
 }
 function requestOrientation(){
  if(motion.attached)return Promise.resolve(true);
  if(motion.promise)return motion.promise;
  motion.requested=true;
  motion.promise=(async()=>{
   try{
    const ctor=window.DeviceOrientationEvent;if(!ctor)return false;
    if(typeof ctor.requestPermission==='function'){
     const permission=await ctor.requestPermission();if(permission!=='granted')return false;
    }
    attachOrientation();return true;
   }catch{return false}
   finally{if(!motion.attached)motion.promise=null}
  })();
  return motion.promise;
 }

 const core=()=>void scanCore(),interaction=()=>void scanInteraction();
 addEventListener('rist:app-ready',core,{once:true});setTimeout(core,10000);
 addEventListener('pointerdown',interaction,{once:true,capture:true,passive:true});addEventListener('keydown',interaction,{once:true,capture:true});
 document.addEventListener('pointerdown',event=>{
  if((event.pointerType==='touch'||event.pointerType==='pen')&&event.target instanceof Element&&event.target.closest('.map'))void requestOrientation();
 },{capture:true,passive:true});
 if(!matchMedia('(max-width:800px)').matches){const idle=window.requestIdleCallback||((fn)=>setTimeout(fn,1800));idle(interaction,{timeout:5000})}
 window.RistRuntime={frame,signalDom,signalViewport,requestOrientation,motion};window.RistPLC={PHASE,state,ensureGroup,scanCore,scanInteraction,loadScript,loadStyle};
})();
