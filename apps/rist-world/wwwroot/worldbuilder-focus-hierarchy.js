const STYLE_ID='rist-worldbuilder-focus-hierarchy-css';
let host=null,select=null,lockButton=null,backButton=null,trail=null,status=null,observer=null,frame=0,lastState=null;

function api(){return window.ristWorldBuilderDepth||null}
function studio(){return document.querySelector('.worldbuilder-studio')}
function canvas(){return studio()?.querySelector('.studio-viewer-canvas')||null}
function value(obj,camel,pascal,fallback=null){return obj?.[camel]??obj?.[pascal]??fallback}
function optionsOf(state){const list=value(state,'options','Options',[]);return Array.isArray(list)?list:[]}
function pathOf(state){const list=value(state,'lockedPath','LockedPath',[]);return Array.isArray(list)?list:[]}
function optionKey(item){return String(value(item,'key','Key',''))}
function optionLabel(item){return String(value(item,'label','Label',''))}
function segmentLabel(item){return String(value(item,'label','Label',''))}
function nextLevel(state){return String(value(state,'nextLevel','NextLevel','Parallax'))}
function selectedKey(state){return String(value(state,'selectedKey','SelectedKey',''))}
function selectedLabel(state){return String(value(state,'selectedLabel','SelectedLabel',''))}
function battleVisible(state){return !!value(state,'battleInstanceVisible','BattleInstanceVisible',false)}
function canLock(state){return !!value(state,'canLock','CanLock',false)}
function canUnlock(state){return !!value(state,'canUnlock','CanUnlock',false)}
function sceneZ(state){return Number(value(state,'sceneZ','SceneZ',0))||0}
function tierIndex(state){return Number(value(state,'tierIndex','TierIndex',0))||0}
function layerOffset(state){return Number(value(state,'layerOffset','LayerOffset',0))||0}

function ensureStyle(){
 if(document.getElementById(STYLE_ID))return;
 const style=document.createElement('style');style.id=STYLE_ID;style.textContent=`
 .wb-focus-hierarchy{position:absolute;top:7px;left:50%;transform:translateX(-50%);z-index:54;max-width:calc(100% - 24px);display:grid;grid-template-rows:auto auto;gap:4px;pointer-events:none;font-family:Inter,system-ui,-apple-system,sans-serif}
 .wb-focus-controls{display:flex;align-items:center;justify-content:center;gap:4px;min-width:0;pointer-events:auto}
 .wb-focus-controls button,.wb-focus-controls select{box-sizing:border-box;height:32px;border:1px solid #715b2d;border-radius:8px;background:rgba(7,15,21,.94);color:#ead99c;font:800 10px/1 system-ui;touch-action:manipulation}
 .wb-focus-controls button{padding:0 10px}.wb-focus-controls button:disabled,.wb-focus-controls select:disabled{opacity:.45}
 .wb-focus-controls select{min-width:132px;max-width:min(48vw,260px);padding:0 28px 0 9px}
 .wb-focus-level{height:32px;display:grid;place-items:center;padding:0 9px;border:1px solid #4b5f69;border-radius:8px;background:rgba(5,12,17,.94);color:#91a9b5;font:900 8px/1 system-ui;letter-spacing:.08em;text-transform:uppercase;white-space:nowrap}
 .wb-focus-lock.active{border-color:#d0aa56;background:#211e12;color:#ffe9a7}
 .wb-focus-trail{pointer-events:auto;display:flex;justify-content:center;gap:3px;max-width:100%;overflow-x:auto;scrollbar-width:none}.wb-focus-trail::-webkit-scrollbar{display:none}
 .wb-focus-crumb{height:20px!important;min-width:max-content;padding:0 7px!important;border:1px solid rgba(87,108,118,.7)!important;border-radius:999px!important;background:rgba(4,11,16,.88)!important;color:#b8c5ca!important;font:800 7px/1 system-ui!important}
 .wb-focus-crumb.current{border-color:#d0aa56!important;color:#ffe6a0!important}
 .wb-focus-status{height:20px;display:grid;place-items:center;padding:0 8px;border-radius:999px;background:rgba(4,11,16,.88);color:#869ca7;font:800 7px/1 system-ui;white-space:nowrap}
 .wb-focus-battle{border-color:#d0aa56!important;color:#ffe6a0!important}
 .worldbuilder-studio.wb-access-large .wb-focus-controls button,.worldbuilder-studio.wb-access-large .wb-focus-controls select{height:44px;font-size:12px}
 @media(max-width:560px){.wb-focus-hierarchy{top:5px;max-width:calc(100% - 12px)}.wb-focus-level{display:none}.wb-focus-controls select{min-width:118px;max-width:45vw}.wb-focus-controls button{padding:0 8px}}
 `;document.head.appendChild(style);
}

function publish(state){
 const root=studio();if(!root||!state)return;
 root.dataset.wbFocusLevel=nextLevel(state);
 root.dataset.wbFocusPath=pathOf(state).map(segmentLabel).join(' / ');
 root.dataset.wbFocusBattle=battleVisible(state)?'true':'false';
 window.dispatchEvent(new CustomEvent('rist:worldbuilder-focus',{detail:state}));
}

