(()=>{
 'use strict';
 const ZONE_KEY='rist:mmo-zone';
 const ZONES_KEY='rist:mmo-zones';
 const ORIGIN={u:0,x:0,y:0,z:0,id:'MapU000X000Y000Z',alias:'Geanaph',owner:'shaelvien'};
 let corner='';
 let target=null;
 let zone=(()=>{try{return JSON.parse(localStorage.getItem(ZONE_KEY)||'null')}catch{return null}})();
 let zones=(()=>{try{const value=JSON.parse(localStorage.getItem(ZONES_KEY)||'[]');return Array.isArray(value)?value:[]}catch{return []}})();
 const coord=(u,x,y,z)=>({u,x,y,z,id:`MapU${String(u).padStart(3,'0')}X${signed(x)}Y${signed(y)}Z${signed(z)}`});
 function signed(value){return value<0?`-${String(Math.abs(value)).padStart(3,'0')}`:String(value).padStart(3,'0')}
 const key=c=>`${c.u}|${c.x}|${c.y}|${c.z}`;
 const occupied=()=>new Set([key(ORIGIN),...zones.filter(z=>z?.claimed).map(key)]);
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
 function saveZone(next){zone=next;localStorage.setItem(ZONE_KEY,JSON.stringify(next));if(next?.claimed){const k=key(next);zones=zones.filter(z=>key(z)!==k);zones.push(next);localStorage.setItem(ZONES_KEY,JSON.stringify(zones))}syncState()}
 const hasWorldExpansionPublic=()=>[...document.querySelectorAll('.public-table-card .public-card-name')].some(node=>node.textContent.trim().toLowerCase()==='world expansion');
 function syncState(){const claimed=zone?.claimed===true,expansion=hasWorldExpansionPublic(),mmo=document.body.classList.contains('rist-mmo-shaelvien');document.body.classList.toggle('rist-mmo-zone-claimed',claimed);document.body.classList.toggle('rist-mmo-owned-zone',claimed);document.body.classList.toggle('rist-world-expansion-public',expansion);document.querySelectorAll('.mmo-corner-plus').forEach(b=>{b.hidden=!mmo||claimed})}
 function first(){target=nearestFree(corner);const p=panel();const where=target?`<p>Nearest free cube: <strong>${target.id}</strong></p>`:'';p.innerHTML=`<h2>Are you a GameMaster?</h2>${where}<div class="mmo-choice-row"><button data-a="yes">Yes</button><button data-a="no">No</button><button data-a="explain">Explain…</button></div><button class="mmo-close" data-close>Exit</button>`;getOverlay().hidden=false;p.onclick=e=>{const answer=e.target.closest('[data-a]')?.dataset.a;if(answer==='yes')second();else if(answer==='no'||e.target.closest('[data-close]'))close();else if(answer==='explain')explain()}}
 function explain(){const p=panel();p.innerHTML='<h2>GameMaster Expansion</h2><p>MMO opens on the public origin zone. The + controls at its corners search outward in that direction and select the nearest unclaimed 100×100-mile cube. A newly claimed cube begins as the standard Ocean 071 world and can be renamed without changing its coordinate identity.</p><p>Additional expansion from an owned zone remains controlled by World Expansion eligibility.</p><button data-back>Back</button><button class="mmo-close" data-close>Exit</button>';p.onclick=e=>{if(e.target.closest('[data-back]'))first();else if(e.target.closest('[data-close]'))close()}}
 function second(){const p=panel();p.innerHTML='<h2>How will you build?</h2><div class="mmo-choice-row"><button data-build="personal">Personal</button><button data-build="shaelvien">MMO Cube</button></div><button class="mmo-close" data-close>Exit</button>';p.onclick=e=>{const type=e.target.closest('[data-build]')?.dataset.build;if(type)choose(type);else if(e.target.closest('[data-close]'))close()}}
 function choose(type){
  if(type==='personal'){window.RistMMO?.setMode?.('local');document.querySelector('.mmo-personal-zone-action')?.click();const record={type:'personal',corner:null,claimed:true,blank:true};saveZone(record);close();document.dispatchEvent(new CustomEvent('rist:mmo-build',{detail:record}));return}
  if(!target)target=nearestFree(corner);if(!target)return;
  window.RistMMO?.setMode?.('shaelvien');document.querySelector('.mmo-shaelvien-zone-action')?.click();const record={...target,type:'shaelvien',alias:'map1',corner,claimed:true,status:'owned-zone',baseTerrain:'Ocean 071',connections:1,aiEligible:false};saveZone(record);const p=panel();p.innerHTML=`<h2>MMO Cube Claimed</h2><p><strong>${record.id}</strong> is now your GM cube. Its starting surface is Ocean 071 and its alias is <strong>map1</strong>. The coordinate identity remains permanent if you rename it.</p><p><strong>Connections:</strong> 1 / 2<br><strong>AI white-space:</strong> Locked</p><button class="mmo-close" data-close>Exit</button>`;p.onclick=e=>{if(e.target.closest('[data-close]'))close()};document.dispatchEvent(new CustomEvent('rist:mmo-build',{detail:record}));
 }
 function ensure(){document.querySelectorAll('.map-shell').forEach(shell=>{if(shell.querySelector('.mmo-corner-plus'))return;for(const c of ['nw','ne','sw','se']){const button=document.createElement('button');button.type='button';button.className=`mmo-corner-plus mmo-${c}`;button.textContent='+';button.setAttribute('aria-label',`Find nearest free MMO cube ${c.toUpperCase()}`);button.onclick=e=>{e.stopPropagation();corner=c;first()};shell.appendChild(button)}});syncState()}
 const queue=()=>window.RistRuntime?.frame?.('mmo-build',ensure)??requestAnimationFrame(ensure);
 document.addEventListener('rist:dom-change',queue);document.addEventListener('rist:mmo-mode',syncState);queue();
})();
