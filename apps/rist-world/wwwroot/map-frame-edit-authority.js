(()=>{
 'use strict';
 const STORE='rist.mapEditLocks.v1';
 let editing=false,lockedLayer='',host=null,worldBtn=null,roleBtn=null,editBtn=null,observer=null;
 const assetSelector='.world-stage .tile-cell,.world-stage .piece';
 const qa=(s,r=document)=>[...(r?.querySelectorAll?.(s)||[])];
 const q=(s,r=document)=>r?.querySelector?.(s)||null;
 const text=e=>(e?.textContent||'').replace(/\s+/g,' ').trim();
 const isGm=()=>/^GM$/i.test(text(roleBtn?.querySelector('strong')||roleBtn));
 function readStore(){try{return JSON.parse(sessionStorage.getItem(STORE)||'{}')}catch{return{}}}
 function writeStore(v){try{sessionStorage.setItem(STORE,JSON.stringify(v))}catch{}}
 function layerKey(){
  const status=text(q('.map .status'))||text(q('.map-shell .status'))||'map';
  const map=q('.map');
  return [status,map?.getAttribute('aria-label')||''].join('|');
 }
 function assetKey(el,index=0){
  if(!el)return'';
  if(!el.dataset.ristEditKey){
   const kind=el.classList.contains('tile-cell')?'tile':([...el.classList].find(c=>['piece','mini','pin','pawn','token','bit'].includes(c))||'asset');
   const name=el.getAttribute('aria-label')||el.getAttribute('title')||text(el.querySelector('img'))||text(el);
   const style=el.getAttribute('style')||'';
   el.dataset.ristEditKey=`${kind}:${name}:${style}:${index}`;
  }
  return el.dataset.ristEditKey;
 }
 function stateFor(el,index){
  const key=assetKey(el,index),all=readStore(),layer=all[lockedLayer||layerKey()]||{};
  return layer[key]==='unlocked'?'unlocked':'locked';
 }
 function setState(el,state,index){
  const lk=lockedLayer||layerKey(),all=readStore(),layer=all[lk]||{};
  layer[assetKey(el,index)]=state;all[lk]=layer;writeStore(all);paintAsset(el,state,index);
 }
 function ensureBadge(el,index){
  let b=q(':scope > .rist-edit-lock-toggle',el);
  if(!b){
   b=document.createElement('button');b.type='button';b.className='rist-edit-lock-toggle';b.setAttribute('aria-label','Toggle asset lock');b.innerHTML='<span aria-hidden="true">●</span>';
   b.addEventListener('pointerdown',e=>{e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();},{capture:true});
   b.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();const cur=stateFor(el,index);setState(el,cur==='unlocked'?'locked':'unlocked',index);});
   el.appendChild(b);
  }
  return b;
 }
 function paintAsset(el,state,index){
  el.classList.toggle('rist-edit-unlocked',state==='unlocked');
  el.classList.toggle('rist-edit-locked',state!=='unlocked');
  el.dataset.ristAssetLock=state;
  if(editing){const b=ensureBadge(el,index);b.setAttribute('aria-pressed',state==='unlocked'?'true':'false');}
  else q(':scope > .rist-edit-lock-toggle',el)?.remove();
 }
 function syncAssets(){
  const assets=qa(assetSelector);
  assets.forEach((el,i)=>{
   let state=stateFor(el,i);
   if(editing&&!el.dataset.ristSeenBeforeEdit){state='unlocked';setState(el,state,i);el.dataset.ristSeenBeforeEdit='1';}
   else paintAsset(el,state,i);
  });
 }
 function clearEditMarks(){qa(assetSelector).forEach((el,i)=>{paintAsset(el,stateFor(el,i),i);delete el.dataset.ristSeenBeforeEdit;});}
 function updateEditButton(){
  if(!editBtn)return;
  editBtn.hidden=!isGm();
  editBtn.classList.toggle('active',editing);
  editBtn.setAttribute('aria-pressed',editing?'true':'false');
  editBtn.textContent=editing?'EDIT ✓':'EDIT';
 }
 function enterEdit(){
  if(!isGm())return;
  editing=true;lockedLayer=layerKey();document.documentElement.classList.add('rist-map-editing');
  qa(assetSelector).forEach(el=>el.dataset.ristSeenBeforeEdit='1');
  syncAssets();updateEditButton();
 }
 function leaveEdit(){
  editing=false;document.documentElement.classList.remove('rist-map-editing');
  clearEditMarks();lockedLayer='';updateEditButton();
 }
 function toggleEdit(){editing?leaveEdit():enterEdit()}
 function frame(){
  const shell=q('.map-shell');if(!shell)return null;
  if(host&&!document.body.contains(host))host=null;
  if(!host){
   host=document.createElement('div');host.className='rist-map-frame-controls';host.setAttribute('role','toolbar');host.setAttribute('aria-label','Map mode controls');
   host.innerHTML='<div class="rist-map-frame-left"></div><div class="rist-map-frame-right"></div>';
   shell.appendChild(host);
  }
  return host;
 }
 function locateLiveButtons(){
  worldBtn=q('#header-slider button[aria-label="Toggle Sandbox and MMO"]')||worldBtn;
  roleBtn=q('#header-slider button[aria-label="Role"]')||roleBtn;
  const f=frame();if(!f)return;
  const left=q('.rist-map-frame-left',f),right=q('.rist-map-frame-right',f);
  if(worldBtn&&worldBtn.parentElement!==left){worldBtn.classList.add('rist-map-frame-toggle','rist-world-toggle');left.appendChild(worldBtn)}
  if(roleBtn&&roleBtn.parentElement!==right){roleBtn.classList.add('rist-map-frame-toggle','rist-role-toggle');right.appendChild(roleBtn)}
  if(!editBtn){editBtn=document.createElement('button');editBtn.type='button';editBtn.className='rist-map-frame-toggle rist-edit-toggle';editBtn.addEventListener('click',toggleEdit);right.appendChild(editBtn)}
  else if(editBtn.parentElement!==right)right.appendChild(editBtn);
  updateEditButton();
 }
 function removeMenu(){
  qa('.world-context-menu').forEach(el=>el.remove());
  qa('button').forEach(b=>{if(/^menu$/i.test(text(b))&&!b.closest('.rist-start-overlay')&&!b.closest('.locked-tile-menu'))b.remove()});
 }
 function navigationBlocked(target){
  if(!editing)return false;
  const el=target?.closest?.('button,[role="button"],select');if(!el)return false;
  if(el.closest('.rist-map-frame-controls'))return false;
  const label=`${text(el)} ${el.getAttribute('aria-label')||''}`;
  return /\b(tier|layer|plane)\b/i.test(label);
 }
 document.addEventListener('click',e=>{
  if(navigationBlocked(e.target)){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();return;}
 },true);
 document.addEventListener('pointerdown',e=>{
  const el=e.target?.closest?.(assetSelector);if(!el||e.target?.closest?.('.rist-edit-lock-toggle'))return;
  const assets=qa(assetSelector),i=assets.indexOf(el),state=stateFor(el,i);
  if(state!=='unlocked'){
   e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();
  }
 },true);
 function scan(){removeMenu();locateLiveButtons();syncAssets();if(editing&&layerKey()!==lockedLayer){leaveEdit();}}
 let raf=0;const schedule=()=>{if(raf)return;raf=requestAnimationFrame(()=>{raf=0;scan()})};
 function start(){scan();observer=new MutationObserver(schedule);observer.observe(q('#app')||document.body,{childList:true,subtree:true});window.addEventListener('resize',schedule,{passive:true});}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.RistMapEdit={get active(){return editing},toggle:toggleEdit,refresh:scan};
})();
