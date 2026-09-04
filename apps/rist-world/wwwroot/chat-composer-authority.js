(()=>{
 'use strict';
 const MODES=[
  ['/s','says','Normal speaking range','normal'],
  ['/e','exclaims','Raised or emphatic speaking range','raised'],
  ['/q','quietly says','Low voice / short range','close'],
  ['/w','whispers','Very close, quiet range','close'],
  ['/h','hails','Moderate-distance calling range','raised'],
  ['/y','yells','Long audible range','long'],
  ['/b','bellows','Maximum natural voice range','long'],
  ['/c','clarion calls','Very long battlefield-style audible range','long'],
  ['/a','announces','Broad local-area announcement','long'],
  ['/sng','sings','Audible singing range','raised'],
  ['/sgn','signs','Visual / line-of-sight communication','visual'],
  ['/g','signals','Visible signal / line-of-sight range','visual'],
  ['/m','magically messages','Magical range set by the effect','magic'],
  ['/t','telepathically messages','Telepathic range set by the effect','magic'],
  ['/r','radios','Device-defined communication range','device'],
  ['/p','projects','Amplified or supernatural voice range','long']
 ];
 const byCode=code=>MODES.find(m=>m[0]===String(code||'').toLowerCase());
 let mode='/s',queued=false,activeMenu=null,activeButton=null,lastSent=null;
 const q=(s,r=document)=>r?.querySelector?.(s)||null;
 const modeEntry=()=>byCode(mode)||MODES[0];
 function applyRangeTheme(entry=modeEntry()){
  const theme=entry?.[3]||'normal';
  document.querySelectorAll('.rist-themed-chat-input,.rist-themed-chat-output').forEach(el=>el.dataset.rpRange=theme);
  const button=q('.rist-rp-mode-button');if(button)button.dataset.rpRange=theme;
 }
 function updateToggle(){const b=q('.rist-rp-mode-button');if(b){b.textContent=mode;b.dataset.rpRange=modeEntry()[3]||'normal';}applyRangeTheme();}
 function parseTyped(value){
  const raw=String(value||'');
  const m=raw.match(/^\s*(\/[a-z]+)(?:\s+|$)([\s\S]*)$/i);
  const found=m&&byCode(m[1]);
  if(!found)return {line:raw,changed:false};
  mode=found[0];updateToggle();
  return {line:m[2]||'',changed:true};
 }
 function setLiveValue(line){
  const live=q('.home-chat-compose textarea');if(!live)return;
  const clean=String(line||'');
  const value=clean.trim()?`${mode} ${clean}`:clean;
  const setter=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value')?.set;
  setter?.call(live,value);live.dispatchEvent(new Event('input',{bubbles:true}));
 }
 function formatLine(text){
  const raw=String(text||'').trim();
  const command=raw.match(/^(\/[a-z]+)\s+([\s\S]+)$/i);
  if(command){const found=byCode(command[1]);if(found)return `${found[1]}: ${command[2]}`;}
  if(lastSent&&raw===lastSent.line)return `${lastSent.verb}: ${raw}`;
  return raw;
 }
 function formatVisibleOutputs(){
  document.querySelectorAll('.rist-themed-chat-copy p').forEach(p=>{
   const original=p.dataset.ristRawText||p.textContent||'';
   if(!p.dataset.ristRawText)p.dataset.ristRawText=original;
   const command=original.match(/^\s*(\/[a-z]+)(?:\s+|$)/i);
   const entry=command&&byCode(command[1])||lastSent&&byCode(lastSent.code)||modeEntry();
   const output=p.closest('.rist-themed-chat-output');if(output)output.dataset.rpRange=entry?.[3]||'normal';
   const formatted=formatLine(original);
   if(p.textContent!==formatted)p.textContent=formatted;
  });
  applyRangeTheme();
 }
 function positionMenu(menu){
  if(!menu)return;
  const map=q('.release-map-region .map-shell')||q('.release-map-region');
  const r=map?.getBoundingClientRect();
  if(!r||r.width<20||r.height<20)return;
  menu.style.setProperty('left',`${Math.round(r.left)}px`,'important');
  menu.style.setProperty('top',`${Math.round(r.top)}px`,'important');
  menu.style.setProperty('width',`${Math.round(r.width)}px`,'important');
  menu.style.setProperty('height',`${Math.round(r.height)}px`,'important');
  menu.style.setProperty('max-height',`${Math.round(r.height)}px`,'important');
  menu.style.setProperty('right','auto','important');
  menu.style.setProperty('bottom','auto','important');
  menu.style.setProperty('transform','none','important');
 }
 function closeMenu(){if(activeMenu){activeMenu.classList.remove('open');activeMenu.remove();activeMenu=null;}if(activeButton){activeButton.setAttribute('aria-expanded','false');activeButton=null;}}
 function buildModeDropdown(){
  const root=document.createElement('div');root.className='rist-rp-mode-dropdown';
  const button=document.createElement('button');button.type='button';button.className='rist-rp-mode-button';button.textContent=mode;button.dataset.rpRange=modeEntry()[3]||'normal';button.setAttribute('aria-haspopup','listbox');button.setAttribute('aria-expanded','false');button.setAttribute('aria-label','Roleplay communication mode');
  function openMenu(){
   closeMenu();const menu=document.createElement('div');menu.className='rist-rp-mode-menu rist-rp-mode-menu-portal open';menu.setAttribute('role','listbox');
   for(const [code,label,range,theme] of MODES){
    const option=document.createElement('button');option.type='button';option.className='rist-rp-mode-option';option.dataset.rpRange=theme;option.setAttribute('role','option');option.dataset.code=code;option.innerHTML=`<strong>${code}</strong><span>${label}…</span><small>${range}</small>`;
    option.addEventListener('click',()=>{mode=code;button.textContent=mode;button.dataset.rpRange=theme;applyRangeTheme([code,label,range,theme]);const input=q('.rist-chat-line-input');if(input)setLiveValue(input.value);closeMenu();});menu.appendChild(option);
   }
   document.body.appendChild(menu);activeMenu=menu;activeButton=button;button.setAttribute('aria-expanded','true');positionMenu(menu);
  }
  button.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();activeButton===button?closeMenu():openMenu();});root.append(button);return root;
 }
 function enhance(){
  const wrap=q('.rist-themed-chat-input');if(!wrap||wrap.dataset.ristComposer==='1')return;
  const source=q('.home-chat-compose textarea');let prior=source?.value||q('textarea',wrap)?.value||'';
  const parsed=parseTyped(prior);prior=parsed.line;
  wrap.dataset.ristComposer='1';wrap.replaceChildren();
  const modeDrop=buildModeDropdown();
  const input=document.createElement('textarea');input.className='rist-chat-line-input';input.maxLength=1200;input.placeholder='Line…';input.value=prior;input.setAttribute('aria-label','Character line');
  input.addEventListener('input',()=>{const parsedInput=parseTyped(input.value);if(parsedInput.changed){input.value=parsedInput.line;input.setSelectionRange?.(input.value.length,input.value.length);}setLiveValue(input.value);});
  const actions=document.createElement('div');actions.className='rist-chat-action-row';
  const send=document.createElement('button');send.type='button';send.className='rist-chat-action-button rist-chat-send';send.innerHTML='<span aria-hidden="true">➤</span>';send.title='Send';send.setAttribute('aria-label','Send');
  send.addEventListener('click',()=>{const entry=modeEntry();lastSent={code:entry[0],verb:entry[1],line:input.value.trim()};applyRangeTheme(entry);setLiveValue(input.value);requestAnimationFrame(()=>{q('.home-chat-send')?.click();setTimeout(()=>{input.value='';setLiveValue('');formatVisibleOutputs();},0);});});
  const log=document.createElement('button');log.type='button';log.className='rist-chat-action-button';log.innerHTML='<span aria-hidden="true">▤</span>';log.title='Chat log';log.setAttribute('aria-label','Chat log');log.addEventListener('click',()=>window.RistChatScripts?.open?.());
  const settings=document.createElement('button');settings.type='button';settings.className='rist-chat-action-button';settings.innerHTML='<span aria-hidden="true">⚙</span>';settings.title='Chat settings';settings.setAttribute('aria-label','Chat settings');settings.addEventListener('click',()=>window.RistStartMenu?.open?.());
  actions.append(send,log,settings);wrap.append(modeDrop,input,actions);setLiveValue(input.value);applyRangeTheme();formatVisibleOutputs();
 }
 function applyExternal(text){const parsed=parseTyped(text);const input=q('.rist-chat-line-input');if(input){input.value=parsed.line;setLiveValue(parsed.line);}applyRangeTheme();return {code:mode,verb:modeEntry()[1],line:parsed.line};}
 function queue(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;enhance();formatVisibleOutputs();})}
 document.addEventListener('click',e=>{if(!e.target.closest('.rist-rp-mode-button')&&!e.target.closest('.rist-rp-mode-menu-portal'))closeMenu();},true);
 window.addEventListener('resize',()=>{if(activeMenu)positionMenu(activeMenu)},{passive:true});window.addEventListener('orientationchange',()=>setTimeout(()=>{if(activeMenu)positionMenu(activeMenu)},120),{passive:true});
 new MutationObserver(queue).observe(document.documentElement,{childList:true,subtree:true,characterData:true});
 window.RistRoleplayCommands={apply:applyExternal,format:formatLine,get code(){return mode},get verb(){return modeEntry()[1]},modes:MODES.map(m=>({code:m[0],label:m[1],range:m[2],theme:m[3]}))};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',queue,{once:true});else queue();
})();