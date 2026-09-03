(()=>{
 'use strict';
 const CATALOG_URL='assets/drive-tiles/catalog.json';
 const TYPES=new Map([
  ['cards','Cards'],['tokens','Tokens / Chits'],['minis','Minis'],['rolling-stock','Rolling Stock'],
  ['pawns','Pawns / Meeples'],['tiles','Tiles'],['terrain','Terrains'],['sprites','Sprites'],['bits','Bits'],['library','Library']
 ]);
 const TERRAIN_FOLDERS=['Beach','Canyons','Cliffs','Desert','Forest','Hills','Ice','Jungle','Lakes','Mountains','Plains','Rivers','Snow','Swamp','Vent Fields','Volcano'];
 const CALFORTH_GAMES=['Backgammon','Battleship','Chess','Chinese Checkers','Cribbage','Dominoes','Go','Jax','Marbles','Othello','Playing Cards'];
 const TREE={
  tiles:{base:['Shaelvien','07_Media','Tiles'],children:{'':['Region_Map','World_Map'],'Region_Map':['Travel','Water'],'World_Map':['Landmarks','Overlays','Source','Terrain'],'World_Map/Terrain':TERRAIN_FOLDERS}},
  terrain:{base:['Shaelvien','07_Media','Tiles'],children:{'':['Region_Map','World_Map'],'Region_Map':['Travel','Water'],'World_Map':['Landmarks','Overlays','Source','Terrain'],'World_Map/Terrain':TERRAIN_FOLDERS}},
  sprites:{base:['Shaelvien','Sprites'],children:{'':[]}},
  library:{base:['Library'],children:{'':['Shaelvien','Calforth'],'Shaelvien':['Manuals'],'Calforth':['Rule Books','Assets'],'Calforth/Rule Books':CALFORTH_GAMES,'Calforth/Assets':CALFORTH_GAMES}}
 };
 let catalog=[],loaded=false,loading=false,path=[],lastSection='',scanFrame=0;
 const q=(s,r=document)=>r?.querySelector(s);
 const qa=(s,r=document)=>[...(r?.querySelectorAll(s)||[])];
 const row=n=>q(`.release-world-shell>.rist-deck-row.row${n}`);
 const current=()=>q('.rist-section-list>button.active')?.dataset.section||'';
 const same=(a,b)=>String(a||'').toLowerCase()===String(b||'').toLowerCase();
 const keyOf=p=>p.join('/');
 const text=e=>(e?.textContent||'').replace(/\s+/g,' ').trim();

 async function load(section){
  if(loaded||loading)return;
  loading=true;
  try{
   const r=await fetch(CATALOG_URL,{cache:'no-store'});
   if(!r.ok)throw new Error(`catalog ${r.status}`);
   const v=await r.json();catalog=Array.isArray(v)?v:[];loaded=true;
  }catch(e){console.error('RIST asset catalog load failed',e);catalog=[]}
  finally{
   loading=false;
   if(TYPES.has(current())&&current()===section)render(section);
  }
 }
 function ensureSelectors(){
  const list=q('.rist-section-list');if(!list)return false;
  const terrain=q('button[data-section="terrain"]',list);if(terrain)terrain.textContent='Terrains';
  const add=(section,name,before)=>{if(q(`button[data-section="${section}"]`,list))return;const b=document.createElement('button');b.type='button';b.dataset.section=section;b.textContent=name;b.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();select(section,b)},true);list.insertBefore(b,q(`button[data-section="${before}"]`,list)||q('button[data-section="add"]',list)||null)};
  add('sprites','Sprites','bits');add('library','Library','add');return true;
 }
 function select(section,button){path=[];lastSection=section;qa('.rist-section-list>button').forEach(b=>b.classList.toggle('active',b===button));render(section)}
 function relevant(a,section){
  const raw=`${a?.name||''} ${a?.folder||''} ${a?.directory||''} ${a?.layer||''} ${a?.image||''}`.toLowerCase();
  if(section==='terrain')return /terrain|beach|coast|ocean|river|lake|forest|jungle|plains|hill|mountain|cliff|canyon|desert|swamp|snow|ice|volcano|vent/.test(raw);
  if(section==='sprites')return /sprite|animation|animated|motion/.test(raw);
  if(section==='library')return /manual|book|library|guide|rule|shaelvien|calforth|chess|backgammon|battleship|checkers|cribbage|domino|go|jax|marble|othello|card/.test(raw);
  if(section==='tiles')return true;
  return section==='cards'?/card/.test(raw):section==='tokens'?/token|chit|marker|pin/.test(raw):section==='minis'?/mini/.test(raw):section==='rolling-stock'?/rolling|locomotive|train|vehicle/.test(raw):section==='pawns'?/pawn|meeple/.test(raw):section==='bits'?/bit|prop|object/.test(raw):true;
 }
 function gameName(raw){return CALFORTH_GAMES.find(game=>raw.includes(game.toLowerCase()))||''}
 function assetPath(a,section){
  if(section==='terrain'||section==='tiles'){
   const image=String(a?.image||'').toLowerCase();const layer=String(a?.layer||'').toLowerCase();const dir=String(a?.directory||'');const folder=String(a?.folder||'');
   const root=image.includes('/region/')||layer==='region'?'Region_Map':'World_Map';
   if(root==='World_Map'&&(same(dir,'Terrain')||section==='terrain'))return [root,'Terrain',folder].filter(Boolean);
   return [root,dir,folder].filter(Boolean);
  }
  if(section==='library'){
   const raw=`${a?.name||''} ${a?.folder||''} ${a?.directory||''} ${a?.image||''}`.toLowerCase();
   if(raw.includes('calforth')){const game=gameName(raw);const isRules=/rule|manual|book|guide/.test(raw);return ['Calforth',isRules?'Rule Books':'Assets',game].filter(Boolean)}
   return ['Shaelvien','Manuals'];
  }
  return [String(a?.directory||''),String(a?.folder||'')].filter(Boolean);
 }
 function children(section){
  const known=TREE[section]?.children?.[keyOf(path)]||[];const found=new Set(known);
  for(const a of catalog.filter(x=>relevant(x,section))){const p=assetPath(a,section);if(path.every((v,i)=>same(v,p[i]))&&p.length>path.length)found.add(p[path.length])}
  return [...found].sort((a,b)=>a.localeCompare(b,undefined,{numeric:true}));
 }
 function assets(section){return catalog.filter(a=>relevant(a,section)&&(()=>{const p=assetPath(a,section);return p.length===path.length&&path.every((v,i)=>same(v,p[i]))})())}
 function hasContents(section,next){const p=[...path,next];return catalog.some(a=>{if(!relevant(a,section))return false;const ap=assetPath(a,section);return p.every((v,i)=>same(v,ap[i]))})}
 function breadcrumb(section){
  const w=document.createElement('div');w.className='rist-folder-breadcrumb';const back=document.createElement('button');back.type='button';back.className='rist-folder-back';back.textContent='‹';back.disabled=!path.length;back.onclick=()=>{path.pop();render(section)};w.append(back);
  for(const part of TREE[section]?.base||['Shaelvien']){const s=document.createElement('span');s.className='rist-folder-fixed';s.textContent=part;w.append(s)}
  path.forEach((part,i)=>{const sep=document.createElement('span');sep.className='rist-folder-separator';sep.textContent='›';w.append(sep);const b=document.createElement('button');b.type='button';b.textContent=part;b.classList.toggle('active',i===path.length-1);b.onclick=()=>{path=path.slice(0,i+1);render(section)};w.append(b)});return w
 }
 function folder(section,name){const b=document.createElement('button');b.type='button';b.className='rist-bottom-folder-card';if(!hasContents(section,name))b.classList.add('empty-folder');b.setAttribute('aria-label',`Open ${name} folder`);const icon=document.createElement('span');icon.className='rist-folder-icon';icon.textContent='▰';const strong=document.createElement('strong');strong.textContent=name;b.append(icon,strong);b.onclick=()=>{path.push(name);render(section)};return b}
 function ensureLegacyLibrary(){const open=q('#header-slider .root-menu-button[aria-label="Assets"]');if(!q('.map-asset-inventory'))open?.click();setTimeout(()=>qa('.map-asset-inventory,.asset-slider-stack,#card-library,.assets-root-panel').forEach(el=>{el.classList.add('rist-old-assets-retired');el.setAttribute('aria-hidden','true')}),0)}
 function startRealDrag(asset,event){ensureLegacyLibrary();const x=event.clientX,y=event.clientY,pointerId=event.pointerId,pointerType=event.pointerType||'touch';let attempts=0;const stage=()=>{attempts++;const chooser=qa('.map-asset-choose').find(b=>(b.getAttribute('title')||'')===asset.name);if(!chooser){if(attempts<30)setTimeout(stage,50);return}chooser.click();setTimeout(()=>{const tray=qa('.tray-item.tile').find(b=>text(q('small',b))===asset.name)||qa('.tray-item.tile').at(-1);if(!tray)return;try{tray.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,pointerId,clientX:x,clientY:y,pointerType,isPrimary:true,button:0,buttons:1}))}catch{}},40)};stage()}
 function assetCard(a){const b=document.createElement('button');b.type='button';b.className='rist-bottom-asset-card';b.title=a.name||'Asset';const img=document.createElement('img');img.src=a.image;img.alt='';img.loading='lazy';img.decoding='async';img.draggable=false;const strong=document.createElement('strong');strong.textContent=a.name||'Asset';b.append(img,strong);b.addEventListener('pointerdown',e=>{e.preventDefault();startRealDrag(a,e)},true);return b}
 function upload(section){const w=document.createElement('div');w.className='rist-folder-actions';const span=document.createElement('span');span.textContent=[...(TREE[section]?.base||['Shaelvien']),...path].join(' / ');const plus=document.createElement('button');plus.type='button';plus.className='rist-folder-upload';plus.textContent='+';plus.title='Add assets to this folder';plus.setAttribute('aria-label',`Add assets to ${span.textContent}`);plus.onclick=()=>{ensureLegacyLibrary();setTimeout(()=>q('.map-asset-inventory input[type="file"],.tileset-upload input[type="file"]')?.click(),80)};w.append(span,plus);return w}
 function render(section){
  if(!TYPES.has(section))return;
  const r1=row(1),r2=row(2),r3=row(3);if(!r1||!r2||!r3)return;
  if(!loaded&&!loading)load(section);
  const h=document.createElement('div');h.className='rist-asset-header-row';h.append(breadcrumb(section));r1.replaceChildren(h);
  const strip=document.createElement('div');strip.className='rist-bottom-assets-strip';
  if(!loaded){const s=document.createElement('span');s.className='deck-copy';s.textContent=loading?'Loading assets…':'Open this section to load assets.';strip.append(s)}
  else{children(section).forEach(n=>strip.append(folder(section,n)));assets(section).forEach(a=>strip.append(assetCard(a)));if(!strip.children.length){const s=document.createElement('span');s.className='deck-copy';s.textContent='This folder is empty. Use + to add assets.';strip.append(s)}}
  r2.replaceChildren(strip);r3.replaceChildren(upload(section));q('.release-public-region')?.style.setProperty('display','none','important');q('.release-private-region')?.style.setProperty('display','none','important')
 }
 function bind(){const list=q('.rist-section-list');if(!list)return;for(const b of qa('button[data-section]',list)){const section=b.dataset.section;if(!TYPES.has(section)||b.dataset.folderBrowserBound==='1')continue;b.dataset.folderBrowserBound='1';b.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();select(section,b)},true)}}
 function scan(){
  ensureSelectors();bind();const s=current();
  if(TYPES.has(s)&&s!==lastSection){path=[];lastSection=s;render(s)}
  else if(!TYPES.has(s))lastSection=s;
 }
 function scheduleScan(){if(scanFrame)return;scanFrame=requestAnimationFrame(()=>{scanFrame=0;scan()})}
 function start(){
  scan();
  const root=q('#app')||document.body;
  new MutationObserver(scheduleScan).observe(root,{childList:true,subtree:true});
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();