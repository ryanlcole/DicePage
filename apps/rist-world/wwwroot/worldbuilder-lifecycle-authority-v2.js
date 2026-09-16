(()=>{
 'use strict';

 const VERSION='20260916-worldbuilder-lifecycle-v2-2';
 const STYLE_ID='rist-worldbuilder-lifecycle-v2-style';
 const RELOAD_KEY='rist.worldbuilder.iosForegroundReloadAt.v2';
 const ACTIVE_KEY='rist.worldbuilder.wasActiveBeforeBackground.v2';
 const WORKSPACE_KEY='rist.shell.workspace.v1';
 let frame=0;
 let observer=null;
 let hiddenAt=0;
 let reloading=false;

 const studio=()=>document.querySelector('.worldbuilder-studio');
 const isIOS=()=>/iPad|iPhone|iPod/i.test(navigator.userAgent)||(/Macintosh/i.test(navigator.userAgent)&&navigator.maxTouchPoints>1);

 function ensureStyle(){
  if(document.getElementById(STYLE_ID))return;
  const style=document.createElement('style');
  style.id=STYLE_ID;
  style.textContent=`
   body.wb-immersive-worldbuilder{overflow:hidden!important;background:#020609!important}
   body.wb-immersive-worldbuilder #app{height:100dvh!important;min-height:100dvh!important;overflow:hidden!important}
   body.wb-immersive-worldbuilder .alpha-world-stage.worldbuilder-stage{
    position:fixed!important;
    inset:20px 0 0 0!important;
    width:auto!important;
    height:auto!important;
    min-height:0!important;
    overflow:hidden!important;
    background:#020609!important;
   }
   body.wb-immersive-worldbuilder .alpha-world-stage.worldbuilder-stage .worldbuilder-studio{
    position:absolute!important;
    inset:0!important;
    width:100%!important;
    height:100%!important;
    min-height:0!important;
    display:block!important;
    overflow:hidden!important;
   }
   body.wb-immersive-worldbuilder .worldbuilder-studio>.studio-workbench{display:none!important}
   body.wb-immersive-worldbuilder .worldbuilder-studio>.studio-viewer{
    position:absolute!important;
    inset:0 0 var(--wb-device-keyboard-h) 0!important;
    width:auto!important;
    height:auto!important;
    min-height:0!important;
    padding:0!important;
    overflow:hidden!important;
   }
   body.wb-immersive-worldbuilder .worldbuilder-studio>.studio-viewer>.studio-viewer-canvas{
    width:100%!important;
    height:100%!important;
    min-height:0!important;
   }
   body.wb-immersive-worldbuilder .worldbuilder-studio>.studio-command-slider{
    position:absolute!important;
    left:0!important;
    right:0!important;
    bottom:var(--wb-device-keyboard-h)!important;
    height:0!important;
    min-height:0!important;
    margin:0!important;
    padding:0!important;
    border:0!important;
    transform:none!important;
    overflow:visible!important;
    pointer-events:none!important;
    background:transparent!important;
   }
   body.wb-immersive-worldbuilder .worldbuilder-studio>.studio-command-slider>.studio-command-rail{display:none!important}
   body.wb-immersive-worldbuilder .worldbuilder-studio:has(.world-asset-rail-shell)>.studio-command-slider{
    height:62px!important;
    pointer-events:auto!important;
    z-index:230!important;
   }
   body.wb-immersive-worldbuilder .worldbuilder-studio:has(.world-asset-rail-shell)>.studio-viewer{
    bottom:calc(var(--wb-device-keyboard-h) + 62px)!important;
   }
   body.wb-immersive-worldbuilder .site-copyright-notice,
   body.wb-immersive-worldbuilder .wb-worldbuilder-only-footer-strip,
   body.wb-immersive-worldbuilder .release-footer-region:has(.site-copyright-notice){
    display:none!important;
    height:0!important;
    min-height:0!important;
    max-height:0!important;
    margin:0!important;
    padding:0!important;
    border:0!important;
    overflow:hidden!important;
   }
   body.wb-immersive-worldbuilder .wb-device-keyboard,
   body.wb-immersive-worldbuilder .wb-device-keyboard .wb-device-mode-row,
   body.wb-immersive-worldbuilder .wb-device-keyboard .wb-device-keys,
   body.wb-immersive-worldbuilder .wb-device-keyboard .wb-device-key,
   body.wb-immersive-worldbuilder .wb-device-keyboard .wb-dpad-key{
    pointer-events:auto!important;
    touch-action:manipulation!important;
   }
   body.wb-immersive-worldbuilder .wb-device-keyboard .wb-device-key,
   body.wb-immersive-worldbuilder .wb-device-keyboard .wb-dpad-key{
    border:2px solid rgba(197,145,62,.94)!important;
    box-shadow:inset 0 0 0 1px rgba(255,214,132,.28),0 0 0 1px rgba(42,24,7,.7)!important;
   }
   body.wb-immersive-worldbuilder .wb-device-keyboard .wb-device-mode{
    border:2px solid rgba(197,145,62,.94)!important;
    box-sizing:border-box!important;
   }
   body.wb-immersive-worldbuilder .wb-device-keyboard .wb-device-mode[aria-selected="true"]{
    border-color:#38bfff!important;
    box-shadow:0 0 8px rgba(56,191,255,.55)!important;
   }
   body.wb-immersive-worldbuilder .wb-device-keyboard .wb-keyboard-v2-art,
   body.wb-immersive-worldbuilder .wb-device-keyboard .wb-keyboard-v2-dpad-art{
    width:100%!important;
    height:100%!important;
    object-fit:contain!important;
    pointer-events:none!important;
   }
  `;
  document.head.appendChild(style);
 }

 function setFooterContext(active){
  document.querySelectorAll('.site-copyright-notice').forEach(node=>{
   const region=node.closest('.release-footer-region');
   if(active){
    node.dataset.wbLifecycleHidden='1';
    node.setAttribute('aria-hidden','true');
    node.style.setProperty('display','none','important');
    if(region){region.classList.add('wb-worldbuilder-only-footer-strip');region.dataset.wbLifecycleHidden='1'}
   }else if(node.dataset.wbLifecycleHidden==='1'){
    delete node.dataset.wbLifecycleHidden;
    node.removeAttribute('aria-hidden');
    node.style.removeProperty('display');
   }
   if(!active&&region?.dataset.wbLifecycleHidden==='1'){
    delete region.dataset.wbLifecycleHidden;
    region.classList.remove('wb-worldbuilder-only-footer-strip');
   }
  });
 }

 function rememberActiveWorldbuilder(){
  const active=!!studio();
  try{
   sessionStorage.setItem(ACTIVE_KEY,active?'1':'0');
   if(active)localStorage.setItem(WORKSPACE_KEY,'world');
  }catch{}
  return active;
 }

 function wasActiveWorldbuilder(){
  try{return sessionStorage.getItem(ACTIVE_KEY)==='1'}catch{return false}
 }

 function applyContext(){
  ensureStyle();
  const active=!!studio();
  document.body?.classList.toggle('wb-immersive-worldbuilder',active);
  setFooterContext(active);
 }

 function refreshAuthorities(source){
  applyContext();
  try{window.RistWorldBuilderKeyboardAuthority?.refresh?.()}catch{}
  try{window.RistWorldBuilderGridCursor?.refresh?.()}catch{}
  try{window.RistWorldBuilderModeKeyboardRelocation?.refresh?.()}catch{}
  try{window.RistWorldTickerData?.refresh?.()}catch{}
  try{window.ristViewerNavigation?.refresh?.()}catch{}
  try{window.ristViewerAuthority?.refresh?.()}catch{}
  try{window.dispatchEvent(new Event('resize'))}catch{}
  try{window.dispatchEvent(new CustomEvent('rist:viewer-state',{detail:{source}}))}catch{}
 }

 function guardedReload(reason){
  if(reloading||!isIOS()||document.hidden)return false;
  const active=wasActiveWorldbuilder()||!!studio();
  if(!active)return false;
  const now=Date.now();
  let last=0;
  try{last=Number(sessionStorage.getItem(RELOAD_KEY)||0)}catch{}
  if(now-last<3000){refreshAuthorities(`${reason}-reload-guard`);return false}
  reloading=true;
  try{
   localStorage.setItem(WORKSPACE_KEY,'world');
   sessionStorage.setItem(RELOAD_KEY,String(now));
   sessionStorage.setItem('rist.worldbuilder.lastForegroundReason',reason);
  }catch{}
  location.reload();
  return true;
 }

 function foreground(source){
  if(document.hidden)return;
  if(isIOS()&&hiddenAt>0&&Date.now()-hiddenAt>100){
   if(guardedReload(source))return;
  }
  hiddenAt=0;
  refreshAuthorities(source);
 }

 function markBackground(){
  hiddenAt=Date.now();
  rememberActiveWorldbuilder();
 }

 function schedule(){if(frame)return;frame=requestAnimationFrame(()=>{frame=0;applyContext()})}

 function start(){
  ensureStyle();applyContext();
  observer=new MutationObserver(schedule);
  observer.observe(document.getElementById('app')||document.body,{childList:true,subtree:true});

  document.addEventListener('visibilitychange',()=>{
   if(document.hidden){markBackground();return}
   foreground('visibility-return');
  });
  window.addEventListener('pagehide',markBackground,{passive:true});
  window.addEventListener('pageshow',event=>{
   if(event.persisted&&isIOS()&&wasActiveWorldbuilder()){
    hiddenAt=hiddenAt||Date.now()-250;
    if(guardedReload('bfcache-return'))return;
   }
   foreground('pageshow');
  },{passive:true});
  window.addEventListener('focus',()=>{
   if(hiddenAt>0&&Date.now()-hiddenAt>100)foreground('focus-return');
   else schedule();
  },{passive:true});
  window.addEventListener('orientationchange',()=>setTimeout(()=>refreshAuthorities('orientationchange'),80),{passive:true});
 }

 const api={
  version:VERSION,
  refresh:()=>refreshAuthorities('manual'),
  foreground:()=>foreground('manual-foreground'),
  state:()=>({worldbuilder:!!studio(),ios:isIOS(),hidden:document.hidden,hiddenAt,reloading,wasActive:wasActiveWorldbuilder()})
 };
 window.RistWorldBuilderLifecycleAuthority=api;
 window.RistWorldBuilderImmersivePolish=api;

 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
