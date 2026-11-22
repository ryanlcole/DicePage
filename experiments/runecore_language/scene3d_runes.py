"""RuneCore.Scene3D/2: 3D storage with provenance-tagged Rune/Shaep descriptors.

No trained LLM, atomic physics, chemical bond inference, or globally mutable
ReLiC canon is implied. Existing spatial data stay immutable. Visual appearance
is art-directed metadata; Rion state only modulates an experimental overlay.
"""
from __future__ import annotations
from dataclasses import asdict
from hashlib import sha256
from pathlib import Path
from math import cos, sin, sqrt, pi, tan
from typing import Iterable
import json
import sqlite3

from scene3d import SceneStore, Voxel, SUPPORTED_PROMPT, project_point
from runecore_language import EXAMPLE, GLYPH_TABLE, parse
from ring_contacts import assign, composite, shaeps_from_links

SCHEMA = 'RuneCore.Scene3D/2'
STATUS = 'EXPERIMENTAL_VISUAL_ENCODING_NOT_CHEMISTRY_OR_TRAINED_LLM'
# These are artist-chosen scene colors, not inferred electron spectra.
ART_COLORS = {
    'shaep.lake': (0.10, 0.45, 0.66),
    'shaep.shore': (0.73, 0.64, 0.42),
    'shaep.land': (0.22, 0.44, 0.29),
    'shaep.substrate': (0.31, 0.37, 0.41),
    'shaep.building.wall': (0.57, 0.34, 0.19),
    'shaep.building.roof': (0.55, 0.24, 0.23),
    'shaep.building.window': (0.39, 0.72, 0.82),
    'shaep.path': (0.86, 0.73, 0.48),
}
REFERENCES = [
    'owner-provided: H 1000 0100 0010 0001',
    'owner-provided: O inner 1010 0101; outer 11101110 11011101 10111011 01110111',
    'https://github.com/ryanlcole/DicePage/pull/58',
]


def canonical(obj: object) -> str:
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def build_descriptors(used_shaeps: Iterable[str]) -> dict:
    """Shared scene-object bindings; only water has an explicit Rune experiment."""
    used = set(used_shaeps)
    unknown = used - ART_COLORS.keys()
    if unknown:
        raise ValueError(f'unknown appearance for Shaep scene groups: {sorted(unknown)}')
    runes = parse(EXAMPLE)[:3]
    links = assign(runes, radius=4.0)
    assemblies = shaeps_from_links(runes, links)
    if len(links) != 2 or len(assemblies) != 1 or assemblies[0].composition(runes) != {'H': 2, 'O': 1}:
        raise AssertionError('water demonstration is not reproducible')
    water = {
        'model': 'shaep.h2o.rotational_demo',
        'kind': 'RUNE_BACKED_EXPERIMENT',
        'composition': {'H': 2, 'O': 1},
        'runes': [
            {'slot':r.slot,'glyph':r.glyph().as_dict(),
             'rings':[{'index':a.index,'direction':a.direction,'seed':a.seed,'repeat':a.repeat()}
                      for a in r.rings],
             'center_offset':list(loc)}
            for r,loc in zip(runes, [(-0.27,0,0), (0.27,0,0), (0,0,0)])
        ],
        'contacts': [asdict(c) for c in links],
        'repeat':4,
        'contact_exposure_repeat':8,
        'physical_status':'NOT_VERIFIED_AS_CHEMISTRY',
        'source_refs':REFERENCES,
    }
    out = {}
    for name in sorted(used):
        out[name] = {
            'scene_group':name,
            'appearance':{'rgb':list(ART_COLORS[name]),'source':'ART_DIRECTION_NOT_PHYSICAL_SPECTRUM'},
            'rune_model':water if name=='shaep.lake' else None,
            'composition_status':'EXPERIMENTAL_H2O_REFERENCE' if name=='shaep.lake'
                                 else 'UNKNOWN_NOT_INFERRED',
        }
    return out


