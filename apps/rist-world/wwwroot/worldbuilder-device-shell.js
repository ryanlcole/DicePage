(()=>{
 'use strict';

 const STYLE_ID='rist-worldbuilder-device-shell-css';
 const MODE_KEY='rist.worldbuilder.deviceKeyboard.mode.v1';
 const COLLAPSE_KEY='rist.worldbuilder.deviceKeyboard.collapsed.v1';
 const WIDGET_KEY='rist.worldbuilder.viewerWidgets.v1';
 const POSITION_KEY='rist.worldbuilder.viewerWidgetPositions.v1';
 const LABEL_KEY='rist.worldbuilder.labelDraft.v1';
 const MODES=['pixels','tiles','sprites','labels','viewer','litch','cad','stylus','tethers','metadata','target','widgets','access','file'];
 const COMING_SOON_MODES=new Set(['litch','cad','stylus','tethers','metadata']);
 const MODE_LABELS={pixels:'Pixels',tiles:'Tiles',sprites:'Sprites',labels:'Labels',viewer:'Viewer',litch:'Litch',cad:'CAD',stylus:'Stylus',tethers:'Tethers',metadata:'Metadata',target:'Target',widgets:'Widgets',access:'Access',file:'File'};
 const ACCESS_LARGE_KEY='rist.worldbuilder.access.largeTargets.v1';
 const ACCESS_CONTRAST_KEY='rist.worldbuilder.access.highContrast.v1';
 const ACCESS_MOTION_KEY='rist.worldbuilder.access.reducedMotion.v1';

 let root=null;
 let keyboard=null;
 let modeRow=null;
 let keysNode=null;
 let modeName=null;
 let liveNode=null;
 let widgetLayer=null;
 let pageObserver=null;
 let timer=0;
 let selectedWidget='clock';
 let labelDraft=null;
 let toolState={
  litch:{tool:'light-peg',intensity:70,radius:2},
  cad:{tool:'line',snap:true},
  stylus:{tool:'visual',width:2,pressure:true},
  tethers:{domain:'sound',strength:50,range:3,direction:'omni'},
  metadata:{field:'keywords',value:''}
 };

 function read(key,fallback){try{return localStorage.getItem(key)??fallback}catch{return fallback}}
 function write(key,value){try{localStorage.setItem(key,String(value))}catch{}}
 function readJson(key,fallback){try{const raw=localStorage.getItem(key);return raw?JSON.parse(raw):fallback}catch{return fallback}}
 function writeJson(key,value){try{localStorage.setItem(key,JSON.stringify(value))}catch{}}
 function studio(){return document.querySelector('.worldbuilder-studio')}
 function viewer(){return root?.querySelector('.studio-viewer-canvas')||null}
 function isIos(){return /iPad|iPhone|iPod/.test(navigator.userAgent)||((navigator.platform==='MacIntel'||navigator.userAgent.includes('Mac'))&&(navigator.maxTouchPoints||0)>1)}
 function isAndroid(){return /Android/i.test(navigator.userAgent)}
 function ensureStyle(){
  if(document.getElementById(STYLE_ID))return;
  const link=document.createElement('link');
  link.id=STYLE_ID;
  link.rel='stylesheet';
  link.href='./css/worldbuilder-device-shell.css?v=20260918-keyboard-coming-soon-1';
  document.head.appendChild(link);
 }
 function announce(message){if(liveNode)liveNode.textContent=message}
 function emit(name,detail={}){
  const event=new CustomEvent(name,{detail,bubbles:true,composed:true,cancelable:true});
  const accepted=window.dispatchEvent(event);
  return {event,accepted};
 }
 function railButtons(){return root?[...root.querySelectorAll('.studio-command-rail button')]:[]}
 function findStrong(title){return railButtons().find(button=>(button.querySelector('strong')?.textContent||'').trim()===title)||null}
 function clickStrong(title){const button=findStrong(title);if(!button||button.disabled)return false;button.click();return true}
 function commandButton(name){return root?.querySelector(`.studio-command-rail [data-wb-command="${name}"]`)||null}
 function runtimeButton(name){return root?.querySelector(`.studio-command-rail [data-wb-runtime="${name}"]`)||null}
 function clickCommand(name){const button=commandButton(name);if(!button||button.disabled)return false;button.click();return true}
 function clickRuntime(name){const button=runtimeButton(name);if(!button||button.disabled)return false;button.click();return true}
 function viewerState(){try{return window.ristViewerAuthority?.get?.()||{}}catch{return{}}}
 function playbackState(){try{return window.ristSpritePlayback?.state?.()||{}}catch{return{}}}
 function parallaxState(){try{return{active:window.ristParallax?.isWorldBuilderActive?.()===true,strength:Number(window.ristParallax?.tiltStrength?.()??.65)}}catch{return{active:false,strength:.65}}}
 function tileButton(){return root?.querySelector('.studio-command-rail .tile-size-button')||null}
 function tileFootprint(){const button=tileButton();const data=Number(button?.dataset?.footprint);if(Number.isFinite(data)&&data>0)return data;const text=(button?.textContent||'1').replace(/[^0-9.]/g,'');return Number(text)||1}
 function selectionCount(){const text=(commandButton('remove')?.querySelector('small')?.textContent||'0').trim();const count=parseInt(text,10);return Number.isFinite(count)?count:0}
 function setPixelFootprint(){const button=tileButton();if(!button||button.disabled)return;let guard=0;const step=()=>{if(tileFootprint()===1||guard++>8){refresh();return}button.click();setTimeout(step,20)};step()}
 function cycleTileSize(){const button=tileButton();if(button&&!button.disabled)button.click();setTimeout(refresh,0)}
 function toggleGrid(){try{window.ristViewerAuthority?.toggleGrid?.({source:'device-keyboard'})}catch{}refresh()}
 function zoomBy(factor){try{window.ristViewerAuthority?.zoomBy?.(factor,{mode:'manual',source:'device-keyboard'})}catch{}refresh()}
 function autoZoom(){try{window.ristViewerAuthority?.resetAutoZoom?.({source:'device-keyboard'})}catch{}refresh()}
 function centerView(){try{window.ristViewerAuthority?.setPosition?.(0,0,true,'device-keyboard-center')}catch{}refresh()}
 function nudge(axis,delta){try{window.ristViewerNavigation?.nudge?.(axis,delta)}catch{}refresh()}
 function toggleLock(){if(clickStrong('Unlock')||clickStrong('Lock')||clickStrong('Z-Lock')){refresh();return}try{window.ristViewerAuthority?.toggleLocked?.({source:'device-keyboard'})}catch{}refresh()}
 function togglePlayback(){try{const state=playbackState().state||'playing';if(state==='playing')window.ristSpritePlayback?.pause?.();else window.ristSpritePlayback?.play?.()}catch{}refresh()}
 function stopPlayback(){try{window.ristSpritePlayback?.stop?.()}catch{}refresh()}
 function cycleFps(){if(clickRuntime('fps')){refresh();return}const values=[6,12,24,30,60];const state=playbackState();const index=values.indexOf(Number(state.fps)||12);const next=values[(index+1)%values.length];try{localStorage.setItem('rist.sprites.fps.v1',String(next));window.dispatchEvent(new CustomEvent('rist-sprite-playback',{detail:{state:state.state||'playing',fps:next}}))}catch{}refresh()}
 function togglePerspective(){if(read(ACCESS_MOTION_KEY,'false')==='true')return;if(clickRuntime('parallax')){refresh();return}try{const active=parallaxState().active;window.ristParallax?.setEnabled?.(true);window.ristParallax?.setActive?.(!active)}catch{}refresh()}
 function openLibrary(sprite=false){if(sprite)clickStrong('Sprite Library');else clickStrong('Library')}
 function save(){clickStrong('Save')}
 function load(){clickStrong('Load')}
 function publish(){clickStrong('Publish')}
 function openMenu(){root?.querySelector('.studio-home')?.click()||window.RistStartMenu?.open?.()}
 function stepDepth(kind,direction){
  const title=kind==='layer'?'Layers':'Tiers';
  clickStrong(title);
  let tries=0;
  const run=()=>{
   const needle=kind==='layer'?'Layer ':'Tier ';
   const panel=[...(root?.querySelectorAll('.studio-mini-panel')||[])].find(node=>node.textContent?.includes(needle));
   const label=kind==='layer'?(direction<0?'Layer Down':'Layer Up'):(direction<0?'Tier Down':'Tier Up');
   const button=[...(panel?.querySelectorAll('button')||[])].find(node=>node.textContent?.trim()===label);
   if(button){if(!button.disabled)button.click();refresh();return}
   if(tries++<5)setTimeout(run,25);
  };
  setTimeout(run,0);
 }

 function descriptor(label,sub,action,options={}){return{label,sub,action,...options}}
 function toolEvent(family,patch={}){
  toolState[family]={...toolState[family],...patch};
  emit(`rist:worldbuilder-${family}`,{...toolState[family],source:'device-keyboard',selectedCount:selectionCount()});
  announce(`${MODE_LABELS[family]||family}: ${Object.values(patch).join(' ')}`);
  refresh();
 }

 function accessState(){return{large:read(ACCESS_LARGE_KEY,'false')==='true',contrast:read(ACCESS_CONTRAST_KEY,'false')==='true',reduced:read(ACCESS_MOTION_KEY,'false')==='true'}}
 function applyAccess(){
  if(!root)return;
  const state=accessState();
  root.classList.toggle('wb-access-large',state.large);
  root.classList.toggle('wb-access-contrast',state.contrast);
  root.classList.toggle('wb-access-reduced',state.reduced);
 }
 function toggleAccess(name){
  const map={large:ACCESS_LARGE_KEY,contrast:ACCESS_CONTRAST_KEY,reduced:ACCESS_MOTION_KEY};
  const key=map[name];if(!key)return;
  const next=read(key,'false')!=='true';write(key,next);
  applyAccess();
  if(name==='reduced'&&next){try{window.ristSpritePlayback?.pause?.()}catch{}try{window.ristParallax?.setActive?.(false)}catch{}}
  refresh();
 }
 function descriptionOnly(){return root?.querySelector('.description-mode-toggle')?.getAttribute('aria-pressed')==='true'}
 function toggleDescription(){const button=root?.querySelector('.description-mode-toggle');if(button&&!button.disabled)button.click();refresh()}

 const widgetDefaults={clock:true,date:true,weather:false,coords:false};
 function widgetVisibility(){return{...widgetDefaults,...readJson(WIDGET_KEY,{})}}
 function saveWidgetVisibility(state){writeJson(WIDGET_KEY,state)}
 function widgetPositions(){return{clock:{x:.04,y:.05},date:{x:.04,y:.18},weather:{x:.62,y:.05},coords:{x:.62,y:.21},...readJson(POSITION_KEY,{})}}
 function saveWidgetPositions(state){writeJson(POSITION_KEY,state)}
 function widgetNode(name){return widgetLayer?.querySelector(`[data-widget="${name}"]`)||null}
 function toggleWidget(name){
  const state=widgetVisibility();state[name]=!state[name];saveWidgetVisibility(state);applyWidgetVisibility();selectedWidget=name;selectWidget(name);refresh();announce(`${name} widget ${state[name]?'shown':'hidden'}`)
 }
 function applyWidgetVisibility(){const state=widgetVisibility();for(const name of Object.keys(widgetDefaults)){const node=widgetNode(name);if(node)node.hidden=!state[name]}}
 function selectWidget(name){selectedWidget=name;widgetLayer?.querySelectorAll('.wb-viewer-widget').forEach(node=>node.classList.toggle('selected',node.dataset.widget===name))}
 function moveWidget(name,dx,dy){
  const node=widgetNode(name);const area=viewer();if(!node||!area)return;
  const areaRect=area.getBoundingClientRect(),rect=node.getBoundingClientRect();
  const left=Math.max(0,Math.min(areaRect.width-rect.width,(rect.left-areaRect.left)+dx));
  const top=Math.max(0,Math.min(areaRect.height-rect.height,(rect.top-areaRect.top)+dy));
  node.style.left=`${left}px`;node.style.top=`${top}px`;
  const positions=widgetPositions();positions[name]={x:areaRect.width?left/areaRect.width:0,y:areaRect.height?top/areaRect.height:0};saveWidgetPositions(positions);
  announce(`${name} widget moved`)
 }
 function resetWidgets(){writeJson(POSITION_KEY,{});positionWidgets();announce('Viewer widgets reset')}
 function positionWidgets(){const area=viewer();if(!area||!widgetLayer)return;const rect=area.getBoundingClientRect();const positions=widgetPositions();for(const [name,pos] of Object.entries(positions)){const node=widgetNode(name);if(!node)continue;const maxX=Math.max(0,rect.width-node.offsetWidth),maxY=Math.max(0,rect.height-node.offsetHeight);node.style.left=`${Math.max(0,Math.min(maxX,pos.x*rect.width))}px`;node.style.top=`${Math.max(0,Math.min(maxY,pos.y*rect.height))}px`}}
 function wireDrag(node){
  const grip=node.querySelector('.wb-widget-grip');if(!grip)return;
  let pointerId=null,startX=0,startY=0,baseLeft=0,baseTop=0;
  grip.addEventListener('pointerdown',event=>{if(event.button!==undefined&&event.button!==0)return;pointerId=event.pointerId;selectWidget(node.dataset.widget);const area=viewer()?.getBoundingClientRect();const rect=node.getBoundingClientRect();if(!area)return;startX=event.clientX;startY=event.clientY;baseLeft=rect.left-area.left;baseTop=rect.top-area.top;grip.setPointerCapture?.(pointerId);event.preventDefault()});
  grip.addEventListener('pointermove',event=>{if(pointerId!==event.pointerId)return;const area=viewer()?.getBoundingClientRect();if(!area)return;const left=Math.max(0,Math.min(area.width-node.offsetWidth,baseLeft+(event.clientX-startX)));const top=Math.max(0,Math.min(area.height-node.offsetHeight,baseTop+(event.clientY-startY)));node.style.left=`${left}px`;node.style.top=`${top}px`});
  const finish=event=>{if(pointerId!==event.pointerId)return;pointerId=null;const area=viewer()?.getBoundingClientRect();if(!area)return;const left=parseFloat(node.style.left)||0,top=parseFloat(node.style.top)||0;const positions=widgetPositions();positions[node.dataset.widget]={x:area.width?left/area.width:0,y:area.height?top/area.height:0};saveWidgetPositions(positions);announce(`${node.dataset.widget} widget placed`)};
  grip.addEventListener('pointerup',finish);grip.addEventListener('pointercancel',finish);
  node.addEventListener('focus',()=>selectWidget(node.dataset.widget));
  node.addEventListener('keydown',event=>{const step=event.shiftKey?24:8;if(event.key==='ArrowLeft'){event.preventDefault();moveWidget(node.dataset.widget,-step,0)}else if(event.key==='ArrowRight'){event.preventDefault();moveWidget(node.dataset.widget,step,0)}else if(event.key==='ArrowUp'){event.preventDefault();moveWidget(node.dataset.widget,0,-step)}else if(event.key==='ArrowDown'){event.preventDefault();moveWidget(node.dataset.widget,0,step)}})
 }
 function makeWidget(name,title,valueText,detailText){
  const section=document.createElement('section');section.className=`wb-viewer-widget wb-widget-${name}`;section.dataset.widget=name;section.tabIndex=0;section.setAttribute('role','group');section.setAttribute('aria-roledescription','movable viewer widget');section.setAttribute('aria-label',`${title} widget. Drag to reposition or use arrow keys while focused.`);
  const grip=document.createElement('div');grip.className='wb-widget-grip';grip.innerHTML=`<span>${title}</span><span aria-hidden="true">⋮⋮</span>`;
  const value=document.createElement('div');value.className='wb-widget-value';value.textContent=valueText;
  const detail=document.createElement('div');detail.className='wb-widget-detail';detail.textContent=detailText;
  section.append(grip,value,detail);widgetLayer.appendChild(section);wireDrag(section);return section
 }
 function buildWidgets(){
  const area=viewer();if(!area)return;
  area.querySelector('.wb-viewer-widgets')?.remove();
  widgetLayer=document.createElement('div');widgetLayer.className='wb-viewer-widgets';widgetLayer.setAttribute('aria-label','Viewer overlay widgets');area.appendChild(widgetLayer);
  makeWidget('clock','Time','--:--','Local device time');
  makeWidget('date','Date','--/--/----','Local device date');
  const weather=makeWidget('weather','Weather','Source not connected','No weather condition is assumed.');weather.dataset.sourceConnected='false';
  makeWidget('coords','Viewer','X 0 · Y 0','Camera presentation position');
  applyWidgetVisibility();positionWidgets();selectWidget(selectedWidget);tickWidgets()
 }
 function tickWidgets(){
  if(!root?.isConnected)return;
  const now=new Date();
  const time=now.toLocaleTimeString([], {hour:'numeric',minute:'2-digit'});
  const date=now.toLocaleDateString([], {weekday:'short',month:'short',day:'numeric',year:'numeric'});
  const clock=widgetNode('clock'),dateNode=widgetNode('date'),coords=widgetNode('coords');
  if(clock){clock.querySelector('.wb-widget-value').textContent=time;clock.querySelector('.wb-widget-detail').textContent=Intl.DateTimeFormat().resolvedOptions().timeZone||'Device local time';clock.setAttribute('aria-label',`Time widget. ${time}. Drag to reposition or use arrow keys while focused.`)}
  if(dateNode){dateNode.querySelector('.wb-widget-value').textContent=date;dateNode.setAttribute('aria-label',`Date widget. ${date}. Drag to reposition or use arrow keys while focused.`)}
  if(coords){const state=viewerState();const x=Number(state.x??state.camX??state.cameraX??0),y=Number(state.y??state.camY??state.cameraY??0),cells=Math.round(Number(state.visibleCells)||12);coords.querySelector('.wb-widget-value').textContent=`X ${Number.isFinite(x)?x.toFixed(2):'0'} · Y ${Number.isFinite(y)?y.toFixed(2):'0'}`;coords.querySelector('.wb-widget-detail').textContent=`${cells} × ${cells} presentation grid · world coordinates unchanged`}
 }
 function setWeather(detail={}){
  const node=widgetNode('weather');if(!node)return;
  const summary=String(detail.summary||detail.condition||'').trim();
  const temp=detail.temperature;
  const unit=String(detail.unit||'').trim();
  const location=String(detail.location||'').trim();
  const source=String(detail.source||'').trim();
  if(!summary&&temp===undefined){node.dataset.sourceConnected='false';node.querySelector('.wb-widget-value').textContent='Source not connected';node.querySelector('.wb-widget-detail').textContent='No weather condition is assumed.';node.setAttribute('aria-label','Weather widget. Weather source not connected.');return}
  const tempText=temp===undefined?'':`${temp}${unit?`°${unit.replace('°','')}`:'°'}`;
  node.dataset.sourceConnected='true';node.querySelector('.wb-widget-value').textContent=[tempText,summary].filter(Boolean).join(' · ');node.querySelector('.wb-widget-detail').textContent=[location,source].filter(Boolean).join(' · ')||'Connected weather data';node.setAttribute('aria-label',`Weather widget. ${node.querySelector('.wb-widget-value').textContent}. ${node.querySelector('.wb-widget-detail').textContent}.`)
 }

 function restoreLabelDraft(){const value=readJson(LABEL_KEY,null);if(value?.text)createLabelDraft(value.text,value)}
 function createLabelDraft(text,options={}){
  const area=viewer();if(!area||!String(text||'').trim())return;
  labelDraft?.remove();
  const node=document.createElement('div');node.className='wb-world-label-draft';node.tabIndex=0;node.setAttribute('role','button');node.setAttribute('aria-roledescription','movable label draft');node.dataset.presentationDraft='true';node.textContent=String(text).trim();
  const state={text:node.textContent,size:Number(options.size)||18,bold:options.bold!==false,italic:!!options.italic,outline:!!options.outline,x:Number.isFinite(options.x)?options.x:.5,y:Number.isFinite(options.y)?options.y:.42};
  node.style.fontSize=`${state.size}px`;node.style.fontWeight=state.bold?'700':'400';node.style.fontStyle=state.italic?'italic':'normal';node.style.textShadow=state.outline?'0 0 2px #000,1px 1px 1px #000,-1px -1px 1px #000':'none';node.style.left=`${state.x*100}%`;node.style.top=`${state.y*100}%`;node.setAttribute('aria-label',`Label draft: ${state.text}. Drag to place or use arrow keys.`);area.appendChild(node);labelDraft=node;labelDraft._state=state;wireLabelDrag(node);saveLabelDraft();emit('rist:worldbuilder-label-draft',{...state,source:'device-keyboard'});announce(`Label draft created: ${state.text}`)
 }
 function wireLabelDrag(node){
  let pointer=null,startX=0,startY=0,startLeft=0,startTop=0;
  node.addEventListener('pointerdown',event=>{if(event.button!==undefined&&event.button!==0)return;const area=viewer()?.getBoundingClientRect(),rect=node.getBoundingClientRect();if(!area)return;pointer=event.pointerId;startX=event.clientX;startY=event.clientY;startLeft=rect.left-area.left;startTop=rect.top-area.top;node.setPointerCapture?.(pointer);event.preventDefault()});
  node.addEventListener('pointermove',event=>{if(pointer!==event.pointerId)return;const area=viewer()?.getBoundingClientRect();if(!area)return;const x=Math.max(0,Math.min(area.width-node.offsetWidth,startLeft+event.clientX-startX));const y=Math.max(0,Math.min(area.height-node.offsetHeight,startTop+event.clientY-startY));node.style.left=`${x}px`;node.style.top=`${y}px`;node.style.transform='none'});
  const finish=event=>{if(pointer!==event.pointerId)return;pointer=null;updateLabelPosition();saveLabelDraft();emit('rist:worldbuilder-label-draft',{...node._state,source:'device-keyboard'})};node.addEventListener('pointerup',finish);node.addEventListener('pointercancel',finish);
  node.addEventListener('keydown',event=>{const step=event.shiftKey?24:6;if(event.key==='ArrowLeft'){event.preventDefault();moveLabel(-step,0)}else if(event.key==='ArrowRight'){event.preventDefault();moveLabel(step,0)}else if(event.key==='ArrowUp'){event.preventDefault();moveLabel(0,-step)}else if(event.key==='ArrowDown'){event.preventDefault();moveLabel(0,step)}})
 }
 function updateLabelPosition(){if(!labelDraft)return;const area=viewer()?.getBoundingClientRect(),rect=labelDraft.getBoundingClientRect();if(!area||!area.width||!area.height)return;labelDraft._state.x=(rect.left-area.left)/area.width;labelDraft._state.y=(rect.top-area.top)/area.height}
 function moveLabel(dx,dy){if(!labelDraft)return;const area=viewer()?.getBoundingClientRect(),rect=labelDraft.getBoundingClientRect();if(!area)return;const x=Math.max(0,Math.min(area.width-rect.width,rect.left-area.left+dx)),y=Math.max(0,Math.min(area.height-rect.height,rect.top-area.top+dy));labelDraft.style.left=`${x}px`;labelDraft.style.top=`${y}px`;labelDraft.style.transform='none';updateLabelPosition();saveLabelDraft();announce('Label moved')}
 function styleLabel(patch){if(!labelDraft)return;Object.assign(labelDraft._state,patch);const state=labelDraft._state;labelDraft.style.fontSize=`${state.size}px`;labelDraft.style.fontWeight=state.bold?'700':'400';labelDraft.style.fontStyle=state.italic?'italic':'normal';labelDraft.style.textShadow=state.outline?'0 0 2px #000,1px 1px 1px #000,-1px -1px 1px #000':'none';saveLabelDraft();emit('rist:worldbuilder-label-draft',{...state,source:'device-keyboard'});refresh()}
 function saveLabelDraft(){if(labelDraft?._state)writeJson(LABEL_KEY,labelDraft._state)}
 function removeLabelDraft(){labelDraft?.remove();labelDraft=null;try{localStorage.removeItem(LABEL_KEY)}catch{}emit('rist:worldbuilder-label-draft-remove',{source:'device-keyboard'});refresh()}
 function commitLabel(){if(!labelDraft?._state)return;emit('rist:worldbuilder-label-commit',{...labelDraft._state,source:'device-keyboard',presentationDraft:true});announce('Label handoff sent to world writer')}

 function commandsFor(mode){
  const view=viewerState(),play=playbackState(),par=parallaxState(),access=accessState(),widgets=widgetVisibility(),selected=selectionCount(),locked=!!view.locked;
  switch(mode){
   case 'pixels':return[
    descriptor('1²','Smallest cell',setPixelFootprint,{active:tileFootprint()===1}),descriptor('Grid',view.grid===false?'Off':'On',toggleGrid,{active:view.grid!==false}),descriptor('Zoom −',`${Math.round(view.visibleCells||12)} squares`,()=>zoomBy(.9)),descriptor('Zoom +',`${Math.round(view.visibleCells||12)} squares`,()=>zoomBy(1.1)),descriptor('Center','Viewer',centerView),descriptor('Undo','Last action',()=>clickCommand('undo'),{disabled:!!commandButton('undo')?.disabled})
   ];
   case 'tiles':return[
    descriptor('Library','Tile assets',()=>openLibrary(false),{wide:true}),descriptor(`${tileFootprint()}²`,'Tile size',cycleTileSize),descriptor('Grid',view.grid===false?'Off':'On',toggleGrid,{active:view.grid!==false}),descriptor('Target',`${selected} selected`,()=>setMode('target'),{disabled:selected<1}),descriptor('Undo','Last action',()=>clickCommand('undo'),{disabled:!!commandButton('undo')?.disabled}),descriptor('Remove',`${selected} selected`,()=>clickCommand('remove'),{disabled:selected<1,danger:true})
   ];
   case 'sprites':return[
    descriptor('Sprite Library','Animated assets',()=>openLibrary(true),{wide:true}),descriptor('Play / Pause',play.state||'playing',togglePlayback,{active:play.state==='playing'}),descriptor('Stop','Sprites',stopPlayback),descriptor('FPS',String(play.fps||12),cycleFps),descriptor('Perspective',access.reduced?'Reduced motion':par.active?'On':'Off',togglePerspective,{active:par.active,disabled:access.reduced}),descriptor(`${tileFootprint()}²`,'Tile size',cycleTileSize)
   ];
   case 'labels':return[];
   case 'viewer':return[
    descriptor('←','Pan west',()=>nudge('x',-1),{disabled:locked}),descriptor('↑','Pan north',()=>nudge('y',-1),{disabled:locked}),descriptor('↓','Pan south',()=>nudge('y',1),{disabled:locked}),descriptor('→','Pan east',()=>nudge('x',1),{disabled:locked}),descriptor('Zoom −','Camera',()=>zoomBy(.9)),descriptor('Zoom +','Camera',()=>zoomBy(1.1)),descriptor('Auto','Fit device',autoZoom),descriptor('Center','0,0',centerView),descriptor('Grid',view.grid===false?'Off':'On',toggleGrid,{active:view.grid!==false}),descriptor('Lock',locked?'Locked':'Unlocked',toggleLock,{active:locked}),descriptor('Layer −','Depth',()=>stepDepth('layer',-1),{disabled:locked}),descriptor('Layer +','Depth',()=>stepDepth('layer',1),{disabled:locked}),descriptor('Tier −','Depth',()=>stepDepth('tier',-1),{disabled:locked}),descriptor('Tier +','Depth',()=>stepDepth('tier',1),{disabled:locked}),descriptor('Perspective',par.active?'On':'Off',togglePerspective,{active:par.active,disabled:access.reduced})
   ];
   case 'litch':{const s=toolState.litch;return[
    descriptor('Light Peg','Place light',()=>toolEvent('litch',{tool:'light-peg'}),{active:s.tool==='light-peg'}),descriptor('Mag Sketch','Analog trace',()=>toolEvent('litch',{tool:'magnetic-sketch'}),{active:s.tool==='magnetic-sketch',wide:true}),descriptor('Intensity −',`${s.intensity}%`,()=>toolEvent('litch',{intensity:Math.max(0,s.intensity-10)})),descriptor('Intensity +',`${s.intensity}%`,()=>toolEvent('litch',{intensity:Math.min(100,s.intensity+10)})),descriptor('Radius −',`${s.radius} cells`,()=>toolEvent('litch',{radius:Math.max(1,s.radius-1)})),descriptor('Radius +',`${s.radius} cells`,()=>toolEvent('litch',{radius:Math.min(20,s.radius+1)})),descriptor('Erase','Litch marks',()=>toolEvent('litch',{tool:'erase'}))
   ]}
   case 'cad':{const s=toolState.cad;return['line','rect','circle','arc','measure','offset','rotate','mirror','elevation','slope'].map(name=>descriptor(name[0].toUpperCase()+name.slice(1),'CAD tool',()=>toolEvent('cad',{tool:name}),{active:s.tool===name})).concat([descriptor('Snap',s.snap?'On':'Off',()=>toolEvent('cad',{snap:!s.snap}),{active:s.snap})])}
   case 'stylus':{const s=toolState.stylus;return[
    ...['visual','terrain','select','annotation','effect'].map(name=>descriptor(name[0].toUpperCase()+name.slice(1),'Stroke meaning',()=>toolEvent('stylus',{tool:name}),{active:s.tool===name})),descriptor('Width −',`${s.width}px`,()=>toolEvent('stylus',{width:Math.max(1,s.width-1)})),descriptor('Width +',`${s.width}px`,()=>toolEvent('stylus',{width:Math.min(64,s.width+1)})),descriptor('Pressure',s.pressure?'On':'Off',()=>toolEvent('stylus',{pressure:!s.pressure}),{active:s.pressure}),descriptor('Erase','Stroke',()=>toolEvent('stylus',{tool:'erase'}))
   ]}
   case 'tethers':{const s=toolState.tethers;return[
    ...['sound','light','vibration','temperature','atmosphere','movement','rules'].map(name=>descriptor(name[0].toUpperCase()+name.slice(1),'Tether domain',()=>toolEvent('tethers',{domain:name}),{active:s.domain===name})),descriptor('Strength −',`${s.strength}%`,()=>toolEvent('tethers',{strength:Math.max(0,s.strength-10)})),descriptor('Strength +',`${s.strength}%`,()=>toolEvent('tethers',{strength:Math.min(100,s.strength+10)})),descriptor('Range −',`${s.range} cells`,()=>toolEvent('tethers',{range:Math.max(0,s.range-1)})),descriptor('Range +',`${s.range} cells`,()=>toolEvent('tethers',{range:Math.min(99,s.range+1)})),descriptor('Direction',s.direction,()=>toolEvent('tethers',{direction:s.direction==='omni'?'directed':'omni'}))
   ]}
   case 'metadata':return[];
   case 'target':return[
    descriptor('Rotate','90°',()=>clickCommand('rotate'),{disabled:selected<1}),descriptor('Resize',`To ${tileFootprint()}²`,()=>clickCommand('resize'),{disabled:selected<1}),descriptor('Tile Size',`${tileFootprint()}²`,cycleTileSize,{disabled:selected<1}),descriptor('Layer −','Selected depth',()=>stepDepth('layer',-1),{disabled:selected<1||locked}),descriptor('Layer +','Selected depth',()=>stepDepth('layer',1),{disabled:selected<1||locked}),descriptor('Tier −','Selected tier',()=>stepDepth('tier',-1),{disabled:selected<1||locked}),descriptor('Tier +','Selected tier',()=>stepDepth('tier',1),{disabled:selected<1||locked}),descriptor('Metadata','Coming Soon',()=>{}, {disabled:true,comingSoon:true}),descriptor('Tethers','Coming Soon',()=>{}, {disabled:true,comingSoon:true}),descriptor('Undo','Last action',()=>clickCommand('undo'),{disabled:!!commandButton('undo')?.disabled}),descriptor('Remove',`${selected} selected`,()=>clickCommand('remove'),{disabled:selected<1,danger:true})
   ];
   case 'widgets':return[
    descriptor('Time',widgets.clock?'Shown':'Hidden',()=>toggleWidget('clock'),{active:widgets.clock}),descriptor('Date',widgets.date?'Shown':'Hidden',()=>toggleWidget('date'),{active:widgets.date}),descriptor('Weather','Coming Soon',()=>{}, {disabled:true,comingSoon:true}),descriptor('Viewer',widgets.coords?'Shown':'Hidden',()=>toggleWidget('coords'),{active:widgets.coords}),descriptor('←',`Move ${selectedWidget}`,()=>moveWidget(selectedWidget,-12,0)),descriptor('↑',`Move ${selectedWidget}`,()=>moveWidget(selectedWidget,0,-12)),descriptor('↓',`Move ${selectedWidget}`,()=>moveWidget(selectedWidget,0,12)),descriptor('→',`Move ${selectedWidget}`,()=>moveWidget(selectedWidget,12,0)),descriptor('Reset','Widget positions',resetWidgets)
   ];
   case 'access':return[
    descriptor('Large Keys',access.large?'On':'Off',()=>toggleAccess('large'),{active:access.large}),descriptor('Contrast',access.contrast?'High':'Normal',()=>toggleAccess('contrast'),{active:access.contrast}),descriptor('Reduce Motion',access.reduced?'On':'Off',()=>toggleAccess('reduced'),{active:access.reduced}),descriptor('Description',descriptionOnly()?'Text map':'Visual map',toggleDescription,{active:descriptionOnly()}),descriptor('Widgets','Overlay controls',()=>setMode('widgets')),descriptor('Viewer','Camera controls',()=>setMode('viewer'))
   ];
   case 'file':return[
    descriptor('Save','World',save,{wide:true}),descriptor('Load','Saved / published',load,{wide:true}),descriptor('Publish','To region',publish,{wide:true}),descriptor('Menu','Shaelvien',openMenu,{wide:true})
   ];
   default:return[];
  }
 }

 function makeKey(item){
  const button=document.createElement('button');button.type='button';button.className='wb-device-key';if(item.active)button.classList.add('active');if(item.danger)button.classList.add('danger');if(item.modifier)button.classList.add('modifier');if(item.wide)button.classList.add('wide');if(item.full)button.classList.add('full');button.disabled=!!item.disabled;button.dataset.accessRole='keyboard-key';button.setAttribute('aria-label',item.sub?`${item.label}. ${item.sub}`:item.label);
  if(item.comingSoon){button.classList.add('coming-soon');button.setAttribute('title','Coming Soon');button.setAttribute('aria-label',`${item.label}. Coming Soon`)}
  const strong=document.createElement('strong');strong.textContent=item.label;button.appendChild(strong);if(item.sub){const small=document.createElement('small');small.textContent=item.sub;button.appendChild(small)}button.addEventListener('click',()=>item.action?.());return button
 }
 function renderLabelEditor(){
  const editor=document.createElement('div');editor.className='wb-device-inline-editor';
  const input=document.createElement('input');input.type='text';input.enterKeyHint='done';input.autocapitalize='words';input.placeholder='Type a label…';input.setAttribute('aria-label','Label text');input.value=labelDraft?._state?.text||'';
  const done=document.createElement('button');done.type='button';done.textContent=labelDraft?'Update':'Return';done.setAttribute('aria-label',labelDraft?'Update label text':'Create label draft');
  const submit=()=>{const text=input.value.trim();if(!text)return;if(labelDraft){labelDraft.textContent=text;labelDraft._state.text=text;labelDraft.setAttribute('aria-label',`Label draft: ${text}. Drag to place or use arrow keys.`);saveLabelDraft();emit('rist:worldbuilder-label-draft',{...labelDraft._state,source:'device-keyboard'})}else createLabelDraft(text);input.blur();refresh()};
  done.addEventListener('click',submit);input.addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();submit()}});editor.append(input,done);keysNode.appendChild(editor);
  const state=labelDraft?._state;[
   descriptor('Bold',state?.bold?'On':'Off',()=>styleLabel({bold:!labelDraft._state.bold}),{active:!!state?.bold,disabled:!state}),descriptor('Italic',state?.italic?'On':'Off',()=>styleLabel({italic:!labelDraft._state.italic}),{active:!!state?.italic,disabled:!state}),descriptor('Size −',state?`${state.size}px`:'—',()=>styleLabel({size:Math.max(8,labelDraft._state.size-2)}),{disabled:!state}),descriptor('Size +',state?`${state.size}px`:'—',()=>styleLabel({size:Math.min(96,labelDraft._state.size+2)}),{disabled:!state}),descriptor('Outline',state?.outline?'On':'Off',()=>styleLabel({outline:!labelDraft._state.outline}),{active:!!state?.outline,disabled:!state}),descriptor('←','Move label',()=>moveLabel(-8,0),{disabled:!state}),descriptor('↑','Move label',()=>moveLabel(0,-8),{disabled:!state}),descriptor('↓','Move label',()=>moveLabel(0,8),{disabled:!state}),descriptor('→','Move label',()=>moveLabel(8,0),{disabled:!state}),descriptor('Commit','Coming Soon',()=>{}, {disabled:true,comingSoon:true,wide:true}),descriptor('Remove','Draft',removeLabelDraft,{disabled:!state,danger:true})
  ].forEach(item=>keysNode.appendChild(makeKey(item)))
 }
 function renderMetadataEditor(){
  const selected=selectionCount();
  const editor=document.createElement('div');editor.className='wb-device-inline-editor';
  const select=document.createElement('select');select.setAttribute('aria-label','Metadata property');['keywords','secret notes','trap mechanics','slope mechanics','movement','TTRPG rules'].forEach(label=>{const option=document.createElement('option');option.value=label.replace(/ /g,'-');option.textContent=label;select.appendChild(option)});select.value=toolState.metadata.field;
  const apply=document.createElement('button');apply.type='button';apply.textContent='Edit';apply.disabled=selected<1;apply.setAttribute('aria-label','Edit selected tile metadata property');editor.append(select,apply);keysNode.appendChild(editor);
  const valueEditor=document.createElement('div');valueEditor.className='wb-device-inline-editor';const input=document.createElement('input');input.type='text';input.placeholder='Property value…';input.setAttribute('aria-label','Metadata value');input.value=toolState.metadata.value||'';const saveButton=document.createElement('button');saveButton.type='button';saveButton.textContent='Apply';saveButton.disabled=selected<1;valueEditor.append(input,saveButton);keysNode.appendChild(valueEditor);
  const applyValue=()=>{toolState.metadata={field:select.value,value:input.value};emit('rist:worldbuilder-metadata-edit',{...toolState.metadata,selectedCount:selected,source:'device-keyboard'});announce(`${select.options[select.selectedIndex]?.textContent||select.value} metadata edit sent for ${selected} selected tile${selected===1?'':'s'}`)};
  apply.addEventListener('click',()=>{input.focus();announce(`Editing ${select.options[select.selectedIndex]?.textContent||select.value}`)});saveButton.addEventListener('click',applyValue);input.addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();applyValue();input.blur()}});
  select.addEventListener('change',()=>{toolState.metadata.field=select.value;emit('rist:worldbuilder-metadata-request',{field:select.value,selectedCount:selected,source:'device-keyboard'})});
  [descriptor('Keywords','Search terms',()=>{select.value='keywords';select.dispatchEvent(new Event('change'));input.focus()},{disabled:selected<1}),descriptor('Secrets','GM notes',()=>{select.value='secret-notes';select.dispatchEvent(new Event('change'));input.focus()},{disabled:selected<1}),descriptor('Trap','Mechanics',()=>{select.value='trap-mechanics';select.dispatchEvent(new Event('change'));input.focus()},{disabled:selected<1}),descriptor('Slope','Terrain',()=>{select.value='slope-mechanics';select.dispatchEvent(new Event('change'));input.focus()},{disabled:selected<1}),descriptor('Movement','Traversal',()=>{select.value='movement';select.dispatchEvent(new Event('change'));input.focus()},{disabled:selected<1}),descriptor('Rules','TTRPG',()=>{select.value='TTRPG-rules';select.dispatchEvent(new Event('change'));input.focus()},{disabled:selected<1})].forEach(item=>keysNode.appendChild(makeKey(item)))
 }
 function renderKeys(){
  if(!keysNode||!root)return;keysNode.replaceChildren();const mode=currentMode();
  if(mode==='labels'){renderLabelEditor();return}
  if(mode==='metadata'){renderMetadataEditor();return}
  commandsFor(mode).forEach(item=>keysNode.appendChild(makeKey(item)))
 }
 function currentMode(){const mode=read(MODE_KEY,'tiles');return MODES.includes(mode)&&!COMING_SOON_MODES.has(mode)?mode:'tiles'}
 function setMode(mode){if(!MODES.includes(mode))return;if(COMING_SOON_MODES.has(mode)){announce(`${MODE_LABELS[mode]} keyboard coming soon`);return}write(MODE_KEY,mode);if(modeName)modeName.textContent=`${MODE_LABELS[mode]} keyboard`;modeRow?.querySelectorAll('.wb-device-mode').forEach(button=>{const on=button.dataset.mode===mode;button.setAttribute('aria-selected',on?'true':'false');button.classList.toggle('active',on)});renderKeys();announce(`${MODE_LABELS[mode]} keyboard`)}
 function renderModes(){modeRow.replaceChildren();for(const mode of MODES){const button=document.createElement('button');button.type='button';button.className='wb-device-mode';button.dataset.mode=mode;button.textContent=MODE_LABELS[mode];button.setAttribute('role','tab');const comingSoon=COMING_SOON_MODES.has(mode);if(comingSoon){button.classList.add('coming-soon');button.disabled=true;button.setAttribute('aria-disabled','true');button.setAttribute('title','Coming Soon');button.setAttribute('aria-label',`${MODE_LABELS[mode]} keyboard. Coming Soon`)}else{button.setAttribute('aria-label',`${MODE_LABELS[mode]} keyboard`);button.addEventListener('click',()=>setMode(mode))}modeRow.appendChild(button)}setMode(currentMode())}
 function setCollapsed(collapsed){if(!root||!keyboard)return;root.classList.toggle('wb-device-collapsed',collapsed);write(COLLAPSE_KEY,collapsed);keyboard.querySelector('.wb-device-collapse')?.setAttribute('aria-expanded',collapsed?'false':'true');const button=keyboard.querySelector('.wb-device-collapse');if(button){button.textContent=collapsed?'⌃':'⌄';button.setAttribute('aria-label',collapsed?'Expand World Builder keyboard':'Collapse World Builder keyboard')}setTimeout(positionWidgets,0)}
 function refresh(){if(!root?.isConnected)return;applyAccess();renderKeys();tickWidgets()}

 function semanticTranslation(node){
  if(!(node instanceof Element))return null;
  const rect=node.getBoundingClientRect();const role=node.getAttribute('role')||node.tagName.toLowerCase();const name=node.getAttribute('aria-label')||node.getAttribute('title')||node.textContent?.trim().replace(/\s+/g,' ').slice(0,120)||role;const state={disabled:node.matches(':disabled'),pressed:node.getAttribute('aria-pressed'),selected:node.getAttribute('aria-selected'),hidden:node.hidden||getComputedStyle(node).display==='none'};const actions=[];if(node instanceof HTMLButtonElement)actions.push('activate');if(node.classList.contains('wb-viewer-widget')||node.classList.contains('wb-world-label-draft'))actions.push('move with drag','move with arrow keys');return{role,accessibleName:name,accessibleDescription:node.getAttribute('aria-description')||'',currentValue:node.getAttribute('aria-valuenow')||'',state,availableActions:actions,spatialRelation:{left:Math.round(rect.left),top:Math.round(rect.top),width:Math.round(rect.width),height:Math.round(rect.height)},changeAnnouncement:liveNode?.textContent||'',alternatePresentation:node.classList.contains('wb-viewer-widget')?'Keyboard movement and screen-reader label available':'Keyboard/touch activation available'}
 }
 function annotateExistingLayout(){
  if(!root)return;root.querySelectorAll('button,.quick-slot,.studio-load-panel,.studio-mini-panel').forEach(node=>{if(!node.getAttribute('aria-label')&&!node.getAttribute('aria-labelledby')){const text=node.textContent?.trim().replace(/\s+/g,' ');if(text)node.setAttribute('aria-label',text.slice(0,160))}node.dataset.accessTranslation='available'})
 }

 function build(host){
  root=host;ensureStyle();applyAccess();
  root.querySelectorAll('.wb-device-keyboard').forEach(node=>node.remove());
  keyboard=document.createElement('section');keyboard.className=`wb-device-keyboard ${isIos()?'wb-device-ios':isAndroid()?'wb-device-android':'wb-device-desktop'}`;keyboard.setAttribute('role','application');keyboard.setAttribute('aria-label','World Builder device keyboard');
  const grabRow=document.createElement('div');grabRow.className='wb-device-grabber-row';
  const menu=document.createElement('button');menu.type='button';menu.className='wb-device-menu';menu.textContent='⌂';menu.setAttribute('aria-label','Open Shaelvien menu');menu.addEventListener('click',openMenu);
  modeName=document.createElement('div');modeName.className='wb-device-mode-name';modeName.textContent='World Builder keyboard';
  const collapse=document.createElement('button');collapse.type='button';collapse.className='wb-device-collapse';collapse.addEventListener('click',()=>setCollapsed(!root.classList.contains('wb-device-collapsed')));
  const grabber=document.createElement('button');grabber.type='button';grabber.className='wb-device-grabber';grabber.setAttribute('aria-label','Toggle World Builder keyboard');grabber.addEventListener('click',()=>setCollapsed(!root.classList.contains('wb-device-collapsed')));modeName.addEventListener('dblclick',()=>setCollapsed(!root.classList.contains('wb-device-collapsed')));
  grabRow.append(menu,modeName,collapse);
  modeRow=document.createElement('div');modeRow.className='wb-device-mode-row';modeRow.setAttribute('role','tablist');modeRow.setAttribute('aria-label','World Builder keyboards');
  keysNode=document.createElement('div');keysNode.className='wb-device-keys';keysNode.setAttribute('role','group');keysNode.setAttribute('aria-label','Keys for selected World Builder keyboard');
  liveNode=document.createElement('div');liveNode.className='wb-device-live-region';liveNode.setAttribute('role','status');liveNode.setAttribute('aria-live','polite');liveNode.setAttribute('aria-atomic','true');
  keyboard.append(grabRow,grabber,modeRow,keysNode,liveNode);root.appendChild(keyboard);
  renderModes();setCollapsed(read(COLLAPSE_KEY,'false')==='true');buildWidgets();restoreLabelDraft();annotateExistingLayout();
  if(timer)clearInterval(timer);timer=setInterval(tickWidgets,1000);
  window.addEventListener('resize',positionWidgets,{passive:true});
 }
 function mount(){const host=studio();if(!host)return;if(host===root&&keyboard?.isConnected&&widgetLayer?.isConnected)return;build(host)}

 window.addEventListener('rist:weather-state',event=>setWeather(event.detail||{}));
 window.addEventListener('rist:viewer-state',()=>{tickWidgets();if(currentMode()==='viewer')renderKeys()});
 window.addEventListener('rist-sprite-playback',()=>{if(currentMode()==='sprites')renderKeys()});
 window.addEventListener('rist-parallax-settings',()=>{if(currentMode()==='viewer'||currentMode()==='sprites')renderKeys()});
 document.addEventListener('keydown',event=>{
  if(!root?.isConnected)return;const target=event.target;const typing=target instanceof HTMLInputElement||target instanceof HTMLTextAreaElement||target instanceof HTMLSelectElement||target?.isContentEditable;if(typing)return;
  if(event.key==='Escape'&&!root.classList.contains('wb-device-collapsed')){setCollapsed(true);event.preventDefault();return}
  if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='s'){event.preventDefault();save();return}
  if(event.key==='Delete'&&selectionCount()>0){event.preventDefault();clickCommand('remove');return}
 });

 window.RistWorldBuilderDeviceShell={
  setMode,
  collapse:()=>setCollapsed(true),
  expand:()=>setCollapsed(false),
  showWidget:name=>{const state=widgetVisibility();if(name in widgetDefaults){state[name]=true;saveWidgetVisibility(state);applyWidgetVisibility();selectWidget(name);refresh()}},
  hideWidget:name=>{const state=widgetVisibility();if(name in widgetDefaults){state[name]=false;saveWidgetVisibility(state);applyWidgetVisibility();refresh()}},
  setWeather,
  describeLayoutBox:semanticTranslation,
  describeVisibleLayout:()=>[...root.querySelectorAll('button,input,select,textarea,.wb-viewer-widget,.wb-world-label-draft')].filter(node=>{const style=getComputedStyle(node);return style.display!=='none'&&style.visibility!=='hidden'}).map(semanticTranslation),
  getState:()=>({mode:currentMode(),collapsed:root?.classList.contains('wb-device-collapsed')===true,widgets:widgetVisibility(),selectedWidget,toolState:structuredClone?structuredClone(toolState):JSON.parse(JSON.stringify(toolState))})
 };

 ensureStyle();mount();pageObserver=new MutationObserver(()=>mount());pageObserver.observe(document.documentElement,{childList:true,subtree:true});
})();
