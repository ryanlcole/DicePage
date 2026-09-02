(()=>{
 'use strict';
 let queued=false;
 const q=(s,r=document)=>r?.querySelector(s);

 function themedParts(){
  const root=q('.rist.release-world.deck-chat');
  if(!root)return {};
  const output=q('.rist-themed-chat-output',root);
  return {root,output,strong:q('.rist-themed-chat-copy strong',output),copy:q('.rist-themed-chat-copy p',output)};
 }
 function liveParts(){
  const live=q('.release-footer-region .inline-chat-output');
  if(!live)return {};
  const strong=q('.dialogue-copy strong',live);
  const paragraph=q('.dialogue-copy p,.chat-output-placeholder',live);
  const speaker=(strong?.childNodes?.[0]?.textContent||strong?.textContent||'').trim();
  const text=(paragraph?.textContent||'').trim();
  return {speaker,text};
 }
 function characterName(){
  return (q('[data-character-name]')?.getAttribute('data-character-name')||q('.character-name')?.textContent||q('.sheet-character-name')?.textContent||'You').trim()||'You';
 }
 function paint(speaker,text){
  const {output,strong,copy}=themedParts();
  if(!output||!strong||!copy||!text)return;
  strong.textContent=speaker||'Shaelvien';
  copy.textContent=text;
  output.dataset.visibleChatText=text;
 }
 function syncAuthoritative(){
  const {output}=themedParts();
  if(!output)return;
  const {speaker,text}=liveParts();
  if(!text||/roleplay output appears here\.?/i.test(text))return;
  if(output.dataset.visibleChatText===text)return;
  paint(speaker||'Shaelvien',text);
 }
 function captureSend(event){
  const button=event.target.closest?.('.rist-themed-chat-input button');
  if(!button||!/^(send)$/i.test((button.textContent||'').trim()))return;
  const input=q('.rist-themed-chat-input textarea');
  const text=(input?.value||'').trim();
  if(!text)return;
  paint(characterName(),text);
  setTimeout(syncAuthoritative,80);
  setTimeout(syncAuthoritative,250);
  setTimeout(syncAuthoritative,700);
 }
 function queue(){
  if(queued)return;
  queued=true;
  requestAnimationFrame(()=>{queued=false;syncAuthoritative();});
 }
 function start(){
  document.addEventListener('click',captureSend,true);
  new MutationObserver(queue).observe(document.body,{childList:true,subtree:true,characterData:true});
  syncAuthoritative();
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
