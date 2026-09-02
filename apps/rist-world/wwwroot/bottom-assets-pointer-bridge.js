(()=>{
 'use strict';

 // The canonical bottom asset rail stages a tile by replaying a pointerdown on
 // the hidden Blazor pallet. The original pointer remains captured by the
 // bottom card, however, so its move/up events never reach WorldMap. Bridge
 // those events back into the Blazor workspace and tolerate synthetic pointer
 // capture after a quick tap/release.
 const active=new Map();
 let forwarding=false;

 const workspace=()=>document.querySelector('.table-workspace');
 const cardFor=e=>e.target?.closest?.('.rist-bottom-asset-card');
 const trayFor=e=>e.target?.closest?.('.tray-item');
 const movedEnough=s=>Math.abs(s.lastX-s.startX)+Math.abs(s.lastY-s.startY)>7;

 function forward(type,state,x=state.lastX,y=state.lastY,buttons=type==='pointerup'?0:1){
  const host=workspace();
  if(!host)return;
  forwarding=true;
  try{
   host.dispatchEvent(new PointerEvent(type,{
    bubbles:true,
    cancelable:true,
    pointerId:state.pointerId,
    pointerType:state.pointerType,
    isPrimary:true,
    clientX:x,
    clientY:y,
    button:0,
    buttons
   }));
  }finally{forwarding=false;}
 }

 function finishAfterSyntheticDown(state){
  // Let Blazor finish BeginTrayDrag first; then replay the latest real finger
  // position. If the finger was already released, also replay pointerup.
  setTimeout(()=>{
   if(!active.has(state.pointerId))return;
   if(movedEnough(state))forward('pointermove',state,state.lastX,state.lastY,1);
   if(state.ended){
    forward('pointerup',state,state.lastX,state.lastY,0);
    active.delete(state.pointerId);
   }
  },0);
 }

 document.addEventListener('pointerdown',event=>{
  if(forwarding)return;
  const card=cardFor(event);
  if(card&&event.isTrusted){
   active.set(event.pointerId,{
    pointerId:event.pointerId,
    pointerType:event.pointerType||'touch',
    startX:event.clientX,
    startY:event.clientY,
    lastX:event.clientX,
    lastY:event.clientY,
    ended:false,
    handedOff:false
   });
   return;
  }

  // bottom-assets-maptools.js dispatches this synthetic pointerdown after the
  // matching asset has been staged into the hidden Blazor pallet.
  const tray=trayFor(event);
  const state=tray&&active.get(event.pointerId);
  if(state&&!event.isTrusted){
   state.handedOff=true;
   finishAfterSyntheticDown(state);
  }
 },true);

 document.addEventListener('pointermove',event=>{
  if(forwarding||!event.isTrusted)return;
  const state=active.get(event.pointerId);
  if(!state)return;
  state.lastX=event.clientX;
  state.lastY=event.clientY;
  if(state.handedOff&&movedEnough(state))forward('pointermove',state,event.clientX,event.clientY,1);
 },true);

 document.addEventListener('pointerup',event=>{
  if(forwarding||!event.isTrusted)return;
  const state=active.get(event.pointerId);
  if(!state)return;
  state.lastX=event.clientX;
  state.lastY=event.clientY;
  state.ended=true;
  if(state.handedOff){
   if(movedEnough(state))forward('pointermove',state,event.clientX,event.clientY,1);
   forward('pointerup',state,event.clientX,event.clientY,0);
   active.delete(event.pointerId);
  }else{
   // Keep the completed pointer briefly because the asset chooser may still
   // be opening/staging. A later synthetic tray pointerdown will finish it.
   setTimeout(()=>active.delete(event.pointerId),2200);
  }
 },true);

 document.addEventListener('pointercancel',event=>{
  if(!event.isTrusted)return;
  const state=active.get(event.pointerId);
  if(!state)return;
  state.ended=true;
  if(state.handedOff)forward('pointercancel',state,event.clientX,event.clientY,0);
  active.delete(event.pointerId);
 },true);

 // Synthetic handoff can occur after the physical pointer is released. The
 // previous capturePointer implementation throws in that case and aborts the
 // Blazor drag. Preserve capture when possible, but make it safe when not.
 const installSafeCapture=()=>{
  if(!window.ristWorld||window.ristWorld.__bottomAssetSafeCapture)return false;
  window.ristWorld.capturePointer=(pointerId,x,y)=>{
   try{
    const el=document.elementFromPoint(x,y);
    if(el?.setPointerCapture)el.setPointerCapture(pointerId);
   }catch{}
  };
  window.ristWorld.__bottomAssetSafeCapture=true;
  return true;
 };
 if(!installSafeCapture()){
  const timer=setInterval(()=>{if(installSafeCapture())clearInterval(timer)},25);
  setTimeout(()=>clearInterval(timer),5000);
 }
})();
