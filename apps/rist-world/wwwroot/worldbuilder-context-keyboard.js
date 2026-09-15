const STYLE_ID='rist-worldbuilder-viewer-keyboard-css';
const MODE_KEY='rist.worldbuilder.keyboard.mode.v2';
const COLLAPSE_KEY='rist.worldbuilder.keyboard.collapsed.v1';
const ACCESS_LARGE_KEY='rist.worldbuilder.access.largeTargets.v1';
const ACCESS_CONTRAST_KEY='rist.worldbuilder.access.highContrast.v1';
const ACCESS_MOTION_KEY='rist.worldbuilder.access.reducedMotion.v1';
const MODES=['pixels','tiles','sprites','target','layers','tiers','parallax','access','file'];
let activeRoot=null,keyboard=null,statusNode=null,modeRow=null,commandRow=null,rootObserver=null,refreshFrame=0,lastSelectedCount=0;

function ensureStyle(){
 if(document.getElementById(STYLE_ID))return;
 const link=document.createElement('link');
 link.id=STYLE_ID;link.rel='stylesheet';link.href='./css/worldbuilder-viewer-keyboard.css?v=20260915-meaning-keyboards-2';
 document.head.appendChild(link);
}
function read(key,fallback){try{return localStorage.getItem(key)??fallback}catch{return fallback}}
function write(key,value){try{localStorage.setItem(key,String(value))}catch{}}
function studio(){return document.querySelector('.worldbuilder-studio')}
function railButtons(root=activeRoot){return root?[...root.querySelectorAll('.studio-command-rail button')]:[]}
function findStrong(title,root=activeRoot){return railButtons(root).find(b=>(b.querySelector('strong')?.textContent||'').trim()===title)||null}
function readSmall(title,root=activeRoot){return (findStrong(title,root)?.querySelector('small')?.textContent||'').trim()}
function clickStrong(title,root=activeRoot){const b=findStrong(title,root);if(!b||b.disabled)return false;b.click();scheduleRefresh();return true}
function commandButton(name,root=activeRoot){return root?.querySelector(`.studio-command-rail [data-wb-command="${name}"]`)||null}
function runtimeButton(name,root=activeRoot){return root?.querySelector(`.studio-command-rail [data-wb-runtime="${name}"]`)||null}
function clickCommand(name,root=activeRoot){const b=commandButton(name,root);if(!b||b.disabled)return false;b.click();scheduleRefresh();return true}
function clickRuntime(name,root=activeRoot){const b=runtimeButton(name,root);if(!b||b.disabled)return false;b.click();scheduleRefresh();return true}
function viewerState(){try{return window.ristViewerAuthority?.get?.()||{}}catch{return{}}}
function playbackState(){try{return window.ristSpritePlayback?.state?.()||{}}catch{return{}}}
function parallaxState(){try{return{enabled:window.ristParallax?.isEnabled?.()!==false,active:window.ristParallax?.isWorldBuilderActive?.()===true,depths:window.ristParallax?.getTierDepths?.()||{}}}catch{return{enabled:true,active:false,depths:{}}}}
function currentMode(){const mode=activeRoot?.dataset.wbKeyboardMode||read(MODE_KEY,'pixels');return MODES.includes(mode)?mode:'pixels'}
function tileButton(){return activeRoot?.querySelector('.studio-command-rail .tile-size-button')||null}
function tileFootprint(){const b=tileButton();const fromData=Number(b?.dataset?.footprint);if(Number.isFinite(fromData)&&fromData>0)return fromData;const text=(b?.querySelector('strong')?.textContent||'1').replace(/[^0-9.]/g,'');return Number(text)||1}
function tileSize(){return `${tileFootprint()}²`}
function selectionCount(){const text=(commandButton('remove')?.querySelector('small')?.textContent||'0').trim();const n=parseInt(text,10);return Number.isFinite(n)?n:0}
function lockLabel(){const b=findStrong('Unlock')||findStrong('Lock')||findStrong('Z-Lock');return (b?.querySelector('strong')?.textContent||'Lock').trim()}
function toggleLock(){if(clickStrong('Unlock')||clickStrong('Lock')||clickStrong('Z-Lock'))return;try{window.ristViewerAuthority?.toggleLocked?.({source:'keyboard'})}catch{}scheduleRefresh()}
function toggleGrid(){try{window.ristViewerAuthority?.toggleGrid?.({source:'keyboard'})}catch{}scheduleRefresh()}
function zoomBy(factor){try{window.ristViewerAuthority?.zoomBy?.(factor,{mode:'manual',source:'keyboard'})}catch{}scheduleRefresh()}
function autoZoom(){try{window.ristViewerAuthority?.resetAutoZoom?.({source:'keyboard'})}catch{}scheduleRefresh()}
function centerView(){try{window.ristViewerAuthority?.setPosition?.(0,0,true,'keyboard-center')}catch{}scheduleRefresh()}
function toggleQuick(){if(!activeRoot)return;activeRoot.dataset.wbQuickHidden=activeRoot.dataset.wbQuickHidden==='true'?'false':'true';write('rist.worldbuilder.keyboard.quickHidden.v1',activeRoot.dataset.wbQuickHidden);scheduleRefresh()}
function openHome(){activeRoot?.querySelector('.studio-home')?.click()}

