(()=>{
 'use strict';
 /* RIST recursion model: TABLETOP > TIER > LAYER. */
 const tierOrder=['WORLD','REGION','LOCAL','SITE','ROOM','ENCOUNTER','OBJECT','CONTAINER','CONTENTS'];
 const layerOrder=['BASE','TERRAIN','STRUCTURE','ACTOR','EFFECT','WEATHER'];
 const tierRanks=new Map(tierOrder.map((name,index)=>[name,index]));
 const layerRanks=new Map(layerOrder.map((name,index)=>[name,index]));
 const normalizeTier=value=>{const x=String(value||'WORLD').trim().toUpperCase();if(x==='ZONE'||x==='CONTINENT')return'REGION';if(x==='AREA')return'LOCAL';if(x==='TACTICAL'||x==='INSTANCE')return'ENCOUNTER';if(x==='UNIVERSAL'||x==='WEATHER'||!tierRanks.has(x))return'WORLD';return x};
 const normalizeLayer=value=>{const x=String(value||'TERRAIN').trim().toUpperCase();return layerRanks.has(x)?x:'TERRAIN'};
 const tierRank=tier=>tierRanks.get(normalizeTier(tier))??0;
 const zoomTier=z=>z<1.8?'WORLD':z<4.5?'REGION':z<10?'LOCAL':z<20?'SITE':z<38?'ROOM':z<70?'ENCOUNTER':z<130?'OBJECT':z<260?'CONTAINER':'CONTENTS';
 const opacityFor=(nativeRank,viewRank)=>{const d=viewRank-nativeRank;return d<0?0:d===0?1:d===1?.62:d===2?.34:.16};
 const cleanUrl=value=>String(value||'').split('?')[0];
 const RECENT_KEY='rist.recursion.tier.v3';
 const remembered=(()=>{try{return JSON.parse(localStorage.getItem(RECENT_KEY)||'{}')}catch{return {}}})();
 const catalogByImage=new Map(),catalogByName=new Map();
 let scheduled=false,rememberSavePending=false,tiltX=0,tiltY=0,rightDrag=null,orientationWired=false,lastStageBase='',catalogLoaded=false;
 const map=()=>document.querySelector('.map');
 const stage=()=>document.querySelector('.world-stage');
 const zoom=()=>Math.max(.1,parseFloat(map()?.dataset.zoom||'1')||1);
 const currentTier=()=>zoomTier(zoom());
 const fingerprint=el=>`${el.getAttribute('aria-label')||''}|${el.querySelector('img')?.getAttribute('src')||''}`;
 function scheduleRememberedSave(){
  if(rememberSavePending)return;rememberSavePending=true;
  const save=()=>{rememberSavePending=false;try{localStorage.setItem(RECENT_KEY,JSON.stringify(remembered))}catch{}};
  if('requestIdleCallback'in window)requestIdleCallback(save,{timeout:1500});else setTimeout(save,250);
 }
 function inferredTierByScale(el,mapRect){const rect=el.getBoundingClientRect();if(!mapRect?.width)return'WORLD';const ratio=rect.width/mapRect.width;return ratio<=.006?'LOCAL':ratio<=.035?'REGION':'WORLD'}
 function catalogHit(el){
  const src=cleanUrl(el.querySelector('img')?.getAttribute('src'));
  if(src&&catalogByImage.has(src))return catalogByImage.get(src);
  const name=el.getAttribute('aria-label')||'';
  return name?catalogByName.get(name)||null:null;
 }
 const labelOf=el=>el.getAttribute('aria-label')||'';
 const roofish=el=>/roof|ceiling|canopy|overhang/i.test(labelOf(el));
 const weatherish=el=>/weather|rain|snow|storm|fog|cloud|sunlight|moonlight/i.test(labelOf(el));
 const effectish=el=>/effect|aura|glow|spell|fire|smoke|poison|plasma|lightning/i.test(labelOf(el));
 const structureish=el=>roofish(el)||/wall|building|house|tower|bridge|door|window|stairs|floor/i.test(labelOf(el));
 const terrainish=el=>/terrain|mountain|hill|river|water|ocean|forest|tree|road|ground|grass|sand|snow|lava|ice/i.test(labelOf(el));
 function assetTier(el,hit,mapRect){
  const explicit=hit?.tier||hit?.nativeTier||'';if(explicit)return normalizeTier(explicit);
  const legacy=String(hit?.layer||'').toUpperCase();if(legacy&&legacy!=='UNIVERSAL'&&legacy!=='WEATHER'&&tierRanks.has(normalizeTier(legacy)))return normalizeTier(legacy);
  const key=fingerprint(el);if(remembered[key])return normalizeTier(remembered[key]);
  const tier=inferredTierByScale(el,mapRect);remembered[key]=tier;scheduleRememberedSave();return tier;
 }
 function assetLayer(el,hit){
  const explicit=hit?.stackLayer||hit?.visualLayer||hit?.surfaceLayer||'';if(explicit)return normalizeLayer(explicit);
  if(String(hit?.layer||'').toUpperCase()==='WEATHER'||weatherish(el))return'WEATHER';
  if(el.classList.contains('piece')||el.classList.contains('mini')||el.classList.contains('pawn')||el.classList.contains('rolling-stock'))return'ACTOR';
  if(effectish(el))return'EFFECT';if(structureish(el))return'STRUCTURE';if(terrainish(el)||el.classList.contains('tile-cell')||el.classList.contains('tile'))return'TERRAIN';return'BASE';
 }
 function applyDepth(el,tier,layer,viewRank){
  const rank=tierRank(tier),opacity=opacityFor(rank,viewRank);
  if(el.dataset.recursionTier!==tier)el.dataset.recursionTier=tier;if(el.dataset.recursionLayer!==layer)el.dataset.recursionLayer=layer;if(el.dataset.nativeLayer!==tier)el.dataset.nativeLayer=tier;
  el.style.setProperty('--rist-tier-depth',String(rank));el.style.setProperty('--rist-layer-depth',String(layerRanks.get(layer)??0));el.style.setProperty('--rist-layer-opacity',String(opacity));
  el.toggleAttribute('data-recursion-ahead',rank>viewRank);el.toggleAttribute('data-recursion-deep',viewRank-rank>2);
 }
 function classify(){
  scheduled=false;const m=map();if(!m)return;
  const mapRect=m.getBoundingClientRect(),viewTier=currentTier(),viewRank=tierRank(viewTier),tiles=[...document.querySelectorAll('.tile-cell')],blockersByTier=new Map();
  for(const el of tiles){const hit=catalogHit(el),tier=assetTier(el,hit,mapRect),layer=assetLayer(el,hit);applyDepth(el,tier,layer,viewRank);if(layer==='STRUCTURE'&&roofish(el)){el.dataset.weatherBlocker='true';const list=blockersByTier.get(tier)||[];list.push(el.getBoundingClientRect());blockersByTier.set(tier,list)}else delete el.dataset.weatherBlocker}
  for(const el of tiles){const tier=normalizeTier(el.dataset.recursionTier),layer=normalizeLayer(el.dataset.recursionLayer);let hidden=tierRank(tier)>viewRank+1;if(layer==='WEATHER'&&!hidden){const rect=el.getBoundingClientRect(),cx=rect.left+rect.width/2,cy=rect.top+rect.height/2;hidden=(blockersByTier.get(tier)||[]).some(block=>cx>=block.left&&cx<=block.right&&cy>=block.top&&cy<=block.bottom)}el.toggleAttribute('data-recursion-hidden',hidden)}
  for(const el of document.querySelectorAll('.piece')){const hit=catalogHit(el),tier=assetTier(el,hit,mapRect),layer=assetLayer(el,hit);applyDepth(el,tier,layer,viewRank);el.toggleAttribute('data-recursion-hidden',tierRank(tier)>viewRank+1)}
  for(const el of document.querySelectorAll('.tray-item')){const hit=catalogHit(el),tier=assetTier(el,hit,mapRect),layer=assetLayer(el,hit);el.dataset.recursionTier=tier;el.dataset.recursionLayer=layer;el.dataset.nativeLayer=tier;const base=(el.title||'Place asset').replace(/ Tier:.*$/,'').replace(/ Native layer:.*$/,'');const title=`${base} Tier: ${tier}. Layer: ${layer}.`;if(el.title!==title)el.title=title}
  m.dataset.recursionTier=viewTier;m.dataset.recursionLayer='BASE';m.dataset.recursionLayerLegacy=viewTier;m.style.setProperty('--rist-recursion-rank',String(viewRank));
  const s=stage();if(s){s.dataset.recursionTabletop='WORLD';s.dataset.activeTier=viewTier}
  document.documentElement.dataset.ristViewportTier=viewTier;document.documentElement.dataset.ristViewportLayer='BASE';applyTilt();
 }
 const schedule=()=>{if(scheduled)return;scheduled=true;(window.RistRuntime?.frame?window.RistRuntime.frame('recursion',classify):requestAnimationFrame(classify))};
 function stripTilt(transform){return String(transform||'').replace(/\s*rotateX\([^)]*\)/g,'').replace(/\s*rotateY\([^)]*\)/g,'').trim()}
 function applyTilt(){const s=stage();if(!s)return;const raw=stripTilt(s.style.transform);if(raw&&raw!==lastStageBase)lastStageBase=raw;const base=raw||lastStageBase||'';const composed=`${base}${base?' ':''}rotateX(${tiltX.toFixed(2)}deg) rotateY(${tiltY.toFixed(2)}deg)`;if(s.style.transform!==composed)s.style.transform=composed}
 const setTilt=(x,y)=>{tiltX=Math.max(-10,Math.min(10,x));tiltY=Math.max(-12,Math.min(12,y));applyTilt()};
 function wireRightTilt(){const m=map();if(!m||m.dataset.ristTiltWired==='2')return;m.dataset.ristTiltWired='2';m.addEventListener('contextmenu',e=>e.preventDefault());m.addEventListener('pointerdown',e=>{if(e.button!==2)return;rightDrag={id:e.pointerId,x:e.clientX,y:e.clientY,tx:tiltX,ty:tiltY};m.setPointerCapture?.(e.pointerId);e.preventDefault();e.stopPropagation()});m.addEventListener('pointermove',e=>{if(!rightDrag||rightDrag.id!==e.pointerId||(e.buttons&2)!==2)return;setTilt(rightDrag.tx-(e.clientY-rightDrag.y)*.08,rightDrag.ty+(e.clientX-rightDrag.x)*.08);e.preventDefault();e.stopPropagation()},{passive:false});const end=e=>{if(!rightDrag||rightDrag.id!==e.pointerId)return;rightDrag=null;e.preventDefault();e.stopPropagation()};m.addEventListener('pointerup',end);m.addEventListener('pointercancel',end)}
 async function enableOrientation(){if(orientationWired)return;try{if(typeof DeviceOrientationEvent!=='undefined'&&typeof DeviceOrientationEvent.requestPermission==='function'){const permission=await DeviceOrientationEvent.requestPermission();if(permission!=='granted')return}}catch{return}orientationWired=true;addEventListener('deviceorientation',e=>{if(e.gamma==null||e.beta==null)return;setTilt((e.beta-45)*.10,e.gamma*.12)},{passive:true})}
 function wireOrientation(){const m=map();if(!m||m.dataset.ristOrientationWired==='2')return;m.dataset.ristOrientationWired='2';m.addEventListener('pointerdown',()=>void enableOrientation(),{once:true,passive:true})}
 function indexCatalog(rows){for(const row of rows){const image=cleanUrl(row?.image);if(image&&!catalogByImage.has(image))catalogByImage.set(image,row);const name=String(row?.name||'');if(name&&!catalogByName.has(name))catalogByName.set(name,row)}}
 async function loadCatalog(){if(catalogLoaded)return;catalogLoaded=true;for(const url of ['data/atlas-public.json','assets/drive-tiles/catalog.json']){try{const response=await fetch(url,{cache:'default'});if(response.ok){const rows=await response.json();if(Array.isArray(rows))indexCatalog(rows)}}catch(error){console.warn('[RIST recursion] catalog unavailable',url,error)}}schedule()}
 function refresh(){wireRightTilt();wireOrientation();schedule()}
 document.addEventListener('rist:dom-change',refresh);document.addEventListener('rist:viewport-change',refresh);
 void loadCatalog();refresh();
 window.RistRecursion={currentTier,tiers:[...tierOrder],layers:[...layerOrder],refresh:schedule};
})();
