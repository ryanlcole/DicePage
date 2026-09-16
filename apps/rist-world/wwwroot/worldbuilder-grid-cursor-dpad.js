(()=>{
 'use strict';

 const STYLE_ID='rist-worldbuilder-grid-cursor-dpad-css';
 const CURSOR_KEY='rist.worldbuilder.gridCursor.v1';
 let root=null,keyboard=null,dpad=null,cursor=null,readout=null,observer=null,frame=0,lastN=0;
 const clamp=(value,min,max)=>Math.max(min,Math.min(max,value));
 const studio=()=>document.querySelector('.worldbuilder-studio');
 const viewer=()=>studio()?.querySelector('.studio-viewer-canvas')||null;
 const grid=()=>studio()?.querySelector('.studio-viewer-grid')||viewer();
 const authority=()=>window.ristViewerAuthority;

 function ensureStyle(){
  if(document.getElementById(STYLE_ID))return;
  const link=document.createElement('link');
  link.id=STYLE_ID;
  link.rel='stylesheet';
  link.href='./css/worldbuilder-grid-cursor-dpad.css?v=20260915-grid-cursor-dpad-1';
  document.head.appendChild(link);
 }
 function readCursor(){
  try{
   const parsed=JSON.parse(localStorage.getItem(CURSOR_KEY)||'null');
   if(parsed&&Number.isFinite(parsed.col)&&Number.isFinite(parsed.row))return parsed;
  }catch{}
  return null;
 }
 function writeCursor(state){try{localStorage.setItem(CURSOR_KEY,JSON.stringify(state))}catch{}}
 function visibleN(){
  const state=authority()?.get?.()||{};
  const fromState=Math.round(Number(state.visibleCells));
  if(Number.isFinite(fromState)&&fromState>0)return clamp(fromState,1,300);
  const fromDataset=Math.round(Number(studio()?.dataset?.cameraVisibleCells));
  if(Number.isFinite(fromDataset)&&fromDataset>0)return clamp(fromDataset,1,300);
  return 12;
 }
 function squareGridRect(){
  const node=grid();
  const rect=node?.getBoundingClientRect();
  if(!rect||rect.width<1||rect.height<1)return null;
  const side=Math.min(rect.width,rect.height);
  return{left:rect.left+((rect.width-side)/2),top:rect.top+((rect.height-side)/2),width:side,height:side};
 }
 function current(){
  const n=visibleN();
  const saved=readCursor();
  const fallback=Math.floor((n-1)/2);
  return{n,col:clamp(Math.round(saved?.col??fallback),0,n-1),row:clamp(Math.round(saved?.row??fallback),0,n-1)};
 }
 function announce(message){
  const live=keyboard?.querySelector('.wb-device-live-region');
  if(live)live.textContent=message;
 }
 function setCursor(col,row,{speak=true}={}){
  const n=visibleN();
  const state={n,col:clamp(Math.round(col),0,n-1),row:clamp(Math.round(row),0,n-1)};
  writeCursor(state);
  renderCursor();
  if(speak)announce(`Grid square column ${state.col+1}, row ${state.row+1} of ${n}`);
  window.dispatchEvent(new CustomEvent('rist:worldbuilder-grid-cursor',{detail:{...state,source:'d-pad'}}));
  return state;
 }
 function renderCursor(){
  const area=viewer(),bounds=squareGridRect();
  if(!area||!bounds)return;
  const state=current();
  if(!cursor||!cursor.isConnected){
   cursor=document.createElement('div');
   cursor.className='wb-grid-cursor';
   cursor.setAttribute('aria-hidden','true');
   area.appendChild(cursor);
  }
  const areaRect=area.getBoundingClientRect();
  const cell=bounds.width/state.n;
  const left=(bounds.left-areaRect.left)+(state.col*cell);
  const top=(bounds.top-areaRect.top)+(state.row*cell);
  cursor.style.left=`${left}px`;
  cursor.style.top=`${top}px`;
  cursor.style.width=`${cell}px`;
  cursor.style.height=`${cell}px`;
  cursor.dataset.col=String(state.col);
  cursor.dataset.row=String(state.row);
  cursor.dataset.n=String(state.n);
  lastN=state.n;
  if(readout)readout.textContent=`${state.col+1},${state.row+1} · ${state.n}×${state.n}`;
 }
 function move(dx,dy){const state=current();return setCursor(state.col+dx,state.row+dy)}
 function cursorClientPoint(){
  const bounds=squareGridRect();if(!bounds)return null;
  const state=current(),cell=bounds.width/state.n;
  return{x:bounds.left+((state.col+.5)*cell),y:bounds.top+((state.row+.5)*cell),...state};
 }
 function syntheticSelect(point){
  const area=viewer();if(!area||!point)return false;
  const target=document.elementFromPoint(point.x,point.y)||area;
  const pointerId=19015;
  const base={bubbles:true,cancelable:true,composed:true,pointerId,pointerType:'mouse',isPrimary:true,button:0,buttons:1,clientX:point.x,clientY:point.y};
  try{
   target.dispatchEvent(new PointerEvent('pointerdown',base));
   target.dispatchEvent(new PointerEvent('pointerup',{...base,buttons:0}));
   target.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,clientX:point.x,clientY:point.y,button:0}));
   return true;
  }catch{
   try{target.dispatchEvent(new MouseEvent('click',{bubbles:true,cancelable:true,clientX:point.x,clientY:point.y,button:0}));return true}catch{return false}
  }
 }
 function select(){
  const point=cursorClientPoint();if(!point)return;
  const detail={column:point.col,row:point.row,n:point.n,clientX:point.x,clientY:point.y,normalizedX:(point.col+.5)/point.n,normalizedY:(point.row+.5)/point.n,source:'d-pad'};
  window.dispatchEvent(new CustomEvent('rist:worldbuilder-grid-cursor-select',{detail}));
  syntheticSelect(point);
  cursor?.setAttribute('data-selected','true');
  setTimeout(()=>cursor?.removeAttribute('data-selected'),120);
  announce(`Selected grid square column ${point.col+1}, row ${point.row+1}`);
 }
 function key(label,cls,action,aria){
  const button=document.createElement('button');button.type='button';button.className=`wb-dpad-key ${cls}`;button.textContent=label;button.setAttribute('aria-label',aria);button.dataset.accessRole='grid-navigation-key';button.addEventListener('click',action);return button;
 }
 function buildDpad(host){
  keyboard=host;
  keyboard.classList.add('wb-has-dpad');
  keyboard.querySelector('.wb-persistent-dpad')?.remove();
  dpad=document.createElement('div');dpad.className='wb-persistent-dpad';dpad.setAttribute('role','group');dpad.setAttribute('aria-label','Grid selection d-pad. Moves the highlighted viewer square one square at a time.');dpad.dataset.accessTranslation='available';
  readout=document.createElement('div');readout.className='wb-dpad-readout';readout.setAttribute('aria-live','polite');
  dpad.append(
   readout,
   key('↑','wb-dpad-up',()=>move(0,-1),'Move highlighted grid square up one square'),
   key('←','wb-dpad-left',()=>move(-1,0),'Move highlighted grid square left one square'),
   key('Select','wb-dpad-select',select,'Select the highlighted grid square'),
   key('→','wb-dpad-right',()=>move(1,0),'Move highlighted grid square right one square'),
   key('↓','wb-dpad-down',()=>move(0,1),'Move highlighted grid square down one square')
  );
  keyboard.appendChild(dpad);
  renderCursor();
 }
 function mount(){
  const nextRoot=studio(),nextKeyboard=nextRoot?.querySelector('.wb-device-keyboard');
  if(!nextRoot||!nextKeyboard)return;
  root=nextRoot;
  if(nextKeyboard!==keyboard||!dpad?.isConnected)buildDpad(nextKeyboard);
  if(!cursor?.isConnected)renderCursor();
 }
 function schedule(){if(frame)return;frame=requestAnimationFrame(()=>{frame=0;mount();const n=visibleN();if(n!==lastN){const previous=readCursor(),oldN=Math.max(1,lastN||previous?.n||n);const ratioX=(Number(previous?.col)||0)/(Math.max(1,oldN-1));const ratioY=(Number(previous?.row)||0)/(Math.max(1,oldN-1));setCursor(Math.round(ratioX*Math.max(0,n-1)),Math.round(ratioY*Math.max(0,n-1)),{speak:false})}else renderCursor()})}
 function onKey(event){
  if(!root?.isConnected||root.classList.contains('wb-device-collapsed'))return;
  const target=event.target;
  if(target instanceof HTMLInputElement||target instanceof HTMLTextAreaElement||target instanceof HTMLSelectElement||target?.isContentEditable)return;
  if(!(event.altKey||event.ctrlKey))return;
  if(event.key==='ArrowLeft'){event.preventDefault();move(-1,0)}
  else if(event.key==='ArrowRight'){event.preventDefault();move(1,0)}
  else if(event.key==='ArrowUp'){event.preventDefault();move(0,-1)}
  else if(event.key==='ArrowDown'){event.preventDefault();move(0,1)}
  else if(event.key==='Enter'){event.preventDefault();select()}
 }

 ensureStyle();
 mount();
 observer=new MutationObserver(schedule);observer.observe(document.documentElement,{childList:true,subtree:true});
 window.addEventListener('resize',schedule,{passive:true});
 window.addEventListener('orientationchange',schedule,{passive:true});
 window.addEventListener('rist:viewer-state',schedule);
 window.addEventListener('rist:camera-window',schedule);
 document.addEventListener('keydown',onKey,true);
 window.RistWorldBuilderGridCursor={
  get:current,
  move,
  select,
  set:(column,row)=>setCursor(Number(column)||0,Number(row)||0),
  center(){const n=visibleN(),mid=Math.floor((n-1)/2);return setCursor(mid,mid)},
  clientPoint:cursorClientPoint,
  refresh:schedule
 };
})();
