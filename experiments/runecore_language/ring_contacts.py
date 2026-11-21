"""Experimental label-blind rotating zero-site compatibility search.

No forces, energetics, chemical valence, or physical bonding are modeled.
Contact is exact phase-aligned complement within the acceptor's outer-ring sector.
"""
from __future__ import annotations
from dataclasses import dataclass
from math import hypot, lcm
from runecore_language import Atom

@dataclass(frozen=True)
class Candidate:
    donor: str
    acceptor: str
    sector: int
    repeat: int
    distance: float

def candidates(atoms:tuple[Atom,...],radius:float=4.0):
    if radius<=0:raise ValueError('radius must be positive')
    result=[]
    for acceptor in atoms:
        outer=acceptor.rings[-1]
        for donor in atoms:
            if donor.slot==acceptor.slot or hypot(donor.x-acceptor.x,donor.y-acceptor.y)>radius:continue
            source=donor.rings[-1]
            n,m=len(source.seed),len(outer.seed)
            if n>=m or m%n:continue
            period=lcm(source.repeat(),outer.repeat())
            for sector in range(m//n):
                if all((source.at(t)[::-1] if source.direction!=outer.direction else source.at(t))
                       == ''.join('1' if c=='0' else '0' for c in outer.at(t)[sector*n:(sector+1)*n])
                       for t in range(period)):
                    result.append(Candidate(donor.slot,acceptor.slot,sector,period,
                                            hypot(donor.x-acceptor.x,donor.y-acceptor.y)))
    return tuple(sorted(result,key=lambda b:(b.donor,b.acceptor,b.sector)))

def assign(atoms:tuple[Atom,...],radius:float=4.0):
    """Maximum-cardinality bipartite matching: 1 donor and 1 acceptor sector per link."""
    possible=candidates(atoms,radius)
    by_donor={}
    for p in possible:by_donor.setdefault(p.donor,[]).append(p)
    booked={}
    def visit(donor,seen):
        for p in by_donor[donor]:
            key=(p.acceptor,p.sector)
            if key in seen:continue
            seen.add(key)
            if key not in booked or visit(booked[key].donor,seen):
                booked[key]=p;return True
        return False
    for donor in sorted(by_donor):visit(donor,set())
    return tuple(sorted(booked.values(),key=lambda p:(p.acceptor,p.sector,p.donor)))

def composite(acceptor:Atom,donors:tuple[Atom,...],links,tick:int):
    by_slot={a.slot:a for a in donors}
    ring=acceptor.rings[-1];raw=ring.at(tick);mask=['0']*len(raw)
    for link in links:
        if link.acceptor!=acceptor.slot:continue
        donor=by_slot[link.donor];source=donor.rings[-1]
        contact=source.at(tick)[::-1] if source.direction!=ring.direction else source.at(tick)
        start=link.sector*len(contact)
        for i,bit in enumerate(contact):
            if bit=='1' and raw[start+i]=='1':raise ValueError('link violates zero-site capacity')
            if bit=='1' and mask[start+i]=='1':raise ValueError('contact overlap')
            mask[start+i]=bit
    return {'exposure':raw,'contacts':''.join(mask),
            'contact':''.join('1' if r=='1' or m=='1' else '0' for r,m in zip(raw,mask))}


def shaeps_from_links(atoms:tuple[Atom,...],links)->tuple:
    """Connected Rune structures are provisional Shaeps, not proven molecules."""
    from runecore_language import Shaep
    by_slot={a.slot:a for a in atoms}
    parent={a.slot:a.slot for a in atoms}
    def root(x):
        while parent[x]!=x:x=parent[x]
        return x
    for link in links:
        if link.donor not in by_slot or link.acceptor not in by_slot:
            raise ValueError('link references absent Rune')
        a,b=root(link.donor),root(link.acceptor)
        if a!=b:parent[max(a,b)]=min(a,b)
    groups={}
    for slot in by_slot:groups.setdefault(root(slot),[]).append(slot)
    out=[]
    for slots in groups.values():
        if len(slots)<2:continue
        members=tuple(sorted(slots))
        contacts=tuple(sorted((x.donor,x.acceptor,x.sector) for x in links
                              if x.donor in members and x.acceptor in members))
        out.append(Shaep(members,contacts))
    return tuple(sorted(out,key=lambda s:s.members))
