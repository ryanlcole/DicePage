export function readJsonRows(prefixes){
  const list=Array.isArray(prefixes)?prefixes:[prefixes];
  const rows=[];
  for(let i=0;i<localStorage.length;i++){
    const key=localStorage.key(i);
    if(!key||!list.some(prefix=>key.startsWith(prefix)))continue;
    try{
      const value=JSON.parse(localStorage.getItem(key)||'null');
      if(value&&typeof value==='object')rows.push(value);
    }catch{}
  }
  return rows;
}

export function readJsonValue(key){
  try{return JSON.parse(localStorage.getItem(key)||'null');}
  catch{return null;}
}

export function writeJsonValue(key,value){
  localStorage.setItem(key,JSON.stringify(value));
  return true;
}
