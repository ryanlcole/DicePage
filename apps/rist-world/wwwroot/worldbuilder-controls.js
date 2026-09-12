import './worldbuilder-projection.js?v=20260912-parallax-shared-depth-1';
import './rist-card-tiff.js';

window.ristWorld=window.ristWorld||{};

const activeMapCardEntry=()=>{
  try{
    const keys=[];
    for(let i=0;i<localStorage.length;i++){
      const key=localStorage.key(i);
      if(key?.startsWith('rist.mapcard.'))keys.push(key);
    }
    keys.sort();
    const key=keys[0];
    return key?{key,raw:localStorage.getItem(key)}:null;
  }catch{return null;}
};

window.ristWorld.exportCurrentWorld=async()=>{
  try{
    const card=activeMapCardEntry();
    if(!card?.raw)return;
    const parsed=JSON.parse(card.raw);
    const safe=(parsed.MapName||parsed.mapName||'shaelvien-map').replace(/[^a-z0-9_-]+/gi,'-').replace(/^-+|-+$/g,'')||'shaelvien-map';
    await window.ristCardTiff?.exportJson?.(parsed,`${safe}.tiff`);
  }catch(err){console.warn('Card TIFF export failed',err);}
};

window.ristWorld.importCurrentWorld=async()=>{
  try{
    const result=await window.ristCardTiff?.pickAndRead?.();
    if(!result)return;
    if(result.kind==='json'){
      const card=JSON.parse(result.raw);
      const cardId=card.CardId||card.cardId;
      if(!cardId)throw new Error('Card ID missing.');
      localStorage.setItem(`rist.mapcard.${cardId}`,result.raw);
      localStorage.setItem('rist.card.import.reference',`RIST1|${cardId}|${card.ManifestHash||card.manifestHash||''}`);
      location.reload();
      return;
    }
    if(result.kind==='tiff'&&result.token){
      localStorage.setItem('rist.card.import.reference',result.token);
      location.reload();
    }
  }catch(err){console.warn('Card import failed',err);}
};

window.ristWorld.worldBuilderZFramePoint=(element,clientY)=>{
  if(!element)return 0;
  const rect=element.getBoundingClientRect();
  if(rect.height<=0)return 0;
  const t=Math.max(0,Math.min(1,(clientY-rect.top)/rect.height));
  return 50-(t*100);
};
