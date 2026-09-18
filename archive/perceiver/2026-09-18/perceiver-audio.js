(()=>{'use strict';

const clamp=(v,a,b)=>Math.min(b,Math.max(a,Number(v)||0));
const dbToGain=db=>Math.pow(10,db/20);
const safeText=v=>Number.isFinite(v)?v.toFixed(1):'--';

class PerceiverAudioEngine{
  constructor(video,onState=()=>{}){
    this.video=video;
    this.onState=onState;
    this.ctx=null;
    this.mediaSource=null;
    this.movieAnalyser=null;
    this.micAnalyser=null;
    this.micStream=null;
    this.micSource=null;
    this.lowGain=null;
    this.midGain=null;
    this.highGain=null;
    this.masterGain=null;
    this.limiter=null;
    this.outputAnalyser=null;
    this.enabled=true;
    this.roomInclusion=.35;
    this.distance=.45;
    this.outputCeiling=.50;
    this.frame=0;
    this.lastState={mic:'off',audio:'idle',roomDb:null,outputDb:null,bands:{low:null,mid:null,high:null}};
  }

  emit(extra={}){
    this.lastState={...this.lastState,...extra};
    this.onState(this.lastState);
    try{dispatchEvent(new CustomEvent('perceiver:audio-state',{detail:this.lastState}))}catch{}
  }

  async ensureGraph(){
    if(this.ctx)return this.ctx;
    const Ctor=window.AudioContext||window.webkitAudioContext;
    if(!Ctor){this.emit({audio:'unsupported'});throw new Error('Web Audio is unavailable in this browser.')}
    const ctx=this.ctx=new Ctor({latencyHint:'playback'});
    await ctx.resume();

    this.mediaSource=ctx.createMediaElementSource(this.video);
    this.movieAnalyser=ctx.createAnalyser();
    this.movieAnalyser.fftSize=2048;
    this.movieAnalyser.smoothingTimeConstant=.72;
    this.mediaSource.connect(this.movieAnalyser);

    const low=ctx.createBiquadFilter();
    low.type='lowpass';low.frequency.value=250;low.Q.value=.707;
    this.lowGain=ctx.createGain();

    const midHigh=ctx.createBiquadFilter();
    midHigh.type='highpass';midHigh.frequency.value=250;midHigh.Q.value=.707;
    const midLow=ctx.createBiquadFilter();
    midLow.type='lowpass';midLow.frequency.value=2500;midLow.Q.value=.707;
    this.midGain=ctx.createGain();

    const high=ctx.createBiquadFilter();
    high.type='highpass';high.frequency.value=2500;high.Q.value=.707;
    this.highGain=ctx.createGain();

    this.mediaSource.connect(low);low.connect(this.lowGain);
    this.mediaSource.connect(midHigh);midHigh.connect(midLow);midLow.connect(this.midGain);
    this.mediaSource.connect(high);high.connect(this.highGain);

    this.masterGain=ctx.createGain();
    this.lowGain.connect(this.masterGain);
    this.midGain.connect(this.masterGain);
    this.highGain.connect(this.masterGain);

    // Independent output governor. This is a digital ceiling, not an SPL claim.
    this.limiter=ctx.createDynamicsCompressor();
    this.limiter.threshold.value=-8;
    this.limiter.knee.value=0;
    this.limiter.ratio.value=20;
    this.limiter.attack.value=.002;
    this.limiter.release.value=.16;

    this.outputAnalyser=ctx.createAnalyser();
    this.outputAnalyser.fftSize=1024;
    this.masterGain.connect(this.limiter);
    this.limiter.connect(this.outputAnalyser);
    this.outputAnalyser.connect(ctx.destination);

    this.applySettings();
    this.emit({audio:'ready'});
    this.loop();
    return ctx;
  }

  async resume(){
    const ctx=await this.ensureGraph();
    if(ctx.state!=='running')await ctx.resume();
    this.emit({audio:ctx.state});
  }

  setEnabled(on){
    this.enabled=!!on;
    this.applySettings();
    return this.enabled;
  }

  setRoomInclusion(v){this.roomInclusion=clamp(v,0,1);return this.roomInclusion}
  setDistance(v){this.distance=clamp(v,0,1);return this.distance}
  setOutputCeiling(v){this.outputCeiling=clamp(v,.15,.65);this.applySettings();return this.outputCeiling}

  applySettings(){
    if(!this.ctx||!this.masterGain)return;
    const now=this.ctx.currentTime;
    const master=this.enabled?this.outputCeiling:0;
    this.masterGain.gain.setTargetAtTime(master,now,.04);
  }

  async enableMicrophone(){
    await this.ensureGraph();
    if(this.micStream){
      this.emit({mic:'on'});
      return 'on';
    }
    const gum=navigator.mediaDevices?.getUserMedia?.bind(navigator.mediaDevices);
    if(!gum){this.emit({mic:'unsupported'});return 'unsupported'}
    try{
      const stream=await gum({
        audio:{
          echoCancellation:true,
          noiseSuppression:false,
          autoGainControl:false,
          channelCount:1
        },
        video:false
      });
      this.micStream=stream;
      this.micSource=this.ctx.createMediaStreamSource(stream);
      this.micAnalyser=this.ctx.createAnalyser();
      this.micAnalyser.fftSize=2048;
      this.micAnalyser.smoothingTimeConstant=.78;
      // Intentional: microphone is ANALYSIS ONLY. There is no connection from
      // micAnalyser or micSource to ctx.destination, eliminating our own monitor path.
      this.micSource.connect(this.micAnalyser);
      this.emit({mic:'on'});
      return 'on';
    }catch(error){
      const name=String(error?.name||'');
      const state=(name==='NotAllowedError'||name==='SecurityError')?'denied':'unavailable';
      this.emit({mic:state});
      return state;
    }
  }

  disableMicrophone(){
    try{this.micStream?.getTracks?.().forEach(track=>track.stop())}catch{}
    try{this.micSource?.disconnect()}catch{}
    this.micStream=null;
    this.micSource=null;
    this.micAnalyser=null;
    this.emit({mic:'off',roomDb:null,bands:{low:null,mid:null,high:null}});
  }

  bandDb(analyser,minHz,maxHz){
    if(!analyser||!this.ctx)return null;
    const bins=new Float32Array(analyser.frequencyBinCount);
    analyser.getFloatFrequencyData(bins);
    const nyquist=this.ctx.sampleRate/2;
    let start=Math.max(0,Math.floor(minHz/nyquist*bins.length));
    let end=Math.min(bins.length-1,Math.ceil(maxHz/nyquist*bins.length));
    if(end<start)return null;
    let power=0,count=0;
    for(let i=start;i<=end;i++){
      const db=bins[i];
      if(Number.isFinite(db)&&db>-160){power+=Math.pow(10,db/10);count++}
    }
    return count?10*Math.log10(Math.max(power/count,1e-12)):null;
  }

  outputDb(){
    if(!this.outputAnalyser)return null;
    const data=new Float32Array(this.outputAnalyser.fftSize);
    this.outputAnalyser.getFloatTimeDomainData(data);
    let sum=0;
    for(const x of data)sum+=x*x;
    const rms=Math.sqrt(sum/Math.max(1,data.length));
    return 20*Math.log10(Math.max(rms,1e-6));
  }

  targetBandGain(roomDb,movieDb,baseAttenuation,maxBoost){
    let boost=0;
    if(this.micAnalyser&&Number.isFinite(roomDb)&&Number.isFinite(movieDb)){
      // Match the room only gently. The requested environmental inclusion may
      // shape the film, but it can never command an unbounded gain increase.
      const desired=Math.max(0,(roomDb+3)-movieDb);
      const roomPresence=clamp((roomDb+70)/40,0,1);
      const moviePresence=clamp((movieDb+75)/45,0,1);
      boost=Math.min(maxBoost,desired)*this.roomInclusion*roomPresence*moviePresence;
    }
    return dbToGain(baseAttenuation+boost);
  }

  update(){
    if(!this.ctx||!this.lowGain)return;
    const d=this.distance;
    const room={
      low:this.bandDb(this.micAnalyser,20,250),
      mid:this.bandDb(this.micAnalyser,250,2500),
      high:this.bandDb(this.micAnalyser,2500,16000)
    };
    const movie={
      low:this.bandDb(this.movieAnalyser,20,250),
      mid:this.bandDb(this.movieAnalyser,250,2500),
      high:this.bandDb(this.movieAnalyser,2500,16000)
    };

    // Distance model: bass is retained farther than mids, while treble loses
    // the most energy. This is perceptual rendering, never source truth.
    const lowDb=-1.5*d;
    const midDb=-4.0*d;
    const highDb=-8.0*d;
    const now=this.ctx.currentTime;
    this.lowGain.gain.setTargetAtTime(this.targetBandGain(room.low,movie.low,lowDb,2.5),now,.09);
    this.midGain.gain.setTargetAtTime(this.targetBandGain(room.mid,movie.mid,midDb,2.0),now,.09);
    this.highGain.gain.setTargetAtTime(this.targetBandGain(room.high,movie.high,highDb,1.5),now,.09);

    const finite=Object.values(room).filter(Number.isFinite);
    const roomDb=finite.length?finite.reduce((a,b)=>a+b,0)/finite.length:null;
    const outputDb=this.outputDb();

    // Extra protection against sustained near-ceiling digital output.
    // Device/headphone SPL is unknowable without calibration, so this only
    // governs digital headroom and never claims ear-level dB safety.
    if(Number.isFinite(outputDb)&&outputDb>-5){
      this.masterGain.gain.setTargetAtTime(Math.min(this.outputCeiling,.38),now,.025);
    }else{
      this.masterGain.gain.setTargetAtTime(this.enabled?this.outputCeiling:0,now,.15);
    }

    this.emit({
      audio:this.ctx.state,
      roomDb,
      outputDb,
      bands:room,
      distance:d,
      roomInclusion:this.roomInclusion,
      outputCeiling:this.outputCeiling
    });
  }

  loop(){
    cancelAnimationFrame(this.frame);
    const tick=()=>{this.update();this.frame=requestAnimationFrame(tick)};
    this.frame=requestAnimationFrame(tick);
  }

  destroy(){
    cancelAnimationFrame(this.frame);
    this.disableMicrophone();
    try{this.mediaSource?.disconnect()}catch{}
    try{this.ctx?.close()}catch{}
    this.ctx=null;
  }
}

window.PerceiverAudioEngine=PerceiverAudioEngine;
})();
