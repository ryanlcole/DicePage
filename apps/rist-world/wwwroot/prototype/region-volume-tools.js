(()=>{
'use strict';

const Q=new URLSearchParams(location.search);
if(String(Q.get('mode')||'').toLowerCase()!=='regiondefiner')return;

const NEW_FLOW=String(Q.get('regionFlow')||'').toLowerCase()==='new';
const REQUESTED_REGION_ID=String(Q.get('regionId')||'');
const CLAIM_ONLY=String(Q.get('access')||'edit').toLowerCase()==='claim';
const MAX_HEIGHT=Math.max(1,Math.trunc(Number(Q.get('maxHeight'))||100));
const LAYERS_PER_TIER=10;
const DEFAULT_MAX_TIER=Math.max(0,Math.floor((MAX_HEIGHT-1)/LAYERS_PER_TIER));
const clamp=(value,min,max)=>Math.min(max,Math.max(min,value));
const sleep=ms=>new Promise(resolve=>setTimeout(resolve,ms));
const bootStarted=Date.now();

function boot(){
  const base=window.ShaelvienPrototype;
  const stage=document.getElementById('stage');
  const world=document.getElementById('world');
  if(!base||!stage||!world){
    if(Date.now()-bootStarted<5000)setTimeout(boot,40);
    return;
  }
  if(stage.dataset.regionVolumeV3==='true')return;
  stage.dataset.regionVolumeV3='true';
  stage.classList.add('region-volume-v3');

  const source='shaelvien-regiondefiner';
  const post=message=>{try{parent.postMessage({source,...message},location.origin)}catch{}};
  const live=document.getElementById('live');
  const announce=message=>{
    const text=String(message||'');
    if(live)live.textContent=text;
    post({type:'controller-state',state:getControllerState()});
  };

  const originalTransform=world.style.transform||'';
  const originalTransformOrigin=world.style.transformOrigin||'';
  const originalMask=world.style.maskImage||'';
  const originalWebkitMask=world.style.webkitMaskImage||'';

  const state={
    phase:NEW_FLOW?'xy':'existing',
    gridColumns:30,
    gridRows:30,
    bounds:null,
    dragOrigin:null,
    dragging:false,
    cursor:{x:.5,y:.5},
    cursorVisible:false,
    controllerAnchor:null,
    minTierIndex:0,
    maxTierIndex:0,
    maxTierIndexAllowed:DEFAULT_MAX_TIER,
    zCursor:0,
    regionName:'',
    regionId:REQUESTED_REGION_ID,
    regionRecord:null,
    pending:false,
    camera:null,
    angle:0,
    worldReady:false
  };

  const style=document.createElement('style');
  style.id='region-volume-v3-style';
  style.textContent=`
    .region-volume-v3 .region-tier-preview,
    .region-volume-v3 .region-definition-grid,
    .region-volume-v3 .region-selection-tools-panel:not(.region-volume-panel){display:none!important}
    .region-volume-panel{position:absolute;left:50%;top:10px;transform:translateX(-50%);z-index:95;width:min(95%,760px);box-sizing:border-box;padding:10px;border:1px solid rgba(236,196,93,.82);border-radius:13px;background:rgba(5,12,18,.9);box-shadow:0 8px 26px rgba(0,0,0,.42);color:#f4e6ba;font:700 11px/1.3 system-ui,sans-serif;letter-spacing:.06em;pointer-events:auto;backdrop-filter:blur(6px)}
    .region-volume-panel header{display:flex;align-items:center;justify-content:space-between;gap:10px;margin-bottom:8px}.region-volume-panel header strong{font-size:12px;color:#fff}.region-volume-panel header small{color:#8edcff}
    .region-volume-tools{display:flex;gap:7px;flex-wrap:wrap;align-items:end}.region-volume-fields{display:grid;grid-template-columns:repeat(4,minmax(74px,1fr));gap:7px;flex:1;min-width:280px}.region-volume-fields.z{grid-template-columns:repeat(2,minmax(90px,1fr));max-width:270px}.region-volume-fields label,.region-volume-name{display:flex;flex-direction:column;gap:4px;color:#9fd9f3;font-size:9px}.region-volume-fields input,.region-volume-name input{min-width:0;border:1px solid rgba(255,255,255,.28);border-radius:8px;padding:8px;background:#071219;color:white;font:800 12px system-ui,sans-serif}
    .region-volume-panel button{border:1px solid rgba(116,205,244,.55);border-radius:9px;background:rgba(11,31,43,.94);color:#e9f8ff;min-height:36px;padding:7px 11px;font:800 10px/1 system-ui,sans-serif;letter-spacing:.08em}.region-volume-panel button.region-primary{border-color:#f3ca63;color:#fff0b7;background:rgba(69,50,14,.92)}.region-volume-panel button.region-back{border-color:rgba(255,255,255,.3)}
    .region-volume-hint{margin:7px 0 0;color:#c7dbe4;font-weight:600;letter-spacing:.02em}.region-volume-summary{display:flex;gap:8px;flex-wrap:wrap;align-items:center;flex:1}.region-volume-summary span{padding:6px 8px;border:1px solid rgba(255,255,255,.18);border-radius:8px;background:rgba(0,0,0,.22);color:#fff}.region-volume-name{flex:1;min-width:210px}.region-volume-next{display:flex;gap:8px;flex-wrap:wrap}.region-volume-next b{color:#ffd86e}
    .region-volume-overlay{position:absolute;inset:0;z-index:72;width:100%;height:100%;touch-action:none;overflow:visible}.region-volume-overlay .bound-fill{fill:rgba(88,204,255,.09);stroke:#ffd66e;stroke-width:3;vector-effect:non-scaling-stroke}.region-volume-overlay .bound-guide{stroke:#7cdcff;stroke-width:1.6;stroke-dasharray:8 6;vector-effect:non-scaling-stroke}.region-volume-overlay .cursor{fill:#fff;stroke:#52d8ff;stroke-width:7;vector-effect:non-scaling-stroke;filter:drop-shadow(0 0 5px #36caff)}.region-volume-overlay .coord-label{fill:#fff7d2;font:800 18px system-ui,sans-serif;paint-order:stroke;stroke:#071219;stroke-width:5;stroke-linejoin:round}.region-volume-v3[data-region-volume-phase="z"] .region-volume-overlay,.region-volume-v3[data-region-volume-phase="save"] .region-volume-overlay,.region-volume-v3[data-region-volume-phase="saved"] .region-volume-overlay,.region-volume-v3[data-region-volume-phase="existing"] .region-volume-overlay{pointer-events:none}
    .region-volume-v3 .region-mode-reference{font-size:0}.region-volume-v3 .region-mode-reference::after{content:'REGION DEFINER · BOUNDED WORLD VOLUME';font-size:11px}
    @media(max-width:720px){.region-volume-panel{top:6px;width:97%;padding:7px}.region-volume-fields{grid-template-columns:repeat(2,minmax(72px,1fr));min-width:210px}.region-volume-panel button{min-height:33px;padding:6px 8px;font-size:9px}.region-volume-hint{font-size:9px}.region-volume-overlay .coord-label{font-size:14px}}
  `;
  document.head.appendChild(style);

  const overlay=document.createElementNS('http://www.w3.org/2000/svg','svg');
  overlay.classList.add('region-volume-overlay');
  overlay.setAttribute('viewBox','0 0 1000 1000');
  overlay.setAttribute('preserveAspectRatio','none');
  overlay.setAttribute('aria-label','Region X and Y coordinate boundary surface');
  stage.appendChild(overlay);

  const panel=document.createElement('section');
  panel.className='region-selection-tools-panel region-volume-panel';
  panel.setAttribute('aria-label','Region bounded volume tools');
  stage.appendChild(panel);

  function stripAngle(transform){return String(transform||'').replace(/\s*rotateX\([^)]*\)/gi,'').trim()}
  function clearWorldMask(){
    world.style.maskImage=originalMask||'none';
    world.style.webkitMaskImage=originalWebkitMask||'none';
    world.style.maskSize='';world.style.webkitMaskSize='';world.style.maskRepeat='';world.style.webkitMaskRepeat='';
    stage.classList.remove('region-cropped');delete stage.dataset.cropMode;
  }
  function worldDimensions(){return{width:Math.max(1,world.offsetWidth||parseFloat(world.style.width)||2048),height:Math.max(1,world.offsetHeight||parseFloat(world.style.height)||2048)}}
  function restoreTopDown(){
    state.camera=null;state.angle=0;
    world.style.transformOrigin=originalTransformOrigin||'0 0';
    world.style.transform=stripAngle(originalTransform);
    clearWorldMask();
    try{base.showAllParallax?.()}catch{}
    requestAnimationFrame(renderOverlay);
  }
  function fitBounds60(){
    if(!state.bounds)return;
    const box=state.bounds,rect=stage.getBoundingClientRect(),dims=worldDimensions(),angle=60,cos=Math.max(.15,Math.cos(angle*Math.PI/180));
    const focusW=Math.max(1,(box.maxX-box.minX)*dims.width),focusH=Math.max(1,(box.maxY-box.minY)*dims.height*cos);
    const scale=Math.max(.000001,Math.min(rect.width/focusW,rect.height/focusH)*.82);
    const centerX=((box.minX+box.maxX)/2)*dims.width,centerY=((box.minY+box.maxY)/2)*dims.height*cos;
    const x=rect.width/2-centerX*scale,y=rect.height/2-centerY*scale;
    state.camera={x,y,scale,angle,dims};state.angle=angle;
    world.style.transformOrigin='0 0';
    world.style.transform=`translate3d(${x.toFixed(3)}px,${y.toFixed(3)}px,0) scale(${scale.toFixed(8)}) rotateX(${angle}deg)`;
    clearWorldMask();
    renderOverlay();
  }

  function normalizedPoint(point){return{x:clamp(Number(point?.x)||0,0,1),y:clamp(Number(point?.y)||0,0,1)}}
  function snapPoint(point){
    const p=normalizedPoint(point),columns=Math.max(1,state.gridColumns),rows=Math.max(1,state.gridRows);
    return{x:clamp(Math.round(p.x*columns)/columns,0,1),y:clamp(Math.round(p.y*rows)/rows,0,1)};
  }
  function canonicalFromClient(clientX,clientY){
    const wr=world.getBoundingClientRect();
    return snapPoint({x:(clientX-wr.left)/Math.max(wr.width,1),y:(clientY-wr.top)/Math.max(wr.height,1)});
  }
  function canonicalToStage(point){
    const sr=stage.getBoundingClientRect();
    if(state.camera){
      const c=state.camera,cos=Math.max(.15,Math.cos(c.angle*Math.PI/180));
      return{x:(c.x+point.x*c.dims.width*c.scale)/Math.max(sr.width,1),y:(c.y+point.y*c.dims.height*c.scale*cos)/Math.max(sr.height,1)};
    }
    const wr=world.getBoundingClientRect();
    return{x:(wr.left-sr.left+point.x*wr.width)/Math.max(sr.width,1),y:(wr.top-sr.top+point.y*wr.height)/Math.max(sr.height,1)};
  }
  function rectangleBounds(a,b){
    return{minX:Math.min(a.x,b.x),minY:Math.min(a.y,b.y),maxX:Math.max(a.x,b.x),maxY:Math.max(a.y,b.y)};
  }
  function validBounds(){return!!state.bounds&&state.bounds.maxX>state.bounds.minX&&state.bounds.maxY>state.bounds.minY}
  function coordNumber(value){return Math.abs(value-Math.round(value))<1e-9?String(Math.round(value)):value.toFixed(2).replace(/\.00$/,'')}
  function coordinateBounds(){
    if(!validBounds())return null;
    const b=state.bounds,c=state.gridColumns,r=state.gridRows;
    return{
      xMin:(b.minX*c)-(c/2),
      xMax:(b.maxX*c)-(c/2),
      yMin:(r/2)-(b.maxY*r),
      yMax:(r/2)-(b.minY*r)
    };
  }
  function normalizedXFromCoordinate(value){return clamp((Number(value)+(state.gridColumns/2))/state.gridColumns,0,1)}
  function normalizedYFromCoordinate(value){return clamp(((state.gridRows/2)-Number(value))/state.gridRows,0,1)}
  function ensureBounds(){if(!state.bounds)state.bounds={minX:0,minY:0,maxX:1,maxY:1}}
  function setCoordinateBoundary(field,value){
    if(!Number.isFinite(Number(value)))return;
    ensureBounds();
    if(field==='xMin')state.bounds.minX=normalizedXFromCoordinate(value);
    if(field==='xMax')state.bounds.maxX=normalizedXFromCoordinate(value);
    if(field==='yMin')state.bounds.maxY=normalizedYFromCoordinate(value);
    if(field==='yMax')state.bounds.minY=normalizedYFromCoordinate(value);
    const b=state.bounds;
    if(b.maxX<b.minX)[b.minX,b.maxX]=[b.maxX,b.minX];
    if(b.maxY<b.minY)[b.minY,b.maxY]=[b.maxY,b.minY];
    state.bounds={minX:snapPoint({x:b.minX,y:0}).x,minY:snapPoint({x:0,y:b.minY}).y,maxX:snapPoint({x:b.maxX,y:0}).x,maxY:snapPoint({x:0,y:b.maxY}).y};
    renderAll();publishState();
  }

  function derivedCells(){
    if(!validBounds())return[];
    const b=state.bounds,c=state.gridColumns,r=state.gridRows;
    const minC=clamp(Math.floor(b.minX*c),0,c-1),maxC=clamp(Math.ceil(b.maxX*c)-1,minC,c-1);
    const minR=clamp(Math.floor(b.minY*r),0,r-1),maxR=clamp(Math.ceil(b.maxY*r)-1,minR,r-1),cells=[];
    for(let row=minR;row<=maxR;row++)for(let col=minC;col<=maxC;col++)cells.push(row*c+col);
    return cells;
  }
  function tierRange(){const out=[];for(let tier=state.minTierIndex;tier<=state.maxTierIndex;tier++)out.push(tier);return out}
  function layerRange(){return Array.from({length:LAYERS_PER_TIER},(_,index)=>index)}
  function volumeSummary(){
    const c=coordinateBounds();if(!c)return'X/Y NOT SET';
    return`X ${coordNumber(c.xMin)}…${coordNumber(c.xMax)} · Y ${coordNumber(c.yMin)}…${coordNumber(c.yMax)} · Z TIER ${state.minTierIndex}…${state.maxTierIndex}`;
  }

  function renderOverlay(){
    let markup='';
    if(validBounds()){
      const b=state.bounds,tl=canonicalToStage({x:b.minX,y:b.minY}),br=canonicalToStage({x:b.maxX,y:b.maxY});
      const x=Math.min(tl.x,br.x)*1000,y=Math.min(tl.y,br.y)*1000,w=Math.abs(br.x-tl.x)*1000,h=Math.abs(br.y-tl.y)*1000;
      const c=coordinateBounds();
      markup+=`<rect class="bound-fill" x="${x.toFixed(2)}" y="${y.toFixed(2)}" width="${w.toFixed(2)}" height="${h.toFixed(2)}"/>`;
      markup+=`<line class="bound-guide" x1="${x.toFixed(2)}" y1="0" x2="${x.toFixed(2)}" y2="1000"/><line class="bound-guide" x1="${(x+w).toFixed(2)}" y1="0" x2="${(x+w).toFixed(2)}" y2="1000"/><line class="bound-guide" x1="0" y1="${y.toFixed(2)}" x2="1000" y2="${y.toFixed(2)}"/><line class="bound-guide" x1="0" y1="${(y+h).toFixed(2)}" x2="1000" y2="${(y+h).toFixed(2)}"/>`;
      if(c)markup+=`<text class="coord-label" x="${clamp(x+8,10,860).toFixed(2)}" y="${clamp(y+24,24,970).toFixed(2)}">X ${coordNumber(c.xMin)}…${coordNumber(c.xMax)} · Y ${coordNumber(c.yMin)}…${coordNumber(c.yMax)}</text>`;
    }
    if(state.cursorVisible&&state.phase==='xy'){
      const p=canonicalToStage(state.cursor);markup+=`<circle class="cursor" cx="${(p.x*1000).toFixed(2)}" cy="${(p.y*1000).toFixed(2)}" r="7"/>`;
    }
    overlay.innerHTML=markup;
    overlay.style.pointerEvents=state.phase==='xy'?'auto':'none';
  }

  function phaseLabel(){return({xy:'1 · DEFINE X / Y BOUNDS',z:'2 · DEFINE Z TIER EXTENT',save:'3 · 60° REGION / SAVE',saved:'REGION · DRESS THE SCENE',existing:'REGION · 60° VIEW'}[state.phase]||'REGION DEFINER')}
  function hintText(){return({
    xy:'The square grid is coordinate authority, not geography. Drag two opposite corners or enter X min/max and Y min/max. Tier and Layer are intentionally unavailable here.',
    z:'Horizontal volume is fixed. Now choose the lowest and highest World Tier included in this Region. The Region may span downward and upward through the World stack.',
    save:'The bounded volume is confirmed, so the same World is now shown at 60°. Name the Region. Saving records authority/camera bounds; it does not crop or copy World terrain.',
    saved:'Dress this Region with additive tabletop miniatures. World terrain stays underneath. Select/group meaningful Region pieces and name their footprint to create a Local; starting play creates an Instance.',
    existing:'This is a 60° representation of one bounded Region volume over the same canonical World.'
  }[state.phase]||'')}
  function button(label,action,className=''){const b=document.createElement('button');b.type='button';b.textContent=label;b.className=className;b.addEventListener('click',action);return b}
  function numericField(label,value,min,max,onChange,placeholder=''){
    const wrap=document.createElement('label'),input=document.createElement('input');wrap.appendChild(document.createTextNode(label));input.type='number';input.step='1';if(Number.isFinite(min))input.min=String(min);if(Number.isFinite(max))input.max=String(max);if(value!==null&&value!==undefined)input.value=String(value);if(placeholder)input.placeholder=placeholder;input.addEventListener('change',()=>onChange(input.value));wrap.appendChild(input);return wrap;
  }
  function appendBack(tools){if(state.phase!=='existing'&&state.phase!=='saved')tools.appendChild(button('BACK',backAction,'region-back'))}
  function renderPanel(){
    panel.innerHTML='';
    const head=document.createElement('header'),title=document.createElement('strong'),status=document.createElement('small');
    title.textContent=phaseLabel();status.textContent=state.pending?'SAVING…':state.phase==='xy'?'WORLD COORDINATES':state.angle===60?'60° SAME WORLD':'BOUNDED VOLUME';head.append(title,status);panel.appendChild(head);
    const tools=document.createElement('div');tools.className='region-volume-tools';appendBack(tools);

    if(state.phase==='xy'){
      const fields=document.createElement('div');fields.className='region-volume-fields';const c=coordinateBounds(),halfX=state.gridColumns/2,halfY=state.gridRows/2;
      fields.append(
        numericField('X MIN',c?coordNumber(c.xMin):null,-halfX,halfX,value=>setCoordinateBoundary('xMin',value),'drag'),
        numericField('X MAX',c?coordNumber(c.xMax):null,-halfX,halfX,value=>setCoordinateBoundary('xMax',value),'drag'),
        numericField('Y MIN',c?coordNumber(c.yMin):null,-halfY,halfY,value=>setCoordinateBoundary('yMin',value),'drag'),
        numericField('Y MAX',c?coordNumber(c.yMax):null,-halfY,halfY,value=>setCoordinateBoundary('yMax',value),'drag')
      );tools.appendChild(fields);tools.appendChild(button('SET X/Y BOUNDS',primaryAction,'region-primary'));
    }else if(state.phase==='z'){
      const summary=document.createElement('div');summary.className='region-volume-summary';const span=document.createElement('span');const c=coordinateBounds();span.textContent=c?`X ${coordNumber(c.xMin)}…${coordNumber(c.xMax)} · Y ${coordNumber(c.yMin)}…${coordNumber(c.yMax)}`:'X/Y';summary.appendChild(span);tools.appendChild(summary);
      const fields=document.createElement('div');fields.className='region-volume-fields z';
      fields.append(
        numericField('Z MIN TIER',state.minTierIndex,0,state.maxTierIndexAllowed,value=>{state.minTierIndex=clamp(Math.trunc(Number(value)||0),0,state.maxTierIndexAllowed);if(state.maxTierIndex<state.minTierIndex)state.maxTierIndex=state.minTierIndex;renderAll();publishState()}),
        numericField('Z MAX TIER',state.maxTierIndex,0,state.maxTierIndexAllowed,value=>{state.maxTierIndex=clamp(Math.trunc(Number(value)||0),0,state.maxTierIndexAllowed);if(state.minTierIndex>state.maxTierIndex)state.minTierIndex=state.maxTierIndex;renderAll();publishState()})
      );tools.appendChild(fields);tools.appendChild(button('CONFIRM VOLUME · 60°',primaryAction,'region-primary'));
    }else if(state.phase==='save'){
      const summary=document.createElement('div');summary.className='region-volume-summary';const span=document.createElement('span');span.textContent=volumeSummary();summary.appendChild(span);tools.appendChild(summary);
      const name=document.createElement('label');name.className='region-volume-name';name.appendChild(document.createTextNode('REGION NAME'));const input=document.createElement('input');input.maxLength=80;input.placeholder='Region name';input.value=state.regionName;input.addEventListener('input',()=>state.regionName=input.value);name.appendChild(input);tools.appendChild(name);
      tools.appendChild(button(CLAIM_ONLY?'REQUEST REGION CLAIM':'SAVE REGION',()=>primaryAction(input.value),'region-primary'));
    }else if(state.phase==='saved'||state.phase==='existing'){
      const summary=document.createElement('div');summary.className='region-volume-summary';const name=document.createElement('span');name.innerHTML=`<b>${escapeHtml(state.regionName||'REGION')}</b>`;const volume=document.createElement('span');volume.textContent=volumeSummary();summary.append(name,volume);tools.appendChild(summary);
      const next=document.createElement('div');next.className='region-volume-next';next.innerHTML='<span><b>REGION:</b> place miniatures</span><span><b>LOCAL:</b> name a meaningful selection</span><span><b>INSTANCE:</b> start play</span>';tools.appendChild(next);
    }
    panel.appendChild(tools);const hint=document.createElement('p');hint.className='region-volume-hint';hint.textContent=hintText();panel.appendChild(hint);
  }
  function escapeHtml(value){return String(value||'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]))}
  function renderAll(){clearWorldMask();renderOverlay();renderPanel()}
  function setPhase(phase){state.phase=phase;stage.dataset.regionVolumePhase=phase;renderAll();publishState()}

  function getControllerState(exitRequested=false){return{phase:state.phase,selectedCount:derivedCells().length,gridShape:'square',tierIndex:state.minTierIndex,pending:state.pending,exitRequested:!!exitRequested,regionId:state.regionId||'',regionName:state.regionName||''}}
  function publishState(exitRequested=false){const snapshot=getControllerState(exitRequested);post({type:'controller-state',state:snapshot});return snapshot}

  function finalizeXY(){
    if(!validBounds()){announce('Define four X/Y boundaries first. Drag a rectangle on the World or enter X min/max and Y min/max.');return false}
    state.controllerAnchor=null;state.cursorVisible=false;state.minTierIndex=clamp(state.minTierIndex,0,state.maxTierIndexAllowed);state.maxTierIndex=clamp(Math.max(state.maxTierIndex,state.minTierIndex),0,state.maxTierIndexAllowed);setPhase('z');
    announce(`X/Y volume fixed: ${volumeSummary().split(' · Z')[0]}. Now define Z min Tier and Z max Tier.`);return true;
  }
  function finalizeZ(){
    if(!validBounds()){setPhase('xy');announce('X/Y boundaries must be defined before Z.');return false}
    state.minTierIndex=clamp(state.minTierIndex,0,state.maxTierIndexAllowed);state.maxTierIndex=clamp(state.maxTierIndex,0,state.maxTierIndexAllowed);if(state.maxTierIndex<state.minTierIndex)[state.minTierIndex,state.maxTierIndex]=[state.maxTierIndex,state.minTierIndex];
    if(CLAIM_ONLY&&state.maxTierIndex!==state.minTierIndex){announce('The current server claim-request contract can request one Tier at a time. A GM/owner can create the full multi-tier Region volume directly. Choose one Tier for this request.');return false}
    setPhase('save');fitBounds60();announce(`Region volume confirmed: ${volumeSummary()}. The same World is now represented at 60 degrees.`);return true;
  }
  async function saveRegion(name){
    name=String(name||'').trim();if(!name){announce('Name the Region before saving.');return false}if(!validBounds())return false;
    if(CLAIM_ONLY&&state.maxTierIndex!==state.minTierIndex){announce('Claim requests currently support one Tier. Nothing was submitted.');return false}
    state.pending=true;renderPanel();publishState();await sleep(0);
    const b=state.bounds,cells=derivedCells(),tiers=tierRange(),layers=layerRange();
    const payload={
      type:CLAIM_ONLY?'request-claim':'create-region',version:3,volumeModel:'BOUNDED_WORLD_VOLUME',name,cells,
      tierIndex:state.minTierIndex,minTierIndex:state.minTierIndex,maxTierIndex:state.maxTierIndex,sourceLayerOffsets:layers,gridShape:'square',
      canonicalMinX:b.minX,canonicalMinY:b.minY,canonicalMaxX:b.maxX,canonicalMaxY:b.maxY,
      viewMinX:b.minX,viewMinY:b.minY,viewMaxX:b.maxX,viewMaxY:b.maxY,
      resolutionScope:'REGION',viewZoomRatio:1/Math.max(b.maxX-b.minX,b.maxY-b.minY,.0001),viewAngle:60,
      visibleTierIndices:tiers,visibleLayerOffsets:layers,boundaryGridColumns:64,boundaryGridRows:64
    };
    post(payload);state.regionName=name;announce(CLAIM_ONLY?'Submitting this bounded Region request to the GM.':'Saving the bounded Region volume over the canonical World.');return true;
  }
  function primaryAction(name=''){
    if(name)state.regionName=String(name).trim();
    if(state.phase==='xy')return finalizeXY();
    if(state.phase==='z')return finalizeZ();
    if(state.phase==='save'){void saveRegion(state.regionName);return true}
    return false;
  }
  function backAction(){
    if(state.pending)return false;
    if(state.phase==='save'){restoreTopDown();setPhase('z');return true}
    if(state.phase==='z'){restoreTopDown();setPhase('xy');return true}
    if(state.phase==='xy'){publishState(true);return true}
    return false;
  }

  function pointerStart(event){
    if(state.phase!=='xy'||event.button>0)return;
    const p=canonicalFromClient(event.clientX,event.clientY);state.dragOrigin=p;state.bounds={minX:p.x,minY:p.y,maxX:p.x,maxY:p.y};state.dragging=true;state.cursor=p;state.cursorVisible=false;try{overlay.setPointerCapture(event.pointerId)}catch{};event.preventDefault();renderAll();
  }
  function pointerMove(event){if(!state.dragging||state.phase!=='xy')return;const p=canonicalFromClient(event.clientX,event.clientY);state.cursor=p;state.bounds=rectangleBounds(state.dragOrigin,p);renderOverlay();event.preventDefault()}
  function pointerEnd(event){if(!state.dragging)return;state.dragging=false;const p=canonicalFromClient(event.clientX,event.clientY);state.bounds=rectangleBounds(state.dragOrigin,p);renderAll();publishState();event.preventDefault()}
  overlay.addEventListener('pointerdown',pointerStart);overlay.addEventListener('pointermove',pointerMove);overlay.addEventListener('pointerup',pointerEnd);overlay.addEventListener('pointercancel',pointerEnd);

  function controllerSelect(){
    if(state.phase==='xy'){
      state.cursorVisible=true;const p=snapPoint(state.cursor);
      if(!state.controllerAnchor)state.controllerAnchor=p;else{state.bounds=rectangleBounds(state.controllerAnchor,p);state.controllerAnchor=null}renderAll();publishState();return true;
    }
    if(state.phase==='z'){state.zCursor=state.zCursor?0:1;announce(`Editing Z ${state.zCursor?'MAX':'MIN'} Tier.`);return true}
    return false;
  }
  function controllerStep(axis,direction){
    direction=Math.sign(Number(direction)||0);if(!direction)return false;
    if(state.phase==='xy'){
      state.cursorVisible=true;const dx=1/Math.max(1,state.gridColumns),dy=1/Math.max(1,state.gridRows);if(String(axis).toLowerCase()==='x')state.cursor.x=clamp(state.cursor.x+direction*dx,0,1);else state.cursor.y=clamp(state.cursor.y+direction*dy,0,1);state.cursor=snapPoint(state.cursor);renderOverlay();publishState();return true;
    }
    if(state.phase==='z'){
      if(String(axis).toLowerCase()==='x'){state.zCursor=state.zCursor?0:1}else if(state.zCursor===0){state.minTierIndex=clamp(state.minTierIndex+direction,0,state.maxTierIndexAllowed);if(state.maxTierIndex<state.minTierIndex)state.maxTierIndex=state.minTierIndex}else{state.maxTierIndex=clamp(state.maxTierIndex+direction,0,state.maxTierIndexAllowed);if(state.minTierIndex>state.maxTierIndex)state.minTierIndex=state.maxTierIndex}renderAll();publishState();return true;
    }
    return false;
  }
  function controllerToggleGrid(){announce(state.phase==='xy'?'The square grid is the X/Y coordinate authority and remains active during Region definition.':'The coordinate grid may return for snapping and measurement; Region identity remains the saved XYZ bounds.');return true}
  function enterController(){state.cursorVisible=state.phase==='xy';renderOverlay();publishState();return true}

  function adoptRegion(region){
    if(!region||typeof region!=='object')return;
    state.regionRecord=region;state.regionId=String(region.id||state.regionId||'');state.regionName=String(region.name||state.regionName||'');state.pending=false;
    const minX=clamp(Number(region.canonicalMinX ?? region.viewMinX)||0,0,1),minY=clamp(Number(region.canonicalMinY ?? region.viewMinY)||0,0,1),maxX=clamp(Number(region.canonicalMaxX ?? region.viewMaxX)||1,0,1),maxY=clamp(Number(region.canonicalMaxY ?? region.viewMaxY)||1,0,1);
    state.bounds={minX:Math.min(minX,maxX),minY:Math.min(minY,maxY),maxX:Math.max(minX,maxX),maxY:Math.max(minY,maxY)};
    state.minTierIndex=Math.max(0,Math.trunc(Number(region.minTierIndex ?? region.tierIndex)||0));state.maxTierIndex=Math.max(state.minTierIndex,Math.trunc(Number(region.maxTierIndex ?? state.minTierIndex)||state.minTierIndex));state.maxTierIndexAllowed=Math.max(state.maxTierIndex,state.maxTierIndexAllowed);
    state.angle=60;state.phase=NEW_FLOW?'saved':'existing';stage.dataset.regionVolumePhase=state.phase;fitBounds60();renderAll();publishState();
  }

  const baseApi=base;
  window.ShaelvienPrototype=Object.freeze({...baseApi,
    enterRegionController:enterController,
    getRegionControllerState:(exitRequested=false)=>getControllerState(exitRequested),
    publishRegionControllerState:(exitRequested=false)=>publishState(exitRequested),
    regionControllerPrimary:(name='')=>primaryAction(name),
    regionControllerBack:backAction,
    regionControllerStep:controllerStep,
    regionControllerSelect:controllerSelect,
    regionControllerToggleGrid:controllerToggleGrid
  });

  const observer=new MutationObserver(()=>{if(stage.dataset.regionVolumeV3!=='true')return;clearWorldMask()});
  observer.observe(world,{attributes:true,attributeFilter:['style'],subtree:false});
  window.addEventListener('resize',()=>{if(state.angle===60&&validBounds())fitBounds60();else renderOverlay()});

  window.addEventListener('message',event=>{
    if(event.origin!==location.origin||event.source!==parent)return;
    const data=event.data;if(!data||data.source!=='shaelvien-regiondefiner-host')return;
    if(data.type==='world-source'){
      const worldSource=data.worldSource&&typeof data.worldSource==='object'?data.worldSource:{};state.worldReady=true;state.gridColumns=Math.max(1,Math.trunc(Number(worldSource.gridColumns)||state.gridColumns));state.gridRows=Math.max(1,Math.trunc(Number(worldSource.gridRows)||state.gridRows));
      if(NEW_FLOW){try{baseApi.showAllParallax?.()}catch{}restoreTopDown();setPhase('xy');announce('Define X min/max and Y min/max on the permanent square World coordinate grid. Tier and Layer come later.');}
    }else if(data.type==='catalog-v2'){
      const regions=Array.isArray(data.regions)?data.regions:[];if(!NEW_FLOW&&REQUESTED_REGION_ID){const region=regions.find(item=>String(item?.id||'')===REQUESTED_REGION_ID);if(region)adoptRegion(region)}
    }else if(data.type==='region-created'){
      state.pending=false;state.regionName=String(data.region?.name||state.regionName||'');adoptRegion(data.region||{});state.phase='saved';stage.dataset.regionVolumePhase='saved';renderAll();announce(`${state.regionName||'Region'} saved as a bounded XYZ volume. Dress it with additive Region miniatures; the World underneath was not copied.`);
    }else if(data.type==='claim-requested'){
      state.pending=false;renderAll();publishState();if(data.result?.success){state.phase='saved';stage.dataset.regionVolumePhase='saved';renderAll();announce(String(data.result?.message||'Region claim request sent.'))}else announce(String(data.result?.message||'Region claim request was not accepted.'));
    }else if(data.type==='error'){
      state.pending=false;renderAll();publishState();announce(String(data.message||'Region operation failed.'));
    }
  });

  clearWorldMask();
  if(NEW_FLOW){restoreTopDown();setPhase('xy')}else{panel.hidden=true;state.phase='existing';stage.dataset.regionVolumePhase='existing';publishState()}
  post({type:'ready'});
}

boot();
})();
