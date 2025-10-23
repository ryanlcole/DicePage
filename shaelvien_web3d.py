# shaelvien_web3d.py
# ShaelvienOS – WebGL2 viewer (points + bonds + smooth lerp; no external libs)

import json, threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from shaelvien_logger import log

_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>Shaelvien WebGL Field</title>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<style>
html,body{margin:0;height:100%;background:#050510;overflow:hidden;color:#bcd;font-family:system-ui}
#info{position:fixed;top:8px;left:8px;background:#1119;padding:5px 9px;border-radius:8px;font-size:12px}
canvas{display:block;width:100%;height:100%}
</style>
</head>
<body>
<div id="info">Shaelvien WebGL — <span id="stat">connecting…</span></div>
<canvas id="gl"></canvas>
<script>
const canvas=document.getElementById('gl');
const gl=canvas.getContext('webgl2',{antialias:true});
if(!gl){document.body.innerHTML='WebGL2 required';throw new Error('no webgl2');}
let W,H;function resize(){W=canvas.width=innerWidth;H=canvas.height=innerHeight;gl.viewport(0,0,W,H);}resize();addEventListener('resize',resize);

// Programs (points)
const vPoints=`#version 300 es
precision highp float;
layout(location=0)in vec3 pos;
layout(location=1)in vec3 col;
layout(location=2)in float size;
uniform mat4 proj;
out vec3 vcol;
void main(){ vcol=col; gl_Position=proj*vec4(pos,1.0); gl_PointSize=size; }
`;
const fPoints=`#version 300 es
precision highp float;
in vec3 vcol; out vec4 outc;
void main(){
  float d=length(gl_PointCoord-vec2(0.5));
  float a=smoothstep(0.5,0.0,d);
  outc=vec4(vcol, a);
}`;
const vLines=`#version 300 es
precision highp float;
layout(location=0)in vec3 pos;
layout(location=1)in vec3 col;
uniform mat4 proj;
out vec3 vcol;
void main(){ vcol=col; gl_Position=proj*vec4(pos,1.0); }
`;
const fLines=`#version 300 es
precision highp float;
in vec3 vcol; out vec4 outc;
void main(){ outc=vec4(vcol, 0.85); }
`;

function compile(src, type){ const sh=gl.createShader(type); gl.shaderSource(sh,src); gl.compileShader(sh); if(!gl.getShaderParameter(sh,gl.COMPILE_STATUS)) throw gl.getShaderInfoLog(sh); return sh; }
function program(vs,fs){ const p=gl.createProgram(); gl.attachShader(p,compile(vs,gl.VERTEX_SHADER)); gl.attachShader(p,compile(fs,gl.FRAGMENT_SHADER)); gl.linkProgram(p); return p; }

const progPts=program(vPoints,fPoints);
const progLin=program(vLines,fLines);
const uProjPts=gl.getUniformLocation(progPts,'proj');
const uProjLin=gl.getUniformLocation(progLin,'proj');

// buffers
const vaoPts=gl.createVertexArray(); gl.bindVertexArray(vaoPts);
const bufPos=gl.createBuffer(), bufCol=gl.createBuffer(), bufSize=gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, bufPos); gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0,3,gl.FLOAT,false,0,0);
gl.bindBuffer(gl.ARRAY_BUFFER, bufCol); gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1,3,gl.FLOAT,false,0,0);
gl.bindBuffer(gl.ARRAY_BUFFER, bufSize); gl.enableVertexAttribArray(2); gl.vertexAttribPointer(2,1,gl.FLOAT,false,0,0);

const vaoLin=gl.createVertexArray(); gl.bindVertexArray(vaoLin);
const bufLinePos=gl.createBuffer(), bufLineCol=gl.createBuffer();
gl.bindBuffer(gl.ARRAY_BUFFER, bufLinePos); gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0,3,gl.FLOAT,false,0,0);
gl.bindBuffer(gl.ARRAY_BUFFER, bufLineCol); gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1,3,gl.FLOAT,false,0,0);

