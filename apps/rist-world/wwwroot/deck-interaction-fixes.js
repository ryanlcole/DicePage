(()=>{
 'use strict';
 const DICE_COUNT=8;
 let chatDraft='';
 let privateRecipient='';
 let diceSyncLock=false;
 let queued=false;
 const q=(s,r=document)=>r?.querySelector(s);
 const qa=(s,r=document)=>[...(r?.querySelectorAll(s)||[])];

 function liveDiceSources(){
  return qa('#footer-slider .release-footer-track > .die-button, #footer-slider .release-footer-track > .die-control');
 }
 function rollDie(index){
  const source=liveDiceSources()[index%DICE_COUNT];
  const button=source?.matches?.('.die-button')?source:source?.querySelector?.('.die-button');
  if(!button)return;
  button.click();
 }
 function syncD5(index,value){
  const source=liveDiceSources()[index%DICE_COUNT];
  const select=source?.querySelector?.('select');
  if(!select)return;
  select.value=value;
  select.dispatchEvent(new Event('change',{bubbles:true}));
  qa('.rist-dice-image-loop > .rist-dice-proxy').forEach((proxy,i)=>{
   if(i%DICE_COUNT!==index%DICE_COUNT)return;
   const mirror=proxy.querySelector('select');
   if(mirror&&mirror.value!==value)mirror.value=value;
  });
 }

 function ensureTripleLoop(loop){
  if(!loop)return;
  const children=[...loop.children];
  if(children.length<DICE_COUNT)return;
  while(loop.children.length>DICE_COUNT*3)loop.lastElementChild?.remove();
  if(loop.children.length===DICE_COUNT*2){
   children.slice(0,DICE_COUNT).forEach((node,index)=>{
    const clone=node.cloneNode(true);
    clone.setAttribute('aria-hidden','true');
    clone.dataset.loopIndex=String(index);
    loop.appendChild(clone);
   });
  }
  [...loop.children].forEach((node,index)=>node.dataset.loopIndex=String(index%DICE_COUNT));
 }
 function cycleWidth(loop){return loop?.scrollWidth?loop.scrollWidth/3:0;}
 function normalizeInfinite(row,loop){
  const cycle=cycleWidth(loop);if(!cycle)return row.scrollLeft;
  let x=row.scrollLeft;
  if(x<cycle*.35){x+=cycle;row.scrollLeft=x;}
  else if(x>cycle*1.65){x-=cycle;row.scrollLeft=x;}
  return x;
 }
 function setBothDiceScroll(source,target,sourceLoop,targetLoop){
  if(diceSyncLock)return;
  diceSyncLock=true;
  const x=normalizeInfinite(source,sourceLoop);
  target.scrollLeft=x;
  normalizeInfinite(target,targetLoop);
  requestAnimationFrame(()=>{diceSyncLock=false;});
 }
 function patchDice(){
  const root=q('.rist.release-world');
  if(!root?.classList.contains('deck-dice'))return;
  const shell=q(':scope > .release-world-shell',root);
  const row1=q(':scope > .rist-deck-row.row1',shell);
  const row2=q(':scope > .rist-deck-row.row2',shell);
  const head=q('.rist-dice-header-loop',row1);
  const art=q('.rist-dice-image-loop',row2);
  if(!row1||!row2||!head||!art)return;
  ensureTripleLoop(head);ensureTripleLoop(art);
  head.classList.remove('rist-dice-synced');art.classList.remove('rist-dice-synced');
  if(row1.dataset.diceLinked!=='1'){
   row1.dataset.diceLinked='1';row2.dataset.diceLinked='1';
   row1.addEventListener('scroll',()=>setBothDiceScroll(row1,row2,head,art),{passive:true});
   row2.addEventListener('scroll',()=>setBothDiceScroll(row2,row1,art,head),{passive:true});
   row1.addEventListener('click',event=>{
    const button=event.target.closest('.rist-dice-header-loop > button');if(!button)return;
    event.preventDefault();event.stopImmediatePropagation();rollDie(Number(button.dataset.loopIndex||0));
   },true);
   row2.addEventListener('click',event=>{
    if(event.target.closest('select'))return;
    const proxy=event.target.closest('.rist-dice-image-loop > .rist-dice-proxy');if(!proxy)return;
    event.preventDefault();event.stopImmediatePropagation();rollDie(Number(proxy.dataset.loopIndex||0));
   },true);
   row2.addEventListener('change',event=>{
    const select=event.target.closest('.rist-dice-image-loop > .rist-dice-proxy select');if(!select)return;
    const proxy=select.closest('.rist-dice-proxy');
    event.stopImmediatePropagation();syncD5(Number(proxy?.dataset.loopIndex||0),select.value);
   },true);
   requestAnimationFrame(()=>{
    const cycle=cycleWidth(head);
    if(cycle){row1.scrollLeft=cycle;row2.scrollLeft=cycle;}
   });
  }
 }

 function privateNames(){
  const values=[];
  const add=v=>{v=(v||'').trim();if(v&&!values.includes(v))values.push(v);};
  qa('[data-private-chat-name]').forEach(el=>add(el.getAttribute('data-private-chat-name')));
  qa('[data-player-name]').forEach(el=>add(el.getAttribute('data-player-name')));
  qa('.participant-name,.player-name').forEach(el=>add(el.textContent));
  return values;
 }
 function patchPrivateSelector(header){
  const active=qa('button',header).find(b=>b.classList.contains('active'))?.textContent?.trim().toLowerCase();
  let select=q('.rist-private-user-select',header);
  if(active!=='private'){select?.remove();return;}
  if(!select){
   select=document.createElement('select');select.className='rist-private-user-select';select.setAttribute('aria-label','Private chat user');
   select.addEventListener('change',()=>{
    privateRecipient=select.value;
    q('.home-inline-chat')?.setAttribute('data-private-recipient',privateRecipient);
    document.dispatchEvent(new CustomEvent('rist:private-recipient-changed',{detail:{name:privateRecipient}}));
   });
   header.appendChild(select);
  }
  const names=privateNames();
  const current=privateRecipient||select.value;
  select.replaceChildren();
  const placeholder=document.createElement('option');placeholder.value='';placeholder.textContent=names.length?'Select user':'No private users';select.appendChild(placeholder);
  names.forEach(name=>{const option=document.createElement('option');option.value=name;option.textContent=name;select.appendChild(option);});
  if(names.includes(current)){select.value=current;privateRecipient=current;}
 }
 function syncLiveChat(text,thenSend=false){
  const live=q('.home-chat-compose textarea');if(!live)return;
  const setter=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value')?.set;
  setter?.call(live,text);live.dispatchEvent(new Event('input',{bubbles:true}));
  if(thenSend)setTimeout(()=>q('.home-chat-send')?.click(),40);
 }
 function patchChat(){
  const root=q('.rist.release-world');if(!root?.classList.contains('deck-chat'))return;
  const header=q('.rist-chat-themed-tabs');if(header)patchPrivateSelector(header);
  const wrap=q('.rist-themed-chat-input');const old=q('textarea',wrap);if(!wrap||!old)return;
  if(old.dataset.stableChat!=='1'){
   if(!chatDraft)chatDraft=old.value||'';
   const stable=old.cloneNode(true);stable.dataset.stableChat='1';stable.value=chatDraft;
   stable.addEventListener('input',()=>{chatDraft=stable.value;});
   old.replaceWith(stable);
  }
  const input=q('textarea[data-stable-chat="1"]',wrap);
  const buttons=qa('button',wrap);
  const send=buttons.find(b=>/^send$/i.test((b.textContent||'').trim()));
  if(send&&send.dataset.stableSend!=='1'){
   send.dataset.stableSend='1';send.addEventListener('click',event=>{
    event.preventDefault();event.stopImmediatePropagation();
    chatDraft=input?.value||'';if(!chatDraft.trim())return;
    syncLiveChat(chatDraft,true);chatDraft='';if(input)input.value='';
   },true);
  }
 }
 function patch(){patchChat();patchDice();}
 function queue(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;patch();});}
 function start(){patch();new MutationObserver(queue).observe(document.body,{childList:true,subtree:true});window.addEventListener('resize',queue,{passive:true});window.addEventListener('orientationchange',()=>setTimeout(queue,120),{passive:true});}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
