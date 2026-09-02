(()=>{
 'use strict';
 const STORE='rist.cast.deck.v2';
 const ROLE_RANK={Anchor:4,Lead:3,Support:2,Ensemble:1};
 let selectedId='';
 let overlay=null;
 const q=(s,r=document)=>r?.querySelector(s);
 const qa=(s,r=document)=>[...(r?.querySelectorAll(s)||[])];
 function load(){
  try{
   const parsed=JSON.parse(localStorage.getItem(STORE)||'[]');
   if(Array.isArray(parsed)&&parsed.length)return parsed;
  }catch{}
  const seed=[{id:'cast-anchor-default',name:'Unknown',portrait:'',role:'Anchor',count:1,linkedTo:'',command:'',inPlay:true}];
  localStorage.setItem(STORE,JSON.stringify(seed));
  return seed;
 }
 const save=cards=>localStorage.setItem(STORE,JSON.stringify(cards));
 function currentCharacter(){
  const raw=(q('[data-character-name]')?.getAttribute('data-character-name')||q('.character-name')?.textContent||q('.sheet-character-name')?.textContent||'Unknown').trim();
  const portrait=q('.dialogue-portrait img')?.src||q('.character-portrait img')?.src||'';
  return {name:raw||'Unknown',portrait};
 }
 function ensureOverlay(){
  if(overlay?.isConnected)return overlay;
  overlay=document.createElement('section');
  overlay.className='rist-cast-overlay';
  overlay.setAttribute('aria-label','Cast');
  overlay.innerHTML='<div class="rist-cast-overlay-row cast-row1"></div><div class="rist-cast-overlay-row cast-row2"></div><div class="rist-cast-overlay-row cast-row3"></div>';
  document.documentElement.appendChild(overlay);
  return overlay;
 }
 function show(active){
  ensureOverlay().classList.toggle('active',active);
  q('.rist.release-world')?.classList.toggle('deck-cast',active);
 }
 function ensureSelector(){
  const list=q('.rist-section-list');if(!list)return;
  let cast=q('button[data-cast-section]',list);
  if(!cast){
   const dice=q('button[data-section="dice"]',list);if(!dice)return;
   cast=document.createElement('button');cast.type='button';cast.dataset.castSection='1';cast.textContent='Cast';
   cast.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();renderCast();},true);
   dice.insertAdjacentElement('afterend',cast);
  }
  if(list.dataset.castExitBound!=='1'){
   list.dataset.castExitBound='1';
   list.addEventListener('click',e=>{
    const b=e.target.closest('button');
    if(b&&!b.hasAttribute('data-cast-section'))show(false);
   },true);
  }
 }
 function row(n){return q(`.cast-row${n}`,ensureOverlay())}
 function setRow(n,node){const r=row(n);if(!r)return;r.replaceChildren(node)}
 function addCurrentCharacter(){
  const c=currentCharacter(),cards=load();
  let existing=cards.find(x=>x.name===c.name&&x.portrait===c.portrait&&x.role==='Ensemble'&&!x.linkedTo);
  if(existing)existing.count=(existing.count||1)+1;
  else cards.push({id:`cast-${Date.now()}`,name:c.name,portrait:c.portrait,role:'Ensemble',count:1,linkedTo:'',command:'',inPlay:true});
  save(cards);renderCast();
 }
 function headerNode(){
  const wrap=document.createElement('div');wrap.className='rist-cast-header';
  const label=document.createElement('span');label.textContent='Name';
  const sheet=document.createElement('strong');sheet.textContent=currentCharacter().name||'Unknown';
  const add=document.createElement('button');add.type='button';add.textContent='+ Card';add.addEventListener('click',addCurrentCharacter);
  wrap.append(label,sheet,add);return wrap;
 }
 function cardNode(card){
  const btn=document.createElement('button');btn.type='button';btn.className='rist-cast-card';btn.classList.toggle('active',card.id===selectedId);
  const art=document.createElement('div');art.className='rist-cast-card-art';
  if(card.portrait){const img=document.createElement('img');img.src=card.portrait;img.alt='';art.appendChild(img)}else art.textContent='♙';
  const info=document.createElement('div');info.className='rist-cast-card-info';
  const name=document.createElement('strong');name.textContent=card.name||'Unknown';
  const role=document.createElement('small');role.textContent=card.role+(card.linkedTo?' · linked':'');
  const count=document.createElement('span');count.className='rist-cast-count';count.textContent=(card.count||1)>1?`×${card.count}`:'';
  info.append(name,role);btn.append(art,info,count);btn.addEventListener('click',()=>{selectedId=card.id;renderCast();});return btn;
 }
 function cardsNode(cards){const wrap=document.createElement('div');wrap.className='rist-cast-cards';cards.forEach(c=>wrap.appendChild(cardNode(c)));return wrap}
 function validLeaders(card,cards){return cards.filter(other=>other.id!==card.id&&other.inPlay!==false&&ROLE_RANK[other.role]>ROLE_RANK[card.role])}
 function propagate(cards,source){for(const child of cards.filter(c=>c.linkedTo===source.id)){child.command=source.command;propagate(cards,child)}}
 function controlsNode(cards){
  const wrap=document.createElement('div');wrap.className='rist-cast-controls';
  let card=cards.find(c=>c.id===selectedId)||cards[0];if(card&&!selectedId)selectedId=card.id;
  const role=document.createElement('select');['Anchor','Lead','Support','Ensemble'].forEach(r=>{const o=document.createElement('option');o.value=r;o.textContent=r;role.appendChild(o)});role.value=card.role;role.setAttribute('aria-label','Cast role');
  const link=document.createElement('select');link.setAttribute('aria-label','Follow card');const none=document.createElement('option');none.value='';none.textContent='Independent';link.appendChild(none);validLeaders(card,cards).forEach(c=>{const o=document.createElement('option');o.value=c.id;o.textContent=`Follow ${c.name}`;link.appendChild(o)});link.value=card.linkedTo||'';
  const command=document.createElement('input');command.type='text';command.placeholder='Command';command.value=card.command||'';
  const issue=document.createElement('button');issue.type='button';issue.textContent='Command';
  const remove=document.createElement('button');remove.type='button';remove.textContent='Remove';remove.disabled=card.id==='cast-anchor-default'&&cards.length===1;
  role.addEventListener('change',()=>{card.role=role.value;if(card.linkedTo&&!validLeaders(card,cards).some(x=>x.id===card.linkedTo))card.linkedTo='';save(cards);renderCast()});
  link.addEventListener('change',()=>{card.linkedTo=link.value;if(card.linkedTo){const parent=cards.find(c=>c.id===card.linkedTo);if(parent?.command)card.command=parent.command}save(cards);renderCast()});
  issue.addEventListener('click',()=>{card.command=command.value.trim();propagate(cards,card);save(cards);renderCast()});
  remove.addEventListener('click',()=>{if(remove.disabled)return;if((card.count||1)>1)card.count--;else{const kept=cards.filter(c=>c.id!==card.id);kept.forEach(c=>{if(c.linkedTo===card.id)c.linkedTo=''});save(kept);selectedId='';renderCast();return}save(cards);renderCast()});
  wrap.append(role,link,command,issue,remove);return wrap;
 }
 function renderCast(){
  ensureSelector();show(true);
  qa('.rist-section-list>button').forEach(b=>b.classList.toggle('active',b.hasAttribute('data-cast-section')));
  const cards=load();if(!selectedId&&cards[0])selectedId=cards[0].id;
  setRow(1,headerNode());setRow(2,cardsNode(cards));setRow(3,controlsNode(cards));
 }
 function start(){ensureSelector();ensureOverlay();new MutationObserver(()=>ensureSelector()).observe(document.body,{childList:true,subtree:true});}
 window.RistCastDeck={render:renderCast,hide:()=>show(false)};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
