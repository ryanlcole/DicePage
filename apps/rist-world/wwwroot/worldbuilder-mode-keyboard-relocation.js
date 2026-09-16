(()=>{
 'use strict';

 const STYLE_ID='rist-worldbuilder-mode-keyboard-relocation-style';
 let observer=null;
 let frame=0;

 function ensureStyle(){
  if(document.getElementById(STYLE_ID))return;
  const style=document.createElement('style');
  style.id=STYLE_ID;
  style.textContent=`
   .worldbuilder-studio .studio-edit-mode,
   .worldbuilder-studio .description-mode-toggle{
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
    opacity:0!important;
    pointer-events:none!important;
   }
   .worldbuilder-studio .wb-world-mode-status{cursor:default!important}
   .worldbuilder-studio .wb-world-mode-status>strong,
   .worldbuilder-studio .wb-world-mode-status>small,
   .worldbuilder-studio .wb-world-mode-action>strong,
   .worldbuilder-studio .wb-world-mode-action>small{
    position:relative;
    z-index:3;
    color:#fff1d2!important;
    text-shadow:0 1px 3px #000!important;
   }
   .worldbuilder-studio .wb-world-mode-action.active>strong,
   .worldbuilder-studio .wb-world-mode-action.active>small{color:#fff8e8!important}
  `;
  document.head.appendChild(style);
 }

 function studio(){return document.querySelector('.worldbuilder-studio')}
 function keyboard(){return studio()?.querySelector('.wb-device-keyboard')||null}
 function currentMode(){
  const selected=keyboard()?.querySelector('.wb-device-mode[aria-selected="true"]');
  return selected?.dataset?.mode||'';
 }
 function keys(){return keyboard()?.querySelector('.wb-device-keys')||null}
 function editBridge(){return studio()?.querySelector('.studio-edit-mode')||null}
 function descriptionBridge(){return studio()?.querySelector('.description-mode-toggle')||null}
 function canEdit(){return !editBridge()}
 function announce(message){const live=studio()?.querySelector('.wb-device-live-region');if(live)live.textContent=message}

 function makeKey(label,sub,{action=null,active=false,status=false,disabled=false}={}){
  const button=document.createElement('button');
  button.type='button';
  button.className='wb-device-key';
  if(active)button.classList.add('active');
  if(status)button.classList.add('wb-world-mode-status');
  else button.classList.add('wb-world-mode-action');
  button.dataset.accessRole=status?'status-key':'keyboard-key';
  button.dataset.accessTranslation='available';
  button.setAttribute('aria-label',sub?`${label}. ${sub}`:label);
  if(status)button.setAttribute('aria-disabled','true');
  if(disabled)button.disabled=true;
  const strong=document.createElement('strong');strong.textContent=label;
  const small=document.createElement('small');small.textContent=sub;
  button.append(strong,small);
  if(status)button.addEventListener('click',event=>event.preventDefault());
  else if(action)button.addEventListener('click',event=>{event.preventDefault();action()});
  return button;
 }

 function enterBuildMode(){
  const bridge=editBridge();
  const button=bridge?.querySelector('button');
  if(!button){announce(canEdit()?'Build mode already active':'Build mode requires sign in');return}
  button.click();
  announce('Entering build mode');
  setTimeout(schedule,0);
 }

 function renderViewerModeKeys(){
  if(currentMode()!=='viewer')return;
  const host=keys();if(!host)return;
  const bridge=editBridge();
  const editable=!bridge;
  const canEnter=!!bridge?.querySelector('button');
  const token=`${editable?'build':'view'}:${canEnter?'enter':'no-enter'}`;
  if(host.dataset.worldModeKeyboardToken===token&&host.querySelector('.wb-world-mode-status'))return;
  host.querySelectorAll('.wb-world-mode-status,.wb-world-mode-action').forEach(node=>node.remove());
  const status=makeKey('World View',editable?'Build mode':'Viewing world',{status:true,active:editable});
  const build=makeKey('Build Mode',editable?'Active':canEnter?'Enter':'Sign in required',{action:enterBuildMode,active:editable,disabled:!editable&&!canEnter});
  host.prepend(build);
  host.prepend(status);
  host.dataset.worldModeKeyboardToken=token;
  window.RistWorldBuilderKeyboardAuthority?.refresh?.();
 }

 function normalizeAccessDescription(){
  if(currentMode()!=='access')return;
  const host=keys();if(!host)return;
  const description=[...host.querySelectorAll('.wb-device-key')].find(button=>(button.querySelector('strong')?.textContent||'').trim()==='Description');
  if(!description)return;
  description.dataset.relocatedDescription='1';
  description.setAttribute('aria-label',descriptionOnly()?'Description only. Text map active':'Description only. Visual map active');
 }
 function descriptionOnly(){return descriptionBridge()?.getAttribute('aria-pressed')==='true'}

 function sync(){
  ensureStyle();
  renderViewerModeKeys();
  normalizeAccessDescription();
 }
 function schedule(){if(frame)return;frame=requestAnimationFrame(()=>{frame=0;sync()})}
 function start(){
  ensureStyle();sync();
  observer=new MutationObserver(schedule);
  observer.observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['class','aria-selected','aria-pressed']});
  document.addEventListener('click',event=>{if(event.target?.closest?.('.wb-device-mode,.wb-device-key,.studio-edit-mode button,.description-mode-toggle'))setTimeout(schedule,0)},true);
  window.addEventListener('rist:game-start',schedule);
  window.addEventListener('pageshow',schedule);
 }

 window.RistWorldBuilderModeKeyboardRelocation={
  refresh:schedule,
  enterBuildMode,
  state:()=>({mode:currentMode(),canEdit:canEdit(),canEnterBuild:!!editBridge()?.querySelector('button'),descriptionOnly:descriptionOnly()})
 };

 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
