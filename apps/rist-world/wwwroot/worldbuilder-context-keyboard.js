const STYLE_ID='rist-worldbuilder-viewer-keyboard-css';
const MODE_KEY='rist.worldbuilder.keyboard.mode.v4';
const QUICK_KEY='rist.worldbuilder.keyboard.quickHidden.v1';
const ACCESS_LARGE_KEY='rist.worldbuilder.access.largeTargets.v1';
const ACCESS_CONTRAST_KEY='rist.worldbuilder.access.highContrast.v1';
const ACCESS_MOTION_KEY='rist.worldbuilder.access.reducedMotion.v1';
const MODES=['pixels','tiles','sprites','target','navigate','z','parallax','access','file'];
const FALLBACK_TIERS=[
 {key:'ocean-floor',label:'Ocean Floor',tierIndex:0},
 {key:'surface',label:'Surface',tierIndex:1},
 {key:'higher-ground',label:'Higher Ground',tierIndex:2},
 {key:'clouds',label:'Clouds',tierIndex:3}
];
let activeRoot=null,keyboard=null,launcher=null,tierHud=null,tierSelect=null,statusNode=null,modeRow=null,commandRow=null,rootObserver=null,refreshFrame=0,lastSelectedCount=0;

function ensureStyle(){if(document.getElementById(STYLE_ID))return;const link=document.createElement('link');link.id=STYLE_ID;link.rel='stylesheet';link.href='./css/worldbuilder-viewer-keyboard.css?v=20260917-single-z-overlay-1';document.head.appendChild(link)}
function read(key,fallback){try{return localStorage.getItem(key)??fallback}catch{return fallback}}
function write(key,value){try{localStorage.setItem(key,String(value))}catch{}}
function studio(){return document.querySelector('.worldbuilder-studio')}
function railButtons(root=activeRoot){return root?[...root.querySelectorAll('.studio-command-rail button')]:[]}
function findStrong(title,root=activeRoot){return railButtons(root).find(b=>(b.querySelector('strong')?.textContent||'').trim()===title)||null}
function clickStrong(title,root=activeRoot){const b=findStrong(title,root);if(!b||b.disabled)return false;b.click();scheduleRefresh();return true}
function commandButton(name,root=activeRoot){return root?.querySelector(`.studio-command-rail [data-wb-command="${name}"]`)||null}
function runtimeButton(name,root=activeRoot){return root?.querySelector(`.studio-command-rail [data-wb-runtime="${name}"]`)||null}
function clickCommand(name,root=activeRoot){const b=commandButton(name,root);if(!b||b.disabled)return false;b.click();scheduleRefresh();return true}
function clickRuntime(name,root=activeRoot){const b=runtimeButton(name,root);if(!b||b.disabled)return false;b.click();scheduleRefresh();return true}
function depthApi(){return window.ristWorldBuilderDepth||null}
function depthState(){const s=depthApi()?.state?.()||{};return{sceneZ:Number(s.sceneZ??activeRoot?.dataset.wbSceneZ??0)||0,tierIndex:Number(s.tierIndex??activeRoot?.dataset.wbTierIndex??0)||0,viewerLocked:(s.viewerLocked??activeRoot?.dataset.wbViewerLocked)==='true'||s.viewerLocked===true}}
function tierShortcuts(){const list=depthApi()?.shortcuts?.();return Array.isArray(list)&&list.length?list:FALLBACK_TIERS}
function moveSceneZ(delta){depthApi()?.moveSceneZ?.(delta);scheduleRefresh()}
function setTier(index){depthApi()?.setTier?.(index);scheduleRefresh()}
function viewerState(){try{return window.ristViewerAuthority?.get?.()||{}}catch{return{}}}
function playbackState(){try{return window.ristSpritePlayback?.state?.()||{}}catch{return{}}}
function parallaxState(){try{const enabled=window.ristParallax?.isEnabled?.()!==false,requested=window.ristParallax?.isWorldBuilderActive?.()===true,strength=Number(window.ristParallax?.tiltStrength?.()??.65);return{enabled,requested,active:enabled&&requested,strength:Number.isFinite(strength)?Math.max(0,Math.min(1,strength)):.65}}catch{return{enabled:true,requested:false,active:false,strength:.65}}}
function currentMode(){const mode=activeRoot?.dataset.wbKeyboardMode||read(MODE_KEY,'pixels');return MODES.includes(mode)?mode:'pixels'}
function tileButton(){return activeRoot?.querySelector('.studio-command-rail .tile-size-button')||null}
function tileFootprint(){const b=tileButton(),fromData=Number(b?.dataset?.footprint);if(Number.isFinite(fromData)&&fromData>0)return fromData;const text=(b?.querySelector('strong')?.textContent||'1').replace(/[^0-9.]/g,'');return Number(text)||1}
function tileSize(){return`${tileFootprint()}²`}
function selectionCount(){const text=(commandButton('remove')?.querySelector('small')?.textContent||'0').trim(),n=parseInt(text,10);return Number.isFinite(n)?n:0}
function lockLabel(){const b=findStrong('Unlock')||findStrong('Lock')||findStrong('Z-Lock');return(b?.querySelector('strong')?.textContent||'Lock').trim()}
function toggleLock(){if(clickStrong('Unlock')||clickStrong('Lock')||clickStrong('Z-Lock'))return;try{window.ristViewerAuthority?.toggleLocked?.({source:'keyboard'})}catch{}scheduleRefresh()}
function toggleGrid(){try{window.ristViewerAuthority?.toggleGrid?.({source:'keyboard'})}catch{}scheduleRefresh()}
function zoomBy(factor){try{window.ristViewerAuthority?.zoomBy?.(factor,{mode:'manual',source:'keyboard'})}catch{}scheduleRefresh()}
function autoZoom(){try{window.ristViewerAuthority?.resetAutoZoom?.({source:'keyboard'})}catch{}scheduleRefresh()}
function centerView(){try{window.ristViewerAuthority?.setPosition?.(0,0,true,'keyboard-center')}catch{}scheduleRefresh()}
function nudge(axis,delta){try{window.ristViewerNavigation?.nudge?.(axis,delta)}catch{}scheduleRefresh()}
function toggleQuick(){if(!activeRoot)return;activeRoot.dataset.wbQuickHidden=activeRoot.dataset.wbQuickHidden==='true'?'false':'true';write(QUICK_KEY,activeRoot.dataset.wbQuickHidden);scheduleRefresh()}
function openHome(){activeRoot?.querySelector('.studio-home')?.click()}
function openLibrary(sprite=false){if(sprite)clickStrong('Sprite Library');else clickStrong('Library');scheduleRefresh()}
function cycleTileSize(){const b=tileButton();if(b&&!b.disabled)b.click();scheduleRefresh()}
function setPixelFootprint(){const b=tileButton();if(!b||b.disabled)return;let tries=0;const step=()=>{if(tileFootprint()===1||tries++>7){scheduleRefresh();return}b.click();setTimeout(step,24)};step()}
function save(){clickStrong('Save')}
function load(){clickStrong('Load')}
function publish(){clickStrong('Publish')}
function descriptionOnly(){return activeRoot?.querySelector('.description-mode-toggle')?.getAttribute('aria-pressed')==='true'}
function toggleDescription(){const button=activeRoot?.querySelector('.description-mode-toggle');if(button&&!button.disabled)button.click();scheduleRefresh()}
function keyboardOpen(){return activeRoot?.classList.contains('wb-keyboard-open')===true}
function setKeyboardOpen(open){if(!activeRoot)return;activeRoot.classList.toggle('wb-keyboard-open',!!open);launcher?.setAttribute('aria-expanded',open?'true':'false');keyboard?.setAttribute('aria-hidden',open?'false':'true');if(open)requestAnimationFrame(()=>modeRow?.querySelector('.active')?.scrollIntoView({block:'nearest',inline:'nearest'}));scheduleRefresh()}

