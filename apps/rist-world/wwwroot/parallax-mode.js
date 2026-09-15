(()=>{
'use strict';

// Canonical map truth is tier + layer. Parallax is viewer perception only.
// A single global tilt-strength preference controls how strongly the perspective
// viewer reveals transitions between tier top-surfaces; it never changes world Z.
const PREF_KEY='rist.parallax.enabled.v1';
const ACTIVE_KEY='rist.parallax.worldbuilder.active.v1';
const TILT_KEY='rist.parallax.tilt-strength.v2';
const PLAY_KEY='rist.sprites.playback.v1';
const FPS_KEY='rist.sprites.fps.v1';
const FPS_VALUES=[6,12,24,30,60];
const DEFAULT_TILT=.65;
const clamp=(v,min,max)=>Math.max(min,Math.min(max,v));
const read=(key,fallback)=>{try{return localStorage.getItem(key)??fallback}catch{return fallback}};
const write=(key,value)=>{try{localStorage.setItem(key,String(value))}catch{}};
const parsedTilt=Number(read(TILT_KEY,String(DEFAULT_TILT)));
const state={
 enabled:read(PREF_KEY,'on')!=='off',
 active:read(ACTIVE_KEY,'on')!=='off',
 tiltStrength:Number.isFinite(parsedTilt)?clamp(parsedTilt,0,1):DEFAULT_TILT,
 playback:read(PLAY_KEY,'playing'),
 fps:Number(read(FPS_KEY,'12'))||12
};
const studio=()=>document.querySelector('.worldbuilder-studio');
const rail=()=>studio()?.querySelector('.studio-command-rail');
const emit=()=>window.dispatchEvent(new CustomEvent('rist-parallax-settings',{detail:{enabled:state.enabled,active:state.active,tiltStrength:state.tiltStrength,truth:'tier-layer',projection:'top-layer-transition'}}));
const emitPlayback=()=>window.dispatchEvent(new CustomEvent('rist-sprite-playback',{detail:{state:state.playback,fps:state.fps}}));
const setText=(node,value)=>{if(node&&node.textContent!==value)node.textContent=value};
const setTiltStrength=value=>{
 state.tiltStrength=clamp(Number(value)||0,0,1);
 write(TILT_KEY,state.tiltStrength.toFixed(3));
 sync();emit();
 return state.tiltStrength;
};
function style(){
 if(document.getElementById('rist-parallax-mode-style'))return;
 const s=document.createElement('style');s.id='rist-parallax-mode-style';s.textContent=`
 .studio-command-rail .wb-runtime-command{box-sizing:border-box;flex:0 0 auto;height:48px;min-width:104px;padding:4px 12px;display:grid;place-items:center;gap:2px;border:1px solid #4b5f69;border-radius:9px;background:#0d171e;color:#d4dde1;touch-action:manipulation}
 .studio-command-rail .wb-runtime-command strong{font:900 12px/1 system-ui;color:#f0ddb0}.studio-command-rail .wb-runtime-command small{font:800 7px/1 system-ui;letter-spacing:.06em;text-transform:uppercase;color:#8fa5b0}.studio-command-rail .wb-runtime-command.active{border-color:#d0aa56;background:#201b10}
 .worldbuilder-studio.sprites-paused .rist-world-sprite *{animation-play-state:paused!important}.worldbuilder-studio.sprites-stopped .rist-world-sprite *{animation:none!important}`;document.head.appendChild(s)
}
function command(name,title,small,onClick){
 const host=rail();if(!host)return null;
 let b=host.querySelector(`[data-wb-runtime="${name}"]`);if(b)return b;
 b=document.createElement('button');b.type='button';b.className='wb-runtime-command';b.dataset.wbRuntime=name;b.innerHTML=`<strong>${title}</strong><small>${small}</small>`;b.addEventListener('click',onClick);
 const view=[...host.querySelectorAll('button')].find(x=>x.querySelector('strong')?.textContent?.trim()==='View');
 const anchor=host.querySelector('[data-wb-runtime="fps"]')||host.querySelector('[data-wb-runtime="transport"]')||host.querySelector('[data-wb-runtime="parallax"]')||view;
 if(anchor)anchor.insertAdjacentElement('afterend',b);else host.appendChild(b);return b
}
function sync(){
 style();const root=studio();if(!root)return;
 const p=command('parallax','Perspective','Tilt',async()=>{
  if(!state.enabled){state.enabled=true;state.active=true;write(PREF_KEY,'on')}
  else state.active=!state.active;
  write(ACTIVE_KEY,state.active?'on':'off');
  if(state.active)await window.ristMotionPermission?.request?.();
  sync();emit()
 });
 const transport=command('transport','Pause','Playing',()=>{state.playback=state.playback==='playing'?'paused':state.playback==='paused'?'stopped':'playing';write(PLAY_KEY,state.playback);sync();emitPlayback()});
 const fps=command('fps','FPS',String(state.fps),()=>{const i=FPS_VALUES.indexOf(state.fps);state.fps=FPS_VALUES[(i+1+FPS_VALUES.length)%FPS_VALUES.length];write(FPS_KEY,state.fps);sync();emitPlayback()});
 if(p){p.classList.toggle('active',state.active&&state.enabled);setText(p.querySelector('strong'),'Perspective');setText(p.querySelector('small'),!state.enabled?'User Off':state.active?`Tilt ${Math.round(state.tiltStrength*100)}%`:'Off');p.setAttribute('aria-label',`Perspective tier-top tilt ${state.active&&state.enabled?'on':'off'}`)}
 if(transport){const next=state.playback==='playing'?'Pause':state.playback==='paused'?'Stop':'Play';setText(transport.querySelector('strong'),next);setText(transport.querySelector('small'),state.playback);transport.classList.toggle('active',state.playback==='playing');transport.setAttribute('aria-label',`Sprite playback ${state.playback}. Click to ${next.toLowerCase()}; cycles play, pause, and stop.`)}
 if(fps){setText(fps.querySelector('small'),String(state.fps));fps.setAttribute('aria-label',`Sprite playback ${state.fps} frames per second. Click to change.`)}
 root.classList.toggle('sprites-playing',state.playback==='playing');root.classList.toggle('sprites-paused',state.playback==='paused');root.classList.toggle('sprites-stopped',state.playback==='stopped');root.style.setProperty('--rist-sprite-fps',String(state.fps));root.style.setProperty('--rist-sprite-frame-duration',`${(1/state.fps).toFixed(5)}s`)
}
window.ristParallax={
 isEnabled:()=>state.enabled,
 isWorldBuilderActive:()=>state.active,
 tiltStrength:()=>state.tiltStrength,
 setTiltStrength,
 settings:()=>({enabled:state.enabled,active:state.active,tiltStrength:state.tiltStrength}),
 setEnabled(v){state.enabled=!!v;write(PREF_KEY,state.enabled?'on':'off');sync();emit();return state.enabled},
 setActive(v){state.active=!!v;write(ACTIVE_KEY,state.active?'on':'off');sync();emit();return state.active},
 resetTilt(){return setTiltStrength(DEFAULT_TILT)},
 // Compatibility only. Older viewer code called these APIs per tier. They now
 // resolve to the one presentation preference and never encode map depth.
 depthForTier:()=>state.tiltStrength,
 setTierDepth:(_tier,value)=>setTiltStrength(value),
 getTierDepths:()=>({viewerTilt:state.tiltStrength})
};
window.ristSpritePlayback={state:()=>({state:state.playback,fps:state.fps}),play(){state.playback='playing';write(PLAY_KEY,state.playback);sync();emitPlayback()},pause(){state.playback='paused';write(PLAY_KEY,state.playback);sync();emitPlayback()},stop(){state.playback='stopped';write(PLAY_KEY,state.playback);sync();emitPlayback()}};
let frame=0;const schedule=()=>{if(frame)return;frame=requestAnimationFrame(()=>{frame=0;sync()})};
const observer=new MutationObserver(schedule);
function start(){sync();observer.observe(document.body,{childList:true,subtree:true});emit();emitPlayback()}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();