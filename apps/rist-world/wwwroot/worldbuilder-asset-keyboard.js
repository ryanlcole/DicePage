(()=>{
 'use strict';
 const VERSION='20260916-asset-keyboard-1';
 if(window.RistWorldBuilderAssetKeyboard?.version===VERSION)return;
 const ASSET_BASE='https://d2d6rnm6fnsp89.cloudfront.net/runtime/worldbuilder/keyboards/v1';
 const STYLE_ID='rist-worldbuilder-asset-keyboard-style';
 const SIZE_KEY='rist.worldbuilder.assetKeyboard.size.v1';
 const FILTER_KEY='rist.worldbuilder.assetKeyboard.filters.v1';
 const PAGE_SIZE=12;
 let dotnet=window.RistWorldBuilderStudioDotNet||null;
 let catalog=[];
 let open=false;
 let spriteOnly=false;
 let page=0;
 let frame=0;
 let observer=null;
 let drag=null;
 let ghost=null;
 let suppressClickUntil=0;
 let filters={type:'all',folder:'all'};
 let size={x:1,y:1};
 const studio=()=>document.querySelector('.worldbuilder-studio');
 const keyboard=()=>studio()?.querySelector('.wb-device-keyboard')||null;
 const keyHost=()=>keyboard()?.querySelector('.wb-device-keys')||null;
 const viewer=()=>studio()?.querySelector('.studio-viewer-canvas')||null;
 const stage=()=>studio()?.querySelector('.world-stage')||viewer();
 const readJson=(key,fallback)=>{try{const raw=localStorage.getItem(key);return raw?JSON.parse(raw):fallback}catch{return fallback}};
 const writeJson=(key,value)=>{try{localStorage.setItem(key,JSON.stringify(value))}catch{}};
 const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
 const value=(obj,a,b,fallback='')=>obj?.[a]??obj?.[b]??fallback;
 const labelOf=button=>(button?.querySelector('strong')?.textContent||button?.getAttribute('aria-label')||'').split('.')[0].trim();

 function ensureStyle(){
  if(document.getElementById(STYLE_ID))return;
  const style=document.createElement('style');style.id=STYLE_ID;style.textContent=`
   .worldbuilder-studio .wb-device-keyboard.wb-asset-keyboard-open .wb-device-keys{overflow:hidden!important;padding:.7%!important;display:block!important;pointer-events:auto!important}
   .wb-asset-keyboard{box-sizing:border-box;width:100%;height:100%;display:grid;grid-template-rows:72% 28%;gap:1.2%;pointer-events:auto}
   .wb-asset-key-grid{min-height:0;display:grid;grid-template-columns:repeat(6,minmax(0,1fr));grid-template-rows:repeat(2,minmax(0,1fr));gap:1.4%}
   .wb-asset-key{box-sizing:border-box;position:relative;min-width:0;min-height:0;padding:0;border:3px solid rgba(190,143,56,.9);border-radius:12%;overflow:hidden;background:#071018 url('${ASSET_BASE}/common/blank.png') center/100% 100% no-repeat;box-shadow:inset 0 0 0 2px rgba(40,127,177,.28),0 0 8px rgba(0,0,0,.65);touch-action:none;-webkit-tap-highlight-color:transparent}
   .wb-asset-key:focus-visible{outline:3px solid #67c8ff;outline-offset:-3px}.wb-asset-key.wb-touch-active{filter:brightness(1.25)}
   .wb-asset-key img{position:absolute;inset:8%;width:84%;height:84%;object-fit:contain;pointer-events:none;user-select:none;-webkit-user-drag:none}
   .wb-asset-key .wb-asset-name{position:absolute;left:5%;right:5%;bottom:4%;z-index:2;padding:2px 3px;border-radius:5px;background:rgba(2,7,11,.76);color:#ffeab8;font:800 7px/1 system-ui;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;pointer-events:none}
   .wb-asset-keyboard-controls{min-height:0;display:grid;grid-template-columns:18% 24% 10% 10% 12% 24%;gap:1%;align-items:stretch}
   .wb-asset-filter,.wb-asset-page,.wb-asset-close{box-sizing:border-box;min-width:0;border:2px solid #8c6b2d;border-radius:10px;background:#0a151d;color:#f3deb0;font:800 8px/1 system-ui;padding:2%;touch-action:manipulation;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
   .wb-asset-filter small,.wb-asset-page small{display:block;margin-top:3px;color:#86b7d4;font-size:6px;text-transform:uppercase;letter-spacing:.08em}
   .wb-asset-size-pad{box-sizing:border-box;position:relative;min-width:0;border:3px solid #ad8438;border-radius:10px;background:linear-gradient(90deg,rgba(54,145,198,.12) 1px,transparent 1px),linear-gradient(rgba(54,145,198,.12) 1px,transparent 1px),#071018;background-size:10% 10%;touch-action:none;overflow:hidden}
   .wb-asset-size-pad::before{content:attr(data-readout);position:absolute;inset:4px auto auto 6px;color:#ffe4a2;font:900 8px/1 system-ui;letter-spacing:.08em;z-index:2}
   .wb-asset-size-thumb{position:absolute;width:18%;aspect-ratio:1;border:2px solid #66c9ff;border-radius:50%;background:#0b4164;box-shadow:0 0 8px #45bfff;transform:translate(-50%,-50%);pointer-events:none}
   .wb-asset-drag-ghost{position:fixed;z-index:2147483400;pointer-events:none;width:84px;height:70px;border:3px solid #d6a84b;border-radius:10px;background:#071018;box-shadow:0 12px 30px #000c;transform:translate(-50%,-50%);overflow:hidden}.wb-asset-drag-ghost img{width:100%;height:100%;object-fit:contain}
   .worldbuilder-studio .world-stage .tile-cell[data-asset-keyboard-rect='1']{transition:none!important}
   @media(max-width:430px){.wb-asset-key-grid{gap:1%}.wb-asset-keyboard-controls{grid-template-columns:18% 22% 10% 10% 12% 26%}.wb-asset-key{border-width:3px}.wb-asset-key .wb-asset-name{font-size:6px}}
  `;document.head.appendChild(style)
 }

 function restoreState(){
  const storedSize=readJson(SIZE_KEY,{x:1,y:1});size={x:clamp(Number(storedSize.x)||1,1,10),y:clamp(Number(storedSize.y)||1,1,10)};
  filters={...filters,...readJson(FILTER_KEY,{})};
 }
 function saveState(){writeJson(SIZE_KEY,size);writeJson(FILTER_KEY,filters)}
 function normalize(raw){return{id:String(value(raw,'id','Id')),name:String(value(raw,'name','Name','Asset')),image:String(value(raw,'image','Image')),layer:String(value(raw,'layer','Layer')),directory:String(value(raw,'directory','Directory')),folder:String(value(raw,'folder','Folder')),kind:String(value(raw,'assetKind','AssetKind','tile')).toLowerCase(),author:String(value(raw,'author','Author')),defaultFootprint:Math.max(1,Number(value(raw,'defaultFootprint','DefaultFootprint',1))||1)}}
 async function ensureCatalog(){
  dotnet=window.RistWorldBuilderStudioDotNet||dotnet;
  if(!dotnet)return false;
  if(catalog.length)return true;
  try{catalog=(await dotnet.invokeMethodAsync('GetAssetKeyboardCatalog')||[]).map(normalize).filter(x=>x.id&&x.image);return true}catch{return false}
 }
 function typeOf(asset){const text=`${asset.kind} ${asset.layer} ${asset.directory} ${asset.folder} ${asset.name}`.toLowerCase();if(asset.kind==='sprite'||text.includes('sprite')||text.includes('animated'))return'sprite';if(text.includes('terrain')||text.includes('ocean')||text.includes('coast')||text.includes('mountain')||text.includes('forest'))return'terrain';return'tile'}
 function baseFiltered(){return catalog.filter(asset=>{const type=typeOf(asset);if(spriteOnly&&type!=='sprite')return false;if(filters.type!=='all'&&type!==filters.type)return false;return true})}
 function folders(){return['all',...new Set(baseFiltered().map(a=>a.folder).filter(Boolean))]}
 function filtered(){let list=baseFiltered();if(filters.folder!=='all')list=list.filter(a=>a.folder===filters.folder);return list}
 function pageCount(){return Math.max(1,Math.ceil(filtered().length/PAGE_SIZE))}
 function visible(){page=clamp(page,0,pageCount()-1);return filtered().slice(page*PAGE_SIZE,page*PAGE_SIZE+PAGE_SIZE)}
 function nextType(){const values=spriteOnly?['sprite']:['all','tile','terrain','sprite'];const i=Math.max(0,values.indexOf(filters.type));filters.type=values[(i+1)%values.length];filters.folder='all';page=0;saveState();render()}
 function nextFolder(){const values=folders();const i=Math.max(0,values.indexOf(filters.folder));filters.folder=values[(i+1)%values.length];page=0;saveState();render()}
 function worldPoint(clientX,clientY){const target=stage();if(!target)return null;const r=target.getBoundingClientRect();if(r.width<1||r.height<1)return null;const x=(clientX-r.left)/r.width,y=(clientY-r.top)/r.height;return x<0||x>1||y<0||y>1?null:[x,y]}
 async function place(asset,x=.5,y=.5){dotnet=window.RistWorldBuilderStudioDotNet||dotnet;if(!dotnet)return false;try{const index=await dotnet.invokeMethodAsync('PlaceAssetKeyboardItemFromJs',asset.id,x,y,size.x,size.y);if(Number(index)<0)return false;await refreshRectangles();window.RistWorldBuilderKeyboardAuthority?.refresh?.();return true}catch{return false}}
 function removeGhost(){ghost?.remove();ghost=null}
 function createGhost(asset,x,y){removeGhost();ghost=document.createElement('div');ghost.className='wb-asset-drag-ghost';const img=document.createElement('img');img.src=asset.image;img.alt='';ghost.appendChild(img);ghost.style.left=`${x}px`;ghost.style.top=`${y}px`;document.body.appendChild(ghost)}

 function assetButton(asset){
  const b=document.createElement('button');b.type='button';b.className='wb-asset-key';b.dataset.assetId=asset.id;b.setAttribute('aria-label',`${asset.name}. ${asset.folder||asset.directory||asset.kind}. Tap to place in viewer center; drag to place at a specific grid location.`);
  const img=document.createElement('img');img.src=asset.image;img.alt='';img.draggable=false;img.decoding='async';const name=document.createElement('span');name.className='wb-asset-name';name.textContent=asset.name;b.append(img,name);return b
 }
 function control(label,small,action,cls='wb-asset-filter'){const b=document.createElement('button');b.type='button';b.className=cls;b.innerHTML=`<strong>${label}</strong>${small?`<small>${small}</small>`:''}`;b.addEventListener('click',action);return b}
 function updateSizePad(pad){pad.dataset.readout=`SIZE ${size.x}×${size.y}`;const thumb=pad.querySelector('.wb-asset-size-thumb');if(thumb){thumb.style.left=`${((size.x-.5)/10)*100}%`;thumb.style.top=`${((size.y-.5)/10)*100}%`}pad.setAttribute('aria-label',`Asset footprint ${size.x} by ${size.y} grid cells. Drag horizontally for width and vertically for height. Arrow keys also adjust size.`)}
 function setSizeFromPointer(pad,x,y){const r=pad.getBoundingClientRect();if(r.width<1||r.height<1)return;size.x=clamp(Math.floor((x-r.left)/r.width*10)+1,1,10);size.y=clamp(Math.floor((y-r.top)/r.height*10)+1,1,10);saveState();updateSizePad(pad)}
 function sizePad(){const pad=document.createElement('button');pad.type='button';pad.className='wb-asset-size-pad';const thumb=document.createElement('span');thumb.className='wb-asset-size-thumb';pad.appendChild(thumb);pad.addEventListener('keydown',e=>{let changed=true;if(e.key==='ArrowLeft')size.x=clamp(size.x-1,1,10);else if(e.key==='ArrowRight')size.x=clamp(size.x+1,1,10);else if(e.key==='ArrowUp')size.y=clamp(size.y+1,1,10);else if(e.key==='ArrowDown')size.y=clamp(size.y-1,1,10);else changed=false;if(changed){e.preventDefault();saveState();updateSizePad(pad)}});let id=null;pad.addEventListener('pointerdown',e=>{id=e.pointerId;pad.setPointerCapture?.(id);setSizeFromPointer(pad,e.clientX,e.clientY);e.preventDefault()});pad.addEventListener('pointermove',e=>{if(id!==e.pointerId)return;setSizeFromPointer(pad,e.clientX,e.clientY);e.preventDefault()});const done=e=>{if(id!==e.pointerId)return;id=null;pad.releasePointerCapture?.(e.pointerId);setSizeFromPointer(pad,e.clientX,e.clientY)};pad.addEventListener('pointerup',done);pad.addEventListener('pointercancel',()=>{id=null});updateSizePad(pad);return pad}

 function render(){
  if(!open)return;ensureStyle();const host=keyHost(),kb=keyboard();if(!host||!kb)return;kb.classList.add('wb-asset-keyboard-open');kb.dataset.assetKeyboard='open';const modeName=kb.querySelector('.wb-device-mode-name');if(modeName)modeName.textContent='Asset keyboard';host.innerHTML='';const root=document.createElement('section');root.className='wb-asset-keyboard';root.setAttribute('aria-label','Asset keyboard');const grid=document.createElement('div');grid.className='wb-asset-key-grid';for(const asset of visible())grid.appendChild(assetButton(asset));root.appendChild(grid);const controls=document.createElement('div');controls.className='wb-asset-keyboard-controls';controls.append(control(filters.type.toUpperCase(),'Type',nextType),control(filters.folder==='all'?'ALL FOLDERS':filters.folder,'Folder',nextFolder),control('‹','Previous',()=>{page=(page-1+pageCount())%pageCount();render()},'wb-asset-page'),control('›','Next',()=>{page=(page+1)%pageCount();render()},'wb-asset-page'),control(`${page+1}/${pageCount()}`,'Page',()=>{},'wb-asset-page'),sizePad());root.appendChild(controls);host.appendChild(root);requestAnimationFrame(()=>refreshRectangles())
 }
 async function openKeyboard(options={}){spriteOnly=!!options.sprite;filters.type=spriteOnly?'sprite':(filters.type||'all');page=0;open=true;if(!(await ensureCatalog())){open=false;return false}render();return true}
 function closeKeyboard(){if(!open)return;open=false;const kb=keyboard();kb?.classList.remove('wb-asset-keyboard-open');if(kb)delete kb.dataset.assetKeyboard;window.RistWorldBuilderDeviceShell?.refresh?.();window.RistWorldBuilderKeyboardAuthority?.refresh?.()}

 async function refreshRectangles(){
  dotnet=window.RistWorldBuilderStudioDotNet||dotnet;if(!dotnet)return;
  let footprints=[];try{footprints=await dotnet.invokeMethodAsync('GetAssetKeyboardFootprints')||[]}catch{return}
  const tiles=[...(studio()?.querySelectorAll('.world-stage .tile-cell')||[])];
  for(const raw of footprints){const index=Number(value(raw,'index','Index',-1)),w=Number(value(raw,'widthCells','WidthCells',1)),h=Number(value(raw,'heightCells','HeightCells',1));const tile=tiles[index];if(!tile)continue;tile.dataset.assetKeyboardRect='1';tile.style.setProperty('width',`${clamp(w,1,30)/30*100}%`,'important');tile.style.setProperty('height',`${clamp(h,1,30)/30*100}%`,'important')}
 }
 function scheduleRectangles(){if(frame)return;frame=requestAnimationFrame(()=>{frame=0;void refreshRectangles()})}

 function beginAssetPointer(e,button){const asset=catalog.find(x=>x.id===button.dataset.assetId);if(!asset)return;e.preventDefault();e.stopPropagation();button.setPointerCapture?.(e.pointerId);button.classList.add('wb-touch-active');drag={id:e.pointerId,button,asset,startX:e.clientX,startY:e.clientY,moved:false}}
 function moveAssetPointer(e){if(!drag||drag.id!==e.pointerId)return;const distance=Math.abs(e.clientX-drag.startX)+Math.abs(e.clientY-drag.startY);if(!drag.moved&&distance>8){drag.moved=true;createGhost(drag.asset,e.clientX,e.clientY)}if(drag.moved&&ghost){ghost.style.left=`${e.clientX}px`;ghost.style.top=`${e.clientY}px`}e.preventDefault();e.stopPropagation()}
 function finishAssetPointer(e,cancel=false){if(!drag||drag.id!==e.pointerId)return;const current=drag;drag=null;current.button.classList.remove('wb-touch-active');current.button.releasePointerCapture?.(e.pointerId);removeGhost();e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();suppressClickUntil=Date.now()+500;if(cancel)return;if(current.moved){const p=worldPoint(e.clientX,e.clientY);if(p)void place(current.asset,p[0],p[1])}else void place(current.asset,.5,.5)}

 let keyTouch=null;
 function keyboardPointerDown(e){const kb=keyboard();if(!kb||!kb.contains(e.target))return;const asset=e.target.closest?.('.wb-asset-key');if(asset){beginAssetPointer(e,asset);return}if(e.pointerType!=='touch'&&e.pointerType!=='pen')return;const button=e.target.closest?.('button');if(!button||button.disabled||button.classList.contains('wb-asset-size-pad'))return;keyTouch={id:e.pointerId,button,startX:e.clientX,startY:e.clientY,moved:false};button.classList.add('wb-touch-active')}
 function keyboardPointerMove(e){if(drag){moveAssetPointer(e);return}if(!keyTouch||keyTouch.id!==e.pointerId)return;if(Math.abs(e.clientX-keyTouch.startX)+Math.abs(e.clientY-keyTouch.startY)>8)keyTouch.moved=true}
 function keyboardPointerUp(e){if(drag){finishAssetPointer(e,false);return}if(!keyTouch||keyTouch.id!==e.pointerId)return;const state=keyTouch;keyTouch=null;state.button.classList.remove('wb-touch-active');if(state.moved)return;e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();suppressClickUntil=Date.now()+450;const label=labelOf(state.button);if(label==='Library'||label==='Sprite Library'){void openKeyboard({sprite:label==='Sprite Library'});return}state.button.click()}
 function keyboardPointerCancel(e){if(drag){finishAssetPointer(e,true);return}if(keyTouch?.id===e.pointerId){keyTouch.button.classList.remove('wb-touch-active');keyTouch=null}}
 function clickCapture(e){
  if(Date.now()<suppressClickUntil&&e.isTrusted){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();return}
  const button=e.target?.closest?.('.wb-device-keyboard button');if(!button)return;const label=labelOf(button);
  if(label==='Library'||label==='Sprite Library'){e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();void openKeyboard({sprite:label==='Sprite Library'});return}
  if(button.classList.contains('wb-device-mode')&&open)setTimeout(closeKeyboard,0)
 }

 function start(){
  ensureStyle();restoreState();dotnet=window.RistWorldBuilderStudioDotNet||dotnet;
  window.addEventListener('rist:worldbuilder-dotnet-ready',e=>{dotnet=e.detail?.dotnet||window.RistWorldBuilderStudioDotNet||dotnet;void ensureCatalog();scheduleRectangles()});
  document.addEventListener('pointerdown',keyboardPointerDown,{capture:true,passive:false});document.addEventListener('pointermove',keyboardPointerMove,{capture:true,passive:false});document.addEventListener('pointerup',keyboardPointerUp,{capture:true,passive:false});document.addEventListener('pointercancel',keyboardPointerCancel,{capture:true,passive:false});document.addEventListener('click',clickCapture,true);
  observer=new MutationObserver(records=>{if(records.some(r=>r.type==='childList')){if(open)setTimeout(render,0);scheduleRectangles()}});observer.observe(document.getElementById('app')||document.body,{childList:true,subtree:true});
  window.addEventListener('rist:viewer-state',scheduleRectangles);window.addEventListener('pageshow',scheduleRectangles,{passive:true});window.addEventListener('resize',scheduleRectangles,{passive:true});
  void ensureCatalog();scheduleRectangles()
 }
 const api={version:VERSION,open:openKeyboard,close:closeKeyboard,refresh:()=>{if(open)render();scheduleRectangles()},state:()=>({open,spriteOnly,page,pageCount:pageCount(),filters:{...filters},size:{...size},catalog:catalog.length})};window.RistWorldBuilderAssetKeyboard=api;
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
