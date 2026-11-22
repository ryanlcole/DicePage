"""Create a standalone Rune-backed 3D viewer from SQLite-exported JSON.
No network fetch, no model inference, no physics claims. Viewer renders only geometry.
"""
from pathlib import Path
import json

BASE=Path(__file__).resolve().parent
html=(BASE/'viewer3d_template.html').read_text(encoding='utf-8')
archive=json.loads((BASE/'scene3d_runes.json').read_text(encoding='utf-8'))
if archive['schema']!='RuneCore.Scene3D/2':raise RuntimeError('wrong schema')
html=html.replace('RuneCore • 3D Scene','RuneCore • 3D Rune-Shaep Scene')
html=html.replace('canvas{width:100%;height:100%;display:block;touch-action:none}',
                  'canvas{width:100%;height:100%;display:block;touch-action:none}#rion-overlay{position:fixed;inset:0;pointer-events:none;z-index:2}')
html=html.replace('<div id="stick"', '<canvas id="rion-overlay" aria-hidden="true"></canvas><div id="stick"')
html=html.replace("if(archive.schema!=='RuneCore.Scene3D/1')", "if(archive.schema!=='RuneCore.Scene3D/2')")
html=html.replace("const materials={grass:[.22,.44,.29],shore:[.73,.64,.42],sand:[.86,.73,.48],water:[.10,.45,.66],stone:[.31,.37,.41],wood:[.57,.34,.19],roof:[.55,.24,.23],glass:[.39,.72,.82],door:[.33,.22,.12]};",
"""// Appearance is stored with Shaep bindings, not hard-coded from element names.
const shaeps=archive.shaep_bindings;
const waterModel=shaeps['shaep.lake']?.rune_model;
if(!waterModel || waterModel.composition.H!==2 || waterModel.composition.O!==1)throw Error('Missing validated experimental H2O Rune template');
const overlay=document.querySelector('#rion-overlay'),rctx=overlay.getContext('2d');
function rotateBits(seed,direction,tick){const k=tick%seed.length;return k===0?seed:(direction==='CW'?seed.slice(-k)+seed.slice(0,-k):seed.slice(k)+seed.slice(0,k))}
// Alternate full contact state and oxygen raw outer-ring state; contacts
// are recomputed from the two recorded hydrogen donors at each phase.
function contactDensity(subtick){const p=Math.floor(subtick/2),outer=waterModel.runes[2].rings.at(-1),raw=rotateBits(outer.seed,outer.direction,p);
 if(subtick%2)return raw.split('').filter(x=>x==='1').length/raw.length;
 const mask=Array(raw.length).fill('0');for(const link of waterModel.contacts){const donor=waterModel.runes.find(r=>r.slot===link.donor),source=donor.rings.at(-1);
 const bits=rotateBits(source.seed,source.direction,p),contact=source.direction===outer.direction?bits:bits.split('').reverse().join('');
 for(let i=0;i<contact.length;i++){const k=link.sector*contact.length+i;
 if(contact[i]==='1'){if(raw[k]==='1'||mask[k]==='1')throw Error('Invalid double-occupied contact');mask[k]='1';}}
 }
 return raw.split('').reduce((n,v,i)=>n+((v==='1'||mask[i]==='1')?1:0),0)/raw.length;}
function sphericalCoil(count,radius,cx,cy,cz){const pts=[],ang=Math.PI*(3-Math.sqrt(5));for(let i=0;i<count;i++){
 const yy=1-2*(i+.5)/count,rr=Math.sqrt(Math.max(0,1-yy*yy)),a=i*ang;
 pts.push([cx+radius*rr*Math.cos(a),cy+radius*yy,cz+radius*rr*Math.sin(a)]);
 }return pts;}
function drawRionDetail(now){const dd=Math.min(2,devicePixelRatio||1),W=innerWidth,H=innerHeight;
 if(overlay.width!==Math.round(W*dd)||overlay.height!==Math.round(H*dd)){overlay.width=Math.round(W*dd);overlay.height=Math.round(H*dd)}
 rctx.setTransform(dd,0,0,dd,0,0);rctx.clearRect(0,0,W,H);
 const sy=Math.sin(cam.yaw),cy=Math.cos(cam.yaw),sp=Math.sin(cam.pitch),cp=Math.cos(cam.pitch);
 const focal=H/(2*Math.tan(1.10/2)),frame=Math.floor(now/400),maxdist=12;
 function point(v){const dx=v[0]-cam.x,dy=v[1]-cam.y,dz=v[2]-cam.z;
  const right=dx*cy-dz*sy,forward=dx*sy+dz*cy,up=dy*cp-forward*sp,depth=forward*cp+dy*sp;
  if(depth<.15||depth>maxdist)return null;
  const x=W/2+focal*right/depth,y=H/2-focal*up/depth;
  return x>-8&&x<W+8&&y>-8&&y<H+8?[x,y,depth]:null;}
 const sources=cells.filter(c=>c.shaep==='shaep.lake' && (c.x-cam.x)**2+(c.y-cam.y)**2+(c.z-cam.z)**2<maxdist*maxdist).sort((a,b)=>((a.x-cam.x)**2+(a.y-cam.y)**2+(a.z-cam.z)**2)-((b.x-cam.x)**2+(b.y-cam.y)**2+(b.z-cam.z)**2)).slice(0,6);
 for(const c of sources){for(const r of waterModel.runes){const pos=r.center_offset,xx=c.x+pos[0],yy=c.y+pos[1]+.16,zz=c.z+pos[2];
   for(const ring of r.rings){const bits=rotateBits(ring.seed,ring.direction,frame),radius=.105+.05*ring.index,sites=sphericalCoil(bits.length,radius,xx,yy,zz);
     for(let i=0;i<bits.length;i++){const p=point(sites[i]);if(!p)continue;
       const rad=Math.max(1.5,Math.min(5.6,18/p[2]));rctx.beginPath();rctx.arc(p[0],p[1],rad,0,Math.PI*2);
       if(bits[i]==='1'){rctx.fillStyle=r.glyph.symbol==='O'?'rgba(255,199,124,.92)':'rgba(109,235,244,.90)';rctx.fill();}
       else{rctx.lineWidth=1.3;rctx.strokeStyle='rgba(255,169,105,.80)';rctx.stroke();}
     }
   }
 }}
}
""")
html=html.replace('const base=materials[c.material];if(!base)throw Error(\'Unknown material\');',
    "const base=shaeps[c.shaep]?.appearance.rgb;if(!base)throw Error('Unbound Shaep appearance');")
