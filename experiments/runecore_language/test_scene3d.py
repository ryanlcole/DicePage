from __future__ import annotations
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest
from scene3d import (
    coil_xy,coil_xyz,build_scene,SceneStore,scene_sha,
    project_point,interpret_scene_intent,SUPPORTED_PROMPT
)

EXACT_FIRST_TEN=[
 (0,0,0),(1,0,0),(1,1,0),(0,1,0),(-1,1,0),
 (-1,0,0),(-1,-1,0),(0,-1,0),(1,-1,0),(1,0,1)
]

class CoilTests(unittest.TestCase):
    def test_owner_exact_order(self):self.assertEqual(list(coil_xyz(1))[:10],EXACT_FIRST_TEN)
    def test_unique_full_cube(self):
        for r in range(4):
            v=list(coil_xyz(r));self.assertEqual(len(v),(2*r+1)**3)
            self.assertEqual(len(set(v)),len(v));self.assertEqual(set(v),{
                (x,y,z) for x in range(-r,r+1) for y in range(-r,r+1) for z in range(-r,r+1)})
    def test_2d_coil_exact(self):
        self.assertEqual(list(coil_xy(1)),[(x,y) for x,y,z in EXACT_FIRST_TEN[:9]])
    def test_sphere_is_mask_not_coil(self):
        v=set(coil_xyz(3,sphere_radius=2.0));self.assertIn((2,0,0),v)
        self.assertNotIn((2,2,0),v)
        self.assertEqual(v,{(x,y,z) for x in range(-3,4) for y in range(-3,4) for z in range(-3,4) if x*x+y*y+z*z<=4})
    def test_negative_radius_rejected(self):
        with self.assertRaises(ValueError):list(coil_xyz(-1))
        with self.assertRaises(ValueError):list(coil_xyz(1,sphere_radius=-1))

class StorageTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.dbpath=Path(self.temp.name)/'scene.db';self.out=Path(self.temp.name)/'scene.json'
        self.s=SceneStore(self.dbpath)
    def tearDown(self):self.s.close();self.temp.cleanup()
    def installed(self):return self.s.populate_once(SUPPORTED_PROMPT)
    def test_intent_supported(self):self.assertEqual(interpret_scene_intent('Please CREATE a scene with a lake, shore and building.'),'lake_shore_building_v1')
    def test_intent_reject_unsupported(self):
        with self.assertRaises(ValueError):interpret_scene_intent('a school on Mars')
    def test_lake_exists(self):
        self.installed();self.assertGreater(sum(c.material=='water' for c in self.s.read_voxels()),100)
    def test_shore_exists(self):
        self.installed();self.assertGreater(sum(c.material=='shore' for c in self.s.read_voxels()),80)
    def test_building_has_height(self):
        self.installed();self.assertTrue(any(c.material=='roof' and c.y>=6 for c in self.s.read_voxels()))
    def test_scene_distinct_cell_coordinates(self):
        self.installed();v=self.s.read_voxels();self.assertEqual(len(v),len({(c.x,c.y,c.z) for c in v}))
    def test_durable_checkpoint_hash(self):
        record=self.installed();self.s.close();self.s=SceneStore(self.dbpath)
        self.assertEqual(scene_sha(self.s.read_voxels()),record['sha256'])
    def test_cannot_overwrite_scene(self):
        self.installed()
        with self.assertRaises(RuntimeError):self.installed()
    def test_export_round_trip(self):
        self.installed();doc=self.s.export(self.out)
        cells=set((v.x,v.y,v.z,v.material,v.shaep) for v in self.s.read_voxels())
        restored={(x,y,z,m,s) for x,y,z0,z1,m,s in doc['spans'] for z in range(z0,z1+1)}
        self.assertEqual(restored,cells)
        self.assertEqual(doc['voxel_count'],len(cells))
        self.assertEqual(json.loads(self.out.read_text())['sha256'],scene_sha(self.s.read_voxels()))
    def test_indexed_proximity(self):
        self.installed();near=self.s.view((1,0,-100),10)
        self.assertEqual(near,())
        close=self.s.view((-6,0,3),5)
        self.assertGreater(len(close),0)
        self.assertTrue(all((c.x+6)**2+c.y*c.y+(c.z-3)**2<=25 for c in close))
    def test_bad_radius_rejected(self):
        with self.assertRaises(ValueError):self.s.view((0,0,0),0)
    def test_sha_tamper_detected(self):
        self.installed()
        self.s.db.execute("UPDATE voxels SET material='stone' WHERE material='water' LIMIT 1");self.s.db.commit()
        with self.assertRaises(RuntimeError):self.s.read_voxels()
    def test_no_physical_atoms_claim(self):
        self.installed();d=self.s.export(self.out)
        self.assertIn('NOT_CHEMISTRY',d['classification'])
        self.assertIn('NOT_CHEMISTRY_OR_TRAINED_LLM',d['classification'])
    def test_voxel_count_is_3d_not_only_2d(self):
        self.installed();vs=self.s.read_voxels()
        self.assertGreater(len({v.y for v in vs}),3)

class PerspectiveTests(unittest.TestCase):
    def test_user_camera_example(self):
        p=project_point((0,0,0),(1,0,-100),focal=100)
        self.assertIsNotNone(p)
        self.assertAlmostEqual(p[0],-1.0)
        self.assertAlmostEqual(p[1],0.0)
        self.assertAlmostEqual(p[2],100.0)
    def test_behind_camera_is_culled(self):
        self.assertIsNone(project_point((0,0,-101),(1,0,-100)))
    def test_larger_distance_scales_down(self):
        near=project_point((10,0,0),(0,0,-10),focal=100)
        far=project_point((10,0,0),(0,0,-100),focal=100)
        self.assertGreater(abs(near[0]),abs(far[0]))
    def test_yaw_changes_image_coordinates(self):
        p0=project_point((0,0,5),(0,0,0),yaw=0)
        p1=project_point((0,0,5),(0,0,0),yaw=.2)
        self.assertNotAlmostEqual(p0[0],p1[0])

if __name__=='__main__':unittest.main()
