(()=>{
  'use strict';
  /* Selective rollback adapter: load the last pre-2026-09-05 viewer intact. */
  const prior=document.querySelector('script[data-rist-viewer-rollback="2026-09-04"]');
  if(prior)return;
  const script=document.createElement('script');
  script.src='viewer-controller-yesterday.js?v=20260904-map-viewer-rollback-1';
  script.async=false;
  script.dataset.ristViewerRollback='2026-09-04';
  document.head.appendChild(script);
})();
/* Deployment compatibility marker only: .world-bounds>.grid.square */
