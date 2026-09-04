(()=>{
 'use strict';
 const ASSIGN_KEY='rist.roleplay.voice.assignments.v2';
 const LEGACY_ASSIGN_KEY='rist.roleplay.voice.assignments.v1';
 const DEFAULT_KEY='rist.roleplay.voice.default.v2';
 const LEGACY_DEFAULT_KEY='rist.roleplay.voice.default.v1';
 const ENABLED_KEY='rist.roleplay.voice.enabled.v1';
 const DEFAULT_VOICE_NAME='Matthew';
 const KOKORO_MODULE='https://cdn.jsdelivr.net/npm/kokoro-js@1.2.1/+esm';
 const KOKORO_MODEL='onnx-community/Kokoro-82M-v1.0-ONNX';
 const CATEGORY_ORDER=['Robotic','Soft','Warm','Firm','Tough','Rough','Deep','Bright','Elegant','Mysterious','Narrator','Creature'];
 const KOKORO_PRESETS=[
  {id:'kokoro:soft:af_sky',engine:'kokoro',providerVoiceId:'af_sky',name:'Sky',category:'Soft',lang:'en-US',speed:0.94},
  {id:'kokoro:soft:bf_lily',engine:'kokoro',providerVoiceId:'bf_lily',name:'Lily',category:'Soft',lang:'en-GB',speed:0.92},
  {id:'kokoro:warm:af_heart',engine:'kokoro',providerVoiceId:'af_heart',name:'Heart',category:'Warm',lang:'en-US',speed:0.98},
  {id:'kokoro:warm:af_sarah',engine:'kokoro',providerVoiceId:'af_sarah',name:'Sarah',category:'Warm',lang:'en-US',speed:0.98},
  {id:'kokoro:firm:af_kore',engine:'kokoro',providerVoiceId:'af_kore',name:'Kore',category:'Firm',lang:'en-US',speed:0.96},
  {id:'kokoro:firm:bm_george',engine:'kokoro',providerVoiceId:'bm_george',name:'George',category:'Firm',lang:'en-GB',speed:0.94},
  {id:'kokoro:tough:am_fenrir',engine:'kokoro',providerVoiceId:'am_fenrir',name:'Fenrir',category:'Tough',lang:'en-US',speed:0.90},
  {id:'kokoro:tough:am_onyx',engine:'kokoro',providerVoiceId:'am_onyx',name:'Onyx',category:'Tough',lang:'en-US',speed:0.88},
  {id:'kokoro:rough:am_adam',engine:'kokoro',providerVoiceId:'am_adam',name:'Adam',category:'Rough',lang:'en-US',speed:0.90},
  {id:'kokoro:rough:bm_lewis',engine:'kokoro',providerVoiceId:'bm_lewis',name:'Lewis',category:'Rough',lang:'en-GB',speed:0.90},
  {id:'kokoro:deep:am_michael',engine:'kokoro',providerVoiceId:'am_michael',name:'Michael',category:'Deep',lang:'en-US',speed:0.86},
  {id:'kokoro:deep:bm_daniel',engine:'kokoro',providerVoiceId:'bm_daniel',name:'Daniel',category:'Deep',lang:'en-GB',speed:0.86},
  {id:'kokoro:bright:af_nova',engine:'kokoro',providerVoiceId:'af_nova',name:'Nova',category:'Bright',lang:'en-US',speed:1.06},
  {id:'kokoro:bright:am_puck',engine:'kokoro',providerVoiceId:'am_puck',name:'Puck',category:'Bright',lang:'en-US',speed:1.08},
  {id:'kokoro:elegant:bf_emma',engine:'kokoro',providerVoiceId:'bf_emma',name:'Emma',category:'Elegant',lang:'en-GB',speed:0.95},
  {id:'kokoro:elegant:bf_isabella',engine:'kokoro',providerVoiceId:'bf_isabella',name:'Isabella',category:'Elegant',lang:'en-GB',speed:0.94},
  {id:'kokoro:mysterious:af_aoede',engine:'kokoro',providerVoiceId:'af_aoede',name:'Aoede',category:'Mysterious',lang:'en-US',speed:0.86},
  {id:'kokoro:mysterious:bm_fable',engine:'kokoro',providerVoiceId:'bm_fable',name:'Fable',category:'Mysterious',lang:'en-GB',speed:0.86},
  {id:'kokoro:narrator:af_bella',engine:'kokoro',providerVoiceId:'af_bella',name:'Bella',category:'Narrator',lang:'en-US',speed:0.96},
  {id:'kokoro:narrator:bm_george',engine:'kokoro',providerVoiceId:'bm_george',name:'George',category:'Narrator',lang:'en-GB',speed:0.94},
  {id:'kokoro:creature:am_echo',engine:'kokoro',providerVoiceId:'am_echo',name:'Echo',category:'Creature',lang:'en-US',speed:0.78},
  {id:'kokoro:creature:am_fenrir',engine:'kokoro',providerVoiceId:'am_fenrir',name:'Fenrir',category:'Creature',lang:'en-US',speed:0.74}
 ];
 let browserVoices=[];
 let kokoroPromise=null;
 let currentAudio=null;
 let currentUrl='';
 let generation=0;
 const synth=window.speechSynthesis;
 const readJson=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(key)||'')||fallback}catch{return fallback}};
 const writeJson=(key,value)=>{try{localStorage.setItem(key,JSON.stringify(value))}catch{}};
 const norm=value=>String(value||'').trim().toLowerCase();
 const emit=(state,detail={})=>document.dispatchEvent(new CustomEvent('rist:roleplay-voice-status',{detail:{state,...detail}}));
 function refreshVoices(){browserVoices=synth?.getVoices?.()||[];return browserVoices}
 function browserId(voice){return `browser:${voice.voiceURI||voice.name}`}
 function browserEntry(voice){return{id:browserId(voice),engine:'browser',providerVoiceId:voice.voiceURI||voice.name,name:voice.name,category:'Robotic',lang:voice.lang||'',default:!!voice.default,localService:!!voice.localService,voiceURI:voice.voiceURI||voice.name,speed:1}}
 function getVoices(){refreshVoices();return[...browserVoices.map(browserEntry),...KOKORO_PRESETS].sort((a,b)=>CATEGORY_ORDER.indexOf(a.category)-CATEGORY_ORDER.indexOf(b.category)||a.name.localeCompare(b.name))}
 function findBrowser(wanted){refreshVoices();const raw=String(wanted||'').replace(/^browser:/,'');return browserVoices.find(v=>v.voiceURI===raw||v.name===raw)||null}
 function chooseBrowserDefault(){
  refreshVoices();
  const saved=localStorage.getItem(LEGACY_DEFAULT_KEY)||'';
  if(saved){const hit=findBrowser(saved);if(hit)return hit}
  const preferred=[DEFAULT_VOICE_NAME,'Amazon Matthew','Matthew Neural','Samantha','Alex','Google US English','Microsoft Aria','Microsoft David'];
  for(const name of preferred){const hit=browserVoices.find(v=>v.name===name||v.name.includes(name));if(hit)return hit}
  return browserVoices.find(v=>v.default&&/^en(?:-|$)/i.test(v.lang))||browserVoices.find(v=>/^en-US$/i.test(v.lang))||browserVoices.find(v=>/^en(?:-|$)/i.test(v.lang))||browserVoices[0]||null;
 }
 function migratePreference(value){
  if(!value)return'';
  if(String(value).startsWith('kokoro:')||String(value).startsWith('browser:'))return String(value);
  const browser=findBrowser(value);return browser?browserId(browser):String(value);
 }
 function defaultId(){
  const saved=localStorage.getItem(DEFAULT_KEY)||'';
  if(saved)return migratePreference(saved);
  const legacy=localStorage.getItem(LEGACY_DEFAULT_KEY)||'';
  if(legacy){const migrated=migratePreference(legacy);try{localStorage.setItem(DEFAULT_KEY,migrated)}catch{}return migrated}
  const browser=chooseBrowserDefault();const id=browser?browserId(browser):KOKORO_PRESETS.find(v=>v.category==='Narrator')?.id||'';
  if(id)try{localStorage.setItem(DEFAULT_KEY,id)}catch{}
  return id;
 }
 function assignments(){
  const current=readJson(ASSIGN_KEY,null);if(current)return current;
  const legacy=readJson(LEGACY_ASSIGN_KEY,{});const migrated={};for(const[key,value]of Object.entries(legacy))migrated[key]=migratePreference(value);writeJson(ASSIGN_KEY,migrated);return migrated;
 }
 function assignedId(identity){return assignments()[norm(identity)]||defaultId()}
 function getEntry(id){
  const wanted=migratePreference(id);
  const preset=KOKORO_PRESETS.find(v=>v.id===wanted);if(preset)return preset;
  const browser=findBrowser(wanted);return browser?browserEntry(browser):null;
 }
 function cleanSpeech(message){
  const text=String(message?.text||'').trim();if(!text)return'';
  const colon=text.indexOf(':');if(colon>0&&colon<40)return text.slice(colon+1).trim()||text;
  return text;
 }
 function stopAudio(){generation++;synth?.cancel?.();if(currentAudio){try{currentAudio.pause();currentAudio.currentTime=0}catch{}currentAudio=null}if(currentUrl){try{URL.revokeObjectURL(currentUrl)}catch{}currentUrl=''}}
 function speakBrowser(text,entry){
  if(!synth)return false;
  const utter=new SpeechSynthesisUtterance(text);const voice=(entry?findBrowser(entry.id||entry.providerVoiceId):null)||chooseBrowserDefault();
  if(voice){utter.voice=voice;utter.lang=voice.lang||'en-US'}else utter.lang='en-US';
  utter.rate=entry?.speed||1;utter.pitch=1;utter.volume=1;synth.cancel();synth.speak(utter);emit('playing',{engine:'browser',voice:entry?.name||voice?.name||'System default'});return true;
 }
 async function loadKokoro(){
  if(kokoroPromise)return kokoroPromise;
  emit('loading',{engine:'kokoro'});
  kokoroPromise=(async()=>{
   const module=await import(KOKORO_MODULE);
   const device=navigator.gpu?'webgpu':'wasm';
   const dtype=device==='webgpu'?'fp32':'q8';
   const tts=await module.KokoroTTS.from_pretrained(KOKORO_MODEL,{device,dtype});
   emit('ready',{engine:'kokoro',device});return tts;
  })().catch(error=>{kokoroPromise=null;emit('error',{engine:'kokoro',message:error?.message||String(error)});throw error});
  return kokoroPromise;
 }
 async function speakKokoro(text,entry,token){
  try{
   const tts=await loadKokoro();if(token!==generation)return false;
   emit('generating',{engine:'kokoro',voice:entry.name});
   const audio=await tts.generate(text,{voice:entry.providerVoiceId,speed:entry.speed||1});if(token!==generation)return false;
   const blob=audio?.toBlob?.();if(!blob)throw new Error('Kokoro returned no playable audio.');
   currentUrl=URL.createObjectURL(blob);currentAudio=new Audio(currentUrl);
   currentAudio.addEventListener('ended',()=>{if(currentUrl){URL.revokeObjectURL(currentUrl);currentUrl=''}currentAudio=null;emit('idle',{engine:'kokoro'})},{once:true});
   currentAudio.addEventListener('error',()=>emit('error',{engine:'kokoro',message:'Kokoro audio playback failed.'}),{once:true});
   await currentAudio.play();emit('playing',{engine:'kokoro',voice:entry.name});return true;
  }catch(error){
   emit('fallback',{engine:'kokoro',message:error?.message||String(error)});const fallback=browserEntry(chooseBrowserDefault()||{});return speakBrowser(text,fallback);
  }
 }
 function speak(message){
  if(localStorage.getItem(ENABLED_KEY)==='false')return false;
  const text=cleanSpeech(message);if(!text)return false;
  stopAudio();const token=generation;const entry=getEntry(assignedId(message?.identity||message?.speaker||'default'))||getEntry(defaultId());
  if(entry?.engine==='kokoro'){void speakKokoro(text,entry,token);return true}
  return speakBrowser(text,entry);
 }
 function preview(id,text='Welcome to Shaelvien. Your journey begins here.'){
  if(localStorage.getItem(ENABLED_KEY)==='false')setEnabled(true);
  stopAudio();const token=generation;const entry=getEntry(id||defaultId())||getEntry(defaultId());
  if(entry?.engine==='kokoro'){void speakKokoro(text,entry,token);return true}
  return speakBrowser(text,entry);
 }
 function setVoice(identity,voiceId){if(!identity||!getEntry(voiceId))return false;const map=assignments();map[norm(identity)]=migratePreference(voiceId);writeJson(ASSIGN_KEY,map);return true}
 function clearVoice(identity){const map=assignments();delete map[norm(identity)];writeJson(ASSIGN_KEY,map)}
 function setDefault(voiceId){const id=migratePreference(voiceId);if(!getEntry(id))return false;try{localStorage.setItem(DEFAULT_KEY,id)}catch{}const browser=findBrowser(id);if(browser)try{localStorage.setItem(LEGACY_DEFAULT_KEY,browser.voiceURI||browser.name)}catch{}return true}
 function setEnabled(value){try{localStorage.setItem(ENABLED_KEY,value?'true':'false')}catch{}if(!value)stopAudio()}
 function describe(id){const v=getEntry(id||defaultId());return v?{id:v.id,name:v.name,lang:v.lang,voiceURI:v.voiceURI||v.id,engine:v.engine,category:v.category,providerVoiceId:v.providerVoiceId}:null}

 function enhanceStartVoiceSelect(){
  const select=document.querySelector('.rist-game-start select[name="defaultVoice"]');if(!select)return;
  const catalog=getVoices();const signature=catalog.map(v=>v.id).join('|');if(select.dataset.ristVoiceCatalog===signature)return;
  const selected=defaultId();select.replaceChildren();
  const system=document.createElement('option');system.value='';system.textContent='System default';select.appendChild(system);
  for(const category of CATEGORY_ORDER){
   const entries=catalog.filter(v=>v.category===category);if(!entries.length)continue;
   const group=document.createElement('optgroup');group.label=category;
   for(const voice of entries){const option=document.createElement('option');option.value=voice.id;option.textContent=`${voice.name}${voice.lang?` (${voice.lang})`:''}${voice.engine==='kokoro'?' · Kokoro':''}`;if(voice.id===selected)option.selected=true;group.appendChild(option)}
   select.appendChild(group);
  }
  select.dataset.ristVoiceCatalog=signature;
 }
 function installStartVoiceUi(){
  const refresh=()=>requestAnimationFrame(enhanceStartVoiceSelect);
  new MutationObserver(refresh).observe(document.body,{childList:true,subtree:true});
  document.addEventListener('rist:roleplay-voices-changed',refresh);
  document.addEventListener('change',event=>{const select=event.target.closest?.('.rist-game-start select[name="defaultVoice"]');if(!select)return;event.stopImmediatePropagation();if(select.value)setDefault(select.value);preview(select.value)},true);
  document.addEventListener('click',event=>{const button=event.target.closest?.('.rist-game-start [data-action="voice-demo"]');if(!button)return;event.preventDefault();event.stopImmediatePropagation();const select=document.querySelector('.rist-game-start select[name="defaultVoice"]');preview(select?.value||defaultId())},true);
  refresh();
 }
 if(synth){refreshVoices();synth.addEventListener?.('voiceschanged',()=>{refreshVoices();document.dispatchEvent(new CustomEvent('rist:roleplay-voices-changed'))});setTimeout(refreshVoices,250)}
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',installStartVoiceUi,{once:true});else installStartVoiceUi();
 window.RistRoleplayVoice={
  defaultVoiceName:DEFAULT_VOICE_NAME,categories:[...CATEGORY_ORDER],speak,preview,cancel:stopAudio,refresh:refreshVoices,
  getVoices,getDefault:()=>describe(defaultId()),setDefault,setVoice,clearVoice,getVoice:identity=>describe(assignedId(identity)),
  loadKokoro:()=>loadKokoro().then(()=>true),setEnabled,get enabled(){return localStorage.getItem(ENABLED_KEY)!=='false'}
 };
})();