function togglePerspective(){if(accessState().reduced)return;if(clickRuntime('parallax'))return;try{const p=parallaxState();if(!p.enabled)window.ristParallax?.setEnabled?.(true);window.ristParallax?.setActive?.(!p.requested)}catch{}scheduleRefresh()}
function adjustTilt(delta){const p=parallaxState();try{window.ristParallax?.setTiltStrength?.(Math.max(0,Math.min(1,p.strength+delta)))}catch{}scheduleRefresh()}
function resetTilt(){try{window.ristParallax?.resetTilt?.()}catch{}scheduleRefresh()}
function requestMotion(){try{window.ristMotionPermission?.request?.()}catch{}scheduleRefresh()}
function togglePlayback(){try{const s=playbackState().state||'playing';if(s==='playing')window.ristSpritePlayback?.pause?.();else window.ristSpritePlayback?.play?.()}catch{}scheduleRefresh()}
function stopPlayback(){try{window.ristSpritePlayback?.stop?.()}catch{}scheduleRefresh()}
function cycleFps(){if(!clickRuntime('fps')){const values=[6,12,24,30,60],s=playbackState(),i=values.indexOf(Number(s.fps)||12),next=values[(i+1)%values.length];try{localStorage.setItem('rist.sprites.fps.v1',String(next));window.dispatchEvent(new CustomEvent('rist-sprite-playback',{detail:{state:s.state||'playing',fps:next}}))}catch{}}scheduleRefresh()}

