(()=>{
 'use strict';
 const ASSIGN_KEY='rist.roleplay.voice.assignments.v1';
 const DEFAULT_KEY='rist.roleplay.voice.default.v1';
 const ENABLED_KEY='rist.roleplay.voice.enabled.v1';
 let voices=[];
 const synth=window.speechSynthesis;
 const readJson=(key,fallback)=>{try{return JSON.parse(localStorage.getItem(key)||'')||fallback}catch{return fallback}};
 const writeJson=(key,value)=>{try{localStorage.setItem(key,JSON.stringify(value))}catch{}};
 const norm=value=>String(value||'').trim().toLowerCase();
 function refreshVoices(){voices=synth?.getVoices?.()||[];return voices}
 function chooseDefault(){
  refreshVoices();
  const saved=localStorage.getItem(DEFAULT_KEY)||'';
  if(saved){const hit=voices.find(v=>v.voiceURI===saved||v.name===saved);if(hit)return hit}
  const preferred=['Samantha','Alex','Google US English','Microsoft Aria','Microsoft David'];
  for(const name of preferred){const hit=voices.find(v=>v.name===name||v.name.includes(name));if(hit){try{localStorage.setItem(DEFAULT_KEY,hit.voiceURI||hit.name)}catch{}return hit}}
  const hit=voices.find(v=>v.default&&/^en(?:-|$)/i.test(v.lang))||voices.find(v=>/^en-US$/i.test(v.lang))||voices.find(v=>/^en(?:-|$)/i.test(v.lang))||voices[0]||null;
  if(hit)try{localStorage.setItem(DEFAULT_KEY,hit.voiceURI||hit.name)}catch{}
  return hit;
 }
 function assignments(){return readJson(ASSIGN_KEY,{})}
 function assignedVoice(identity){
  refreshVoices();
  const wanted=assignments()[norm(identity)];
  if(wanted){const hit=voices.find(v=>v.voiceURI===wanted||v.name===wanted);if(hit)return hit}
  return chooseDefault();
 }
 function cleanSpeech(message){
  const text=String(message?.text||'').trim();
  if(!text)return'';
  const colon=text.indexOf(':');
  if(colon>0&&colon<40)return text.slice(colon+1).trim()||text;
  return text;
 }
 function speak(message){
  if(!synth||localStorage.getItem(ENABLED_KEY)==='false')return false;
  const text=cleanSpeech(message);if(!text)return false;
  const utter=new SpeechSynthesisUtterance(text);
  const voice=assignedVoice(message?.identity||message?.speaker||'default');
  if(voice){utter.voice=voice;utter.lang=voice.lang||'en-US'}else utter.lang='en-US';
  utter.rate=1;utter.pitch=1;utter.volume=1;
  synth.cancel();synth.speak(utter);return true;
 }
 function setVoice(identity,voiceId){
  if(!identity)return false;refreshVoices();
  const hit=voices.find(v=>v.voiceURI===voiceId||v.name===voiceId);if(!hit)return false;
  const map=assignments();map[norm(identity)]=hit.voiceURI||hit.name;writeJson(ASSIGN_KEY,map);return true;
 }
 function clearVoice(identity){const map=assignments();delete map[norm(identity)];writeJson(ASSIGN_KEY,map)}
 function setDefault(voiceId){refreshVoices();const hit=voices.find(v=>v.voiceURI===voiceId||v.name===voiceId);if(!hit)return false;try{localStorage.setItem(DEFAULT_KEY,hit.voiceURI||hit.name)}catch{}return true}
 function setEnabled(value){try{localStorage.setItem(ENABLED_KEY,value?'true':'false')}catch{}if(!value)synth?.cancel?.()}
 if(synth){refreshVoices();synth.addEventListener?.('voiceschanged',refreshVoices);setTimeout(refreshVoices,250)}
 window.RistRoleplayVoice={
  speak,cancel:()=>synth?.cancel?.(),refresh:refreshVoices,
  getVoices:()=>refreshVoices().map(v=>({name:v.name,lang:v.lang,voiceURI:v.voiceURI,default:v.default,localService:v.localService})),
  getDefault:()=>{const v=chooseDefault();return v?{name:v.name,lang:v.lang,voiceURI:v.voiceURI}:null},
  setDefault,setVoice,clearVoice,
  getVoice:identity=>{const v=assignedVoice(identity);return v?{name:v.name,lang:v.lang,voiceURI:v.voiceURI}:null},
  setEnabled,get enabled(){return localStorage.getItem(ENABLED_KEY)!=='false'}
 };
})();