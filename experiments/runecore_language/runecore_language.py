"""RuneCore Language/1 reference parser and finite-state rotator.

Experimental structural language, NOT a trained LLM and NOT quantum chemistry.
The conventions here implement the user's current ring examples and are
not promoted to scientific law or to the user's authoritative project database.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from math import lcm
import json
import re

RING_RE = re.compile(r"^RING\s+(\d+)\s+(CW|CCW)\s+([01]{1,256})$", re.I)
ATOM_RE = re.compile(r"^ATOM\s+([A-Za-z0-9_.-]+)\s+([A-Za-z0-9_.-]+)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)$", re.I)

@dataclass(frozen=True)
class Ring:
    index: int
    direction: str
    seed: str
    def __post_init__(self):
        if self.index < 1 or self.direction not in ('CW','CCW') or not re.fullmatch('[01]{1,256}',self.seed):
            raise ValueError('invalid ring')
        if self.direction != ('CW' if self.index % 2 else 'CCW'):
            raise ValueError('ring directions must alternate CW/CCW from inner ring')
    def at(self,tick:int)->str:
        if tick < 0: raise ValueError('negative tick')
        k=tick % len(self.seed)
        if self.direction=='CW': return self.seed[-k:]+self.seed[:-k] if k else self.seed
        return self.seed[k:]+self.seed[:k]
    def repeat(self)->int:
        for p in range(1,len(self.seed)+1):
            if self.at(p)==self.seed: return p
        raise AssertionError('unreachable')

@dataclass(frozen=True)
class Atom:
    slot: str
    symbol: str
    x: float
    y: float
    rings: tuple[Ring,...]
    def __post_init__(self):
        if not self.rings or tuple(r.index for r in self.rings)!=tuple(range(1,len(self.rings)+1)):
            raise ValueError('rings must be consecutive from 1')
    def glyph(self)->str:
        # Rotation invariant, identity deliberately excludes position, slot and phase.
        canonical=[]
        for r in self.rings:
            rotations=[r.seed[i:]+r.seed[:i] for i in range(len(r.seed))]
            canonical.append((r.index,r.direction,min(rotations)))
        return sha256(json.dumps(canonical,separators=(',',':')).encode()).hexdigest()[:16]
    def repeat(self)->int:
        return lcm(*(r.repeat() for r in self.rings))

def parse(text:str)->tuple[Atom,...]:
    """Strict, human-readable ring grammar. START/STOP delimit records, NOT motion."""
    atoms=[]; current=None; rings=[]; slots=set()
    for line_no,raw in enumerate(text.splitlines(),1):
        line=raw.split('#',1)[0].strip()
        if not line: continue
        m=ATOM_RE.fullmatch(line)
        if m:
            if current is not None: raise ValueError(f'line {line_no}: missing ENDATOM')
            slot,sym,x,y=m.groups()
            if slot in slots:raise ValueError(f'line {line_no}: duplicate slot')
            slots.add(slot);current=(slot,sym,float(x),float(y));rings=[]
        elif line.upper()=='ENDATOM':
            if current is None:raise ValueError(f'line {line_no}: ENDATOM without ATOM')
            atoms.append(Atom(*current,tuple(rings)))
            current=None; rings=[]
        else:
            m=RING_RE.fullmatch(line)
            if current is None or m is None: raise ValueError(f'line {line_no}: invalid statement')
            idx,di,bits=m.groups(); rings.append(Ring(int(idx),di.upper(),bits))
    if current is not None:raise ValueError('unclosed atom')
    return tuple(atoms)

def frame(atoms:tuple[Atom,...],tick:int,viewport:tuple[float,float,float,float])->dict:
    if tick<0:raise ValueError('negative tick')
    x0,y0,x1,y1=viewport
    if not x0 < x1 or not y0 < y1: raise ValueError('invalid viewport')
    visible=[{'slot':a.slot,'symbol':a.symbol,'x':a.x,'y':a.y,'glyph':a.glyph(),
              'runes':[{'index':r.index,'direction':r.direction,'bits':r.at(tick),'repeat':r.repeat()}
                       for r in a.rings]}
             for a in atoms if x0<=a.x<=x1 and y0<=a.y<=y1]
    return {'language':'RuneCore/1','tick':tick,'viewport':[x0,y0,x1,y1], 'atoms':visible,
            'status':'EXPERIMENTAL_ROTATIONAL_ENCODING_NOT_CHEMISTRY'}

EXAMPLE='''# Slots stay fixed; only ring phases advance.
ATOM RAM1 H -2 0
RING 1 CW 1000
ENDATOM
ATOM RAM2 H 2 0
RING 1 CW 1000
ENDATOM
ATOM RAM3 O 0 0
RING 1 CW 1010
RING 2 CCW 11101110
ENDATOM
ATOM RAM4 H 100 100
RING 1 CW 1000
ENDATOM
'''

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description='Reference RuneCore/1 interpreter')
    p.add_argument('--tick',type=int,default=0)
    p.add_argument('--view',type=float,nargs=4,default=[-4,-3,4,3])
    p.add_argument('--file',type=str)
    a=p.parse_args()
    from pathlib import Path
    atoms=parse(Path(a.file).read_text() if a.file else EXAMPLE)
    print(json.dumps(frame(atoms,a.tick,tuple(a.view)),indent=2))
