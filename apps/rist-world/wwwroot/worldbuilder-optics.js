(()=>{
 'use strict';
 const DEPTH_STEP=.05;
 let observer=null;
 let depthQueue=Promise.resolve();
 let activeDialPointer=null;

 const clamp=(value,min,max)=>Math.max(min,Math.min(max,value));
 const studio=()=>document.querySelector('.worldbuilder-studio');
 const contextStrip=()=>studio()?.querySelector('.studio-context-strip');
 const command=name=>[...(studio()?.querySelectorAll('.studio-command-rail button')||[])].find(button=>(button.querySelector('strong')?.textContent||'').trim()===name);
 const locked=()=>window.ristViewerAuthority?.get?.().locked??(localStorage.getItem('rist.world.viewerLocked')!=='false');
 const readNumber=(text,fallback=0)=>{const match=String(text??'').match(/-?\d+(?:\.\d+)?/);return match?Number(match[0]):fallback;};
 const nextFrame=()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)));
 const readDepth=()=>{
  const layer=readNumber(command('Layers')?.querySelector('small')?.textContent,0);
  const tier=readNumber(command('Tiers')?.querySelector('small')?.textContent,0);
  return{layer,tier};
 };
 const parallaxDepth=tier=>{
  const value=window.ristParallax?.depthForTier?.(tier);
  return clamp(Number.isFinite(Number(value))?Number(value):1,0,2);
 };
 const setParallaxDepth=(tier,value)=>{
  const next=clamp(Number(value)||0,0,2);
  if(window.ristParallax?.setTierDepth)window.ristParallax.setTierDepth(tier,next);
  render();
  return next;
 };

 function ensureStyle(){
  let style=document.getElementById('rist-worldbuilder-optics-style');
  if(style)return style;
  style=document.createElement('style');
  style.id='rist-worldbuilder-optics-style';
  style.textContent=`
   .worldbuilder-studio #viewer-frame-controls,
   .worldbuilder-studio .viewer-frame-controls,
   .worldbuilder-studio .viewer-navigation-strip,
   .worldbuilder-studio .wb-coordinate-legend,
   .worldbuilder-studio .coordinate-legend,
   .worldbuilder-studio .viewer-navigator,
   .worldbuilder-studio .wb-axis-ruler,
   .worldbuilder-studio .wb-z-ruler,
   .worldbuilder-studio .wb-x-ruler,
   .worldbuilder-studio .wb-y-ruler,
   .worldbuilder-studio .rist-coordinate-frame,
   .worldbuilder-studio .optic-backend-control{display:none!important;visibility:hidden!important;pointer-events:none!important}
   .worldbuilder-studio .studio-mini-panel[aria-label="Layer controls"],
   .worldbuilder-studio .studio-mini-panel[aria-label="Tier controls"]{visibility:hidden!important;pointer-events:none!important;opacity:0!important}
   .worldbuilder-studio .studio-home,.worldbuilder-studio .studio-profile{font-size:15px!important}
   .worldbuilder-studio .studio-context-strip{height:36px!important;overflow:hidden!important}
   .worldbuilder-studio .studio-context-strip>.studio-ticker{display:none!important}
   .worldbuilder-studio .wb-viewer-optics{box-sizing:border-box;width:100%;height:36px;display:grid;grid-template-columns:repeat(5,minmax(0,1fr));align-items:center;gap:2px;padding:1px 2px;background:#071018;overflow:hidden;touch-action:none;user-select:none;-webkit-user-select:none}
   .worldbuilder-studio .wb-optic{min-width:0;height:34px;display:grid;grid-template-columns:12px minmax(27px,1fr) 12px;align-items:center;gap:1px;border-left:1px solid rgba(113,91,45,.42)}
   .worldbuilder-studio .wb-optic:first-child{border-left:0}
   .worldbuilder-studio .wb-optic-step{box-sizing:border-box;width:12px;height:32px;padding:0;border:0;background:transparent;color:#8ca4b1;font:900 11px/1 system-ui;touch-action:manipulation}
   .worldbuilder-studio .wb-optic-step:disabled{opacity:.22}
   .worldbuilder-studio .wb-optic-knob{--dial-turn:0deg;position:relative;justify-self:center;box-sizing:border-box;width:31px;height:31px;border:1px solid #816b3a;border-radius:50%;background:radial-gradient(circle at 50% 46%,#17252e 0 36%,#0b141b 38% 58%,#25333a 60% 64%,#0a1116 66% 100%);box-shadow:inset 0 0 0 2px #05090c,0 1px 3px #000a;color:#f0ddb0;display:grid;grid-template-rows:10px 1fr;place-items:center;padding:4px 0 2px;touch-action:none;cursor:ns-resize;overflow:hidden}
   .worldbuilder-studio .wb-optic-knob::before{content:"";position:absolute;left:50%;top:1px;width:1px;height:6px;background:#e6c66f;transform-origin:50% 14px;transform:translateX(-50%) rotate(var(--dial-turn));box-shadow:0 0 3px #e6c66f}
   .worldbuilder-studio .wb-optic-knob::after{content:"";position:absolute;inset:2px;border-radius:50%;border:1px dashed rgba(142,166,179,.22);pointer-events:none}
   .worldbuilder-studio .wb-optic-label{position:relative;z-index:1;color:#7ea9c2;font:900 6px/1 system-ui;letter-spacing:.04em}
   .worldbuilder-studio .wb-optic-value{position:relative;z-index:1;max-width:27px;color:#f3dfaa;font:900 9px/1 system-ui;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
   .worldbuilder-studio .wb-optic.locked .wb-optic-knob{filter:saturate(.45) brightness(.72);cursor:not-allowed}
   @media(max-width:760px){
    .worldbuilder-studio .wb-viewer-optics{gap:1px;padding-inline:1px}
    .worldbuilder-studio .wb-optic{grid-template-columns:10px minmax(25px,1fr) 10px}
    .worldbuilder-studio .wb-optic-step{width:10px;font-size:10px}
    .worldbuilder-studio .wb-optic-knob{width:29px;height:29px}
   }
  `;
  document.head.appendChild(style);
  return style;
 }

 const dialTurns={
  x:value=>`${(Number(value)||0)*15}deg`,
  y:value=>`${(Number(value)||0)*15}deg`,
  layer:value=>`${(Number(value)||0)*30}deg`,
  tier:value=>`${(Number(value)||0)*30}deg`,
  depth:value=>`${(Number(value)||0)*180}deg`
 };

 function makeOptic(key,label,title){
  const host=document.createElement('div');host.className='wb-optic';host.dataset.axis=key;host.title=title;
  const down=document.createElement('button');down.type='button';down.className='wb-optic-step';down.textContent='‹';down.setAttribute('aria-label',`${title} decrease`);
  const knob=document.createElement('button');knob.type='button';knob.className='wb-optic-knob';knob.setAttribute('aria-label',`${title} dial`);
  const name=document.createElement('span');name.className='wb-optic-label';name.textContent=label;
  const value=document.createElement('strong');value.className='wb-optic-value';value.textContent='0';
  knob.append(name,value);
  const up=document.createElement('button');up.type='button';up.className='wb-optic-step';up.textContent='›';up.setAttribute('aria-label',`${title} increase`);
  host.append(down,knob,up);
  return{key,host,down,knob,up,value};
 }

 function retireLegacyNavigation(){
  document.querySelectorAll('.worldbuilder-studio .wb-coordinate-legend,.worldbuilder-studio .coordinate-legend,.worldbuilder-studio .viewer-navigator').forEach(node=>node.remove());
  for(const label of ['Layers','Tiers'])command(label)?.classList.toggle('optic-backend-control',!!contextStrip());
 }

 let controls=null;
 function ensureControls(){
  const strip=contextStrip();if(!strip)return null;
  retireLegacyNavigation();
  let nav=strip.querySelector('.wb-viewer-optics');
  if(nav&&controls)return controls;
  nav?.remove();
  nav=document.createElement('nav');nav.className='wb-viewer-optics';nav.setAttribute('aria-label','Precision viewer optics');
  const items={
   x:makeOptic('x','X','Viewer X'),
   y:makeOptic('y','Y','Viewer Y'),
   layer:makeOptic('layer','L','Z layer'),
   tier:makeOptic('tier','T','Z tier'),
   depth:makeOptic('depth','D','Parallax depth')
  };
  for(const item of Object.values(items))nav.appendChild(item.host);
  strip.appendChild(nav);
  controls={nav,items};
  const applyStep=(key,delta)=>{
   if((key==='x'||key==='y'||key==='layer'||key==='tier')&&locked())return;
   if(key==='x'||key==='y'){window.ristViewerNavigation?.nudge?.(key,delta);return;}
   if(key==='depth'){const {tier}=readDepth();setParallaxDepth(tier,parallaxDepth(tier)+(delta*DEPTH_STEP));return;}
   depthQueue=depthQueue.then(()=>stepWorldDepth(key,delta)).catch(()=>{});
  };
  for(const item of Object.values(items)){
   item.down.addEventListener('click',()=>applyStep(item.key,-1));
   item.up.addEventListener('click',()=>applyStep(item.key,1));
   item.knob.addEventListener('wheel',event=>{event.preventDefault();applyStep(item.key,event.deltaY>0?-1:1);},{passive:false});
   let drag=null;
   item.knob.addEventListener('pointerdown',event=>{
    if(event.pointerType==='mouse'&&event.button!==0)return;
    if(!event.isPrimary||activeDialPointer!==null)return;
    if(item.key!=='depth'&&locked())return;
    activeDialPointer=event.pointerId;
    drag={id:event.pointerId,x:event.clientX,y:event.clientY,travel:0};
    item.knob.setPointerCapture?.(event.pointerId);event.preventDefault();event.stopPropagation();
   });
   item.knob.addEventListener('pointermove',event=>{
    if(!drag||drag.id!==event.pointerId)return;
    const dx=event.clientX-drag.x,dy=event.clientY-drag.y;drag.x=event.clientX;drag.y=event.clientY;drag.travel+=dx-dy;
    while(Math.abs(drag.travel)>=9){const dir=drag.travel>0?1:-1;drag.travel-=dir*9;applyStep(item.key,dir);}
    event.preventDefault();event.stopPropagation();
   });
   const finish=event=>{
    if(!drag||drag.id!==event.pointerId)return;
    activeDialPointer=null;drag=null;event.preventDefault();event.stopPropagation();
   };
   item.knob.addEventListener('pointerup',finish);item.knob.addEventListener('pointercancel',finish);
  }
  return controls;
 }

 async function stepWorldDepth(kind,delta){
  if(locked())return;
  const triggerName=kind==='layer'?'Layers':'Tiers';
  const panelLabel=kind==='layer'?'Layer controls':'Tier controls';
  const actionText=`${kind==='layer'?'Layer':'Tier'} ${delta<0?'Down':'Up'}`;
  let panel=studio()?.querySelector(`.studio-mini-panel[aria-label="${panelLabel}"]`);
  const wasOpen=!!panel;
  if(!panel){command(triggerName)?.click();await nextFrame();panel=studio()?.querySelector(`.studio-mini-panel[aria-label="${panelLabel}"]`);}
  const action=panel?[...panel.querySelectorAll('button')].find(button=>(button.textContent||'').trim()===actionText):null;
  if(action&&!action.disabled)action.click();
  await nextFrame();
  if(!wasOpen)command(triggerName)?.click();
  await nextFrame();render();
 }

 function render(){
  retireLegacyNavigation();
  const ui=ensureControls();if(!ui)return;
  const nav=window.ristViewerNavigation?.get?.()||{x:0,y:0};
  const depth=readDepth();
  const values={x:Math.round(Number(nav.x)||0),y:Math.round(Number(nav.y)||0),layer:depth.layer,tier:depth.tier,depth:parallaxDepth(depth.tier)};
  for(const [key,item] of Object.entries(ui.items)){
   const value=values[key];const text=key==='depth'?Number(value).toFixed(2):String(value);
   if(item.value.textContent!==text)item.value.textContent=text;
   item.knob.style.setProperty('--dial-turn',dialTurns[key](value));
   const isLocked=key!=='depth'&&locked();item.host.classList.toggle('locked',isLocked);item.down.disabled=isLocked;item.up.disabled=isLocked;item.knob.setAttribute('aria-disabled',String(isLocked));
  }
 }

 function sync(){ensureStyle();retireLegacyNavigation();ensureControls();render();}
 function start(){
  ensureStyle();sync();
  observer=new MutationObserver(()=>requestAnimationFrame(sync));observer.observe(document.body,{childList:true,subtree:true});
  window.addEventListener('rist:viewer-state',render);
  window.addEventListener('rist:viewer-pan',render);
  window.addEventListener('rist-parallax-settings',render);
  window.addEventListener('storage',render);
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
