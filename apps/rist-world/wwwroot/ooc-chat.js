(()=>{
 'use strict';
 const HISTORY_KEY='rist.ooc.history.v1';
 const CHANNEL_NAME='rist-ooc-local';
 const maxHistory=150;
 let open=false,dragging=false,dragDx=0,dragDy=0,manualPosition=false;
 let history=[];
 try{history=JSON.parse(localStorage.getItem(HISTORY_KEY)||'[]');if(!Array.isArray(history))history=[]}catch{history=[]}
 const channel='BroadcastChannel' in window?new BroadcastChannel(CHANNEL_NAME):null;

 function escapeHtml(value){return String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]))}
 function displayName(){
  const candidates=[
   document.querySelector('.rist-account-profile strong')?.textContent,
   document.querySelector('.footer-character-button strong')?.textContent,
   document.querySelector('#header-slider .header-user-name')?.textContent
  ].map(x=>x?.trim()).filter(Boolean);
  return candidates[0]||'Player';
 }
 function persist(){try{localStorage.setItem(HISTORY_KEY,JSON.stringify(history.slice(-maxHistory)))}catch{}}
 function ensureStyle(){if(document.getElementById('rist-ooc-style'))return;const style=document.createElement('style');style.id='rist-ooc-style';style.textContent=`
.rist .home-inline-chat{grid-template-columns:52px 62px minmax(0,1fr) 92px 72px!important}
.rist-ooc-toggle{height:78px;min-height:78px;width:52px;min-width:52px;padding:0;border:1px solid #725d30;border-left:0;border-radius:0;background:#151b21;color:#e5cf91;font:900 11px/1 system-ui;letter-spacing:.04em;touch-action:manipulation}
.rist-ooc-toggle.active{background:#27303a;color:#fff2bd}
.rist-ooc-window{position:fixed;z-index:1200;box-sizing:border-box;width:min(430px,calc(100vw - 20px));height:min(310px,44vh);min-width:270px;min-height:190px;display:grid;grid-template-rows:34px minmax(0,1fr) 44px;border:1px solid #806a38;border-radius:8px;background:rgba(7,13,18,.91);box-shadow:0 12px 34px rgba(0,0,0,.55);backdrop-filter:blur(4px);overflow:hidden;resize:both}
.rist-ooc-window[hidden]{display:none!important}
.rist-ooc-header{display:flex;align-items:center;gap:8px;padding:0 8px;background:rgba(28,36,43,.96);border-bottom:1px solid #5d4c29;color:#ead79f;cursor:move;user-select:none;touch-action:none}
.rist-ooc-header strong{font:900 11px/1 system-ui;letter-spacing:.08em}
.rist-ooc-header small{margin-left:auto;color:#8f9aa3;font:10px/1 system-ui}
.rist-ooc-header button{width:28px;height:26px;border:0;background:transparent;color:#d9d0bd;font-size:20px;line-height:1;cursor:pointer}
.rist-ooc-log{overflow:auto;padding:8px 10px;scrollbar-width:thin;overscroll-behavior:contain}
.rist-ooc-entry{display:grid;grid-template-columns:auto 1fr;column-gap:6px;margin:0 0 5px;color:#e7e1d3;font:12px/1.25 system-ui}
.rist-ooc-entry time{grid-column:1;color:#78838d;font-size:9px;padding-top:2px}
.rist-ooc-entry .name{grid-column:2;color:#d7be80;font-weight:800}
.rist-ooc-entry .text{grid-column:2;overflow-wrap:anywhere}
.rist-ooc-empty{margin:12px;color:#77818a;font:11px/1.3 system-ui}
.rist-ooc-compose{display:grid;grid-template-columns:minmax(0,1fr) 64px;gap:5px;padding:5px;background:rgba(11,18,24,.97);border-top:1px solid #4f4227}
.rist-ooc-compose input{min-width:0;width:100%;box-sizing:border-box;border:1px solid #3c4751;border-radius:5px;background:#0d151b;color:#f1eee6;padding:7px 9px;font-size:16px;outline:none}
.rist-ooc-compose input:focus{border-color:#9a8043}
.rist-ooc-compose button{border:1px solid #806a38;border-radius:5px;background:#171f26;color:#ead79f;font-weight:800;touch-action:manipulation}
@media(max-width:620px){.rist-ooc-window{width:calc(100vw - 12px);height:min(260px,40vh);resize:none}.rist .home-inline-chat{grid-template-columns:46px 48px minmax(0,1fr) 70px 58px!important}.rist-ooc-toggle{width:46px;min-width:46px}.rist .release-footer-stack .home-inline-chat .chat-history-toggle{width:48px!important;min-width:48px!important}.rist .release-footer-stack .dice-tray-toggle{width:58px!important;min-width:58px!important}.rist .release-footer-stack .home-inline-chat .home-chat-send{font-size:12px!important}}
`;document.head.appendChild(style)}
 function ensure(){
  ensureStyle();
  let toggle=document.querySelector('.rist-ooc-toggle');
  const chat=document.querySelector('.home-inline-chat');
  if(chat&&!toggle){toggle=document.createElement('button');toggle.type='button';toggle.className='rist-ooc-toggle';toggle.textContent='OOC';toggle.title='Out-of-character chat';toggle.setAttribute('aria-label','Open out-of-character chat');toggle.addEventListener('click',()=>setOpen(!open));chat.prepend(toggle)}
  let win=document.querySelector('.rist-ooc-window');
  if(!win){
   win=document.createElement('section');win.className='rist-ooc-window';win.hidden=true;win.setAttribute('role','dialog');win.setAttribute('aria-label','Out-of-character chat');
   win.innerHTML='<header class="rist-ooc-header"><strong>OOC CHAT</strong><small>Not perception filtered</small><button type="button" aria-label="Close OOC chat">×</button></header><div class="rist-ooc-log" aria-live="polite"></div><form class="rist-ooc-compose"><input type="text" maxlength="500" autocomplete="off" placeholder="Out of character…" aria-label="Out-of-character message"><button type="submit">Send</button></form>';
   document.body.appendChild(win);
   win.querySelector('.rist-ooc-header button').addEventListener('click',()=>setOpen(false));
   win.querySelector('form').addEventListener('submit',e=>{e.preventDefault();send()});
   const header=win.querySelector('.rist-ooc-header');
   header.addEventListener('pointerdown',e=>{if(e.target.closest('button'))return;const r=win.getBoundingClientRect();dragging=true;manualPosition=true;dragDx=e.clientX-r.left;dragDy=e.clientY-r.top;try{header.setPointerCapture(e.pointerId)}catch{}});
   header.addEventListener('pointermove',e=>{if(!dragging)return;const left=Math.max(4,Math.min(innerWidth-win.offsetWidth-4,e.clientX-dragDx));const top=Math.max(4,Math.min(innerHeight-win.offsetHeight-4,e.clientY-dragDy));win.style.left=left+'px';win.style.top=top+'px';win.style.bottom='auto'});
   const stop=e=>{if(!dragging)return;dragging=false;try{header.releasePointerCapture(e.pointerId)}catch{}};header.addEventListener('pointerup',stop);header.addEventListener('pointercancel',stop);
  }
  return {toggle,win};
 }
 function place(win){if(manualPosition)return;const map=document.querySelector('.map-shell,.map');const r=map?.getBoundingClientRect();const footer=document.querySelector('.release-footer-region')?.getBoundingClientRect();const margin=10;if(r){win.style.left=Math.max(margin,r.left+margin)+'px';const bottom=footer?Math.max(margin,innerHeight-footer.top+margin):margin;win.style.bottom=bottom+'px';win.style.top='auto'}else{win.style.left=margin+'px';win.style.bottom='200px';win.style.top='auto'}}
 function render(){const {win}=ensure();const log=win.querySelector('.rist-ooc-log');if(!history.length){log.innerHTML='<p class="rist-ooc-empty">OOC messages appear here. This channel is outside character perception.</p>';return}log.innerHTML=history.slice(-maxHistory).map(m=>`<article class="rist-ooc-entry"><time>${escapeHtml(new Date(m.time).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'}))}</time><span class="name">${escapeHtml(m.name)}</span><span class="text">${escapeHtml(m.text)}</span></article>`).join('');log.scrollTop=log.scrollHeight}
 function setOpen(value){open=!!value;const {toggle,win}=ensure();win.hidden=!open;toggle?.classList.toggle('active',open);toggle?.setAttribute('aria-expanded',String(open));if(open){place(win);render();setTimeout(()=>win.querySelector('input')?.focus(),0)}}
 function receive(message,remote=false){if(!message||typeof message.text!=='string'||!message.text.trim())return;const normalized={id:String(message.id||crypto.randomUUID?.()||Date.now()),name:String(message.name||'Player').slice(0,80),text:message.text.trim().slice(0,500),time:Number(message.time)||Date.now()};if(history.some(x=>x.id===normalized.id))return;history.push(normalized);history=history.slice(-maxHistory);persist();render();if(!remote)channel?.postMessage(normalized);document.dispatchEvent(new CustomEvent('rist:ooc-received',{detail:normalized}))}
 function send(){const {win}=ensure();const input=win.querySelector('input');const text=input.value.trim();if(!text)return;const message={id:crypto.randomUUID?.()||String(Date.now())+Math.random(),name:displayName(),text,time:Date.now()};input.value='';receive(message,false);document.dispatchEvent(new CustomEvent('rist:ooc-send',{detail:message}))}
 channel?.addEventListener('message',e=>receive(e.data,true));
 document.addEventListener('keydown',e=>{if(e.key==='Escape'&&open){setOpen(false);e.stopPropagation()}else if(e.key==='Enter'&&!open&&!e.ctrlKey&&!e.metaKey&&!e.altKey&&document.activeElement===document.body){setOpen(true);e.preventDefault()}});
 addEventListener('resize',()=>{if(open){manualPosition=false;place(ensure().win)}},{passive:true});
 const observer=new MutationObserver(()=>ensure());
 function start(){ensure();render();observer.observe(document.body,{childList:true,subtree:true})}
 window.RistOocChat={open:()=>setOpen(true),close:()=>setOpen(false),toggle:()=>setOpen(!open),receive,state:()=>({open,history:[...history]})};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
