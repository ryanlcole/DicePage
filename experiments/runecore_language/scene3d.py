"""RuneCore 3D coordinate storage, coil traversal and deterministic scene builder.

This module stores *scene voxels* and semantic Shaep object references, NOT
physical atoms or learned/model-synthesized chemistry. Source of truth remains
ReLiC project database; this is an independent experimental SQLite snapshot.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from collections import Counter
from typing import Iterable
import argparse
import json
import math
import sqlite3

SUPPORTED_PROMPT = 'create a scene with a lake, shore and building'
MATERIALS = {'grass', 'shore', 'sand', 'water', 'stone', 'wood', 'roof', 'glass', 'door'}


def coil_xy(radius: int, *, center_first: bool = True):
    """2D square-coil order. First nine at z=0 match owner's exact sequence."""
    if radius < 0: raise ValueError('radius must be nonnegative')
    if center_first: yield (0, 0)
    for r in range(1, radius + 1):
        yield (r, 0)
        for y in range(1, r + 1): yield (r, y)
        for x in range(r-1, -r-1, -1): yield (x, r)
        for y in range(r-1, -r-1, -1): yield (-r, y)
        for x in range(-r+1, r+1): yield (x, -r)
        for y in range(-r+1, 0): yield (r, y)
    if not center_first: yield (0, 0)


def coil_xyz(shell_radius: int, *, sphere_radius: float | None = None):
    """Expanding 3D Chebyshev shells; z=0, +1, -1, +2, -2, ...

    A coil is an INDEXING ORDER, not a physical sphere. Optional Euclidean
    sphere mask makes a spherical *subset* of the square-coil lattice.
    """
    if shell_radius < 0: raise ValueError('shell radius must be nonnegative')
    if sphere_radius is not None and sphere_radius < 0:
        raise ValueError('sphere radius must be nonnegative')
    if sphere_radius is None or sphere_radius >= 0: yield (0,0,0)
    for s in range(1,shell_radius+1):
        zs=[0]
        for v in range(1,s+1): zs.extend([v,-v])
        for z in zs:
            for x,y in coil_xy(s,center_first=False):
                if max(abs(x),abs(y),abs(z)) != s: continue
                if sphere_radius is not None and x*x+y*y+z*z > sphere_radius*sphere_radius: continue
                yield (x,y,z)


@dataclass(frozen=True)
class Voxel:
    x: int
    y: int
    z: int
    material: str
    shaep: str
    def __post_init__(self):
        if not all(type(i) is int for i in (self.x,self.y,self.z)):
            raise ValueError('voxel coordinates must be integers')
        if self.material not in MATERIALS: raise ValueError('unknown material')
        if not self.shaep: raise ValueError('Shaep reference required')


def interpret_scene_intent(command: str) -> str:
    """Explicitly bounded rule-based command interpreter. NOT an LLM."""
    words=set(command.lower().replace(',',' ').replace('.',' ').split())
    if {'lake','shore','building'} <= words and {'scene','create'} <= words:
        return 'lake_shore_building_v1'
    raise ValueError('unsupported scene command; no scene was created')


def build_scene(command: str = SUPPORTED_PROMPT) -> tuple[Voxel,...]:
    interpret_scene_intent(command)
    cells: dict[tuple[int,int,int],Voxel]={}
    def put(x,y,z,mat,obj):cells[(x,y,z)]=Voxel(x,y,z,mat,obj)
    # X is lateral, Y is vertical, Z is depth. Water and shore occupy Y=0.
    # The lake is elliptical in XZ; the shoreline is a ring, not an ocean.
    for z in range(-18,19):
        for x in range(-22,23):
            d=math.sqrt(((x+6)/7.5)**2+((z-3)/8.5)**2)
            if d<0.93: material,obj='water','shaep.lake'
            elif d<1.23: material,obj='shore','shaep.shore'
            else: material,obj='grass','shaep.land'
            put(x,-1,z,'stone','shaep.substrate')
            put(x,0,z,material,obj)
    # Building has 3D extent, front doorway faces negative Z.
    xmin,xmax,zmin,zmax=9,16,0,9
    for y in range(1,6):
        for z in range(zmin,zmax+1):
            for x in range(xmin,xmax+1):
                boundary=(x in (xmin,xmax) or z in (zmin,zmax))
                if not boundary:continue
                # Open doorway, not a solid stone patch.
                if z==zmin and x in (12,13) and y<=3:continue
                if y in (3,4) and ((x in (xmin,xmax) and z in (3,6)) or (z==zmin and x in (10,15))):
                    put(x,y,z,'glass','shaep.building.window')
                else:put(x,y,z,'wood','shaep.building.wall')
    for z in range(zmin-1,zmax+2):
        for x in range(xmin-1,xmax+2):
            # stepped pitched roof, ridge across Z
            y=6+min(3,max(0,4-abs(x-12)))
            put(x,y,z,'roof','shaep.building.roof')
    # Short footpath from building entrance to the shore.
    for z in range(-4,0):
        for x in (12,13):put(x,0,z,'sand','shaep.path')
    return tuple(cells[k] for k in sorted(cells))


