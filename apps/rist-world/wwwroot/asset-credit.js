(()=>{
 const packs={
  'kenney-toon-minis':{name:'Character Minis',creator:'Kenney',origin:'https://kenney.nl/assets/toon-characters',license:'Creative Commons CC0 1.0',licenseUrl:'https://creativecommons.org/publicdomain/zero/1.0/',support:'https://kenney.nl/support'},
  'kenney-isometric-vehicles':{name:'Isometric Vehicles',creator:'Kenney',origin:'https://kenney.nl/assets/isometric-tiles-vehicles',license:'Creative Commons CC0 1.0',licenseUrl:'https://creativecommons.org/publicdomain/zero/1.0/',support:'https://kenney.nl/support'},
  'kenney-board-pieces':{name:'Black Board Pieces',creator:'Kenney',origin:'https://kenney.nl/assets/boardgame-pack',license:'Creative Commons CC0 1.0',licenseUrl:'https://creativecommons.org/publicdomain/zero/1.0/',support:'https://kenney.nl/support'},
  'kenney-runes-grey':{name:'Grey Runes',creator:'Kenney',origin:'https://kenney.nl/assets/rune-pack',license:'Creative Commons CC0 1.0',licenseUrl:'https://creativecommons.org/publicdomain/zero/1.0/',support:'https://kenney.nl/support'},
  'kenney-hex-tiles':{name:'Hexagon Tiles',creator:'Kenney',origin:'https://kenney.nl/assets/hexagon-pack',license:'Creative Commons CC0 1.0',licenseUrl:'https://creativecommons.org/publicdomain/zero/1.0/',support:'https://kenney.nl/support'},
  'kenney-isometric-landscape':{name:'Isometric Landscape',creator:'Kenney',origin:'https://kenney.nl/assets/isometric-tiles-landscape',license:'Creative Commons CC0 1.0',licenseUrl:'https://creativecommons.org/publicdomain/zero/1.0/',support:'https://kenney.nl/support'},
  'kenney-generic-items':{name:'Generic Items',creator:'Kenney',origin:'https://kenney.nl/assets/generic-items',license:'Creative Commons CC0 1.0',licenseUrl:'https://creativecommons.org/publicdomain/zero/1.0/',support:'https://kenney.nl/support'}
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
  const connected=!!sessionStorage.getItem('rist.session');
  const support=pack.support?`<a class="asset-credit-donate" href="${pack.support}" target="_blank" rel="noopener">Donate / Support</a>`:(connected&&pack.creatorDiscord?`<a class="asset-credit-donate" href="${pack.creatorDiscord}" target="_blank" rel="noopener">Creator Discord</a>`:'');
  const o=ensure(),panel=o.querySelector('.asset-credit-panel');
  panel.innerHTML=`<h2>Community Asset</h2><strong class="asset-credit-creator">${pack.creator}</strong><span class="asset-credit-pack">${pack.name}</span><p>This asset is part of a free creator pack used by RIST. Creator and source information travels with the pack.</p><div class="asset-credit-actions"><a href="${pack.origin}" target="_blank" rel="noopener">Asset Origin</a><a href="${pack.licenseUrl}" target="_blank" rel="noopener">${pack.license}</a>${support}</div><button type="button" data-credit-close>Continue</button>`;
  o.hidden=false;
 }
 function idFrom(el){const title=el?.getAttribute('title')||'';const match=title.match(/Kenney\s*•\s*(kenney-[a-z0-9-]+)/i);return match?.[1]?.toLowerCase()||''}
 document.addEventListener('pointerdown',e=>{const tile=e.target.closest('.library-tile');if(!tile)return;const id=idFrom(tile);if(id)show(id)},true);
 window.RistAssetCredit={show,close,packs};
})();
