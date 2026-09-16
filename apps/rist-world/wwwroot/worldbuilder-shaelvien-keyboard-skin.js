(()=>{
 'use strict';

 const STYLE_ID='rist-worldbuilder-shaelvien-keyboard-skin-css';
 const STYLE_URL='./css/worldbuilder-shaelvien-keyboard-skin.css?v=20260916-shaelvien-tiles-1';
 const ASSET_BASE='https://d2d6rnm6fnsp89.cloudfront.net/runtime/worldbuilder/keyboards/v1';
 const BLANK_ASSET=`${ASSET_BASE}/common/blank.png`;
 const DPAD_FALLBACK={
  up:`${ASSET_BASE}/common/dpad_up.png`,
  left:`${ASSET_BASE}/common/dpad_left.png`,
  center:`${ASSET_BASE}/common/dpad_center.png`,
  right:`${ASSET_BASE}/common/dpad_right.png`,
  down:`${ASSET_BASE}/common/dpad_down.png`
 };

 const MAP={
  pixels:{
   '1²':'1x1','1x1':'1x1','Grid':'grid','Zoom −':'zoom_minus','Zoom -':'zoom_minus','Zoom +':'zoom_plus','Undo':'undo'
  },
  tiles:{
   'Library':'library','Tile Size':'tile_size','Rotate':'rotate','Layer +':'layer_plus','Layer −':'layer_minus','Layer -':'layer_minus','Tier +':'tier_plus','Tier −':'tier_minus','Tier -':'tier_minus','Remove':'delete','Delete':'delete','Move':'move','Copy':'copy','Place':'place','Flip':'flip'
  },
  sprites:{
   'Sprite Library':'sprite_library','Stop':'stop','FPS':'fps','Perspective':'parallax','Parallax':'parallax','Direction':'direction','Loop':'loop','Offset':'offset','Animate':'animate','Speed +':'speed_plus','Speed −':'speed_minus','Speed -':'speed_minus'
  },
  labels:{
   'Size +':'size_plus','Size −':'size_minus','Size -':'size_minus','Outline':'outline','Commit':'place','Place':'place','Style':'style','Font':'font','Color':'color','Shadow':'shadow','Align':'align','Curve':'curve','Rotate':'rotate'
  },
  viewer:{
   'Grid':'grid_n','Grid N':'grid_n','Zoom +':'zoom_plus','Zoom −':'zoom_minus','Zoom -':'zoom_minus','Auto':'auto','Center':'center','Layer +':'layer_plus','Layer −':'layer_minus','Layer -':'layer_minus','Tier +':'tier_plus','Tier −':'tier_minus','Tier -':'tier_minus','Widgets':'widgets','Focus':'focus','Projection':'projection'
  },
  litch:{
   'Light Peg':'light_peg','Mag Sketch':'sketch','Sketch':'sketch','Intensity −':'bright','Intensity -':'bright','Intensity +':'bright','Bright':'bright','Radius −':'radius','Radius -':'radius','Radius +':'radius','Radius':'radius','Erase':'erase','Shadow':'shadow','Line':'line','Close':'close','Convert':'convert','Glow':'glow','Temp':'temp','Flicker':'flicker'
  },
  cad:{
   'Line':'line','Rect':'rect','Rectangle':'rect','Circle':'circle','Arc':'arc','Measure':'measure','Snap':'snap','Rotate':'rotate','Mirror':'mirror','Offset':'offset','Align':'align','Duplicate':'duplicate','Poly':'poly'
  },
  stylus:{
   'Visual':'visual','Terrain':'terrain','Select':'select','Erase':'erase','Effect':'effect','Annotation':'annotate','Annotate':'annotate','Width −':'width','Width -':'width','Width +':'width','Width':'width','Pressure':'pressure','Tilt':'tilt','Smooth':'smooth','Undo':'undo','Redo':'redo'
  },
  tethers:{
   'Sound':'sound','Light':'light','Vibration':'vibration','Temperature':'temp','Temp':'temp','Atmosphere':'air','Air':'air','Movement':'movement','Rules':'rules','Strength −':'strength','Strength -':'strength','Strength +':'strength','Strength':'strength','Range −':'range','Range -':'range','Range +':'range','Range':'range','Direction':'direction','Obstruct':'obstruct','Preview':'preview'
  },
  metadata:{
   'Keywords':'keywords','Secrets':'secret','Secret':'secret','Trap':'trap','Slope':'slope','Movement':'move_cost','Rules':'ruleset','Ruleset':'ruleset','Notes':'notes','Search':'search','Tags':'tags','Provenance':'provenance','Permissions':'permissions','Save':'save'
  },
  target:{
   'Select':'select','Move':'move','Rotate':'rotate','Resize':'scale','Scale':'scale','Copy':'copy','Remove':'delete','Delete':'delete','Focus':'focus','Link':'link','Lock':'lock','Group':'group','Layer +':'layer','Layer −':'layer','Layer -':'layer','Layer':'layer','Tier +':'tier','Tier −':'tier','Tier -':'tier','Tier':'tier'
  },
  admin:{
   'Anchor':'anchor','Rectangle':'rectangle','Add / Remove':'add_remove','Add/Remove':'add_remove','All Visible':'all_visible','Clear':'clear','Apply Color':'fill','Fill':'fill','Opacity':'opacity','Set Border':'border','Border':'border','Border Type':'border_type','View/Edit':'view_edit','Public/Deny':'public_deny','Assign Permission':'assign','Assign':'assign'
  },
  widgets:{
   'Time':'clock','Clock':'clock','Date':'date','Weather':'weather','Viewer':'coords','Coords':'coords','Move':'move','Reset':'reset','Anchor':'anchor','Forecast':'forecast','Time Zone':'time_zone','Select':'select','Overlay':'overlay','Show/Hide':'show_hide'
  },
  access:{
   'Large Keys':'large_keys','Contrast':'contrast','Reduce Motion':'motion','Motion':'motion','Description':'screen_read','Screen Read':'screen_read','Captions':'captions','Haptics':'haptics','Voice Nav':'voice_nav','Key Nav':'key_nav','Semantics':'semantics','Announce':'announce','Focus Ring':'focus_ring','Alternate':'alternate'
  },
  file:{
   'Save':'save','Load':'load','Publish':'publish','Export':'export','Import':'import','Backup':'backup','Restore':'restore','Library':'library','Version':'version','Share':'share','Revert':'revert','Menu':'menu'
  }
 };

 let observer=null;
 let frame=0;
 let keyboard=null;

 function ensureStyle(){
  if(document.getElementById(STYLE_ID))return;
  const link=document.createElement('link');
  link.id=STYLE_ID;
  link.rel='stylesheet';
  link.href=STYLE_URL;
  document.head.appendChild(link);
 }
 function activeMode(host){
  const selected=host?.querySelector('.wb-device-mode[aria-selected="true"]');
  if(selected?.dataset?.mode)return selected.dataset.mode;
  try{
   if(localStorage.getItem('rist.worldbuilder.deviceKeyboard.mode.adminOverlay.v1')==='true')return'admin';
   return localStorage.getItem('rist.worldbuilder.deviceKeyboard.mode.v1')||'tiles';
  }catch{return'tiles'}
 }
 function labelOf(button){return(button.querySelector('strong')?.textContent||button.getAttribute('aria-label')||'').trim()}
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
 function image(src,cls){
  const node=document.createElement('img');
  node.className=cls;
  node.src=src;
  node.alt='';
  node.decoding='async';
  node.loading='eager';
  node.setAttribute('aria-hidden','true');
  node.draggable=false;
  return node;
 }
 function skinKey(button,mode){
  if(!(button instanceof HTMLButtonElement)||button.closest('.wb-persistent-dpad'))return;
  const id=assetId(mode,button);
  const token=`${mode}:${id||'blank'}`;
  if(button.dataset.shaelvienSkinToken===token&&button.querySelector('.wb-shaelvien-key-art'))return;
  button.querySelector('.wb-shaelvien-key-art')?.remove();
  const src=id?`${ASSET_BASE}/keyboards/${mode}/tiles/${id}.png`:BLANK_ASSET;
  const art=image(src,'wb-shaelvien-key-art');
  if(id)art.addEventListener('error',()=>{if(art.src!==BLANK_ASSET)art.src=BLANK_ASSET},{once:true});
  button.prepend(art);
  button.classList.toggle('wb-shaelvien-key-exact',!!id);
  button.classList.toggle('wb-shaelvien-key-fallback',!id);
  button.dataset.shaelvienSkinToken=token;
  button.dataset.shaelvienAsset=id||'blank';
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
 function skinDpad(host,mode){
  const safeMode=MAP[mode]?mode:'tiles';
  host.querySelectorAll('.wb-persistent-dpad .wb-dpad-key').forEach(button=>{
   const direction=dpadDirection(button);if(!direction)return;
   const token=`${safeMode}:${direction}`;
   if(button.dataset.shaelvienDpadToken===token&&button.querySelector('.wb-shaelvien-dpad-art'))return;
   button.querySelector('.wb-shaelvien-dpad-art')?.remove();
   const art=image(`${ASSET_BASE}/keyboards/${safeMode}/dpad/${direction}.png`,'wb-shaelvien-dpad-art');
   art.addEventListener('error',()=>{art.src=DPAD_FALLBACK[direction]},{once:true});
   button.prepend(art);
   button.dataset.shaelvienDpadToken=token;
   button.dataset.accessTranslation='available';
  });
 }
 function apply(){
  const next=document.querySelector('.worldbuilder-studio .wb-device-keyboard');
  if(!next)return;
  keyboard=next;
  keyboard.classList.add('wb-shaelvien-skinned');
  const mode=activeMode(keyboard);
  keyboard.dataset.shaelvienKeyboardMode=mode;
  keyboard.querySelectorAll('.wb-device-keys .wb-device-key').forEach(button=>skinKey(button,mode));
  skinDpad(keyboard,mode);
 }
 function schedule(){
  if(frame)return;
  frame=requestAnimationFrame(()=>{frame=0;apply()});
 }
 function start(){
  ensureStyle();apply();
  observer=new MutationObserver(schedule);
  observer.observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['aria-selected','class']});
  document.addEventListener('click',event=>{if(event.target?.closest?.('.wb-device-mode,.wb-device-key,.wb-dpad-key'))schedule()},true);
  window.addEventListener('rist-sprite-playback',schedule);
  window.addEventListener('rist:viewer-state',schedule);
  window.addEventListener('resize',schedule,{passive:true});
  window.addEventListener('orientationchange',schedule,{passive:true});
 }

 window.RistWorldBuilderShaelvienKeyboardSkin={
  refresh:schedule,
  assetBase:ASSET_BASE,
  currentMode:()=>keyboard?activeMode(keyboard):null
 };

 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
