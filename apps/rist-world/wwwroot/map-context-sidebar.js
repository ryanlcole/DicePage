(()=>{
 'use strict';
 const TZ_KEY='rist.context.timezone.v1';
 const DEFAULT_ZONE={mode:'utc',zone:'UTC',label:'UTC'};
 const fmt=n=>{
  const a=Math.abs(n),d=a>=100?0:a>=10?1:a>=1?2:a>=.1?3:4;
  return (a<1e-9?0:n).toFixed(d).replace(/\.0+$|(?<=\.[0-9]*?)0+$/,'').replace(/\.$/,'');
 };
 const parseScale=map=>{
  const text=map.querySelector('.status')?.textContent||'';
  const match=text.match(/([0-9]+(?:\.[0-9]+)?)\s*(mi|km|m|yd|ft)\/(?:sq|hex)/i);
  return match?{distance:Number(match[1])||1,unit:match[2]}:{distance:1,unit:''};
 };
 function currentZone(){
  try{return {...DEFAULT_ZONE,...(JSON.parse(localStorage.getItem(TZ_KEY)||'null')||{})}}
  catch{return {...DEFAULT_ZONE}}
 }
 function visibleCenter(map){
  const stage=map.querySelector('.world-stage');
  if(!stage)return{x:0,y:0,unit:''};
  const mapRect=map.getBoundingClientRect(),stageRect=stage.getBoundingClientRect();
  if(mapRect.width<2||stageRect.width<2)return{x:0,y:0,unit:''};
  const scale=parseScale(map),cols=20,rows=13;
  const halfX=cols*scale.distance/2,halfY=rows*scale.distance/2;
  const cx=mapRect.left+mapRect.width/2,cy=mapRect.top+mapRect.height/2;
  return{
   x:Math.max(-halfX,Math.min(halfX,(((cx-stageRect.left)/stageRect.width)-.5)*cols*scale.distance)),
   y:Math.max(-halfY,Math.min(halfY,(.5-((cy-stageRect.top)/stageRect.height))*rows*scale.distance)),
   unit:scale.unit
  };
 }
 function editContext(key,source){
  if(key==='utc'){openTimeEditor(source);return}
  document.dispatchEvent(new CustomEvent('rist:context-edit',{detail:{context:key,source}}));
 }
 function openTimeEditor(anchor){
  document.querySelector('.map-context-time-editor')?.remove();
  const current=currentZone();
  const box=document.createElement('div');
  box.className='map-context-time-editor';
  box.innerHTML=`<strong>Clock</strong><label><span>Display</span><select class="context-time-mode"><option value="utc">UTC</option><option value="local">Local</option><option value="zone">Other time zone</option></select></label><label class="context-time-zone-row"><span>Time zone</span><input class="context-time-zone" type="text" inputmode="text" placeholder="America/New_York" value="${current.mode==='zone'?(current.zone||'').replace(/"/g,'&quot;'):''}"></label><div class="context-time-actions"><button type="button" data-cancel>Cancel</button><button type="button" data-save>Apply</button></div>`;
  document.body.appendChild(box);
  const rect=anchor?.getBoundingClientRect?.()||{right:innerWidth/2,top:8};
  box.style.right=Math.max(8,innerWidth-rect.right)+'px';
  box.style.top=Math.min(innerHeight-box.offsetHeight-8,Math.max(8,rect.top+20))+'px';
  const mode=box.querySelector('.context-time-mode');
  const zoneRow=box.querySelector('.context-time-zone-row');
  const zone=box.querySelector('.context-time-zone');
  mode.value=current.mode||'utc';
  const sync=()=>zoneRow.hidden=mode.value!=='zone';
  mode.onchange=sync;sync();
  box.querySelector('[data-cancel]').onclick=()=>box.remove();
  box.querySelector('[data-save]').onclick=()=>{
   let next;
   if(mode.value==='local'){
    const value=Intl.DateTimeFormat().resolvedOptions().timeZone||'UTC';
    next={mode:'local',zone:value,label:'LOCAL'};
   }else if(mode.value==='zone'){
    const value=(zone.value||'').trim();
    try{new Intl.DateTimeFormat(undefined,{timeZone:value}).format(new Date())}
    catch{
     zone.setCustomValidity('Enter a valid IANA time zone, for example America/New_York.');
     zone.reportValidity();
     return;
    }
    next={mode:'zone',zone:value,label:value.split('/').pop()?.replace(/_/g,' ')||value};
   }else next={...DEFAULT_ZONE};
   localStorage.setItem(TZ_KEY,JSON.stringify(next));
   box.remove();
   tick();
  };
 }
 function ensureMapContext(){
  document.querySelectorAll('.map-context-sidebar').forEach(node=>node.remove());
  document.querySelectorAll('.map-shell').forEach(shell=>{
   shell.classList.add('map-context-ready');
   shell.classList.remove('map-context-collapsed');
   const map=shell.querySelector(':scope > .map');
   if(!map)return;
   let coord=map.querySelector(':scope > .map-current-coordinates');
   if(!coord){
    coord=document.createElement('div');
    coord.className='map-current-coordinates';
    coord.setAttribute('aria-label','Current map coordinates');
    map.appendChild(coord);
   }
   const center=visibleCenter(map);
   coord.textContent=`${fmt(center.x)}, ${fmt(center.y)}${center.unit?` ${center.unit}`:''}`;
  });
 }
 function tick(){
  if(document.hidden)return;
  const now=new Date(),config=currentZone(),zone=config.zone||'UTC';
  let dateFormatter,timeFormatter;
  try{
   dateFormatter=new Intl.DateTimeFormat(undefined,{year:'numeric',month:'2-digit',day:'2-digit',timeZone:zone});
   timeFormatter=new Intl.DateTimeFormat(undefined,{hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false,timeZone:zone});
  }catch{
   dateFormatter=new Intl.DateTimeFormat(undefined,{year:'numeric',month:'2-digit',day:'2-digit',timeZone:'UTC'});
   timeFormatter=new Intl.DateTimeFormat(undefined,{hour:'2-digit',minute:'2-digit',second:'2-digit',hour12:false,timeZone:'UTC'});
  }
  document.querySelectorAll('.world-context-date time').forEach(node=>{
   node.textContent=dateFormatter.format(now);
   node.dateTime=now.toISOString().slice(0,10);
  });
  document.querySelectorAll('.world-context-utc').forEach(button=>{
   const label=button.querySelector('strong');
   if(label)label.textContent=`${config.label||'UTC'}:`;
   const time=button.querySelector('time');
   if(time){time.textContent=timeFormatter.format(now);time.dateTime=now.toISOString()}
  });
 }
 window.RistWorldContext={
  edit:key=>{
   const source=document.querySelector(`.world-context-strip [data-context="${key}"]`)||document.querySelector('.header-settings-button');
   editContext(key,source);
  },
  openClock:()=>openTimeEditor(document.querySelector('.world-context-utc')||document.querySelector('.header-settings-button'))
 };
 const queue=()=>window.RistRuntime?.frame?.('world-context',ensureMapContext)??requestAnimationFrame(ensureMapContext);
 document.addEventListener('rist:dom-change',queue);
 document.addEventListener('rist:viewport-change',queue);
 document.addEventListener('visibilitychange',()=>{if(!document.hidden){queue();tick()}});
 setInterval(tick,1000);
 queue();
 tick();
})();
