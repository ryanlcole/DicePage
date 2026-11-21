"""RuneCore Language/1: Rion -> Ring -> Rune -> Glyph -> Shaep.

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

# Official atomic numbers/symbols are periodic-table catalog metadata, NOT
# inferred binary ring encodings. IUPAC: https://iupac.org/what-we-do/periodic-table-of-elements/
_SYMBOLS = """H He Li Be B C N O F Ne Na Mg Al Si P S Cl Ar K Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr Rb Sr Y Zr Nb Mo Tc Ru Rh Pd Ag Cd In Sn Sb Te I Xe Cs Ba La Ce Pr Nd Pm Sm Eu Gd Tb Dy Ho Er Tm Yb Lu Hf Ta W Re Os Ir Pt Au Hg Tl Pb Bi Po At Rn Fr Ra Ac Th Pa U Np Pu Am Cm Bk Cf Es Fm Md No Lr Rf Db Sg Bh Hs Mt Ds Rg Cn Nh Fl Mc Lv Ts Og""".split()

@dataclass(frozen=True)
class Glyph:
    atomic_number: int
    symbol: str
    def as_dict(self):
        return {'atomic_number': self.atomic_number, 'symbol': self.symbol,
                'classification': 'REFERENCE_PERIODIC_ELEMENT'}

GLYPH_TABLE = {symbol: Glyph(i,symbol) for i,symbol in enumerate(_SYMBOLS,1)}
if len(GLYPH_TABLE)!=118 or len(_SYMBOLS)!=118:
    raise AssertionError('periodic Glyph catalog must contain 118 unique elements')

RING_RE = re.compile(r"^RING\s+(\d+)\s+(CW|CCW)\s+([01]{1,256})$", re.I)
RUNE_RE = re.compile(r"^(?:RUNE|ATOM)\s+([A-Za-z0-9_.-]+)\s+([A-Za-z0-9_.-]+)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)$", re.I)

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
class Rune:
    """An encoded element instance in a fixed memory slot, containing atomic Rings."""
    slot: str
    symbol: str
    x: float
    y: float
    rings: tuple[Ring,...]
    def __post_init__(self):
        if not self.rings or tuple(r.index for r in self.rings)!=tuple(range(1,len(self.rings)+1)):
            raise ValueError('rings must be consecutive from 1')
    def glyph(self)->Glyph|None:
        return GLYPH_TABLE.get(self.symbol)
    def pattern_signature(self)->str:
        """Rotation-invariant ring hash; not the periodic Glyph or atom identity."""
        canonical=[]
        for r in self.rings:
            rotations=[r.seed[i:]+r.seed[:i] for i in range(len(r.seed))]
            canonical.append((r.index,r.direction,min(rotations)))
        return sha256(json.dumps(canonical,separators=(',',':')).encode()).hexdigest()[:16]
    def repeat(self)->int:
        return lcm(*(r.repeat() for r in self.rings))

# Legacy Atom name is a compatibility alias only. Rune is the canonical element.
Atom = Rune

@dataclass(frozen=True)
class Shaep:
    """Bounded composition of Rune slots and candidate contacts, NOT proven chemistry."""
    members: tuple[str,...]
    contacts: tuple[tuple[str,str,int],...] = ()
    def __post_init__(self):
        if len(self.members)<2 or len(set(self.members))!=len(self.members):
            raise ValueError('Shaep requires distinct Rune slots')
        for donor,acceptor,sector in self.contacts:
            if donor not in self.members or acceptor not in self.members or donor==acceptor or sector<0:
                raise ValueError('invalid Shaep contact')
    def composition(self,runes:tuple[Rune,...])->dict:
        from collections import Counter
        by_slot={r.slot:r for r in runes}
        if any(m not in by_slot for m in self.members):raise ValueError('missing Rune')
        return dict(sorted(Counter(by_slot[m].symbol for m in self.members).items()))
    def status(self):return 'EXPERIMENTAL_ASSEMBLY_NOT_CHEMISTRY'


def parse(text:str)->tuple[Rune,...]:
    """Parse RUNE/ENDRUNE; accept ATOM/ENDATOM from legacy prototype."""
    runes=[];current=None;rings=[];slots=set();ending=None
    for line_no,raw in enumerate(text.splitlines(),1):
        line=raw.split('#',1)[0].strip()
        if not line:continue
        m=RUNE_RE.fullmatch(line)
        if m:
            if current is not None:raise ValueError(f'line {line_no}: missing {ending}')
            slot,sym,x,y=m.groups()
            if slot in slots:raise ValueError(f'line {line_no}: duplicate slot')
            slots.add(slot);current=(slot,sym,float(x),float(y));rings=[]
            ending='ENDRUNE' if line.upper().startswith('RUNE ') else 'ENDATOM'
        elif line.upper() in ('ENDRUNE','ENDATOM'):
            if current is None or line.upper()!=ending:raise ValueError(f'line {line_no}: invalid terminator')
            runes.append(Rune(*current,tuple(rings)))
            current=None;rings=[];ending=None
        else:
            m=RING_RE.fullmatch(line)
            if current is None or m is None:raise ValueError(f'line {line_no}: invalid statement')
            idx,di,bits=m.groups();rings.append(Ring(int(idx),di.upper(),bits))
    if current is not None:raise ValueError('unclosed Rune')
    return tuple(runes)

def frame(runes:tuple[Rune,...],tick:int,viewport:tuple[float,float,float,float])->dict:
    """Read-only visible Runes. Legacy 'atoms' response aliases 'runes'."""
    if tick<0:raise ValueError('negative tick')
    x0,y0,x1,y1=viewport
    if not x0<x1 or not y0<y1:raise ValueError('invalid viewport')
    visible=[]
    for r in runes:
        if not (x0<=r.x<=x1 and y0<=r.y<=y1):continue
        glyph=r.glyph()
        visible.append({'slot':r.slot,'rune':r.slot,'symbol':r.symbol,
          'glyph':glyph.as_dict() if glyph else
                  {'symbol':r.symbol,'classification':'UNKNOWN_NOT_PERIODIC_GLYPH'},
          'pattern_signature':r.pattern_signature(),'x':r.x,'y':r.y,
          'rings':[{'index':ring.index,'direction':ring.direction,
                    'bits':ring.at(tick),'repeat':ring.repeat()} for ring in r.rings]})
    return {'language':'RuneCore/1','tick':tick,'viewport':[x0,y0,x1,y1],
            'runes':visible,'atoms':visible,
            'status':'EXPERIMENTAL_ROTATIONAL_ENCODING_NOT_CHEMISTRY'}


EXAMPLE='''# Slots stay fixed; only ring phases advance.
RUNE RAM1 H -2 0
RING 1 CW 1000
ENDRUNE
RUNE RAM2 H 2 0
RING 1 CW 1000
ENDRUNE
RUNE RAM3 O 0 0
RING 1 CW 1010
RING 2 CCW 11101110
ENDRUNE
RUNE RAM4 H 100 100
RING 1 CW 1000
ENDRUNE
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
