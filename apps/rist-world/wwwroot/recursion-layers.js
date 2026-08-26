(()=>{
 /* RIST recursion model
    TABLETOP: the physical root surface.
    TIER: a distinct elevated/contained surface (world, region, building floor, mountain level, etc.).
    LAYER: things stacked on one tier (base, terrain, structures, actors, effects, weather).
    Existing asset `layer` metadata is accepted as a legacy tier hint so old packs keep working. */
 const tierOrder=['WORLD','REGION','LOCAL','SITE','ROOM','ENCOUNTER','OBJECT','CONTAINER','CONTENTS'];
 const layerOrder=['BASE','TERRAIN','STRUCTURE','ACTOR','EFFECT','WEATHER'];
 const normalizeTier=v=>{
  const x=String(v||'WORLD').trim().toUpperCase();
  if(x==='ZONE'||x==='CONTINENT')return'REGION';
  if(x==='AREA')return'LOCAL';
  if(x==='TACTICAL'||x==='INSTANCE')return'ENCOUNTER';
  if(x==='UNIVERSAL'||x==='WEATHER'||!tierOrder.includes(x))return'WORLD';
  return x;
 };
 const normalizeLayer=v=>{const x=String(v||'TERRAIN').trim().toUpperCase();return layerOrder.includes(x)?x:'TERRAIN'};
 const tierRank=t=>Math.max(0,tierOrder.indexOf(normalizeTier(t)));
 const zoomTier=z=>z<1.8?'WORLD':z<4.5?'REGION':z<10?'LOCAL':z<20?'SITE':z<38?'ROOM':z<70?'ENCOUNTER':z<130?'OBJECT':z<260?'CONTAINER':'CONTENTS';
 const opacityFor=(nativeRank,viewRank)=>{const d=viewRank-nativeRank;if(d<0)return 0;if(d===0)return 1;if(d===1)return .62;if(d===2)return .34;return .16};
 let catalog=[],scheduled=false,tiltX=0,tiltY=0,rightDrag=null,orientationWired=false,lastStageBase='';
 const stored=()=>{try{return JSON.parse(localStorage.getItem('rist.recursion.tier.v3')||'{}')}catch{return {}}};
 const remembered=stored();
 const saveRemembered=()=>{try{localStorage.setItem('rist.recursion.tier.v3',JSON.stringify(remembered))}catch{}};
 const map=()=>document.querySelector('.map');
 const stage=()=>document.querySelector('.world-stage');
 const zoom=()=>Math.max(.1,parseFloat(map()?.dataset.zoom||'1')||1);
 const currentTier=()=>zoomTier(zoom());
 const fingerprint=el=>{const img=el.querySelector('img'),src=img?.getAttribute('src')||'';return[el.getAttribute('aria-label')||'',src].join('|')};
 const inferredTierByScale=el=>{const m=map(),r=el.getBoundingClientRect(),mr=m?.getBoundingClientRect();if(!mr?.width)return'WORLD';const ratio=r.width/mr.width;if(ratio<=.006)return'LOCAL';if(ratio<=.035)return'REGION';return'WORLD'};
 const catalogHit=el=>{const img=el.querySelector('img'),src=img?.getAttribute('src')||'',name=el.getAttribute('aria-label')||'';return catalog.find(x=>(x.image&&src&&String(x.image).split('?')[0]===src.split('?')[0])||(x.name&&name&&x.name===name))||null};
 const roofish=el=>/roof|ceiling|canopy|overhang/i.test(el.getAttribute('aria-label')||'');
 const weatherish=el=>/weather|rain|snow|storm|fog|cloud|sunlight|moonlight/i.test(el.getAttribute('aria-label')||'');
 const effectish=el=>/effect|aura|glow|spell|fire|smoke|poison|plasma|lightning/i.test(el.getAttribute('aria-label')||'');
 const structureish=el=>roofish(el)||/wall|building|house|tower|bridge|door|window|stairs|floor/i.test(el.getAttribute('aria-label')||'');
 const terrainish=el=>/terrain|mountain|hill|river|water|ocean|forest|tree|road|ground|grass|sand|snow|lava|ice/i.test(el.getAttribute('aria-label')||'');
 function assetTier(el,hit=catalogHit(el)){
  const explicit=hit?.tier||hit?.nativeTier||'';
  if(explicit)return normalizeTier(explicit);
  const legacy=String(hit?.layer||'').toUpperCase();
  if(legacy&&legacy!=='UNIVERSAL'&&legacy!=='WEATHER'&&tierOrder.includes(normalizeTier(legacy)))return normalizeTier(legacy);
  const key=fingerprint(el);if(remembered[key])return normalizeTier(remembered[key]);
  const tier=inferredTierByScale(el);remembered[key]=tier;saveRemembered();return tier;
 }
 function assetLayer(el,hit=catalogHit(el)){
  const explicit=hit?.stackLayer||hit?.visualLayer||hit?.surfaceLayer||'';
  if(explicit)return normalizeLayer(explicit);
  if(String(hit?.layer||'').toUpperCase()==='WEATHER'||weatherish(el))return'WEATHER';
  if(el.classList.contains('piece')||el.classList.contains('mini')||el.classList.contains('pawn')||el.classList.contains('rolling-stock'))return'ACTOR';
  if(effectish(el))return'EFFECT';
  if(structureish(el))return'STRUCTURE';
  if(terrainish(el)||el.classList.contains('tile-cell')||el.classList.contains('tile'))return'TERRAIN';
  return'BASE';
 }
 const overlaps=(a,b)=>{const ar=a.getBoundingClientRect(),br=b.getBoundingClientRect(),x=ar.left+ar.width/2,y=ar.top+ar.height/2;return x>=br.left&&x<=br.right&&y>=br.top&&y<=br.bottom};
 function applyDepth(el,tier,layer,viewRank){
  const r=tierRank(tier),opacity=opacityFor(r,viewRank);
  el.dataset.recursionTier=tier;
  el.dataset.recursionLayer=layer;
  el.dataset.nativeLayer=tier; /* legacy compatibility */
  el.style.setProperty('--rist-tier-depth',String(r));
  el.style.setProperty('--rist-layer-depth',String(layerOrder.indexOf(layer)));
  el.style.setProperty('--rist-layer-opacity',String(opacity));
  el.toggleAttribute('data-recursion-ahead',r>viewRank);
  el.toggleAttribute('data-recursion-deep',viewRank-r>2);
 }
 function classify(){
  scheduled=false;
  const viewTier=currentTier(),viewRank=tierRank(viewTier),tiles=[...document.querySelectorAll('.tile-cell')],blockers=[];
  for(const el of tiles){
   const hit=catalogHit(el),tier=assetTier(el,hit),layer=assetLayer(el,hit);
   applyDepth(el,tier,layer,viewRank);
   if(layer==='STRUCTURE'&&roofish(el)){el.dataset.weatherBlocker='true';blockers.push(el)}else delete el.dataset.weatherBlocker;
  }
  for(const el of tiles){
   const tier=normalizeTier(el.dataset.recursionTier),layer=normalizeLayer(el.dataset.recursionLayer);
   let hidden=tierRank(tier)>viewRank+1;
   if(layer==='WEATHER'&&blockers.some(b=>normalizeTier(b.dataset.recursionTier)===tier&&b!==el&&overlaps(el,b)))hidden=true;
   el.toggleAttribute('data-recursion-hidden',hidden);
  }
  for(const el of document.querySelectorAll('.piece')){
   const hit=catalogHit(el),tier=assetTier(el,hit),layer=assetLayer(el,hit);
   applyDepth(el,tier,layer,viewRank);
   el.toggleAttribute('data-recursion-hidden',tierRank(tier)>viewRank+1);
  }
  for(const el of document.querySelectorAll('.tray-item')){
   const hit=catalogHit(el),tier=assetTier(el,hit),layer=assetLayer(el,hit);
   el.dataset.recursionTier=tier;el.dataset.recursionLayer=layer;el.dataset.nativeLayer=tier;
   el.title=(el.title||'Place asset').replace(/ Tier:.*$/,'').replace(/ Native layer:.*$/,'')+` Tier: ${tier}. Layer: ${layer}.`;
  }
  const m=map();if(m){
   m.dataset.recursionTier=viewTier;
   m.dataset.recursionLayer='BASE';
   m.dataset.recursionLayerLegacy=viewTier;
   m.style.setProperty('--rist-recursion-rank',String(viewRank));
  }
  const s=stage();if(s){s.dataset.recursionTabletop='WORLD';s.dataset.activeTier=viewTier;}
  document.documentElement.dataset.ristViewportTier=viewTier;
  document.documentElement.dataset.ristViewportLayer='BASE';
  applyTilt();
 }
 const schedule=()=>{if(!scheduled){scheduled=true;requestAnimationFrame(classify)}};
 function applyTilt(){const s=stage();if(!s)return;const raw=(s.style.transform||'').replace(/\s*rotateX\([^)]*\)/g,'').replace(/\s*rotateY\([^)]*\)/g,'').trim();if(raw)lastStageBase=raw;const base=raw||lastStageBase||'none';const composed=`${base==='none'?'':base+' '}rotateX(${tiltX.toFixed(2)}deg) rotateY(${tiltY.toFixed(2)}deg)`;if(s.style.transform!==composed)s.style.transform=composed}
 const setTilt=(x,y)=>{tiltX=Math.max(-10,Math.min(10,x));tiltY=Math.max(-12,Math.min(12,y));applyTilt()};
 function wireRightTilt(){const m=map();if(!m||m.dataset.ristTiltWired)return;m.dataset.ristTiltWired='1';m.addEventListener('contextmenu',e=>e.preventDefault());m.addEventListener('pointerdown',e=>{if(e.button!==2)return;rightDrag={x:e.clientX,y:e.clientY,tx:tiltX,ty:tiltY};m.setPointerCapture?.(e.pointerId);e.preventDefault();e.stopPropagation()});m.addEventListener('pointermove',e=>{if(!rightDrag||(e.buttons&2)!==2)return;setTilt(rightDrag.tx-(e.clientY-rightDrag.y)*.08,rightDrag.ty+(e.clientX-rightDrag.x)*.08);e.preventDefault();e.stopPropagation()});const end=e=>{if(rightDrag){rightDrag=null;e.preventDefault();e.stopPropagation()}};m.addEventListener('pointerup',end);m.addEventListener('pointercancel',end)}
 async function enableOrientation(){if(orientationWired)return;try{if(typeof DeviceOrientationEvent!=='undefined'&&typeof DeviceOrientationEvent.requestPermission==='function'){const p=await DeviceOrientationEvent.requestPermission();if(p!=='granted')return}}catch{return}orientationWired=true;addEventListener('deviceorientation',e=>{if(e.gamma==null||e.beta==null)return;setTilt((e.beta-45)*.10,e.gamma*.12)},{passive:true})}
 function wireOrientation(){const m=map();if(!m||m.dataset.ristOrientationWired)return;m.dataset.ristOrientationWired='1';m.addEventListener('pointerdown',()=>{enableOrientation()},{once:true,passive:true})}
 async function loadCatalog(){for(const url of ['data/atlas-public.json','assets/drive-tiles/catalog.json']){try{const r=await fetch(url,{cache:'no-store'});if(r.ok){const rows=await r.json();if(Array.isArray(rows))catalog.push(...rows)}}catch{}}schedule()}
 const observer=new MutationObserver(()=>{wireRightTilt();wireOrientation();schedule()});
 function start(){observer.observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['data-zoom']});wireRightTilt();wireOrientation();loadCatalog();schedule();setInterval(()=>{const s=stage();if(!s)return;const raw=(s.style.transform||'').replace(/\s*rotateX\([^)]*\)/g,'').replace(/\s*rotateY\([^)]*\)/g,'').trim();if(raw&&raw!==lastStageBase){lastStageBase=raw;applyTilt()}},180)}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 addEventListener('resize',schedule,{passive:true});addEventListener('orientationchange',schedule,{passive:true});
 window.RistRecursion={currentTier,tiers:[...tierOrder],layers:[...layerOrder],refresh:schedule};
})();
