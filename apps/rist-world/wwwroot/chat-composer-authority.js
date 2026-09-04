(()=>{
 'use strict';
 const MODES=[
  ['/s','says…','Normal speaking range'],
  ['/e','exclaims…','Raised or emphatic speaking range'],
  ['/q','quietly says…','Low voice / short range'],
  ['/w','whispers…','Very close, quiet range'],
  ['/h','hails…','Moderate-distance calling range'],
  ['/y','yells…','Long audible range'],
  ['/b','bellows…','Maximum natural voice range'],
  ['/c','clarion calls…','Very long battlefield-style audible range'],
  ['/a','announces…','Broad local-area announcement'],
  ['/sng','sings…','Audible singing range'],
  ['/sgn','signs…','Visual / line-of-sight communication'],
  ['/g','signals…','Visible signal / line-of-sight range'],
  ['/m','magically messages…','Magical range set by the effect'],
  ['/t','telepathically messages…','Telepathic range set by the effect'],
  ['/r','radios…','Device-defined communication range'],
  ['/p','projects…','Amplified or supernatural voice range']
 ];
 let mode='/s',queued=false,activeMenu=null,activeButton=null;
 const q=(s,r=document)=>r?.querySelector?.(s)||null;
 function setLiveValue(line){
  const live=q('.home-chat-compose textarea');
  if(!live)return;
  const clean=line||'';
  const value=clean.trim()?`${mode} ${clean}`:clean;
  const setter=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value')?.set;
  setter?.call(live,value);
  live.dispatchEvent(new Event('input',{bubbles:true}));
 }
 function positionMenu(menu,button){
  if(!menu||!button)return;
  const r=button.getBoundingClientRect();
  const width=Math.min(310,Math.max(220,window.innerWidth-20));
  const left=Math.max(8,Math.min(window.innerWidth-width-8,r.left));
  const maxHeight=Math.max(160,Math.min(window.innerHeight*.62,r.top-16));
  menu.style.setProperty('width',`${width}px`,'important');
  menu.style.setProperty('left',`${left}px`,'important');
  menu.style.setProperty('right','auto','important');
  menu.style.setProperty('bottom','auto','important');
  menu.style.setProperty('top','8px','important');
  menu.style.setProperty('max-height',`${maxHeight}px`,'important');
 }
 function closeMenu(){
  if(activeMenu){activeMenu.classList.remove('open');activeMenu.remove();activeMenu=null;}
  if(activeButton){activeButton.setAttribute('aria-expanded','false');activeButton=null;}
 }
 function buildModeDropdown(){
  const root=document.createElement('div');root.className='rist-rp-mode-dropdown';
  const button=document.createElement('button');button.type='button';button.className='rist-rp-mode-button';button.textContent=mode;button.setAttribute('aria-haspopup','listbox');button.setAttribute('aria-expanded','false');button.setAttribute('aria-label','Roleplay communication mode');
  function openMenu(){
   closeMenu();
   const menu=document.createElement('div');menu.className='rist-rp-mode-menu rist-rp-mode-menu-portal open';menu.setAttribute('role','listbox');
   for(const [code,label,range] of MODES){
    const option=document.createElement('button');option.type='button';option.className='rist-rp-mode-option';option.setAttribute('role','option');option.dataset.code=code;option.innerHTML=`<strong>${code}</strong><span>${label}</span><small>${range}</small>`;
    option.addEventListener('click',()=>{mode=code;button.textContent=mode;const input=q('.rist-chat-line-input');if(input)setLiveValue(input.value);closeMenu();});
    menu.appendChild(option);
   }
   document.body.appendChild(menu);activeMenu=menu;activeButton=button;button.setAttribute('aria-expanded','true');positionMenu(menu,button);
  }
  button.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();if(activeButton===button)closeMenu();else openMenu();});
  root.append(button);return root;
 }
 function enhance(){
  const wrap=q('.rist-themed-chat-input');if(!wrap||wrap.dataset.ristComposer==='1')return;
  const source=q('.home-chat-compose textarea');
  let prior=source?.value||q('textarea',wrap)?.value||'';
  const found=MODES.find(([code])=>prior===code||prior.startsWith(code+' '));
  if(found){mode=found[0];prior=prior.slice(mode.length).trimStart();}
  wrap.dataset.ristComposer='1';wrap.replaceChildren();
  const modeDrop=buildModeDropdown();
  const input=document.createElement('textarea');input.className='rist-chat-line-input';input.maxLength=1200;input.placeholder='character line…';input.value=prior;input.setAttribute('aria-label','Character line');input.addEventListener('input',()=>setLiveValue(input.value));
  const send=document.createElement('button');send.type='button';send.className='rist-chat-send';send.textContent='Send';send.addEventListener('click',()=>{setLiveValue(input.value);requestAnimationFrame(()=>{q('.home-chat-send')?.click();setTimeout(()=>{input.value='';setLiveValue('');},0);});});
  const tools=document.createElement('div');tools.className='rist-chat-tool-stack';
  const log=document.createElement('button');log.type='button';log.className='rist-chat-icon-button';log.innerHTML='<span aria-hidden="true">▤</span>';log.title='Chat log';log.setAttribute('aria-label','Chat log');log.addEventListener('click',()=>window.RistChatScripts?.open?.());
  const settings=document.createElement('button');settings.type='button';settings.className='rist-chat-icon-button';settings.innerHTML='<span aria-hidden="true">⚙</span>';settings.title='Chat settings';settings.setAttribute('aria-label','Chat settings');settings.addEventListener('click',()=>window.RistStartMenu?.open?.());
  tools.append(log,settings);wrap.append(modeDrop,input,send,tools);setLiveValue(input.value);
 }
 function queue(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;enhance()})}
 document.addEventListener('click',e=>{if(!e.target.closest('.rist-rp-mode-button')&&!e.target.closest('.rist-rp-mode-menu-portal'))closeMenu();},true);
 window.addEventListener('resize',()=>{if(activeMenu&&activeButton)positionMenu(activeMenu,activeButton)},{passive:true});
 window.addEventListener('orientationchange',()=>setTimeout(()=>{if(activeMenu&&activeButton)positionMenu(activeMenu,activeButton)},120),{passive:true});
 new MutationObserver(queue).observe(document.documentElement,{childList:true,subtree:true});
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',queue,{once:true});else queue();
})();