def water_phase(descriptor: dict, tick: int) -> dict:
    """Derive alternate contact/exposure frames rather than hard-code 11111111."""
    if tick < 0:raise ValueError('negative tick')
    model=descriptor['rune_model']
    if model is None:raise ValueError('no Rune model on this scene group')
    runes=parse(EXAMPLE)[:3]
    links=assign(runes,4.0)
    phase=tick//2
    result=composite(runes[2],runes,links,phase)
    visible=result['contact'] if tick%2==0 else result['exposure']
    return {'frame':tick,'bits':visible,'raw':result['exposure'],
            'contact':result['contact'], 'density':visible.count('1')/len(visible),
            'classification':'DERIVED_EXPERIMENTAL_CONTACT_OVERLAY'}


def spherical_coil_sites(count: int, radius: float, center: tuple[float,float,float]):
    """Discrete Fibonacci-sphere coil for on-screen Rion sites (not particle orbitals).

    Spatial storage traversal separately uses scene3d.coil_xyz; this angular
    coil is an illustrative spherical layout for the positions of ring bits.
    The bit *positions* stay put and their occupancy rotates each phase.
    """
    if count < 1 or radius <= 0:raise ValueError('positive site count and radius required')
    golden_angle=pi*(3-sqrt(5))
    for i in range(count):
        height=1-2*(i+.5)/count
        width=sqrt(max(0.,1-height*height))
        angle=i*golden_angle
        yield (center[0]+radius*width*cos(angle),
               center[1]+radius*height,
               center[2]+radius*width*sin(angle))


def rune_rion_points(descriptor: dict, origin: tuple[float,float,float], tick: int):
    """3D viewer data for an example Rune-backed Shaep, with 0/1 positions."""
    model=descriptor['rune_model']
    if model is None:return ()
    if tick<0:raise ValueError('negative tick')
    from runecore_language import Ring
    points=[]
    for template in model['runes']:
        ox,oy,oz=template['center_offset']
        origin2=(origin[0]+ox,origin[1]+oy,origin[2]+oz)
        for row in template['rings']:
            r=Ring(row['index'],row['direction'],row['seed'])
            bits=r.at(tick)
            radius=0.105+0.050*row['index']
            for i,center in enumerate(spherical_coil_sites(len(bits),radius,origin2)):
                points.append({'pos':[round(n,8) for n in center], 'bit':int(bits[i]),
                               'slot':template['slot'],'ring':r.index,
                               'glyph':template['glyph']['symbol']})
    return tuple(points)


