(()=>{
 'use strict';
 let chatDraft='';
 let privateRecipient='';
 let diceSyncLock=false;
 let queued=false;
 const q=(s,r=document)=>r?.querySelector(s);
 const qa=(s,r=document)=>[...(r?.querySelectorAll(s)||[])];
 function liveDiceSources(){return qa('#footer-slider .release-footer-track > .die-button, #footer-slider .release-footer-track > .die-control')}
 function dieKey(el){
  const sprite=el?.matches?.('.die-sprite')?el:el?.querySelector?.('.die-sprite');
  if(!sprite)return '';
  const cls=[...sprite.classList].find(c=>/^die-d/.test(c)&&c!=='die-sprite');
  return cls?cls.replace(/^die-/,''):'';
 }
 function sourceForKey(key){return liveDiceSources().find(source=>dieKey(source)===key)}
 function rollDie(index){const sources=liveDiceSources();const source=sources[index%sources.length];const button=source?.matches?.('.die-button')?source:source?.querySelector?.('.die-button');button?.click()}
 function rollDieKey(key){const source=sourceForKey(key);const button=source?.matches?.('.die-button')?source:source?.querySelector?.('.die-button');button?.click()}
 function syncD5(key,value){
  const normalized=String(Math.max(1,Math.min(5,Number(value)||1)));
  const source=sourceForKey(key);const select=source?.querySelector?.('select');
  if(select){select.value=normalized;select.dispatchEvent(new Event('change',{bubbles:true}))}
  qa('.rist-dice-image-loop > .rist-dice-proxy').forEach(proxy=>{
   if(dieKey(proxy)!==key)return;
   const mirror=proxy.querySelector('select');if(mirror)mirror.value=normalized;
   const valueNode=proxy.querySelector('.rist-d5-step-value');if(valueNode)valueNode.textContent=`${key==='d5-bonus'?'+':'-'}${normalized}`;
  });
 }
 function ensureTripleLoop(loop,count){
  if(!loop||count<1)return;const children=[...loop.children];if(children.length<count)return;
  while(loop.children.length>count*3)loop.lastElementChild?.remove();
  if(loop.children.length===count*2){children.slice(0,count).forEach((node,index)=>{const clone=node.cloneNode(true);clone.setAttribute('aria-hidden','true');clone.dataset.loopIndex=String(index);loop.appendChild(clone)})}
  [...loop.children].forEach((node,index)=>node.dataset.loopIndex=String(index%count));
 }
 function cycleWidth(loop){return loop?.scrollWidth?loop.scrollWidth/3:0}
 function normalizeInfinite(row,loop){const cycle=cycleWidth(loop);if(!cycle)return row.scrollLeft;let x=row.scrollLeft;if(x<cycle*.35){x+=cycle;row.scrollLeft=x}else if(x>cycle*1.65){x-=cycle;row.scrollLeft=x}return x}
 function setBothDiceScroll(source,target,sourceLoop,targetLoop){if(diceSyncLock)return;diceSyncLock=true;const x=normalizeInfinite(source,sourceLoop);target.scrollLeft=x;normalizeInfinite(target,targetLoop);requestAnimationFrame(()=>{diceSyncLock=false})}
 function ensureD5Stepper(proxy,key){
  if(!proxy||!['d5-bonus','d5-penalty'].includes(key)||proxy.querySelector('.rist-d5-stepper'))return;
  const select=proxy.querySelector('select');const die=proxy.querySelector('.die-button');if(!select||!die)return;
  proxy.classList.add('d5-control',key==='d5-bonus'?'bonus-d5':'penalty-d5');
  const stepper=document.createElement('div');stepper.className='rist-d5-stepper';
  const minus=document.createElement('button');minus.type='button';minus.className='rist-d5-step-minus';minus.textContent='−';
  const value=document.createElement('span');value.className='rist-d5-step-value';value.textContent=`${key==='d5-bonus'?'+':'-'}${select.value||1}`;
  const plus=document.createElement('button');plus.type='button';plus.className='rist-d5-step-plus';plus.textContent='+';
  const adjust=delta=>{const current=Number(select.value)||1;syncD5(key,Math.max(1,Math.min(5,current+delta)))};
  minus.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();adjust(-1)});
  plus.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();adjust(1)});
  stepper.append(minus,value,plus);proxy.appendChild(stepper);
 }
 function patchDice(){
  const root=q('.rist.release-world');if(!root?.classList.contains('deck-dice'))return;
  const shell=q(':scope > .release-world-shell',root);const row1=q(':scope > .rist-deck-row.row1',shell);const row2=q(':scope > .rist-deck-row.row2',shell);const head=q('.rist-dice-header-loop',row1);const art=q('.rist-dice-image-loop',row2);if(!row1||!row2||!head||!art)return;
  const count=liveDiceSources().length;if(!count)return;
  ensureTripleLoop(head,count);ensureTripleLoop(art,count);head.classList.remove('rist-dice-synced');art.classList.remove('rist-dice-synced');
  qa('.rist-dice-proxy',art).forEach(proxy=>ensureD5Stepper(proxy,dieKey(proxy)));
  if(row1.dataset.diceLinked!=='1'){
   row1.dataset.diceLinked='1';row2.dataset.diceLinked='1';
   row1.addEventListener('scroll',()=>setBothDiceScroll(row1,row2,head,art),{passive:true});row2.addEventListener('scroll',()=>setBothDiceScroll(row2,row1,art,head),{passive:true});
   row1.addEventListener('click',event=>{const button=event.target.closest('.rist-dice-header-loop > button');if(!button)return;event.preventDefault();event.stopImmediatePropagation();rollDie(Number(button.dataset.loopIndex||0))},true);
   row2.addEventListener('click',event=>{if(event.target.closest('.rist-d5-stepper,select'))return;const proxy=event.target.closest('.rist-dice-image-loop > .rist-dice-proxy');if(!proxy)return;event.preventDefault();event.stopImmediatePropagation();const key=dieKey(proxy);if(key)rollDieKey(key);else rollDie(Number(proxy.dataset.loopIndex||0))},true);
   requestAnimationFrame(()=>{const cycle=cycleWidth(head);if(cycle){row1.scrollLeft=cycle;row2.scrollLeft=cycle}});
  }
 }
 function privateNames(){const values=[];const add=v=>{v=(v||'').trim();if(v&&!values.includes(v))values.push(v)};qa('[data-private-chat-name]').forEach(el=>add(el.getAttribute('data-private-chat-name')));qa('[data-player-name]').forEach(el=>add(el.getAttribute('data-player-name')));qa('.participant-name,.player-name').forEach(el=>add(el.textContent));return values}
 function patchPrivateSelector(header){
  const active=qa('button',header).find(b=>b.classList.contains('active'))?.textContent?.trim().toLowerCase();let select=q('.rist-private-user-select',header);if(active!=='private'){select?.remove();return}
  if(!select){select=document.createElement('select');select.className='rist-private-user-select';select.setAttribute('aria-label','Private chat user');select.addEventListener('change',()=>{privateRecipient=select.value;q('.home-inline-chat')?.setAttribute('data-private-recipient',privateRecipient);document.dispatchEvent(new CustomEvent('rist:private-recipient-changed',{detail:{name:privateRecipient}}))});header.appendChild(select)}
  const names=privateNames(),current=privateRecipient||select.value;select.replaceChildren();const placeholder=document.createElement('option');placeholder.value='';placeholder.textContent=names.length?'Select user':'No private users';select.appendChild(placeholder);names.forEach(name=>{const option=document.createElement('option');option.value=name;option.textContent=name;select.appendChild(option)});if(names.includes(current)){select.value=current;privateRecipient=current}
 }
 function syncLiveChat(text,thenSend=false){const live=q('.home-chat-compose textarea');if(!live)return;const setter=Object.getOwnPropertyDescriptor(HTMLTextAreaElement.prototype,'value')?.set;setter?.call(live,text);live.dispatchEvent(new Event('input',{bubbles:true}));if(thenSend)setTimeout(()=>q('.home-chat-send')?.click(),40)}
 function patchChat(){
  const root=q('.rist.release-world');if(!root?.classList.contains('deck-chat'))return;
  const header=q('.rist-chat-themed-tabs');if(header)patchPrivateSelector(header);
  const wrap=q('.rist-themed-chat-input');const input=q('textarea',wrap);if(!wrap||!input)return;
  if(input.dataset.stableChat!=='1'){
   input.dataset.stableChat='1';if(!chatDraft)chatDraft=input.value||'';input.value=chatDraft;
   input.addEventListener('input',event=>{chatDraft=input.value;event.stopImmediatePropagation()},true);
  }
  const send=qa('button',wrap).find(b=>/^send$/i.test((b.textContent||'').trim()));
  if(send&&send.dataset.stableSend!=='1'){
   send.dataset.stableSend='1';send.addEventListener('click',event=>{event.preventDefault();event.stopImmediatePropagation();chatDraft=input.value||'';if(!chatDraft.trim())return;syncLiveChat(chatDraft,true);chatDraft='';input.value=''},true);
  }
 }
 function patch(){patchChat();patchDice()}
 function queue(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;patch()})}
 function start(){patch();new MutationObserver(queue).observe(document.body,{childList:true,subtree:true});window.addEventListener('resize',queue,{passive:true});window.addEventListener('orientationchange',()=>setTimeout(queue,120),{passive:true})}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
