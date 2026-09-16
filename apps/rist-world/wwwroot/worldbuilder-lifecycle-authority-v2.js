(()=>{
 'use strict';

 const VERSION='20260916-worldbuilder-lifecycle-v2-1';
 const STYLE_ID='rist-worldbuilder-lifecycle-v2-style';
 const RELOAD_KEY='rist.worldbuilder.iosForegroundReloadAt.v2';
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
   body.wb-immersive-worldbuilder .site-copyright-notice{
    display:none!important;
    height:0!important;
    min-height:0!important;
    max-height:0!important;
    margin:0!important;
    padding:0!important;
    border:0!important;
    overflow:hidden!important;
   }
   body.wb-immersive-worldbuilder .wb-worldbuilder-only-footer-strip{
    display:none!important;
    height:0!important;
    min-height:0!important;
    max-height:0!important;
    margin:0!important;
    padding:0!important;
    border:0!important;
    overflow:hidden!important;
   }
  `;
  document.head.appendChild(style);
 }

 function setFooterContext(active){
  document.querySelectorAll('.site-copyright-notice').forEach(node=>{
   const region=node.closest('.release-footer-region');
   const regionWasTickerOnly=!!region&&region.getBoundingClientRect().height<=24;
   if(active){
    node.dataset.wbLifecycleHidden='1';
    node.setAttribute('aria-hidden','true');
    node.style.setProperty('display','none','important');
    if(regionWasTickerOnly){
     region.classList.add('wb-worldbuilder-only-footer-strip');
     region.dataset.wbLifecycleHidden='1';
    }
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
  if(reloading||!isIOS()||document.hidden||!studio())return false;
  const now=Date.now();
  let last=0;
  try{last=Number(sessionStorage.getItem(RELOAD_KEY)||0)}catch{}
  if(now-last<3000){refreshAuthorities(`${reason}-reload-guard`);return false}
  reloading=true;
  try{sessionStorage.setItem(RELOAD_KEY,String(now));sessionStorage.setItem('rist.worldbuilder.lastForegroundReason',reason)}catch{}
  location.reload();
  return true;
 }

 function foreground(source){
  if(document.hidden)return;
  if(isIOS()&&hiddenAt>0&&Date.now()-hiddenAt>150){
   if(guardedReload(source))return;
  }
  hiddenAt=0;
  refreshAuthorities(source);
 }

 function schedule(){if(frame)return;frame=requestAnimationFrame(()=>{frame=0;applyContext()})}

 function start(){
  ensureStyle();applyContext();
  observer=new MutationObserver(schedule);
  observer.observe(document.getElementById('app')||document.body,{childList:true,subtree:true});

  document.addEventListener('visibilitychange',()=>{
   if(document.hidden){hiddenAt=Date.now();return}
   foreground('visibility-return');
  });
  window.addEventListener('pagehide',()=>{hiddenAt=Date.now()},{passive:true});
  window.addEventListener('pageshow',event=>{
   if(event.persisted&&isIOS()&&studio()){guardedReload('bfcache-return');return}
   foreground('pageshow');
  },{passive:true});
  window.addEventListener('focus',()=>{
   if(hiddenAt>0&&Date.now()-hiddenAt>250)foreground('focus-return');
   else schedule();
  },{passive:true});
  window.addEventListener('orientationchange',()=>setTimeout(()=>refreshAuthorities('orientationchange'),80),{passive:true});
 }

 const api={
  version:VERSION,
  refresh:()=>refreshAuthorities('manual'),
  foreground:()=>foreground('manual-foreground'),
  state:()=>({worldbuilder:!!studio(),ios:isIOS(),hidden:document.hidden,hiddenAt,reloading})
 };
 window.RistWorldBuilderLifecycleAuthority=api;
 window.RistWorldBuilderImmersivePolish=api;

 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