html=html.replace("uniform float uTime;", "uniform float uTime;uniform float uRunePulse;")
html=html.replace("(0.88+0.12*sin(uTime*1.3+vPosition.x*0.74+vPosition.z*0.43))",
                  "((0.65+0.35*uRunePulse)*(0.96+0.04*sin(uTime*1.3+vPosition.x*0.74+vPosition.z*0.43)))")
html=html.replace("time:gl.getUniformLocation(program,'uTime')", "time:gl.getUniformLocation(program,'uTime'),runePulse:gl.getUniformLocation(program,'uRunePulse')")
html=html.replace("const shade=mesh[i+6]>.5?.93+.07*Math.sin(now*.0013+mesh[i]*.7+mesh[i+2]*.4):1;",
                  "const shade=mesh[i+6]>.5?(.65+.35*contactDensity(Math.floor(now/200)))*(.96+.04*Math.sin(now*.0013+mesh[i]*.7+mesh[i+2]*.4)):1;")
html=html.replace("gl.uniform1f(uniform.time,now*.001);", "gl.uniform1f(uniform.time,now*.001);gl.uniform1f(uniform.runePulse,contactDensity(Math.floor(now/200)));")
html=html.replace("requestAnimationFrame(tick)}", "drawRionDetail(now);requestAnimationFrame(tick)}")
html=html.replace('__SCENE_JSON__',json.dumps(archive,separators=(',',':')).replace('<','\\u003c'))
if '__SCENE_JSON__' in html:raise RuntimeError('JSON substitution failed')
(BASE/'viewer3d_runes.html').write_text(html,encoding='utf-8')
print('Generated', len(html), 'bytes')
