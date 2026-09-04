(()=>{
 'use strict';
 const MODE_KEY='rist.roleplay.voice.capture-mode.v1';
 const MODE_CHARACTER='character';
 const MODE_LIVE='live';
 const q=(s,r=document)=>r?.querySelector?.(s)||null;
 let pendingClip=null;
 let pendingClipUrl='';
 let activeRecorder=null;
 let activeStream=null;
 let activeRecognition=null;
 let recording=false;
 let startText='';
 let startCommand='/s';

 function mode(){return localStorage.getItem(MODE_KEY)===MODE_LIVE?MODE_LIVE:MODE_CHARACTER}
 function setMode(value){localStorage.setItem(MODE_KEY,value===MODE_LIVE?MODE_LIVE:MODE_CHARACTER);syncUi()}
 function clearPendingClip(){if(pendingClipUrl){try{URL.revokeObjectURL(pendingClipUrl)}catch{}pendingClipUrl=''}pendingClip=null}
 function playPendingClip(){
  if(!pendingClip)return false;
  const blob=pendingClip;clearPendingClip();
  const url=URL.createObjectURL(blob);const audio=new Audio(url);
  audio.addEventListener('ended',()=>URL.revokeObjectURL(url),{once:true});
  audio.addEventListener('error',()=>URL.revokeObjectURL(url),{once:true});
  audio.play().catch(()=>URL.revokeObjectURL(url));
  document.dispatchEvent(new CustomEvent('rist:roleplay-live-voice-played'));
  return true;
 }
 function patchVoiceEngine(){
  const api=window.RistRoleplayVoice;if(!api||api.__chatVoicePatched)return false;
  const original=api.speak?.bind(api);
  api.speak=(message)=>{
   if(mode()===MODE_LIVE&&pendingClip&&String(message?.medium||'audible')!=='thought')return playPendingClip();
   return original?original(message):false;
  };
  api.__chatVoicePatched=true;
  return true;
 }
 function ensureStyles(){
  if(q('#rist-roleplay-voice-chat-style'))return;
  const style=document.createElement('style');style.id='rist-roleplay-voice-chat-style';style.textContent=`
   .rist-chat-action-button.rist-voice-record,.rist-chat-action-button.rist-voice-settings{min-width:38px!important;touch-action:manipulation!important}
   .rist-chat-action-button.rist-voice-record[data-recording="true"]{outline:2px solid currentColor!important;outline-offset:1px!important;animation:ristVoicePulse .9s ease-in-out infinite alternate}
   @keyframes ristVoicePulse{from{opacity:.68}to{opacity:1}}
   .rist-roleplay-voice-panel{position:fixed;z-index:2147483000;box-sizing:border-box;width:min(360px,calc(100vw - 18px));max-height:min(520px,calc(100vh - 18px));overflow:auto;padding:10px;border:1px solid #8d7439;border-radius:12px;background:#0c1319;color:#eee6d2;box-shadow:0 12px 36px #000b;font:700 12px/1.3 system-ui,-apple-system,sans-serif}
   .rist-roleplay-voice-panel h3{margin:0 0 8px;color:#e1c77f;font-size:13px}.rist-roleplay-voice-panel label{display:grid;gap:4px;margin:8px 0}.rist-roleplay-voice-panel select{box-sizing:border-box;width:100%;min-height:38px;padding:6px 8px;border:1px solid #725d30;border-radius:9px;background:#111920;color:#eee6d2;font-size:16px}.rist-roleplay-voice-panel .voice-panel-actions{display:flex;gap:6px;flex-wrap:wrap;margin-top:8px}.rist-roleplay-voice-panel button{min-height:36px;padding:0 10px;border:1px solid #725d30;border-radius:9px;background:#111920;color:#d7be80;font-weight:800}.rist-roleplay-voice-panel small{display:block;margin-top:8px;color:#9f957f;font-weight:600}.rist-roleplay-voice-status{min-height:16px;margin-top:6px;color:#cbb77d}
  `;document.head.appendChild(style);
 }
 function currentInput(){return q('.rist-chat-line-input')||q('.home-chat-compose textarea')}
 function beginTranscriptState(){
  const input=currentInput();const value=String(input?.value||'');const match=value.match(/^\s*(\/[a-z]+)(?:\s+|$)/i);startCommand=match?.[1]||'/s';startText=match?value.replace(/^\s*\/[a-z]+\s*/i,'').trim():value.trim();
 }
 function applyTranscript(text,isFinal){
  const input=currentInput();if(!input)return;
  const spoken=String(text||'').trim();const combined=[startText,spoken].filter(Boolean).join(startText&&spoken?' ':'').trim();
  input.value=`${startCommand} ${combined}`.replace(/\s+$/,' ');input.dispatchEvent(new Event('input',{bubbles:true}));
  if(isFinal)input.setSelectionRange?.(input.value.length,input.value.length);
 }
 function recognitionCtor(){return window.SpeechRecognition||window.webkitSpeechRecognition||null}
 function startRecognition(){
  const Ctor=recognitionCtor();if(!Ctor)return null;
  const rec=new Ctor();rec.continuous=true;rec.interimResults=true;rec.lang=document.documentElement.lang||'en-US';
  rec.onresult=event=>{let finalText='',interim='';for(let i=event.resultIndex;i<event.results.length;i++){const text=event.results[i][0]?.transcript||'';if(event.results[i].isFinal)finalText+=text;else interim+=text}applyTranscript(finalText||interim,!!finalText)};
  rec.onerror=event=>setStatus(`Transcription: ${event.error||'unavailable'}`);
  rec.onend=()=>{if(recording&&mode()===MODE_CHARACTER){recording=false;syncUi()}};
  try{rec.start();return rec}catch{return null}
 }
 async function startRecording(){
  if(recording)return;
  beginTranscriptState();clearPendingClip();recording=true;syncUi();setStatus('Listening…');
  activeRecognition=startRecognition();
  if(mode()===MODE_LIVE){
   if(!navigator.mediaDevices?.getUserMedia||!window.MediaRecorder){recording=false;activeRecognition?.stop?.();activeRecognition=null;syncUi();setStatus('Live voice recording is not supported by this browser.');return}
   try{
    activeStream=await navigator.mediaDevices.getUserMedia({audio:true});
    const chunks=[];activeRecorder=new MediaRecorder(activeStream);
    activeRecorder.ondataavailable=e=>{if(e.data?.size)chunks.push(e.data)};
    activeRecorder.onstop=()=>{const type=activeRecorder?.mimeType||'audio/webm';if(chunks.length){pendingClip=new Blob(chunks,{type});document.dispatchEvent(new CustomEvent('rist:roleplay-live-voice-ready',{detail:{blob:pendingClip,mimeType:type}}));setStatus('Voice acting ready for the next Roleplay send.')}cleanupMedia(false)};
    activeRecorder.start();
   }catch(error){recording=false;activeRecognition?.stop?.();activeRecognition=null;cleanupMedia(true);syncUi();setStatus(error?.name==='NotAllowedError'?'Microphone permission was denied.':'Microphone could not start.');}
  }else if(!activeRecognition){recording=false;syncUi();setStatus('Voice-to-text is not available in this browser. You can still use the device keyboard dictation button.');}
 }
 function cleanupMedia(stopRecorder){
  if(stopRecorder&&activeRecorder&&activeRecorder.state!=='inactive'){try{activeRecorder.stop()}catch{}}
  activeRecorder=null;if(activeStream){for(const track of activeStream.getTracks())track.stop();activeStream=null}
 }
 function stopRecording(){
  if(!recording)return;recording=false;
  if(activeRecognition){try{activeRecognition.stop()}catch{}activeRecognition=null}
  if(activeRecorder&&activeRecorder.state!=='inactive'){try{activeRecorder.stop()}catch{cleanupMedia(false)}}else cleanupMedia(false);
  syncUi();if(mode()===MODE_CHARACTER)setStatus('Transcript ready. Send it to use the selected character voice.');
 }
 function toggleRecording(){recording?stopRecording():void startRecording()}
 function setStatus(text){document.querySelectorAll('.rist-roleplay-voice-status').forEach(el=>el.textContent=text||'')}
 function voiceOptions(select){
  const api=window.RistRoleplayVoice;if(!api||!select)return;
  const current=api.getDefault?.()?.id||'';select.replaceChildren();
  for(const category of api.categories||[]){const entries=(api.getVoices?.()||[]).filter(v=>v.category===category);if(!entries.length)continue;const group=document.createElement('optgroup');group.label=category;for(const v of entries){const opt=document.createElement('option');opt.value=v.id;opt.textContent=`${v.name}${v.engine==='kokoro'?' · Kokoro':''}${v.lang?` (${v.lang})`:''}`;if(v.id===current)opt.selected=true;group.appendChild(opt)}select.appendChild(group)}
 }
 function positionPanel(panel,anchor){const r=anchor.getBoundingClientRect();const w=Math.min(360,window.innerWidth-18);const left=Math.max(9,Math.min(window.innerWidth-w-9,r.right-w));panel.style.left=`${Math.round(left)}px`;const h=Math.min(panel.offsetHeight||360,window.innerHeight-18);const above=r.top-h-8;panel.style.top=`${Math.round(above>=9?above:Math.min(window.innerHeight-h-9,r.bottom+8))}px`}
 function closePanel(){q('.rist-roleplay-voice-panel')?.remove()}
 function openPanel(anchor){
  closePanel();const api=window.RistRoleplayVoice;if(!api)return;
  const panel=document.createElement('section');panel.className='rist-roleplay-voice-panel';panel.setAttribute('role','dialog');panel.setAttribute('aria-label','Roleplay voice settings');
  const title=document.createElement('h3');title.textContent='Roleplay Voice';
  const modeLabel=document.createElement('label');modeLabel.textContent='Record mode';const modeSelect=document.createElement('select');modeSelect.innerHTML='<option value="character">Voice → Text → Character Voice</option><option value="live">Voice → Text + My Voice</option>';modeSelect.value=mode();modeSelect.addEventListener('change',()=>{setMode(modeSelect.value);setStatus(modeSelect.value===MODE_LIVE?'Your next recording will play your voice instead of TTS.':'Recordings become text, then use the selected character voice.')});modeLabel.appendChild(modeSelect);
  const voiceLabel=document.createElement('label');voiceLabel.textContent='Character voice';const voiceSelect=document.createElement('select');voiceOptions(voiceSelect);voiceSelect.addEventListener('change',()=>{api.setDefault?.(voiceSelect.value);api.preview?.(voiceSelect.value)});voiceLabel.appendChild(voiceSelect);
  const actions=document.createElement('div');actions.className='voice-panel-actions';const preview=document.createElement('button');preview.type='button';preview.textContent='Preview';preview.addEventListener('click',()=>api.preview?.(voiceSelect.value));const enabled=document.createElement('button');enabled.type='button';enabled.textContent=api.enabled?'Voice On':'Voice Off';enabled.addEventListener('click',()=>{api.setEnabled?.(!api.enabled);enabled.textContent=api.enabled?'Voice On':'Voice Off'});const done=document.createElement('button');done.type='button';done.textContent='Done';done.addEventListener('click',closePanel);actions.append(preview,enabled,done);
  const status=document.createElement('div');status.className='rist-roleplay-voice-status';status.setAttribute('aria-live','polite');
  const privacy=document.createElement('small');privacy.textContent='Microphone audio is kept only in memory for the current voice-acted line. Character Voice mode discards mic audio and keeps the transcript.';
  panel.append(title,modeLabel,voiceLabel,actions,status,privacy);document.body.appendChild(panel);requestAnimationFrame(()=>positionPanel(panel,anchor));
 }
 function syncUi(){
  document.querySelectorAll('.rist-voice-record').forEach(button=>{button.dataset.recording=recording?'true':'false';button.setAttribute('aria-pressed',recording?'true':'false');button.title=recording?'Stop recording':(mode()===MODE_LIVE?'Record voice acting':'Voice to text');button.setAttribute('aria-label',button.title);button.textContent=recording?'■':'●'});
 }
 function enhanceComposer(){
  patchVoiceEngine();ensureStyles();const actions=q('.rist-chat-action-row');if(!actions)return;
  if(!q('.rist-voice-settings',actions)){const settings=document.createElement('button');settings.type='button';settings.className='rist-chat-action-button rist-voice-settings';settings.textContent='◖◗';settings.title='Roleplay voice settings';settings.setAttribute('aria-label','Roleplay voice settings');settings.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();q('.rist-roleplay-voice-panel')?closePanel():openPanel(settings)});actions.appendChild(settings)}
  if(!q('.rist-voice-record',actions)){const record=document.createElement('button');record.type='button';record.className='rist-chat-action-button rist-voice-record';record.textContent='●';record.addEventListener('click',e=>{e.preventDefault();e.stopPropagation();toggleRecording()});actions.appendChild(record)}
  syncUi();
 }
 function queue(){requestAnimationFrame(enhanceComposer)}
 document.addEventListener('click',event=>{const panel=q('.rist-roleplay-voice-panel');if(panel&&!event.target.closest('.rist-roleplay-voice-panel')&&!event.target.closest('.rist-voice-settings'))closePanel()},true);
 window.addEventListener('resize',()=>closePanel(),{passive:true});window.addEventListener('orientationchange',()=>closePanel(),{passive:true});window.addEventListener('beforeunload',clearPendingClip);
 new MutationObserver(queue).observe(document.documentElement,{childList:true,subtree:true});
 if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',queue,{once:true});else queue();
 window.RistRoleplayVoiceChat={get mode(){return mode()},setMode,start:startRecording,stop:stopRecording,get recording(){return recording},clearPending:clearPendingClip};
})();
