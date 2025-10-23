from dataclasses import dataclass, asdict
from typing import Dict, List, Callable, Optional, Any

@dataclass
class Glyph:
    id: str
    type: str
    color: str
    active: bool=False
    x: Optional[float]=None
    y: Optional[float]=None
    resonance: Optional[float]=None

PALETTE = {
    "daemon":"#9b59b6","tray":"#3498db","hud":"#2ecc71",
    "spark":"#f1c40f","solar":"#e67e22","lunar":"#95a5a6","stone":"#7f8c8d",
    "element":"#1abc9c","matter":"#16a085","dna":"#e84393","wave":"#2980b9",
}
_REG: Dict[str,Glyph] = {}
def _seed():
    for g in [
        ("daemon","system"),("tray","system"),("hud","system"),
        ("spark","system"),("solar","system"),("lunar","system"),("stone","system"),
        ("element","placeholder"),("matter","placeholder"),("dna","placeholder"),("wave","placeholder")]:
        _REG[g[0]] = Glyph(g[0], g[1], PALETTE[g[0]])
_seed()

def serialize_map()->List[Dict[str,Any]]: return [asdict(g) for g in _REG.values()]

def activate(gid:str,x:float,y:float,res:Callable[[Dict[str,Any]],float]):
    g=_REG.get(gid); 
    if not g: raise KeyError(gid)
    g.active=True; g.x=float(x); g.y=float(y)
    try: g.resonance=float(res(asdict(g)))
    except Exception: g.resonance=1.0

def deactivate(gid:str):
    g=_REG.get(gid); 
    if not g: return
    g.active=False; g.x=g.y=g.resonance=None
