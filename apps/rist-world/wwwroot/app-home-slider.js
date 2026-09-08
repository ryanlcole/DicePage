(()=>{
 'use strict';
 const HOME_ID='rist-app-home-slider',STYLE_ID='rist-app-home-slider-runtime-style';
 function ensureRuntimeAuthority(){
  if(document.getElementById(STYLE_ID))return;
  const style=document.createElement('style');
  style.id=STYLE_ID;
  style.textContent=`
   html body #app>.rist.release-world>.release-world-shell>.release-footer-region{display:none!important;position:absolute!important;width:0!important;height:0!important;min-width:0!important;min-height:0!important;max-width:0!important;max-height:0!important;overflow:hidden!important;visibility:hidden!important;pointer-events:none!important}
   html body #app>.rist.release-world>.release-world-shell>.release-private-region{display:block!important;height:var(--rist-home-slider,58px)!important;min-height:var(--rist-home-slider,58px)!important;max-height:var(--rist-home-slider,58px)!important;overflow:hidden!important}
   html body #app>.rist.release-world>.release-world-shell>.release-private-region>.private-assets-rail{position:absolute!important;width:1px!important;height:1px!important;min-width:0!important;min-height:0!important;max-width:1px!important;max-height:1px!important;overflow:hidden!important;opacity:0!important;pointer-events:none!important;clip-path:inset(50%)!important}
  `;
  document.body.appendChild(style);
 }
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
  ensureRuntimeAuthority();
  const region=document.querySelector('.rist.release-world .release-private-region');
  if(!region)return;
  let slider=region.querySelector('#'+HOME_ID);
  if(!slider){
   slider=document.createElement('nav');
   slider.id=HOME_ID;
   slider.className='rist-app-home-slider';
   slider.setAttribute('aria-label','Private home slider');
   slider.append(button('Chat','chat'),button('Dice','dice'),button('Actors','actors'));
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
