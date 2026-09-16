(()=>{
 'use strict';

 const PREF='rist.primaryHumanLanguage';
 const LEGACY_PREF='rist_ui_language';

 const LANGUAGE_META={
  English:{code:'en',locale:'en',label:'English',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  Spanish:{code:'es',locale:'es',label:'Español',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  French:{code:'fr',locale:'fr',label:'Français',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  German:{code:'de',locale:'de',label:'Deutsch',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  Italian:{code:'it',locale:'it',label:'Italiano',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  Portuguese:{code:'pt',locale:'pt',label:'Português',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  Polish:{code:'pl',locale:'pl',label:'Polski',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  Dutch:{code:'nl',locale:'nl',label:'Nederlands',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  Swedish:{code:'sv',locale:'sv',label:'Svenska',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  Norwegian:{code:'no',locale:'no',label:'Norsk',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  Danish:{code:'da',locale:'da',label:'Dansk',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  Finnish:{code:'fi',locale:'fi',label:'Suomi',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  Russian:{code:'ru',locale:'ru',label:'Русский',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  Ukrainian:{code:'uk',locale:'uk',label:'Українська',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  Arabic:{code:'ar',locale:'ar',label:'العربية',dir:'rtl',font:'"Noto Sans Arabic","Segoe UI",Tahoma,Arial,sans-serif'},
  Hebrew:{code:'he',locale:'he',label:'עברית',dir:'rtl',font:'"Noto Sans Hebrew","Arial Hebrew",Arial,sans-serif'},
  Hindi:{code:'hi',locale:'hi',label:'हिन्दी',dir:'ltr',font:'"Noto Sans Devanagari","Nirmala UI",system-ui,sans-serif'},
  Bengali:{code:'bn',locale:'bn',label:'বাংলা',dir:'ltr',font:'"Noto Sans Bengali","Nirmala UI",system-ui,sans-serif'},
  Urdu:{code:'ur',locale:'ur',label:'اردو',dir:'rtl',font:'"Noto Nastaliq Urdu","Noto Sans Arabic","Segoe UI",sans-serif'},
  'Mandarin Chinese':{code:'zh',locale:'zh-Hans',label:'普通话（简体中文）',dir:'ltr',font:'"PingFang SC","Microsoft YaHei","Noto Sans SC","Source Han Sans SC",system-ui,sans-serif'},
  Cantonese:{code:'zh',locale:'zh-Hant-HK',label:'粵語',dir:'ltr',font:'"PingFang HK","Microsoft JhengHei","Noto Sans TC",system-ui,sans-serif'},
  Japanese:{code:'ja',locale:'ja',label:'日本語',dir:'ltr',font:'"Hiragino Sans","Yu Gothic","Noto Sans JP",system-ui,sans-serif'},
  Korean:{code:'ko',locale:'ko',label:'한국어',dir:'ltr',font:'"Apple SD Gothic Neo","Malgun Gothic","Noto Sans KR",system-ui,sans-serif'},
  Vietnamese:{code:'vi',locale:'vi',label:'Tiếng Việt',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  Thai:{code:'th',locale:'th',label:'ไทย',dir:'ltr',font:'"Noto Sans Thai","Leelawadee UI",Tahoma,system-ui,sans-serif'},
  Indonesian:{code:'id',locale:'id',label:'Bahasa Indonesia',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  Malay:{code:'ms',locale:'ms',label:'Bahasa Melayu',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  Filipino:{code:'tl',locale:'fil',label:'Filipino',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  Swahili:{code:'sw',locale:'sw',label:'Kiswahili',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  Turkish:{code:'tr',locale:'tr',label:'Türkçe',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  Greek:{code:'el',locale:'el',label:'Ελληνικά',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  Czech:{code:'cs',locale:'cs',label:'Čeština',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  Romanian:{code:'ro',locale:'ro',label:'Română',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'},
  Hungarian:{code:'hu',locale:'hu',label:'Magyar',dir:'ltr',font:'system-ui,-apple-system,"Segoe UI",sans-serif'}
 };
 const LANGUAGE_CODES=Object.fromEntries(Object.entries(LANGUAGE_META).map(([name,meta])=>[name,meta.code]));

 // These labels cover the always-visible home/start chrome. The translation service
 // remains responsible for longer prose, but the core UI now changes immediately
 // even when that service is unavailable.
 const CORE_LABELS={
  Spanish:{'START':'INICIO','Exit':'Salir','Back':'Atrás','Language':'Idioma','Primary language':'Idioma principal','Chat':'Chat','Dice':'Dados','Actors':'Personajes','Editor':'Editor','Custom':'Personalizado'},
  French:{'START':'ACCUEIL','Exit':'Quitter','Back':'Retour','Language':'Langue','Primary language':'Langue principale','Chat':'Discussion','Dice':'Dés','Actors':'Personnages','Editor':'Éditeur','Custom':'Personnalisé'},
  German:{'START':'START','Exit':'Beenden','Back':'Zurück','Language':'Sprache','Primary language':'Hauptsprache','Chat':'Chat','Dice':'Würfel','Actors':'Figuren','Editor':'Editor','Custom':'Benutzerdefiniert'},
  Italian:{'START':'INIZIO','Exit':'Esci','Back':'Indietro','Language':'Lingua','Primary language':'Lingua principale','Chat':'Chat','Dice':'Dadi','Actors':'Personaggi','Editor':'Editor','Custom':'Personalizzato'},
  Portuguese:{'START':'INÍCIO','Exit':'Sair','Back':'Voltar','Language':'Idioma','Primary language':'Idioma principal','Chat':'Chat','Dice':'Dados','Actors':'Personagens','Editor':'Editor','Custom':'Personalizado'},
  Polish:{'START':'START','Exit':'Wyjdź','Back':'Wstecz','Language':'Język','Primary language':'Język główny','Chat':'Czat','Dice':'Kości','Actors':'Postacie','Editor':'Edytor','Custom':'Własne'},
  Dutch:{'START':'START','Exit':'Afsluiten','Back':'Terug','Language':'Taal','Primary language':'Primaire taal','Chat':'Chat','Dice':'Dobbelstenen','Actors':'Personages','Editor':'Editor','Custom':'Aangepast'},
  Swedish:{'START':'START','Exit':'Avsluta','Back':'Tillbaka','Language':'Språk','Primary language':'Primärt språk','Chat':'Chatt','Dice':'Tärningar','Actors':'Karaktärer','Editor':'Redigerare','Custom':'Anpassat'},
  Norwegian:{'START':'START','Exit':'Avslutt','Back':'Tilbake','Language':'Språk','Primary language':'Primærspråk','Chat':'Chat','Dice':'Terninger','Actors':'Figurer','Editor':'Redigerer','Custom':'Egendefinert'},
  Danish:{'START':'START','Exit':'Afslut','Back':'Tilbage','Language':'Sprog','Primary language':'Primært sprog','Chat':'Chat','Dice':'Terninger','Actors':'Figurer','Editor':'Editor','Custom':'Brugerdefineret'},
  Finnish:{'START':'ALOITA','Exit':'Poistu','Back':'Takaisin','Language':'Kieli','Primary language':'Ensisijainen kieli','Chat':'Keskustelu','Dice':'Nopat','Actors':'Hahmot','Editor':'Muokkain','Custom':'Mukautettu'},
  Russian:{'START':'СТАРТ','Exit':'Выход','Back':'Назад','Language':'Язык','Primary language':'Основной язык','Chat':'Чат','Dice':'Кубики','Actors':'Персонажи','Editor':'Редактор','Custom':'Своё'},
  Ukrainian:{'START':'СТАРТ','Exit':'Вийти','Back':'Назад','Language':'Мова','Primary language':'Основна мова','Chat':'Чат','Dice':'Кубики','Actors':'Персонажі','Editor':'Редактор','Custom':'Власне'},
  Arabic:{'START':'البدء','Exit':'خروج','Back':'رجوع','Language':'اللغة','Primary language':'اللغة الأساسية','Chat':'الدردشة','Dice':'النرد','Actors':'الشخصيات','Editor':'المحرر','Custom':'مخصص'},
  Hebrew:{'START':'התחלה','Exit':'יציאה','Back':'חזרה','Language':'שפה','Primary language':'שפה ראשית','Chat':'צ׳אט','Dice':'קוביות','Actors':'דמויות','Editor':'עורך','Custom':'מותאם אישית'},
  Hindi:{'START':'आरंभ','Exit':'बाहर जाएँ','Back':'वापस','Language':'भाषा','Primary language':'प्राथमिक भाषा','Chat':'चैट','Dice':'पासे','Actors':'पात्र','Editor':'संपादक','Custom':'कस्टम'},
  Bengali:{'START':'শুরু','Exit':'বের হন','Back':'ফিরে যান','Language':'ভাষা','Primary language':'প্রধান ভাষা','Chat':'চ্যাট','Dice':'পাশা','Actors':'চরিত্র','Editor':'সম্পাদক','Custom':'কাস্টম'},
  Urdu:{'START':'شروع','Exit':'باہر جائیں','Back':'واپس','Language':'زبان','Primary language':'بنیادی زبان','Chat':'چیٹ','Dice':'پاسا','Actors':'کردار','Editor':'ایڈیٹر','Custom':'حسبِ ضرورت'},
  'Mandarin Chinese':{'START':'开始','Exit':'退出','Back':'返回','Language':'语言','Primary language':'主要语言','Chat':'聊天','Dice':'骰子','Actors':'角色','Editor':'编辑器','Custom':'自定义'},
  Cantonese:{'START':'開始','Exit':'離開','Back':'返回','Language':'語言','Primary language':'主要語言','Chat':'聊天','Dice':'骰仔','Actors':'角色','Editor':'編輯器','Custom':'自訂'},
  Japanese:{'START':'スタート','Exit':'終了','Back':'戻る','Language':'言語','Primary language':'メイン言語','Chat':'チャット','Dice':'ダイス','Actors':'キャラクター','Editor':'エディター','Custom':'カスタム'},
  Korean:{'START':'시작','Exit':'종료','Back':'뒤로','Language':'언어','Primary language':'기본 언어','Chat':'채팅','Dice':'주사위','Actors':'캐릭터','Editor':'편집기','Custom':'사용자 지정'},
  Vietnamese:{'START':'BẮT ĐẦU','Exit':'Thoát','Back':'Quay lại','Language':'Ngôn ngữ','Primary language':'Ngôn ngữ chính','Chat':'Trò chuyện','Dice':'Xúc xắc','Actors':'Nhân vật','Editor':'Trình chỉnh sửa','Custom':'Tùy chỉnh'},
  Thai:{'START':'เริ่ม','Exit':'ออก','Back':'ย้อนกลับ','Language':'ภาษา','Primary language':'ภาษาหลัก','Chat':'แชท','Dice':'ลูกเต๋า','Actors':'ตัวละคร','Editor':'ตัวแก้ไข','Custom':'กำหนดเอง'},
  Indonesian:{'START':'MULAI','Exit':'Keluar','Back':'Kembali','Language':'Bahasa','Primary language':'Bahasa utama','Chat':'Obrolan','Dice':'Dadu','Actors':'Karakter','Editor':'Editor','Custom':'Kustom'},
  Malay:{'START':'MULA','Exit':'Keluar','Back':'Kembali','Language':'Bahasa','Primary language':'Bahasa utama','Chat':'Sembang','Dice':'Dadu','Actors':'Watak','Editor':'Editor','Custom':'Tersuai'},
  Filipino:{'START':'SIMULA','Exit':'Lumabas','Back':'Bumalik','Language':'Wika','Primary language':'Pangunahing wika','Chat':'Chat','Dice':'Dais','Actors':'Mga Tauhan','Editor':'Editor','Custom':'Pasadya'},
  Swahili:{'START':'ANZA','Exit':'Toka','Back':'Rudi','Language':'Lugha','Primary language':'Lugha kuu','Chat':'Gumzo','Dice':'Kete','Actors':'Wahusika','Editor':'Kihariri','Custom':'Maalum'},
  Turkish:{'START':'BAŞLA','Exit':'Çıkış','Back':'Geri','Language':'Dil','Primary language':'Ana dil','Chat':'Sohbet','Dice':'Zar','Actors':'Karakterler','Editor':'Düzenleyici','Custom':'Özel'},
  Greek:{'START':'ΕΝΑΡΞΗ','Exit':'Έξοδος','Back':'Πίσω','Language':'Γλώσσα','Primary language':'Κύρια γλώσσα','Chat':'Συνομιλία','Dice':'Ζάρια','Actors':'Χαρακτήρες','Editor':'Επεξεργαστής','Custom':'Προσαρμοσμένο'},
  Czech:{'START':'START','Exit':'Ukončit','Back':'Zpět','Language':'Jazyk','Primary language':'Hlavní jazyk','Chat':'Chat','Dice':'Kostky','Actors':'Postavy','Editor':'Editor','Custom':'Vlastní'},
  Romanian:{'START':'START','Exit':'Ieșire','Back':'Înapoi','Language':'Limbă','Primary language':'Limba principală','Chat':'Chat','Dice':'Zaruri','Actors':'Personaje','Editor':'Editor','Custom':'Personalizat'},
  Hungarian:{'START':'INDÍTÁS','Exit':'Kilépés','Back':'Vissza','Language':'Nyelv','Primary language':'Elsődleges nyelv','Chat':'Csevegés','Dice':'Kockák','Actors':'Karakterek','Editor':'Szerkesztő','Custom':'Egyéni'}
 };

 const aliases=new Map();
 for(const [name,meta] of Object.entries(LANGUAGE_META)){
  aliases.set(name.toLowerCase(),name);
  aliases.set(meta.label.toLowerCase(),name);
  aliases.set(meta.locale.toLowerCase(),name);
  if(!aliases.has(meta.code.toLowerCase()))aliases.set(meta.code.toLowerCase(),name);
 }
 aliases.set('mandarin','Mandarin Chinese');
 aliases.set('chinese','Mandarin Chinese');
 aliases.set('simplified chinese','Mandarin Chinese');
 aliases.set('zh-cn','Mandarin Chinese');
 aliases.set('zh-hans','Mandarin Chinese');
 aliases.set('cantonese chinese','Cantonese');
 aliases.set('zh-hk','Cantonese');
 aliases.set('zh-hant-hk','Cantonese');

 let apiBase='';
 let configPromise=null;
 let currentName=normalizeLanguage(localStorage.getItem(PREF)||localStorage.getItem(LEGACY_PREF)||'English');
 let currentCode=LANGUAGE_META[currentName].code;
 let applying=false;
 const originals=new WeakMap();
 const translations=new Map();
 const chatTranslations=new Map();
 let observer=null;

 function normalizeLanguage(value){
  const raw=String(value||'').trim();
  if(LANGUAGE_META[raw])return raw;
  return aliases.get(raw.toLowerCase())||'English';
 }
 function metaFor(value){return LANGUAGE_META[normalizeLanguage(value)]||LANGUAGE_META.English}
 function languageOptions(){return Object.entries(LANGUAGE_META).map(([value,meta])=>({value,label:meta.label,code:meta.code,locale:meta.locale,dir:meta.dir}))}
 function cleanText(value){return String(value||'').replace(/\s+/g,' ').trim()}
 function coreTranslation(text){
  const source=cleanText(text);
  return CORE_LABELS[currentName]?.[source]||null;
 }
 function roots(){
  const list=[];
  const add=el=>{if(el&&!list.includes(el))list.push(el)};
  add(document.querySelector('.rist-start-overlay'));
  add(document.querySelector('.launcher-hub'));
  add(document.querySelector('#rist-app-home-slider'));
  const publicHome=document.querySelector('.site-header');
  if(publicHome){
   for(const selector of ['.site-header','.relic-story-banner','.hero','.overview','.feature-grid','.ecosystem','.audience-line','.final-cta','footer'])add(document.querySelector(selector));
  }
  return list;
 }
 function textNodes(root){
  const out=[];
  const walker=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode(node){
   const parent=node.parentElement;
   if(!parent)return NodeFilter.FILTER_REJECT;
   if(parent.closest('script,style,noscript,textarea,input,select,option,[contenteditable="true"]'))return NodeFilter.FILTER_REJECT;
   return cleanText(node.nodeValue)?NodeFilter.FILTER_ACCEPT:NodeFilter.FILTER_REJECT
  }});
  let node;
  while((node=walker.nextNode()))out.push(node);
  return out;
 }
 function sourceFor(node){if(!originals.has(node))originals.set(node,node.nodeValue);return cleanText(originals.get(node))}
 function restore(){for(const root of roots())for(const node of textNodes(root)){if(originals.has(node))node.nodeValue=originals.get(node)}}
 function applyLocalePresentation(){
  const meta=metaFor(currentName);
  const html=document.documentElement;
  html.lang=meta.locale;
  html.dir=meta.dir;
  html.dataset.uiLanguage=meta.locale;
  html.dataset.uiDirection=meta.dir;
  html.style.setProperty('--rist-ui-font',meta.font);
  if(document.body){
   document.body.dir=meta.dir;
   document.body.dataset.uiLanguage=meta.locale;
  }
  let style=document.getElementById('rist-ui-locale-style');
  if(!style){
   style=document.createElement('style');
   style.id='rist-ui-locale-style';
   document.head.appendChild(style);
  }
  style.textContent='body,button,input,select,textarea{font-family:var(--rist-ui-font,system-ui,-apple-system,"Segoe UI",sans-serif)}';
 }
 async function loadConfig(){
  if(apiBase)return apiBase;
  if(configPromise)return configPromise;
  configPromise=(async()=>{
   const urls=location.pathname.startsWith('/Game/')?['translation-config.json','/Game/translation-config.json','/translation-config.json']:['/Game/translation-config.json','/translation-config.json'];
   for(const url of urls){
    try{
     const res=await fetch(url,{cache:'no-store'});
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
 async function fetchTranslations(texts){
  const unique=[...new Set(texts.map(cleanText).filter(Boolean))];
  if(!unique.length||currentCode==='en')return new Map();
  const result=new Map();
  const unresolved=[];
  for(const text of unique){
   const local=coreTranslation(text);
   if(local){result.set(text,local);continue}
   const cached=translations.get(currentCode+'\0'+text);
   if(cached){result.set(text,cached);continue}
   unresolved.push(text);
  }
  if(!unresolved.length)return result;
  if(!apiBase)await loadConfig();
  if(!apiBase)return result;
  for(let i=0;i<unresolved.length;i+=80){
   const chunk=unresolved.slice(i,i+80);
   try{
    const res=await fetch(apiBase+'/ui/translate',{method:'POST',headers:{'content-type':'application/json'},body:JSON.stringify({sourceLanguageCode:'en',targetLanguageCode:currentCode,texts:chunk})});
    if(!res.ok)continue;
    const data=await res.json();
    for(const item of data.items||[]){
     if(item?.translated&&item.source)translations.set(currentCode+'\0'+cleanText(item.source),String(item.text||item.source));
    }
   }catch{}
  }
  for(const text of unresolved){
   const translated=translations.get(currentCode+'\0'+text);
   if(translated)result.set(text,translated);
  }
  return result;
 }
 function syncNativePrimary(){
  const el=document.querySelector('[data-native-primary-language]');
  if(!el||el.value===currentName)return;
  if([...el.options||[]].some(option=>option.value===currentName)){
   el.value=currentName;
   el.dispatchEvent(new Event('change',{bubbles:true}));
  }
 }
 function refreshLanguageSelectors(){
  for(const el of document.querySelectorAll('[data-primary-language],[data-native-primary-language]')){
   for(const option of el.options||[]){
    const meta=LANGUAGE_META[option.value];
    if(meta){
     option.textContent=meta.label;
     option.lang=meta.locale;
     option.dir=meta.dir;
    }
   }
   if(el.value!==currentName&&[...el.options||[]].some(option=>option.value===currentName))el.value=currentName;
   el.lang=metaFor(currentName).locale;
   el.dir=metaFor(currentName).dir;
  }
 }
 async function translateChat(text,sourceLanguageCode,targetLanguageCode=currentCode){
  if(!text||sourceLanguageCode===targetLanguageCode)return {text,sourceLanguageCode,targetLanguageCode,cached:true};
  if(!apiBase)await loadConfig();
  if(!apiBase)return {text,sourceLanguageCode,targetLanguageCode,error:'Translation unavailable'};
  const key=sourceLanguageCode+'\0'+targetLanguageCode+'\0'+text;
  if(chatTranslations.has(key))return {text:chatTranslations.get(key),sourceLanguageCode,targetLanguageCode,cached:true};
  const token=sessionStorage.getItem('rist.session');
  if(!token)return {text,sourceLanguageCode,targetLanguageCode,error:'Authentication required'};
  try{
   const res=await fetch(apiBase+'/chat/translate',{method:'POST',headers:{'content-type':'application/json',authorization:'Bearer '+token},body:JSON.stringify({text,sourceLanguageCode,targetLanguageCode})});
   if(!res.ok)return {text,sourceLanguageCode,targetLanguageCode,error:'Translation unavailable'};
   const data=await res.json();
   if(data?.text)chatTranslations.set(key,String(data.text));
   return data;
  }catch{return {text,sourceLanguageCode,targetLanguageCode,error:'Translation unavailable'}}
 }
 async function applyCommonRoleplay(){
  const nodes=[...document.querySelectorAll('[data-roleplay-language="Common"] [data-common-source]')];
  for(const node of nodes){
   const source=node.getAttribute('data-common-source')||node.textContent||'';
   if(!source.trim())continue;
   const container=node.closest('[data-roleplay-language="Common"]');
   const sourceName=container?.getAttribute('data-human-language')||node.getAttribute('data-human-language')||'English';
   const sourceCode=LANGUAGE_CODES[normalizeLanguage(sourceName)]||'en';
   if(sourceCode===currentCode){node.textContent=source;node.dataset.commonTranslatedFor=currentCode;continue}
   if(node.dataset.commonTranslatedFor===currentCode)continue;
   const result=await translateChat(source,sourceCode,currentCode);
   if(!result.error&&result.text){node.textContent=result.text;node.dataset.commonTranslatedFor=currentCode}
  }
 }
 async function apply(){
  if(applying)return;
  applying=true;
  try{
   applyLocalePresentation();
   syncNativePrimary();
   refreshLanguageSelectors();
   if(currentCode==='en'){
    restore();
   }else{
    const nodes=[];
    for(const root of roots())for(const node of textNodes(root))nodes.push(node);
    const map=await fetchTranslations(nodes.map(sourceFor));
    for(const node of nodes){
     const raw=originals.get(node);
     const source=cleanText(raw);
     const translated=map.get(source);
     if(!translated)continue;
     const lead=(raw.match(/^\s*/)||[''])[0],trail=(raw.match(/\s*$/)||[''])[0];
     node.nodeValue=lead+translated+trail;
    }
   }
   await applyCommonRoleplay();
  }finally{applying=false}
 }
 async function setLanguage(value){
  currentName=normalizeLanguage(value);
  currentCode=LANGUAGE_META[currentName].code;
  localStorage.setItem(PREF,currentName);
  localStorage.setItem(LEGACY_PREF,currentName);
  applyLocalePresentation();
  refreshLanguageSelectors();
  for(const node of document.querySelectorAll('[data-common-translated-for]'))delete node.dataset.commonTranslatedFor;
  const detail={name:currentName,code:currentCode,locale:LANGUAGE_META[currentName].locale,dir:LANGUAGE_META[currentName].dir,label:LANGUAGE_META[currentName].label};
  document.dispatchEvent(new CustomEvent('rist:ui-language-changed',{detail}));
  window.dispatchEvent(new CustomEvent('rist-ui-language-change',{detail:{language:currentName,...detail}}));
  await apply();
 }
 function handleLanguageControlChange(event){
  const target=event.target;
  if(!(target instanceof HTMLSelectElement))return;
  if(!target.matches('[data-primary-language],[data-native-primary-language]'))return;
  const next=normalizeLanguage(target.value);
  if(next!==currentName)void setLanguage(next);
 }
 function startObserver(){
  if(observer)return;
  let queued=false;
  observer=new MutationObserver(()=>{
   if(applying||queued)return;
   queued=true;
   queueMicrotask(()=>{queued=false;void apply()});
  });
  observer.observe(document.body,{childList:true,subtree:true});
 }
 async function init(){
  document.addEventListener('change',handleLanguageControlChange,true);
  applyLocalePresentation();
  await apply();
  startObserver();
  const detail={name:currentName,code:currentCode,locale:LANGUAGE_META[currentName].locale,dir:LANGUAGE_META[currentName].dir,label:LANGUAGE_META[currentName].label};
  document.dispatchEvent(new CustomEvent('rist:ui-language-changed',{detail}));
  window.dispatchEvent(new CustomEvent('rist-ui-language-change',{detail:{language:currentName,...detail}}));
  void loadConfig();
 }
 window.RistUiLanguage={
  setLanguage,
  apply,
  translateChat,
  applyCommonRoleplay,
  normalizeLanguage,
  languageOptions,
  metaFor,
  state:()=>({name:currentName,code:currentCode,apiBase,...metaFor(currentName)}),
  languageCodes:{...LANGUAGE_CODES}
 };
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init,{once:true});else void init();
})();
