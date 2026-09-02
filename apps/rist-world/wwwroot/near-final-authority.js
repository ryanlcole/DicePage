(()=>{
 'use strict';
 const STORAGE_KEY='rist.custom.asset.sections.v1';
 const BASE_FILTERS=[['cards','Cards'],['tokens','Tokens / Chits'],['minis','Minis'],['rolling-stock','Rolling Stock'],['pawns','Pawns / Meeples'],['tiles','Tiles'],['terrain','Terrain'],['bits','Bits']];
 let activeCustom='';
 let editorFilter='cards';
 let patchQueued=false;
 const qs=(s,r=document)=>r?.querySelector(s);
 const qsa=(s,r=document)=>[...(r?.querySelectorAll(s)||[])];
 const imp=(el,name,value)=>el?.style.setProperty(name,value,'important');
 function loadCustom(){try{return JSON.parse(localStorage.getItem(STORAGE_KEY)||'[]').filter(x=>x&&x.id&&x.name)}catch{return[]}}
 function saveCustom(items){localStorage.setItem(STORAGE_KEY,JSON.stringify(items))}
 function customById(id){return loadCustom().find(x=>x.id===id)}
 function selectorList(){return qs('.rist-section-list')}
 function deckShell(){return qs('.rist.release-world>.release-world-shell')}
 function deckRoot(){return qs('.rist.release-world')}
 function rows(){const shell=deckShell();return [1,2,3].map(i=>qs(`:scope>.rist-deck-row.row${i}`,shell))}
 function setRow(row,node){if(!row)return;row.replaceChildren();if(node)row.appendChild(node);imp(row,'display','flex')}
 function clickFilter(key){
  const label=BASE_FILTERS.find(x=>x[0]===key)?.[1];if(!label)return;
  const buttons=qsa('.release-public-region .asset-type-tabs button');
  const b=buttons.find(x=>(x.textContent||'').trim().toLowerCase()===label.toLowerCase());
  b?.click();
 }
 function rebuildSelector(){
  const list=selectorList();if(!list)return;
  qsa('button[data-section="custom1"]',list).forEach(b=>b.remove());
  qsa('button[data-custom-section]',list).forEach(b=>b.remove());
  let add=qs('button[data-section="add"]',list);
  if(!add){add=document.createElement('button');add.type='button';add.dataset.section='add';add.textContent='+';list.appendChild(add)}
  for(const item of loadCustom()){
   const b=document.createElement('button');b.type='button';b.dataset.customSection=item.id;b.textContent=item.name;
   b.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();activeCustom=item.id;clickFilter(item.filter||'cards');renderCustomSection(item.id)});
   list.insertBefore(b,add);
  }
  if(add.dataset.nearFinalBound!=='1'){
   add.dataset.nearFinalBound='1';
   add.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();activeCustom='editor';editorFilter='cards';renderCustomEditor()},true);
  }
 }
 function assetActions(){
  const wrap=document.createElement('div');wrap.className='rist-deck-actions';
  for(const label of ['Send to map','Remove from map','Discard']){const b=document.createElement('button');b.type='button';b.textContent=label;wrap.appendChild(b)}
  return wrap;
 }
 function customHeader(item){
  const wrap=document.createElement('div');wrap.className='rist-custom-header';
  const input=document.createElement('input');input.type='text';input.maxLength=32;input.value=item.name;input.setAttribute('aria-label','Asset section name');
  const saveName=()=>{const name=input.value.trim();if(!name)return;const all=loadCustom();const found=all.find(x=>x.id===item.id);if(found){found.name=name;saveCustom(all);rebuildSelector();}}
  input.addEventListener('change',saveName);input.addEventListener('keydown',e=>{if(e.key==='Enter'){e.preventDefault();saveName();input.blur();}});
  const filter=document.createElement('button');filter.type='button';filter.textContent=`Filter: ${BASE_FILTERS.find(x=>x[0]===item.filter)?.[1]||'Cards'}`;filter.addEventListener('click',()=>{activeCustom='editor-existing';editorFilter=item.filter||'cards';renderCustomEditor(item)});
  wrap.append(input,filter);return wrap;
 }
 function showAssetRegion(){
  const root=deckRoot();const shell=deckShell();const pub=qs(':scope>.release-public-region',shell);if(!root||!pub)return;
  root.classList.remove('deck-chat','deck-dice','deck-logs');root.classList.add('deck-assets');
  imp(pub,'display','block');imp(pub,'left','15%');imp(pub,'width','85%');imp(pub,'top','70%');imp(pub,'height','30%');imp(pub,'min-height','0');imp(pub,'max-height','none');
 }
 function renderCustomSection(id){
  const item=customById(id);if(!item)return;rebuildSelector();clickFilter(item.filter||'cards');showAssetRegion();
  const [r1,,r3]=rows();setRow(r1,customHeader(item));setRow(r3,assetActions());
  selectorList()?.querySelectorAll('button').forEach(b=>b.classList.toggle('active',b.dataset.customSection===id));
 }
 function filterPicker(selected,onChange){
  const wrap=document.createElement('div');wrap.className='rist-custom-filter-picker';
  for(const [key,label] of BASE_FILTERS){const b=document.createElement('button');b.type='button';b.textContent=label;b.classList.toggle('active',key===selected);b.addEventListener('click',()=>onChange(key));wrap.appendChild(b)}
  return wrap;
 }
 function renderCustomEditor(existing=null){
  const root=deckRoot();const shell=deckShell();if(!root||!shell)return;
  root.classList.remove('deck-chat','deck-dice','deck-assets','deck-logs');root.classList.add('deck-custom-editor');
  const pub=qs(':scope>.release-public-region',shell);if(pub)imp(pub,'display','none');
  const [r1,r2,r3]=rows();
  const head=document.createElement('div');head.className='rist-custom-editor-head';
  const name=document.createElement('input');name.type='text';name.maxLength=32;name.placeholder='Name this asset section';name.value=existing?.name||'';head.appendChild(name);setRow(r1,head);
  const rerenderPicker=()=>setRow(r2,filterPicker(editorFilter,key=>{editorFilter=key;rerenderPicker()}));rerenderPicker();
  const actions=document.createElement('div');actions.className='rist-deck-actions';
  const save=document.createElement('button');save.type='button';save.textContent='Save filter';save.addEventListener('click',()=>{
   const sectionName=name.value.trim();if(!sectionName){name.focus();return}
   const all=loadCustom();
   if(existing){const found=all.find(x=>x.id===existing.id);if(found){found.name=sectionName;found.filter=editorFilter}else all.push({id:existing.id,name:sectionName,filter:editorFilter});activeCustom=existing.id;}
   else{const id=`custom-${Date.now()}`;all.push({id,name:sectionName,filter:editorFilter});activeCustom=id;}
   saveCustom(all);rebuildSelector();renderCustomSection(activeCustom);
  });
  const cancel=document.createElement('button');cancel.type='button';cancel.textContent='Cancel';cancel.addEventListener('click',()=>{activeCustom='';const chat=qs('.rist-section-list button[data-section="chat"]');chat?.click();});
  actions.append(save,cancel);setRow(r3,actions);setTimeout(()=>name.focus(),0);
 }
 function syncDiceTracks(){
  const head=qs('.rist-dice-header-loop');const art=qs('.rist-dice-image-loop');if(!head||!art)return;
  if(head.dataset.syncReady==='1'&&art.dataset.syncReady==='1')return;
  head.classList.remove('rist-dice-synced');art.classList.remove('rist-dice-synced');
  void head.offsetWidth;void art.offsetWidth;
  requestAnimationFrame(()=>{head.classList.add('rist-dice-synced');art.classList.add('rist-dice-synced');head.dataset.syncReady='1';art.dataset.syncReady='1';});
 }
 function normalizeLandscapeAndMap(){
  const root=deckRoot();const shell=deckShell();const mapRegion=qs(':scope>.release-map-region',shell);if(!root||!shell||!mapRegion)return;
  imp(root,'padding','0');imp(shell,'display','block');imp(shell,'padding','0');imp(shell,'margin','0');
  imp(mapRegion,'top','0');imp(mapRegion,'left','0');imp(mapRegion,'right','0');imp(mapRegion,'height','70%');imp(mapRegion,'min-height','70%');imp(mapRegion,'max-height','70%');
  shell.style.setProperty('--rist-deck-top','70%','important');shell.style.setProperty('--rist-deck-h','30%','important');
  const selector=qs(':scope>.rist-section-selector',shell);if(selector){imp(selector,'top','70%');imp(selector,'height','30%');imp(selector,'bottom','0')}
  if(root.classList.contains('deck-assets')){const pub=qs(':scope>.release-public-region',shell);if(pub){imp(pub,'top','70%');imp(pub,'height','30%')}}
 }
 function patch(){rebuildSelector();syncDiceTracks();normalizeLandscapeAndMap();if(activeCustom==='editor')renderCustomEditor();else if(activeCustom&&activeCustom!=='editor-existing')renderCustomSection(activeCustom)}
 function queue(){if(patchQueued)return;patchQueued=true;requestAnimationFrame(()=>{patchQueued=false;patch()})}
 function start(){patch();new MutationObserver(queue).observe(document.body,{childList:true,subtree:true});window.addEventListener('resize',queue,{passive:true});window.addEventListener('orientationchange',()=>setTimeout(queue,120),{passive:true})}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
