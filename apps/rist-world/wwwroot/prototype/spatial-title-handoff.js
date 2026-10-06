(() => {
'use strict';

const query=new URLSearchParams(location.search);
if(window.parent===window||query.get('live-worldbuilder')!=='1'||String(query.get('mode')||'worldbuilder').toLowerCase()==='regiondefiner')return;

const baseApi=window.ShaelvienPrototype;
const WORLD_GRID_COLUMNS=300;
const WORLD_GRID_ROWS=300;
let pending=null;
let mapSelectionAnchor=null;
let selectorControlState=null;

const pause=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const clamp=(value,min,max)=>Math.min(max,Math.max(min,value));
const selectedCells=snapshot=>Array.isArray(snapshot?.selectedCells)?snapshot.selectedCells:[];

function live(message){
  const node=document.getElementById('live');
  if(node)node.textContent=String(message||'');
}

function selectorOverlay(){return document.querySelector('.spatial-selection-grid')}
function worldNode(){return document.getElementById('world')}
function stageNode(){return document.getElementById('stage')}

function visibleMapLayers(snapshot){
  const world=worldNode();
  if(!world)return{
    tiers:Array.isArray(snapshot?.visibleTierIndices)?snapshot.visibleTierIndices:[],
    layers:Array.isArray(snapshot?.visibleLayerOffsets)?snapshot.visibleLayerOffsets:[]
  };
  const tiers=new Set(),layers=new Set();
  for(const node of world.querySelectorAll('[data-tier][data-layer]')){
    if(node.classList.contains('spatial-selection-grid'))continue;
    const style=getComputedStyle(node);
    if(node.hidden||style.display==='none'||style.visibility==='hidden'||Number(style.opacity||1)<=.001)continue;
    const tier=Number(node.dataset.tier),layer=Number(node.dataset.layer);
    if(Number.isInteger(tier)&&tier>=0)tiers.add(tier);
    if(Number.isInteger(layer)&&layer>=0&&layer<=9)layers.add(layer);
  }
  return{
    tiers:tiers.size?[...tiers].sort((a,b)=>a-b):(Array.isArray(snapshot?.visibleTierIndices)?snapshot.visibleTierIndices:[]),
    layers:layers.size?[...layers].sort((a,b)=>a-b):(Array.isArray(snapshot?.visibleLayerOffsets)?snapshot.visibleLayerOffsets:[])
  };
}

function localSelectionBounds(snapshot){
  const cells=selectedCells(snapshot);
  if(!cells.length)return null;
  const columns=Math.max(1,Number(snapshot?.columns)||30),rows=Math.max(1,Number(snapshot?.rows)||30);
  const shape=String(snapshot?.gridShape||'hex').toLowerCase()==='square'?'square':'hex';
  const viewWidth=shape==='hex'?columns+.5:columns;
  let minX=1,minY=1,maxX=0,maxY=0;
  for(const raw of cells){
    const cell=clamp(Math.trunc(Number(raw)||0),0,(columns*rows)-1);
    const row=Math.floor(cell/columns),column=cell%columns,offset=shape==='hex'&&(row%2)?0.5:0;
    minX=Math.min(minX,(column+offset)/viewWidth);
    maxX=Math.max(maxX,(column+offset+1)/viewWidth);
    minY=Math.min(minY,row/rows);
    maxY=Math.max(maxY,(row+1)/rows);
  }
  return{minX:clamp(minX,0,1),minY:clamp(minY,0,1),maxX:clamp(maxX,0,1),maxY:clamp(maxY,0,1)};
}

function freezeSelectionSnapshot(raw){
  if(!raw||typeof raw!=='object')return null;
  const layers=visibleMapLayers(raw);
  return{
    ...raw,
    viewMinX:clamp(Number(raw.viewMinX)||0,0,1),
    viewMinY:clamp(Number(raw.viewMinY)||0,0,1),
    viewMaxX:clamp(Number(raw.viewMaxX)||1,0,1),
    viewMaxY:clamp(Number(raw.viewMaxY)||1,0,1),
    scope:String(raw.scope||'WORLD').toUpperCase(),
    zoomRatio:Math.max(1,Number(raw.zoomRatio)||1),
    viewAngle:Math.max(0,Number(raw.viewAngle)||0),
    tierIndex:Math.max(0,Math.trunc(Number(raw.tierIndex)||0)),
    visibleTierIndices:layers.tiers,
    visibleLayerOffsets:layers.layers,
    parentSpatialNodeId:String(raw.parentSpatialNodeId||''),
    spatialPath:String(raw.spatialPath||'')
  };
}

function anchoredSnapshot(){
  const raw=baseApi?.getSpatialSelection?.();
  const anchor=mapSelectionAnchor;
  if(!raw||!anchor)return raw;
  const cells=selectedCells(raw),columns=Math.max(1,Number(raw.columns)||30),rows=Math.max(1,Number(raw.rows)||30);
  const shape=String(raw.gridShape||'hex').toLowerCase()==='square'?'square':'hex';
  const viewWidth=shape==='hex'?columns+.5:columns;
  const mapPoint=(lx,ly)=>({
    x:anchor.viewMinX+(clamp(lx,0,1)*(anchor.viewMaxX-anchor.viewMinX)),
    y:anchor.viewMinY+(clamp(ly,0,1)*(anchor.viewMaxY-anchor.viewMinY))
  });
  const local=localSelectionBounds(raw);
  const bounds=local?{
    a:mapPoint(local.minX,local.minY),
    b:mapPoint(local.maxX,local.maxY)
  }:{a:{x:anchor.viewMinX,y:anchor.viewMinY},b:{x:anchor.viewMaxX,y:anchor.viewMaxY}};
  const canonicalCells=[...new Set(cells.map(rawCell=>{
    const cell=clamp(Math.trunc(Number(rawCell)||0),0,(columns*rows)-1);
    const row=Math.floor(cell/columns),column=cell%columns,offset=shape==='hex'&&(row%2)?0.5:0;
    const p=mapPoint((column+offset+.5)/viewWidth,(row+.5)/rows);
    const x=clamp(Math.floor(p.x*WORLD_GRID_COLUMNS),0,WORLD_GRID_COLUMNS-1);
    const y=clamp(Math.floor(p.y*WORLD_GRID_ROWS),0,WORLD_GRID_ROWS-1);
    return(y*WORLD_GRID_COLUMNS)+x;
  }))].sort((a,b)=>a-b);
  return{
    ...raw,
    canonicalCells,
    scope:anchor.scope,
    zoomRatio:anchor.zoomRatio,
    viewAngle:anchor.viewAngle,
    viewMinX:anchor.viewMinX,
    viewMinY:anchor.viewMinY,
    viewMaxX:anchor.viewMaxX,
    viewMaxY:anchor.viewMaxY,
    canonicalMinX:bounds.a.x,
    canonicalMinY:bounds.a.y,
    canonicalMaxX:bounds.b.x,
    canonicalMaxY:bounds.b.y,
    tierIndex:anchor.tierIndex,
    visibleTierIndices:[...anchor.visibleTierIndices],
    visibleLayerOffsets:[...anchor.visibleLayerOffsets],
    parentSpatialNodeId:anchor.parentSpatialNodeId,
    spatialPath:anchor.spatialPath
  };
}

function lockSelectorControls(){
  if(selectorControlState)return;
  const ids=['zoomIn','zoomOut','fit','settingsFit','tierToggle'];
  selectorControlState=ids.map(id=>{
    const node=document.getElementById(id);
    if(!node)return null;
    const state={node,disabled:!!node.disabled,ariaDisabled:node.getAttribute('aria-disabled')};
    node.disabled=true;node.setAttribute('aria-disabled','true');
    return state;
  }).filter(Boolean);
}

function unlockSelectorControls(){
  for(const state of selectorControlState||[]){
    state.node.disabled=state.disabled;
    if(state.ariaDisabled===null)state.node.removeAttribute('aria-disabled');
    else state.node.setAttribute('aria-disabled',state.ariaDisabled);
  }
  selectorControlState=null;
}

function anchorSelectorToMap(){
  const overlay=selectorOverlay(),world=worldNode(),anchor=mapSelectionAnchor;
  if(!overlay||!world||!anchor)return false;
  if(overlay.parentElement!==world)world.appendChild(overlay);
  const width=Math.max(.000001,anchor.viewMaxX-anchor.viewMinX),height=Math.max(.000001,anchor.viewMaxY-anchor.viewMinY);
  Object.assign(overlay.style,{
    inset:'auto',
    left:`${anchor.viewMinX*100}%`,
    top:`${anchor.viewMinY*100}%`,
    width:`${width*100}%`,
    height:`${height*100}%`
  });
  overlay.dataset.coordinateSpace='world-map';
  overlay.dataset.visibleTiers=anchor.visibleTierIndices.join(',');
  overlay.dataset.visibleLayers=anchor.visibleLayerOffsets.join(',');
  return true;
}

function releaseSelectorFromMap(){
  const overlay=selectorOverlay(),stage=stageNode();
  if(overlay&&stage&&overlay.parentElement!==stage)stage.appendChild(overlay);
  if(overlay){
    Object.assign(overlay.style,{inset:'0',left:'',top:'',width:'',height:''});
    delete overlay.dataset.coordinateSpace;
    delete overlay.dataset.visibleTiers;
    delete overlay.dataset.visibleLayers;
  }
  unlockSelectorControls();
}

function beginMapSelection(raw={}){
  const started=baseApi?.beginSpatialSelection?.(raw);
  if(!started)return started;
  const initial=baseApi.getSpatialSelection?.();
  mapSelectionAnchor=freezeSelectionSnapshot(initial);
  lockSelectorControls();
  requestAnimationFrame(()=>{
    anchorSelectorToMap();
    live('Select hexes on the visible map layers. The camera is only a lens and is locked until this selection is named or cancelled.');
  });
  return started;
}

function finishMapSelection(focus=true){
  const result=baseApi?.finishSpatialSelection?.(focus);
  releaseSelectorFromMap();
  mapSelectionAnchor=null;
  return result;
}

function cancelMapSelection(){
  const result=baseApi?.cancelSpatialSelection?.();
  releaseSelectorFromMap();
  mapSelectionAnchor=null;
  return result;
}

if(baseApi){
  window.ShaelvienPrototype=Object.freeze({
    ...baseApi,
    beginSpatialSelection:beginMapSelection,
    getSpatialSelection:anchoredSnapshot,
    finishSpatialSelection:finishMapSelection,
    cancelSpatialSelection:cancelMapSelection
  });
}

function blockCameraMutationWhileSelecting(event){
  if(!mapSelectionAnchor)return;
  event.preventDefault();
  event.stopImmediatePropagation();
}
const stage=stageNode();
stage?.addEventListener('wheel',blockCameraMutationWhileSelecting,{capture:true,passive:false});

function selectionCenter(snapshot){
  const minX=Number.isFinite(Number(snapshot?.canonicalMinX))?Number(snapshot.canonicalMinX):.5;
  const minY=Number.isFinite(Number(snapshot?.canonicalMinY))?Number(snapshot.canonicalMinY):.5;
  const maxX=Number.isFinite(Number(snapshot?.canonicalMaxX))?Number(snapshot.canonicalMaxX):minX;
  const maxY=Number.isFinite(Number(snapshot?.canonicalMaxY))?Number(snapshot.canonicalMaxY):minY;
  return{x:clamp((minX+maxX)/2,0,1),y:clamp((minY+maxY)/2,0,1)};
}

function createDraftTitle(snapshot){
  const world=worldNode();
  if(!world)return null;
  document.querySelectorAll('[data-spatial-title-draft="true"]').forEach(node=>node.remove());
  const plane=document.getElementById('surfacePlane');
  const width=Math.max(1,Number(plane?.naturalWidth)||Number(world.scrollWidth)||2048);
  const height=Math.max(1,Number(plane?.naturalHeight)||Number(world.scrollHeight)||2048);
  const center=selectionCenter(snapshot);
  const node=document.createElement('div');
  node.className='user-image-placement user-label-placement spatial-title-draft';
  node.dataset.spatialTitleDraft='true';
  node.setAttribute('role','status');
  node.setAttribute('aria-live','polite');
  Object.assign(node.style,{
    position:'absolute',
    left:`${center.x*width}px`,
    top:`${center.y*height}px`,
    transform:'translate(-50%,-50%)',
    transformOrigin:'50% 50%',
    zIndex:'9999',
    pointerEvents:'none',
    minWidth:'180px',
    maxWidth:'70%',
    textAlign:'center',
    whiteSpace:'nowrap',
    overflow:'visible',
    font:'700 48px/1.1 system-ui,sans-serif',
    letterSpacing:'.02em',
    color:'#fff2c7',
    textShadow:'0 2px 5px #000,0 0 10px #000',
    opacity:'.72'
  });
  node.textContent='NAME';
  world.appendChild(node);
  return node;
}

function openLabelsComposer(){
  const keyboard=document.getElementById('viewerKeyboard');
  if(keyboard)keyboard.dataset.spatialTitle='active';
  const toggle=document.getElementById('keyboardToggle');
  if(keyboard?.hidden)toggle?.click();
  let labels=[...document.querySelectorAll('#keyboardTabs button')].find(button=>String(button.textContent||'').trim().toLowerCase()==='labels');
  if(labels&&!labels.classList.contains('active'))labels.click();
  labels=[...document.querySelectorAll('#keyboardTabs button')].find(button=>String(button.textContent||'').trim().toLowerCase()==='labels');
  if(labels&&!labels.classList.contains('active'))labels.click();
  return document.querySelector('#keyboardKeys .label-text-input');
}

function removePendingDraft(){
  if(!pending)return;
  pending.resolve?.('');
  const keyboard=document.getElementById('viewerKeyboard');
  if(keyboard)delete keyboard.dataset.spatialTitle;
  clearInterval(pending.pollId);
  if(pending.input&&pending.captureKeydown)pending.input.removeEventListener('keydown',pending.captureKeydown,true);
  if(pending.input&&pending.onInput)pending.input.removeEventListener('input',pending.onInput);
  pending.draft?.remove();
  pending=null;
}

async function commitTitleRepresentation(){
  const state=pending;
  if(!state||!state.awaitingSave)return;
  clearInterval(state.pollId);
  if(state.input&&state.captureKeydown)state.input.removeEventListener('keydown',state.captureKeydown,true);
  if(state.input&&state.onInput)state.input.removeEventListener('input',state.onInput);
  state.draft?.remove();

  const input=state.input?.isConnected?state.input:openLabelsComposer();
  if(!input){pending=null;live(`${state.name} saved, but the title editor could not reopen.`);return;}
  input.readOnly=false;
  input.removeAttribute('aria-busy');
  input.value=state.name;
  input.dispatchEvent(new Event('input',{bubbles:true}));
  input.dispatchEvent(new KeyboardEvent('keydown',{key:'Enter',code:'Enter',bubbles:true,cancelable:true}));
  pending=null;

  await pause(0);
  const editor=document.querySelector('#keyboardKeys .label-text-input');
  if(editor){
    editor.placeholder='Edit title text';
    editor.focus({preventScroll:true});
  }
  live(`${state.name} saved. Title selected; adjust font and position, then use World Builder Save when finished.`);
}

function watchForBoundarySave(){
  if(!pending)return;
  clearInterval(pending.pollId);
  pending.pollId=setInterval(()=>{
    if(!pending?.awaitingSave)return;
    const api=window.ShaelvienPrototype;
    const snapshot=typeof api?.getSpatialSelection==='function'?api.getSpatialSelection():null;
    if(snapshot?.active===false)void commitTitleRepresentation();
  },50);
}

function failTitleEntry(message){
  live(message);
  return Promise.resolve('');
}

function beginSpatialTitle(defaultValue=''){
  const api=window.ShaelvienPrototype;
  const snapshot=typeof api?.getSpatialSelection==='function'?api.getSpatialSelection():null;
  if(!snapshot||selectedCells(snapshot).length===0)return failTitleEntry('Select at least one map hex before naming this space.');

  removePendingDraft();
  const draft=createDraftTitle(snapshot);
  const input=openLabelsComposer();
  if(!draft||!input)return failTitleEntry('The text editor is unavailable. The area was not saved; no browser prompt was used.');

  input.value='';
  input.placeholder=snapshot.kind==='INSTANCE'?'Name this scene · Enter to save':'Name this area · Enter to save';
  input.setAttribute('aria-label',input.placeholder);
  input.readOnly=false;
  input.removeAttribute('aria-invalid');

  return new Promise(resolve=>{
    const onInput=()=>{
      const value=String(input.value||'');
      draft.textContent=value.trim()||'NAME';
      draft.style.opacity=value.trim()?'.96':'.72';
      draft.style.fontSize=`${Math.max(32,Math.min(64,48-(Math.max(0,value.length-18)*.6)))}px`;
      input.removeAttribute('aria-invalid');
    };
    const captureKeydown=event=>{
      if(event.key==='Enter'){
        event.preventDefault();
        event.stopImmediatePropagation();
        const name=String(input.value||'').trim();
        if(!name){
          input.setAttribute('aria-invalid','true');
          draft.textContent='NAME REQUIRED';
          draft.style.opacity='1';
          live('Enter a name before saving this space.');
          input.focus({preventScroll:true});
          return;
        }
        if(pending?.awaitingSave)return;
        pending.name=name;
        pending.awaitingSave=true;
        input.readOnly=true;
        input.setAttribute('aria-busy','true');
        draft.textContent=name;
        draft.style.opacity='1';
        live(`${name} ready. Saving spatial identity…`);
        watchForBoundarySave();
        resolve(name);
        return;
      }
      if(event.key==='Escape'){
        event.preventDefault();
        event.stopImmediatePropagation();
        removePendingDraft();
        resolve('');
      }
    };
    pending={snapshot,draft,input,onInput,captureKeydown,resolve,name:'',awaitingSave:false,pollId:0};
    input.addEventListener('input',onInput);
    input.addEventListener('keydown',captureKeydown,true);
    requestAnimationFrame(()=>{
      input.focus({preventScroll:true});
      input.setSelectionRange(0,input.value.length);
    });
    live('Text editor active. Enter the title shown over the selected map area, then press Enter to save.');
  });
}

// The parent module calls this view-only composer directly. Never replace a
// parent global with an iframe-realm function: Blazor's invocation resolver
// cannot reliably treat that function as a callable in the parent's realm.
window.RistSpatialTitle={request:beginSpatialTitle};
window.addEventListener('pagehide',()=>{
  removePendingDraft();
  releaseSelectorFromMap();
},{once:true});
})();
