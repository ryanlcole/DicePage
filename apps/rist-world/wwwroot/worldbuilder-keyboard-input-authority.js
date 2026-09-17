(()=>{
 'use strict';

 const VERSION='20260917-keyboard-input-1';
 if(window.RistWorldBuilderKeyboardInput?.version===VERSION)return;

 const TAP_SLOP=24;
 const FALLBACK_DELAY=40;
 const STYLE_ID='rist-worldbuilder-keyboard-input-authority-style';
 let active=null;
 let pending=null;
 let assisted=0;

 const keyboard=()=>document.querySelector('.worldbuilder-studio .wb-device-keyboard');
 const assetKeyboardOpen=host=>!!host&&(host.classList.contains('wb-asset-keyboard-open')||host.dataset.assetKeyboard==='open');
 const supportedPointer=event=>event.pointerType==='touch'||event.pointerType==='pen';
 const inside=(rect,x,y,pad=0)=>x>=rect.left-pad&&x<=rect.right+pad&&y>=rect.top-pad&&y<=rect.bottom+pad;

 function ensureStyle(){
  if(document.getElementById(STYLE_ID))return;
  const style=document.createElement('style');
  style.id=STYLE_ID;
  style.textContent=`
   .worldbuilder-studio .wb-device-keyboard .wb-device-key,
   .worldbuilder-studio .wb-device-keyboard .wb-dpad-key,
   .worldbuilder-studio .wb-device-keyboard .wb-device-menu,
   .worldbuilder-studio .wb-device-keyboard .wb-device-collapse,
   .worldbuilder-studio .wb-device-keyboard .wb-device-grabber{
    touch-action:none!important;
   }
   .worldbuilder-studio .wb-device-keyboard .wb-device-mode-row,
   .worldbuilder-studio .wb-device-keyboard .wb-device-mode{
    touch-action:pan-x!important;
   }
  `;
  document.head.appendChild(style);
 }

 function interactiveButtonAt(host,x,y){
  if(!host)return null;
  const buttons=[...host.querySelectorAll('button:not(:disabled)')];
  for(let index=buttons.length-1;index>=0;index--){
   const button=buttons[index];
   if(button.classList.contains('wb-asset-key')||button.classList.contains('wb-asset-size-pad'))continue;
   if(!button.isConnected||button.getClientRects().length===0)continue;
   const style=getComputedStyle(button);
   if(style.display==='none'||style.visibility==='hidden'||style.pointerEvents==='none')continue;
   const rect=button.getBoundingClientRect();
   if(rect.width>0&&rect.height>0&&inside(rect,x,y))return button;
  }
  return null;
 }

 function clearActive(){
  active?.button?.classList.remove('wb-touch-active');
  active=null;
 }

 function pointerDown(event){
  if(!supportedPointer(event))return;
  const host=keyboard();
  if(!host||assetKeyboardOpen(host))return;
  const rect=host.getBoundingClientRect();
  if(!inside(rect,event.clientX,event.clientY))return;
  const button=interactiveButtonAt(host,event.clientX,event.clientY);
  if(!button)return;
  clearActive();
  active={id:event.pointerId,button,startX:event.clientX,startY:event.clientY,moved:false};
  button.classList.add('wb-touch-active');
 }

 function pointerMove(event){
  if(!active||active.id!==event.pointerId)return;
  const distance=Math.hypot(event.clientX-active.startX,event.clientY-active.startY);
  if(distance>TAP_SLOP){active.moved=true;active.button?.classList.remove('wb-touch-active')}
 }

 function matchingClick(event,record){
  const target=event.target;
  return !!record?.button&&!!target&&(target===record.button||record.button.contains?.(target));
 }

 function clickCapture(event){
  if(pending&&matchingClick(event,pending))pending.clicked=true;
 }

 function pointerUp(event){
  if(!active||active.id!==event.pointerId)return;
  const state=active;
  active=null;
  state.button?.classList.remove('wb-touch-active');
  if(state.moved)return;
  const host=keyboard();
  if(!host||assetKeyboardOpen(host))return;

  let button=state.button?.isConnected?state.button:null;
  if(button){
   const rect=button.getBoundingClientRect();
   if(!inside(rect,event.clientX,event.clientY,10))button=null;
  }
  button=button||interactiveButtonAt(host,event.clientX,event.clientY);
  if(!button||button.disabled)return;

  const record={button,clicked:false,created:performance.now()};
  pending=record;
  setTimeout(()=>{
   if(pending!==record)return;
   pending=null;
   if(record.clicked||!record.button?.isConnected||record.button.disabled)return;
   assisted++;
   try{record.button.focus({preventScroll:true})}catch{}
   record.button.click();
  },FALLBACK_DELAY);
 }

 function pointerCancel(event){
  if(active?.id===event.pointerId)clearActive();
 }

 function reset(){clearActive();pending=null}

 ensureStyle();
 window.addEventListener('pointerdown',pointerDown,{capture:true,passive:true});
 window.addEventListener('pointermove',pointerMove,{capture:true,passive:true});
 window.addEventListener('pointerup',pointerUp,{capture:true,passive:true});
 window.addEventListener('pointercancel',pointerCancel,{capture:true,passive:true});
 window.addEventListener('click',clickCapture,{capture:true,passive:true});
 window.addEventListener('pagehide',reset,{passive:true});
 window.addEventListener('pageshow',reset,{passive:true});

 window.RistWorldBuilderKeyboardInput={
  version:VERSION,
  refresh:ensureStyle,
  reset,
  state:()=>({active:!!active,pending:!!pending,assisted,tapSlop:TAP_SLOP})
 };
})();
