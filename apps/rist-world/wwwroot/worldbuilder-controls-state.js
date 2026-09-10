window.ristWorld=window.ristWorld||{};
window.ristWorld.readPublishState=()=>{
  try{return JSON.parse(localStorage.getItem('rist.world.publish.permissions.v1')||'null')||{published:false,owner:'self',active:['self'],saved:[]};}
  catch{return {published:false,owner:'self',active:['self'],saved:[]};}
};
window.ristWorld.writePublishState=state=>{
  try{
    if(state?.published){
      const prior=window.ristWorld.readPublishState?.()||{};
      const cartographer=window.prompt('Cartographer name',state.cartographer||prior.cartographer||'');
      if(cartographer===null)return false;
      const mapTitle=window.prompt('Map name — as the cartographer would have named it',state.mapTitle||prior.mapTitle||'');
      if(mapTitle===null)return false;
      const inGameCreationDate=window.prompt("In-game creation date — use this world's calendar or era",state.inGameCreationDate||prior.inGameCreationDate||'');
      if(inGameCreationDate===null)return false;
      if(!cartographer.trim()||!mapTitle.trim()||!inGameCreationDate.trim()){
        window.alert('Cartographer, map name, and in-game creation date are required to publish this map.');
        return false;
      }
      state.cartographer=cartographer.trim();
      state.mapTitle=mapTitle.trim();
      state.inGameCreationDate=inGameCreationDate.trim();
    }
    localStorage.setItem('rist.world.publish.permissions.v1',JSON.stringify(state));
    return true;
  }catch{return false;}
};
