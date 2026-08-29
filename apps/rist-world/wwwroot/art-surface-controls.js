(()=>{
 'use strict';
 const STUDIO='.rist-art-studio',CANVAS='.rist-art-studio>main>canvas',DRAW_TOOLS=new Set(['pen','paint','fill','erase']);
 const activeTool=host=>host?.querySelector('[data-tool].active')?.dataset.tool||'select';
 const ensureLocked=host=>{const palette=host?.querySelector('.rist-art-palette'),lock=host?.querySelector('.rist-palette-lock');if(palette&&lock&&!palette.classList.contains('locked'))lock.click()};
 function addPad(host){
  if(!host||host.querySelector('.rist-art-nav-pad'))return;
  const pad=document.createElement('div');pad.className='rist-art-nav-pad';pad.setAttribute('role','group');pad.setAttribute('aria-label','Artwork view controls');
  pad.innerHTML='<button type="button" data-pan="up" aria-label="Move view up">▲</button><button type="button" data-pan="left" aria-label="Move view left">◀</button><button type="button" data-pan="center" aria-label="Center view">●</button><button type="button" data-pan="right" aria-label="Move view right">▶</button><button type="button" data-pan="down" aria-label="Move view down">▼</button>';
  host.appendChild(pad);
  pad.querySelector('[data-pan="up"]').onclick=()=>window.RistArtStudio?.panBy?.(0,54);
  pad.querySelector('[data-pan="down"]').onclick=()=>window.RistArtStudio?.panBy?.(0,-54);
  pad.querySelector('[data-pan="left"]').onclick=()=>window.RistArtStudio?.panBy?.(54,0);
  pad.querySelector('[data-pan="right"]').onclick=()=>window.RistArtStudio?.panBy?.(-54,0);
  pad.querySelector('[data-pan="center"]').onclick=()=>window.RistArtStudio?.centerView?.();
 }
 function wireStudio(host){if(!host||host.dataset.surfaceControls==='2')return;host.dataset.surfaceControls='2';addPad(host);host.querySelectorAll('[data-tool]').forEach(button=>button.addEventListener('click',()=>{if(DRAW_TOOLS.has(button.dataset.tool))ensureLocked(host)},{capture:true}));ensureLocked(host)}
 const scan=()=>document.querySelectorAll(STUDIO).forEach(wireStudio);
 document.addEventListener('pointerdown',e=>{const target=e.target instanceof Element?e.target:null,canvas=target?.closest(CANVAS);if(!canvas)return;const host=canvas.closest(STUDIO);if(DRAW_TOOLS.has(activeTool(host)))ensureLocked(host)},true);
 window.ristOpenPortraitArtStudio=()=>{const input=document.querySelector('#portrait-art-target input[type="file"]');if(input&&window.RistArtStudio?.open){window.RistArtStudio.open(input);requestAnimationFrame(scan)}};
 document.addEventListener('rist:dom-change',scan);scan();
})();