function panelFor(kind){
 const needle=kind==='layer'?'Layer ':'Tier ';
 return [...(activeRoot?.querySelectorAll('.studio-mini-panel')||[])].find(p=>p.textContent?.includes(needle))||null;
}
function ensurePanel(kind){
 const panel=panelFor(kind);if(panel)return panel;
 clickStrong(kind==='layer'?'Layers':'Tiers');
 return null;
}
function stepDepth(kind,direction){
 if(!activeRoot)return;
 ensurePanel(kind);
 let attempts=0;
 const run=()=>{
  const panel=panelFor(kind);
  const text=kind==='layer'?(direction<0?'Layer Down':'Layer Up'):(direction<0?'Tier Down':'Tier Up');
  const button=[...(panel?.querySelectorAll('button')||[])].find(b=>b.textContent?.trim()===text);
  if(button){if(!button.disabled)button.click();scheduleRefresh();return}
  if(attempts++<4)setTimeout(run,20);
 };
 setTimeout(run,0);
}
function toggleParallax(){
 if(clickRuntime('parallax'))return;
 try{const enabled=window.ristParallax?.isEnabled?.()!==false;window.ristParallax?.setEnabled?.(!enabled)}catch{}
 scheduleRefresh();
}
function togglePlayback(){
 try{const s=playbackState().state||'playing';if(s==='playing')window.ristSpritePlayback?.pause?.();else window.ristSpritePlayback?.play?.()}catch{}
 scheduleRefresh();
}
function stopPlayback(){try{window.ristSpritePlayback?.stop?.()}catch{}scheduleRefresh()}
function cycleFps(){if(!clickRuntime('fps')){const values=[6,12,24,30,60],state=playbackState(),i=values.indexOf(Number(state.fps)||12),next=values[(i+1)%values.length];try{localStorage.setItem('rist.sprites.fps.v1',String(next));window.dispatchEvent(new CustomEvent('rist-sprite-playback',{detail:{state:state.state||'playing',fps:next}}))}catch{}}scheduleRefresh()}
function requestMotion(){try{window.ristMotionPermission?.request?.()}catch{}scheduleRefresh()}
function openLibrary(sprite=false){if(sprite)clickStrong('Sprite Library');else clickStrong('Library');scheduleRefresh()}
function cycleTileSize(){const b=tileButton();if(b&&!b.disabled)b.click();scheduleRefresh()}
function setPixelFootprint(){
 const b=tileButton();if(!b||b.disabled)return;
 let tries=0;
 const step=()=>{
  if(tileFootprint()===1||tries++>7){scheduleRefresh();return}
  b.click();setTimeout(step,24);
 };
 step();
}
function save(){clickStrong('Save')}
function load(){clickStrong('Load')}
function publish(){clickStrong('Publish')}

