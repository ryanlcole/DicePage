(()=>{
 'use strict';
 let observer=null,frame=0,lastGrid=null,lastLock=null;
 const studio=()=>document.querySelector('.worldbuilder-studio');
 const authority=()=>window.ristViewerAuthority;
 const railButtons=()=>[...(studio()?.querySelectorAll('.studio-command-rail button')||[])];
 const commandButton=label=>railButtons().find(button=>button.querySelector('strong')?.textContent?.trim()===label)||null;
 const lockButton=()=>railButtons().find(button=>{const strong=button.querySelector('strong')?.textContent?.trim();const small=button.querySelector('small')?.textContent?.trim().toLowerCase()||'';return strong==='Depth View'||strong==='Z-Lock'||strong==='Lock'||strong==='Unlock'||small.includes('viewer locked')||small.includes('viewer unlocked')})||null;
 function wireView(){const button=commandButton('View');if(!button||button.dataset.wbViewerAuthority==='1')return;button.dataset.wbViewerAuthority='1';button.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();event.stopImmediatePropagation();authority()?.toggleGrid?.({source:'view-button'});sync()},{capture:true})}
 function sync(){const root=studio(),api=authority();if(!root||!api)return false;wireView();const state=api.get();const view=commandButton('View');if(view){view.classList.toggle('active',!!state.grid);view.setAttribute('aria-pressed',state.grid?'true':'false');view.setAttribute('aria-label',`Viewer grid ${state.grid?'on':'off'}`)}const lock=lockButton();if(lock){lock.classList.toggle('active',!!state.locked);lock.setAttribute('aria-pressed',state.locked?'true':'false');lock.setAttribute('aria-label',`Viewer ${state.locked?'locked':'unlocked'}. Pinch zoom remains available.`)}lastGrid=!!state.grid;lastLock=!!state.locked;return true}
 function schedule(){if(frame)return;frame=requestAnimationFrame(()=>{frame=0;sync()})}
 function start(){if(!sync())return setTimeout(start,100);observer=new MutationObserver(schedule);observer.observe(studio(),{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['class']});window.addEventListener('rist:viewer-state',schedule);window.addEventListener('pageshow',schedule,{passive:true});document.addEventListener('visibilitychange',()=>{if(document.visibilityState==='visible')schedule()})}
 window.ristWorldBuilderViewControls={sync,state:()=>({grid:lastGrid,locked:lastLock,authority:authority()?.get?.()||null})};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
