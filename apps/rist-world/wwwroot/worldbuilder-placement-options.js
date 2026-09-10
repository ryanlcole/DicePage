(()=>{
 'use strict';
 let pending={upperLayer:false,upperTier:false,treatment:'normal'};
 const normalizeTreatment=value=>value==='trim'?'crop':(['normal','blend','crop'].includes(value)?value:'normal');
 window.ristPlacement={
  set(options){pending={upperLayer:!!options?.upperLayer,upperTier:!!options?.upperTier,treatment:normalizeTreatment(options?.treatment)};},
  consume(){const value=pending;pending={upperLayer:false,upperTier:false,treatment:'normal'};return value;}
 };
})();
