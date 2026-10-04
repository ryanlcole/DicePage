(() => {
'use strict';

const query=new URLSearchParams(location.search);
if(window.parent===window||query.get('live-worldbuilder')!=='1'||String(query.get('mode')||'worldbuilder').toLowerCase()==='regiondefiner')return;
if(String(query.get('access')||'view').toLowerCase()!=='edit')return;

const baseApi=window.ShaelvienPrototype;
if(!baseApi)return;

function selectedDepth(){
  const panel=document.querySelector('.spatial-selection-depth-panel:not([hidden])');
  if(!panel)return null;
  const tierText=String(panel.querySelector('[data-depth-tier-label]')?.textContent||'');
  const layerText=String(panel.querySelector('[data-depth-layer-label]')?.textContent||'');
  const tierMatch=tierText.match(/\d+/),layerMatch=layerText.match(/\d+/);
  if(!tierMatch||!layerMatch)return null;
  return{tier:Math.max(0,Number(tierMatch[0])||0),layer:Math.max(0,Number(layerMatch[0])||0)};
}

function getSpatialSelection(){
  const snapshot=baseApi?.getSpatialSelection?.();
  const depth=selectedDepth();
  if(!snapshot||!depth)return snapshot;
  return{
    ...snapshot,
    tierIndex:depth.tier,
    visibleTierIndices:[depth.tier],
    visibleLayerOffsets:[depth.layer]
  };
}

window.ShaelvienPrototype=Object.freeze({
  ...baseApi,
  getSpatialSelection
});
})();
