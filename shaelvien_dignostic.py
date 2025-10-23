# shaelvien_daemon.py
from __future__ import annotations
import json, os, sys, time, traceback, socket, mimetypes
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import psutil, logging
from logging.handlers import RotatingFileHandler
import glyph_core, world_core

HOST,PORT="127.0.0.1",8787
def resource_path(p): base=getattr(sys,"_MEIPASS",None); 
if base and os.path.exists(base): return os.path.join(base,p)
return os.path.join(os.path.dirname(os.path.abspath(__file__)),p)
BASE=os.path.dirname(os.path.abspath(__file__))
LOGS=os.path.normpath(resource_path("logs")); os.makedirs(LOGS,exist_ok=True)
LOG=os.path.join(LOGS,"daemon.log")
logger=logging.getLogger("shaelvien_daemon"); logger.setLevel(logging.WARNING)
h=RotatingFileHandler(LOG,maxBytes=1_000_000,backupCount=3,encoding="utf-8")
h.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")); logger.addHandler(h)
def log_success(m): logger.warning("SUCCESS: %s",m)
def log_warn(m): logger.warning(m)
def log_error(m): logger.error(m)

# ---------- INLINE HUD (patched with /control fetch) ----------
_HUD_INLINE_HTML = r"""<!doctype html><html><head><meta charset='utf-8'>
<title>Shaelvien HUD — World</title>
<meta name='viewport' content='width=device-width,initial-scale=1.0'>
<link rel='icon' href='/assets/favicon.png'><style>
html,body{margin:0;padding:0;background:#0e1116;color:#e5e7eb;font-family:system-ui}
#topbar{display:flex;gap:8px;align-items:center;padding:8px 14px;background:#0b0e13;border-bottom:1px solid #1f2937}
.btn{background:#1f2937;color:#e5e7eb;border:1px solid #374151;border-radius:8px;padding:4px 8px;font-size:13px;cursor:pointer}
.btn.on{outline:1px solid #9fd66f}#stat{margin-left:auto;font-size:12px;color:#9ca3af}
</style></head><body><div id='topbar'>
<button id='btnWorld' class='btn'>World Mode</button>
<button id='btnLinks' class='btn'>Show Links</button>
<button id='btnSimple' class='btn'>Simplify Anim</button>
<button id='btnGlyph' class='btn'>Glyph Mode</button><span id='stat'>...</span></div>
<canvas id='canvas'></canvas>
<script>
;(async()=>{const API={state:'/state',map:'/map',world:'/world',control:'/control'};
let toggles={showLinks:false,simpleAnim:false,glyphMode:true,worldMode:true};
async function loadSettings(){try{const r=await fetch(API.control);if(r.ok){const j=await r.json();if(j.settings)toggles=j.settings;}}catch(e){}}
async function postCtl(){try{await fetch(API.control,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(toggles)});}catch(e){}}
const bW=document.getElementById('btnWorld'),bL=document.getElementById('btnLinks'),bS=document.getElementById('btnSimple'),bG=document.getElementById('btnGlyph'),stat=document.getElementById('stat');
function sync(){bW.classList.toggle('on',!!toggles.worldMode);bL.classList.toggle('on',!!toggles.showLinks);
bS.classList.toggle('on',!!toggles.simpleAnim);bG.classList.toggle('on',!!toggles.glyphMode);}
await loadSettings();sync();
bW.onclick=()=>{toggles.worldMode=!toggles.worldMode;sync();postCtl();};
bL.onclick=()=>{toggles.showLinks=!toggles.showLinks;sync();postCtl();};
bS.onclick=()=>{toggles.simpleAnim=!toggles.simpleAnim;sync();postCtl();};
bG.onclick=()=>{toggles.glyphMode=!toggles.glyphMode;sync();postCtl();};
const c=document.getElementById('canvas'),ctx=c.getContext('2d');
function resize(){const dpr=Math.max(1,window.devicePixelRatio||1);c.width=c.clientWidth*dpr;c.height=c.clientHeight*dpr;ctx.setTransform(dpr,0,0,dpr,0,0);}window.addEventListener('resize',resize);resize();
function linkColor(h){return h>=.8?'#9fd66f':h>=.5?'#e8c96a':'#ff7a6b';}
function drawNode(n,x,y){const r=20,h=n.health||0;ctx.save();ctx.translate(x,y);
ctx.beginPath();ctx.arc(0,0,r,0,2*Math.PI);ctx.strokeStyle=linkColor(h);ctx.lineWidth=3;ctx.stroke();
ctx.textAlign='center';ctx.font='18px system-ui';ctx.fillText(n.glyph||n.id,0,5);ctx.restore();}
let map={},world={regions:[],global:{brightness:1}};async function tick(){
try{const[m,s,w]=await Promise.all([fetch(API.map),fetch(API.state),fetch(API.world)]);
map=await m.json();world=await w.json();}catch(e){}
draw();}function draw(){const w=c.clientWidth,h=c.clientHeight;ctx.clearRect(0,0,w,h);
if(toggles.worldMode){ctx.fillStyle=`rgba(80,120,160,${.2+(1-world.global.haze||0)*.2})`;ctx.fillRect(0,0,w,h);}
for(const n of map.nodes||[]){const x=w*(Math.random()*0.8+0.1),y=h*(Math.random()*0.8+0.1);drawNode(n,x,y);}
stat.textContent=new Date().toLocaleTimeString();requestAnimationFrame(draw);}
setInterval(tick,1000);requestAnimationFrame(draw);})();
</script></body></html>"""

