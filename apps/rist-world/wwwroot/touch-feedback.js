(()=>{
 'use strict';
 const selector='button,[role="button"],label,a,.rist-bottom-folder-card,.rist-bottom-asset-card,.rist-folder-fixed';
 let active=null,clearTimer=0;
 const clear=()=>{if(clearTimer){clearTimeout(clearTimer);clearTimer=0}if(active){active.classList.remove('rist-touch-active');active=null}};
 document.addEventListener('pointerdown',event=>{
  if(event.pointerType&&event.pointerType!=='touch'&&event.pointerType!=='pen')return;
  const target=event.target instanceof Element?event.target.closest(selector):null;
  if(!target||target.matches(':disabled,[aria-disabled="true"]'))return;
  clear();active=target;target.classList.add('rist-touch-active');
 },{capture:true,passive:true});
 for(const type of ['pointerup','pointercancel','lostpointercapture'])document.addEventListener(type,()=>{clearTimer=setTimeout(clear,90)},{capture:true,passive:true});
 document.addEventListener('click',()=>{clearTimer=setTimeout(clear,110)},{capture:true,passive:true});
})();