function currentTierIndex(){const match=(readSmall('Tiers')||'').match(/-?\d+/);return match?Number(match[0]):0}
function currentTierDepth(){try{return Number(window.ristParallax?.depthForTier?.(currentTierIndex()))||0}catch{return 0}}
function adjustParallaxDepth(delta){
 const tier=currentTierIndex(),next=Math.max(0,Math.min(2,currentTierDepth()+delta));
 try{window.ristParallax?.setTierDepth?.(tier,Number(next.toFixed(2)))}catch{}
 scheduleRefresh();
}

function accessState(){return{large:read(ACCESS_LARGE_KEY,'false')==='true',contrast:read(ACCESS_CONTRAST_KEY,'false')==='true',reduced:read(ACCESS_MOTION_KEY,'false')==='true'}}
function applyAccessState(){
 const state=accessState();if(!activeRoot)return state;
 activeRoot.classList.toggle('wb-access-large',state.large);
 activeRoot.classList.toggle('wb-access-contrast',state.contrast);
 activeRoot.classList.toggle('wb-access-reduced',state.reduced);
 return state;
}
function toggleLargeTargets(){const s=accessState();write(ACCESS_LARGE_KEY,!s.large);applyAccessState();scheduleRefresh()}
function toggleHighContrast(){const s=accessState();write(ACCESS_CONTRAST_KEY,!s.contrast);applyAccessState();scheduleRefresh()}
function toggleReducedMotion(){
 const s=accessState(),next=!s.reduced;write(ACCESS_MOTION_KEY,next);applyAccessState();
 if(next){try{window.ristSpritePlayback?.pause?.()}catch{}try{window.ristParallax?.setEnabled?.(false)}catch{}}
 scheduleRefresh();
}

