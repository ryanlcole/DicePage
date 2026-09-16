(()=>{
 'use strict';

 const VERSION='20260916-keyboard-authority-v2-1';
 if(window.RistWorldBuilderKeyboardAuthority?.version===VERSION)return;

 const ASSET_BASE='https://d2d6rnm6fnsp89.cloudfront.net/runtime/worldbuilder/keyboards/v1';
 const BLANK=`${ASSET_BASE}/common/blank.png`;
 const ACTIVE=`${ASSET_BASE}/common/active.png`;
 const STYLE_ID='rist-worldbuilder-keyboard-authority-v2-style';
 const MODE_KEY='rist.worldbuilder.deviceKeyboard.mode.v1';
 const ADMIN_KEY='rist.worldbuilder.deviceKeyboard.mode.adminOverlay.v1';

 /* Only map artwork that actually represents the command. Unknown keys keep their
    semantic text over the generic blank key instead of borrowing a misleading icon. */
 const MAP={
  pixels:{'1²':'1x1','1x1':'1x1','Grid':'grid','Zoom −':'zoom_minus','Zoom -':'zoom_minus','Zoom +':'zoom_plus','Undo':'undo'},
  tiles:{'Library':'library','Tile Size':'tile_size','Rotate':'rotate','Layer +':'layer_plus','Layer −':'layer_minus','Layer -':'layer_minus','Tier +':'tier_plus','Tier −':'tier_minus','Tier -':'tier_minus','Remove':'delete','Delete':'delete','Move':'move','Copy':'copy','Place':'place','Flip':'flip'},
  sprites:{'Sprite Library':'sprite_library','Stop':'stop','FPS':'fps','Perspective':'parallax','Parallax':'parallax','Direction':'direction','Loop':'loop','Offset':'offset','Animate':'animate','Speed +':'speed_plus','Speed −':'speed_minus','Speed -':'speed_minus'},
  labels:{'Size +':'size_plus','Size −':'size_minus','Size -':'size_minus','Outline':'outline','Commit':'place','Place':'place','Style':'style','Font':'font','Color':'color','Shadow':'shadow','Align':'align','Curve':'curve','Rotate':'rotate'},
  viewer:{'Grid':'grid_n','Grid N':'grid_n','Zoom +':'zoom_plus','Zoom −':'zoom_minus','Zoom -':'zoom_minus','Auto':'auto','Center':'center','Layer +':'layer_plus','Layer −':'layer_minus','Layer -':'layer_minus','Tier +':'tier_plus','Tier −':'tier_minus','Tier -':'tier_minus','Widgets':'widgets','Focus':'focus','Projection':'projection'},
  litch:{'Light Peg':'light_peg','Mag Sketch':'sketch','Sketch':'sketch','Intensity −':'bright','Intensity -':'bright','Intensity +':'bright','Bright':'bright','Radius −':'radius','Radius -':'radius','Radius +':'radius','Radius':'radius','Erase':'erase','Shadow':'shadow','Line':'line','Close':'close','Convert':'convert','Glow':'glow','Temp':'temp','Flicker':'flicker'},
  cad:{'Line':'line','Rect':'rect','Rectangle':'rect','Circle':'circle','Arc':'arc','Measure':'measure','Snap':'snap','Rotate':'rotate','Mirror':'mirror','Offset':'offset','Align':'align','Duplicate':'duplicate','Poly':'poly'},
  stylus:{'Visual':'visual','Terrain':'terrain','Select':'select','Erase':'erase','Effect':'effect','Annotation':'annotate','Annotate':'annotate','Width −':'width','Width -':'width','Width +':'width','Width':'width','Pressure':'pressure','Tilt':'tilt','Smooth':'smooth','Undo':'undo','Redo':'redo'},
  tethers:{'Sound':'sound','Light':'light','Vibration':'vibration','Temperature':'temp','Temp':'temp','Atmosphere':'air','Air':'air','Movement':'movement','Rules':'rules','Strength −':'strength','Strength -':'strength','Strength +':'strength','Strength':'strength','Range −':'range','Range -':'range','Range +':'range','Range':'range','Direction':'direction','Obstruct':'obstruct','Preview':'preview'},
  metadata:{'Keywords':'keywords','Secrets':'secret','Secret':'secret','Trap':'trap','Slope':'slope','Movement':'move_cost','Rules':'ruleset','Ruleset':'ruleset','Notes':'notes','Search':'search','Tags':'tags','Provenance':'provenance','Permissions':'permissions','Save':'save'},
  target:{'Select':'select','Move':'move','Rotate':'rotate','Resize':'scale','Scale':'scale','Copy':'copy','Remove':'delete','Delete':'delete','Focus':'focus','Link':'link','Lock':'lock','Group':'group','Layer +':'layer','Layer −':'layer','Layer -':'layer','Layer':'layer','Tier +':'tier','Tier −':'tier','Tier -':'tier','Tier':'tier'},
  admin:{'Anchor':'anchor','Rectangle':'rectangle','Add / Remove':'add_remove','Add/Remove':'add_remove','All Visible':'all_visible','Clear':'clear','Apply Color':'fill','Fill':'fill','Opacity':'opacity','Set Border':'border','Border':'border','Border Type':'border_type','View/Edit':'view_edit','Public/Deny':'public_deny','Assign Permission':'assign','Assign':'assign'},
  widgets:{'Time':'clock','Clock':'clock','Date':'date','Weather':'weather','Viewer':'coords','Coords':'coords','Move':'move','Reset':'reset','Anchor':'anchor','Forecast':'forecast','Time Zone':'time_zone','Select':'select','Overlay':'overlay','Show/Hide':'show_hide'},
  access:{'Large Keys':'large_keys','Contrast':'contrast','Reduce Motion':'motion','Motion':'motion','Description':'screen_read','Screen Read':'screen_read','Captions':'captions','Haptics':'haptics','Voice Nav':'voice_nav','Key Nav':'key_nav','Semantics':'semantics','Announce':'announce','Focus Ring':'focus_ring','Alternate':'alternate'},
  file:{'Save':'save','Load':'load','Publish':'publish','Export':'export','Import':'import','Backup':'backup','Restore':'restore','Library':'library','Version':'version','Share':'share','Revert':'revert','Menu':'menu'}
 };

 let frame=0;
 let observer=null;
 let mounted=null;

 const studio=()=>document.querySelector('.worldbuilder-studio');
 const keyboard=()=>studio()?.querySelector('.wb-device-keyboard')||null;
 const keys=()=>keyboard()?.querySelector('.wb-device-keys')||null;

 function ensureStyle(){
  if(document.getElementById(STYLE_ID))return;
  const style=document.createElement('style');
  style.id=STYLE_ID;
  style.textContent=`
   .worldbuilder-studio .wb-device-keyboard.wb-keyboard-authority-v2 .wb-device-mode{
    background-repeat:no-repeat!important;
    background-position:center!important;
    background-size:contain!important;
   }
   .worldbuilder-studio .wb-device-keyboard.wb-keyboard-authority-v2 .wb-device-key{
    position:relative!important;
    overflow:hidden!important;
   }
   .worldbuilder-studio .wb-device-keyboard .wb-keyboard-v2-art,
   .worldbuilder-studio .wb-device-keyboard .wb-keyboard-v2-dpad-art{
    position:absolute!important;
    left:50%!important;
    top:50%!important;
    width:96%!important;
    height:96%!important;
    transform:translate(-50%,-50%)!important;
    object-fit:contain!important;
    pointer-events:none!important;
    user-select:none!important;
    -webkit-user-select:none!important;
    -webkit-user-drag:none!important;
    z-index:1!important;
   }
   .worldbuilder-studio .wb-device-keyboard .wb-device-key.wb-keyboard-v2-exact>strong,
   .worldbuilder-studio .wb-device-keyboard .wb-device-key.wb-keyboard-v2-exact>small{
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
   .worldbuilder-studio .wb-device-keyboard .wb-device-key.wb-keyboard-v2-fallback>strong,
   .worldbuilder-studio .wb-device-keyboard .wb-device-key.wb-keyboard-v2-fallback>small{
    position:relative!important;
    z-index:3!important;
    text-shadow:0 1px 3px #000!important;
   }
   .worldbuilder-studio .wb-device-keyboard .wb-dpad-key{
    position:relative!important;
    overflow:hidden!important;
    color:transparent!important;
    font-size:0!important;
    text-shadow:none!important;
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

 function assetId(mode,button){
  const label=labelOf(button);
  if(mode==='sprites'&&label==='Play / Pause'){
   const sub=(button.querySelector('small')?.textContent||'').toLowerCase();
   return sub==='playing'?'pause':'play';
  }
  if(mode==='tiles'&&/^\d+(?:\.\d+)?²$/.test(label))return'tile_size';
  if(mode==='sprites'&&/^\d+(?:\.\d+)?²$/.test(label))return null;
  return MAP[mode]?.[label]||null;
 }

 function removeLegacyArt(button){
  button.querySelectorAll(':scope > .wb-shaelvien-key-art,:scope > .wb-final-key-art').forEach(node=>node.remove());
  button.classList.remove('wb-final-art-loaded','wb-shaelvien-key-exact','wb-shaelvien-key-fallback');
 }

 function decorateKey(button,mode){
  if(!(button instanceof HTMLButtonElement)||button.closest('.wb-persistent-dpad'))return;
  removeLegacyArt(button);
  const id=assetId(mode,button);
  const token=`${mode}:${id||'blank'}`;
  const existing=button.querySelector(':scope > .wb-keyboard-v2-art');
  if(button.dataset.keyboardV2ArtToken===token&&existing){
   button.classList.toggle('wb-keyboard-v2-exact',!!id);
   button.classList.toggle('wb-keyboard-v2-fallback',!id);
   button.classList.toggle('wb-shaelvien-key-exact',!!id);
   return;
  }
  existing?.remove();
  const img=document.createElement('img');
  img.className='wb-keyboard-v2-art';
  img.alt='';img.setAttribute('aria-hidden','true');img.draggable=false;img.decoding='async';
  img.src=id?`${ASSET_BASE}/keyboards/${mode}/tiles/${id}.png`:BLANK;
  if(id)img.addEventListener('error',()=>{
   img.src=BLANK;
   button.classList.remove('wb-keyboard-v2-exact','wb-shaelvien-key-exact');
   button.classList.add('wb-keyboard-v2-fallback');
  },{once:true});
  button.prepend(img);
  button.dataset.keyboardV2ArtToken=token;
  button.dataset.accessTranslation='available';
  button.classList.toggle('wb-keyboard-v2-exact',!!id);
  button.classList.toggle('wb-keyboard-v2-fallback',!id);
  button.classList.toggle('wb-shaelvien-key-exact',!!id);
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
   button.querySelectorAll(':scope > .wb-shaelvien-dpad-art,:scope > .wb-final-dpad-art').forEach(node=>node.remove());
   const direction=dpadDirection(button);if(!direction)return;
   const token=`${safe}:${direction}`;
   const existing=button.querySelector(':scope > .wb-keyboard-v2-dpad-art');
   if(button.dataset.keyboardV2DpadToken===token&&existing)return;
   existing?.remove();
   const img=document.createElement('img');
   img.className='wb-keyboard-v2-dpad-art';
   img.alt='';img.setAttribute('aria-hidden','true');img.draggable=false;img.decoding='async';
   img.src=`${ASSET_BASE}/keyboards/${safe}/dpad/${direction}.png`;
   img.addEventListener('error',()=>{img.src=`${ASSET_BASE}/common/dpad_${direction}.png`},{once:true});
   button.prepend(img);
   button.dataset.keyboardV2DpadToken=token;
   button.dataset.accessTranslation='available';
  });
 }

 function applyModeArt(host){
  host.querySelectorAll('.wb-device-mode').forEach(button=>{
   const selected=button.getAttribute('aria-selected')==='true';
   button.style.setProperty('background-image',`url("${selected?ACTIVE:BLANK}")`,'important');
   button.style.setProperty('background-size','contain','important');
  });
 }

 function installPointerFeedback(host){
  if(host.dataset.keyboardV2Pointer==='1')return;
  host.dataset.keyboardV2Pointer='1';
  let pressed=null;
  const clear=()=>{pressed?.classList.remove('wb-touch-active');pressed=null};
  host.addEventListener('pointerdown',event=>{
   const button=event.target?.closest?.('button');
   if(!button||button.disabled||!host.contains(button))return;
   clear();pressed=button;button.classList.add('wb-touch-active');
  },{passive:true});
  host.addEventListener('pointerup',clear,{passive:true});
  host.addEventListener('pointercancel',clear,{passive:true});
  host.addEventListener('pointerleave',event=>{if(event.pointerType!=='mouse')clear()},{passive:true});
 }

 function apply(){
  ensureStyle();
  const host=keyboard();if(!host)return;
  mounted=host;
  host.classList.add('wb-shaelvien-skinned','wb-keyboard-authority-v2');
  host.dataset.keyboardAuthority=VERSION;
  const mode=activeMode();
  host.dataset.shaelvienKeyboardMode=mode;
  applyModeArt(host);
  host.querySelectorAll('.wb-device-keys .wb-device-key').forEach(button=>decorateKey(button,mode));
  decorateDpad(host,mode);
  installPointerFeedback(host);
 }

 function schedule(){if(frame)return;frame=requestAnimationFrame(()=>{frame=0;apply()})}

 function start(){
  ensureStyle();apply();
  observer=new MutationObserver(records=>{
   if(records.some(record=>record.type==='childList'||record.attributeName==='aria-selected'||record.attributeName==='disabled'))schedule();
  });
  observer.observe(document.getElementById('app')||document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['aria-selected','disabled']});
  document.addEventListener('click',event=>{if(event.target?.closest?.('.wb-device-keyboard'))setTimeout(schedule,0)},true);
  window.addEventListener('rist-sprite-playback',schedule);
  window.addEventListener('rist:viewer-state',schedule);
  window.addEventListener('resize',schedule,{passive:true});
  window.addEventListener('orientationchange',schedule,{passive:true});
  window.addEventListener('pageshow',schedule,{passive:true});
 }

 const api={
  version:VERSION,
  refresh:schedule,
  resume:schedule,
  assetBase:ASSET_BASE,
  currentMode:activeMode,
  state:()=>({mounted:!!mounted?.isConnected,mode:activeMode(),keys:keys()?.querySelectorAll('.wb-device-key').length||0,art:keys()?.querySelectorAll('.wb-keyboard-v2-art').length||0,legacyArt:document.querySelectorAll('.wb-shaelvien-key-art,.wb-final-key-art').length})
 };
 window.RistWorldBuilderKeyboardAuthority=api;
 /* Compatibility aliases stop older bridges from injecting retired authorities. */
 window.RistWorldBuilderKeyboardRuntime=api;
 window.RistWorldBuilderFinalKeyboardAuthority=api;
 window.RistWorldBuilderShaelvienKeyboardSkin=api;
 window.RistWorldBuilderKeyboardVisualAccessibility=api;

 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