function setState(state){if(state){lastState=state;publish(state)}scheduleRender();return state}
async function refresh(){try{const state=await api()?.refreshFocus?.();if(state)setState(state)}catch{}return lastState}
async function choose(key){try{setState(await api()?.selectFocus?.(key))}catch{}}
async function lock(){try{setState(await api()?.lockFocus?.())}catch{}}
async function back(){try{setState(await api()?.unlockFocus?.())}catch{}}
async function reset(){try{setState(await api()?.resetFocus?.())}catch{}}
async function rewindTo(index){
 const path=pathOf(lastState);let count=path.length-(index+1);while(count-->0){try{lastState=await api()?.unlockFocus?.()||lastState}catch{break}}
 setState(lastState);
}

function build(){
 const target=canvas();if(!target)return false;
 ensureStyle();host?.remove();
 host=document.createElement('section');host.className='wb-focus-hierarchy';host.setAttribute('aria-label','World Builder focus hierarchy');
 const controls=document.createElement('div');controls.className='wb-focus-controls';
 backButton=document.createElement('button');backButton.type='button';backButton.textContent='‹';backButton.setAttribute('aria-label','Move out one focus level');backButton.addEventListener('click',back);
 const level=document.createElement('span');level.className='wb-focus-level';level.dataset.role='level';
 select=document.createElement('select');select.setAttribute('aria-label','Choose focus');select.addEventListener('change',()=>choose(select.value));
 lockButton=document.createElement('button');lockButton.type='button';lockButton.className='wb-focus-lock';lockButton.textContent='Lock';lockButton.addEventListener('click',lock);
 const resetButton=document.createElement('button');resetButton.type='button';resetButton.textContent='⌂';resetButton.setAttribute('aria-label','Reset focus to Surface');resetButton.addEventListener('click',reset);
 controls.append(backButton,level,select,lockButton,resetButton);
 trail=document.createElement('div');trail.className='wb-focus-trail';trail.setAttribute('aria-label','Locked focus path');
 status=document.createElement('span');status.className='wb-focus-status';trail.append(status);
 host.append(controls,trail);target.append(host);return true;
}

function render(){
 const root=studio(),target=canvas();if(!root||!target)return;
 if(!host?.isConnected||host.parentElement!==target){if(!build())return}
 const state=lastState;if(!state){void refresh();return}
 const opts=optionsOf(state),selected=selectedKey(state),level=nextLevel(state),path=pathOf(state),battle=battleVisible(state);
 const levelNode=host.querySelector('[data-role="level"]');if(levelNode)levelNode.textContent=level;
 const signature=opts.map(x=>`${optionKey(x)}:${optionLabel(x)}`).join('|');
 if(select.dataset.signature!==signature){select.replaceChildren();if(opts.length){for(const item of opts){const option=document.createElement('option');option.value=optionKey(item);option.textContent=optionLabel(item);select.append(option)}}else{const option=document.createElement('option');option.value='';option.textContent=level==='Region'?'Define a Region to continue':battle?'Battle Instance':'No content at this level';select.append(option)}select.dataset.signature=signature}
 if([...select.options].some(x=>x.value===selected))select.value=selected;
 select.disabled=opts.length===0||battle;backButton.disabled=!canUnlock(state);lockButton.disabled=!canLock(state)||battle;lockButton.classList.toggle('active',canLock(state)&&!battle);lockButton.textContent=battle?'Locked':'Lock';
 trail.replaceChildren();path.forEach((segment,index)=>{const crumb=document.createElement('button');crumb.type='button';crumb.className='wb-focus-crumb';crumb.textContent=segmentLabel(segment);crumb.setAttribute('aria-label',`Return focus to ${segmentLabel(segment)}`);crumb.addEventListener('click',()=>rewindTo(index));trail.append(crumb)});
 const current=document.createElement('span');current.className=`wb-focus-status${battle?' wb-focus-battle':''}`;current.textContent=battle?'Battle Instance':`${level}: ${selectedLabel(state)||'—'} · T${tierIndex(state)} L${layerOffset(state)} Z${sceneZ(state)}`;current.setAttribute('role','status');current.setAttribute('aria-live','polite');trail.append(current);
}
function scheduleRender(){if(frame)return;frame=requestAnimationFrame(()=>{frame=0;render()})}
function mount(){if(!studio()||!canvas())return;if(!host?.isConnected)build();scheduleRender();void refresh()}

window.addEventListener('rist:worldbuilder-depth',()=>{scheduleRender();if(!lastState)void refresh()});
window.addEventListener('rist:worldbuilder-focus',scheduleRender);
window.addEventListener('resize',scheduleRender,{passive:true});
observer=new MutationObserver(()=>mount());observer.observe(document.documentElement,{childList:true,subtree:true});
ensureStyle();mount();
