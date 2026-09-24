const sessions=new WeakMap();

function clamp(value,min,max){return Math.max(min,Math.min(max,value));}
function num(value,fallback=0){const n=Number(value);return Number.isFinite(n)?n:fallback;}

export function attach(root,dotnet){
  if(!root||sessions.has(root))return;
  const state={dotnet,drag:null};

  const onContext=event=>{
    if(event.target instanceof Element&&event.target.closest('[data-ccd-field],[data-ccd-card]')){
      event.preventDefault();event.stopPropagation();
    }
  };

  const onDragStart=event=>{
    if(event.target instanceof Element&&event.target.closest('[data-ccd-field]')){
      event.preventDefault();event.stopPropagation();
    }
  };

  const onPointerDown=event=>{
    const target=event.target instanceof Element?event.target:null;
    const field=target?.closest('[data-ccd-field]');
    if(!field)return;
    const id=String(field.getAttribute('data-ccd-field')||'');
    if(!id)return;
    event.preventDefault();event.stopPropagation();
    void dotnet.invokeMethodAsync('SelectFieldFromJs',id);

    const card=root.querySelector('[data-ccd-card]');
    const surface=card?.querySelector('.ccd-field-surface');
    if(!surface)return;
    const rect=surface.getBoundingClientRect();
    if(rect.width<=0||rect.height<=0)return;

    const x=num(field.dataset.x,50),y=num(field.dataset.y,50),w=num(field.dataset.w,36),h=num(field.dataset.h,15);
    const handle=target.closest('[data-ccd-resize]');
    const mode=handle?'resize':'move';
    const corner=String(handle?.getAttribute('data-ccd-resize')||'');
    const pointerTarget=handle||field;
    pointerTarget.setPointerCapture?.(event.pointerId);
    state.drag={pointerId:event.pointerId,id,field,pointerTarget,rect,mode,corner,startClientX:event.clientX,startClientY:event.clientY,x,y,w,h};
  };

  const onPointerMove=event=>{
    const drag=state.drag;
    if(!drag||drag.pointerId!==event.pointerId)return;
    event.preventDefault();event.stopPropagation();
    const dx=(event.clientX-drag.startClientX)/drag.rect.width*100;
    const dy=(event.clientY-drag.startClientY)/drag.rect.height*100;
    let x=drag.x,y=drag.y,w=drag.w,h=drag.h;

    if(drag.mode==='move'){
      x=clamp(drag.x+dx,0,100);
      y=clamp(drag.y+dy,0,100);
    }else{
      const left0=drag.x-drag.w/2,right0=drag.x+drag.w/2,top0=drag.y-drag.h/2,bottom0=drag.y+drag.h/2;
      let left=left0,right=right0,top=top0,bottom=bottom0;
      if(drag.corner.includes('w'))left=clamp(left0+dx,0,right-5);
      if(drag.corner.includes('e'))right=clamp(right0+dx,left+5,100);
      if(drag.corner.includes('n'))top=clamp(top0+dy,0,bottom-5);
      if(drag.corner.includes('s'))bottom=clamp(bottom0+dy,top+5,100);
      w=clamp(right-left,5,100);h=clamp(bottom-top,5,100);
      x=clamp((left+right)/2,0,100);y=clamp((top+bottom)/2,0,100);
    }

    Object.assign(drag,{liveX:x,liveY:y,liveW:w,liveH:h});
    drag.field.dataset.x=String(x);drag.field.dataset.y=String(y);drag.field.dataset.w=String(w);drag.field.dataset.h=String(h);
    drag.field.style.left=x+'%';drag.field.style.top=y+'%';drag.field.style.width=w+'%';drag.field.style.height=h+'%';
  };

  const endPointer=event=>{
    const drag=state.drag;
    if(!drag||drag.pointerId!==event.pointerId)return;
    event.preventDefault();event.stopPropagation();
    const x=num(drag.liveX,drag.x),y=num(drag.liveY,drag.y),w=num(drag.liveW,drag.w),h=num(drag.liveH,drag.h);
    if(drag.pointerTarget?.hasPointerCapture?.(event.pointerId))drag.pointerTarget.releasePointerCapture(event.pointerId);
    state.drag=null;
    void dotnet.invokeMethodAsync('CommitFieldTransform',drag.id,x,y,w,h);
  };

  root.addEventListener('contextmenu',onContext,{capture:true});
  root.addEventListener('dragstart',onDragStart,{capture:true});
  root.addEventListener('pointerdown',onPointerDown,{capture:true});
  root.addEventListener('pointermove',onPointerMove,{capture:true});
  root.addEventListener('pointerup',endPointer,{capture:true});
  root.addEventListener('pointercancel',endPointer,{capture:true});
  sessions.set(root,{state,onContext,onDragStart,onPointerDown,onPointerMove,endPointer});
}

export function detach(root){
  const session=sessions.get(root);
  if(!session)return;
  root.removeEventListener('contextmenu',session.onContext,{capture:true});
  root.removeEventListener('dragstart',session.onDragStart,{capture:true});
  root.removeEventListener('pointerdown',session.onPointerDown,{capture:true});
  root.removeEventListener('pointermove',session.onPointerMove,{capture:true});
  root.removeEventListener('pointerup',session.endPointer,{capture:true});
  root.removeEventListener('pointercancel',session.endPointer,{capture:true});
  sessions.delete(root);
}
