export function attachAxisRulers(element){
 const studio=element?.closest?.('.worldbuilder-studio');
 if(!studio)return{dispose(){}};
 let active=null,suppressClick=false;
 const zPointers=new Map();
 let zPinchDistance=0;
 const canvas=()=>studio.querySelector('.studio-viewer-canvas');
 const nav=()=>window.ristViewerNavigation;
 const locked=()=>studio.classList.contains('viewer-locked');
 const existingZ=()=>canvas()?.querySelector('.wb-z-ruler');
 const sceneZ=()=>{const legacy=existingZ()?.querySelector('.wb-z-ruler-current');const top=parseFloat(legacy?.style?.top||'50');return Number.isFinite(top)?Math.round(50-top):0;};
 const cellSize=()=>{const s=studio.querySelector('.world-stage'),r=s?.getBoundingClientRect();return r&&r.width>0&&r.height>0?[r.width/30,r.height/30]:[1,1];};
 const make=(axis,label)=>{
  let r=axis==='z'?existingZ():canvas()?.querySelector(`.wb-${axis}-ruler`);
  if(!r){r=document.createElement('button');r.type='button';canvas()?.appendChild(r);}
  r.classList.add('wb-axis-ruler',`wb-${axis}-ruler`);r.dataset.axis=axis;r.setAttribute('aria-label',`${label} axis ruler`);
  if(!r.querySelector('.wb-axis-ticks')){const ticks=document.createElement('span');ticks.className='wb-axis-ticks';r.appendChild(ticks);}
  if(!r.querySelector('.wb-axis-marker')){const marker=document.createElement('span');marker.className='wb-axis-marker';r.appendChild(marker);}
  if(!r.querySelector('.wb-axis-label')){const text=document.createElement('span');text.className='wb-axis-label';r.appendChild(text);}
  return r;
 };
 const xr=make('x','X'),yr=make('y','Y'),zr=make('z','Z / Layer');
 const render=()=>{
  const state=nav()?.get?.()||{x:0,y:0,panX:0,panY:0};const z=sceneZ();
  studio.style.setProperty('--wb-axis-x-shift',`${Number(state.panX)||0}px`);studio.style.setProperty('--wb-axis-y-shift',`${Number(state.panY)||0}px`);studio.style.setProperty('--wb-axis-z-shift',`${z*-10}px`);
  const tier=Math.max(0,Math.floor(z/10)),layer=z-(tier*10);const zl=zr?.querySelector('.wb-axis-label');if(zl)zl.textContent=`Z ${z} · T${tier} L${layer}`;
  const xl=xr?.querySelector('.wb-axis-label');if(xl)xl.textContent=`X ${Math.round(Number(state.x)||0)}`;
  const yl=yr?.querySelector('.wb-axis-label');if(yl)yl.textContent=`Y ${Math.round(Number(state.y)||0)}`;
 };
 const zDistance=()=>{const v=[...zPointers.values()];if(v.length<2)return 0;return Math.hypot(v[0].x-v[1].x,v[0].y-v[1].y);};
 const sendZPinch=ratio=>{if(!Number.isFinite(ratio)||Math.abs(ratio-1)<.012)return;const deltaY=ratio>1?-340:340;element.dispatchEvent(new WheelEvent('wheel',{deltaY,bubbles:true,cancelable:true}));};
 const down=e=>{
  const r=e.target.closest?.('.wb-axis-ruler');if(!r||locked())return;
  const axis=r.dataset.axis;
  if(axis==='z'){
   zPointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
   if(zPointers.size===2)zPinchDistance=zDistance();
   r.setPointerCapture?.(e.pointerId);e.preventDefault();e.stopPropagation();return;
  }
  const state=nav()?.get?.()||{x:0,y:0};
  active={id:e.pointerId,axis,startX:e.clientX,startY:e.clientY,startViewX:Number(state.x)||0,startViewY:Number(state.y)||0,moved:false};
  r.setPointerCapture?.(e.pointerId);e.preventDefault();e.stopPropagation();
 };
 const move=e=>{
  if(locked())return;
  if(zPointers.has(e.pointerId)){
   zPointers.set(e.pointerId,{x:e.clientX,y:e.clientY});
   if(zPointers.size===2){const next=zDistance();if(zPinchDistance){const ratio=next/zPinchDistance;if(Math.abs(ratio-1)>.012){sendZPinch(ratio);zPinchDistance=next;}}else zPinchDistance=next;}
   render();e.preventDefault();e.stopPropagation();return;
  }
  if(!active||e.pointerId!==active.id)return;
  const dx=e.clientX-active.startX,dy=e.clientY-active.startY;if(Math.abs(dx)+Math.abs(dy)>5)active.moved=true;
  const [cw,ch]=cellSize();
  if(active.axis==='x')nav()?.setPosition?.(active.startViewX+Math.round(dx/Math.max(cw,1)),active.startViewY);
  else if(active.axis==='y')nav()?.setPosition?.(active.startViewX,active.startViewY+Math.round(dy/Math.max(ch,1)));
  render();e.preventDefault();e.stopPropagation();
 };
 const finish=e=>{
  if(zPointers.has(e.pointerId)){zPointers.delete(e.pointerId);if(zPointers.size<2)zPinchDistance=0;e.preventDefault();e.stopPropagation();return;}
  if(!active||e.pointerId!==active.id)return;suppressClick=active.moved;active=null;setTimeout(()=>suppressClick=false,120);e.preventDefault();e.stopPropagation();
 };
 const guardClick=e=>{if(!suppressClick)return;e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();};
 for(const r of [xr,yr,zr])r?.addEventListener('pointerdown',down,{passive:false});
 document.addEventListener('pointermove',move,{capture:true,passive:false});document.addEventListener('pointerup',finish,{capture:true,passive:false});document.addEventListener('pointercancel',finish,{capture:true,passive:false});zr?.addEventListener('click',guardClick,true);
 window.addEventListener('rist:viewer-pan',render);const observer=new MutationObserver(render);observer.observe(studio,{attributes:true,subtree:true,attributeFilter:['class','style']});render();
 return{dispose(){observer.disconnect();document.removeEventListener('pointermove',move,true);document.removeEventListener('pointerup',finish,true);document.removeEventListener('pointercancel',finish,true);window.removeEventListener('rist:viewer-pan',render);xr?.remove();yr?.remove();zr?.querySelectorAll('.wb-axis-ticks,.wb-axis-marker,.wb-axis-label').forEach(x=>x.remove());}};
}
