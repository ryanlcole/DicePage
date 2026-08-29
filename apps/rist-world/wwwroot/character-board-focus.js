(()=>{
 'use strict';
 const rootSel='.character-console';
 const interactive='button,input,textarea,select,label,a';
 const clamp=(n,min,max)=>Math.min(max,Math.max(min,n));
 let activeSlider=null,activePointer=null;

 function navFor(root){
  let nav=root.parentElement?.querySelector(':scope > .board-focus-nav');
  if(nav)return nav;
  nav=document.createElement('div');
  nav.className='board-focus-nav';
  nav.innerHTML='<button type="button" data-board-close aria-label="Close section" title="Close section">×</button>';
  root.insertAdjacentElement('afterend',nav);
  nav.querySelector('[data-board-close]').addEventListener('click',e=>{e.stopPropagation();clearSection(root)});
  return nav;
 }
 const removeCardActions=root=>root.querySelectorAll('.board-card-actions').forEach(node=>node.remove());
 function clearCards(root){removeCardActions(root);root.querySelectorAll('.board-card-active').forEach(node=>node.classList.remove('board-card-active'));root.classList.remove('board-card-focus')}
 function clearSection(root){clearCards(root);root.querySelectorAll('.board-section-active').forEach(node=>node.classList.remove('board-section-active'));root.classList.remove('board-section-focus')}
 const back=root=>root.classList.contains('board-card-focus')?clearCards(root):clearSection(root);
 function fit(root){root.classList.add('board-fit');if(!root.classList.contains('board-section-focus')){root.style.transform='';root.style.width=''}}
 const isArticle=el=>el.matches('.character-control-set>article,.feat-card-set>article');
 function saveCharacter(root){
  const save=[...root.querySelectorAll('.character-console-tools button')].find(button=>button.textContent.trim()==='Save');
  if(!save)return false;
  save.click();return true;
 }
 function addCardActions(root,article){
  removeCardActions(root);
  const tools=article.querySelector('.control-tools-row')||article;
  const bar=document.createElement('div');
  bar.className='board-card-actions';
  bar.innerHTML='<button type="button" data-card-close aria-label="Cancel" title="Cancel">×</button><button type="button" data-card-save aria-label="Save" title="Save">✓</button>';
  bar.querySelector('[data-card-close]').addEventListener('click',e=>{e.stopPropagation();clearCards(root)});
  bar.querySelector('[data-card-save]').addEventListener('click',e=>{e.stopPropagation();saveCharacter(root);clearCards(root)});
  tools.append(bar);
 }
 function updateSliderVisual(shell,input){
  if(!shell||!input)return;
  const min=Number(input.min||0),max=Number(input.max||100),value=Number(input.value||0);
  const pct=max===min?0:clamp(((value-min)/(max-min))*100,0,100);
  shell.style.setProperty('--pct',`${pct}%`);
  const handle=shell.querySelector('.scarab-handle');
  if(handle){handle.style.top='auto';handle.style.bottom=`${pct}%`;handle.style.left='50%';handle.style.transform='translate(-50%,50%)'}
 }
 function setSliderFromY(shell,clientY){
  const input=shell?.querySelector('input[type="range"]');if(!input||input.disabled)return;
  const rail=shell.querySelector('.slider-rail')||shell,r=rail.getBoundingClientRect();
  const min=Number(input.min||0),max=Number(input.max||100),step=Math.max(Number(input.step||1),Number.EPSILON);
  const ratio=clamp((r.bottom-clientY)/Math.max(1,r.height),0,1);
  let next=min+(max-min)*ratio;next=Math.round((next-min)/step)*step+min;next=clamp(next,min,max);
  input.value=String(next);input.dispatchEvent(new Event('input',{bubbles:true}));updateSliderVisual(shell,input);
 }
 function startSlider(shell,clientY,pointerId){
  const input=shell?.querySelector('input[type="range"]');if(!input||input.disabled)return false;
  activeSlider=shell;activePointer=pointerId;shell.classList.add('slider-dragging');setSliderFromY(shell,clientY);return true;
 }
 function stopSlider(){activeSlider?.classList.remove('slider-dragging');activeSlider=null;activePointer=null}
 function wireSlider(shell){
  const input=shell.querySelector('input[type="range"]');if(input)updateSliderVisual(shell,input);
  if(shell.dataset.directSlider==='5')return;
  shell.dataset.directSlider='5';
  input?.addEventListener('input',()=>updateSliderVisual(shell,input));
  input?.addEventListener('change',()=>updateSliderVisual(shell,input));
  shell.addEventListener('pointerdown',e=>{if(startSlider(shell,e.clientY,e.pointerId)){shell.setPointerCapture?.(e.pointerId);e.preventDefault();e.stopPropagation()}},{passive:false});
 }
 if(!window.__ristBoardSliderGlobal5){
  window.__ristBoardSliderGlobal5=true;
  window.addEventListener('pointermove',e=>{if(!activeSlider||activePointer!==e.pointerId)return;e.preventDefault();setSliderFromY(activeSlider,e.clientY)},{passive:false});
  window.addEventListener('pointerup',e=>{if(activeSlider&&activePointer===e.pointerId)stopSlider()},{passive:true});
  window.addEventListener('pointercancel',stopSlider,{passive:true});
 }
 function numberAttributeCodes(root){
  root.querySelectorAll('.attributes-bank .character-control-set>article').forEach((article,index)=>{
   const code=article.querySelector('.nameplate-code-button');if(!code)return;
   const value=`AT${index+1}`;if(code.dataset.generatedCode!==value){code.textContent=value;code.dataset.generatedCode=value}
  });
 }
 function measureArticle(article){
  const compact=article.querySelector('.compact-field-control');if(!compact)return;
  const identity=compact.querySelector('.control-identity-row'),tools=compact.querySelector('.control-tools-row');
  const required=Math.max(250,Math.ceil(identity?.scrollWidth||220),Math.ceil(tools?.scrollWidth||180))+24;
  article.style.setProperty('--focus-card-width',`${Math.min(required,520)}px`);
 }
 function decorateArticle(article){article.querySelectorAll('.vertical-slider-shell').forEach(wireSlider);window.RistRuntime?.frame?.(`measure-${article.dataset.generatedCode||article.className}`,()=>measureArticle(article))??requestAnimationFrame(()=>measureArticle(article))}
 function decorate(root){numberAttributeCodes(root);root.querySelectorAll('.character-control-set>article,.feat-card-set>article').forEach(decorateArticle)}
 function wire(root){
  if(root.matches('[data-board-static="true"]')){root.classList.remove('board-fit','board-section-focus','board-card-focus');root.querySelectorAll('.board-section-active,.board-card-active').forEach(node=>node.classList.remove('board-section-active','board-card-active'));decorate(root);return}
  if(root.dataset.boardFocus==='3'){decorate(root);return}
  root.dataset.boardFocus='3';fit(root);navFor(root);decorate(root);
  root.addEventListener('click',e=>{
   if(e.target.closest(interactive))return;
   const section=e.target.closest('.console-bank');if(!section)return;
   const article=e.target.closest('.character-control-set>article,.feat-card-set>article');
   if(!root.classList.contains('board-section-focus')){root.querySelectorAll('.board-section-active').forEach(node=>node.classList.remove('board-section-active'));section.classList.add('board-section-active');root.classList.add('board-section-focus');requestAnimationFrame(()=>section.scrollIntoView({block:'start',behavior:'smooth'}));return}
   if(!section.classList.contains('board-section-active')||!article||!isArticle(article))return;
   clearCards(root);article.classList.add('board-card-active');root.classList.add('board-card-focus');addCardActions(root,article);requestAnimationFrame(()=>{measureArticle(article);article.scrollIntoView({block:'center',inline:'center',behavior:'smooth'})});
  });
 }
 const scan=()=>document.querySelectorAll(rootSel).forEach(wire);
 document.addEventListener('rist:dom-change',scan);
 document.addEventListener('rist:viewport-change',()=>document.querySelectorAll('.board-card-active').forEach(measureArticle));
 document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelectorAll(rootSel).forEach(back)});
 scan();
})();
