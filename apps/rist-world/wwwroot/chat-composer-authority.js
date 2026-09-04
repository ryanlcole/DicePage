(()=>{
 'use strict';
 const MODES=[
  ['/s','says…','Normal speaking range'],
  ['/e','exclaims…','Emphatic speaking range'],
  ['/w','whispers…','Very close, quiet range'],
  ['/y','yells…','Long audible range'],
  ['/c','clarion calls…','Very long battlefield-style call'],
  ['/a','announces…','Broad area announcement'],
  ['/g','signals…','Visible / line-of-sight communication'],
  ['/m','magically messages…','Magical ranged communication'],
  ['/t','telepathically messages…','Telepathic communication']
 ];
 let mode='/s',queued=false;
 const q=(s,r=document)=>r?.querySelector?.(s)||null;
 function setLiveValue(line){
  const live=q('.home-chat-compose textarea');
  if(!live)return;
  const value=line.trim()?`${mode} ${line}`:line;
  const setter=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value')?.set;
  setter?.call(live,value);
  live.dispatchEvent(new Event('input',{bubbles:true}));
 }
 function closeMenus(except){document.querySelectorAll('.rist-rp-mode-menu.open').forEach(m=>{if(m!==except)m.classList.remove('open')});}
 function buildModeDropdown(){
  const root=document.createElement('div');root.className='rist-rp-mode-dropdown';
  const button=document.createElement('button');button.type='button';button.className='rist-rp-mode-button';button.textContent=mode;button.setAttribute('aria-haspopup','listbox');button.setAttribute('aria-expanded','false');button.setAttribute('aria-label','Roleplay communication mode');
  const menu=document.createElement('div');menu.className='rist-rp-mode-menu';menu.setAttribute('role','listbox');
  for(const [code,label,range] of MODES){
   const option=document.createElement('button');option.type='button';option.className='rist-rp-mode-option';option.setAttribute('role','option');option.dataset.code=code;option.innerHTML=`<strong>${code}</strong><span>${label}</span><small>${range}</small>`;
   option.addEventListener('click',()=>{mode=code;button.textContent=mode;button.setAttribute('aria-expanded','false');menu.classList.remove('open');const input=q('.rist-chat-line-input');if(input)setLiveValue(input.value);});
   menu.appendChild(option);
  }
  button.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();const open=!menu.classList.contains('open');closeMenus(menu);menu.classList.toggle('open',open);button.setAttribute('aria-expanded',open?'true':'false');});
  root.append(button,menu);return root;
 }
 function enhance(){
  const wrap=q('.rist-themed-chat-input');if(!wrap||wrap.dataset.ristComposer==='1')return;
  const prior=q('textarea',wrap)?.value||'';
  wrap.dataset.ristComposer='1';wrap.replaceChildren();
  const modeDrop=buildModeDropdown();
  const input=document.createElement('textarea');input.className='rist-chat-line-input';input.maxLength=1200;input.placeholder='character line…';input.value=prior.replace(/^\/[a-z]\s+/i,'');input.setAttribute('aria-label','Character line');input.addEventListener('input',()=>setLiveValue(input.value));
  const send=document.createElement('button');send.type='button';send.className='rist-chat-send';send.textContent='Send';send.addEventListener('click',()=>{setLiveValue(input.value);requestAnimationFrame(()=>q('.home-chat-send')?.click())});
  const tools=document.createElement('div');tools.className='rist-chat-tool-stack';
  const log=document.createElement('button');log.type='button';log.className='rist-chat-icon-button';log.innerHTML='<span aria-hidden="true">▤</span>';log.title='Chat log';log.setAttribute('aria-label','Chat log');log.addEventListener('click',()=>window.RistChatScripts?.open?.());
  const settings=document.createElement('button');settings.type='button';settings.className='rist-chat-icon-button';settings.innerHTML='<span aria-hidden="true">⚙</span>';settings.title='Chat settings';settings.setAttribute('aria-label','Chat settings');settings.addEventListener('click',()=>window.RistStartMenu?.open?.());
  tools.append(log,settings);wrap.append(modeDrop,input,send,tools);setLiveValue(input.value);
 }
 function queue(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;enhance()})}
 document.addEventListener('click',e=>{if(!e.target.closest('.rist-rp-mode-dropdown'))closeMenus();},true);
 new MutationObserver(queue).observe(document.documentElement,{childList:true,subtree:true});
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',queue,{once:true});else queue();
})();