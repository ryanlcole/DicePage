(()=>{
 const STUDIO='.rist-art-studio';
 const CANVAS='.rist-art-studio>main>canvas';
 const DRAW_TOOLS=new Set(['pen','paint','fill','erase']);
 const activeTool=host=>host?.querySelector('[data-tool].active')?.dataset.tool||'select';
 const clickTool=(host,name)=>host?.querySelector(`[data-tool="${name}"]`)?.click();
 const ensureLocked=host=>{
  const palette=host?.querySelector('.rist-art-palette');
  const lock=host?.querySelector('.rist-palette-lock');
  if(palette&&lock&&!palette.classList.contains('locked'))lock.click();
 };
 const nudge=(host,dx,dy)=>{
  const canvas=host?.querySelector('main>canvas');
  if(!canvas)return;
  const previous=activeTool(host);
  clickTool(host,'move');
  const r=canvas.getBoundingClientRect(),x=r.left+r.width/2,y=r.top+r.height/2,id=9901;
  canvas.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,pointerId:id,clientX:x,clientY:y,pointerType:'mouse',buttons:1}));
  canvas.dispatchEvent(new PointerEvent('pointermove',{bubbles:true,pointerId:id,clientX:x+dx,clientY:y+dy,pointerType:'mouse',buttons:1}));
  canvas.dispatchEvent(new PointerEvent('pointerup',{bubbles:true,pointerId:id,clientX:x+dx,clientY:y+dy,pointerType:'mouse'}));
  if(previous&&previous!=='move')clickTool(host,previous);
 };
 const addPad=host=>{
  if(!host||host.querySelector('.rist-art-nav-pad'))return;
  const pad=document.createElement('div');
  pad.className='rist-art-nav-pad';
  pad.setAttribute('role','group');
  pad.setAttribute('aria-label','Artwork view controls');
  pad.innerHTML=`<button type="button" data-pan="up" aria-label="Move view up">▲</button><button type="button" data-pan="left" aria-label="Move view left">◀</button><button type="button" data-pan="center" aria-label="Center view">●</button><button type="button" data-pan="right" aria-label="Move view right">▶</button><button type="button" data-pan="down" aria-label="Move view down">▼</button>`;
  host.appendChild(pad);
  pad.querySelector('[data-pan="up"]').onclick=()=>nudge(host,0,54);
  pad.querySelector('[data-pan="down"]').onclick=()=>nudge(host,0,-54);
  pad.querySelector('[data-pan="left"]').onclick=()=>nudge(host,54,0);
  pad.querySelector('[data-pan="right"]').onclick=()=>nudge(host,-54,0);
  pad.querySelector('[data-pan="center"]').onclick=()=>{
   const canvas=host.querySelector('main>canvas');if(!canvas)return;
   const previous=activeTool(host);clickTool(host,'move');
   // Return toward origin with repeated deterministic nudges rather than touch-dragging the artwork.
   for(let i=0;i<8;i++)nudge(host,0,0);
   if(previous&&previous!=='move')clickTool(host,previous);
  };
 };
 const wireStudio=host=>{
  if(!host||host.dataset.surfaceControls==='1')return;
  host.dataset.surfaceControls='1';
  addPad(host);
  host.querySelectorAll('[data-tool]').forEach(btn=>btn.addEventListener('click',()=>{if(DRAW_TOOLS.has(btn.dataset.tool))ensureLocked(host);},{capture:true}));
  ensureLocked(host);
 };
 const scan=()=>document.querySelectorAll(STUDIO).forEach(wireStudio);
 const observer=new MutationObserver(scan);observer.observe(document.body,{childList:true,subtree:true});
 document.addEventListener('pointerdown',e=>{
  const canvas=e.target?.closest?.(CANVAS);if(!canvas)return;
  const host=canvas.closest(STUDIO);if(DRAW_TOOLS.has(activeTool(host)))ensureLocked(host);
 },true);
 window.ristOpenPortraitArtStudio=()=>{
  const input=document.querySelector('#portrait-art-target input[type="file"]');
  if(input&&window.RistArtStudio?.open){window.RistArtStudio.open(input);requestAnimationFrame(scan);}
 };
 // Card image inputs already receive the generic Paint launcher from art-studio.js.
 // This shared controller ensures portrait and card drawing use the same fixed-canvas navigation behavior.
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',scan,{once:true});else scan();
})();