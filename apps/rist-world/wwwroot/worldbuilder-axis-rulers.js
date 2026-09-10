export function attachAxisRulers(element,dotnet){
 const studio=element?.closest?.('.worldbuilder-studio');
 if(!studio)return{dispose(){}};
 let disposed=false,depth={sceneZ:0,tierIndex:0,layerOffset:0,viewerLocked:true};
 let active=null,suppressClick=false;

 const canvas=()=>studio.querySelector('.studio-viewer-canvas');
 const getNav=()=>window.ristViewerNavigation;
 const locked=()=>!!(depth.viewerLocked??depth.ViewerLocked);
 const sceneZ=()=>Number(depth.sceneZ??depth.SceneZ??0);
 const tier=()=>Number(depth.tierIndex??depth.TierIndex??0);
 const layer=()=>Number(depth.layerOffset??depth.LayerOffset??0);
 const refreshDepth=async()=>{try{depth=await dotnet.invokeMethodAsync('GetWorldBuilderDepthState');}catch{};render();};
 const make=(axis,label)=>{
  let r=canvas()?.querySelector(`.wb-${axis}-ruler`);if(r)return r;
  r=document.createElement('button');r.type='button';r.className=`wb-axis-ruler wb-${axis}-ruler`;r.dataset.axis=axis;r.setAttribute('aria-label',`${label} axis ruler`);
  const ticks=document.createElement('span');ticks.className='wb-axis-ticks';r.appendChild(ticks);
  const marker=document.createElement('span');marker.className='wb-axis-marker';r.appendChild(marker);
  const text=document.createElement('span');text.className='wb-axis-label';r.appendChild(text);
  canvas()?.appendChild(r);return r;
 };
 const xr=make('x','X'),yr=make('y','Y'),zr=make('z','Z');

 const render=()=>{
  const nav=getNav()?.get?.()||{panX:0,panY:0};
  studio.style.setProperty('--wb-axis-x-shift',`${Number(nav.panX)||0}px`);
  studio.style.setProperty('--wb-axis-y-shift',`${Number(nav.panY)||0}px`);
  studio.style.setProperty('--wb-axis-z-shift',`${sceneZ()*-10}px`);
  const zl=zr?.querySelector('.wb-axis-label');if(zl)zl.textContent=`Tier ${tier()} · Layer ${layer()}`;
  const xl=xr?.querySelector('.wb-axis-label');if(xl)xl.textContent='X';
  const yl=yr?.querySelector('.wb-axis-label');if(yl)yl.textContent='Y';
  studio.classList.toggle('viewer-locked',locked());
 };
 const openZMenu=(clientY)=>{
  const rect=zr.getBoundingClientRect();const t=Math.max(0,Math.min(1,(clientY-rect.top)/rect.height));const approx=Math.round(sceneZ()+((.5-t)*50));
  studio.querySelectorAll('.wb-modal').forEach(x=>x.remove());
  const host=document.createElement('section');host.className='wb-modal';host.setAttribute('role','dialog');host.setAttribute('aria-modal','true');
  const h=document.createElement('header');const title=document.createElement('strong');title.textContent='Z Location';const x=document.createElement('button');x.type='button';x.textContent='×';x.onclick=()=>host.remove();h.append(title,x);host.append(h);
  const label=document.createElement('label');label.append(document.createTextNode('Approximate Z'));const input=document.createElement('input');input.type='number';input.step='1';input.value=String(approx);label.append(input);host.append(label);
  const button=(txt,fn)=>{const b=document.createElement('button');b.type='button';b.textContent=txt;b.onclick=fn;return b;};
  host.append(button('Add Tier',async()=>{try{depth=await dotnet.invokeMethodAsync('AddTierAtSceneZFromJs',Math.round(Number(input.value)||0));}catch{}host.remove();render();}),button('Add Layer',async()=>{try{depth=await dotnet.invokeMethodAsync('AddLayerAtSceneZFromJs',Math.round(Number(input.value)||0));}catch{}host.remove();render();}),button('Cancel',()=>host.remove()));
  canvas()?.appendChild(host);
 };
 const down=e=>{
  const r=e.target.closest?.('.wb-axis-ruler');if(!r||locked())return;
  active={id:e.pointerId,axis:r.dataset.axis,startX:e.clientX,startY:e.clientY,startNav:getNav()?.get?.()||{panX:0,panY:0},startZ:sceneZ(),moved:false};
  r.setPointerCapture?.(e.pointerId);e.preventDefault();e.stopPropagation();
 };
 const move=e=>{
  if(!active||e.pointerId!==active.id||locked())return;
  const dx=e.clientX-active.startX,dy=e.clientY-active.startY;if(Math.abs(dx)+Math.abs(dy)>5)active.moved=true;
  if(active.axis==='x')getNav()?.setPan?.(active.startNav.panX+dx,active.startNav.panY,true);
  else if(active.axis==='y')getNav()?.setPan?.(active.startNav.panX,active.startNav.panY+dy,true);
  else if(active.axis==='z'){
   const rect=zr.getBoundingClientRect();const tick=Math.max(8,rect.height/50);const steps=Math.round(-dy/tick);const target=active.startZ+steps;
   if(target!==sceneZ())dotnet.invokeMethodAsync('SetViewerSceneZFromJs',target).then(v=>{depth=v;render();}).catch(()=>{});
  }
  render();e.preventDefault();e.stopPropagation();
 };
 const finish=e=>{if(!active||e.pointerId!==active.id)return;suppressClick=active.moved;active=null;setTimeout(()=>suppressClick=false,80);e.preventDefault();e.stopPropagation();};
 const click=e=>{const r=e.target.closest?.('.wb-axis-ruler');if(!r)return;if(suppressClick){e.preventDefault();e.stopPropagation();return;}if(r.dataset.axis==='z')openZMenu(e.clientY);};
 xr?.addEventListener('pointerdown',down);yr?.addEventListener('pointerdown',down);zr?.addEventListener('pointerdown',down);
 document.addEventListener('pointermove',move,{capture:true,passive:false});document.addEventListener('pointerup',finish,{capture:true,passive:false});document.addEventListener('pointercancel',finish,{capture:true,passive:false});
 xr?.addEventListener('click',click);yr?.addEventListener('click',click);zr?.addEventListener('click',click);
 window.addEventListener('rist:viewer-pan',render);
 refreshDepth();
 return{refresh:refreshDepth,dispose(){disposed=true;document.removeEventListener('pointermove',move,true);document.removeEventListener('pointerup',finish,true);document.removeEventListener('pointercancel',finish,true);window.removeEventListener('rist:viewer-pan',render);xr?.remove();yr?.remove();zr?.remove();}};
}
