(()=>{
 const rootSel='.character-console';
 const interactive='button,input,textarea,select,label,a';
 const clamp=(n,min,max)=>Math.min(max,Math.max(min,n));
 let activeSlider=null;
 let activePointer=null;

 function navFor(root){
   let nav=root.parentElement?.querySelector(':scope > .board-focus-nav');
   if(!nav){
     nav=document.createElement('div');
     nav.className='board-focus-nav';
     nav.innerHTML='<button type="button" data-board-close aria-label="Close section" title="Close section">×</button>';
     root.insertAdjacentElement('afterend',nav);
     nav.querySelector('[data-board-close]').addEventListener('click',e=>{e.stopPropagation();clearSection(root);});
   }
   return nav;
 }
 function removeCardActions(root){root.querySelectorAll('.board-card-actions').forEach(x=>x.remove());}
 function clearCards(root){removeCardActions(root);root.querySelectorAll('.board-card-active').forEach(x=>x.classList.remove('board-card-active'));root.classList.remove('board-card-focus');}
 function clearSection(root){clearCards(root);root.querySelectorAll('.board-section-active').forEach(x=>x.classList.remove('board-section-active'));root.classList.remove('board-section-focus');}
 function back(root){if(root.classList.contains('board-card-focus')){clearCards(root);return;}clearSection(root);}
 function fit(root){root.classList.add('board-fit');if(!root.classList.contains('board-section-focus')){root.style.transform='';root.style.width='';}}
 function isArticle(el){return el.matches('.character-control-set>article,.feat-card-set>article');}
 function saveCharacter(root){
   const tools=[...root.querySelectorAll('.character-console-tools button')];
   const save=tools.find(b=>b.textContent.trim()==='Save');
   if(save){save.click();return true;}
   return false;
 }
 function addCardActions(root,article){
   removeCardActions(root);
   const tools=article.querySelector('.control-tools-row')||article;
   const bar=document.createElement('div');
   bar.className='board-card-actions';
   bar.innerHTML='<button type="button" data-card-close aria-label="Cancel" title="Cancel">×</button><button type="button" data-card-save aria-label="Save" title="Save">✓</button>';
   bar.querySelector('[data-card-close]').addEventListener('click',e=>{e.stopPropagation();clearCards(root);});
   bar.querySelector('[data-card-save]').addEventListener('click',e=>{e.stopPropagation();saveCharacter(root);clearCards(root);});
   tools.append(bar);
 }

 function updateSliderVisual(shell,input){
   if(!shell||!input)return;
   const min=Number(input.min||0),max=Number(input.max||100),v=Number(input.value||0);
   const pct=max===min?0:clamp(((v-min)/(max-min))*100,0,100);
   shell.style.setProperty('--pct',`${pct}%`);
   const handle=shell.querySelector('.scarab-handle');
   if(handle){
     handle.style.top='auto';
     handle.style.bottom=`${pct}%`;
     handle.style.left='50%';
     handle.style.transform='translate(-50%,50%)';
   }
 }
 function setSliderFromY(shell,clientY){
   const input=shell?.querySelector('input[type="range"]');
   if(!input||input.disabled)return;
   const rail=shell.querySelector('.slider-rail')||shell;
   const r=rail.getBoundingClientRect();
   const min=Number(input.min||0),max=Number(input.max||100),step=Math.max(Number(input.step||1),Number.EPSILON);
   const ratio=clamp((r.bottom-clientY)/Math.max(1,r.height),0,1);
   let next=min+(max-min)*ratio;
   next=Math.round((next-min)/step)*step+min;
   next=clamp(next,min,max);
   input.value=String(next);
   input.dispatchEvent(new Event('input',{bubbles:true}));
   updateSliderVisual(shell,input);
 }
 function startSlider(shell,clientY,pointerId){
   const input=shell?.querySelector('input[type="range"]');
   if(!input||input.disabled)return false;
   activeSlider=shell;activePointer=pointerId??'touch';
   shell.classList.add('slider-dragging');
   setSliderFromY(shell,clientY);
   return true;
 }
 function stopSlider(){if(activeSlider)activeSlider.classList.remove('slider-dragging');activeSlider=null;activePointer=null;}
 function wireSlider(shell){
   const input=shell.querySelector('input[type="range"]');
   if(input)updateSliderVisual(shell,input);
   if(shell.dataset.directSlider==='4')return;
   shell.dataset.directSlider='4';
   if(input){input.addEventListener('input',()=>updateSliderVisual(shell,input));input.addEventListener('change',()=>updateSliderVisual(shell,input));}
   shell.addEventListener('pointerdown',e=>{if(startSlider(shell,e.clientY,e.pointerId)){e.preventDefault();e.stopPropagation();}}, {passive:false});
   shell.addEventListener('touchstart',e=>{const t=e.touches[0];if(t&&startSlider(shell,t.clientY,'touch')){e.preventDefault();e.stopPropagation();}}, {passive:false});
 }
 if(!window.__ristBoardSliderGlobal4){
   window.__ristBoardSliderGlobal4=true;
   window.addEventListener('pointermove',e=>{if(!activeSlider||activePointer!==e.pointerId)return;e.preventDefault();setSliderFromY(activeSlider,e.clientY);},{passive:false});
   window.addEventListener('pointerup',e=>{if(activeSlider&&activePointer===e.pointerId)stopSlider();},{passive:true});
   window.addEventListener('pointercancel',stopSlider,{passive:true});
   window.addEventListener('touchmove',e=>{if(!activeSlider||activePointer!=='touch')return;const t=e.touches[0];if(!t)return;e.preventDefault();setSliderFromY(activeSlider,t.clientY);},{passive:false});
   window.addEventListener('touchend',()=>{if(activePointer==='touch')stopSlider();},{passive:true});
   window.addEventListener('touchcancel',()=>{if(activePointer==='touch')stopSlider();},{passive:true});
 }

 function numberAttributeCodes(root){
   root.querySelectorAll('.attributes-bank .character-control-set>article').forEach((article,index)=>{
     const code=article.querySelector('.nameplate-code-button');
     if(code){code.textContent=`AT${index+1}`;code.dataset.generatedCode=`AT${index+1}`;}
   });
 }
 function measureArticle(article){
   const compact=article.querySelector('.compact-field-control');
   if(!compact)return;
   const identity=compact.querySelector('.control-identity-row');
   const tools=compact.querySelector('.control-tools-row');
   const identityWidth=Math.ceil(identity?.scrollWidth||220);
   const toolsWidth=Math.ceil(tools?.scrollWidth||180);
   const required=Math.max(250,identityWidth,toolsWidth)+24;
   article.style.setProperty('--focus-card-width',`${Math.min(required,520)}px`);
 }
 function decorateArticle(article){
   article.querySelectorAll('.vertical-slider-shell').forEach(wireSlider);
   requestAnimationFrame(()=>measureArticle(article));
 }
 function decorate(root){numberAttributeCodes(root);root.querySelectorAll('.character-control-set>article,.feat-card-set>article').forEach(decorateArticle);}

 function wirePortraitEditor(editor){
   if(editor.dataset.dragPan==='1')return;
   editor.dataset.dragPan='1';
   const crop=editor.querySelector('.portrait-crop');
   const img=crop?.querySelector('img');
   const ranges=[...editor.querySelectorAll('label input[type="range"]')];
   const xRange=ranges[1],yRange=ranges[2];
   if(!crop||!img||!xRange||!yRange)return;
   crop.classList.add('portrait-pan-enabled');img.draggable=false;
   let dragging=false,startX=0,startY=0,startVX=50,startVY=50;
   const apply=(clientX,clientY)=>{
     const r=crop.getBoundingClientRect();
     const dx=(clientX-startX)/Math.max(1,r.width)*100;
     const dy=(clientY-startY)/Math.max(1,r.height)*100;
     xRange.value=String(clamp(Math.round(startVX+dx),0,100));
     yRange.value=String(clamp(Math.round(startVY+dy),0,100));
     xRange.dispatchEvent(new Event('input',{bubbles:true}));
     yRange.dispatchEvent(new Event('input',{bubbles:true}));
   };
   crop.addEventListener('pointerdown',e=>{dragging=true;startX=e.clientX;startY=e.clientY;startVX=Number(xRange.value);startVY=Number(yRange.value);crop.setPointerCapture?.(e.pointerId);crop.classList.add('portrait-panning');e.preventDefault();},{passive:false});
   crop.addEventListener('pointermove',e=>{if(!dragging)return;apply(e.clientX,e.clientY);e.preventDefault();},{passive:false});
   const done=()=>{dragging=false;crop.classList.remove('portrait-panning');};
   crop.addEventListener('pointerup',done);crop.addEventListener('pointercancel',done);
   crop.addEventListener('touchstart',e=>{const t=e.touches[0];if(!t)return;dragging=true;startX=t.clientX;startY=t.clientY;startVX=Number(xRange.value);startVY=Number(yRange.value);crop.classList.add('portrait-panning');e.preventDefault();},{passive:false});
   crop.addEventListener('touchmove',e=>{if(!dragging)return;const t=e.touches[0];if(!t)return;apply(t.clientX,t.clientY);e.preventDefault();},{passive:false});
   crop.addEventListener('touchend',done);crop.addEventListener('touchcancel',done);
 }

function wire(root){
   if(root.matches('[data-board-static="true"]')){
     root.classList.remove('board-fit','board-section-focus','board-card-focus');
     root.querySelectorAll('.board-section-active,.board-card-active').forEach(x=>x.classList.remove('board-section-active','board-card-active'));
     decorate(root);
     return;
   }
   if(root.dataset.boardFocus==='2'){decorate(root);return;}
   root.dataset.boardFocus='2';fit(root);navFor(root);decorate(root);
   root.addEventListener('click',e=>{
     if(e.target.closest(interactive))return;
     const section=e.target.closest('.console-bank');if(!section)return;
     const article=e.target.closest('.character-control-set>article,.feat-card-set>article');
     if(!root.classList.contains('board-section-focus')){root.querySelectorAll('.board-section-active').forEach(x=>x.classList.remove('board-section-active'));section.classList.add('board-section-active');root.classList.add('board-section-focus');requestAnimationFrame(()=>section.scrollIntoView({block:'start',behavior:'smooth'}));return;}
     if(!section.classList.contains('board-section-active'))return;
     if(article&&isArticle(article)){clearCards(root);article.classList.add('board-card-active');root.classList.add('board-card-focus');addCardActions(root,article);requestAnimationFrame(()=>{measureArticle(article);article.scrollIntoView({block:'center',inline:'center',behavior:'smooth'});});}
   });
 }
 function scan(){document.querySelectorAll(rootSel).forEach(wire);document.querySelectorAll('.portrait-editor').forEach(wirePortraitEditor);}
 new MutationObserver(scan).observe(document.documentElement,{childList:true,subtree:true});
 addEventListener('resize',()=>{scan();document.querySelectorAll('.board-card-active').forEach(measureArticle);},{passive:true});
 document.addEventListener('keydown',e=>{if(e.key==='Escape')document.querySelectorAll(rootSel).forEach(back);});scan();
})();
