(function(root){
  'use strict';
  // Input changes camera representation only. World mutations stay in the host.
  function installDesktopZoomBar({stage,document:doc,zoom,fit}){
    const finePointer=root.matchMedia?.('(hover: hover) and (pointer: fine)');
    if(!finePointer)return()=>{};
    let bar=null;
    let range=null;
    let previous=50;

    const ensure=()=>{
      const shouldShow=finePointer.matches;
      if(!shouldShow){bar?.remove();bar=null;range=null;return;}
      if(bar?.isConnected)return;
      bar=doc.createElement('label');
      bar.id='desktopZoomBar';
      bar.className='desktop-zoom-bar';
      bar.setAttribute('data-ui','');
      bar.innerHTML='<span aria-hidden="true">−</span><input id="desktopZoomRange" type="range" min="0" max="100" value="50" step="1" aria-label="Zoom"><span aria-hidden="true">+</span>';
      range=bar.querySelector('input');
      Object.assign(bar.style,{position:'absolute',right:'14px',top:'50%',transform:'translateY(-50%)',zIndex:'40',display:'flex',flexDirection:'column-reverse',alignItems:'center',gap:'6px',padding:'9px 6px',border:'1px solid rgba(215,180,94,.82)',borderRadius:'999px',background:'rgba(3,10,16,.88)',color:'#f6e2a6',font:'900 14px/1 system-ui'});
      Object.assign(range.style,{writingMode:'vertical-lr',direction:'rtl',width:'24px',height:'clamp(130px,30vh,260px)',accentColor:'#62ccff',cursor:'ns-resize'});
      range.addEventListener('input',()=>{
        const next=Number(range.value);
        if(next===previous)return;
        zoom(next>previous?1.08:1/1.08);
        previous=next;
      });
      range.addEventListener('dblclick',()=>{fit();range.value='50';previous=50;});
      stage.appendChild(bar);
    };

    finePointer.addEventListener?.('change',ensure);
    ensure();
    return()=>{finePointer.removeEventListener?.('change',ensure);bar?.remove();};
  }

  function install({stage,document:doc,pan,zoom,fit,tiers,settings,upload,keyboard,modal}){
    const removeZoomBar=installDesktopZoomBar({stage,document:doc,zoom,fit});
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
    return()=>{doc.removeEventListener('keydown',onKey);removeZoomBar();};
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
