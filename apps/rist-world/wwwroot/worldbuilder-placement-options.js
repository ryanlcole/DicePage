(()=>{
 'use strict';
 let pending={upperLayer:false,treatment:'normal'};
 window.ristPlacement={
  set(options){pending={upperLayer:!!options?.upperLayer,treatment:['normal','blend','crop'].includes(options?.treatment)?options.treatment:'normal'};},
  consume(){const value=pending;pending={upperLayer:false,treatment:'normal'};return value;}
 };
})();
