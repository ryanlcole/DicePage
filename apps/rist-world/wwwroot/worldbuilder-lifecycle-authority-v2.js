(()=>{
 'use strict';

 const VERSION='20260917-worldbuilder-lifecycle-v2-3';
 const ACTIVE_KEY='rist.worldbuilder.wasActiveBeforeBackground.v2';
 const WORKSPACE_KEY='rist.shell.workspace.v1';
 let hiddenAt=0,frame=0,observer=null,resumeGeneration=0;
 const studio=()=>document.querySelector('.worldbuilder-studio');

 function remember(){const active=!!studio();try{sessionStorage.setItem(ACTIVE_KEY,active?'1':'0');if(active)localStorage.setItem(WORKSPACE_KEY,'world')}catch{}return active}
 function wasActive(){try{return sessionStorage.getItem(ACTIVE_KEY)==='1'}catch{return false}}
 function setFooter(active){document.querySelectorAll('.site-copyright-notice').forEach(node=>{const region=node.closest('.release-footer-region');if(active){node.dataset.wbLifecycleHidden='1';node.setAttribute('aria-hidden','true');node.style.setProperty('display','none','important');if(region){region.classList.add('wb-worldbuilder-only-footer-strip');region.dataset.wbLifecycleHidden='1'}}else if(node.dataset.wbLifecycleHidden==='1'){delete node.dataset.wbLifecycleHidden;node.removeAttribute('aria-hidden');node.style.removeProperty('display')}if(!active&&region?.dataset.wbLifecycleHidden==='1'){delete region.dataset.wbLifecycleHidden;region.classList.remove('wb-worldbuilder-only-footer-strip')}})}
 function apply(){const active=!!studio();document.body?.classList.toggle('wb-immersive-worldbuilder',active);setFooter(active)}
 function refresh(source){apply();try{window.RistWorldBuilderKeyboardAuthority?.refresh?.()}catch{}try{window.RistWorldBuilderGridCursor?.refresh?.()}catch{}try{window.RistWorldBuilderModeKeyboardRelocation?.refresh?.()}catch{}try{window.RistWorldTickerData?.refresh?.()}catch{}try{window.ristViewerNavigation?.refresh?.()}catch{}try{window.ristViewerAuthority?.refresh?.()}catch{}try{window.dispatchEvent(new Event('resize'))}catch{}try{window.dispatchEvent(new CustomEvent('rist:viewer-state',{detail:{source,resume:true}}))}catch{}}
 function schedule(){if(frame)return;frame=requestAnimationFrame(()=>{frame=0;apply()})}
 function restore(source){if(document.hidden)return;const generation=++resumeGeneration;hiddenAt=0;try{if(wasActive())localStorage.setItem(WORKSPACE_KEY,'world')}catch{};const run=(suffix)=>{if(generation!==resumeGeneration||document.hidden)return;refresh(`${source}-${suffix}`)};requestAnimationFrame(()=>{run('raf1');requestAnimationFrame(()=>run('raf2'))});setTimeout(()=>run('settled-120'),120);setTimeout(()=>run('settled-500'),500)}
 function background(){hiddenAt=Date.now();remember()}
 function start(){apply();observer=new MutationObserver(schedule);observer.observe(document.getElementById('app')||document.body,{childList:true,subtree:true});document.addEventListener('visibilitychange',()=>document.hidden?background():restore('visibility-return'));window.addEventListener('pagehide',background,{passive:true});window.addEventListener('pageshow',event=>restore(event.persisted?'bfcache-return':'pageshow'),{passive:true});window.addEventListener('focus',()=>restore('focus-return'),{passive:true});window.addEventListener('orientationchange',()=>setTimeout(()=>restore('orientationchange'),80),{passive:true})}
 const api={version:VERSION,refresh:()=>refresh('manual'),foreground:()=>restore('manual-foreground'),state:()=>({worldbuilder:!!studio(),hidden:document.hidden,hiddenAt,wasActive:wasActive(),resumeGeneration})};window.RistWorldBuilderLifecycleAuthority=api;window.RistWorldBuilderImmersivePolish=api;if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