function mat4persp(fov,asp,n,f){const t=Math.tan(fov/2)*n;const r=t*asp;return [
n/r,0,0,0,
0,n/t,0,0,
0,0,-(f+n)/(f-n),-1,
0,0,-(2*f*n)/(f-n),0];}

let nodes=[]; // persistent nodes {pos:[x,y,z], tgt:[x,y,z], col:[r,g,b], size, id}
function ensureNodes(n){
  while(nodes.length<n){
    const theta=Math.random()*6.283, phi=Math.acos(2*Math.random()-1), R=48+(Math.random()*8-4);
    const x=R*Math.sin(phi)*Math.cos(theta), y=R*Math.cos(phi), z=R*Math.sin(phi)*Math.sin(theta);
    nodes.push({pos:[x,y,z], tgt:[x,y,z], col:[0.7,0.8,1.0], size:6, id:nodes.length});
  }
  if(nodes.length>n) nodes = nodes.slice(0,n);
}

function lerp(a,b,t){ return a+(b-a)*t; }
function vlerp(out, a, b, t){ out[0]=lerp(a[0],b[0],t); out[1]=lerp(a[1],b[1],t); out[2]=lerp(a[2],b[2],t); }

let tClock=0;
function render(ts){
  requestAnimationFrame(render); 
  const dt = 0.016; tClock += dt;

  const asp=W/H, proj=new Float32Array(mat4persp(1.1,asp,0.1,200.0));
  // camera (gentle orbit)
  const c=Math.cos(tClock*0.15), s=Math.sin(tClock*0.15);
  const view=[c,0,-s,0, 0,1,0,0, s,0,c,-82, 0,0,0,1];
  const m=new Float32Array(16);
  for(let r=0;r<4;r++)for(let c2=0;c2<4;c2++){m[r*4+c2]=0;for(let k=0;k<4;k++)m[r*4+c2]+=proj[r*4+k]*view[k*4+c2];}

  // smooth movement to targets
  for(const n of nodes){
    vlerp(n.pos, n.pos, n.tgt, 0.08); // smooth follow
  }

  // points upload
  const P=new Float32Array(nodes.flatMap(n=>n.pos));
  const C=new Float32Array(nodes.flatMap(n=>n.col));
  const S=new Float32Array(nodes.map(n=>n.size));

  // bonds
  const thresh=22;
  const LP=[], LC=[];
  for(let i=0;i<nodes.length;i++){
    const a=nodes[i].pos;
    for(let j=i+1;j<nodes.length;j++){
      const b=nodes[j].pos;
      const dx=a[0]-b[0], dy=a[1]-b[1], dz=a[2]-b[2];
      const d=Math.sqrt(dx*dx+dy*dy+dz*dz);
      if(d<thresh){
        const fade=Math.max(0.15, 1-(d/thresh));
        const col=[0.88*fade, 0.92*fade, 1.0*fade];
        LP.push(a[0],a[1],a[2], b[0],b[1],b[2]);
        LC.push(col[0],col[1],col[2], col[0],col[1],col[2]);
      }
    }
  }

  gl.clearColor(0.02,0.02,0.06,1); gl.clear(gl.COLOR_BUFFER_BIT);

  // draw lines
  if(LP.length){
    gl.useProgram(progLin);
    gl.uniformMatrix4fv(uProjLin,false,m);
    gl.bindVertexArray(vaoLin);
    gl.bindBuffer(gl.ARRAY_BUFFER, bufLinePos); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(LP), gl.DYNAMIC_DRAW);
    gl.bindBuffer(gl.ARRAY_BUFFER, bufLineCol); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(LC), gl.DYNAMIC_DRAW);
    gl.drawArrays(gl.LINES, 0, LP.length/3);
  }

  // draw points
  gl.useProgram(progPts);
  gl.uniformMatrix4fv(uProjPts,false,m);
  gl.bindVertexArray(vaoPts);
  gl.bindBuffer(gl.ARRAY_BUFFER, bufPos); gl.bufferData(gl.ARRAY_BUFFER, P, gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER, bufCol); gl.bufferData(gl.ARRAY_BUFFER, C, gl.DYNAMIC_DRAW);
  gl.bindBuffer(gl.ARRAY_BUFFER, bufSize); gl.bufferData(gl.ARRAY_BUFFER, S, gl.DYNAMIC_DRAW);
  gl.drawArrays(gl.POINTS, 0, nodes.length);
}
render(0);

