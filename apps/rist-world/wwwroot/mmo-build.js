(()=>{
 const ZONE_KEY='rist:mmo-zone';
 let corner='';
 let zone=(()=>{try{return JSON.parse(localStorage.getItem(ZONE_KEY)||'null')}catch{return null}})();
 function getOverlay(){let o=document.querySelector('.mmo-build-overlay');if(o)return o;o=document.createElement('div');o.className='mmo-build-overlay';o.hidden=true;o.innerHTML='<section class="mmo-build-panel" role="dialog" aria-modal="true" aria-label="Shaelvien world expansion"></section>';document.body.appendChild(o);o.addEventListener('click',e=>{if(e.target===o)close()});return o}
 function panel(){return getOverlay().querySelector('.mmo-build-panel')}
 function close(){getOverlay().hidden=true}
 function saveZone(next){zone=next;localStorage.setItem(ZONE_KEY,JSON.stringify(next));syncState()}
 function hasWorldExpansionPublic(){return [...document.querySelectorAll('.public-table-card .public-card-name')].some(x=>x.textContent.trim().toLowerCase()==='world expansion')}
 function syncState(){
  const claimed=zone?.type==='shaelvien';
  const expansion=hasWorldExpansionPublic();
  document.body.classList.toggle('rist-mmo-zone-claimed',claimed);
  document.body.classList.toggle('rist-mmo-owned-zone',claimed);
  document.body.classList.toggle('rist-world-expansion-public',expansion);
 }
 function first(){const p=panel();p.innerHTML='<h2>Are you a GameMaster?</h2><div class="mmo-choice-row"><button data-a="yes">Yes</button><button data-a="no">No</button><button data-a="explain">Explain…</button></div><button class="mmo-close" data-close>Exit</button>';getOverlay().hidden=false;p.onclick=e=>{const a=e.target.closest('[data-a]')?.dataset.a;if(a==='yes')second();else if(a==='no'||e.target.closest('[data-close]'))close();else if(a==='explain')explain()}}
 function explain(){const p=panel();p.innerHTML='<h2>GameMaster Expansion</h2><p>Your first Personal zone is a blank map you build from scratch. Your first Shaelvien zone receives the current MMO map as its starting map. After a zone is claimed, adjacent + controls remain hidden unless a purchased World Expansion card is flipped to the public card area.</p><p>Shaelvien grows like a chess board. AI connective building only becomes eligible after two GM maps connect to the same blank area.</p><button data-back>Back</button><button class="mmo-close" data-close>Exit</button>';p.onclick=e=>{if(e.target.closest('[data-back]'))first();else if(e.target.closest('[data-close]'))close()}}
 function second(){const p=panel();p.innerHTML='<h2>How will you build?</h2><div class="mmo-choice-row"><button data-build="personal">Personal</button><button data-build="shaelvien">Shaelvien</button></div><button class="mmo-close" data-close>Exit</button>';p.onclick=e=>{const b=e.target.closest('[data-build]')?.dataset.build;if(b)choose(b);else if(e.target.closest('[data-close]'))close()}}
 function choose(type){
  if(type==='personal'){
   window.RistMMO?.setMode?.('local');
   document.querySelector('.mmo-personal-zone-action')?.click();
   saveZone({type:'personal',corner:null,claimed:true});
   close();
   document.dispatchEvent(new CustomEvent('rist:mmo-build',{detail:{type,corner:null,blank:true}}));
   return;
  }
  window.RistMMO?.setMode?.('shaelvien');
  document.querySelector('.mmo-shaelvien-zone-action')?.click();
  const record={type:'shaelvien',corner,claimed:true,status:'owned-zone',connections:1,aiEligible:false};
  saveZone(record);
  const p=panel();p.innerHTML='<h2>Shaelvien Zone Claimed</h2><p>The current map is now the starting map for your GM zone. This zone is editable by its owner. World expansion controls are hidden until a World Expansion card is purchased and flipped public.</p><p><strong>Connections:</strong> 1 / 2<br><strong>AI white-space:</strong> Locked</p><button class="mmo-close" data-close>Exit</button>';p.onclick=e=>{if(e.target.closest('[data-close]'))close()};
  document.dispatchEvent(new CustomEvent('rist:mmo-build',{detail:record}));
 }
 function ensure(){document.querySelectorAll('.map-shell').forEach(shell=>{if(!shell.querySelector('.mmo-corner-plus'))for(const c of ['nw','ne','sw','se']){const b=document.createElement('button');b.type='button';b.className=`mmo-corner-plus mmo-${c}`;b.textContent='+';b.setAttribute('aria-label','Build beside map');b.onclick=e=>{e.stopPropagation();corner=c;first()};shell.appendChild(b)}});syncState()}
 const observer=new MutationObserver(()=>ensure());observer.observe(document.documentElement,{childList:true,subtree:true});
 document.addEventListener('rist:mmo-mode',syncState);document.addEventListener('DOMContentLoaded',ensure);setTimeout(ensure,0);
})();
