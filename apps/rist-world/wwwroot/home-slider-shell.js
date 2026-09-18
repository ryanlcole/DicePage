(()=>{
 'use strict';
 const HOME_ID='rist-app-home-slider';
 let observer=null;
 function isGameMaster(){
  const root=document.querySelector('.rist.release-world');
  const text=((root?.textContent)||'').toLowerCase();
  return text.includes('gamemaster')||text.includes('game master')||text.includes(' gm ');
 }
 function makeButton(label,key){
  const button=document.createElement('button');
  button.type='button';
  button.className='rist-app-slider-button';
  button.dataset.sliderTarget=key;
  button.textContent=label;
  button.setAttribute('aria-label',label);
  return button;
 }
 function suppressLegacyFooter(root){
  const legacy=root.querySelector('.release-footer-region');
  if(legacy){
   legacy.setAttribute('aria-hidden','true');
   legacy.style.setProperty('display','none','important');
   legacy.style.setProperty('visibility','hidden','important');
   legacy.style.setProperty('pointer-events','none','important');
  }
 }
 function buildHome(){
  const root=document.querySelector('.rist.release-world');
  if(!root)return false;
  suppressLegacyFooter(root);
  const region=root.querySelector('.release-private-region');
  if(!region)return false;
  const oldRail=region.querySelector('.private-assets-rail');
  if(oldRail){
   oldRail.setAttribute('aria-hidden','true');
   oldRail.style.setProperty('visibility','hidden','important');
   oldRail.style.setProperty('pointer-events','none','important');
  }
  let slider=region.querySelector('#'+HOME_ID);
  if(!slider){
   slider=document.createElement('nav');
   slider.id=HOME_ID;
   slider.className='rist-app-home-slider';
   slider.setAttribute('aria-label','Private home slider');
   slider.append(
    makeButton('Chat','chat'),
    makeButton('Dice','dice'),
    makeButton('Actors','actors')
   );
   if(isGameMaster())slider.append(makeButton('Editor','editor'));
   slider.append(makeButton('Custom','custom'));
   region.appendChild(slider);
  }else if(isGameMaster()&&!slider.querySelector('[data-slider-target="editor"]')){
   const custom=slider.querySelector('[data-slider-target="custom"]');
   slider.insertBefore(makeButton('Editor','editor'),custom||null);
  }
  region.dataset.appSlider='home';
  return true;
 }
 function start(){
  buildHome();
  const app=document.getElementById('app')||document.body;
  if(!observer){
   observer=new MutationObserver(()=>buildHome());
   observer.observe(app,{childList:true,subtree:true});
  }
  document.addEventListener('rist:game-start',buildHome);
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.RistAppSliders={...(window.RistAppSliders||{}),home:buildHome};
})();
