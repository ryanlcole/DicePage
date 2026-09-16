(()=>{
 'use strict';

 const CONFIG_PATHS=()=>location.pathname.startsWith('/Game/')
  ? ['translation-config.json','/Game/translation-config.json','/translation-config.json']
  : ['/Game/translation-config.json','/translation-config.json'];
 const HOME_SCOPE='.launcher-hub,.rist-start-overlay,#rist-app-home-slider';
 const EXCLUDE_SCOPE=[
  'script','style','noscript','textarea','select','option','[contenteditable="true"]','[translate="no"]','[data-no-ui-translate]',
  '[data-common-source]','[data-roleplay-language]','.chat-message','.message-body','.message-content','.rist-chat-message',
  '[data-chat-message]','[data-user-content]','[data-authored-content]','[data-world-label]','[data-world-name]','[data-asset-name]','[data-card-content]',
  '[data-visible-chat-text]','.rist-themed-chat-copy','.inline-chat-output .dialogue-copy','.rist-ooc-entry .name','.rist-ooc-entry .text',
  '[data-character-name]','.character-name','.sheet-character-name','.world-label','.map-label','.token-label','.sprite-label',
  '.map-asset-card .map-asset-choose strong','.asset-rating-row span','.library-nav-card strong','.library-path-home','.library-card-face strong',
  '.product-card h3','.product-card .product-body>p','.product-price','.worldbuilder-map-surface','.worldbuilder-canvas','.world-map-canvas','.map-canvas','.sprite-preview','.asset-preview'
 ].join(',');
 const ATTRS=['aria-label','aria-description','title','placeholder'];
 const BRAND_ONLY=/^(?:SHAELVIEN|RIST|ReLiC|ReLiCGameMaster|SHAEP|EI|GM|MMO|SRPG)$/i;
 const originals=new WeakMap();
 const lastApplied=new WeakMap();
 const attrOriginals=new WeakMap();
 const attrApplied=new WeakMap();
 const optionOriginals=new WeakMap();
 const optionApplied=new WeakMap();
 const cache=new Map();
 let apiBase='';
 let configPromise=null;
 let running=false;
 let queued=false;
 let observer=null;
 let activeLanguage='English';
 let activeCode='en';
 let activeLocale='en';
 let activeDir='ltr';

 const clean=value=>String(value??'').replace(/\s+/g,' ').trim();
 function state(){
  const base=window.RistUiLanguage?.state?.()||{};
  activeLanguage=String(base.name||activeLanguage||'English');
  activeCode=String(base.code||activeCode||'en');
  activeLocale=String(base.locale||activeLocale||activeCode||'en');
  activeDir=String(base.dir||activeDir||'ltr');
  return {name:activeLanguage,code:activeCode,locale:activeLocale,dir:activeDir};
 }
 function translationCode(){
  const s=state();
  if(s.name==='Cantonese')return 'zh-TW';
  return s.code;
 }
 function appRoot(){return document.getElementById('app')||document.body}
 function isHome(node){return !!node?.parentElement?.closest?.(HOME_SCOPE)}
 function excludedElement(el){return !el||!!el.closest?.(EXCLUDE_SCOPE)}
 function looksLikeUi(text){
  const value=clean(text);
  if(!value||BRAND_ONLY.test(value))return false;
  if(!/[A-Za-z]/.test(value))return false;
  if(/^https?:\/\//i.test(value)||/^[/\\][\w./\\-]+$/.test(value))return false;
  if(/^[-+]?\d+(?:[.,:]\d+)*%?$/.test(value))return false;
  return true;
 }
 function textNodes(){
  const root=appRoot();
  if(!root)return [];
  const out=[];
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode(node){
   const parent=node.parentElement;
   if(!parent||isHome(node)||excludedElement(parent))return NodeFilter.FILTER_REJECT;
   if(!looksLikeUi(node.nodeValue))return NodeFilter.FILTER_REJECT;
   return NodeFilter.FILTER_ACCEPT;
  }});
  let node;
  while((node=walker.nextNode()))out.push(node);
  return out;
 }
 function sourceFor(node){
  const current=node.nodeValue??'';
  if(!originals.has(node))originals.set(node,current);
  else{
   const previousApplied=lastApplied.get(node);
   const original=originals.get(node);
   if(current!==previousApplied&&current!==original)originals.set(node,current);
  }
  return clean(originals.get(node));
 }
 function attributeTargets(){
  const root=appRoot();
  if(!root)return [];
  const out=[];
  const selectors=ATTRS.map(attr=>`[${attr}]`).join(',');
  for(const el of root.querySelectorAll(selectors)){
   if(el.closest(HOME_SCOPE)||excludedElement(el))continue;
   for(const attr of ATTRS){
    if(!el.hasAttribute(attr))continue;
    let originalMap=attrOriginals.get(el);
    if(!originalMap){originalMap={};attrOriginals.set(el,originalMap)}
    let appliedMap=attrApplied.get(el);
    if(!appliedMap){appliedMap={};attrApplied.set(el,appliedMap)}
    const current=el.getAttribute(attr)||'';
    if(!(attr in originalMap))originalMap[attr]=current;
    else if(current!==appliedMap[attr]&&current!==originalMap[attr])originalMap[attr]=current;
    const source=clean(originalMap[attr]);
    if(looksLikeUi(source))out.push({el,attr,source});
   }
  }
  return out;
 }
 function optionTargets(){
  const root=appRoot();
  if(!root)return [];
  const result=[];
  for(const option of root.querySelectorAll('select:not([data-primary-language]):not([data-native-primary-language]):not([data-site-language]) option')){
   const parent=option.parentElement;
   if(!parent||excludedElement(parent))continue;
   const current=option.textContent||'';
   if(!optionOriginals.has(option))optionOriginals.set(option,current);
   else{
    const applied=optionApplied.get(option);
    const original=optionOriginals.get(option);
    if(current!==applied&&current!==original)optionOriginals.set(option,current);
   }
   const source=clean(optionOriginals.get(option));
   const value=clean(option.value);
   if(parent.closest('.map-asset-filters,.upload-location-grid')&&value&&value!=='all'&&source===value)continue;
   if(looksLikeUi(source))result.push({option,source});
  }
  return result;
 }
 function refreshLanguageSelectors(){
  const options=window.RistUiLanguage?.languageOptions?.()||[];
  const lang=state();
  for(const select of document.querySelectorAll('[data-site-language],[data-primary-language],[data-native-primary-language]')){
   if(options.length){
    for(const item of options){
     let option=[...select.options].find(o=>o.value===item.value);
     if(!option){option=document.createElement('option');option.value=item.value;select.appendChild(option)}
     option.textContent=item.label;option.lang=item.locale;option.dir=item.dir;
    }
   }
   if([...select.options].some(o=>o.value===lang.name))select.value=lang.name;
   select.lang=lang.locale||lang.code||'en';
   select.dir=lang.dir||'ltr';
  }
 }
 async function loadConfig(){
  if(apiBase)return apiBase;
  if(configPromise)return configPromise;
  configPromise=(async()=>{
   for(const path of CONFIG_PATHS()){
    try{
     const res=await fetch(path,{cache:'no-store'});
     if(!res.ok)continue;
     const cfg=await res.json();
     const candidate=String(cfg.apiBaseUrl||'').replace(/\/$/,'');
     if(candidate){apiBase=candidate;break}
    }catch{}
   }
   return apiBase;
  })().finally(()=>{configPromise=null});
  return configPromise;
 }
 async function translateMany(values){
  const target=translationCode();
  const unique=[...new Set(values.map(clean).filter(looksLikeUi))];
  const result=new Map();
  if(target==='en'||!unique.length)return result;
  const unresolved=[];
  for(const text of unique){
   const key=target+'\0'+text;
   if(cache.has(key))result.set(text,cache.get(key));
   else unresolved.push(text);
  }
  if(!unresolved.length)return result;
  if(!apiBase)await loadConfig();
  if(!apiBase)return result;
  const token=sessionStorage.getItem('rist.session')||'';
  for(let i=0;i<unresolved.length;i+=80){
   const chunk=unresolved.slice(i,i+80);
   const headers={'content-type':'application/json'};
   if(token)headers.authorization='Bearer '+token;
   try{
    const res=await fetch(apiBase+'/ui/translate',{method:'POST',headers,body:JSON.stringify({sourceLanguageCode:'en',targetLanguageCode:target,texts:chunk})});
    if(!res.ok)continue;
    const data=await res.json();
    for(const item of data.items||[]){
     const source=clean(item?.source);
     const translated=String(item?.text||'');
     if(item?.translated&&source&&translated){
      cache.set(target+'\0'+source,translated);
      result.set(source,translated);
     }
    }
   }catch{}
  }
  return result;
 }
 function restoreEnglish(){
  refreshLanguageSelectors();
  for(const node of textNodes()){
   if(!originals.has(node))continue;
   const original=originals.get(node);
   if(node.nodeValue!==original)node.nodeValue=original;
   lastApplied.delete(node);
  }
  for(const {el,attr} of attributeTargets()){
   const original=attrOriginals.get(el)?.[attr];
   if(original!==undefined&&el.getAttribute(attr)!==original)el.setAttribute(attr,original);
   const applied=attrApplied.get(el);if(applied)delete applied[attr];
  }
  for(const {option} of optionTargets()){
   const original=optionOriginals.get(option);
   if(original!==undefined&&option.textContent!==original)option.textContent=original;
   optionApplied.delete(option);
  }
 }
 function applyDirectionSafety(){
  let style=document.getElementById('rist-sitewide-locale-safety');
  if(!style){style=document.createElement('style');style.id='rist-sitewide-locale-safety';document.head.appendChild(style)}
  style.textContent=`
html[dir="rtl"] .worldbuilder-stage,
html[dir="rtl"] .worldbuilder-map-surface,
html[dir="rtl"] .worldbuilder-canvas,
html[dir="rtl"] .world-map-canvas,
html[dir="rtl"] canvas,
html[dir="rtl"] svg[data-spatial-truth],
html[dir="rtl"] [data-spatial-truth]{direction:ltr;unicode-bidi:isolate}
html[dir="rtl"] code,html[dir="rtl"] pre,html[dir="rtl"] [data-coordinate],html[dir="rtl"] input[type="number"]{direction:ltr;unicode-bidi:isolate}
`;
 }
 async function apply(){
  if(running)return;
  running=true;
  try{
   const s=state();
   refreshLanguageSelectors();
   applyDirectionSafety();
   if(s.code==='en'){
    restoreEnglish();
    return;
   }
   const nodes=textNodes();
   const attrs=attributeTargets();
   const options=optionTargets();
   const sources=[];
   for(const node of nodes)sources.push(sourceFor(node));
   for(const item of attrs)sources.push(item.source);
   for(const item of options)sources.push(item.source);
   const translated=await translateMany(sources);
   for(const node of nodes){
    const source=sourceFor(node);
    const next=translated.get(source);
    if(!next)continue;
    const raw=originals.get(node)??node.nodeValue??'';
    const lead=(raw.match(/^\s*/)||[''])[0];
    const trail=(raw.match(/\s*$/)||[''])[0];
    const value=lead+next+trail;
    if(node.nodeValue!==value)node.nodeValue=value;
    lastApplied.set(node,value);
   }
   for(const {el,attr,source} of attrs){
    const next=translated.get(source);
    if(!next)continue;
    if(el.getAttribute(attr)!==next)el.setAttribute(attr,next);
    let map=attrApplied.get(el);if(!map){map={};attrApplied.set(el,map)}map[attr]=next;
   }
   for(const {option,source} of options){
    const next=translated.get(source);
    if(!next)continue;
    if(option.textContent!==next)option.textContent=next;
    optionApplied.set(option,next);
   }
  }finally{running=false}
 }
 function queueApply(){
  if(queued)return;
  queued=true;
  setTimeout(()=>{queued=false;void apply()},30);
 }
 function startObserver(){
  if(observer||!document.body)return;
  observer=new MutationObserver(mutations=>{
   if(running)return;
   if(mutations.some(m=>m.type==='childList'||m.type==='characterData'||m.type==='attributes'))queueApply();
  });
  observer.observe(document.body,{subtree:true,childList:true,characterData:true,attributes:true,attributeFilter:ATTRS});
 }
 function init(){
  state();
  document.addEventListener('change',event=>{const target=event.target;if(target instanceof HTMLSelectElement&&target.matches('[data-site-language]'))void window.RistUiLanguage?.setLanguage?.(target.value)},true);
  document.addEventListener('rist:ui-language-changed',queueApply);
  window.addEventListener('rist-ui-language-change',queueApply);
  startObserver();
  void loadConfig();
  queueApply();
 }
 window.RistSitewideLanguage={apply,state:()=>state(),refresh:queueApply};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else init();
})();
