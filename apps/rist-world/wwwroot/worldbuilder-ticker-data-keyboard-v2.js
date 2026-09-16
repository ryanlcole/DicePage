(()=>{
 'use strict';

 const SETTINGS_KEY='rist.worldbuilder.tickerData.v1';
 const LEGACY_WIDGET_KEY='rist.worldbuilder.viewerWidgets.v1';
 const DEFAULTS=Object.freeze({timeFormat:'12',dateFormat:'short',weather:true,viewer:false});
 const EDIT_DOMAINS=['sky','calendar','ugc','stars'];
 let settings=readSettings();
 let weather=null;
 let frame=0;
 let observer=null;
 let timer=0;

 function readSettings(){try{return{...DEFAULTS,...JSON.parse(localStorage.getItem(SETTINGS_KEY)||'{}')}}catch{return{...DEFAULTS}}}
 function writeSettings(next=settings){
  settings={...DEFAULTS,...next};
  try{localStorage.setItem(SETTINGS_KEY,JSON.stringify(settings))}catch{}
  try{localStorage.setItem(LEGACY_WIDGET_KEY,JSON.stringify({clock:false,date:false,weather:false,coords:false}))}catch{}
 }
 function announce(message){const live=document.querySelector('.worldbuilder-studio .wb-device-live-region');if(live)live.textContent=message}
 function schedule(){if(frame)return;frame=requestAnimationFrame(()=>{frame=0;sync()})}
 function viewerState(){try{return window.ristViewerAuthority?.get?.()||{}}catch{return{}}}
 function worldBuilderActive(){return !!document.querySelector('.worldbuilder-studio')}
 function formatTime(now){return now.toLocaleTimeString([],settings.timeFormat==='24'?{hour:'2-digit',minute:'2-digit',hour12:false}:{hour:'numeric',minute:'2-digit',hour12:true})}
 function formatDate(now){return settings.dateFormat==='full'?now.toLocaleDateString([],{weekday:'short',month:'short',day:'numeric',year:'numeric'}):now.toLocaleDateString([],{weekday:'short',month:'short',day:'numeric'})}
 function weatherText(){
  if(!weather)return'';
  const summary=String(weather.summary||weather.condition||'').trim();
  const temp=weather.temperature;
  const unit=String(weather.unit||'').replace('°','').trim();
  const tempText=temp===undefined||temp===null||temp===''?'':`${temp}°${unit}`;
  return[tempText,summary].filter(Boolean).join(' ');
 }
 function viewerText(){
  const s=viewerState();
  const x=Number(s.x??s.camX??s.cameraX??0),y=Number(s.y??s.camY??s.cameraY??0),n=Math.max(1,Math.round(Number(s.visibleCells)||12));
  return`X ${Number.isFinite(x)?x.toFixed(1):'0.0'} · Y ${Number.isFinite(y)?y.toFixed(1):'0.0'} · ${n}×${n}`;
 }
 function makeReadout(kind,label){
  const node=document.createElement('span');node.className=`world-context-data-readout world-context-data-${kind}`;node.dataset.tickerData=kind;
  const title=document.createElement('strong');title.textContent=label;
  const value=document.createElement(kind==='time'||kind==='date'?'time':'span');value.dataset.tickerDataValue=kind;
  node.append(title,value);return node;
 }
 function groups(track){const direct=[...track.querySelectorAll(':scope > [data-ticker-group]')];return direct.length?direct:[track]}
 function hideLegacyNoise(group){
  const patterns=[/\bSTARS\s*:\s*EDIT\b/i,/\bSKY\s*:\s*EDIT\b/i,/\bCALENDAR\s*:\s*EDIT\b/i,/\bUGC\s*:\s*EDIT\b/i,/^START MENU$/i];
  [...group.children].forEach(node=>{
   if(node.dataset?.tickerData)return;
   const text=(node.textContent||'').trim().replace(/\s+/g,' ');
   const hide=patterns.some(pattern=>pattern.test(text))||/^[·•|]+$/.test(text)||node.classList?.contains('world-context-date')||node.classList?.contains('world-context-utc')||node.classList?.contains('world-context-start-menu');
   if(hide){node.dataset.tickerDataHidden='1';node.hidden=true;node.setAttribute('aria-hidden','true')}
  });
 }
 function ensureTicker(){
  const track=document.querySelector('.world-context-strip .world-context-track');if(!track)return;
  track.dataset.dataTicker='2';
  for(const group of groups(track)){
   hideLegacyNoise(group);
   const wanted=['time','date'];
   if(settings.weather&&weatherText())wanted.push('weather');
   if(settings.viewer&&worldBuilderActive())wanted.push('viewer');
   for(const kind of ['time','date','weather','viewer']){
    let node=group.querySelector(`:scope > [data-ticker-data="${kind}"]`);
    if(wanted.includes(kind)&&!node){node=makeReadout(kind,kind==='viewer'?'VIEW':kind.toUpperCase());group.appendChild(node)}
    if(node){node.hidden=!wanted.includes(kind);node.setAttribute('aria-hidden',wanted.includes(kind)?'false':'true')}
   }
   const now=new Date();
   const values={time:formatTime(now),date:formatDate(now),weather:weatherText(),viewer:viewerText()};
   for(const[kind,value]of Object.entries(values)){
    const node=group.querySelector(`:scope > [data-ticker-data="${kind}"] [data-ticker-data-value]`);
    if(node&&node.textContent!==value)node.textContent=value;
   }
  }
 }
 function keepWidgetLayerStable(){
  document.querySelectorAll('.worldbuilder-studio .wb-viewer-widgets').forEach(node=>{
   node.hidden=true;
   node.setAttribute('aria-hidden','true');
   node.style.setProperty('display','none','important');
   node.style.setProperty('pointer-events','none','important');
   node.dataset.tickerSuppressed='1';
  });
 }
 function makeKey(label,sub,action,active=false){
  const button=document.createElement('button');button.type='button';button.className='wb-device-key wb-data-key';if(active)button.classList.add('active');
  button.dataset.accessRole='keyboard-key';button.dataset.accessTranslation='available';button.setAttribute('aria-label',sub?`${label}. ${sub}`:label);
  const strong=document.createElement('strong');strong.textContent=label;button.appendChild(strong);
  if(sub){const small=document.createElement('small');small.textContent=sub;button.appendChild(small)}
  button.addEventListener('click',event=>{event.preventDefault();action?.()});return button;
 }
 function setSetting(patch,message){writeSettings({...settings,...patch});announce(message);schedule()}
 function requestEdit(domain){
  window.dispatchEvent(new CustomEvent('rist:worldbuilder-data-edit-request',{detail:{domain,source:'data-keyboard',requiresAuthoritativeWriter:true},bubbles:true,composed:true,cancelable:true}));
  announce(`${domain[0].toUpperCase()+domain.slice(1)} data edit requested`);
 }
 function renderDataKeyboard(){
  const tab=document.querySelector('.worldbuilder-studio .wb-device-mode[data-mode="widgets"]');if(!tab)return;
  tab.textContent='DATA';tab.setAttribute('aria-label','Data keyboard');
  if(tab.getAttribute('aria-selected')!=='true')return;
  const title=document.querySelector('.worldbuilder-studio .wb-device-mode-name');if(title)title.textContent='Data keyboard';
  const keys=document.querySelector('.worldbuilder-studio .wb-device-keys');if(!keys)return;
  const token=JSON.stringify(settings);
  if(keys.dataset.dataKeyboardV2===token&&keys.querySelector('.wb-data-key'))return;
  keys.replaceChildren(
   makeKey('Time',settings.timeFormat==='24'?'24 hour':'12 hour',()=>setSetting({timeFormat:settings.timeFormat==='24'?'12':'24'},'Time format changed'),true),
   makeKey('Date',settings.dateFormat==='full'?'Full':'Compact',()=>setSetting({dateFormat:settings.dateFormat==='full'?'short':'full'},'Date format changed'),true),
   makeKey('Weather',settings.weather?'Ticker when connected':'Hidden',()=>setSetting({weather:!settings.weather},`Weather ticker ${settings.weather?'hidden':'enabled'}`),settings.weather),
   makeKey('Viewer',settings.viewer?'Ticker shown':'Hidden',()=>setSetting({viewer:!settings.viewer},`Viewer ticker ${settings.viewer?'hidden':'shown'}`),settings.viewer),
   makeKey('Stars','Edit data',()=>requestEdit('stars')),
   makeKey('Sky','Edit data',()=>requestEdit('sky')),
   makeKey('Calendar','Edit data',()=>requestEdit('calendar')),
   makeKey('UGC','Edit data',()=>requestEdit('ugc')),
   makeKey('Reset','Ticker data',()=>{settings={...DEFAULTS};writeSettings(settings);announce('Ticker data reset');schedule()})
  );
  keys.dataset.dataKeyboardV2=token;
 }
 function renameAccessShortcut(){
  const key=[...document.querySelectorAll('.worldbuilder-studio .wb-device-key')].find(node=>(node.querySelector('strong')?.textContent||'').trim()==='Widgets');
  if(key){key.querySelector('strong').textContent='Data';key.setAttribute('aria-label','Data. Ticker and world data controls')}
 }
 function sync(){keepWidgetLayerStable();ensureTicker();renderDataKeyboard();renameAccessShortcut()}
 function start(){
  writeSettings(settings);sync();
  observer=new MutationObserver(schedule);observer.observe(document.documentElement,{childList:true,subtree:true,attributes:true,attributeFilter:['aria-selected','class']});
  document.addEventListener('click',event=>{if(event.target?.closest?.('.wb-device-mode,.wb-device-key'))setTimeout(schedule,0)},true);
  window.addEventListener('rist:viewer-state',schedule);
  window.addEventListener('rist:weather-state',event=>{weather=event.detail||null;schedule()});
  timer=setInterval(()=>{ensureTicker();keepWidgetLayerStable()},1000);
 }
 window.RistWorldTickerData={get:()=>({...settings}),set:patch=>setSetting(patch||{},'Ticker data updated'),setWeather:detail=>{weather=detail||null;schedule()},edit:domain=>{if(EDIT_DOMAINS.includes(domain))requestEdit(domain)},refresh:schedule,version:'2'};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
