window.ristWorld=window.ristWorld||{};
window.ristWorld.readPublishState=()=>{
  try{return JSON.parse(localStorage.getItem('rist.world.publish.permissions.v1')||'null')||{published:false,owner:'self',active:['self'],saved:[]};}
  catch{return {published:false,owner:'self',active:['self'],saved:[]};}
};
window.ristWorld.writePublishState=state=>{try{localStorage.setItem('rist.world.publish.permissions.v1',JSON.stringify(state));}catch{}};
