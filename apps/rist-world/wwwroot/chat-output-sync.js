(()=>{
 'use strict';
 let queued=false;
 const q=(s,r=document)=>r?.querySelector(s);
 function audience(){
  const active=[...document.querySelectorAll('.rist-chat-themed-tabs button')].find(b=>b.classList.contains('active'));
  const text=(active?.textContent||'Roleplay').trim().toLowerCase();
  return text==='gm'?'gm':text==='private'?'private':'roleplay';
 }
 function themedParts(){
  const root=q('.rist.release-world.deck-chat');if(!root)return {};
  const output=q('.rist-themed-chat-output',root);if(!output)return {root};
  let portrait=q('.rist-themed-chat-portrait',output);
  if(!portrait){portrait=document.createElement('div');portrait.className='rist-themed-chat-portrait';output.prepend(portrait)}
  let copy=q('.rist-themed-chat-copy',output);
  if(!copy){copy=document.createElement('div');copy.className='rist-themed-chat-copy';output.appendChild(copy)}
  let strong=q('strong',copy);if(!strong){strong=document.createElement('strong');copy.appendChild(strong)}
  let text=q('p',copy);if(!text){text=document.createElement('p');copy.appendChild(text)}
  return {root,output,portrait,strong,copy:text};
 }
 function liveParts(){
  const live=q('.release-footer-region .inline-chat-output');if(!live)return {};
  const strong=q('.dialogue-copy strong',live),paragraph=q('.dialogue-copy p,.chat-output-placeholder',live);
  const speaker=(strong?.childNodes?.[0]?.textContent||strong?.textContent||'').trim();
  const text=(paragraph?.textContent||'').trim();
  const portrait=q('.dialogue-portrait img',live)?.src||'';
  return {speaker,text,portrait};
 }
 function characterName(){return (q('[data-character-name]')?.getAttribute('data-character-name')||q('.character-name')?.textContent||q('.sheet-character-name')?.textContent||'Unknown').trim()||'Unknown'}
 function characterPortrait(){return liveParts().portrait||q('.character-portrait img')?.src||''}
 function playerProfileImage(){return window.RistProfileImage?.get?.()||window.RistProfileImage?.current?.()||localStorage.getItem('rist.profile.image.v1')||''}
 function paintPortrait(host,src,kind){
  if(!host)return;host.replaceChildren();host.dataset.portraitKind=kind;
  if(src){const img=document.createElement('img');img.src=src;img.alt='';host.appendChild(img);return}
  const placeholder=document.createElement('span');placeholder.className='rist-chat-portrait-placeholder';placeholder.textContent=kind==='character'?'♙':'?';host.appendChild(placeholder);
 }
 function refreshPortrait(){
  const parts=themedParts();if(!parts.output)return;
  const mode=audience();parts.output.dataset.chatAudience=mode;
  paintPortrait(parts.portrait,mode==='roleplay'?characterPortrait():playerProfileImage(),mode==='roleplay'?'character':'profile');
 }
 function paint(speaker,text){
  const {output,portrait,strong,copy}=themedParts();if(!output||!strong||!copy||!text)return;
  const mode=audience();output.dataset.chatAudience=mode;
  strong.textContent=speaker|| (mode==='roleplay'?characterName():'Player');
  copy.textContent=text;output.dataset.visibleChatText=text;
  paintPortrait(portrait,mode==='roleplay'?characterPortrait():playerProfileImage(),mode==='roleplay'?'character':'profile');
 }
 function syncAuthoritative(){
  const {output}=themedParts();if(!output)return;
  refreshPortrait();
  if(audience()!=='roleplay')return;
  const {speaker,text}=liveParts();
  if(!text||/roleplay output appears here\.?/i.test(text)||output.dataset.visibleChatText===text)return;
  paint(speaker||characterName(),text);
 }
 function captureSend(event){
  const button=event.target.closest?.('.rist-themed-chat-input button');if(!button||!/^(send)$/i.test((button.textContent||'').trim()))return;
  const input=q('.rist-themed-chat-input textarea'),text=(input?.value||'').trim();if(!text)return;
  const mode=audience();paint(mode==='roleplay'?characterName():'Player',text);
  if(mode==='roleplay'){setTimeout(syncAuthoritative,80);setTimeout(syncAuthoritative,250);setTimeout(syncAuthoritative,700)}
 }
 function queue(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;syncAuthoritative()})}
 function start(){
  document.addEventListener('click',event=>{captureSend(event);if(event.target.closest?.('.rist-chat-themed-tabs button'))setTimeout(refreshPortrait,0)},true);
  document.addEventListener('rist:profile-image-changed',refreshPortrait);
  new MutationObserver(queue).observe(document.body,{childList:true,subtree:true,characterData:true});syncAuthoritative();
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();