// Desktop/laptop controller presentation adapter.
// Mouse owns pointer/cursor behavior. Gamepads provide semantic navigation only.
// If no connected gamepad exposes an analog stick, the on-screen analog is
// represented as a D-pad without changing the X/Y semantic control contract.
(()=>{
  'use strict';
  if(window.ristDesktopControllerAdapter)return;

  const DESKTOP_FINE_POINTER=window.matchMedia?.('(hover: hover) and (pointer: fine)');
  let lastMode='';

  function isDesktop(){return Boolean(DESKTOP_FINE_POINTER?.matches)}
  function pads(){try{return [...(navigator.getGamepads?.()||[])].filter(Boolean).filter(p=>p.connected)}catch{return[]}}
  function hasAnalogStick(){return pads().some(p=>Array.isArray(p.axes)||p.axes ? p.axes.length>=2 : false)}

  function apply(){
    const desktop=isDesktop();
    const analogCapable=desktop&&hasAnalogStick();
    const mode=!desktop?'touch':(analogCapable?'analog':'dpad');
    document.documentElement.dataset.ristDesktopControl=mode;
    document.body?.classList.toggle('rist-desktop-input',desktop);
    document.querySelectorAll('.universal-analog').forEach(node=>{
      node.classList.toggle('hardware-analog',analogCapable);
      node.classList.toggle('hardware-dpad',desktop&&!analogCapable);
      // On desktop/laptop the mouse owns cursor behavior. A controller never
      // enters viewer-cursor mode; its stick/D-pad remains semantic X/Y input.
      if(desktop&&pads().length)node.classList.add('paging-mode');
    });
    if(mode!==lastMode){
      lastMode=mode;
      window.dispatchEvent(new CustomEvent('rist:desktop-controller-mode',{detail:{mode,desktop,analogCapable}}));
    }
  }

  const style=document.createElement('style');
  style.id='rist-desktop-controller-adapter-style';
  style.textContent=`
    html[data-rist-desktop-control="dpad"] .universal-analog .analog-knob{display:none!important}
    html[data-rist-desktop-control="dpad"] .universal-analog .analog-pad{
      border-radius:16%!important;
      background:
        linear-gradient(90deg,transparent 34%,rgba(98,204,255,.28) 34% 66%,transparent 66%),
        linear-gradient(transparent 34%,rgba(98,204,255,.28) 34% 66%,transparent 66%),
        radial-gradient(circle at center,#0d2a40 0 22%,#06131f 23% 100%)!important;
    }
    html[data-rist-desktop-control="dpad"] .universal-analog .analog-pad:after{
      content:"D-PAD";position:absolute;inset:0;display:grid;place-items:center;
      color:#8edbff;font:900 9px/1 system-ui;letter-spacing:.12em;pointer-events:none
    }
    html[data-rist-desktop-control="analog"] .universal-analog .analog-knob{display:block}
    .rist-desktop-input .viewer-reticle{display:none!important}
  `;
  document.head.appendChild(style);

  window.addEventListener('gamepadconnected',apply);
  window.addEventListener('gamepaddisconnected',apply);
  DESKTOP_FINE_POINTER?.addEventListener?.('change',apply);
  new MutationObserver(apply).observe(document.documentElement,{subtree:true,childList:true,attributes:true,attributeFilter:['class']});
  window.setInterval(apply,750);
  apply();

  window.ristDesktopControllerAdapter={refresh:apply,mode:()=>lastMode};
})();
