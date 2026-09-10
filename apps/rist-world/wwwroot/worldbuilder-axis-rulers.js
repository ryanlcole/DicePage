export function attachAxisRulers(element){
 const studio=element?.closest?.('.worldbuilder-studio');
 if(!studio)return{dispose(){}};
 let active=null,suppressClick=false,zStepsSent=0;
 const canvas=()=>studio.querySelector('.studio-viewer-canvas');
 const nav=()=>window.ristViewerNavigation;
 const locked=()=>studio.classList.contains('viewer-locked');
 const existingZ=()=>canvas()?.querySelector('.wb-z-ruler');
 const sceneZ=()=>{const legacy=existingZ()?.querySelector('.wb-z-ruler-current');const top=parseFloat(legacy?.style?.top||'50');return Number.isFinite(top)?Math.round(50-top):0;};
 const make=(axis,label)=>{
  let r=axis==='z'?existingZ():canvas()?.querySelector(`.wb-${axis}-ruler`);
  if(!r){r=document.createElement('button');r.type='button';canvas()?.appendChild(r);}
  r.classList.add('wb-axis-ruler',`wb-${axis}-ruler`);r.dataset.axis=axis;r.setAttribute('aria-label',`${label} axis ruler`);
  if(!r.querySelector('.wb-axis-ticks')){const ticks=document.createElement('span');ticks.className='wb-axis-ticks';r.appendChild(ticks);}
  if(!r.querySelector('.wb-axis-marker')){const marker=document.createElement('span');marker.className='wb-axis-marker';r.appendChild(marker);}
  if(!r.querySelector('.wb-axis-label')){const text=document.createElement('span');text.className='wb-axis-label';r.appendChild(text);}
  return r;
 };
 const xr=make('x','X'),yr=make('y','Y'),zr=make('z','Z');
 const render=()=>{
  const state=nav()?.get?.()||{panX:0,panY:0};const z=sceneZ();
  studio.style.setProperty('--wb-axis-x-shift',`${Number(state.panX)||0}px`);studio.style.setProperty('--wb-axis-y-shift',`${Number(state.panY)||0}px`);studio.style.setProperty('--wb-axis-z-shift',`${z*-10}px`);
  const tier=Math.max(0,Math.floor(z/10)),layer=z-(tier*10);const zl=zr?.querySelector('.wb-axis-label');if(zl)zl.textContent=`Tier ${tier} · Layer ${layer}`;
  const xl=xr?.querySelector('.wb-axis-label');if(xl)xl.textContent='X';const yl=yr?.querySelector('.wb-axis-label');if(yl)yl.textContent='Y';
 };
 const down=e=>{const r=e.target.closest?.('.wb-axis-ruler');if(!r||locked())return;active={id:e.pointerId,axis:r.dataset.axis,startX:e.clientX,startY:e.clientY,startNav:nav()?.get?.()||{panX:0,panY:0},moved:false};zStepsSent=0;r.setPointerCapture?.(e.pointerId);e.preventDefault();e.stopPropagation();};
 const move=e=>{if(!active||e.pointerId!==active.id||locked())return;const dx=e.clientX-active.startX,dy=e.clientY-active.startY;if(Math.abs(dx)+Math.abs(dy)>5)active.moved=true;if(active.axis==='x')nav()?.setPan?.(active.startNav.panX+dx,active.startNav.panY,true);else if(active.axis==='y')nav()?.setPan?.(active.startNav.panX,active.startNav.panY+dy,true);else if(active.axis==='z'){const rect=zr.getBoundingClientRect(),tick=Math.max(8,rect.height/50),steps=Math.round(-dy/tick),delta=steps-zStepsSent;if(delta){zStepsSent=steps;for(let i=0;i<Math.abs(delta);i++)element.dispatchEvent(new WheelEvent('wheel',{deltaY:Math.sign(delta)*-340,bubbles:true,cancelable:true}));}}render();e.preventDefault();e.stopPropagation();};
 const finish=e=>{if(!active||e.pointerId!==active.id)return;suppressClick=active.moved;active=null;setTimeout(()=>suppressClick=false,120);e.preventDefault();e.stopPropagation();};
 const guardClick=e=>{if(!suppressClick)return;e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();};
 for(const r of [xr,yr,zr])r?.addEventListener('pointerdown',down,{passive:false});
 document.addEventListener('pointermove',move,{capture:true,passive:false});document.addEventListener('pointerup',finish,{capture:true,passive:false});document.addEventListener('pointercancel',finish,{capture:true,passive:false});zr?.addEventListener('click',guardClick,true);
 window.addEventListener('rist:viewer-pan',render);const observer=new MutationObserver(render);observer.observe(studio,{attributes:true,subtree:true,attributeFilter:['class','style']});render();
 return{dispose(){observer.disconnect();document.removeEventListener('pointermove',move,true);document.removeEventListener('pointerup',finish,true);document.removeEventListener('pointercancel',finish,true);window.removeEventListener('rist:viewer-pan',render);xr?.remove();yr?.remove();zr?.querySelectorAll('.wb-axis-ticks,.wb-axis-marker,.wb-axis-label').forEach(x=>x.remove());}};
}
