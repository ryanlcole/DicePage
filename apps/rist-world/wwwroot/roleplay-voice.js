(()=>{
 'use strict';
 const ASSIGN_KEY='rist.roleplay.voice.assignments.v2';
 const DEFAULT_KEY='rist.roleplay.voice.default.v2';
 const ENABLED_KEY='rist.roleplay.voice.enabled.v1';
 const KOKORO_MODULE='https://cdn.jsdelivr.net/npm/kokoro-js@1.2.1/+esm';
 const KOKORO_MODEL='onnx-community/Kokoro-82M-v1.0-ONNX';
 const CATEGORY_ORDER=['Robotic','Soft','Warm','Firm','Tough','Rough','Deep','Bright','Elegant','Mysterious','Narrator','Creature'];
 const KOKORO_PRESETS=[
  {id:'kokoro:soft:af_sky',engine:'kokoro',providerVoiceId:'af_sky',name:'Sky',category:'Soft',lang:'en-US',speed:.94},
  {id:'kokoro:soft:bf_lily',engine:'kokoro',providerVoiceId:'bf_lily',name:'Lily',category:'Soft',lang:'en-GB',speed:.92},
  {id:'kokoro:warm:af_heart',engine:'kokoro',providerVoiceId:'af_heart',name:'Heart',category:'Warm',lang:'en-US',speed:.98},
  {id:'kokoro:warm:af_sarah',engine:'kokoro',providerVoiceId:'af_sarah',name:'Sarah',category:'Warm',lang:'en-US',speed:.98},
  {id:'kokoro:firm:af_kore',engine:'kokoro',providerVoiceId:'af_kore',name:'Kore',category:'Firm',lang:'en-US',speed:.96},
  {id:'kokoro:firm:bm_george',engine:'kokoro',providerVoiceId:'bm_george',name:'George',category:'Firm',lang:'en-GB',speed:.94},
  {id:'kokoro:tough:am_fenrir',engine:'kokoro',providerVoiceId:'am_fenrir',name:'Fenrir',category:'Tough',lang:'en-US',speed:.90},
  {id:'kokoro:tough:am_onyx',engine:'kokoro',providerVoiceId:'am_onyx',name:'Onyx',category:'Tough',lang:'en-US',speed:.88},
  {id:'kokoro:rough:am_adam',engine:'kokoro',providerVoiceId:'am_adam',name:'Adam',category:'Rough',lang:'en-US',speed:.90},
  {id:'kokoro:rough:bm_lewis',engine:'kokoro',providerVoiceId:'bm_lewis',name:'Lewis',category:'Rough',lang:'en-GB',speed:.90},
  {id:'kokoro:deep:am_michael',engine:'kokoro',providerVoiceId:'am_michael',name:'Michael',category:'Deep',lang:'en-US',speed:.86},
  {id:'kokoro:deep:bm_daniel',engine:'kokoro',providerVoiceId:'bm_daniel',name:'Daniel',category:'Deep',lang:'en-GB',speed:.86},
  {id:'kokoro:bright:af_nova',engine:'kokoro',providerVoiceId:'af_nova',name:'Nova',category:'Bright',lang:'en-US',speed:1.06},
  {id:'kokoro:bright:am_puck',engine:'kokoro',providerVoiceId:'am_puck',name:'Puck',category:'Bright',lang:'en-US',speed:1.08},
  {id:'kokoro:elegant:bf_emma',engine:'kokoro',providerVoiceId:'bf_emma',name:'Emma',category:'Elegant',lang:'en-GB',speed:.95},
  {id:'kokoro:elegant:bf_isabella',engine:'kokoro',providerVoiceId:'bf_isabella',name:'Isabella',category:'Elegant',lang:'en-GB',speed:.94},
  {id:'kokoro:mysterious:af_aoede',engine:'kokoro',providerVoiceId:'af_aoede',name:'Aoede',category:'Mysterious',lang:'en-US',speed:.86},
  {id:'kokoro:mysterious:bm_fable',engine:'kokoro',providerVoiceId:'bm_fable',name:'Fable',category:'Mysterious',lang:'en-GB',speed:.86},
  {id:'kokoro:narrator:af_bella',engine:'kokoro',providerVoiceId:'af_bella',name:'Bella',category:'Narrator',lang:'en-US',speed:.96},
  {id:'kokoro:narrator:bm_george',engine:'kokoro',providerVoiceId:'bm_george',name:'George',category:'Narrator',lang:'en-GB',speed:.94},
  {id:'kokoro:creature:am_echo',engine:'kokoro',providerVoiceId:'am_echo',name:'Echo',category:'Creature',lang:'en-US',speed:.78},
  {id:'kokoro:creature:am_fenrir',engine:'kokoro',providerVoiceId:'am_fenrir',name:'Fenrir',category:'Creature',lang:'en-US',speed:.74}
 ];
 const synth=window.speechSynthesis;
 let browserVoices=[];
 let browserVoicesLoaded=false;
 let kokoroPromise=null;
 let currentAudio=null;
 let currentUrl='';
 let generation=0;
 const norm=v=>String(v||'').trim().toLowerCase();
 const readJson=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(key)||'')||fallback}catch{return fallback}};
 const writeJson=(key,value)=>{try{localStorage.setItem(key,JSON.stringify(value))}catch{}};
 const emit=(state,detail={})=>document.dispatchEvent(new CustomEvent('rist:roleplay-voice-status',{detail:{state,...detail}}));
 function catalog(){return[{id:'',engine:'browser',name:'System default',category:'Robotic'},...KOKORO_PRESETS.map(v=>({...v}))]}
 function refreshVoices(){browserVoices=synth?.getVoices?.()||[];browserVoicesLoaded=true;return browserVoices}
 function ensureBrowserVoices(){return browserVoicesLoaded?browserVoices:refreshVoices()}
 function browserId(v){return `browser:${v.voiceURI||v.name}`}
 function browserEntry(v){return{id:browserId(v),engine:'browser',providerVoiceId:v.voiceURI||v.name,name:v.name,category:'Robotic',lang:v.lang||'',voiceURI:v.voiceURI||v.name,speed:1}}
 function findBrowser(id){const raw=String(id||'').replace(/^browser:/,'');return ensureBrowserVoices().find(v=>v.voiceURI===raw||v.name===raw)||null}
 function defaultId(){return localStorage.getItem(DEFAULT_KEY)||''}
 function assignments(){return readJson(ASSIGN_KEY,{})}
 function assignedId(identity){return assignments()[norm(identity)]??defaultId()}
 function getEntry(id,resolveBrowser=false){const wanted=String(id||'');const preset=KOKORO_PRESETS.find(v=>v.id===wanted);if(preset)return preset;if(!wanted)return{id:'',engine:'browser',name:'System default',category:'Robotic',speed:1};if(wanted.startsWith('browser:')){if(!resolveBrowser)return{id:wanted,engine:'browser',name:wanted.slice(8)||'System voice',category:'Robotic',speed:1};const v=findBrowser(wanted);return v?browserEntry(v):{id:'',engine:'browser',name:'System default',category:'Robotic',speed:1}}return null}
 function cleanSpeech(message){const text=String(message?.text||'').trim();if(!text)return'';const colon=text.indexOf(':');return colon>0&&colon<40?(text.slice(colon+1).trim()||text):text}
 function stopAudio(){generation++;synth?.cancel?.();if(currentAudio){try{currentAudio.pause();currentAudio.currentTime=0}catch{}currentAudio=null}if(currentUrl){try{URL.revokeObjectURL(currentUrl)}catch{}currentUrl=''}}
 function chooseBrowserDefault(){const voices=ensureBrowserVoices();return voices.find(v=>v.default&&/^en(?:-|$)/i.test(v.lang))||voices.find(v=>/^en-US$/i.test(v.lang))||voices.find(v=>/^en(?:-|$)/i.test(v.lang))||voices[0]||null}
 function speakBrowser(text,entry){if(!synth)return false;const utter=new SpeechSynthesisUtterance(text);const voice=entry?.id?.startsWith('browser:')?findBrowser(entry.id):chooseBrowserDefault();if(voice){utter.voice=voice;utter.lang=voice.lang||'en-US'}else utter.lang='en-US';utter.rate=entry?.speed||1;synth.cancel();synth.speak(utter);emit('playing',{engine:'browser',voice:voice?.name||'System default'});return true}
 async function loadKokoro(){if(kokoroPromise)return kokoroPromise;emit('loading',{engine:'kokoro'});kokoroPromise=(async()=>{const module=await import(KOKORO_MODULE);const device=navigator.gpu?'webgpu':'wasm';const dtype=device==='webgpu'?'fp32':'q8';const tts=await module.KokoroTTS.from_pretrained(KOKORO_MODEL,{device,dtype});emit('ready',{engine:'kokoro',device});return tts})().catch(error=>{kokoroPromise=null;emit('error',{engine:'kokoro',message:error?.message||String(error)});throw error});return kokoroPromise}
 async function speakKokoro(text,entry,token){try{const tts=await loadKokoro();if(token!==generation)return false;emit('generating',{engine:'kokoro',voice:entry.name});const audio=await tts.generate(text,{voice:entry.providerVoiceId,speed:entry.speed||1});if(token!==generation)return false;const blob=audio?.toBlob?.();if(!blob)throw new Error('Kokoro returned no playable audio.');currentUrl=URL.createObjectURL(blob);currentAudio=new Audio(currentUrl);currentAudio.addEventListener('ended',()=>{if(currentUrl){URL.revokeObjectURL(currentUrl);currentUrl=''}currentAudio=null;emit('idle',{engine:'kokoro'})},{once:true});await currentAudio.play();emit('playing',{engine:'kokoro',voice:entry.name});return true}catch(error){emit('fallback',{engine:'kokoro',message:error?.message||String(error)});return speakBrowser(text,{id:'',engine:'browser',speed:1})}}
 function speak(message){if(localStorage.getItem(ENABLED_KEY)==='false')return false;const text=cleanSpeech(message);if(!text)return false;stopAudio();const token=generation;const entry=getEntry(assignedId(message?.identity||message?.speaker||'default'),true)||getEntry('',true);if(entry.engine==='kokoro'){void speakKokoro(text,entry,token);return true}return speakBrowser(text,entry)}
 function preview(id,text='Welcome to Shaelvien. Your journey begins here.'){if(localStorage.getItem(ENABLED_KEY)==='false')setEnabled(true);stopAudio();const token=generation;const entry=getEntry(id??defaultId(),true)||getEntry('',true);if(entry.engine==='kokoro'){void speakKokoro(text,entry,token);return true}return speakBrowser(text,entry)}
 function setVoice(identity,voiceId){if(!identity||!getEntry(voiceId,false))return false;const map=assignments();map[norm(identity)]=String(voiceId||'');writeJson(ASSIGN_KEY,map);return true}
 function clearVoice(identity){const map=assignments();delete map[norm(identity)];writeJson(ASSIGN_KEY,map)}
 function setDefault(voiceId){const id=String(voiceId||'');if(id&&!getEntry(id,false))return false;try{localStorage.setItem(DEFAULT_KEY,id)}catch{}return true}
 function setEnabled(value){try{localStorage.setItem(ENABLED_KEY,value?'true':'false')}catch{}if(!value)stopAudio()}
 function describe(id){const v=getEntry(id??defaultId(),false);return v?{id:v.id,name:v.name,lang:v.lang||'',voiceURI:v.voiceURI||v.id,engine:v.engine,category:v.category,providerVoiceId:v.providerVoiceId||''}:null}
 window.RistRoleplayVoice={
  categories:[...CATEGORY_ORDER],speak,preview,cancel:stopAudio,refresh:refreshVoices,
  getCatalog:catalog,getVoices:catalog,getDefault:()=>describe(defaultId()),getDefaultId:defaultId,
  setDefault,setVoice,clearVoice,getVoice:identity=>describe(assignedId(identity)),
  loadKokoro:()=>loadKokoro().then(()=>true),setEnabled,get enabled(){return localStorage.getItem(ENABLED_KEY)!=='false'}
 };
})();
