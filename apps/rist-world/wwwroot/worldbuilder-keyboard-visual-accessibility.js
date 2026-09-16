(()=>{
 'use strict';
 const VERSION='20260916-keyboard-visual-accessibility-1';
 if(window.RistWorldBuilderKeyboardVisualAccessibility?.version===VERSION)return;
 const STYLE_ID='rist-worldbuilder-keyboard-visual-accessibility-style';
 let frame=0;
 let observer=null;

 function ensureStyle(){
  if(document.getElementById(STYLE_ID))return;
  const style=document.createElement('style');style.id=STYLE_ID;
  style.textContent=`
   /* Uploaded key artwork owns visible labels. Semantic button aria-labels own accessibility. */
   .worldbuilder-studio .wb-device-keyboard .wb-device-key.wb-final-art-loaded>strong,
   .worldbuilder-studio .wb-device-keyboard .wb-device-key.wb-final-art-loaded>small{
    display:none!important;
   }
   .worldbuilder-studio .wb-device-keyboard .wb-persistent-dpad{
    display:grid!important;
    visibility:visible!important;
    opacity:1!important;
    pointer-events:auto!important;
    z-index:30!important;
    left:1%!important;
    right:auto!important;
    top:32%!important;
    bottom:2%!important;
    width:22%!important;
    height:auto!important;
   }
   .worldbuilder-studio .wb-device-keyboard .wb-dpad-key{
    position:relative!important;
    overflow:hidden!important;
    pointer-events:auto!important;
    touch-action:manipulation!important;
    color:transparent!important;
    font-size:0!important;
    text-shadow:none!important;
    background:transparent!important;
    border:0!important;
    box-shadow:none!important;
   }
   .worldbuilder-studio .wb-device-keyboard .wb-dpad-readout{
    position:absolute!important;
    width:1px!important;
    height:1px!important;
    padding:0!important;
    margin:-1px!important;
    overflow:hidden!important;
    clip:rect(0,0,0,0)!important;
    clip-path:inset(50%)!important;
    white-space:nowrap!important;
    border:0!important;
   }
   .worldbuilder-studio .wb-device-keyboard .wb-final-dpad-art{
    position:absolute!important;
    inset:0!important;
    width:100%!important;
    height:100%!important;
    object-fit:fill!important;
    pointer-events:none!important;
    z-index:1!important;
   }
  `;
  document.head.appendChild(style);
 }
 function refresh(){
  ensureStyle();
  try{window.RistWorldBuilderGridCursor?.refresh?.()}catch{}
  try{window.RistWorldBuilderFinalKeyboardAuthority?.refresh?.()}catch{}
 }
 function schedule(){if(frame)return;frame=requestAnimationFrame(()=>{frame=0;refresh()})}
 function start(){
  refresh();
  observer=new MutationObserver(records=>{
   if(records.some(record=>[...record.addedNodes].some(node=>node.nodeType===1&&(node.matches?.('.wb-device-keyboard,.wb-persistent-dpad,.wb-device-key')||node.querySelector?.('.wb-device-keyboard,.wb-persistent-dpad,.wb-device-key')))))schedule();
  });
  observer.observe(document.documentElement,{childList:true,subtree:true});
  window.addEventListener('pageshow',schedule);
  window.addEventListener('focus',schedule,{passive:true});
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)schedule()});
 }
 window.RistWorldBuilderKeyboardVisualAccessibility={version:VERSION,refresh:schedule};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
