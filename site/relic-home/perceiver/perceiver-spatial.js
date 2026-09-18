(()=>{'use strict';

const clamp=(v,a,b)=>Math.min(b,Math.max(a,Number(v)||0));

class PerceiverSpatialController{
  constructor({stage,video,marker,tag,modeButton,clearButton,planeSelect,status,tiltButton,calibrateButton,strength,smooth,strengthOut,smoothOut,speedInputs}){
    this.stage=stage;this.video=video;this.marker=marker;this.tag=tag;
    this.modeButton=modeButton;this.clearButton=clearButton;this.planeSelect=planeSelect;this.status=status;
    this.tiltButton=tiltButton;this.calibrateButton=calibrateButton;this.strength=strength;this.smooth=smooth;this.strengthOut=strengthOut;this.smoothOut=smoothOut;
    this.speedInputs=speedInputs;
    this.focus={mode:'auto',x:.5,y:.5,plane:'focus'};
    this.tilt={enabled:false,permission:'unknown',baseBeta:null,baseGamma:null,lastBeta:null,lastGamma:null,targetX:0,targetY:0,x:0,y:0,listening:false};
    this.load();
    this.bind();
    this.renderFocus();
    this.renderTilt();
  }

  load(){
    try{
      const raw=localStorage.getItem('perceiver.focus');
      if(raw){
        const p=JSON.parse(raw);
        if(p&&['auto','manual'].includes(p.mode)){
          this.focus={
            mode:p.mode,
            x:clamp(p.x,0,1),
            y:clamp(p.y,0,1),
            plane:['far','background','focus','near','foreground'].includes(p.plane)?p.plane:'focus'
          };
        }
      }
      const strength=localStorage.getItem('perceiver.tilt.strength');
      const smooth=localStorage.getItem('perceiver.tilt.smooth');
      if(strength!==null)this.strength.value=strength;
      if(smooth!==null)this.smooth.value=smooth;
    }catch{}
    this.planeSelect.value=this.focus.plane;
  }

  saveFocus(){try{localStorage.setItem('perceiver.focus',JSON.stringify(this.focus))}catch{}}
  saveTilt(){try{localStorage.setItem('perceiver.tilt.strength',this.strength.value);localStorage.setItem('perceiver.tilt.smooth',this.smooth.value)}catch{}}

  bind(){
    this.modeButton.addEventListener('click',()=>{
      this.focus.mode=this.focus.mode==='auto'?'manual':'auto';
      if(this.focus.mode==='auto'){this.focus.x=.5;this.focus.y=.5}
      this.saveFocus();this.renderFocus();
    });
    this.clearButton.addEventListener('click',()=>{
      this.focus.mode='auto';this.focus.x=.5;this.focus.y=.5;this.saveFocus();this.renderFocus();
    });
    this.planeSelect.addEventListener('change',()=>{
      this.focus.plane=this.planeSelect.value||'focus';this.saveFocus();this.renderFocus();
    });
    this.stage.addEventListener('pointerdown',event=>this.pickFocus(event));
    this.video.addEventListener('loadedmetadata',()=>this.renderFocus());
    addEventListener('resize',()=>this.renderFocus(),{passive:true});
    addEventListener('orientationchange',()=>{this.tilt.baseBeta=null;this.tilt.baseGamma=null;this.renderFocus()},{passive:true});

    this.tiltButton.addEventListener('click',()=>this.toggleTilt());
    this.calibrateButton.addEventListener('click',()=>this.calibrate());
    this.strength.addEventListener('input',()=>{this.saveTilt();this.renderTilt()});
    this.smooth.addEventListener('input',()=>{this.saveTilt();this.renderTilt()});
  }

  videoRect(){
    const r=this.stage.getBoundingClientRect();
    if(!this.video.classList.contains('active')||!this.video.videoWidth||!this.video.videoHeight)return{left:0,top:0,width:r.width,height:r.height};
    const mediaRatio=this.video.videoWidth/this.video.videoHeight;
    const boxRatio=r.width/Math.max(1,r.height);
    if(mediaRatio>boxRatio){
      const width=r.width,height=width/mediaRatio;
      return{left:0,top:(r.height-height)/2,width,height};
    }
    const height=r.height,width=height*mediaRatio;
    return{left:(r.width-width)/2,top:0,width,height};
  }

  pickFocus(event){
    if(this.focus.mode!=='manual'||!this.video.classList.contains('active'))return;
    const sr=this.stage.getBoundingClientRect(),vr=this.videoRect();
    const x=event.clientX-sr.left,y=event.clientY-sr.top;
    if(x<vr.left||x>vr.left+vr.width||y<vr.top||y>vr.top+vr.height)return;
    this.focus.x=clamp((x-vr.left)/vr.width,0,1);
    this.focus.y=clamp((y-vr.top)/vr.height,0,1);
    this.saveFocus();this.renderFocus();
  }

  focusSpeed(){
    if(this.focus.plane==='focus')return 1;
    const input=this.speedInputs[this.focus.plane];
    return input?Number(input.value)/100:1;
  }

  renderFocus(){
    const vr=this.videoRect();
    this.marker.style.left=(vr.left+this.focus.x*vr.width)+'px';
    this.marker.style.top=(vr.top+this.focus.y*vr.height)+'px';
    this.marker.classList.toggle('manual',this.focus.mode==='manual');
    this.stage.classList.toggle('manual-focus',this.focus.mode==='manual');
    this.modeButton.classList.toggle('active',this.focus.mode==='auto');
    this.modeButton.textContent=this.focus.mode==='auto'?'FOCUS · AUTO':'FOCUS · MANUAL';
    this.clearButton.disabled=this.focus.mode!=='manual';
    this.tag.textContent=(this.focus.mode==='manual'?'MANUAL':'AUTO')+' · '+this.focus.plane.toUpperCase()+' · '+this.focusSpeed().toFixed(2)+'×';
    this.status.innerHTML='<strong>Focus:</strong> '+(this.focus.mode==='manual'
      ?'manual anchor '+Math.round(this.focus.x*100)+'%, '+Math.round(this.focus.y*100)+'% · '+this.focus.plane+'. Tap the visible video to move it.'
      :'automatic center reference. Switch to manual, then tap the visible video to anchor focus.');
  }

  screenAdjusted(beta,gamma){
    const angle=screen.orientation?.angle??window.orientation??0;
    if(angle===90)return{beta:-gamma,gamma:beta};
    if(angle===-90||angle===270)return{beta:gamma,gamma:-beta};
    if(Math.abs(angle)===180)return{beta:-beta,gamma:-gamma};
    return{beta,gamma};
  }

  onOrientation(event){
    if(event.beta==null||event.gamma==null)return;
    const a=this.screenAdjusted(Number(event.beta),Number(event.gamma));
    this.tilt.lastBeta=a.beta;this.tilt.lastGamma=a.gamma;
    if(this.tilt.baseBeta==null||this.tilt.baseGamma==null){this.tilt.baseBeta=a.beta;this.tilt.baseGamma=a.gamma}
    if(!this.tilt.enabled)return;
    const strength=Number(this.strength.value)/100;
    this.tilt.targetX=clamp((a.gamma-this.tilt.baseGamma)*1.1,-24,24)*strength;
    this.tilt.targetY=clamp((a.beta-this.tilt.baseBeta)*.8,-18,18)*strength;
  }

  async toggleTilt(){
    if(this.tilt.enabled){
      this.tilt.enabled=false;this.tilt.targetX=0;this.tilt.targetY=0;this.renderTilt();return false;
    }
    try{
      const Orientation=window.DeviceOrientationEvent;
      if(!Orientation){this.tilt.permission='unsupported';this.renderTilt();return false}
      if(typeof Orientation.requestPermission==='function'){
        this.tilt.permission=await Orientation.requestPermission();
        if(this.tilt.permission!=='granted'){this.renderTilt();return false}
      }else this.tilt.permission='granted';
      if(!this.tilt.listening){
        this._orientationHandler=event=>this.onOrientation(event);
        addEventListener('deviceorientation',this._orientationHandler,{passive:true});
        this.tilt.listening=true;
      }
      this.tilt.enabled=true;this.tilt.baseBeta=null;this.tilt.baseGamma=null;this.renderTilt();return true;
    }catch{
      this.tilt.permission='denied';this.renderTilt();return false;
    }
  }

  calibrate(){
    if(this.tilt.lastBeta==null||this.tilt.lastGamma==null)return;
    this.tilt.baseBeta=this.tilt.lastBeta;this.tilt.baseGamma=this.tilt.lastGamma;
    this.tilt.targetX=0;this.tilt.targetY=0;this.tilt.x=0;this.tilt.y=0;
    this.statusTilt('<strong>Tilt:</strong> center calibrated.');
  }

  statusTilt(html){this.tiltStatus.innerHTML=html}

  renderTilt(){
    this.strengthOut.textContent=this.strength.value+'%';
    this.smoothOut.textContent=this.smooth.value+'%';
    this.tiltButton.classList.toggle('active',this.tilt.enabled);
    this.tiltButton.textContent=this.tilt.enabled?'TILT · ON':'TILT · OFF';
    this.calibrateButton.disabled=!this.tilt.enabled;
    if(this.tilt.permission==='unsupported')this.tiltStatus.innerHTML='<strong>Tilt:</strong> unavailable on this device.';
    else if(this.tilt.permission==='denied')this.tiltStatus.innerHTML='<strong>Tilt:</strong> permission denied.';
    else if(this.tilt.enabled)this.tiltStatus.innerHTML='<strong>Tilt:</strong> enabled. Hold the device naturally, then calibrate center if needed.';
    else this.tiltStatus.innerHTML='<strong>Tilt:</strong> off. Enabling it requests device-orientation permission on supported phones.';
  }

  attachTiltStatus(element){this.tiltStatus=element;this.renderTilt()}

  offsets(){
    const smoothing=clamp(Number(this.smooth.value)/100,.03,.35);
    this.tilt.x+=(this.tilt.targetX-this.tilt.x)*smoothing;
    this.tilt.y+=(this.tilt.targetY-this.tilt.y)*smoothing;
    return this.tilt.enabled?{x:this.tilt.x,y:this.tilt.y}:{x:0,y:0};
  }

  destroy(){
    if(this._orientationHandler)removeEventListener('deviceorientation',this._orientationHandler);
  }
}

window.PerceiverSpatialController=PerceiverSpatialController;
})();