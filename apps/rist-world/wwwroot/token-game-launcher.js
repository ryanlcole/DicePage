(()=>{
 const gameNames=['Chess Pieces','Crystal Chessboard','Chess Tokens','Tabletop Grid','Classic Cards','Card Tables','Timers & Spinner','Light Board','Dark Board'];
 let gameIndex=0;
 const tokenSource=()=>document.querySelector('#active-character-token-source');
 function decorateTokenButtons(){
  const rail=document.querySelector('#token-slider');
  if(!rail)return;
  const mini=rail.querySelector('.mini-choice');
  if(mini){
   mini.parentElement?.classList.add('coin-token-source');
   mini.classList.add('coin-choice');
   mini.textContent='';
   mini.parentElement?.setAttribute('aria-label','Add coin miniature to pallet');
   mini.parentElement?.setAttribute('title','Coins / miniatures');
  }
  const pawn=rail.querySelector('.pawn-choice');
  if(pawn){
   pawn.parentElement?.classList.add('character-token-source');
   pawn.classList.add('character-front-token');
   pawn.textContent='';
   const src=tokenSource()?.dataset.frontToken||'';
   pawn.classList.toggle('has-character-token',!!src);
   pawn.classList.toggle('no-character-token',!src);
   if(src)pawn.style.setProperty('background-image',`url("${src.replaceAll('"','%22')}")`,'important');
   else pawn.style.removeProperty('background-image');
   const name=tokenSource()?.dataset.character||'selected character';
   pawn.parentElement?.setAttribute('aria-label',`Add ${name||'selected character'} front token to pallet`);
   pawn.parentElement?.setAttribute('title',name||'Character token');
  }
  if(!rail.querySelector('.calforth-token-button')){
   const button=document.createElement('button');
   button.type='button';button.className='calforth-token-button';button.setAttribute('aria-label','Play tabletop games with Calforth Brightly');button.title='Calforth Brightly · Games';
   const face=document.createElement('span');face.className='calforth-token-face';button.append(face);button.addEventListener('click',openGames);
   const pawnButton=rail.querySelector('.character-token-source')||rail.querySelector('.pawn-choice')?.parentElement;
   (pawnButton||rail.querySelector('.token-pin-source'))?.insertAdjacentElement('afterend',button);
  }
 }
 function gameChoice(index){
  const b=document.createElement('button');b.type='button';b.className='calforth-game-choice'+(index===gameIndex?' active':'');b.dataset.index=index;
  const thumb=document.createElement('span');thumb.className=`calforth-game-thumb atlas-${index}`;
  const label=document.createElement('span');label.textContent=gameNames[index];
  b.append(thumb,label);b.addEventListener('click',()=>selectGame(index));return b;
 }
 function selectGame(index){
  gameIndex=index;
  const overlay=document.querySelector('.calforth-game-overlay');if(!overlay)return;
  overlay.querySelectorAll('.calforth-game-choice').forEach((b,i)=>b.classList.toggle('active',i===index));
  const stage=overlay.querySelector('.calforth-game-stage');if(stage)stage.className=`calforth-game-stage atlas-${index}`;
  const title=overlay.querySelector('.calforth-selected-game');if(title)title.textContent=gameNames[index];
 }
 function closeGames(){document.querySelector('.calforth-game-overlay')?.remove()}
 function openGames(){
  closeGames();
  const overlay=document.createElement('div');overlay.className='calforth-game-overlay';overlay.addEventListener('click',e=>{if(e.target===overlay)closeGames()});
  const card=document.createElement('section');card.className='calforth-game-card';card.setAttribute('role','dialog');card.setAttribute('aria-modal','true');card.setAttribute('aria-label','Calforth Brightly games');
  const head=document.createElement('header');head.className='calforth-game-head';
  const avatar=document.createElement('span');avatar.className='calforth-game-avatar';
  const title=document.createElement('div');title.className='calforth-game-title';title.innerHTML='<strong>Calforth Brightly</strong><span>Choose a tabletop game</span>';
  const close=document.createElement('button');close.type='button';close.className='calforth-game-close';close.textContent='×';close.setAttribute('aria-label','Close games');close.addEventListener('click',closeGames);head.append(avatar,title,close);
  const grid=document.createElement('nav');grid.className='calforth-game-grid';gameNames.forEach((_,i)=>grid.append(gameChoice(i)));
  const wrap=document.createElement('div');wrap.className='calforth-game-stage-wrap';
  const selected=document.createElement('strong');selected.className='calforth-selected-game';selected.textContent=gameNames[gameIndex];
  const stage=document.createElement('div');stage.className=`calforth-game-stage atlas-${gameIndex}`;stage.setAttribute('role','img');stage.setAttribute('aria-label',gameNames[gameIndex]);
  const help=document.createElement('p');help.className='calforth-game-help';help.textContent='Calforth games are public tabletop utilities and do not require login.';
  wrap.append(selected,stage,help);card.append(head,grid,wrap);overlay.append(card);document.body.append(overlay);
 }
 function scan(){decorateTokenButtons()}
 const mo=new MutationObserver(scan);mo.observe(document.documentElement,{subtree:true,childList:true,attributes:true,attributeFilter:['data-front-token','data-character']});
 addEventListener('rist:app-ready',scan);if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',scan,{once:true});else scan();setTimeout(scan,1200);
})();
