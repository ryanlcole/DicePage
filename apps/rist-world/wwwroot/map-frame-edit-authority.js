(()=>{
 'use strict';
 const STORE='rist.mapEditLocks.v1';
 let editing=false,lockedLayer='',host=null,roleSource=null,roleBtn=null,editBtn=null,observer=null;
 const assetSelector='.world-stage .tile-cell,.world-stage .piece';
 const qa=(s,r=document)=>[...(r?.querySelectorAll?.(s)||[])];
 const q=(s,r=document)=>r?.querySelector?.(s)||null;
 const text=e=>(e?.textContent||'').replace(/\s+/g,' ').trim();
 const currentRole=()=>/^GM$/i.test(text(roleSource?.querySelector('strong')||roleSource))?'GM':'RP';
 const isGm=()=>currentRole()==='GM';
 function readStore(){try{return JSON.parse(sessionStorage.getItem(STORE)||'{}')}catch{return{}}}
 function writeStore(v){try{sessionStorage.setItem(STORE,JSON.stringify(v))}catch{}}
 function layerKey(){const status=text(q('.map .status'))||text(q('.map-shell .status'))||'map';const map=q('.map');return [status,map?.getAttribute('aria-label')||''].join('|')}
 function assetKey(el,index=0){if(!el)return'';if(!el.dataset.ristEditKey){const kind=el.classList.contains('tile-cell')?'tile':([...el.classList].find(c=>['piece','mini','pin','pawn','token','bit'].includes(c))||'asset');const name=el.getAttribute('aria-label')||el.getAttribute('title')||text(el.querySelector('img'))||text(el);const style=el.getAttribute('style')||'';el.dataset.ristEditKey=`${kind}:${name}:${style}:${index}`}return el.dataset.ristEditKey}
 function stateFor(el,index){const key=assetKey(el,index),all=readStore(),layer=all[lockedLayer||layerKey()]||{};return layer[key]==='unlocked'?'unlocked':'locked'}
 function setState(el,state,index){const lk=lockedLayer||layerKey(),all=readStore(),layer=all[lk]||{};layer[assetKey(el,index)]=state;all[lk]=layer;writeStore(all);paintAsset(el,state,index)}
 function ensureBadge(el,index){let b=q(':scope > .rist-edit-lock-toggle',el);if(!b){b=document.createElement('button');b.type='button';b.className='rist-edit-lock-toggle';b.setAttribute('aria-label','Toggle asset lock');b.innerHTML='<span aria-hidden="true">●</span>';b.addEventListener('pointerdown',e=>{e.preventDefault();e.stopPropagation();e.stopImmediatePropagation()},{capture:true});b.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();setState(el,stateFor(el,index)==='unlocked'?'locked':'unlocked',index)});el.appendChild(b)}return b}
 function paintAsset(el,state,index){el.classList.toggle('rist-edit-unlocked',state==='unlocked');el.classList.toggle('rist-edit-locked',state!=='unlocked');el.dataset.ristAssetLock=state;if(editing){ensureBadge(el,index).setAttribute('aria-pressed',state==='unlocked'?'true':'false')}else q(':scope > .rist-edit-lock-toggle',el)?.remove()}
 function syncAssets(){const assets=qa(assetSelector);assets.forEach((el,i)=>{let state=stateFor(el,i);if(editing&&!el.dataset.ristSeenBeforeEdit){state='unlocked';setState(el,state,i);el.dataset.ristSeenBeforeEdit='1'}else paintAsset(el,state,i)})}
 function clearEditMarks(){qa(assetSelector).forEach((el,i)=>{paintAsset(el,stateFor(el,i),i);delete el.dataset.ristSeenBeforeEdit})}
 function updateEditButton(){if(!editBtn)return;editBtn.hidden=!isGm();editBtn.classList.toggle('active',editing);editBtn.setAttribute('aria-pressed',editing?'true':'false');editBtn.textContent=editing?'EDIT ✓':'EDIT'}
 function enterEdit(){if(!isGm())return;editing=true;lockedLayer=layerKey();document.documentElement.classList.add('rist-map-editing');qa(assetSelector).forEach(el=>el.dataset.ristSeenBeforeEdit='1');syncAssets();updateEditButton()}
 function leaveEdit(){editing=false;document.documentElement.classList.remove('rist-map-editing');clearEditMarks();lockedLayer='';updateEditButton()}
 function toggleEdit(){editing?leaveEdit():enterEdit()}
 function frame(){const shell=q('.map-shell');if(!shell)return null;if(host&&!document.body.contains(host))host=null;if(!host){host=document.createElement('div');host.className='rist-map-frame-controls rist-map-frame-role-controls';host.setAttribute('role','toolbar');host.setAttribute('aria-label','Map role controls');shell.appendChild(host)}return host}
 function chooseRole(){
  roleSource=q('#header-slider button[aria-label="Role"]')||roleSource;if(!roleSource)return;
  const target=isGm()?'RolePlayer':'GameMaster';
  roleSource.click();
  setTimeout(()=>{
   const choices=qa('#header-slider .root-menu-panel[aria-label="Choose role"] button');
   const choice=choices.find(b=>text(b)===target);
   if(choice)choice.click();
  },0);
 }
 function updateRoleButton(){if(!roleBtn)return;const gm=isGm();roleBtn.textContent=gm?'GameMaster':'RolePlayer';roleBtn.classList.toggle('active',gm);roleBtn.setAttribute('aria-pressed',gm?'true':'false');updateEditButton()}
 function locateRoleControl(){
  roleSource=q('#header-slider button[aria-label="Role"]')||roleSource;
  const f=frame();if(!f)return;
  if(!roleBtn){roleBtn=document.createElement('button');roleBtn.type='button';roleBtn.className='rist-map-frame-toggle rist-role-toggle';roleBtn.setAttribute('aria-label','Toggle GameMaster and RolePlayer');roleBtn.addEventListener('click',chooseRole);f.appendChild(roleBtn)}else if(roleBtn.parentElement!==f)f.appendChild(roleBtn);
  if(!editBtn){editBtn=document.createElement('button');editBtn.type='button';editBtn.className='rist-map-frame-toggle rist-edit-toggle';editBtn.addEventListener('click',toggleEdit);f.appendChild(editBtn)}else if(editBtn.parentElement!==f)f.appendChild(editBtn);
  updateRoleButton();
 }
 function removeDuplicateMenu(){
  qa('.world-context-menu').forEach(el=>el.remove());
  qa('button').forEach(b=>{if(/^menu$/i.test(text(b))&&!b.closest('.rist-start-overlay')&&!b.closest('.locked-tile-menu'))b.remove()});
 }
 function navigationBlocked(target){if(!editing)return false;const el=target?.closest?.('button,[role="button"],select');if(!el)return false;if(el.closest('.rist-map-frame-controls'))return false;return /\b(tier|layer|plane)\b/i.test(`${text(el)} ${el.getAttribute('aria-label')||''}`)}
 document.addEventListener('click',e=>{if(navigationBlocked(e.target)){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation()}},true);
 document.addEventListener('pointerdown',e=>{const el=e.target?.closest?.(assetSelector);if(!el||e.target?.closest?.('.rist-edit-lock-toggle'))return;const assets=qa(assetSelector),i=assets.indexOf(el);if(stateFor(el,i)!=='unlocked'){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation()}},true);
 function scan(){removeDuplicateMenu();locateRoleControl();syncAssets();if(editing&&layerKey()!==lockedLayer)leaveEdit()}
 let raf=0;const schedule=()=>{if(raf)return;raf=requestAnimationFrame(()=>{raf=0;scan()})};
 function start(){scan();observer=new MutationObserver(schedule);observer.observe(q('#app')||document.body,{childList:true,subtree:true});window.addEventListener('resize',schedule,{passive:true})}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.RistMapEdit={get active(){return editing},toggle:toggleEdit,refresh:scan};
})();