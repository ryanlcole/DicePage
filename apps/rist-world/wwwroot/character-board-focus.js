(()=>{
 const rootSel='.character-console';
 const interactive='button,input,textarea,select,label,a';
 function navFor(root){
   let nav=root.parentElement?.querySelector(':scope > .board-focus-nav');
   if(!nav){nav=document.createElement('div');nav.className='board-focus-nav';nav.innerHTML='<button type="button" data-board-back>← Back</button>';root.insertAdjacentElement('afterend',nav);nav.querySelector('[data-board-back]').addEventListener('click',e=>{e.stopPropagation();back(root);});}
   return nav;
 }
 function clearCards(root){root.querySelectorAll('.board-card-active').forEach(x=>x.classList.remove('board-card-active'));root.classList.remove('board-card-focus');}
 function clearSection(root){clearCards(root);root.querySelectorAll('.board-section-active').forEach(x=>x.classList.remove('board-section-active'));root.classList.remove('board-section-focus');}
 function back(root){if(root.classList.contains('board-card-focus')){clearCards(root);return;}clearSection(root);}
 function fit(root){root.classList.add('board-fit'); if(!root.classList.contains('board-section-focus')){root.style.transform='';root.style.width='';}}
 function isArticle(el){return el.matches('.character-control-set>article,.feat-card-set>article');}
 function wire(root){if(root.dataset.boardFocus==='1')return;root.dataset.boardFocus='1';fit(root);navFor(root);
   root.addEventListener('click',e=>{
     if(e.target.closest(interactive)) return;
     const section=e.target.closest('.console-bank'); if(!section)return;
     const article=e.target.closest('.character-control-set>article,.feat-card-set>article');
     if(!root.classList.contains('board-section-focus')){
       root.querySelectorAll('.board-section-active').forEach(x=>x.classList.remove('board-section-active'));
       section.classList.add('board-section-active');root.classList.add('board-section-focus');
       requestAnimationFrame(()=>section.scrollIntoView({block:'start',behavior:'smooth'}));return;
     }
     if(!section.classList.contains('board-section-active'))return;
     if(article&&isArticle(article)){
       clearCards(root);article.classList.add('board-card-active');root.classList.add('board-card-focus');
       requestAnimationFrame(()=>article.scrollIntoView({block:'center',inline:'center',behavior:'smooth'}));
     }
   });
 }
 function scan(){document.querySelectorAll(rootSel).forEach(wire);}
 new MutationObserver(scan).observe(document.documentElement,{childList:true,subtree:true});
 addEventListener('resize',scan,{passive:true});document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelectorAll(rootSel).forEach(back);});scan();
})();