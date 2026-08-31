(()=>{
 'use strict';
 const ZONE_KEY='rist:mmo-zone';
 const ZONES_KEY='rist:mmo-zones';
 const SANDBOX_KEY='rist:sandbox-zone';
 const ORIGIN={u:0,x:0,y:0,z:0,id:'MapU000X000Y000Z',alias:'Geanaph',owner:'shaelvien'};
 const DEFAULT_SIZE=100;
 const DEFAULT_TILE='Ocean 071';
 let corner='';
 let target=null;
 let zone=(()=>{try{return JSON.parse(localStorage.getItem(ZONE_KEY)||'null')}catch{return null}})();
 let sandbox=(()=>{try{return JSON.parse(localStorage.getItem(SANDBOX_KEY)||'null')}catch{return null}})();
 let zones=(()=>{try{const value=JSON.parse(localStorage.getItem(ZONES_KEY)||'[]');return Array.isArray(value)?value:[]}catch{return []}})();
 const coord=(u,x,y,z)=>({u,x,y,z,id:`MapU${String(u).padStart(3,'0')}X${signed(x)}Y${signed(y)}Z${signed(z)}`});
 function signed(value){return value<0?`-${String(Math.abs(value)).padStart(3,'0')}`:String(value).padStart(3,'0')}
 const key=c=>`${c.u}|${c.x}|${c.y}|${c.z}`;
 const occupied=()=>new Set([key(ORIGIN),...zones.filter(z=>z?.claimed&&z?.type==='shaelvien').map(key)]);
 function nearestFree(which){
  const used=occupied();
  const sx=which.endsWith('e')?1:-1;
  const sy=which.startsWith('s')?1:-1;
  for(let ring=1;ring<10000;ring++){
   for(let step=0;step<=ring;step++){
    for(const [dx,dy] of [[ring,step],[step,ring]]){
     const candidate=coord(0,sx*dx,sy*dy,0);
     if(!used.has(key(candidate)))return candidate;
    }
   }
  }
  return null;
 }
 function getOverlay(){let overlay=document.querySelector('.mmo-build-overlay');if(overlay)return overlay;overlay=document.createElement('div');overlay.className='mmo-build-overlay';overlay.hidden=true;overlay.innerHTML='<section class="mmo-build-panel" role="dialog" aria-modal="true" aria-label="RIST MMO world expansion"></section>';document.body.appendChild(overlay);overlay.addEventListener('click',e=>{if(e.target===overlay)close()});return overlay}
 const panel=()=>getOverlay().querySelector('.mmo-build-panel');
 const close=()=>{getOverlay().hidden=true};
 function saveZone(next){zone=next;localStorage.setItem(ZONE_KEY,JSON.stringify(next));if(next?.claimed&&next?.type==='shaelvien'){const k=key(next);zones=zones.filter(z=>key(z)!==k);zones.push(next);localStorage.setItem(ZONES_KEY,JSON.stringify(zones))}syncState()}
 function saveSandbox(next){sandbox=next;localStorage.setItem(SANDBOX_KEY,JSON.stringify(next));syncState()}
 const hasWorldExpansionPublic=()=>[...document.querySelectorAll('.public-table-card .public-card-name')].some(node=>node.textContent.trim().toLowerCase()==='world expansion');
 function ocean071Url(){
  const normalize=value=>(value||'').toLowerCase().replace(/[^a-z0-9]+/g,' ');
  const candidates=[...document.querySelectorAll('img')];
  for(const img of candidates){
   const own=normalize(`${img.alt||''} ${img.title||''} ${img.dataset?.name||''} ${img.dataset?.assetName||''}`);
   const parent=normalize(img.closest('[data-name],[data-asset-name],.tile-card,.asset-card,.tile-browser-item,.asset-item')?.textContent||'');
   if(((own+' '+parent).includes('ocean 071')&&img.currentSrc)||((own+' '+parent).includes('ocean 071')&&img.src))return img.currentSrc||img.src;
  }
  return '';
 }
 function ensureTempStyle(){
  if(document.getElementById('rist-default-ocean-style'))return;
  const style=document.createElement('style');style.id='rist-default-ocean-style';
  style.textContent=`
   .rist-default-ocean{position:absolute;inset:0;z-index:0;pointer-events:none;overflow:hidden;background:#163d55;background-repeat:repeat;background-size:1% 1%;}
   .rist-default-ocean::after{content:"";position:absolute;inset:0;background-image:linear-gradient(to right,rgba(255,255,255,.16) 1px,transparent 1px),linear-gradient(to bottom,rgba(255,255,255,.16) 1px,transparent 1px);background-size:1% 1%;pointer-events:none;}
   .rist-default-ocean-label{position:absolute;left:50%;top:10px;transform:translateX(-50%);z-index:2;padding:4px 9px;border-radius:999px;background:rgba(0,0,0,.58);color:#fff;font:600 12px/1.2 system-ui,sans-serif;letter-spacing:.02em;white-space:nowrap;pointer-events:none;}
   .map:has(>.rist-default-ocean)>:not(.rist-default-ocean):not(.rist-default-ocean-label){position:relative;z-index:1;}
  `;
  document.head.appendChild(style);
 }
 function ensureDefaultTable(){
  const mmo=document.body.classList.contains('rist-mmo-shaelvien');
  const local=document.body.classList.contains('rist-mmo-local');
  const claimed=zone?.claimed===true&&zone?.type==='shaelvien';
  const show=(mmo&&!claimed)||local;
  document.querySelectorAll('.rist-default-ocean,.rist-default-ocean-label').forEach(el=>{if(!show)el.remove()});
  if(!show)return;
  ensureTempStyle();
  document.querySelectorAll('.map').forEach(map=>{
   let surface=map.querySelector(':scope > .rist-default-ocean');
   if(!surface){surface=document.createElement('div');surface.className='rist-default-ocean';surface.dataset.columns=String(DEFAULT_SIZE);surface.dataset.rows=String(DEFAULT_SIZE);surface.dataset.tileMiles='1';surface.dataset.tileName=DEFAULT_TILE;map.prepend(surface)}
   surface.dataset.temporary=String(mmo&&!claimed);
   surface.dataset.scope=local?'sandbox':'public';
   const url=ocean071Url();
   if(url)surface.style.backgroundImage=`url("${String(url).replace(/"/g,'\\"')}")`;
   let label=map.querySelector(':scope > .rist-default-ocean-label');
   if(!label){label=document.createElement('div');label.className='rist-default-ocean-label';map.appendChild(label)}
   label.textContent=local?'Sandbox · 100 × 100 miles · Ocean 071 · 1 mile per tile':'Temporary Public Zone · 100 × 100 miles · Ocean 071 · 1 mile per tile';
  });
 }
 function syncState(){const claimed=zone?.claimed===true&&zone?.type==='shaelvien',expansion=hasWorldExpansionPublic(),mmo=document.body.classList.contains('rist-mmo-shaelvien');document.body.classList.toggle('rist-mmo-zone-claimed',claimed);document.body.classList.toggle('rist-mmo-owned-zone',claimed);document.body.classList.toggle('rist-world-expansion-public',expansion);document.querySelectorAll('.mmo-corner-plus').forEach(b=>{b.hidden=!mmo||claimed});ensureDefaultTable()}
 function first(){target=nearestFree(corner);const p=panel();const where=target?`<p>Nearest free cube: <strong>${target.id}</strong></p>`:'';p.innerHTML=`<h2>Are you a GameMaster?</h2>${where}<div class="mmo-choice-row"><button data-a="yes">Yes</button><button data-a="no">No</button><button data-a="explain">Explain…</button></div><button class="mmo-close" data-close>Exit</button>`;getOverlay().hidden=false;p.onclick=e=>{const answer=e.target.closest('[data-a]')?.dataset.a;if(answer==='yes')second();else if(answer==='no'||e.target.closest('[data-close]'))close();else if(answer==='explain')explain()}}
 function explain(){const p=panel();p.innerHTML='<h2>GameMaster Expansion</h2><p>Both Sandbox and the public new-zone table begin as a 100×100-mile Ocean 071 surface: 10,000 one-mile tiles. Sandbox work remains outside the MMO world. The public version is temporary until a cube is claimed. The + controls search outward in that direction and select the nearest unclaimed 100×100-mile cube.</p><p>Additional expansion from an owned MMO zone remains controlled by World Expansion eligibility.</p><button data-back>Back</button><button class="mmo-close" data-close>Exit</button>';p.onclick=e=>{if(e.target.closest('[data-back]'))first();else if(e.target.closest('[data-close]'))close()}}
 function second(){const p=panel();p.innerHTML='<h2>How will you build?</h2><div class="mmo-choice-row"><button data-build="personal">Sandbox</button><button data-build="shaelvien">MMO Cube</button></div><button class="mmo-close" data-close>Exit</button>';p.onclick=e=>{const type=e.target.closest('[data-build]')?.dataset.build;if(type)choose(type);else if(e.target.closest('[data-close]'))close()}}
 function choose(type){
  if(type==='personal'){
   window.RistMMO?.setMode?.('local');
   document.querySelector('.mmo-personal-zone-action')?.click();
   const record={type:'personal',alias:'map1',claimed:false,scope:'sandbox',baseTerrain:DEFAULT_TILE,widthMiles:DEFAULT_SIZE,heightMiles:DEFAULT_SIZE,tileMiles:1};
   saveSandbox(record);
   close();
   document.dispatchEvent(new CustomEvent('rist:sandbox-build',{detail:record}));
   return;
  }
  if(!target)target=nearestFree(corner);if(!target)return;
  window.RistMMO?.setMode?.('shaelvien');document.querySelector('.mmo-shaelvien-zone-action')?.click();const record={...target,type:'shaelvien',alias:'map1',corner,claimed:true,status:'owned-zone',baseTerrain:DEFAULT_TILE,widthMiles:DEFAULT_SIZE,heightMiles:DEFAULT_SIZE,tileMiles:1,connections:1,aiEligible:false};saveZone(record);const p=panel();p.innerHTML=`<h2>MMO Cube Claimed</h2><p><strong>${record.id}</strong> is now your GM cube. Its starting surface is 100×100 miles of Ocean 071 at one mile per tile, and its alias is <strong>map1</strong>. The coordinate identity remains permanent if you rename it.</p><p><strong>Connections:</strong> 1 / 2<br><strong>AI white-space:</strong> Locked</p><button class="mmo-close" data-close>Exit</button>`;p.onclick=e=>{if(e.target.closest('[data-close]'))close()};document.dispatchEvent(new CustomEvent('rist:mmo-build',{detail:record}));
 }
 function ensure(){document.querySelectorAll('.map-shell').forEach(shell=>{if(shell.querySelector('.mmo-corner-plus'))return;for(const c of ['nw','ne','sw','se']){const button=document.createElement('button');button.type='button';button.className=`mmo-corner-plus mmo-${c}`;button.textContent='+';button.setAttribute('aria-label',`Find nearest free MMO cube ${c.toUpperCase()}`);button.onclick=e=>{e.stopPropagation();corner=c;first()};shell.appendChild(button)}});syncState()}
 const queue=()=>window.RistRuntime?.frame?.('mmo-build',ensure)??requestAnimationFrame(ensure);
 document.addEventListener('rist:dom-change',queue);document.addEventListener('rist:mmo-mode',syncState);queue();
})();