(()=>{
 const KEY='rist:mmo-mode';
 let mode=localStorage.getItem(KEY)||'local';
 function apply(next,persist=true){
  mode=next==='shaelvien'?'shaelvien':'local';
  if(persist)localStorage.setItem(KEY,mode);
  document.body.classList.toggle('rist-mmo-shaelvien',mode==='shaelvien');
  document.body.classList.toggle('rist-mmo-local',mode==='local');
  const b=document.querySelector('.header-mmo-button');
  if(b){b.classList.toggle('active',mode==='shaelvien');b.setAttribute('aria-pressed',String(mode==='shaelvien'));b.title=mode==='shaelvien'?'Shaelvien MMO — published map locked':'GM local mode — editable personal map';}
  document.dispatchEvent(new CustomEvent('rist:mmo-mode',{detail:{mode}}));
 }
 function toggle(){apply(mode==='shaelvien'?'local':'shaelvien')}
 function guard(e){
  if(mode!=='shaelvien')return;
  if(e.target.closest('.tile-browser,.pallet,.zone-editor,.tile-cell,.piece:not(.pin),.map-lock-button')){e.preventDefault();e.stopImmediatePropagation()}
 }
 document.addEventListener('pointerdown',guard,true);
 window.RistMMO={toggle,setMode:apply,get mode(){return mode}};
 document.addEventListener('DOMContentLoaded',()=>apply(mode,false));
 setTimeout(()=>apply(mode,false),0);
})();