function descriptor(label,sub,action,{active=false,disabled=false,danger=false}={}){return{label,sub,action,active,disabled,danger}}
function commandsFor(mode){
 const view=viewerState(),play=playbackState(),par=parallaxState(),selected=selectionCount(),locked=!!view.locked,access=accessState(),depth=currentTierDepth();
 switch(mode){
  case 'pixels':return[
   descriptor('1²','Pixel Footprint',setPixelFootprint,{active:tileFootprint()===1}),descriptor('Grid',view.grid===false?'Off':'On',toggleGrid,{active:view.grid!==false}),
   descriptor('Zoom −',`${Math.round(view.visibleCells||12)} Cells`,()=>zoomBy(.9)),descriptor('Zoom +',`${Math.round(view.visibleCells||12)} Cells`,()=>zoomBy(1.1)),
   descriptor('Auto View','Fit Viewer',autoZoom),descriptor('Center','X 0 · Y 0',centerView),descriptor('Undo','Last Action',()=>clickCommand('undo'),{disabled:!!commandButton('undo')?.disabled})
  ];
  case 'tiles':return[
   descriptor('Library','Tile Assets',()=>openLibrary(false)),descriptor(tileSize(),'Tile Size',cycleTileSize),descriptor('Quick','Asset Strip',toggleQuick,{active:activeRoot?.dataset.wbQuickHidden!=='true'}),
   descriptor('Undo','Last Action',()=>clickCommand('undo'),{disabled:!!commandButton('undo')?.disabled}),descriptor('Target',`${selected} Selected`,()=>setMode('target'),{disabled:selected<1}),descriptor('Grid',view.grid===false?'Off':'On',toggleGrid,{active:view.grid!==false})
  ];
  case 'sprites':return[
   descriptor('Sprite Library','Animated Assets',()=>openLibrary(true)),descriptor('Play / Pause',play.state||'playing',togglePlayback,{active:play.state==='playing'}),descriptor('Stop','Sprites',stopPlayback),
   descriptor('FPS',String(play.fps||12),cycleFps),descriptor('Parallax',par.active?'On':'Off',toggleParallax,{active:par.active}),descriptor(tileSize(),'Tile Size',cycleTileSize),descriptor('Target',`${selected} Selected`,()=>setMode('target'),{disabled:selected<1})
  ];
  case 'target':return[
   descriptor('Rotate','90°',()=>clickCommand('rotate'),{disabled:selected<1}),descriptor('Resize',`To ${tileSize()}`,()=>clickCommand('resize'),{disabled:selected<1}),
   descriptor('Tile Size',tileSize(),cycleTileSize,{disabled:selected<1}),descriptor('Layer','Depth Tools',()=>setMode('layers'),{disabled:selected<1}),descriptor('Tier','Tier Tools',()=>setMode('tiers'),{disabled:selected<1}),
   descriptor('Undo','Last Action',()=>clickCommand('undo'),{disabled:!!commandButton('undo')?.disabled}),descriptor('Remove',`${selected} Selected`,()=>clickCommand('remove'),{disabled:selected<1,danger:true})
  ];
  case 'layers':return[
   descriptor('Layer −',readSmall('Layers')||'Depth',()=>stepDepth('layer',-1),{disabled:locked}),descriptor('Layer +',readSmall('Layers')||'Depth',()=>stepDepth('layer',1),{disabled:locked}),
   descriptor(lockLabel(),locked?'Viewer Locked':'Viewer Unlocked',toggleLock,{active:locked}),descriptor('Tier Tools',readSmall('Tiers')||'Tier',()=>setMode('tiers')),
   descriptor('Grid',view.grid===false?'Off':'On',toggleGrid,{active:view.grid!==false}),descriptor('Center','X 0 · Y 0',centerView),descriptor('Auto View',`${Math.round(view.visibleCells||12)} Cells`,autoZoom)
  ];
  case 'tiers':return[
   descriptor('Tier −',readSmall('Tiers')||'Depth',()=>stepDepth('tier',-1),{disabled:locked}),descriptor('Tier +',readSmall('Tiers')||'Depth',()=>stepDepth('tier',1),{disabled:locked}),
   descriptor(lockLabel(),locked?'Viewer Locked':'Viewer Unlocked',toggleLock,{active:locked}),descriptor('Layer −',readSmall('Layers')||'Depth',()=>stepDepth('layer',-1),{disabled:locked}),descriptor('Layer +',readSmall('Layers')||'Depth',()=>stepDepth('layer',1),{disabled:locked}),descriptor('Parallax','Tier Depth',()=>setMode('parallax'))
  ];
  case 'parallax':return[
   descriptor('Parallax',par.active?'On':'Off',toggleParallax,{active:par.active}),descriptor('Depth −',depth.toFixed(2),()=>adjustParallaxDepth(-.1)),descriptor('Depth +',depth.toFixed(2),()=>adjustParallaxDepth(.1)),
   descriptor('Play / Pause',play.state||'playing',togglePlayback,{active:play.state==='playing'}),descriptor('FPS',String(play.fps||12),cycleFps),descriptor('Motion','Device Tilt',requestMotion),descriptor('Reduce Motion',access.reduced?'On':'Off',toggleReducedMotion,{active:access.reduced})
  ];
  case 'access':return[
   descriptor('Large Keys',access.large?'On':'Off',toggleLargeTargets,{active:access.large}),descriptor('High Contrast',access.contrast?'On':'Off',toggleHighContrast,{active:access.contrast}),descriptor('Reduce Motion',access.reduced?'On':'Off',toggleReducedMotion,{active:access.reduced}),
   descriptor('Grid',view.grid===false?'Off':'On',toggleGrid,{active:view.grid!==false}),descriptor('Center','Viewer',centerView),descriptor('Auto View','Fit Device',autoZoom),descriptor(lockLabel(),locked?'Viewer Locked':'Viewer Unlocked',toggleLock,{active:locked})
  ];
  case 'file':return[
   descriptor('Save','World',save),descriptor('Load','Saved / Published',load),descriptor('Publish','To Region',publish),descriptor('Menu','Shaelvien',openHome),descriptor('Grid',view.grid===false?'Off':'On',toggleGrid,{active:view.grid!==false}),descriptor(lockLabel(),locked?'Viewer Locked':'Viewer Unlocked',toggleLock,{active:locked})
  ];
  default:return[];
 }
}
function modeLabel(mode){return({pixels:'Pixels',tiles:'Tiles',sprites:'Sprites',target:'Target',layers:'Layers',tiers:'Tiers',parallax:'Parallax',access:'Access',file:'File'})[mode]||mode}
function setMode(mode){
 if(!activeRoot||!MODES.includes(mode))return;
 activeRoot.dataset.wbKeyboardMode=mode;write(MODE_KEY,mode);
 [...(modeRow?.querySelectorAll('button')||[])].forEach(b=>{const on=b.dataset.mode===mode;b.classList.toggle('active',on);b.setAttribute('aria-pressed',on?'true':'false');b.setAttribute('aria-selected',on?'true':'false')});
 renderCommands();updateStatus();
}
function renderModes(){
 if(!modeRow)return;modeRow.replaceChildren();
 for(const mode of MODES){const b=document.createElement('button');b.type='button';b.className='wb-keyboard-mode';b.dataset.mode=mode;b.textContent=modeLabel(mode);b.setAttribute('role','tab');b.setAttribute('aria-label',`${modeLabel(mode)} keyboard`);b.addEventListener('click',()=>setMode(mode));modeRow.appendChild(b)}
}
function renderCommands(){
 if(!commandRow||!activeRoot)return;const mode=currentMode();commandRow.replaceChildren();
 for(const item of commandsFor(mode)){
  const b=document.createElement('button');b.type='button';b.className='wb-keyboard-command';if(item.active)b.classList.add('active');if(item.danger)b.classList.add('danger');b.disabled=!!item.disabled;b.innerHTML='<strong></strong><small></small>';b.querySelector('strong').textContent=item.label;b.querySelector('small').textContent=item.sub||'';b.setAttribute('aria-label',item.sub?`${item.label}: ${item.sub}`:item.label);b.addEventListener('click',()=>{item.action?.();setTimeout(()=>{renderCommands();updateStatus()},30)});commandRow.appendChild(b)
 }
}
function updateStatus(){
 if(!statusNode||!activeRoot)return;const view=viewerState(),layer=readSmall('Layers'),tier=readSmall('Tiers'),selected=selectionCount(),parts=[modeLabel(currentMode()).toUpperCase(),`${Math.round(view.visibleCells||12)} CELLS`];if(layer)parts.push(layer);if(tier)parts.push(tier);if(selected>0)parts.push(`${selected} TARGET${selected===1?'':'S'}`);statusNode.textContent=parts.join(' · ')
}
function refreshNow(){
 if(!activeRoot?.isConnected)return;
 const selected=selectionCount();
 if(selected>0&&lastSelectedCount===0&&currentMode()!=='target'){
  lastSelectedCount=selected;setMode('target');return;
 }
 lastSelectedCount=selected;renderCommands();updateStatus();
}
function scheduleRefresh(){if(refreshFrame)return;refreshFrame=requestAnimationFrame(()=>{refreshFrame=0;refreshNow()})}
function closeTopOverlay(){
 const preview=activeRoot?.querySelector('.asset-preview-close');if(preview){preview.click();return true}
 const rail=activeRoot?.querySelector('.world-asset-rail .rail-back');if(rail){rail.click();return true}
 return false;
}
function build(root){
 activeRoot=root;ensureStyle();root.dataset.wbQuickHidden=read('rist.worldbuilder.keyboard.quickHidden.v1','false');
 const collapsed=read(COLLAPSE_KEY,'false')==='true';root.classList.toggle('wb-keyboard-collapsed',collapsed);applyAccessState();
 keyboard=document.createElement('section');keyboard.className='wb-context-keyboard';keyboard.setAttribute('role','toolbar');keyboard.setAttribute('aria-label','World Builder contextual keyboard');
 const head=document.createElement('div');head.className='wb-keyboard-head';
 const badge=document.createElement('span');badge.className='wb-keyboard-badge';badge.textContent='VIEWER';
 statusNode=document.createElement('span');statusNode.className='wb-keyboard-status';statusNode.setAttribute('role','status');statusNode.setAttribute('aria-live','polite');statusNode.setAttribute('aria-atomic','true');
 const collapse=document.createElement('button');collapse.type='button';collapse.className='wb-keyboard-collapse';collapse.textContent=collapsed?'⌃':'⌄';collapse.setAttribute('aria-label',collapsed?'Expand World Builder keyboard':'Collapse World Builder keyboard');collapse.setAttribute('aria-expanded',collapsed?'false':'true');collapse.addEventListener('click',()=>{const next=!root.classList.contains('wb-keyboard-collapsed');root.classList.toggle('wb-keyboard-collapsed',next);write(COLLAPSE_KEY,String(next));collapse.textContent=next?'⌃':'⌄';collapse.setAttribute('aria-label',next?'Expand World Builder keyboard':'Collapse World Builder keyboard');collapse.setAttribute('aria-expanded',next?'false':'true');scheduleRefresh()});
 head.append(badge,statusNode,collapse);modeRow=document.createElement('div');modeRow.className='wb-keyboard-mode-row';modeRow.setAttribute('role','tablist');modeRow.setAttribute('aria-label','World Builder keyboard modes');commandRow=document.createElement('div');commandRow.className='wb-keyboard-command-row';commandRow.setAttribute('role','group');commandRow.setAttribute('aria-label','Commands for selected World Builder keyboard');keyboard.append(head,modeRow,commandRow);root.appendChild(keyboard);
 renderModes();const stored=read(MODE_KEY,'pixels');setMode(MODES.includes(stored)?stored:'pixels');lastSelectedCount=selectionCount();
 rootObserver?.disconnect();rootObserver=new MutationObserver(records=>{if(records.every(r=>r.target?.closest?.('.wb-context-keyboard')))return;scheduleRefresh()});rootObserver.observe(root,{childList:true,subtree:true,attributes:true,characterData:true,attributeFilter:['disabled','class','data-viewer-locked','data-camera-visible-cells','data-footprint']});
}
function mount(){const root=studio();if(!root)return;if(root===activeRoot&&keyboard?.isConnected)return;rootObserver?.disconnect();keyboard?.remove();build(root)}