async function fetchState(){
  try{
    const r=await fetch('/state',{cache:'no-store'}); if(!r.ok) throw 0;
    const j=await r.json();
    document.getElementById('stat').textContent=`Connected ✓ — ${j.count} | avgE ${j.avgE.toFixed(3)}`;
    ensureNodes(j.count);
    // Update targets/colors/sizes only; positions lerp client-side for smoothness
    for(let i=0;i<j.count;i++){
      const it=j.items[i]; const n=nodes[i];
      const e=it.energy, ph=it.phase;
      const R=40 + Math.sin(ph + e)*6;
      const theta = (i/j.count)*6.283 + Math.sin(ph)*0.2;      // stable ring-ish distribution
      const phi   = Math.acos(2*(i/j.count)-1);                // even-ish spread
      n.tgt = [ R*Math.sin(phi)*Math.cos(theta),
                R*Math.cos(phi),
                R*Math.sin(phi)*Math.sin(theta) ];
      n.col = [ 0.45 + 0.5*Math.sin(ph+0.2),
                0.45 + 0.5*Math.cos(ph+0.5),
                0.55 + 0.4*Math.sin(ph+1.0) ];
      n.size = 6 + e*8;
    }
  }catch(e){
    document.getElementById('stat').textContent='connecting…';
  }finally{
    setTimeout(fetchState, 180);
  }
}
fetchState();
</script>
</body>
</html>
"""

class _Handler(BaseHTTPRequestHandler):
    FIELD_REF = None
    def _json_state(self):
        items = []
        prts = getattr(self.FIELD_REF, "particles", []) if self.FIELD_REF else []
        for p in prts:
            items.append({
                "energy": float(p.energy),
                "phase": float(p.phase),
                "element": getattr(p, "element", "Neutral"),
                "symbol": getattr(p, "symbol", "⦿"),
            })
        avgE = sum(x["energy"] for x in items)/len(items) if items else 0.0
        return {"count": len(items), "avgE": avgE, "items": items}

    def do_GET(self):
        path = urlparse(self.path).path
        if path in ("/", "/index.html"):
            data = _HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type","text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers(); self.wfile.write(data)
        elif path == "/state":
            js = json.dumps(self._json_state()).encode()
            self.send_response(200)
            self.send_header("Content-Type","application/json")
            self.send_header("Cache-Control","no-store")
            self.send_header("Content-Length", str(len(js)))
            self.end_headers(); self.wfile.write(js)
        else:
            self.send_response(404); self.end_headers()

class ShaelvienWeb3D(threading.Thread):
    def __init__(self, field_ref, host="127.0.0.1", port=8787, log=lambda m: None):
        super().__init__(daemon=True)
        self.host, self.port = host, port
        self.httpd = None
        _Handler.FIELD_REF = field_ref

    def run(self):
        try:
            self.httpd = HTTPServer((self.host, self.port), _Handler)
            log.success("[Web3D] Serving http://%s:%s", self.host, self.port)
            self.httpd.serve_forever()
        except Exception as e:
            log.error("[Web3D] Error: %s", e)

    def stop(self):
        try:
            if self.httpd:
                self.httpd.shutdown()
                log.warning("[Web3D] Stopped.")
        except Exception:
            pass