def scene_sha(voxels: Iterable[Voxel]) -> str:
    payload=[(v.x,v.y,v.z,v.material,v.shaep) for v in voxels]
    return sha256(json.dumps(payload,separators=(',',':')).encode()).hexdigest()


class SceneStore:
    """Durable local SQLite snapshot with per-coordinate uniqueness and readback."""
    def __init__(self, path: str|Path):
        self.db=sqlite3.connect(str(path))
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY,value TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS voxels (
                x INTEGER NOT NULL,y INTEGER NOT NULL,z INTEGER NOT NULL,
                material TEXT NOT NULL,shaep TEXT NOT NULL,
                PRIMARY KEY(x,y,z)
            ) WITHOUT ROWID;
            CREATE INDEX IF NOT EXISTS idx_voxels_xz ON voxels(x,z);
        ''')
    def close(self):self.db.close()
    def populate_once(self,command: str):
        voxels=build_scene(command)
        with self.db:
            if self.db.execute('SELECT 1 FROM meta WHERE key="scene_sha256"').fetchone():
                raise RuntimeError('stored scene exists; explicit new version required')
            self.db.executemany('INSERT INTO voxels VALUES(?,?,?,?,?)',
                 ((v.x,v.y,v.z,v.material,v.shaep) for v in voxels))
            self.db.executemany('INSERT INTO meta VALUES(?,?)',(
                ('source_command',command),('intent','lake_shore_building_v1'),
                ('scene_sha256',scene_sha(voxels)),('status','EXPERIMENTAL_SCENE_NOT_CHEMISTRY'),
                ('coordinate_convention','x lateral, y vertical, z depth')))
        return {'voxel_count':len(voxels),'sha256':scene_sha(voxels)}
    def read_voxels(self):
        rows=self.db.execute('SELECT x,y,z,material,shaep FROM voxels ORDER BY x,y,z').fetchall()
        voxels=tuple(Voxel(*r) for r in rows)
        expected=self.db.execute('SELECT value FROM meta WHERE key="scene_sha256"').fetchone()
        if expected is None or scene_sha(voxels)!=expected[0]:
            raise RuntimeError('storage integrity failure')
        return voxels
    def view(self, camera, radius=38.0):
        if radius<=0:raise ValueError('radius must be positive')
        x,y,z=camera
        # Spatial query: excludes distant voxels rather than retrieving full scene.
        rows=self.db.execute('''SELECT x,y,z,material,shaep FROM voxels
           WHERE x BETWEEN ? AND ? AND y BETWEEN ? AND ? AND z BETWEEN ? AND ?''',
           (x-radius,x+radius,y-radius,y+radius,z-radius,z+radius))
        return tuple(Voxel(*r) for r in rows
                    if (r[0]-x)**2+(r[1]-y)**2+(r[2]-z)**2<=radius*radius)
    def export(self, path: str|Path):
        voxels=self.read_voxels()
        # Compact row spans: x/y fixed; contiguous z and matching mat/Shaep.
        spans=[]
        byrow={}
        for v in voxels:byrow.setdefault((v.x,v.y),[]).append(v)
        for (x,y),ordered in sorted(byrow.items()):
            ordered.sort(key=lambda v:v.z)
            if not ordered:continue
            first=last=ordered[0].z;material=ordered[0].material;shaep=ordered[0].shaep
            for v in ordered[1:]:
                if v.z==last+1 and v.material==material and v.shaep==shaep:last=v.z
                else:
                    spans.append([x,y,first,last,material,shaep]);first=last=v.z;material=v.material;shaep=v.shaep
            spans.append([x,y,first,last,material,shaep])
        document={'schema':'RuneCore.Scene3D/1','coord':'x lateral, y vertical, z depth',
                  'source_command':SUPPORTED_PROMPT,'voxel_count':len(voxels),
                  'sha256':scene_sha(voxels),
                  'classification':'EXPERIMENTAL_SCENE_NOT_CHEMISTRY_OR_TRAINED_LLM',
                  'spans':spans}
        Path(path).write_text(json.dumps(document,separators=(',',':')),encoding='utf-8')
        return document


def project_point(point,camera, *, yaw=0.0,pitch=0.0,focal=1.0,near=0.05):
    """Perspective camera: yaw=0 looks toward +Z, Y points up."""
    dx,dy,dz=(point[i]-camera[i] for i in range(3))
    sy,cy=math.sin(yaw),math.cos(yaw)
    sp,cp=math.sin(pitch),math.cos(pitch)
    right=dx*cy-dz*sy
    forward_xy=dx*sy+dz*cy
    up=dy*cp-forward_xy*sp
    depth=forward_xy*cp+dy*sp
    if depth<=near:return None
    return (focal*right/depth,focal*up/depth,depth)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--database',default='scene3d.sqlite3')
    p.add_argument('--export',default='scene_data.json')
    p.add_argument('--command',default=SUPPORTED_PROMPT)
    args=p.parse_args()
    store=SceneStore(args.database)
    try:
        result=store.populate_once(args.command)
        doc=store.export(args.export)
        print(json.dumps({**result,'spans':len(doc['spans']),'classification':doc['classification']}))
    finally:store.close()

if __name__=='__main__':main()
