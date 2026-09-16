(()=>{
 'use strict';
 const ROOT='[data-rist-play-entry]';
 const ATTRS=['aria-label','aria-description','title','placeholder'];
 const originals=new WeakMap();
 const applied=new WeakMap();
 const attrOriginals=new WeakMap();
 let apiBase='';
 let applying=false;
 let queued=false;
 let observer=null;

 const clean=value=>String(value??'').replace(/\s+/g,' ').trim();
 function root(){return document.querySelector(ROOT)}
 function state(){return window.RistUiLanguage?.state?.()||{name:localStorage.getItem('rist.primaryHumanLanguage')||'English',code:'en',locale:'en',dir:'ltr'}}
 function translationCode(language){return language?.name==='Cantonese'?'zh-TW':String(language?.code||'en')}
 function textNodes(){
  const host=root();
  if(!host)return [];
  const out=[];
  const walker=document.createTreeWalker(host,NodeFilter.SHOW_TEXT,{acceptNode(node){
   const parent=node.parentElement;
   if(!parent||parent.closest('script,style,noscript,textarea,input,select,option,[contenteditable="true"]'))return NodeFilter.FILTER_REJECT;
   return clean(node.nodeValue)?NodeFilter.FILTER_ACCEPT:NodeFilter.FILTER_REJECT;
  }});
  let node;
  while((node=walker.nextNode()))out.push(node);
  return out;
 }
 function sourceFor(node){
  const current=node.nodeValue??'';
  if(!originals.has(node))originals.set(node,current);
  else{
   const previous=applied.get(node);
   const original=originals.get(node);
   if(current!==previous&&current!==original)originals.set(node,current);
  }
  return clean(originals.get(node));
 }
 function attributeTargets(){
  const host=root();
  if(!host)return [];
  const targets=[];
  for(const el of [host,...host.querySelectorAll(ATTRS.map(attr=>`[${attr}]`).join(','))]){
   let map=attrOriginals.get(el);
   if(!map){map={};attrOriginals.set(el,map)}
   for(const attr of ATTRS){
    if(!el.hasAttribute?.(attr))continue;
    if(!(attr in map))map[attr]=el.getAttribute(attr)||'';
    const source=clean(map[attr]);
    if(source)targets.push({el,attr,source});
   }
  }
  return targets;
 }
 async function loadApi(){
  if(apiBase)return apiBase;
  for(const path of ['/translation-config.json','/Game/translation-config.json']){
   try{
    const response=await fetch(path,{cache:'no-store'});
    if(!response.ok)continue;
    const config=await response.json();
    const value=String(config.apiBaseUrl||'').replace(/\/$/,'');
    if(value){apiBase=value;break}
   }catch{}
  }
  return apiBase;
 }
 async function translations(values){
  const language=state();
  const target=translationCode(language);
  const unique=[...new Set(values.map(clean).filter(Boolean))];
  const result=new Map();
  if(!unique.length||target==='en')return result;
  if(!apiBase)await loadApi();
  if(!apiBase)return result;
  const token=sessionStorage.getItem('rist.session')||'';
  const headers={'content-type':'application/json'};
  if(token)headers.authorization='Bearer '+token;
  for(let i=0;i<unique.length;i+=80){
   const chunk=unique.slice(i,i+80);
   try{
    const response=await fetch(apiBase+'/ui/translate',{method:'POST',headers,body:JSON.stringify({sourceLanguageCode:'en',targetLanguageCode:target,texts:chunk})});
    if(!response.ok)continue;
    const data=await response.json();
    for(const item of data.items||[]){
     if(item?.translated&&item.source)result.set(clean(item.source),String(item.text||item.source));
    }
   }catch{}
  }
  return result;
 }
 function restore(){
  for(const node of textNodes()){
   if(!originals.has(node))continue;
   const original=originals.get(node);
   if(node.nodeValue!==original)node.nodeValue=original;
   applied.delete(node);
  }
  for(const {el,attr} of attributeTargets()){
   const original=attrOriginals.get(el)?.[attr];
   if(original!==undefined&&el.getAttribute(attr)!==original)el.setAttribute(attr,original);
  }
 }
 async function apply(){
  if(applying)return;
  applying=true;
  try{
   const language=state();
   if(translationCode(language)==='en'){restore();return}
   const nodes=textNodes();
   const attrs=attributeTargets();
   const map=await translations([...nodes.map(sourceFor),...attrs.map(item=>item.source)]);
   for(const node of nodes){
    const source=sourceFor(node),next=map.get(source);
    if(!next)continue;
    const raw=originals.get(node)??node.nodeValue??'';
    const lead=(raw.match(/^\s*/)||[''])[0],trail=(raw.match(/\s*$/)||[''])[0];
    const value=lead+next+trail;
    if(node.nodeValue!==value)node.nodeValue=value;
    applied.set(node,value);
   }
   for(const {el,attr,source} of attrs){const next=map.get(source);if(next&&el.getAttribute(attr)!==next)el.setAttribute(attr,next)}
  }finally{applying=false}
 }
 function queue(){if(queued)return;queued=true;setTimeout(()=>{queued=false;void apply()},20)}
 function init(){
  const host=root();
  if(!host)return;
  document.addEventListener('rist:ui-language-changed',queue);
  window.addEventListener('rist-ui-language-change',queue);
  observer=new MutationObserver(mutations=>{if(!applying&&mutations.some(m=>m.type==='childList'||m.type==='characterData'||m.type==='attributes'))queue()});
  observer.observe(host,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:ATTRS});
  void loadApi();
  queue();
 }
 window.RistPlayEntryLanguage={apply,refresh:queue};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