function accessState(){return{large:read(ACCESS_LARGE_KEY,'false')==='true',contrast:read(ACCESS_CONTRAST_KEY,'false')==='true',reduced:read(ACCESS_MOTION_KEY,'false')==='true'}}
function applyAccessState(){const s=accessState();if(!activeRoot)return s;activeRoot.classList.toggle('wb-access-large',s.large);activeRoot.classList.toggle('wb-access-contrast',s.contrast);activeRoot.classList.toggle('wb-access-reduced',s.reduced);return s}
function toggleLargeTargets(){const s=accessState();write(ACCESS_LARGE_KEY,!s.large);applyAccessState();scheduleRefresh()}
function toggleHighContrast(){const s=accessState();write(ACCESS_CONTRAST_KEY,!s.contrast);applyAccessState();scheduleRefresh()}
function toggleReducedMotion(){const s=accessState(),next=!s.reduced;write(ACCESS_MOTION_KEY,next);applyAccessState();if(next){try{window.ristSpritePlayback?.pause?.()}catch{}try{window.ristParallax?.setActive?.(false)}catch{}}scheduleRefresh()}

function descriptor(label,sub,action,{active=false,disabled=false,danger=false}={}){return{label,sub,action,active,disabled,danger}}
function commandsFor(mode){
 const view=viewerState(),play=playbackState(),par=parallaxState(),selected=selectionCount(),locked=depthState().viewerLocked,access=accessState(),depth=depthState();
 switch(mode){
  case 'pixels':return[
   descriptor('1²','Smallest Cell',setPixelFootprint,{active:tileFootprint()===1}),descriptor('Grid',view.grid===false?'Off':'On',toggleGrid,{active:view.grid!==false}),descriptor('Zoom −',`${Math.round(view.visibleCells||12)} Cells`,()=>zoomBy(.9)),descriptor('Zoom +',`${Math.round(view.visibleCells||12)} Cells`,()=>zoomBy(1.1)),descriptor('Center','Viewer',centerView),descriptor('Undo','Last Action',()=>clickCommand('undo'),{disabled:!!commandButton('undo')?.disabled})
  ];
  case 'tiles':return[
   descriptor('Library','Tile Assets',()=>openLibrary(false)),descriptor(tileSize(),'Tile Size',cycleTileSize),descriptor('Quick','Asset Strip',toggleQuick,{active:activeRoot?.dataset.wbQuickHidden!=='true'}),descriptor('Target',`${selected} Selected`,()=>setMode('target'),{disabled:selected<1}),descriptor('Undo','Last Action',()=>clickCommand('undo'),{disabled:!!commandButton('undo')?.disabled}),descriptor('Grid',view.grid===false?'Off':'On',toggleGrid,{active:view.grid!==false})
  ];
  case 'sprites':return[
   descriptor('Sprite Library','Animated Assets',()=>openLibrary(true)),descriptor('Play / Pause',play.state||'playing',togglePlayback,{active:play.state==='playing'}),descriptor('Stop','Sprites',stopPlayback),descriptor('FPS',String(play.fps||12),cycleFps),descriptor('Perspective',access.reduced?'Motion Reduced':par.active?'Tilt On':'Tilt Off',togglePerspective,{active:par.active,disabled:access.reduced}),descriptor(tileSize(),'Tile Size',cycleTileSize),descriptor('Target',`${selected} Selected`,()=>setMode('target'),{disabled:selected<1})
  ];
  case 'target':return[
   descriptor('Rotate','90°',()=>clickCommand('rotate'),{disabled:selected<1}),descriptor('Resize',`To ${tileSize()}`,()=>clickCommand('resize'),{disabled:selected<1}),descriptor('Tile Size',tileSize(),cycleTileSize,{disabled:selected<1}),descriptor('Z / Tier',`Z ${depth.sceneZ}`,()=>setMode('z'),{disabled:selected<1}),descriptor('Undo','Last Action',()=>clickCommand('undo'),{disabled:!!commandButton('undo')?.disabled}),descriptor('Remove',`${selected} Selected`,()=>clickCommand('remove'),{disabled:selected<1,danger:true})
  ];
  case 'navigate':return[
   descriptor('←','Pan X −',()=>nudge('x',-1),{disabled:locked}),descriptor('→','Pan X +',()=>nudge('x',1),{disabled:locked}),descriptor('↑','Pan Y −',()=>nudge('y',-1),{disabled:locked}),descriptor('↓','Pan Y +',()=>nudge('y',1),{disabled:locked}),descriptor('Zoom −','Viewer',()=>zoomBy(.9)),descriptor('Zoom +','Viewer',()=>zoomBy(1.1)),descriptor('Z −',`Z ${depth.sceneZ}`,()=>moveSceneZ(-1),{disabled:locked}),descriptor('Z +',`Z ${depth.sceneZ}`,()=>moveSceneZ(1),{disabled:locked}),descriptor('Center','0,0',centerView),descriptor('Auto View','Fit Device',autoZoom),descriptor(lockLabel(),locked?'Viewer Locked':'Viewer Unlocked',toggleLock,{active:locked})
  ];
  case 'z':return[
   descriptor('Z −',`Z ${depth.sceneZ}`,()=>moveSceneZ(-1),{disabled:locked}),descriptor('Z +',`Z ${depth.sceneZ}`,()=>moveSceneZ(1),{disabled:locked}),descriptor('Ocean Floor','Tier 0',()=>setTier(0),{active:depth.tierIndex===0,disabled:locked}),descriptor('Surface','Tier 1',()=>setTier(1),{active:depth.tierIndex===1,disabled:locked}),descriptor('Higher Ground','Tier 2',()=>setTier(2),{active:depth.tierIndex===2,disabled:locked}),descriptor('Clouds','Tier 3',()=>setTier(3),{active:depth.tierIndex===3,disabled:locked}),descriptor(lockLabel(),locked?'Viewer Locked':'Viewer Unlocked',toggleLock,{active:locked}),descriptor('Grid',view.grid===false?'Off':'On',toggleGrid,{active:view.grid!==false})
  ];
  case 'parallax':return[
   descriptor('Perspective',access.reduced?'Motion Reduced':par.active?'Tier Tilt On':'Tier Tilt Off',togglePerspective,{active:par.active,disabled:access.reduced}),descriptor('Tilt −',`${Math.round(par.strength*100)}%`,()=>adjustTilt(-.1),{disabled:!par.active||access.reduced}),descriptor('Tilt +',`${Math.round(par.strength*100)}%`,()=>adjustTilt(.1),{disabled:!par.active||access.reduced}),descriptor('Reset Tilt','Viewer Only',resetTilt,{disabled:access.reduced}),descriptor('Z / Tier',`Z ${depth.sceneZ}`,()=>setMode('z')),descriptor('Motion','Device / Pointer',requestMotion,{disabled:access.reduced}),descriptor('Reduce Motion',access.reduced?'On':'Off',toggleReducedMotion,{active:access.reduced})
  ];
  case 'access':return[
   descriptor('Large Keys',access.large?'On':'Off',toggleLargeTargets,{active:access.large}),descriptor('High Contrast',access.contrast?'On':'Off',toggleHighContrast,{active:access.contrast}),descriptor('Reduce Motion',access.reduced?'On':'Off',toggleReducedMotion,{active:access.reduced}),descriptor('Description',descriptionOnly()?'Text Map':'Visual Map',toggleDescription,{active:descriptionOnly()}),descriptor('Navigate','Accessible View',()=>setMode('navigate')),descriptor('Grid',view.grid===false?'Off':'On',toggleGrid,{active:view.grid!==false}),descriptor('Center','Viewer',centerView),descriptor('Auto View','Fit Device',autoZoom),descriptor(lockLabel(),locked?'Viewer Locked':'Viewer Unlocked',toggleLock,{active:locked})
  ];
  case 'file':return[
   descriptor('Save','World',save),descriptor('Load','Saved / Published',load),descriptor('Publish','To Region',publish),descriptor('Menu','Shaelvien',openHome),descriptor('Grid',view.grid===false?'Off':'On',toggleGrid,{active:view.grid!==false}),descriptor(lockLabel(),locked?'Viewer Locked':'Viewer Unlocked',toggleLock,{active:locked})
  ];
  default:return[];
 }
}
function modeLabel(mode){return({pixels:'Pixels',tiles:'Tiles',sprites:'Sprites',target:'Target',navigate:'Navigate',z:'Z / Tiers',parallax:'Perspective',access:'Access',file:'File'})[mode]||mode}
function setMode(mode){if(!activeRoot||!MODES.includes(mode))return;activeRoot.dataset.wbKeyboardMode=mode;write(MODE_KEY,mode);[...(modeRow?.querySelectorAll('button')||[])].forEach(b=>{const on=b.dataset.mode===mode;b.classList.toggle('active',on);b.setAttribute('aria-pressed',on?'true':'false');b.setAttribute('aria-selected',on?'true':'false')});renderCommands();updateStatus()}
function renderModes(){if(!modeRow)return;modeRow.replaceChildren();for(const mode of MODES){const b=document.createElement('button');b.type='button';b.className='wb-keyboard-mode';b.dataset.mode=mode;b.textContent=modeLabel(mode);b.setAttribute('role','tab');b.setAttribute('aria-label',`${modeLabel(mode)} keyboard`);b.addEventListener('click',()=>setMode(mode));modeRow.appendChild(b)}}
function renderCommands(){if(!commandRow||!activeRoot)return;commandRow.replaceChildren();for(const item of commandsFor(currentMode())){const b=document.createElement('button');b.type='button';b.className='wb-keyboard-command';if(item.active)b.classList.add('active');if(item.danger)b.classList.add('danger');b.disabled=!!item.disabled;const strong=document.createElement('strong'),small=document.createElement('small');strong.textContent=item.label;small.textContent=item.sub;b.append(strong,small);b.setAttribute('aria-label',`${item.label}: ${item.sub}`);b.addEventListener('click',item.action);commandRow.appendChild(b)}}
function renderTierSelect(){if(!tierSelect)return;const depth=depthState(),list=tierShortcuts(),current=String(depth.tierIndex);const signature=list.map(x=>`${x.tierIndex}:${x.label}`).join('|');if(tierSelect.dataset.signature!==signature){tierSelect.replaceChildren();for(const item of list){const option=document.createElement('option');option.value=String(item.tierIndex);option.textContent=item.label;tierSelect.appendChild(option)}tierSelect.dataset.signature=signature}if([...tierSelect.options].some(o=>o.value===current))tierSelect.value=current;tierSelect.disabled=depth.viewerLocked;tierSelect.setAttribute('aria-label',`Tier shortcut. Current tier ${depth.tierIndex}, Z ${depth.sceneZ}`)}
function updateStatus(){if(!statusNode||!activeRoot)return;const view=viewerState(),selected=selectionCount(),depth=depthState(),parts=[modeLabel(currentMode()).toUpperCase(),`${Math.round(view.visibleCells||12)} CELLS`,`Z ${depth.sceneZ}`,`TIER ${depth.tierIndex}`];if(selected>0)parts.push(`${selected} TARGET${selected===1?'':'S'}`);statusNode.textContent=parts.join(' · ');renderTierSelect()}
function refreshNow(){if(!activeRoot?.isConnected)return;const selected=selectionCount();if(selected>0&&lastSelectedCount===0&&currentMode()!=='target'&&keyboardOpen()){lastSelectedCount=selected;setMode('target');return}lastSelectedCount=selected;renderCommands();updateStatus()}
function scheduleRefresh(){if(refreshFrame)return;refreshFrame=requestAnimationFrame(()=>{refreshFrame=0;refreshNow()})}
function closeTopOverlay(){const preview=activeRoot?.querySelector('.asset-preview-close');if(preview){preview.click();return true}const rail=activeRoot?.querySelector('.world-asset-rail .rail-back');if(rail){rail.click();return true}return false}
function build(root){
 activeRoot=root;ensureStyle();root.dataset.wbQuickHidden=read(QUICK_KEY,'false');root.classList.remove('wb-keyboard-open');applyAccessState();
 root.querySelectorAll('.wb-context-keyboard,.wb-keyboard-launcher,.wb-tier-shortcut-hud').forEach(node=>node.remove());
 launcher=document.createElement('button');launcher.type='button';launcher.className='wb-keyboard-launcher';launcher.textContent='⌨︎';launcher.setAttribute('aria-label','Open World Builder keyboard');launcher.setAttribute('aria-expanded','false');launcher.addEventListener('click',()=>setKeyboardOpen(true));
 tierHud=document.createElement('label');tierHud.className='wb-tier-shortcut-hud';const tierLabel=document.createElement('span');tierLabel.textContent='Tier';tierSelect=document.createElement('select');tierSelect.className='wb-tier-shortcut-select';tierSelect.addEventListener('change',()=>setTier(Number(tierSelect.value)));tierHud.append(tierLabel,tierSelect);
 keyboard=document.createElement('section');keyboard.className='wb-context-keyboard';keyboard.setAttribute('role','toolbar');keyboard.setAttribute('aria-label','World Builder contextual keyboard');keyboard.setAttribute('aria-hidden','true');
 const head=document.createElement('div');head.className='wb-keyboard-head';const badge=document.createElement('span');badge.className='wb-keyboard-badge';badge.textContent='VIEWER';statusNode=document.createElement('span');statusNode.className='wb-keyboard-status';statusNode.setAttribute('role','status');statusNode.setAttribute('aria-live','polite');statusNode.setAttribute('aria-atomic','true');const close=document.createElement('button');close.type='button';close.className='wb-keyboard-close';close.textContent='⌄';close.setAttribute('aria-label','Hide World Builder keyboard');close.addEventListener('click',()=>setKeyboardOpen(false));head.append(badge,statusNode,close);
 modeRow=document.createElement('div');modeRow.className='wb-keyboard-mode-row';modeRow.setAttribute('role','tablist');modeRow.setAttribute('aria-label','World Builder keyboard modes');commandRow=document.createElement('div');commandRow.className='wb-keyboard-command-row';commandRow.setAttribute('role','group');commandRow.setAttribute('aria-label','Commands for selected World Builder keyboard');keyboard.append(head,modeRow,commandRow);root.append(tierHud,launcher,keyboard);
 renderModes();const stored=read(MODE_KEY,'pixels');setMode(MODES.includes(stored)?stored:'pixels');lastSelectedCount=selectionCount();renderTierSelect();depthApi()?.refresh?.();
 rootObserver?.disconnect();rootObserver=new MutationObserver(records=>{if(records.every(r=>r.target?.closest?.('.wb-context-keyboard,.wb-tier-shortcut-hud')))return;scheduleRefresh()});rootObserver.observe(root,{childList:true,subtree:true,attributes:true,characterData:true,attributeFilter:['disabled','class','data-viewer-locked','data-camera-visible-cells','data-footprint','aria-pressed','data-wb-scene-z','data-wb-tier-index']})
}
function mount(){const root=studio();if(!root)return;if(root===activeRoot&&keyboard?.isConnected)return;rootObserver?.disconnect();keyboard?.remove();launcher?.remove();tierHud?.remove();build(root)}

