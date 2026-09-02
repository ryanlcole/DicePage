(()=>{
 'use strict';
 const STORE='rist.cast.deck.v1';
 const ROLE_RANK={Lead:3,Support:2,Ensemble:1};
 let selectedId='';
 let castActive=false;
 let queued=false;
 const q=(s,r=document)=>r?.querySelector(s);
 const qa=(s,r=document)=>[...(r?.querySelectorAll(s)||[])];
 const load=()=>{try{return JSON.parse(localStorage.getItem(STORE)||'[]')}catch{return[]}};
 const save=cards=>localStorage.setItem(STORE,JSON.stringify(cards));
 function currentCharacter(){
  const name=(q('[data-character-name]')?.getAttribute('data-character-name')||q('.character-name')?.textContent||q('.sheet-character-name')?.textContent||'Character').trim();
  const portrait=q('.dialogue-portrait img')?.src||q('.character-portrait img')?.src||'';
  return {name:name||'Character',portrait};
 }
 function ensureSelector(){
  const list=q('.rist-section-list');if(!list)return;
  if(!list.dataset.castExitBound){list.dataset.castExitBound='1';list.addEventListener('click',e=>{const b=e.target.closest('button');if(b&&!b.hasAttribute('data-cast-section'))castActive=false;},true);}
  if(q('button[data-cast-section]',list))return;
  const dice=q('button[data-section="dice"]',list);if(!dice)return;
  const b=document.createElement('button');b.type='button';b.dataset.castSection='1';b.textContent='Cast';
  b.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();e.stopImmediatePropagation();castActive=true;renderCast();},true);
  dice.insertAdjacentElement('afterend',b);
 }
 function deckRows(){const shell=q('.rist.release-world>.release-world-shell');return [1,2,3].map(i=>q(`:scope>.rist-deck-row.row${i}`,shell));}
 function hideLegacyRegions(){const shell=q('.rist.release-world>.release-world-shell');['.release-public-region','.release-private-region','.release-footer-region'].forEach(sel=>{const el=q(`:scope>${sel}`,shell);if(el)el.style.setProperty('display','none','important')});}
 function setRow(row,node){if(!row)return;row.replaceChildren();row.appendChild(node);row.style.setProperty('display','flex','important');}
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
  const sheet=document.createElement('strong');sheet.textContent=currentCharacter().name;
  const add=document.createElement('button');add.type='button';add.textContent='+ Card';add.addEventListener('click',addCurrentCharacter);
  wrap.append(label,sheet,add);return wrap;
 }
 function cardNode(card){
  const btn=document.createElement('button');btn.type='button';btn.className='rist-cast-card';btn.classList.toggle('active',card.id===selectedId);btn.dataset.castId=card.id;
  const art=document.createElement('div');art.className='rist-cast-card-art';if(card.portrait){const img=document.createElement('img');img.src=card.portrait;img.alt='';art.appendChild(img)}else art.textContent='♙';
  const info=document.createElement('div');info.className='rist-cast-card-info';const name=document.createElement('strong');name.textContent=card.name;const role=document.createElement('small');role.textContent=card.role+(card.linkedTo?' · linked':'');info.append(name,role);
  const count=document.createElement('span');count.className='rist-cast-count';count.textContent=(card.count||1)>1?`×${card.count}`:'';
  btn.append(art,info,count);btn.addEventListener('click',()=>{selectedId=card.id;renderCast();});return btn;
 }
 function cardsNode(cards){const wrap=document.createElement('div');wrap.className='rist-cast-cards';if(!cards.length){const empty=document.createElement('button');empty.type='button';empty.className='rist-cast-empty';empty.textContent='+ Add current character card';empty.addEventListener('click',addCurrentCharacter);wrap.appendChild(empty);return wrap;}cards.forEach(c=>wrap.appendChild(cardNode(c)));return wrap;}
 function validLeaders(card,cards){return cards.filter(other=>other.id!==card.id&&other.inPlay!==false&&ROLE_RANK[other.role]>ROLE_RANK[card.role]);}
 function propagate(cards,source){for(const child of cards.filter(c=>c.linkedTo===source.id)){child.command=source.command;propagate(cards,child)}}
 function controlsNode(cards){
  const wrap=document.createElement('div');wrap.className='rist-cast-controls';let card=cards.find(c=>c.id===selectedId)||cards[0];if(card&&!selectedId)selectedId=card.id;if(!card){wrap.textContent='Add a character card to begin.';return wrap;}
  const role=document.createElement('select');['Lead','Support','Ensemble'].forEach(r=>{const o=document.createElement('option');o.value=r;o.textContent=r;role.appendChild(o)});role.value=card.role;role.setAttribute('aria-label','Cast role');
  const link=document.createElement('select');link.setAttribute('aria-label','Follow card');const none=document.createElement('option');none.value='';none.textContent='Independent';link.appendChild(none);validLeaders(card,cards).forEach(c=>{const o=document.createElement('option');o.value=c.id;o.textContent=`Follow ${c.name}`;link.appendChild(o)});link.value=card.linkedTo||'';
  const command=document.createElement('input');command.type='text';command.placeholder='Command';command.value=card.command||'';
  const issue=document.createElement('button');issue.type='button';issue.textContent='Command';const remove=document.createElement('button');remove.type='button';remove.textContent='Remove';
  role.addEventListener('change',()=>{card.role=role.value;if(card.linkedTo&&!validLeaders(card,cards).some(x=>x.id===card.linkedTo))card.linkedTo='';save(cards);renderCast();});
  link.addEventListener('change',()=>{card.linkedTo=link.value;if(card.linkedTo){const parent=cards.find(c=>c.id===card.linkedTo);if(parent?.command)card.command=parent.command;}save(cards);renderCast();});
  issue.addEventListener('click',()=>{card.command=command.value.trim();propagate(cards,card);save(cards);renderCast();});
  remove.addEventListener('click',()=>{if((card.count||1)>1)card.count--;else{cards=cards.filter(c=>c.id!==card.id);cards.forEach(c=>{if(c.linkedTo===card.id)c.linkedTo=''});selectedId='';}save(cards);renderCast();});
  wrap.append(role,link,command,issue,remove);return wrap;
 }
 function renderCast(){
  const root=q('.rist.release-world');const shell=q(':scope>.release-world-shell',root);if(!root||!shell)return;
  root.classList.remove('deck-chat','deck-dice','deck-assets','deck-logs','deck-custom-editor');root.classList.add('deck-cast');hideLegacyRegions();qa('.rist-section-list>button').forEach(b=>b.classList.toggle('active',b.hasAttribute('data-cast-section')));
  const cards=load();if(!selectedId&&cards[0])selectedId=cards[0].id;const [r1,r2,r3]=deckRows();setRow(r1,headerNode());setRow(r2,cardsNode(cards));setRow(r3,controlsNode(cards));
 }
 function patch(){ensureSelector();if(castActive&&!q('.rist.release-world')?.classList.contains('deck-cast'))renderCast();}
 function queue(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;patch()})}
 function start(){patch();new MutationObserver(queue).observe(document.body,{childList:true,subtree:true});}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
