(()=>{
 'use strict';

 const SETTINGS_KEY='rist.worldbuilder.tickerData.v1';
 const LEGACY_WIDGET_KEY='rist.worldbuilder.viewerWidgets.v1';
 const DEFAULTS=Object.freeze({timeFormat:'12',dateFormat:'short',weather:true,viewer:false});
 const EDIT_DOMAINS=['sky','calendar','ugc'];
 let settings=readSettings();
 let weather=null;
 let syncFrame=0;
 let observer=null;
 let timer=0;

 function readSettings(){
  try{return{...DEFAULTS,...JSON.parse(localStorage.getItem(SETTINGS_KEY)||'{}')}}catch{return{...DEFAULTS}}
 }
 function saveSettings(next=settings){
  settings={...DEFAULTS,...next};
  try{localStorage.setItem(SETTINGS_KEY,JSON.stringify(settings))}catch{}
  try{localStorage.setItem(LEGACY_WIDGET_KEY,JSON.stringify({clock:false,date:false,weather:false,coords:false}))}catch{}
  window.dispatchEvent(new CustomEvent('rist:world-ticker-settings',{detail:{...settings},bubbles:true,composed:true}));
 }
 function announce(message){
  const live=document.querySelector('.worldbuilder-studio .wb-device-live-region');
  if(live)live.textContent=message;
 }
 function schedule(){
  if(syncFrame)return;
  syncFrame=requestAnimationFrame(()=>{syncFrame=0;sync()});
 }
 function worldBuilderActive(){return !!document.querySelector('.worldbuilder-studio')}
 function viewerState(){try{return window.ristViewerAuthority?.get?.()||{}}catch{return{}}}
 function formatTime(now){
  return now.toLocaleTimeString([],settings.timeFormat==='24'
   ?{hour:'2-digit',minute:'2-digit',hour12:false}
   :{hour:'numeric',minute:'2-digit',hour12:true});
 }
 function formatDate(now){
  return settings.dateFormat==='full'
   ?now.toLocaleDateString([],{weekday:'short',month:'short',day:'numeric',year:'numeric'})
   :now.toLocaleDateString([],{weekday:'short',month:'short',day:'numeric'});
 }
 function weatherText(){
  if(!weather)return'';
  const summary=String(weather.summary||weather.condition||'').trim();
  const temp=weather.temperature;
  const unit=String(weather.unit||'').replace('°','').trim();
  const tempText=temp===undefined||temp===null||temp===''?'':`${temp}°${unit}`;
  return [tempText,summary].filter(Boolean).join(' ');
 }
 function viewerText(){
  const state=viewerState();
  const x=Number(state.x??state.camX??state.cameraX??0);
  const y=Number(state.y??state.camY??state.cameraY??0);
  const n=Math.max(1,Math.round(Number(state.visibleCells)||12));
  const sx=Number.isFinite(x)?x.toFixed(1):'0.0';
  const sy=Number.isFinite(y)?y.toFixed(1):'0.0';
  return `X ${sx} · Y ${sy} · ${n}×${n}`;
 }
 function makeReadout(kind,label){
  const node=document.createElement('span');
  node.className=`world-context-data-readout world-context-data-${kind}`;
  node.dataset.tickerData=kind;
  const title=document.createElement('strong');title.textContent=label;
  const value=document.createElement(kind==='time'||kind==='date'?'time':'span');value.dataset.tickerDataValue=kind;
  node.append(title,value);
  return node;
 }
 function directGroups(track){
  const groups=[...track.querySelectorAll(':scope > [data-ticker-group]')];
  return groups.length?groups:[track];
 }
 function hideLegacyTickerNoise(group){
  const patterns=[/\bSKY\s*:\s*EDIT\b/i,/\bCALENDAR\s*:\s*EDIT\b/i,/\bUGC\s*:\s*EDIT\b/i,/^START MENU$/i];
  [...group.children].forEach(node=>{
   if(node.dataset?.tickerData)return;
   const text=(node.textContent||'').trim().replace(/\s+/g,' ');
   const hide=patterns.some(pattern=>pattern.test(text))||/^[·•|]+$/.test(text)||node.classList?.contains('world-context-date')||node.classList?.contains('world-context-utc')||node.classList?.contains('world-context-start-menu');
   if(hide)node.dataset.tickerDataHidden='1';
  });
 }
 function ensureTicker(){
  const track=document.querySelector('.world-context-strip .world-context-track');
  if(!track)return;
  track.dataset.dataTicker='1';
  for(const group of directGroups(track)){
   hideLegacyTickerNoise(group);
   const wanted=['time','date'];
   if(settings.weather&&weatherText())wanted.push('weather');
   if(settings.viewer&&worldBuilderActive())wanted.push('viewer');
   for(const kind of ['time','date','weather','viewer']){
    let node=group.querySelector(`:scope > [data-ticker-data="${kind}"]`);
    if(wanted.includes(kind)&&!node){node=makeReadout(kind,kind==='viewer'?'VIEW':kind.toUpperCase());group.appendChild(node)}
    if(node)node.hidden=!wanted.includes(kind);
   }
   const now=new Date();
   const values={time:formatTime(now),date:formatDate(now),weather:weatherText(),viewer:viewerText()};
   for(const [kind,value] of Object.entries(values)){
    const node=group.querySelector(`:scope > [data-ticker-data="${kind}"] [data-ticker-data-value]`);
    if(node&&node.textContent!==value)node.textContent=value;
   }
  }
 }

 function makeDataKey(label,sub,action,options={}){
  const button=document.createElement('button');
  button.type='button';button.className='wb-device-key wb-data-key';
  if(options.active)button.classList.add('active');
  if(options.wide)button.classList.add('wide');
  button.dataset.accessRole='keyboard-key';button.dataset.accessTranslation='available';
  button.setAttribute('aria-label',sub?`${label}. ${sub}`:label);
  const strong=document.createElement('strong');strong.textContent=label;button.appendChild(strong);
  if(sub){const small=document.createElement('small');small.textContent=sub;button.appendChild(small)}
  button.addEventListener('click',event=>{event.preventDefault();action?.()});
  return button;
 }
 function setSetting(patch,message){
  saveSettings({...settings,...patch});announce(message);schedule();
 }
 function requestEdit(domain){
  const event=new CustomEvent('rist:worldbuilder-data-edit-request',{detail:{domain,source:'data-keyboard',requiresAuthoritativeWriter:true},bubbles:true,composed:true,cancelable:true});
  window.dispatchEvent(event);
  announce(`${domain[0].toUpperCase()+domain.slice(1)} data edit requested`);
 }
 function renderDataKeyboard(){
  const button=document.querySelector('.worldbuilder-studio .wb-device-mode[data-mode="widgets"]');
  if(!button)return;
  button.textContent='DATA';button.setAttribute('aria-label','Data keyboard');
  const active=button.getAttribute('aria-selected')==='true';
  if(!active)return;
  const modeName=document.querySelector('.worldbuilder-studio .wb-device-mode-name');
  if(modeName)modeName.textContent='Data keyboard';
  const keys=document.querySelector('.worldbuilder-studio .wb-device-keys');
  if(!keys)return;
  const token=JSON.stringify(settings);
  if(keys.dataset.dataKeyboardToken===token&&keys.querySelector('.wb-data-key'))return;
  keys.replaceChildren(
   makeDataKey('Time',settings.timeFormat==='24'?'24 hour':'12 hour',()=>setSetting({timeFormat:settings.timeFormat==='24'?'12':'24'},'Time format changed'),{active:true}),
   makeDataKey('Date',settings.dateFormat==='full'?'Full':'Compact',()=>setSetting({dateFormat:settings.dateFormat==='full'?'short':'full'},'Date format changed'),{active:true}),
   makeDataKey('Weather',settings.weather?'Ticker when connected':'Hidden',()=>setSetting({weather:!settings.weather},`Weather ticker ${settings.weather?'hidden':'enabled'}`),{active:settings.weather}),
   makeDataKey('Viewer',settings.viewer?'Ticker shown':'Hidden',()=>setSetting({viewer:!settings.viewer},`Viewer ticker ${settings.viewer?'hidden':'shown'}`),{active:settings.viewer}),
   makeDataKey('Sky','Edit data',()=>requestEdit('sky')),
   makeDataKey('Calendar','Edit data',()=>requestEdit('calendar')),
   makeDataKey('UGC','Edit data',()=>requestEdit('ugc')),
   makeDataKey('Reset','Ticker data',()=>{settings={...DEFAULTS};saveSettings(settings);announce('Ticker data reset');schedule()},{wide:true})
  );
  keys.dataset.dataKeyboardToken=token;
 }
 function suppressViewerWidgets(){
  document.querySelectorAll('.worldbuilder-studio .wb-viewer-widgets').forEach(node=>node.remove());
 }
 function renameAccessWidgetShortcut(){
  const widgets=[...document.querySelectorAll('.worldbuilder-studio .wb-device-key')].find(node=>(node.querySelector('strong')?.textContent||'').trim()==='Widgets');
  if(widgets){widgets.querySelector('strong').textContent='Data';widgets.setAttribute('aria-label','Data. Ticker and world data controls')}
 }
 function sync(){
  saveSettings(settings);
  suppressViewerWidgets();
  ensureTicker();
  renderDataKeyboard();
  renameAccessWidgetShortcut();
 }
 function start(){
  saveSettings(settings);sync();
  observer=new MutationObserver(schedule);observer.observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['aria-selected','class']});
  document.addEventListener('click',event=>{if(event.target?.closest?.('.wb-device-mode,.wb-device-key'))setTimeout(schedule,0)},true);
  window.addEventListener('rist:viewer-state',schedule);
  window.addEventListener('rist:world-ticker-settings',event=>{settings={...DEFAULTS,...(event.detail||{})};schedule()});
  window.addEventListener('rist:weather-state',event=>{weather=event.detail||null;schedule()});
  timer=setInterval(()=>{ensureTicker();suppressViewerWidgets()},1000);
 }

 window.RistWorldTickerData={
  get:()=>({...settings}),
  set:patch=>setSetting(patch||{},'Ticker data updated'),
  setWeather:detail=>{weather=detail||null;schedule()},
  edit:domain=>{if(EDIT_DOMAINS.includes(domain))requestEdit(domain)},
  refresh:schedule
 };

 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
