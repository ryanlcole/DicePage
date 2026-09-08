(()=>{
 'use strict';
 const HOME_ID='rist-app-home-slider';
 function looksLikeGameMaster(){
  const text=(document.querySelector('.map-shell')?.textContent||document.querySelector('.rist.release-world')?.textContent||'').toLowerCase();
  return text.includes('gamemaster')||text.includes('game master');
 }
 function button(label,key){
  const el=document.createElement('button');
  el.type='button';
  el.className='rist-app-slider-button';
  el.dataset.sliderTarget=key;
  el.textContent=label;
  el.setAttribute('aria-label',label);
  return el;
 }
 function build(){
  const region=document.querySelector('.rist.release-world .release-private-region');
  if(!region)return;
  let slider=region.querySelector('#'+HOME_ID);
  if(!slider){
   slider=document.createElement('nav');
   slider.id=HOME_ID;
   slider.className='rist-app-home-slider';
   slider.setAttribute('aria-label','Private home slider');
   slider.append(
    button('Chat','chat'),
    button('Dice','dice'),
    button('Actors','actors')
   );
   if(looksLikeGameMaster())slider.append(button('Editor','editor'));
   slider.append(button('Custom','custom'));
   region.appendChild(slider);
  }
  region.dataset.appSlider='home';
 }
 function start(){
  build();
  const observer=new MutationObserver(()=>build());
  observer.observe(document.getElementById('app')||document.body,{childList:true,subtree:true});
  document.addEventListener('rist:game-start',build);
 }
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
 window.RistAppSliders={home:build};
})();