class RuneSceneStore:
    """Add descriptor records without rewriting v0.12 voxel coordinates."""
    def __init__(self,path: str|Path):
        self.spatial=SceneStore(path)
        self.db=self.spatial.db
        self.db.executescript('''
            CREATE TABLE IF NOT EXISTS rune_scene_descriptors (
                scene_group TEXT PRIMARY KEY, descriptor_json TEXT NOT NULL,
                descriptor_sha256 TEXT NOT NULL
            ) WITHOUT ROWID;
            CREATE INDEX IF NOT EXISTS idx_rune_scene_group ON voxels(shaep);
            CREATE TRIGGER IF NOT EXISTS no_descriptor_update
                BEFORE UPDATE ON rune_scene_descriptors BEGIN SELECT RAISE(ABORT,'version descriptors instead'); END;
            CREATE TRIGGER IF NOT EXISTS no_descriptor_delete
                BEFORE DELETE ON rune_scene_descriptors BEGIN SELECT RAISE(ABORT,'version descriptors instead'); END;
        ''')
    def close(self):self.spatial.close()
    def install(self,command=SUPPORTED_PROMPT):
        """Install source scene and all descriptors together or roll back."""
        rows=self.db.execute('SELECT COUNT(*) FROM voxels').fetchone()[0]
        if rows:
            raise RuntimeError('already populated; use a distinct versioned database')
        spatial_result=self.spatial.populate_once(command)
        voxels=self.spatial.read_voxels()
        descriptors=build_descriptors(v.shaep for v in voxels)
        with self.db:
            self.db.executemany('INSERT INTO rune_scene_descriptors VALUES (?,?,?)',
                [(k,canonical(v),sha256(canonical(v).encode()).hexdigest())
                 for k,v in sorted(descriptors.items())])
            self.db.execute('INSERT INTO meta VALUES (?,?)',(
                'rune_binding_sha256',sha256(canonical(descriptors).encode()).hexdigest()))
            self.db.execute('INSERT INTO meta VALUES (?,?)',('rune_binding_schema',SCHEMA))
        return {'cells':spatial_result['voxel_count'],'scene_sha256':spatial_result['sha256'],
                'descriptors':len(descriptors),'status':STATUS}
    def descriptors(self)->dict:
        raw=self.db.execute('SELECT scene_group,descriptor_json,descriptor_sha256 FROM rune_scene_descriptors ORDER BY scene_group').fetchall()
        descriptors={}
        for group,encoded,digest in raw:
            if sha256(encoded.encode()).hexdigest()!=digest:raise RuntimeError('descriptor record altered')
            obj=json.loads(encoded)
            if obj['scene_group']!=group:raise RuntimeError('scene group mismatch')
            descriptors[group]=obj
        expected=self.db.execute('SELECT value FROM meta WHERE key="rune_binding_sha256"').fetchone()
        if expected is None or sha256(canonical(descriptors).encode()).hexdigest()!=expected[0]:
            raise RuntimeError('descriptor set missing or altered')
        return descriptors
    def export(self,path:str|Path):
        previous=self.spatial.export(Path(path).with_suffix('.v12_tmp.json'))
        Path(path).with_suffix('.v12_tmp.json').unlink(missing_ok=True)
        descriptors=self.descriptors()
        self.spatial.read_voxels()  # verify scene SHA
        doc={**previous,'schema':SCHEMA,'shaep_bindings':descriptors,
             'source_refs':REFERENCES,'classification':STATUS,
             'spatial_grid':'x lateral, y vertical, z depth; source coil_xyz is positional enumeration',
             'ring_geometry':'spherical Fibonacci coil for illustration; not atomic orbitals'}
        doc['binding_sha256']=sha256(canonical(descriptors).encode()).hexdigest()
        Path(path).write_text(canonical(doc),encoding='utf-8')
        return doc
    def view(self,camera:tuple[float,float,float],radius=12.0,*,tick=0,yaw=0.,pitch=0.,fov=1.10,aspect=1.6):
        """Read only visible cells and provenance; no state writes or clock advances."""
        if tick<0:raise ValueError('negative tick')
        if radius<=0 or not 0<fov<pi or aspect<=0:raise ValueError('invalid perspective')
        descriptors=self.descriptors()
        candidate=self.spatial.view(camera,radius)
        chosen=[]
        for v in candidate:
            projected=project_point((v.x,v.y,v.z),camera,yaw=yaw,pitch=pitch,focal=1.,near=.05)
            if projected is None:continue
            sx,sy,_=projected
            if abs(sy) > tan(fov/2)+0.15 or abs(sx)>aspect*tan(fov/2)+0.15:continue
            chosen.append(v)
        visible=[{'xyz':[v.x,v.y,v.z],'scene_group':v.shaep,'material':v.material,
                  'rgb':descriptors[v.shaep]['appearance']['rgb']} for v in chosen]
        return {'schema':SCHEMA,'tick':tick,'camera':list(camera),'cells':visible,
                'count':len(visible),'classification':STATUS}

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument('--database',default='scene3d_runes.sqlite3')
    p.add_argument('--export',default='scene3d_runes.json')
    a=p.parse_args()
    store=RuneSceneStore(a.database)
    try:
        result=store.install()
        doc=store.export(a.export)
        print(canonical({**result,'spans':len(doc['spans']), 'binding_sha256':doc['binding_sha256']}))
    finally:store.close()
