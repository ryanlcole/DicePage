(()=>{
 'use strict';
 const PREF='rist.primaryHumanLanguage';
 const LANGUAGE_CODES={
  English:'en',Spanish:'es',French:'fr',German:'de',Italian:'it',Portuguese:'pt',Polish:'pl',Dutch:'nl',Swedish:'sv',Norwegian:'no',Danish:'da',Finnish:'fi',Russian:'ru',Ukrainian:'uk',Arabic:'ar',Hebrew:'he',Hindi:'hi',Bengali:'bn',Urdu:'ur','Mandarin Chinese':'zh','Cantonese':'zh',Japanese:'ja',Korean:'ko',Vietnamese:'vi',Thai:'th',Indonesian:'id',Malay:'ms',Filipino:'tl',Swahili:'sw',Turkish:'tr',Greek:'el',Czech:'cs',Romanian:'ro',Hungarian:'hu'
 };
 const CODE_NAMES=Object.fromEntries(Object.entries(LANGUAGE_CODES).map(([name,code])=>[code,name]));
 let apiBase='';
 let currentName=localStorage.getItem(PREF)||'English';
 let currentCode=LANGUAGE_CODES[currentName]||'en';
 let applying=false;
 const originals=new WeakMap();
 const translations=new Map();
 const chatTranslations=new Map();
 let observer=null;

 function cleanText(value){return String(value||'').replace(/\s+/g,' ').trim()}
 function roots(){
  const list=[];
  const menu=document.querySelector('.rist-start-overlay');if(menu)list.push(menu);
  const home=document.querySelector('.site-header');if(home){for(const selector of ['.site-header','.hero','.overview','.feature-grid','.ecosystem','.audience-line','.final-cta','footer']){const el=document.querySelector(selector);if(el)list.push(el)}}
  return list;
 }
 function textNodes(root){
  const out=[];const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode(node){const parent=node.parentElement;if(!parent)return NodeFilter.FILTER_REJECT;if(parent.closest('script,style,noscript,textarea,input,select,option,[contenteditable="true"]'))return NodeFilter.FILTER_REJECT;return cleanText(node.nodeValue)?NodeFilter.FILTER_ACCEPT:NodeFilter.FILTER_REJECT}});let node;while((node=walker.nextNode()))out.push(node);return out;
 }
 function sourceFor(node){if(!originals.has(node))originals.set(node,node.nodeValue);return cleanText(originals.get(node))}
 function restore(){for(const root of roots())for(const node of textNodes(root)){if(originals.has(node))node.nodeValue=originals.get(node)}}
 async function loadConfig(){try{const url=location.pathname.startsWith('/Game/')?'translation-config.json':'/translation-config.json';const res=await fetch(url,{cache:'no-store'});if(res.ok){const cfg=await res.json();apiBase=String(cfg.apiBaseUrl||'').replace(/\/$/,'')}}catch{apiBase=''}}
 async function fetchTranslations(texts){
  const unique=[...new Set(texts.map(cleanText).filter(Boolean))];if(!unique.length||!apiBase||currentCode==='en')return new Map();
  const missing=unique.filter(text=>!translations.has(currentCode+'\0'+text));
  for(let i=0;i<missing.length;i+=80){const chunk=missing.slice(i,i+80);try{const res=await fetch(apiBase+'/ui/translate',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({sourceLanguageCode:'en',targetLanguageCode:currentCode,texts:chunk})});if(!res.ok)continue;const data=await res.json();for(const item of data.items||[]){if(item?.translated&&item.source)translations.set(currentCode+'\0'+cleanText(item.source),String(item.text||item.source))}}catch{}}
  const result=new Map();for(const text of unique){const translated=translations.get(currentCode+'\0'+text);if(translated)result.set(text,translated)}return result;
 }
 function syncNativePrimary(){
  const el=document.querySelector('[data-native-primary-language]');if(!el||el.value===currentName)return;
  if([...el.options||[]].some(option=>option.value===currentName)){el.value=currentName;el.dispatchEvent(new Event('change',{bubbles:true}))}
 }
 async function translateChat(text,sourceLanguageCode,targetLanguageCode=currentCode){
  if(!text||!apiBase||sourceLanguageCode===targetLanguageCode)return {text,sourceLanguageCode,targetLanguageCode,cached:true};
  const key=sourceLanguageCode+'\0'+targetLanguageCode+'\0'+text;if(chatTranslations.has(key))return {text:chatTranslations.get(key),sourceLanguageCode,targetLanguageCode,cached:true};
  const token=sessionStorage.getItem('rist.session');if(!token)return {text,sourceLanguageCode,targetLanguageCode,error:'Authentication required'};
  try{const res=await fetch(apiBase+'/chat/translate',{method:'POST',headers:{'content-type':'application/json',authorization:'Bearer '+token},body:JSON.stringify({text,sourceLanguageCode,targetLanguageCode})});if(!res.ok)return {text,sourceLanguageCode,targetLanguageCode,error:'Translation unavailable'};const data=await res.json();if(data?.text)chatTranslations.set(key,String(data.text));return data}catch{return {text,sourceLanguageCode,targetLanguageCode,error:'Translation unavailable'}}
 }
 async function applyCommonRoleplay(){
  const nodes=[...document.querySelectorAll('[data-roleplay-language="Common"] [data-common-source]')];
  for(const node of nodes){
   const source=node.getAttribute('data-common-source')||node.textContent||'';if(!source.trim())continue;
   const container=node.closest('[data-roleplay-language="Common"]');
   const sourceName=container?.getAttribute('data-human-language')||node.getAttribute('data-human-language')||'English';
   const sourceCode=LANGUAGE_CODES[sourceName]||'en';
   if(sourceCode===currentCode){node.textContent=source;node.dataset.commonTranslatedFor=currentCode;continue}
   if(node.dataset.commonTranslatedFor===currentCode)continue;
   const result=await translateChat(source,sourceCode,currentCode);
   if(!result.error&&result.text){node.textContent=result.text;node.dataset.commonTranslatedFor=currentCode}
  }
 }
 async function apply(){
  if(applying)return;applying=true;
  try{
   syncNativePrimary();
   if(currentCode==='en'){restore();document.documentElement.lang='en'}
   else{
    const nodes=[];for(const root of roots())for(const node of textNodes(root))nodes.push(node);
    const map=await fetchTranslations(nodes.map(sourceFor));
    for(const node of nodes){const raw=originals.get(node);const source=cleanText(raw);const translated=map.get(source);if(!translated)continue;const lead=(raw.match(/^\s*/)||[''])[0],trail=(raw.match(/\s*$/)||[''])[0];node.nodeValue=lead+translated+trail}
    document.documentElement.lang=currentCode;
   }
   await applyCommonRoleplay();
  }finally{applying=false}
 }
 async function setLanguage(value){
  const code=LANGUAGE_CODES[value]||String(value||'').toLowerCase();const name=LANGUAGE_CODES[value]?value:(CODE_NAMES[code]||value||'English');
  currentName=name;currentCode=LANGUAGE_CODES[name]||code||'en';localStorage.setItem(PREF,currentName);
  for(const node of document.querySelectorAll('[data-common-translated-for]'))delete node.dataset.commonTranslatedFor;
  document.dispatchEvent(new CustomEvent('rist:ui-language-changed',{detail:{name:currentName,code:currentCode}}));await apply();
 }
 function startObserver(){if(observer)return;let queued=false;observer=new MutationObserver(()=>{if(applying||queued)return;queued=true;queueMicrotask(()=>{queued=false;void apply()})});observer.observe(document.body,{childList:true,subtree:true})}
 async function init(){await loadConfig();await apply();startObserver()}
 window.RistUiLanguage={setLanguage,apply,translateChat,applyCommonRoleplay,state:()=>({name:currentName,code:currentCode,apiBase}),languageCodes:{...LANGUAGE_CODES}};
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else void init();
})();
