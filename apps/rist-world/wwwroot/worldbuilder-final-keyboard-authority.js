(()=>{
 'use strict';

 const VERSION='20260916-final-keyboard-1';
 if(window.RistWorldBuilderFinalKeyboardAuthority?.version===VERSION)return;

 const ASSET_BASE='https://d2d6rnm6fnsp89.cloudfront.net/runtime/worldbuilder/keyboards/v1';
 const BLANK=`${ASSET_BASE}/common/blank.png`;
 const ACTIVE=`${ASSET_BASE}/common/active.png`;
 const STYLE_ID='rist-worldbuilder-final-keyboard-authority-style';
 const MODE_KEY='rist.worldbuilder.deviceKeyboard.mode.v1';
 const ADMIN_KEY='rist.worldbuilder.deviceKeyboard.mode.adminOverlay.v1';

 const MAP={
  pixels:{'1²':'1x1','1x1':'1x1','Grid':'grid','Zoom −':'zoom_minus','Zoom -':'zoom_minus','Zoom +':'zoom_plus','Undo':'undo','Center':'select'},
  tiles:{'Library':'library','Tile Size':'tile_size','Rotate':'rotate','Layer +':'layer_plus','Layer −':'layer_minus','Layer -':'layer_minus','Tier +':'tier_plus','Tier −':'tier_minus','Tier -':'tier_minus','Remove':'delete','Delete':'delete','Move':'move','Copy':'copy','Place':'place','Flip':'flip','Grid':'tile_size','Target':'move','Undo':'rotate'},
  sprites:{'Sprite Library':'sprite_library','Stop':'stop','FPS':'fps','Perspective':'parallax','Parallax':'parallax','Direction':'direction','Loop':'loop','Offset':'offset','Animate':'animate','Speed +':'speed_plus','Speed −':'speed_minus','Speed -':'speed_minus'},
  labels:{'Size +':'size_plus','Size −':'size_minus','Size -':'size_minus','Outline':'outline','Commit':'place','Place':'place','Style':'style','Font':'font','Color':'color','Shadow':'shadow','Align':'align','Curve':'curve','Rotate':'rotate','Bold':'style','Italic':'style','Remove':'outline'},
  viewer:{'Grid':'grid_n','Grid N':'grid_n','Zoom +':'zoom_plus','Zoom −':'zoom_minus','Zoom -':'zoom_minus','Auto':'auto','Center':'center','Layer +':'layer_plus','Layer −':'layer_minus','Layer -':'layer_minus','Tier +':'tier_plus','Tier −':'tier_minus','Tier -':'tier_minus','Widgets':'widgets','Data':'widgets','Focus':'focus','Projection':'projection','World View':'focus','Build Mode':'projection','Lock':'focus','Perspective':'projection'},
  litch:{'Light Peg':'light_peg','Mag Sketch':'sketch','Sketch':'sketch','Intensity −':'bright','Intensity -':'bright','Intensity +':'bright','Bright':'bright','Radius −':'radius','Radius -':'radius','Radius +':'radius','Radius':'radius','Erase':'erase','Shadow':'shadow','Line':'line','Close':'close','Convert':'convert','Glow':'glow','Temp':'temp','Flicker':'flicker'},
  cad:{'Line':'line','Rect':'rect','Rectangle':'rect','Circle':'circle','Arc':'arc','Measure':'measure','Snap':'snap','Rotate':'rotate','Mirror':'mirror','Offset':'offset','Align':'align','Duplicate':'duplicate','Poly':'poly','Elevation':'offset','Slope':'measure'},
  stylus:{'Visual':'visual','Terrain':'terrain','Select':'select','Erase':'erase','Effect':'effect','Annotation':'annotate','Annotate':'annotate','Width −':'width','Width -':'width','Width +':'width','Width':'width','Pressure':'pressure','Tilt':'tilt','Smooth':'smooth','Undo':'undo','Redo':'redo'},
  tethers:{'Sound':'sound','Light':'light','Vibration':'vibration','Temperature':'temp','Temp':'temp','Atmosphere':'air','Air':'air','Movement':'movement','Rules':'rules','Strength −':'strength','Strength -':'strength','Strength +':'strength','Strength':'strength','Range −':'range','Range -':'range','Range +':'range','Range':'range','Direction':'direction','Obstruct':'obstruct','Preview':'preview'},
  metadata:{'Keywords':'keywords','Secrets':'secret','Secret':'secret','Trap':'trap','Slope':'slope','Movement':'move_cost','Rules':'ruleset','Ruleset':'ruleset','Notes':'notes','Search':'search','Tags':'tags','Provenance':'provenance','Permissions':'permissions','Save':'save'},
  target:{'Select':'select','Move':'move','Rotate':'rotate','Resize':'scale','Scale':'scale','Copy':'copy','Remove':'delete','Delete':'delete','Focus':'focus','Link':'link','Lock':'lock','Group':'group','Layer +':'layer','Layer −':'layer','Layer -':'layer','Layer':'layer','Tier +':'tier','Tier −':'tier','Tier -':'tier','Tier':'tier','Tile Size':'scale','Metadata':'link','Tethers':'link','Undo':'rotate'},
  admin:{'Anchor':'anchor','Rectangle':'rectangle','Add / Remove':'add_remove','Add/Remove':'add_remove','All Visible':'all_visible','Clear':'clear','Apply Color':'fill','Fill':'fill','Opacity':'opacity','Set Border':'border','Border':'border','Border Type':'border_type','View/Edit':'view_edit','Public/Deny':'public_deny','Assign Permission':'assign','Assign':'assign'},
  widgets:{'Time':'clock','Clock':'clock','Date':'date','Weather':'weather','Viewer':'coords','Coords':'coords','Move':'move','Reset':'reset','Anchor':'anchor','Forecast':'forecast','Time Zone':'time_zone','Select':'select','Overlay':'overlay','Show/Hide':'show_hide','Sky':'forecast','Calendar':'date','UGC':'overlay'},
  access:{'Large Keys':'large_keys','Contrast':'contrast','Reduce Motion':'motion','Motion':'motion','Description':'screen_read','Screen Read':'screen_read','Captions':'captions','Haptics':'haptics','Voice Nav':'voice_nav','Key Nav':'key_nav','Semantics':'semantics','Announce':'announce','Focus Ring':'focus_ring','Alternate':'alternate','Data':'alternate','Viewer':'alternate'},
  file:{'Save':'save','Load':'load','Publish':'publish','Export':'export','Import':'import','Backup':'backup','Restore':'restore','Library':'library','Version':'version','Share':'share','Revert':'revert','Menu':'menu'}
 };

 let frame=0;
 let observer=null;
 let touch=null;
 let lastHeal=0;
 let lastResume=0;

 const studio=()=>document.querySelector('.worldbuilder-studio');
 const keyboard=()=>studio()?.querySelector('.wb-device-keyboard')||null;
 const keys=()=>keyboard()?.querySelector('.wb-device-keys')||null;

 function ensureStyle(){
  if(document.getElementById(STYLE_ID))return;
  const style=document.createElement('style');
  style.id=STYLE_ID;
  style.textContent=`
   .worldbuilder-studio .wb-device-keyboard.wb-final-keyboard-authority{
    pointer-events:auto!important;
   }
   .worldbuilder-studio .wb-device-keyboard.wb-final-keyboard-authority .wb-device-mode,
   .worldbuilder-studio .wb-device-keyboard.wb-final-keyboard-authority .wb-device-key,
   .worldbuilder-studio .wb-device-keyboard.wb-final-keyboard-authority .wb-dpad-key,
   .worldbuilder-studio .wb-device-keyboard.wb-final-keyboard-authority .wb-device-menu,
   .worldbuilder-studio .wb-device-keyboard.wb-final-keyboard-authority .wb-device-collapse,
   .worldbuilder-studio .wb-device-keyboard.wb-final-keyboard-authority .wb-device-grabber{
    pointer-events:auto!important;
    touch-action:manipulation!important;
    -webkit-tap-highlight-color:transparent!important;
   }
   .worldbuilder-studio .wb-device-keyboard.wb-final-keyboard-authority .wb-device-mode{
    border:0!important;
    border-radius:0!important;
    background-color:transparent!important;
    background-repeat:no-repeat!important;
    background-position:center!important;
    background-size:100% 100%!important;
    color:#fff0cb!important;
    box-shadow:none!important;
    text-shadow:0 1px 3px #000!important;
   }
   .worldbuilder-studio .wb-device-keyboard.wb-final-keyboard-authority .wb-device-keys{
    display:grid!important;
    visibility:visible!important;
    opacity:1!important;
    pointer-events:auto!important;
   }
   .worldbuilder-studio .wb-device-keyboard.wb-final-keyboard-authority .wb-device-key{
    position:relative!important;
    overflow:hidden!important;
    background:transparent!important;
    border:0!important;
    box-shadow:none!important;
   }
   .wb-final-key-art,.wb-final-dpad-art{
    position:absolute!important;
    inset:0!important;
    width:100%!important;
    height:100%!important;
    object-fit:fill!important;
    pointer-events:none!important;
    user-select:none!important;
    -webkit-user-select:none!important;
    -webkit-user-drag:none!important;
    z-index:1!important;
   }
   .worldbuilder-studio .wb-device-keyboard.wb-final-keyboard-authority .wb-device-key.wb-final-art-loaded>strong{
    position:absolute!important;
    width:1px!important;
    height:1px!important;
    padding:0!important;
    margin:-1px!important;
    overflow:hidden!important;
    clip:rect(0,0,0,0)!important;
    white-space:nowrap!important;
    border:0!important;
   }
   .worldbuilder-studio .wb-device-keyboard.wb-final-keyboard-authority .wb-device-key.wb-final-art-loaded>small{
    position:absolute!important;
    right:4%!important;
    bottom:5%!important;
    z-index:3!important;
    max-width:88%!important;
    padding:1.5% 3%!important;
    border-radius:99px!important;
    background:rgba(2,7,12,.70)!important;
    color:#f4e5c5!important;
    text-shadow:0 1px 2px #000!important;
   }
   .worldbuilder-studio .wb-device-keyboard.wb-final-keyboard-authority button.wb-final-touch-active{
    filter:brightness(1.25) drop-shadow(0 0 7px rgba(56,155,255,.75))!important;
    transform:scale(.97)!important;
   }
   .worldbuilder-studio.wb-final-resume-repaint .studio-viewer-canvas,
   .worldbuilder-studio.wb-final-resume-repaint .map,
   .worldbuilder-studio.wb-final-resume-repaint .world-stage{
    transform:translateZ(0)!important;
    backface-visibility:hidden!important;
   }
  `;
  document.head.appendChild(style);
 }

 function activeMode(){
  const selected=keyboard()?.querySelector('.wb-device-mode[aria-selected="true"]');
  if(selected?.dataset?.mode)return selected.dataset.mode;
  try{
   if(localStorage.getItem(ADMIN_KEY)==='true')return'admin';
   return localStorage.getItem(MODE_KEY)||'tiles';
  }catch{return'tiles'}
 }

 function labelOf(button){
  const strong=button.querySelector('strong')?.textContent?.trim();
  if(strong)return strong;
  const aria=(button.getAttribute('aria-label')||'').split('.')[0].trim();
  return aria||button.textContent?.trim()||'';
 }

 function artId(mode,button){
  const label=labelOf(button);
  if(mode==='sprites'&&label==='Play / Pause'){
   const sub=(button.querySelector('small')?.textContent||'').toLowerCase();
   return sub==='playing'?'pause':'play';
  }
  if(mode==='tiles'&&/^\d+(?:\.\d+)?²$/.test(label))return'tile_size';
  if(mode==='sprites'&&/^\d+(?:\.\d+)?²$/.test(label))return null;
  return MAP[mode]?.[label]||null;
 }

 function applyModeArt(host){
  host.querySelectorAll('.wb-device-mode').forEach(button=>{
   const on=button.getAttribute('aria-selected')==='true';
   button.style.setProperty('background-image',`url("${on?ACTIVE:BLANK}")`,'important');
  });
 }

 function decorateKey(button,mode){
  if(!(button instanceof HTMLButtonElement)||button.closest('.wb-persistent-dpad'))return;
  const id=artId(mode,button);
  const token=`${mode}:${id||'blank'}`;
  if(button.dataset.finalArtToken===token&&button.querySelector('.wb-final-key-art'))return;
  button.querySelector('.wb-final-key-art')?.remove();
  button.classList.remove('wb-final-art-loaded');
  const img=document.createElement('img');
  img.className='wb-final-key-art';
  img.alt='';img.setAttribute('aria-hidden','true');img.draggable=false;img.decoding='async';
  img.src=id?`${ASSET_BASE}/keyboards/${mode}/tiles/${id}.png`:BLANK;
  img.addEventListener('load',()=>button.classList.add('wb-final-art-loaded'),{once:true});
  img.addEventListener('error',()=>{
   button.classList.remove('wb-final-art-loaded');
   if(img.src!==BLANK)img.src=BLANK;
  },{once:true});
  button.prepend(img);
  button.dataset.finalArtToken=token;
  button.dataset.finalAsset=id||'blank';
  button.dataset.accessTranslation='available';
 }

 function dpadDirection(button){
  if(button.classList.contains('wb-dpad-up'))return'up';
  if(button.classList.contains('wb-dpad-left'))return'left';
  if(button.classList.contains('wb-dpad-right'))return'right';
  if(button.classList.contains('wb-dpad-down'))return'down';
  if(button.classList.contains('wb-dpad-select'))return'center';
  return null;
 }

 function decorateDpad(host,mode){
  const safe=MAP[mode]?mode:'tiles';
  host.querySelectorAll('.wb-persistent-dpad .wb-dpad-key').forEach(button=>{
   const direction=dpadDirection(button);if(!direction)return;
   const token=`${safe}:${direction}`;
   if(button.dataset.finalDpadToken===token&&button.querySelector('.wb-final-dpad-art'))return;
   button.querySelector('.wb-final-dpad-art')?.remove();
   const img=document.createElement('img');
   img.className='wb-final-dpad-art';img.alt='';img.setAttribute('aria-hidden','true');img.draggable=false;img.decoding='async';
   img.src=`${ASSET_BASE}/keyboards/${safe}/dpad/${direction}.png`;
   img.addEventListener('error',()=>{img.src=`${ASSET_BASE}/common/dpad_${direction}.png`},{once:true});
   button.prepend(img);button.dataset.finalDpadToken=token;
  });
 }

 function healEmptyKeys(mode){
  const node=keys();if(!node)return;
  if(node.querySelector('.wb-device-key,.wb-device-inline-editor,.wb-admin-keyboard'))return;
  const now=Date.now();if(now-lastHeal<200)return;lastHeal=now;
  try{window.RistWorldBuilderDeviceShell?.setMode?.(mode)}catch{}
  setTimeout(schedule,0);
 }

 function apply(){
  ensureStyle();
  const host=keyboard();if(!host)return;
  host.classList.add('wb-shaelvien-skinned','wb-final-keyboard-authority');
  host.dataset.finalKeyboardAuthority=VERSION;
  const mode=activeMode();
  host.dataset.shaelvienKeyboardMode=mode;
  applyModeArt(host);
  healEmptyKeys(mode);
  host.querySelectorAll('.wb-device-keys .wb-device-key').forEach(button=>decorateKey(button,mode));
  decorateDpad(host,mode);
 }

 function schedule(){
  if(frame)return;
  frame=requestAnimationFrame(()=>{frame=0;apply()});
 }

 function buttonFrom(target){return target?.closest?.('.wb-device-keyboard button')||null}
 function touchPoint(event){return event.touches?.[0]||event.changedTouches?.[0]||null}
 function installTouch(){
  document.addEventListener('touchstart',event=>{
   const button=buttonFrom(event.target);const point=touchPoint(event);
   if(!button||button.disabled||!point)return;
   touch={button,x:point.clientX,y:point.clientY,moved:false};
   button.classList.add('wb-final-touch-active');
  },{capture:true,passive:true});
  document.addEventListener('touchmove',event=>{
   if(!touch)return;const point=touchPoint(event);if(!point)return;
   if(Math.hypot(point.clientX-touch.x,point.clientY-touch.y)>12){touch.moved=true;touch.button?.classList.remove('wb-final-touch-active')}
  },{capture:true,passive:true});
  document.addEventListener('touchend',event=>{
   if(!touch)return;
   const state=touch;touch=null;state.button?.classList.remove('wb-final-touch-active');
   if(state.moved||state.button?.disabled||!state.button?.isConnected)return;
   const point=touchPoint(event);const at=point?document.elementFromPoint(point.clientX,point.clientY):null;
   if(at&&!state.button.contains(at))return;
   event.preventDefault();event.stopPropagation();
   state.button.classList.add('wb-final-touch-active');
   state.button.click();
   setTimeout(()=>state.button?.classList.remove('wb-final-touch-active'),110);
  },{capture:true,passive:false});
  document.addEventListener('touchcancel',()=>{touch?.button?.classList.remove('wb-final-touch-active');touch=null},{capture:true,passive:true});
 }

 function repaint(source='resume'){
  const root=studio();if(!root||document.hidden)return;
  const now=Date.now();if(now-lastResume<75)return;lastResume=now;
  root.hidden=false;
  root.style.setProperty('visibility','visible','important');
  root.style.setProperty('opacity','1','important');
  root.classList.remove('wb-gesture-panning','wb-gesture-pinching');
  root.classList.add('wb-final-resume-repaint');
  root.querySelectorAll('.studio-viewer,.studio-viewer-canvas,.map-shell,.map,.world-stage').forEach(node=>{
   node.style.setProperty('visibility','visible','important');
   node.style.setProperty('opacity','1','important');
  });
  void root.offsetHeight;
  try{window.RistWorldBuilderDeviceShell?.setMode?.(activeMode())}catch{}
  try{window.RistWorldBuilderGridCursor?.refresh?.()}catch{}
  try{window.RistWorldBuilderShaelvienKeyboardSkin?.refresh?.()}catch{}
  try{window.RistWorldTickerData?.refresh?.()}catch{}
  try{window.dispatchEvent(new Event('resize'))}catch{}
  try{window.dispatchEvent(new CustomEvent('rist:viewer-state',{detail:{source}}))}catch{}
  requestAnimationFrame(()=>{root.classList.remove('wb-final-resume-repaint');schedule()});
 }

 function resume(source){
  requestAnimationFrame(()=>requestAnimationFrame(()=>repaint(source)));
  setTimeout(()=>repaint(source),180);
  setTimeout(()=>repaint(source),650);
 }

 function start(){
  ensureStyle();apply();installTouch();
  observer=new MutationObserver(schedule);
  observer.observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['class','aria-selected','disabled']});
  document.addEventListener('click',event=>{if(event.target?.closest?.('.wb-device-keyboard'))setTimeout(schedule,0)},true);
  window.addEventListener('pageshow',()=>resume('pageshow'));
  window.addEventListener('focus',()=>resume('focus'),{passive:true});
  document.addEventListener('visibilitychange',()=>{if(!document.hidden)resume('visibilitychange')});
  window.addEventListener('orientationchange',()=>resume('orientationchange'),{passive:true});
  window.addEventListener('resize',schedule,{passive:true});
 }

 window.RistWorldBuilderFinalKeyboardAuthority={
  version:VERSION,
  refresh:schedule,
  resume:()=>resume('manual'),
  state:()=>({mounted:!!keyboard(),mode:activeMode(),keys:keys()?.querySelectorAll('.wb-device-key').length||0,art:keys()?.querySelectorAll('.wb-final-key-art').length||0})
 };

 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