def get_state(): 
    try:
        cpu=psutil.cpu_percent(interval=None); mem=psutil.virtual_memory()
        return {"cpu":cpu,"mem":{"percent":mem.percent},"ts":int(time.time()*1000)}
    except: return {"cpu":0,"mem":{"percent":0},"ts":int(time.time()*1000)}

class H(SimpleHTTPRequestHandler):
    def translate_path(self,p): 
        p=p.split("?",1)[0]; 
        if p.startswith("/assets/"): return os.path.join(BASE,p[8:])
        return os.path.join(BASE,p.lstrip("/"))
    def log_message(self,*a): pass
    def do_GET(self):
        try:
            p=urlparse(self.path).path
            if p in ("/","/index.html"): self._html("<meta http-equiv='refresh' content='0;url=/hud'>"); return
            if p=="/hud": glyph_core.write_hud_heartbeat(); self._html(_HUD_INLINE_HTML); return
            if p=="/state": self._json(get_state()); return
            if p=="/map": self._json(glyph_core.build_graph({"daemon_alive":1})); return
            if p=="/world": self._json(world_core.build_world({"daemon_alive":1})); return
            if p=="/control": self._json({"settings":glyph_core.load_settings()}); return
            self._json({"err":"404"} ,404)
        except Exception as e: log_error(str(e)); self._json({"err":"internal"},500)
    def do_POST(self):
        try:
            p=urlparse(self.path).path; ln=int(self.headers.get("Content-Length","0") or 0)
            raw=self.rfile.read(ln) if ln else b"{}"; data=json.loads(raw.decode("utf-8"))
            if p=="/control": glyph_core.save_settings(data); self._json({"ok":True,"settings":glyph_core.load_settings()}); return
            self._json({"err":"404"},404)
        except Exception as e: log_error(str(e)); self._json({"err":"internal"},500)
    def _json(self,o,c=200): b=json.dumps(o).encode(); self.send_response(c)
        ;self.send_header("Content-Type","application/json"); self.send_header("Content-Length",str(len(b)))
        ;self.end_headers(); self.wfile.write(b)
    def _html(self,h): b=h.encode(); self.send_response(200)
        ;self.send_header("Content-Type","text/html"); self.send_header("Content-Length",str(len(b)))
        ;self.end_headers(); self.wfile.write(b)

def run():
    s=HTTPServer((HOST,PORT),H); log_success(f"Daemon @ http://{HOST}:{PORT}")
    try: s.serve_forever(0.2)
    except KeyboardInterrupt: pass
    finally: s.server_close()

if __name__=="__main__":
    print("Starting Shaelvien Daemon..."); run()
