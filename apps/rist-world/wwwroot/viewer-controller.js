(()=>{
 const closeClass='map-viewer-close';
 let viewerResizeObserver=null;
 let selectedSection='chat';
 const ASSET_LABELS={cards:'Cards',tokens:'Tokens / Chits',minis:'Minis','rolling-stock':'Rolling Stock',pawns:'Pawns / Meeples',tiles:'Tiles',terrain:'Terrain',bits:'Bits',custom1:'Custom1',add:'+'};
 const SECTIONS=[
  ['chat','Chat'],['dice','Dice'],['cards','Cards'],['tokens','Tokens'],['minis','Minis'],['rolling-stock','Rolling Stock'],['pawns','Pawns/Meeples'],['tiles','Tiles'],['terrain','Terrains'],['bits','Bits'],['logs','Logs'],['custom1','Custom1'],['add','+']
 ];

 function clickButton(selector){const button=document.querySelector(selector);if(button){button.click();return true;}return false;}
 function closeTarget(target){
  if(target.matches('.root-menu-panel'))return clickButton('#header-slider .root-menu-button.active[aria-expanded="true"]');
  if(target.matches('.release-action-menu.save-menu'))return clickButton('#header-slider .root-menu-button[aria-label="Save and export"]');
  if(target.matches('.release-action-menu.load-menu'))return clickButton('#header-slider .root-menu-button[aria-label="Load"]');
  if(target.matches('#card-library'))return clickButton('#header-slider .root-menu-button[aria-label="Cards"]');
  if(target.matches('.asset-slider-stack'))return clickButton('#header-slider .root-menu-button[aria-label="Browse asset library"]');
  if(target.matches('.rist-tutorial-shell')){const skip=[...target.querySelectorAll('button')].find(button=>/skip tutorial|close/i.test(button.textContent||''));if(skip){skip.click();return true;}}
  return false;
 }
 function addClose(target){if(!target||target.querySelector(`:scope > .${closeClass}`))return;const button=document.createElement('button');button.type='button';button.className=closeClass;button.setAttribute('aria-label','Close');button.title='Close';button.textContent='×';button.addEventListener('click',event=>{event.preventDefault();event.stopPropagation();closeTarget(target);});target.prepend(button);}

 function ensureSquareGridAuthority(){if(document.getElementById('rist-viewer-square-grid-authority'))return;const style=document.createElement('style');style.id='rist-viewer-square-grid-authority';style.textContent=`.rist.release-world .map:has(.grid.square)::before{background-size:var(--rist-viewer-square-cell,64px) var(--rist-viewer-square-cell,64px)!important;}`;document.head.appendChild(style);}
 function updateSquareCellSize(map){if(!map)return;const rect=map.getBoundingClientRect();if(rect.width<2||rect.height<2)return;const cell=Math.max(24,Math.round(Math.min(rect.width,rect.height)/10));map.style.setProperty('--rist-viewer-square-cell',`${cell}px`);}
 function fixViewer(){
  const shell=document.querySelector('.release-map-region .map-shell');const map=shell?.querySelector(':scope > .map');const stage=map?.querySelector(':scope > .world-stage');if(!shell||!map)return;const important=(el,name,value)=>el.style.setProperty(name,value,'important');
  for(const [name,value] of Object.entries({'box-sizing':'border-box','grid-column':'2','grid-row':'2','position':'relative','width':'100%','height':'100%','min-width':'0','min-height':'0','max-width':'none','max-height':'none','aspect-ratio':'auto','margin':'0','overflow':'hidden'}))important(map,name,value);
  if(stage)for(const [name,value] of Object.entries({'position':'absolute','inset':'0','width':'100%','height':'100%','min-width':'0','min-height':'0','max-width':'none','max-height':'none','aspect-ratio':'auto'}))important(stage,name,value);
  ensureSquareGridAuthority();updateSquareCellSize(map);
  if(!viewerResizeObserver)viewerResizeObserver=new ResizeObserver(entries=>{for(const entry of entries)if(entry.target.matches?.('.release-map-region .map-shell>.map'))updateSquareCellSize(entry.target);});
  if(!map.dataset.viewerSquareObserved){map.dataset.viewerSquareObserved='1';viewerResizeObserver.observe(map);}
 }

 function ensureAuthorityStyle(){
  if(document.getElementById('rist-control-deck-authority'))return;
  const style=document.createElement('style');style.id='rist-control-deck-authority';style.textContent=`
   .world-context-strip{box-sizing:border-box!important;position:relative!important;display:grid!important;grid-template-columns:10% 80% 10%!important;width:100%!important;height:5dvh!important;min-height:5dvh!important;max-height:5dvh!important;padding:0!important;gap:0!important;overflow:hidden!important;}
   .world-context-menu{grid-column:1!important;justify-self:start!important;align-self:center!important;max-width:100%!important;}
   .world-context-track{grid-column:2!important;position:relative!important;width:100%!important;min-width:0!important;max-width:100%!important;height:100%!important;overflow:hidden!important;contain:layout paint!important;}
   .world-context-login{grid-column:3!important;justify-self:end!important;align-self:center!important;max-width:100%!important;}
   .world-context-track>.bulletin-flow{position:absolute!important;inset:0 auto 0 0!important;display:flex!important;align-items:center!important;gap:18px!important;width:max-content!important;min-width:max-content!important;white-space:nowrap!important;animation:ristBulletinFlow 34s linear infinite!important;will-change:transform!important;}
   .world-context-track>.bulletin-flow>*{flex:0 0 auto!important;width:auto!important;min-width:max-content!important;white-space:nowrap!important;}
   @keyframes ristBulletinFlow{from{transform:translateX(0)}to{transform:translateX(-50%)}}

   .rist.release-world{box-sizing:border-box!important;position:relative!important;width:100%!important;height:95dvh!important;min-height:95dvh!important;max-height:95dvh!important;overflow:hidden!important;}
   .rist.release-world>.release-world-shell{box-sizing:border-box!important;position:relative!important;display:block!important;width:100%!important;height:95dvh!important;min-height:95dvh!important;max-height:95dvh!important;overflow:hidden!important;}
   .rist.release-world .release-map-region{box-sizing:border-box!important;position:absolute!important;left:0!important;right:0!important;top:0!important;width:100%!important;height:70dvh!important;min-height:70dvh!important;max-height:70dvh!important;margin:0!important;overflow:hidden!important;z-index:1!important;}

   .rist.release-world .release-menu-region{box-sizing:border-box!important;position:fixed!important;left:0!important;right:0!important;top:5dvh!important;width:100vw!important;height:5dvh!important;min-height:5dvh!important;max-height:5dvh!important;margin:0!important;padding:0!important;overflow:visible!important;z-index:2147483000!important;pointer-events:none!important;opacity:0!important;transform:translateY(-110%)!important;transition:transform .18s ease-out,opacity .12s linear!important;background:#05090cf7!important;border-bottom:1px solid #725d30!important;}
   .rist.release-world .release-menu-region.rist-os-menu-open{pointer-events:auto!important;opacity:1!important;transform:translateY(0)!important;}
   .rist.release-world .release-menu-region>#header-slider{box-sizing:border-box!important;position:relative!important;width:100%!important;height:5dvh!important;min-height:5dvh!important;max-height:5dvh!important;overflow:visible!important;}
   .rist.release-world .release-menu-region #header-slider .release-root-track{height:5dvh!important;min-height:5dvh!important;max-height:5dvh!important;display:flex!important;align-items:center!important;overflow-x:auto!important;overflow-y:hidden!important;pointer-events:auto!important;scrollbar-width:none!important;}
   .rist.release-world .release-menu-region #header-slider .release-root-track::-webkit-scrollbar{display:none!important;}

   .rist-section-selector{box-sizing:border-box!important;position:absolute!important;left:0!important;top:70dvh!important;width:15%!important;height:25dvh!important;z-index:40!important;display:grid!important;grid-template-rows:28px minmax(0,1fr) 28px!important;background:#081117!important;border-top:1px solid #725d30!important;border-right:1px solid #725d30!important;overflow:hidden!important;}
   .rist-section-selector>.selector-arrow{box-sizing:border-box!important;width:100%!important;height:28px!important;border:0!important;border-radius:0!important;background:#10181d!important;color:#d7be80!important;font:900 18px/1 system-ui!important;}
   .rist-section-list{min-height:0!important;overflow-y:auto!important;overflow-x:hidden!important;scrollbar-width:none!important;display:flex!important;flex-direction:column!important;align-items:stretch!important;}
   .rist-section-list::-webkit-scrollbar{display:none!important;}
   .rist-section-list>button{box-sizing:border-box!important;flex:0 0 auto!important;width:100%!important;min-height:32px!important;padding:5px 4px!important;border:0!important;border-bottom:1px solid #312b20!important;background:#0b141b!important;color:#bcae89!important;font:800 9px/1.1 system-ui!important;text-align:left!important;white-space:normal!important;overflow-wrap:anywhere!important;}
   .rist-section-list>button.active{background:#172229!important;color:#f1d68f!important;box-shadow:inset 3px 0 #a57c2f!important;}

   .rist-deck-row{box-sizing:border-box!important;position:absolute!important;left:15%!important;width:85%!important;height:calc(25dvh / 3)!important;z-index:35!important;display:none!important;align-items:center!important;padding:4px 8px!important;background:#0b141b!important;color:#d7be80!important;border-top:1px solid #4d4023!important;overflow:hidden!important;font:800 10px/1.2 system-ui!important;}
   .rist-deck-row.row1{top:70dvh!important}.rist-deck-row.row2{top:calc(70dvh + (25dvh / 3))!important}.rist-deck-row.row3{top:calc(70dvh + (50dvh / 3))!important}
   .rist-deck-row .deck-copy{min-width:0!important;overflow:hidden!important;text-overflow:ellipsis!important;white-space:nowrap!important;}

   .rist.release-world .release-public-region,.rist.release-world .release-private-region,.rist.release-world .release-footer-region{box-sizing:border-box!important;position:absolute!important;left:15%!important;width:85%!important;margin:0!important;z-index:30!important;display:none!important;overflow:hidden!important;}

   .rist.release-world.deck-assets .release-public-region{display:block!important;top:calc(70dvh + (25dvh / 3))!important;height:calc(25dvh / 3)!important;min-height:0!important;max-height:none!important;}
   .rist.release-world.deck-assets .release-private-region{display:block!important;top:calc(70dvh + (50dvh / 3))!important;height:calc(25dvh / 3)!important;min-height:0!important;max-height:none!important;}
   .rist.release-world.deck-assets .release-public-region>.public-assets-rail,.rist.release-world.deck-assets .release-private-region>.private-assets-rail{display:block!important;width:100%!important;height:100%!important;min-height:0!important;max-height:none!important;}
   .rist.release-world.deck-assets .asset-rail-header{display:none!important;}
   .rist.release-world.deck-assets .public-assets-strip,.rist.release-world.deck-assets .private-assets-strip{box-sizing:border-box!important;width:100%!important;height:100%!important;min-height:100%!important;max-height:100%!important;}
   .rist.release-world.deck-assets .rist-deck-row.row1{display:flex!important;}

   .rist.release-world.deck-chat .release-footer-region{display:block!important;top:70dvh!important;height:25dvh!important;min-height:0!important;max-height:none!important;}
   .rist.release-world.deck-chat .release-footer-region>.release-footer-stack{box-sizing:border-box!important;width:100%!important;height:25dvh!important;min-height:25dvh!important;max-height:25dvh!important;display:grid!important;grid-template-columns:1fr!important;grid-template-rows:repeat(3,minmax(0,1fr))!important;overflow:hidden!important;}
   .rist.release-world.deck-chat .release-footer-stack>.inline-chat-output{grid-column:1!important;grid-row:2!important;position:relative!important;width:100%!important;height:100%!important;min-height:0!important;max-height:none!important;}
   .rist.release-world.deck-chat .release-footer-stack>.footer-dock{display:contents!important;position:static!important;width:auto!important;height:auto!important;min-height:0!important;max-height:none!important;}
   .rist.release-world.deck-chat .release-footer-stack .home-inline-chat{display:contents!important;position:static!important;width:auto!important;height:auto!important;min-height:0!important;max-height:none!important;}
   .rist.release-world.deck-chat .release-footer-stack .chat-mode-rail{grid-column:1!important;grid-row:1!important;width:100%!important;height:100%!important;min-height:0!important;max-height:none!important;}
   .rist.release-world.deck-chat .release-footer-stack .chat-compose-rail{grid-column:1!important;grid-row:3!important;width:100%!important;height:100%!important;min-height:0!important;max-height:none!important;}
   .rist.release-world.deck-chat #footer-slider,.rist.release-world.deck-chat .site-copyright-notice{display:none!important;}

   .rist.release-world.deck-dice .release-footer-region{display:block!important;top:calc(70dvh + (25dvh / 3))!important;height:calc(25dvh / 3)!important;min-height:0!important;max-height:none!important;}
   .rist.release-world.deck-dice .release-footer-region>.release-footer-stack{box-sizing:border-box!important;width:100%!important;height:100%!important;min-height:0!important;max-height:none!important;display:block!important;overflow:hidden!important;}
   .rist.release-world.deck-dice .inline-chat-output,.rist.release-world.deck-dice .home-inline-chat,.rist.release-world.deck-dice .site-copyright-notice{display:none!important;}
   .rist.release-world.deck-dice .footer-dock{position:static!important;display:block!important;width:100%!important;height:100%!important;min-height:0!important;max-height:none!important;overflow:hidden!important;}
   .rist.release-world.deck-dice #footer-slider{box-sizing:border-box!important;position:relative!important;left:auto!important;right:auto!important;top:auto!important;bottom:auto!important;width:100%!important;height:100%!important;min-height:100%!important;max-height:100%!important;display:block!important;opacity:1!important;visibility:visible!important;pointer-events:auto!important;}
   .rist.release-world.deck-dice #footer-slider .release-footer-track{height:100%!important;min-height:100%!important;max-height:100%!important;}
   .rist.release-world.deck-dice .rist-deck-row.row1,.rist.release-world.deck-dice .rist-deck-row.row3{display:flex!important;}

   .rist.release-world.deck-logs .rist-deck-row{display:flex!important;}

   @media (max-height:640px){
    .rist-section-selector{grid-template-rows:22px minmax(0,1fr) 22px!important}.rist-section-selector>.selector-arrow{height:22px!important}.rist-section-list>button{min-height:26px!important;font-size:8px!important;}
   }
  `;document.head.appendChild(style);
 }

 function buildBulletinFlow(track){
  if(!track||track.querySelector(':scope>.bulletin-flow'))return;
  const originals=[...track.children];const flow=document.createElement('div');flow.className='bulletin-flow';originals.forEach(el=>flow.appendChild(el));
  [...flow.children].map(el=>el.cloneNode(true)).forEach(el=>{el.setAttribute('aria-hidden','true');flow.appendChild(el);});track.appendChild(flow);
 }
 function syncOsMenu(){
  const track=document.querySelector('.world-context-track');const button=document.querySelector('.world-context-menu');const region=document.querySelector('.release-menu-region');if(!track||!button||!region)return;
  buildBulletinFlow(track);region.classList.toggle('rist-os-menu-open',button.getAttribute('aria-pressed')==='true');
 }

 function ensureDeck(){
  const root=document.querySelector('.rist.release-world');const shell=root?.querySelector(':scope>.release-world-shell');if(!root||!shell)return;
  let selector=shell.querySelector(':scope>.rist-section-selector');
  if(!selector){
   selector=document.createElement('aside');selector.className='rist-section-selector';selector.setAttribute('aria-label','Section selector');
   const up=document.createElement('button');up.type='button';up.className='selector-arrow';up.textContent='▲';up.setAttribute('aria-label','Scroll section selector up');
   const list=document.createElement('div');list.className='rist-section-list';
   const down=document.createElement('button');down.type='button';down.className='selector-arrow';down.textContent='▼';down.setAttribute('aria-label','Scroll section selector down');
   up.addEventListener('click',()=>list.scrollBy({top:-Math.max(60,list.clientHeight*.75),behavior:'smooth'}));down.addEventListener('click',()=>list.scrollBy({top:Math.max(60,list.clientHeight*.75),behavior:'smooth'}));
   for(const [key,label] of SECTIONS){const button=document.createElement('button');button.type='button';button.dataset.section=key;button.textContent=label;button.addEventListener('click',()=>selectSection(key));list.appendChild(button);}
   selector.append(up,list,down);shell.appendChild(selector);
  }
  for(let i=1;i<=3;i++)if(!shell.querySelector(`:scope>.rist-deck-row.row${i}`)){const row=document.createElement('div');row.className=`rist-deck-row row${i}`;row.innerHTML='<span class="deck-copy"></span>';shell.appendChild(row);}
  applySection(root,shell);
 }

 function clickAssetFilter(key){
  const wanted=ASSET_LABELS[key];if(!wanted||key==='custom1'||key==='add')return;
  const buttons=[...document.querySelectorAll('.release-public-region .asset-type-tabs button')];
  const match=buttons.find(button=>(button.textContent||'').trim().toLowerCase()===wanted.toLowerCase());match?.click();
 }
 function selectSection(key){selectedSection=key;clickAssetFilter(key);const root=document.querySelector('.rist.release-world');const shell=root?.querySelector(':scope>.release-world-shell');if(root&&shell)applySection(root,shell);}
 function assetNames(){
  const names=[...document.querySelectorAll('.public-assets-items .public-asset-card small,.private-assets-items .hand-card-wrap small,.private-assets-items button small')].map(el=>(el.textContent||'').trim()).filter(Boolean);
  return [...new Set(names)].slice(0,16);
 }
 function diceShorthand(){
  const labels=[...document.querySelectorAll('#footer-slider .die-button[aria-label]')].map(button=>(button.getAttribute('aria-label')||'').replace(/^Roll selected bonus die$/i,'+d5').replace(/^Roll selected penalty die$/i,'-d5').replace(/^Roll\s+/i,'').trim()).filter(Boolean);
  return [...new Set(labels)].join(' · ')||'Dice shorthand';
 }
 function diceResult(){
  const sum=document.querySelector('#footer-slider .sum');const text=(sum?.textContent||'').replace(/\s+/g,' ').trim();return text?`Dice results · ${text}`:'Dice results · no roll yet';
 }
 function setRow(shell,index,text){const copy=shell.querySelector(`:scope>.rist-deck-row.row${index} .deck-copy`);if(copy)copy.textContent=text;}
 function applySection(root,shell){
  root.classList.remove('deck-chat','deck-dice','deck-assets','deck-logs');
  const buttons=[...shell.querySelectorAll('.rist-section-list>button')];buttons.forEach(button=>button.classList.toggle('active',button.dataset.section===selectedSection));
  if(selectedSection==='chat'){
   root.classList.add('deck-chat');setRow(shell,1,'Chat settings');setRow(shell,2,'Chat output');setRow(shell,3,'Chat input');
  }else if(selectedSection==='dice'){
   root.classList.add('deck-dice');setRow(shell,1,`Dice shorthand · ${diceShorthand()}`);setRow(shell,2,'Dice buttons');setRow(shell,3,diceResult());
  }else if(selectedSection==='logs'){
   root.classList.add('deck-logs');setRow(shell,1,'Log names · Roleplay Log · Roll Log');setRow(shell,2,'Log details');setRow(shell,3,'Log sharing options');
  }else{
   root.classList.add('deck-assets');const label=SECTIONS.find(entry=>entry[0]===selectedSection)?.[1]||'Assets';const names=assetNames();setRow(shell,1,names.length?`${label} · ${names.join(' · ')}`:`${label} · asset names`);setRow(shell,2,'Public asset');setRow(shell,3,'Private asset');
  }
  requestAnimationFrame(fixViewer);
 }

 function enhance(){
  ensureAuthorityStyle();document.querySelectorAll('.root-menu-panel,.release-action-menu,#card-library,.asset-slider-stack,.rist-tutorial-shell').forEach(addClose);syncOsMenu();ensureDeck();fixViewer();
 }
 let queued=false;function queue(){if(queued)return;queued=true;requestAnimationFrame(()=>{queued=false;enhance();});}
 function start(){enhance();new MutationObserver(queue).observe(document.body,{childList:true,subtree:true,attributes:true,attributeFilter:['aria-pressed','class']});window.addEventListener('resize',queue,{passive:true});window.addEventListener('orientationchange',()=>setTimeout(queue,120),{passive:true});}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();
