(()=>{
 const rootSel='.character-console';
 const interactive='button,input,textarea,select,label,a';
 const clamp=(n,min,max)=>Math.min(max,Math.max(min,n));
 function navFor(root){
   let nav=root.parentElement?.querySelector(':scope > .board-focus-nav');
   if(!nav){
     nav=document.createElement('div');
     nav.className='board-focus-nav';
     nav.innerHTML='<button type="button" data-board-back aria-label="Back" title="Back">⟲</button>';
     root.insertAdjacentElement('afterend',nav);
     nav.querySelector('[data-board-back]').addEventListener('click',e=>{e.stopPropagation();back(root);});
   }
   return nav;
 }
 function removeCardActions(root){root.querySelectorAll('.board-card-actions').forEach(x=>x.remove());}
 function clearCards(root){removeCardActions(root);root.querySelectorAll('.board-card-active').forEach(x=>x.classList.remove('board-card-active'));root.classList.remove('board-card-focus');}
 function clearSection(root){clearCards(root);root.querySelectorAll('.board-section-active').forEach(x=>x.classList.remove('board-section-active'));root.classList.remove('board-section-focus');}
 function back(root){if(root.classList.contains('board-card-focus')){clearCards(root);return;}clearSection(root);}
 function fit(root){root.classList.add('board-fit');if(!root.classList.contains('board-section-focus')){root.style.transform='';root.style.width='';}}
 function isArticle(el){return el.matches('.character-control-set>article,.feat-card-set>article');}
 function clickExisting(article,selector){const el=article.querySelector(selector);if(el&&!el.disabled){el.click();return true;}return false;}
 function globalEdit(root){const tools=[...root.querySelectorAll('.character-console-tools button')];const edit=tools.find(b=>b.textContent.trim()==='Edit');if(edit){edit.click();return true;}return false;}
 function addCardActions(root,article){
   removeCardActions(root);
   const bar=document.createElement('div');
   bar.className='board-card-actions';
   bar.innerHTML='<button type="button" data-card-edit aria-label="Edit" title="Edit">✎</button><button type="button" data-card-dice aria-label="Dice bag" title="Dice bag">⚄</button>';
   bar.querySelector('[data-card-edit]').addEventListener('click',e=>{e.stopPropagation();globalEdit(root);});
   bar.querySelector('[data-card-dice]').addEventListener('click',e=>{e.stopPropagation();clickExisting(article,'.mini-bag,.card-bag');});
   article.prepend(bar);
 }
 function syncAttributeFromScore(article){
   const score=article.querySelector('.attribute-readouts label:first-child input');
   const mod=article.querySelector('.attribute-readouts label:nth-child(2) input');
   const range=article.querySelector('.vertical-slider-shell input[type="range"]');
   if(!score||!mod||!range)return;
   const apply=()=>{
     const s=Number.parseInt(score.value||'10',10);
     const m=clamp(Math.floor((s-10)/2),-10,10);
     if(Number(mod.value)!==m){mod.value=String(m);mod.dispatchEvent(new Event('change',{bubbles:true}));}
     range.value=String(m);range.dispatchEvent(new Event('input',{bubbles:true}));
     article.querySelector('.vertical-slider-shell')?.style.setProperty('--pct',`${(m+10)*5}%`);
   };
   score.addEventListener('change',apply);
   score.addEventListener('input',()=>requestAnimationFrame(apply));
 }
 function wireSlider(shell){
   if(shell.dataset.directSlider==='1')return;
   shell.dataset.directSlider='1';
   const input=shell.querySelector('input[type="range"]');
   if(!input)return;
   const updatePct=()=>{
     const min=Number(input.min||0),max=Number(input.max||100),v=Number(input.value||0);
     const pct=max===min?0:((v-min)/(max-min))*100;
     shell.style.setProperty('--pct',`${pct}%`);
   };
   const setFromPointer=e=>{
     if(input.disabled)return;
     const r=shell.getBoundingClientRect();
     const min=Number(input.min||0),max=Number(input.max||100);
     const ratio=clamp((r.bottom-e.clientY)/Math.max(1,r.height),0,1);
     const next=Math.round(min+(max-min)*ratio);
     input.value=String(next);
     input.dispatchEvent(new Event('input',{bubbles:true}));
     updatePct();
   };
   shell.addEventListener('pointerdown',e=>{if(input.disabled)return;e.preventDefault();shell.setPointerCapture?.(e.pointerId);setFromPointer(e);});
   shell.addEventListener('pointermove',e=>{if(!shell.hasPointerCapture?.(e.pointerId))return;e.preventDefault();setFromPointer(e);});
   input.addEventListener('input',updatePct);
   updatePct();
 }
 function decorateArticle(article){
   if(article.dataset.boardDecorated==='1')return;
   article.dataset.boardDecorated='1';
   article.querySelectorAll('.vertical-slider-shell').forEach(wireSlider);
   if(article.matches('.attribute-channel'))syncAttributeFromScore(article);
   const hand=article.querySelector('.show-hand');
   const bag=article.querySelector('.mini-bag,.card-bag');
   if(hand){hand.classList.add('card-back-action');hand.setAttribute('aria-label','Card');hand.setAttribute('title','Card');}
   if(hand&&bag){const holder=document.createElement('div');holder.className='card-bag-actions';bag.parentNode.insertBefore(holder,bag);holder.append(bag,hand);}
 }
 function decorate(root){root.querySelectorAll('.character-control-set>article,.feat-card-set>article').forEach(decorateArticle);}
 function wire(root){
   if(root.dataset.boardFocus==='1'){decorate(root);return;}
   root.dataset.boardFocus='1';fit(root);navFor(root);decorate(root);
   root.addEventListener('click',e=>{
     if(e.target.closest(interactive))return;
     const section=e.target.closest('.console-bank');if(!section)return;
     const article=e.target.closest('.character-control-set>article,.feat-card-set>article');
     if(!root.classList.contains('board-section-focus')){root.querySelectorAll('.board-section-active').forEach(x=>x.classList.remove('board-section-active'));section.classList.add('board-section-active');root.classList.add('board-section-focus');requestAnimationFrame(()=>section.scrollIntoView({block:'start',behavior:'smooth'}));return;}
     if(!section.classList.contains('board-section-active'))return;
     if(article&&isArticle(article)){clearCards(root);article.classList.add('board-card-active');root.classList.add('board-card-focus');addCardActions(root,article);requestAnimationFrame(()=>article.scrollIntoView({block:'center',inline:'center',behavior:'smooth'}));}
   });
 }
 function scan(){document.querySelectorAll(rootSel).forEach(wire);}
 new MutationObserver(scan).observe(document.documentElement,{childList:true,subtree:true});
 addEventListener('resize',scan,{passive:true});document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelectorAll(rootSel).forEach(back);});scan();
})();