(()=>{
'use strict';
const Q=new URLSearchParams(location.search);
if(String(Q.get('mode')||'').toLowerCase()!=='regiondefiner')return;
const NEW_FLOW=String(Q.get('regionFlow')||'').toLowerCase()==='new';
const REQUESTED_REGION_ID=String(Q.get('regionId')||'');
const CLAIM_ONLY=String(Q.get('access')||'edit').toLowerCase()==='claim';
const clamp=(v,a,b)=>Math.min(b,Math.max(a,v));
const wrap=(v,n)=>(v%n+n)%n;
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
  if(stage.dataset.regionGeometryV2==='true')return;
  stage.dataset.regionGeometryV2='true';
  stage.classList.add('region-geometry-v2');

  const source='shaelvien-regiondefiner';
  const post=message=>{try{parent.postMessage({source,...message},location.origin)}catch{}};
  const live=document.getElementById('live');
  const announce=message=>{const text=String(message||'');if(live)live.textContent=text;post({type:'controller-state',state:getControllerState()})};
  const originalTransform=world.style.transform||'';
  const originalTransformOrigin=world.style.transformOrigin||'';
  const originalMask=world.style.maskImage||'';
  const originalWebkitMask=world.style.webkitMaskImage||'';

  const state={
    phase:NEW_FLOW?'focus':'existing',
    focusTool:'rectangle',
    borderTool:'line',
    focusPath:[],
    focusBBox:null,
    borderPath:[],
    dragOrigin:null,
    drawing:false,
    controllerAnchor:null,
    cursor:{x:.5,y:.5},
    cursorVisible:false,
    tierCursor:0,
    visibleTiers:new Set(),
    regionName:'',
    pending:false,
    regionId:REQUESTED_REGION_ID,
    regionRecord:null,
    camera:null,
    angle:0,
    worldReady:false,
    finalCellCount:0
  };

  const style=document.createElement('style');
  style.id='region-geometry-v2-style';
  style.textContent=`
    .region-geometry-v2 .region-tier-preview,
    .region-geometry-v2.region-geometry-authoring .region-definition-grid,
    .region-geometry-v2.region-geometry-authoring .region-selection-tools-panel:not(.region-geometry-panel){display:none!important}
    .region-geometry-panel{position:absolute;left:50%;top:12px;transform:translateX(-50%);z-index:90;width:min(92%,620px);box-sizing:border-box;padding:9px 10px;border:1px solid rgba(236,196,93,.8);border-radius:13px;background:rgba(5,12,18,.88);box-shadow:0 8px 26px rgba(0,0,0,.38);color:#f4e6ba;font:700 11px/1.25 system-ui,sans-serif;letter-spacing:.08em;pointer-events:auto;backdrop-filter:blur(5px)}
    .region-geometry-panel header{display:flex;align-items:center;justify-content:space-between;gap:8px;margin-bottom:7px}.region-geometry-panel header strong{font-size:12px;color:#fff}.region-geometry-panel header small{color:#8edcff}
    .region-geometry-tools{display:flex;gap:6px;flex-wrap:wrap;align-items:center}.region-geometry-tools button,.region-geometry-panel .region-primary,.region-geometry-panel .region-back{border:1px solid rgba(116,205,244,.55);border-radius:9px;background:rgba(11,31,43,.9);color:#e9f8ff;min-height:34px;padding:6px 10px;font:800 10px/1 system-ui,sans-serif;letter-spacing:.08em}.region-geometry-tools button.active{border-color:#f3ca63;background:rgba(87,60,11,.88);color:#fff3c5}.region-geometry-panel .region-primary{margin-left:auto;border-color:#f3ca63;color:#fff0b7}.region-geometry-panel .region-back{border-color:rgba(255,255,255,.3)}
    .region-geometry-hint{margin:6px 0 0;color:#c7dbe4;font-weight:600;letter-spacing:.03em}.region-geometry-tier-list{display:flex;gap:7px;flex-wrap:wrap}.region-geometry-tier-list label{display:flex;align-items:center;gap:5px;border:1px solid rgba(255,255,255,.18);border-radius:8px;padding:6px 8px;background:rgba(0,0,0,.2)}
    .region-geometry-name{display:flex;gap:7px;align-items:center;flex:1}.region-geometry-name input{min-width:0;flex:1;border:1px solid rgba(255,255,255,.28);border-radius:8px;padding:8px;background:#071219;color:white;font:700 12px system-ui,sans-serif}.region-geometry-status{color:#9bdfff;white-space:nowrap}
    .region-geometry-overlay{position:absolute;inset:0;z-index:70;width:100%;height:100%;touch-action:none;overflow:visible}.region-geometry-overlay .focus-dim{fill:rgba(0,0,0,.38);fill-rule:evenodd;pointer-events:none}.region-geometry-overlay .focus-line{fill:none;stroke:#82dbff;stroke-width:2.4;stroke-dasharray:9 7;vector-effect:non-scaling-stroke;pointer-events:none}.region-geometry-overlay .border-line{fill:rgba(255,203,77,.06);stroke:#ffd66e;stroke-width:3.5;vector-effect:non-scaling-stroke;pointer-events:none}.region-geometry-overlay .draft-line{fill:none;stroke:#fff;stroke-width:2;stroke-dasharray:4 5;vector-effect:non-scaling-stroke;pointer-events:none}.region-geometry-overlay .cursor{fill:#fff;stroke:#52d8ff;stroke-width:7;vector-effect:non-scaling-stroke;filter:drop-shadow(0 0 5px #36caff);pointer-events:none}.region-geometry-v2[data-region-geometry-phase="tiers"] .region-geometry-overlay,.region-geometry-v2[data-region-geometry-phase="save"] .region-geometry-overlay,.region-geometry-v2[data-region-geometry-phase="saved"] .region-geometry-overlay{pointer-events:none}
    .region-geometry-v2 .region-mode-reference{font-size:0}.region-geometry-v2 .region-mode-reference::after{content:'REGION DEFINER · ONE CANONICAL MAP';font-size:11px}
    @media(max-width:720px){.region-geometry-panel{top:7px;width:95%;padding:7px}.region-geometry-tools button,.region-geometry-panel .region-primary,.region-geometry-panel .region-back{min-height:32px;padding:5px 8px;font-size:9px}.region-geometry-hint{font-size:9px}}
  `;
  document.head.appendChild(style);

  const overlay=document.createElementNS('http://www.w3.org/2000/svg','svg');
  overlay.classList.add('region-geometry-overlay');
  overlay.setAttribute('viewBox','0 0 1000 1000');
  overlay.setAttribute('preserveAspectRatio','none');
  overlay.setAttribute('aria-label','Region geometry authoring surface');
  stage.appendChild(overlay);

  const panel=document.createElement('section');
  panel.className='region-selection-tools-panel region-geometry-panel';
  panel.setAttribute('aria-label','Region definition tools');
  stage.appendChild(panel);

  function polygonBBox(points){
    if(!Array.isArray(points)||points.length<1)return null;
    let minX=1,minY=1,maxX=0,maxY=0;
    for(const p of points){minX=Math.min(minX,p.x);minY=Math.min(minY,p.y);maxX=Math.max(maxX,p.x);maxY=Math.max(maxY,p.y)}
    return{minX:clamp(minX,0,1),minY:clamp(minY,0,1),maxX:clamp(maxX,0,1),maxY:clamp(maxY,0,1),width:Math.max(.0001,maxX-minX),height:Math.max(.0001,maxY-minY)};
  }
  function rectanglePoints(a,b){
    const minX=Math.min(a.x,b.x),maxX=Math.max(a.x,b.x),minY=Math.min(a.y,b.y),maxY=Math.max(a.y,b.y);
    return[{x:minX,y:minY},{x:maxX,y:minY},{x:maxX,y:maxY},{x:minX,y:maxY}];
  }
  function ellipsePoints(a,b,count=56){
    const box=polygonBBox([a,b]);if(!box)return[];
    const cx=(box.minX+box.maxX)/2,cy=(box.minY+box.maxY)/2,rx=box.width/2,ry=box.height/2,points=[];
    for(let i=0;i<count;i++){const t=(i/count)*Math.PI*2;points.push({x:cx+Math.cos(t)*rx,y:cy+Math.sin(t)*ry})}
    return points;
  }
  function centroid(points){
    if(!points.length)return{x:.5,y:.5};
    return points.reduce((a,p)=>({x:a.x+p.x/points.length,y:a.y+p.y/points.length}),{x:0,y:0});
  }
  function insetPolygon(points,factor=.92){
    const c=centroid(points);return points.map(p=>({x:c.x+(p.x-c.x)*factor,y:c.y+(p.y-c.y)*factor}));
  }
  function pointInPolygon(point,poly){
    if(!poly||poly.length<3)return false;
    let inside=false;
    for(let i=0,j=poly.length-1;i<poly.length;j=i++){
      const a=poly[i],b=poly[j];
      const cross=((a.y>point.y)!=(b.y>point.y))&&(point.x<(b.x-a.x)*(point.y-a.y)/((b.y-a.y)||1e-12)+a.x);
      if(cross)inside=!inside;
    }
    return inside;
  }
  function normalizePoint(point){return{x:clamp(Number(point?.x)||0,0,1),y:clamp(Number(point?.y)||0,0,1)}}
  function segmentDistance(p,a,b){
    const vx=b.x-a.x,vy=b.y-a.y,wx=p.x-a.x,wy=p.y-a.y,den=vx*vx+vy*vy;
    const t=den?clamp((wx*vx+wy*vy)/den,0,1):0,dx=p.x-(a.x+t*vx),dy=p.y-(a.y+t*vy);
    return Math.hypot(dx,dy);
  }
  function decimate(points,min=.0025){
    const out=[];for(const p of points){if(!out.length||Math.hypot(p.x-out.at(-1).x,p.y-out.at(-1).y)>=min)out.push(p)}return out;
  }

  function stripAngle(transform){return String(transform||'').replace(/\s*rotateX\([^)]*\)/gi,'').trim()}
  function tierOf(node){
    const direct=Number(node?.dataset?.tier);if(Number.isInteger(direct)&&direct>=0)return direct;
    if(node?.id==='surfacePlane')return 0;if(node?.id==='highlandsPlane')return 1;if(node?.id==='mountainPlane')return 2;
    return null;
  }
  function collectTierIndices(){
    const values=new Set([0,1,2]);
    world.querySelectorAll('[data-tier],#surfacePlane,#highlandsPlane,#mountainPlane').forEach(node=>{const tier=tierOf(node);if(tier!==null)values.add(tier)});
    return[...values].filter(v=>v>=0&&v<32).sort((a,b)=>a-b);
  }
  function applyVisibleTiers(){
    if(!state.visibleTiers.size)return;
    world.querySelectorAll('[data-tier],#surfacePlane,#highlandsPlane,#mountainPlane').forEach(node=>{
      const tier=tierOf(node);if(tier===null)return;
      node.style.visibility=state.visibleTiers.has(tier)?'':'hidden';
    });
  }
  function clearWorldMask(){
    if(world.style.maskImage!=='none')world.style.maskImage='none';
    if(world.style.webkitMaskImage!=='none')world.style.webkitMaskImage='none';
    world.style.maskSize='';world.style.webkitMaskSize='';world.style.maskRepeat='';world.style.webkitMaskRepeat='';
    stage.classList.remove('region-cropped');delete stage.dataset.cropMode;
  }
  function worldDimensions(){return{width:Math.max(1,world.offsetWidth||parseFloat(world.style.width)||2048),height:Math.max(1,world.offsetHeight||parseFloat(world.style.height)||2048)}}
  function fitFocus(angle=0){
    const box=state.focusBBox;if(!box)return;
    const rect=stage.getBoundingClientRect(),dims=worldDimensions(),cos=Math.max(.15,Math.cos(angle*Math.PI/180));
    const focusW=Math.max(1,box.width*dims.width),focusH=Math.max(1,box.height*dims.height*cos);
    const scale=Math.max(.000001,Math.min(rect.width/focusW,rect.height/focusH)*.88);
    const centerX=(box.minX+box.maxX)/2*dims.width,centerY=(box.minY+box.maxY)/2*dims.height*cos;
    const x=rect.width/2-centerX*scale,y=rect.height/2-centerY*scale;
    state.camera={x,y,scale,angle,dims};state.angle=angle;
    enforceWorld();renderOverlay();
  }
  function restoreFullView(){
    state.camera=null;state.angle=0;
    world.style.transformOrigin=originalTransformOrigin||'0 0';
    world.style.transform=stripAngle(originalTransform);
    clearWorldMask();
    try{base.showAllParallax?.()}catch{}
    requestAnimationFrame(()=>{clearWorldMask();renderOverlay()});
  }
  function enforceWorld(){
    clearWorldMask();
    if(state.camera){
      const c=state.camera;
      const transform=`translate3d(${c.x.toFixed(3)}px,${c.y.toFixed(3)}px,0) scale(${c.scale.toFixed(8)})${c.angle?` rotateX(${c.angle}deg)`:''}`;
      world.style.transformOrigin='0 0';if(world.style.transform!==transform)world.style.transform=transform;
    }else{
      const baseTransform=stripAngle(world.style.transform||originalTransform);
      const wanted=state.angle?`${baseTransform} rotateX(${state.angle}deg)`.trim():baseTransform;
      if(world.style.transform!==wanted)world.style.transform=wanted;
    }
    applyVisibleTiers();
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
  function canonicalFromClient(clientX,clientY){
    const sr=stage.getBoundingClientRect();
    if(state.camera){
      const c=state.camera,cos=Math.max(.15,Math.cos(c.angle*Math.PI/180));
      return normalizePoint({x:(clientX-sr.left-c.x)/(c.dims.width*c.scale),y:(clientY-sr.top-c.y)/(c.dims.height*c.scale*cos)});
    }
    const wr=world.getBoundingClientRect();
    return normalizePoint({x:(clientX-wr.left)/Math.max(wr.width,1),y:(clientY-wr.top)/Math.max(wr.height,1)});
  }
  function pathD(points,close=true){
    if(!points?.length)return'';
    return points.map((p,index)=>{const s=canonicalToStage(p);return`${index?'L':'M'} ${(s.x*1000).toFixed(2)} ${(s.y*1000).toFixed(2)}`}).join(' ')+(close?' Z':'');
  }
  function focusDimPath(){
    if(state.focusPath.length<3)return'';
    return`M 0 0 H 1000 V 1000 H 0 Z ${pathD(state.focusPath,true)}`;
  }
  function renderOverlay(){
    const focus=state.focusPath.length>=3?`<path class="focus-dim" d="${focusDimPath()}"/><path class="focus-line" d="${pathD(state.focusPath,true)}"/>`:'';
    const border=state.borderPath.length>=2?`<path class="border-line" d="${pathD(state.borderPath,state.borderPath.length>=3)}"/>`:'';
    const cursorPoint=canonicalToStage(state.cursor),cursor=state.cursorVisible&&['focus','border'].includes(state.phase)?`<circle class="cursor" cx="${(cursorPoint.x*1000).toFixed(2)}" cy="${(cursorPoint.y*1000).toFixed(2)}" r="7"/>`:'';
    overlay.innerHTML=focus+border+cursor;
    overlay.style.pointerEvents=['focus','border'].includes(state.phase)?'auto':'none';
  }
  function insideFocus(point){return state.focusPath.length<3||pointInPolygon(point,state.focusPath)}
  function phaseLabel(){return({focus:'1 · FOCUS SHAPE',border:'2 · REGION BORDER',tiers:'3 · 60° / VISIBLE TIERS',save:'4 · SAVE REGION',saved:'REGION SAVED',existing:'REGION VIEW'}[state.phase]||'REGION DEFINER')}
  function hintText(){return({
    focus:'Choose a rough work area. Crop changes only the view/edit limit; it never creates another map.',
    border:'Draw the true region border inside the focused world view. The surrounding world remains context.',
    tiers:'Regional presentation is fixed at 60°. Choose which world tiers remain visible.',
    save:'Name the region and save its boundary/view metadata over the one canonical world map.',
    saved:'Region boundary saved. Grids return for tile placement and play, not geography authoring.',
    existing:'This is a permissioned regional view over the canonical world map.'
  }[state.phase]||'')}
  function button(label,active,action){const b=document.createElement('button');b.type='button';b.textContent=label;b.classList.toggle('active',!!active);b.addEventListener('click',action);return b}
  function renderPanel(){
    panel.innerHTML='';
    const head=document.createElement('header'),title=document.createElement('strong'),status=document.createElement('small');
    title.textContent=phaseLabel();status.className='region-geometry-status';status.textContent=state.pending?'SAVING…':'ONE MAP';head.append(title,status);panel.appendChild(head);
    const tools=document.createElement('div');tools.className='region-geometry-tools';
    if(state.phase==='focus'){
      for(const [id,label] of [['rectangle','RECT'],['ellipse','ELLIPSE'],['lasso','LASSO']])tools.appendChild(button(label,state.focusTool===id,()=>{state.focusTool=id;state.focusPath=[];state.focusBBox=null;state.controllerAnchor=null;renderAll()}));
      const primary=button('CROP VIEW',false,()=>primaryAction());primary.className='region-primary';tools.appendChild(primary);
    }else if(state.phase==='border'){
      for(const [id,label] of [['line','LINE'],['pencil','PENCIL'],['magic','MAGIC SELECT']])tools.appendChild(button(label,state.borderTool===id,()=>{state.borderTool=id;state.controllerAnchor=null;if(id==='magic')seedMagicBorder();renderAll()}));
      tools.appendChild(button('CLEAR BORDER',false,()=>{state.borderPath=[];renderAll()}));
      const primary=button('SET REGION BORDER',false,()=>primaryAction());primary.className='region-primary';tools.appendChild(primary);
    }else if(state.phase==='tiers'){
      const list=document.createElement('div');list.className='region-geometry-tier-list';
      const tiers=collectTierIndices();if(!state.visibleTiers.size)tiers.forEach(t=>state.visibleTiers.add(t));
      tiers.forEach((tier,index)=>{const label=document.createElement('label');label.classList.toggle('active',index===state.tierCursor);const input=document.createElement('input');input.type='checkbox';input.checked=state.visibleTiers.has(tier);input.addEventListener('change',()=>{if(input.checked)state.visibleTiers.add(tier);else state.visibleTiers.delete(tier);if(!state.visibleTiers.size){state.visibleTiers.add(tier);input.checked=true}applyVisibleTiers();publishState()});label.append(input,document.createTextNode(`TIER ${tier}`));list.appendChild(label)});tools.appendChild(list);
      const primary=button('CONTINUE',false,()=>primaryAction());primary.className='region-primary';tools.appendChild(primary);
    }else if(state.phase==='save'){
      const group=document.createElement('label');group.className='region-geometry-name';const input=document.createElement('input');input.maxLength=80;input.placeholder='Region name';input.value=state.regionName;input.addEventListener('input',()=>state.regionName=input.value);group.appendChild(input);tools.appendChild(group);
      const primary=button(CLAIM_ONLY?'REQUEST CLAIM':'SAVE REGION',false,()=>primaryAction(input.value));primary.className='region-primary';tools.appendChild(primary);
    }else if(state.phase==='saved'){
      const done=document.createElement('span');done.textContent=state.regionName||'REGION SAVED';tools.appendChild(done);
    }
    if(!['existing','saved'].includes(state.phase)){const back=button('BACK',false,()=>backAction());back.className='region-back';tools.prepend(back)}
    panel.appendChild(tools);
    const hint=document.createElement('p');hint.className='region-geometry-hint';hint.textContent=hintText();panel.appendChild(hint);
  }
  function setPhase(phase){
    state.phase=phase;stage.dataset.regionGeometryPhase=phase;
    stage.classList.toggle('region-geometry-authoring',['focus','border','tiers','save'].includes(phase));
    renderAll();publishState();
  }
  function getControllerState(exitRequested=false){
    const tiers=[...state.visibleTiers].sort((a,b)=>a-b);
    return{phase:state.phase,selectedCount:state.borderPath.length>=3?Math.max(1,state.finalCellCount||1):0,gridShape:'none',tierIndex:tiers[0]??0,pending:state.pending,exitRequested:!!exitRequested,regionId:state.regionId||'',regionName:state.regionName||''};
  }
  function publishState(exitRequested=false){post({type:'controller-state',state:getControllerState(exitRequested)});return getControllerState(exitRequested)}
  function renderAll(){enforceWorld();renderOverlay();renderPanel()}

  function finalizeFocus(){
    if(state.focusPath.length<3){announce('Draw a rough shape around the area you want to work in.');return false}
    state.focusBBox=polygonBBox(state.focusPath);if(!state.focusBBox)return false;
    state.controllerAnchor=null;state.borderPath=[];state.angle=0;
    setPhase('border');fitFocus(0);
    announce('Focused view ready. This is only a view and edit limit. Draw the Region border with Line, Pencil, or Magic Select.');
    return true;
  }
  function seedMagicBorder(){
    if(state.focusPath.length<3)return;
    state.borderPath=insetPolygon(state.focusPath,.92);state.borderTool='magic';renderAll();announce('Magic Select seeded an editable border from the focused shape. Use Line or Pencil to replace/refine it if needed.');
  }
  function finalizeBorder(){
    if(state.borderPath.length<3){announce('Draw a closed Region border first.');return false}
    const filtered=state.borderPath.filter(insideFocus);
    if(filtered.length<3){announce('The Region border must remain inside the focused edit area.');return false}
    state.borderPath=filtered;state.controllerAnchor=null;
    const tiers=collectTierIndices();if(!state.visibleTiers.size)tiers.forEach(t=>state.visibleTiers.add(t));
    setPhase('tiers');fitFocus(60);applyVisibleTiers();
    announce('Region border set. The regional representation is now 60 degrees. Choose the tiers that should be visible.');
    return true;
  }
  function primaryAction(name=''){
    if(name)state.regionName=String(name).trim();
    if(state.phase==='focus')return finalizeFocus();
    if(state.phase==='border')return finalizeBorder();
    if(state.phase==='tiers'){if(!state.visibleTiers.size){announce('Keep at least one tier visible.');return false}setPhase('save');announce('Name the region, then save it.');return true}
    if(state.phase==='save'){saveRegion(state.regionName);return true}
    return false;
  }
  function backAction(){
    if(state.pending)return false;
    if(state.phase==='save'){setPhase('tiers');return true}
    if(state.phase==='tiers'){state.angle=0;setPhase('border');fitFocus(0);return true}
    if(state.phase==='border'){state.borderPath=[];state.focusBBox=null;restoreFullView();setPhase('focus');return true}
    if(state.phase==='focus'){publishState(true);return true}
    return false;
  }

  function rasterInterior(poly,columns=300,rows=300){
    const result=[];if(poly.length<3)return result;
    const box=polygonBBox(poly);if(!box)return result;
    const minC=clamp(Math.floor(box.minX*columns),0,columns-1),maxC=clamp(Math.ceil(box.maxX*columns),0,columns-1),minR=clamp(Math.floor(box.minY*rows),0,rows-1),maxR=clamp(Math.ceil(box.maxY*rows),0,rows-1);
    for(let row=minR;row<=maxR;row++)for(let col=minC;col<=maxC;col++)if(pointInPolygon({x:(col+.5)/columns,y:(row+.5)/rows},poly))result.push(row*columns+col);
    if(!result.length){const c=centroid(poly),col=clamp(Math.floor(c.x*columns),0,columns-1),row=clamp(Math.floor(c.y*rows),0,rows-1);result.push(row*columns+col)}
    return result;
  }
  function rasterBoundary(poly,columns=64,rows=64){
    const result=[];if(poly.length<2)return result;
    const threshold=1.25/Math.max(columns,rows),closed=[...poly,poly[0]];
    for(let row=0;row<rows;row++)for(let col=0;col<columns;col++){
      const p={x:(col+.5)/columns,y:(row+.5)/rows};let hit=false;
      for(let i=0;i<closed.length-1;i++)if(segmentDistance(p,closed[i],closed[i+1])<=threshold){hit=true;break}
      if(hit)result.push(row*columns+col);
    }
    return result;
  }
  async function saveRegion(name){
    name=String(name||'').trim();if(!name){announce('Enter a Region name first.');return}
    if(state.borderPath.length<3||!state.focusBBox){announce('The focus view and Region border must be defined before saving.');return}
    state.pending=true;renderPanel();publishState();await sleep(0);
    const cells=rasterInterior(state.borderPath,300,300),boundaryCells=rasterBoundary(state.borderPath,64,64),borderBox=polygonBBox(state.borderPath),visibleTiers=[...state.visibleTiers].sort((a,b)=>a-b);
    state.finalCellCount=cells.length;
    const payload={
      type:CLAIM_ONLY?'request-claim':'create-region',version:2,name,cells,
      tierIndex:visibleTiers[0]??0,sourceLayerOffsets:Array.from({length:10},(_,index)=>index),gridShape:'square',
      boundaryCells,boundaryGridColumns:64,boundaryGridRows:64,
      viewMinX:state.focusBBox.minX,viewMinY:state.focusBBox.minY,viewMaxX:state.focusBBox.maxX,viewMaxY:state.focusBBox.maxY,
      canonicalMinX:borderBox?.minX??0,canonicalMinY:borderBox?.minY??0,canonicalMaxX:borderBox?.maxX??1,canonicalMaxY:borderBox?.maxY??1,
      resolutionScope:'REGION',viewZoomRatio:1/Math.max(state.focusBBox.width,state.focusBBox.height,.0001),viewAngle:60,
      visibleTierIndices:visibleTiers,visibleLayerOffsets:Array.from({length:10},(_,index)=>index),focusTool:state.focusTool,borderTool:state.borderTool
    };
    post(payload);state.regionName=name;announce(CLAIM_ONLY?'Submitting the Region boundary for GM approval.':'Saving Region geometry over the canonical world map.');
  }

  function adoptRegion(region){
    if(!region||typeof region!=='object')return;
    state.regionRecord=region;state.regionId=String(region.id||state.regionId||'');state.regionName=String(region.name||state.regionName||'');state.pending=false;
    const minX=clamp(Number(region.viewMinX)||0,0,1),minY=clamp(Number(region.viewMinY)||0,0,1),maxX=clamp(Number(region.viewMaxX)||1,0,1),maxY=clamp(Number(region.viewMaxY)||1,0,1);
    state.focusBBox={minX,minY,maxX:Math.max(minX,maxX),maxY:Math.max(minY,maxY),width:Math.max(.0001,maxX-minX),height:Math.max(.0001,maxY-minY)};
    state.focusPath=rectanglePoints({x:state.focusBBox.minX,y:state.focusBBox.minY},{x:state.focusBBox.maxX,y:state.focusBBox.maxY});
    const tiers=Array.isArray(region.visibleTierIndices)?region.visibleTierIndices.map(Number).filter(Number.isInteger):[];state.visibleTiers=new Set(tiers.length?tiers:collectTierIndices());
    clearWorldMask();try{base.showAllParallax?.()}catch{}
    state.angle=60;state.phase=NEW_FLOW?'saved':'existing';stage.dataset.regionGeometryPhase=state.phase;stage.classList.remove('region-geometry-authoring');fitFocus(60);applyVisibleTiers();renderAll();publishState();
  }

  function pointerStart(event){
    if(!['focus','border'].includes(state.phase)||event.button>0)return;
    const p=canonicalFromClient(event.clientX,event.clientY);state.cursor=p;state.cursorVisible=false;
    if(state.phase==='focus'){
      state.drawing=true;state.dragOrigin=p;state.focusPath=state.focusTool==='lasso'?[p]:[];
    }else if(state.borderTool==='line'){
      if(!insideFocus(p))return;state.borderPath.push(p);state.drawing=false;renderAll();
    }else if(state.borderTool==='magic'){
      seedMagicBorder();state.drawing=false;
    }else{
      if(!insideFocus(p))return;state.drawing=true;state.borderPath=[p];
    }
    try{overlay.setPointerCapture(event.pointerId)}catch{};event.preventDefault();renderAll();
  }
  function pointerMove(event){
    if(!state.drawing)return;
    const p=canonicalFromClient(event.clientX,event.clientY);state.cursor=p;
    if(state.phase==='focus'){
      if(state.focusTool==='rectangle')state.focusPath=rectanglePoints(state.dragOrigin,p);
      else if(state.focusTool==='ellipse')state.focusPath=ellipsePoints(state.dragOrigin,p);
      else state.focusPath=decimate([...state.focusPath,p],.003);
    }else if(state.borderTool==='pencil'&&insideFocus(p))state.borderPath=decimate([...state.borderPath,p],.0025);
    renderOverlay();event.preventDefault();
  }
  function pointerEnd(event){
    if(!state.drawing)return;state.drawing=false;
    const p=canonicalFromClient(event.clientX,event.clientY);
    if(state.phase==='focus'){
      if(state.focusTool==='rectangle')state.focusPath=rectanglePoints(state.dragOrigin,p);
      else if(state.focusTool==='ellipse')state.focusPath=ellipsePoints(state.dragOrigin,p);
      else state.focusPath=decimate([...state.focusPath,p],.003);
      state.focusBBox=polygonBBox(state.focusPath);
    }else if(state.borderTool==='pencil'&&insideFocus(p))state.borderPath=decimate([...state.borderPath,p],.0025);
    renderAll();publishState();event.preventDefault();
  }
  overlay.addEventListener('pointerdown',pointerStart);overlay.addEventListener('pointermove',pointerMove);overlay.addEventListener('pointerup',pointerEnd);overlay.addEventListener('pointercancel',pointerEnd);

  function controllerSelect(){
    state.cursorVisible=true;const p={...state.cursor};
    if(state.phase==='focus'){
      if(state.focusTool==='lasso'){state.focusPath.push(p);state.focusBBox=polygonBBox(state.focusPath)}
      else if(!state.controllerAnchor)state.controllerAnchor=p;
      else{state.focusPath=state.focusTool==='ellipse'?ellipsePoints(state.controllerAnchor,p):rectanglePoints(state.controllerAnchor,p);state.focusBBox=polygonBBox(state.focusPath);state.controllerAnchor=null}
    }else if(state.phase==='border'){
      if(state.borderTool==='magic')seedMagicBorder();
      else if(insideFocus(p))state.borderPath.push(p);
    }else if(state.phase==='tiers'){
      const tiers=collectTierIndices(),tier=tiers[wrap(state.tierCursor,tiers.length)];
      if(state.visibleTiers.has(tier)&&state.visibleTiers.size>1)state.visibleTiers.delete(tier);else state.visibleTiers.add(tier);applyVisibleTiers();
    }
    renderAll();publishState();return true;
  }
  function controllerStep(axis,direction){
    direction=Math.sign(Number(direction)||0);if(!direction)return false;
    if(state.phase==='tiers'){
      const tiers=collectTierIndices();state.tierCursor=wrap(state.tierCursor+direction,Math.max(1,tiers.length));renderPanel();publishState();return true;
    }
    if(!['focus','border'].includes(state.phase))return false;
    state.cursorVisible=true;const step=.02;
    if(String(axis).toLowerCase()==='x')state.cursor.x=clamp(state.cursor.x+direction*step,0,1);else state.cursor.y=clamp(state.cursor.y+direction*step,0,1);
    renderOverlay();publishState();return true;
  }
  function controllerPrimary(name=''){return primaryAction(name)}
  function controllerBack(){return backAction()}
  function controllerToggleGrid(){announce('Geography definition is gridless. Grids return for tile placement and during play.');return true}
  function enterController(){state.cursorVisible=true;if(NEW_FLOW&&state.phase==='existing')setPhase('focus');renderOverlay();publishState();return true}

  const baseApi=base;
  window.ShaelvienPrototype=Object.freeze({...baseApi,
    enterRegionController:enterController,
    getRegionControllerState:(exitRequested=false)=>getControllerState(exitRequested),
    publishRegionControllerState:(exitRequested=false)=>publishState(exitRequested),
    regionControllerPrimary:controllerPrimary,
    regionControllerBack:controllerBack,
    regionControllerStep:controllerStep,
    regionControllerSelect:controllerSelect,
    regionControllerToggleGrid:controllerToggleGrid
  });

  const observer=new MutationObserver(()=>{
    if(stage.dataset.regionGeometryV2!=='true')return;
    enforceWorld();
  });
  observer.observe(world,{attributes:true,attributeFilter:['style'],subtree:false});
  window.addEventListener('resize',()=>{if(state.focusBBox&&state.phase!=='focus')fitFocus(state.angle);else renderOverlay()});

  window.addEventListener('message',event=>{
    if(event.origin!==location.origin||event.source!==parent)return;
    const data=event.data;if(!data||data.source!=='shaelvien-regiondefiner-host')return;
    if(data.type==='world-source'){
      state.worldReady=true;
      if(NEW_FLOW){
        try{baseApi.showAllParallax?.()}catch{}
        document.querySelectorAll('.region-tier-preview').forEach(node=>node.hidden=true);
        stage.classList.remove('region-tier-previewing','region-selection-only','region-build-mode');
        restoreFullView();setPhase('focus');announce('Draw a rough focus shape on the world. Cursor and touch use the same selection actions.');
      }
    }else if(data.type==='catalog-v2'){
      const regions=Array.isArray(data.regions)?data.regions:[];
      if(!NEW_FLOW&&REQUESTED_REGION_ID){const region=regions.find(item=>String(item?.id||'')===REQUESTED_REGION_ID);if(region)adoptRegion(region)}
    }else if(data.type==='region-created'){
      state.pending=false;state.regionName=String(data.region?.name||state.regionName||'');adoptRegion(data.region||{});setPhase('saved');announce(`${state.regionName||'Region'} saved. The world map was not copied or cut.`);
    }else if(data.type==='claim-requested'){
      state.pending=false;renderAll();publishState();if(data.result?.success){setPhase('saved');announce(String(data.result?.message||'Claim request sent.'))}else announce(String(data.result?.message||'Claim request was not accepted.'));
    }else if(data.type==='error'){
      state.pending=false;renderAll();publishState();announce(String(data.message||'Region operation failed.'));
    }
  });

  clearWorldMask();
  if(NEW_FLOW){state.visibleTiers=new Set(collectTierIndices());restoreFullView();setPhase('focus')}else{panel.hidden=true;state.phase='existing';stage.dataset.regionGeometryPhase='existing';publishState()}
  post({type:'ready'});
}
boot();
})();
