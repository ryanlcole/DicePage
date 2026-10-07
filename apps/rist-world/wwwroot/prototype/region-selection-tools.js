(()=>{
'use strict';

// Retired compatibility shim.
//
// Region identity is no longer authored by hex/cell painting, crop masks,
// freehand borders, or image-edge tracing. The canonical Region Definer is
// apps/rist-world/wwwroot/prototype/region-volume-tools.js and defines one
// bounded volume over the same World: X min/max, Y min/max, then Z min/max
// Tier. Grid cells remain compatibility/rendering metadata only.
//
// Keep this file at its historical URL so a cached prototype document cannot
// resurrect the removed selector by receiving a 404 and falling back to older
// browser state.
const query=new URLSearchParams(location.search);
if(String(query.get('mode')||'').toLowerCase()==='regiondefiner'){
  const stage=document.getElementById('stage');
  if(stage)stage.dataset.legacyRegionSelection='retired';
}
})();
