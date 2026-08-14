window.ristWorld={
 point:(el,x,y)=>{const r=el.getBoundingClientRect();return[(x-r.left)/r.width,(y-r.top)/r.height]},
 worldPoint:(el,x,y,panX,panY,zoom)=>{
  const r=el.getBoundingClientRect();
  const sx=(x-r.left)/r.width;
  const sy=(y-r.top)/r.height;
  const z=Math.max(Number(zoom)||1,.01);
  return [((sx-.5)/z)+.5-(Number(panX)||0)/(r.width*z),((sy-.5)/z)+.5-(Number(panY)||0)/(r.height*z)];
 },
 dropPoint:(el,x,y,panX,panY,zoom)=>{
  const r=el.getBoundingClientRect();
  const inside=x>=r.left&&x<=r.right&&y>=r.top&&y<=r.bottom;
  if(!inside)return [0,0,0];
  const sx=(x-r.left)/r.width;
  const sy=(y-r.top)/r.height;
  const z=Math.max(Number(zoom)||1,.01);
  return [1,((sx-.5)/z)+.5-(Number(panX)||0)/(r.width*z),((sy-.5)/z)+.5-(Number(panY)||0)/(r.height*z)];
 }
};
