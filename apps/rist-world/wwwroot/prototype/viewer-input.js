(function(root){
  'use strict';
  // Input changes camera representation only. World mutations stay in the host.
  function install({stage,document:doc,pan,zoom,fit,tiers,settings,upload,keyboard,modal}){
    const onKey=event=>{
      if(event.defaultPrevented||event.isComposing)return;
      const panel=modal();
      if(panel){
        if(event.key==='Tab'){
          const controls=Array.from(panel.querySelectorAll('button,input,select,textarea,a[href],[tabindex]'))
            .filter(node=>!node.disabled&&node.tabIndex>=0&&node.getClientRects().length);
          const current=controls.indexOf(doc.activeElement);
          if(controls.length&&(current<0||(event.shiftKey?current===0:current===controls.length-1))){
            event.preventDefault();controls[event.shiftKey?controls.length-1:0].focus();
          }
        }
        return;
      }
      // Native form and button keys belong to that control, never to the camera.
      if(event.target!==stage||doc.activeElement!==stage||event.ctrlKey||event.metaKey||event.altKey)return;
      const step=event.shiftKey?128:32;
      const actions={ArrowLeft:()=>pan(step,0),ArrowRight:()=>pan(-step,0),ArrowUp:()=>pan(0,step),ArrowDown:()=>pan(0,-step),
        '+':()=>zoom(1.22),'=':()=>zoom(1.22),'-':()=>zoom(1/1.22),f:fit,t:tiers,s:settings,u:upload,k:keyboard};
      const action=actions[event.key.length===1?event.key.toLowerCase():event.key];
      if(action){event.preventDefault();action();}
    };
    doc.addEventListener('keydown',onKey);
    return()=>doc.removeEventListener('keydown',onKey);
  }
  function resizeCamera(camera,previous,next){
    if(next.width<=0||next.height<=0)return null;
    if(!previous||previous.width<=0||previous.height<=0)return null;
    const dx=(next.width-previous.width)/2,dy=(next.height-previous.height)/2;
    return{...camera,x:camera.x+dx,y:camera.y+dy,fitX:camera.fitX+dx,fitY:camera.fitY+dy};
  }
  function preserveFocus(container,render,fallback){
    const active=container.ownerDocument.activeElement;
    const key=container.contains(active)?active.getAttribute('data-focus-key'):null;
    render();
    if(key&&!active.isConnected){
      const replacement=Array.from(container.querySelectorAll('[data-focus-key]')).find(node=>node.getAttribute('data-focus-key')===key&&!node.disabled);
      (replacement||fallback)?.focus({preventScroll:true});
    }
  }
  const api=Object.freeze({install,resizeCamera,preserveFocus});
  if(typeof module==='object'&&module.exports)module.exports=api;
  else root.RistViewerInput=api;
})(typeof globalThis==='object'?globalThis:this);