window.addEventListener('rist:viewer-state',scheduleRefresh);window.addEventListener('rist-parallax-settings',scheduleRefresh);window.addEventListener('rist:worldbuilder-depth',scheduleRefresh);window.addEventListener('rist-sprite-playback',scheduleRefresh);window.addEventListener('resize',scheduleRefresh,{passive:true});
document.addEventListener('keydown',event=>{
 if(!activeRoot?.isConnected)return;const target=event.target,typing=target instanceof HTMLInputElement||target instanceof HTMLTextAreaElement||target instanceof HTMLSelectElement||target?.isContentEditable;if(typing)return;const key=event.key.toLowerCase();
 if((event.ctrlKey||event.metaKey)&&key==='z'){event.preventDefault();clickCommand('undo');return}if((event.ctrlKey||event.metaKey)&&key==='s'){event.preventDefault();save();return}if(event.key==='Delete'){event.preventDefault();clickCommand('remove');return}if(event.key==='Escape'){if(closeTopOverlay()){event.preventDefault();return}if(keyboardOpen()){event.preventDefault();setKeyboardOpen(false);return}}
 const number=Number(event.key);if(keyboardOpen()&&Number.isInteger(number)&&number>=1&&number<=MODES.length){event.preventDefault();setMode(MODES[number-1]);return}
 if(key==='g'){event.preventDefault();toggleGrid();return}if(key==='r'){event.preventDefault();clickCommand('rotate');return}if(key==='p'){event.preventDefault();setMode('parallax');setKeyboardOpen(true);return}if(key==='n'){event.preventDefault();setMode('navigate');setKeyboardOpen(true);return}if(event.key==='['){event.preventDefault();moveSceneZ(-1);return}if(event.key===']'){event.preventDefault();moveSceneZ(1);return}
});

ensureStyle();mount();
const pageObserver=new MutationObserver(()=>mount());pageObserver.observe(document.documentElement,{childList:true,subtree:true});