(()=>{
 'use strict';

 const VERSION='20260916-immersive-polish-1';
 const STYLE_ID='rist-worldbuilder-immersive-polish-style';
 const RELOAD_KEY='rist.worldbuilder.iosResumeReloadAt.v1';
 let frame=0;
 let hiddenAt=0;
 let observer=null;

 const studio=()=>document.querySelector('.worldbuilder-studio');
 const app=()=>document.getElementById('app');
 const isIOS=()=>/iPad|iPhone|iPod/i.test(navigator.userAgent)||(/Macintosh/i.test(navigator.userAgent)&&navigator.maxTouchPoints>1);

 function ensureStyle(){
  if(document.getElementById(STYLE_ID))return;
  const style=document.createElement('style');
  style.id=STYLE_ID;
  style.textContent=`
   /* Buttons keep percentage hit boxes; artwork keeps its authored proportions. */
   .worldbuilder-studio .wb-final-key-art,
   .worldbuilder-studio .wb-final-dpad-art{
    inset:50% auto auto 50%!important;
    width:96%!important;
    height:96%!important;
    transform:translate(-50%,-50%)!important;
    object-fit:contain!important;
   }
   .worldbuilder-studio .wb-device-mode{
    background-size:contain!important;
    background-position:center!important;
    background-repeat:no-repeat!important;
   }

   /* Immersive Worldbuilder does not need the site copyright/contact ticker. */
   body.wb-immersive-worldbuilder .site-copyright-notice{
    display:none!important;
    height:0!important;
    min-height:0!important;
    max-height:0!important;
    padding:0!important;
    margin:0!important;
    border:0!important;
    overflow:hidden!important;
   }

   /* Temporary compositor nudge used only while an iOS page resumes. */
   html.wb-ios-resume-repaint,
   html.wb-ios-resume-repaint body,
   html.wb-ios-resume-repaint #app{
    visibility:visible!important;
    opacity:1!important;
   }
  `;
  document.head.appendChild(style);
 }

 function applyPageContext(){
  ensureStyle();
  const active=!!studio();
  document.body?.classList.toggle('wb-immersive-worldbuilder',active);
  const legal=document.querySelector('.site-copyright-notice');
  if(legal)legal.setAttribute('aria-hidden',active?'true':'false');
 }

 function visibleGeometry(){
  const root=studio();
  if(!root)return false;
  const rect=root.getBoundingClientRect();
  const style=getComputedStyle(root);
  return rect.width>4&&rect.height>4&&style.display!=='none'&&style.visibility!=='hidden'&&Number(style.opacity||1)>0;
 }

 function refreshAuthorities(source){
  try{window.RistWorldBuilderFinalKeyboardAuthority?.resume?.()}catch{}
  try{window.RistWorldBuilderGridCursor?.refresh?.()}catch{}
  try{window.RistWorldBuilderShaelvienKeyboardSkin?.refresh?.()}catch{}
  try{window.RistWorldTickerData?.refresh?.()}catch{}
  try{window.dispatchEvent(new Event('resize'))}catch{}
  try{window.dispatchEvent(new CustomEvent('rist:viewer-state',{detail:{source}}))}catch{}
 }

 function restoreInline(node,name,value,priority){
  if(!node)return;
  if(value)node.style.setProperty(name,value,priority||'');
  else node.style.removeProperty(name);
 }

 function forceRecompose(source='resume'){
  if(document.hidden)return;
  applyPageContext();
  const root=studio(),mount=app();
  if(!root||!mount)return;

  const display=mount.style.getPropertyValue('display');
  const displayPriority=mount.style.getPropertyPriority('display');
  const transform=mount.style.getPropertyValue('transform');
  const transformPriority=mount.style.getPropertyPriority('transform');

  document.documentElement.classList.add('wb-ios-resume-repaint');
  mount.style.setProperty('display','none','important');
  void document.documentElement.offsetHeight;

  requestAnimationFrame(()=>{
   restoreInline(mount,'display',display,displayPriority);
   mount.style.setProperty('transform','translateZ(0)','important');
   root.style.setProperty('visibility','visible','important');
   root.style.setProperty('opacity','1','important');
   root.querySelectorAll('.studio-viewer,.studio-viewer-canvas,.map-shell,.map,.world-stage,.wb-device-keyboard').forEach(node=>{
    node.style.setProperty('visibility','visible','important');
    node.style.setProperty('opacity','1','important');
   });
   void mount.offsetHeight;
   refreshAuthorities(source);

   requestAnimationFrame(()=>{
    restoreInline(mount,'transform',transform,transformPriority);
    document.documentElement.classList.remove('wb-ios-resume-repaint');
    schedule();
   });
  });

  setTimeout(()=>{
   if(!document.hidden&&!visibleGeometry())guardedReload('resume-surface-missing');
  },900);
 }

 function guardedReload(reason){
  if(!isIOS()||document.hidden||!studio())return;
  const now=Date.now();
  let last=0;
  try{last=Number(sessionStorage.getItem(RELOAD_KEY)||0)}catch{}
  if(now-last<8000)return;
  try{sessionStorage.setItem(RELOAD_KEY,String(now))}catch{}
  try{sessionStorage.setItem('rist.worldbuilder.resumeReason',reason)}catch{}
  location.reload();
 }

 function resume(source,event){
  if(!isIOS()){
   schedule();
   return;
  }
  if(event?.persisted){
   guardedReload('bfcache-pageshow');
   return;
  }
  requestAnimationFrame(()=>forceRecompose(source));
  setTimeout(()=>forceRecompose(`${source}-late`),220);
 }

 function schedule(){
  if(frame)return;
  frame=requestAnimationFrame(()=>{frame=0;applyPageContext()});
 }

 function start(){
  ensureStyle();
  applyPageContext();
  observer=new MutationObserver(schedule);
  observer.observe(document.getElementById('app')||document.body,{childList:true,subtree:true});
  window.addEventListener('pageshow',event=>resume('pageshow',event));
  window.addEventListener('pagehide',()=>{hiddenAt=Date.now()});
  window.addEventListener('focus',()=>{if(Date.now()-hiddenAt>250)resume('focus')},{passive:true});
  document.addEventListener('visibilitychange',()=>{
   if(document.hidden){hiddenAt=Date.now();return}
   if(Date.now()-hiddenAt>250)resume('visibilitychange');
   else schedule();
  });
  window.addEventListener('orientationchange',()=>setTimeout(()=>resume('orientationchange'),80),{passive:true});
 }

 window.RistWorldBuilderImmersivePolish={
  version:VERSION,
  refresh:schedule,
  resume:()=>resume('manual'),
  state:()=>({worldbuilder:!!studio(),geometryVisible:visibleGeometry(),ios:isIOS()})
 };

 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});
 else start();
})();
