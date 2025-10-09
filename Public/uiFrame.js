let visible=false;
export function initUIFrame(){}
export function setDebugVisible(v){
  visible=!!v; const el=document.getElementById('dbg'); el.style.display=visible?'block':'none';
}