window.addEventListener('rist:viewer-state',scheduleRefresh);window.addEventListener('rist-parallax-settings',scheduleRefresh);window.addEventListener('rist-sprite-playback',scheduleRefresh);window.addEventListener('resize',scheduleRefresh,{passive:true});
document.addEventListener('keydown',event=>{
 if(!activeRoot?.isConnected)return;const target=event.target;const typing=target instanceof HTMLInputElement||target instanceof HTMLTextAreaElement||target instanceof HTMLSelectElement||target?.isContentEditable;if(typing)return;
 const key=event.key.toLowerCase();
 if((event.ctrlKey||event.metaKey)&&key==='z'){event.preventDefault();clickCommand('undo');return}
 if((event.ctrlKey||event.metaKey)&&key==='s'){event.preventDefault();save();return}
 if(event.key==='Delete'){event.preventDefault();clickCommand('remove');return}
 if(event.key==='Escape'){if(closeTopOverlay()){event.preventDefault();return}setMode('pixels');return}
 const number=Number(event.key);if(Number.isInteger(number)&&number>=1&&number<=MODES.length){event.preventDefault();setMode(MODES[number-1]);return}
 if(key==='g'){event.preventDefault();toggleGrid();return}
 if(key==='r'){event.preventDefault();clickCommand('rotate');return}
 if(event.key==='['){event.preventDefault();stepDepth('layer',-1);return}
 if(event.key===']'){event.preventDefault();stepDepth('layer',1);return}
});

ensureStyle();mount();
const pageObserver=new MutationObserver(()=>mount());pageObserver.observe(document.documentElement,{childList:true,subtree:true});
