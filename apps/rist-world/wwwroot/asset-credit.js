(()=>{
 const creator={
  name:'Kenney',
  about:'Independent game-asset creator known for large, cohesive libraries of free game-development art. These starter packs are published for broad reuse under CC0.',
  website:'https://kenney.nl/',
  support:'https://kenney.nl/support'
 };
 const packs={
  'kenney-toon-minis':{name:'Character Minis',info:'A character-focused starter set suitable for player and NPC miniature-style representations.',origin:'https://kenney.nl/assets/toon-characters',license:'Creative Commons CC0 1.0',licenseUrl:'https://creativecommons.org/publicdomain/zero/1.0/'},
  'kenney-isometric-vehicles':{name:'Isometric Vehicles',info:'An isometric transport set for carts, vehicles, rolling stock, and region-scale movement pieces.',origin:'https://kenney.nl/assets/isometric-tiles-vehicles',license:'Creative Commons CC0 1.0',licenseUrl:'https://creativecommons.org/publicdomain/zero/1.0/'},
  'kenney-board-pieces':{name:'Black Board Pieces',info:'Simple physical-game pieces suited to pawns, meeples, markers, and generic tabletop stand-ins.',origin:'https://kenney.nl/assets/boardgame-pack',license:'Creative Commons CC0 1.0',licenseUrl:'https://creativecommons.org/publicdomain/zero/1.0/'},
  'kenney-runes-grey':{name:'Grey Runes',info:'Compact symbolic marks suited to tokens, chits, status markers, magical identifiers, and counters.',origin:'https://kenney.nl/assets/rune-pack',license:'Creative Commons CC0 1.0',licenseUrl:'https://creativecommons.org/publicdomain/zero/1.0/'},
  'kenney-hex-tiles':{name:'Hexagon Tiles',info:'A modular hex-oriented environment set used as a lightweight starter library for map tiles.',origin:'https://kenney.nl/assets/hexagon-pack',license:'Creative Commons CC0 1.0',licenseUrl:'https://creativecommons.org/publicdomain/zero/1.0/'},
  'kenney-isometric-landscape':{name:'Isometric Landscape',info:'Terrain and scenery pieces for constructing readable fantasy-compatible local environments.',origin:'https://kenney.nl/assets/isometric-tiles-landscape',license:'Creative Commons CC0 1.0',licenseUrl:'https://creativecommons.org/publicdomain/zero/1.0/'},
  'kenney-generic-items':{name:'Generic Items',info:'General-purpose object art for props, inventory-like bits, interactable objects, and miscellaneous table pieces.',origin:'https://kenney.nl/assets/generic-items',license:'Creative Commons CC0 1.0',licenseUrl:'https://creativecommons.org/publicdomain/zero/1.0/'}
 };
 let overlay;
 function ensure(){
  if(overlay&&document.body.contains(overlay))return overlay;
  overlay=document.createElement('div');overlay.className='asset-credit-overlay';overlay.hidden=true;
  overlay.innerHTML='<section class="asset-credit-panel" role="dialog" aria-modal="true" aria-label="Asset creator information"></section>';
  overlay.addEventListener('click',e=>{if(e.target===overlay||e.target.closest('[data-credit-close]'))close()});
  document.body.appendChild(overlay);return overlay;
 }
 function close(){if(overlay)overlay.hidden=true}
 function show(id){
  const pack=packs[id];if(!pack)return;
  const key='rist.asset-credit.seen.'+id;if(sessionStorage.getItem(key)==='1')return;sessionStorage.setItem(key,'1');
  const o=ensure(),panel=o.querySelector('.asset-credit-panel');
  panel.innerHTML=`<h2>Community Asset</h2><strong class="asset-credit-creator">${creator.name}</strong><span class="asset-credit-pack">${pack.name}</span><div class="asset-credit-info"><p><b>Creator:</b> ${creator.about}</p><p><b>Pack:</b> ${pack.info}</p><p><b>License:</b> ${pack.license}</p></div><div class="asset-credit-actions"><a href="${pack.origin}" target="_blank" rel="noopener">Asset Origin</a><a href="${creator.website}" target="_blank" rel="noopener">Creator Info</a><a href="${pack.licenseUrl}" target="_blank" rel="noopener">License</a><a class="asset-credit-donate" href="${creator.support}" target="_blank" rel="noopener">Donate / Support</a></div><button type="button" data-credit-close>Continue</button>`;
  o.hidden=false;
 }
 function idFrom(el){const title=el?.getAttribute('title')||'';const match=title.match(/Kenney\s*•\s*(kenney-[a-z0-9-]+)/i);return match?.[1]?.toLowerCase()||''}
 document.addEventListener('pointerdown',e=>{const tile=e.target.closest('.library-tile');if(!tile)return;const id=idFrom(tile);if(id)show(id)},true);
 window.RistAssetCredit={show,close,packs,creator};
})();
