"""Regression tests tying the old ring language to 3D viewer cells without physics claims."""
from pathlib import Path
import json
import sqlite3
import tempfile
import unittest
from scene3d import SUPPORTED_PROMPT, coil_xyz, scene_sha
from scene3d_runes import (RuneSceneStore, STATUS, SCHEMA, build_descriptors,
                            water_phase, spherical_coil_sites, rune_rion_points)

class SceneRuneTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.path=Path(self.tmp.name)/'scene.db'
        self.export_path=Path(self.tmp.name)/'scene.json'
        self.store=RuneSceneStore(self.path)
    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()
    def seed(self):return self.store.install(SUPPORTED_PROMPT)
    def test_installs_full_scene_without_loss(self):
        result=self.seed()
        self.assertEqual(result['cells'],3604)
        self.assertEqual(len(self.store.spatial.read_voxels()),3604)
    def test_original_coil_first_ten_intact(self):
        expected=[(0,0,0),(1,0,0),(1,1,0),(0,1,0),(-1,1,0),(-1,0,0),(-1,-1,0),(0,-1,0),(1,-1,0),(1,0,1)]
        self.assertEqual(list(coil_xyz(1))[:10],expected)
    def test_water_composition_exact(self):
        self.seed();water=self.store.descriptors()['shaep.lake']['rune_model']
        self.assertEqual(water['composition'],{'H':2,'O':1})
        self.assertEqual([r['glyph']['atomic_number'] for r in water['runes']],[1,1,8])
    def test_outer_oxygen_zero_positions_alternate(self):
        self.seed();w=self.store.descriptors()['shaep.lake']
        self.assertEqual([water_phase(w,2*i+1)['bits'] for i in range(4)],
                         ['11101110','11011101','10111011','01110111'])
    def test_contact_all_ones_derived(self):
        self.seed();w=self.store.descriptors()['shaep.lake']
        self.assertEqual([water_phase(w,2*i)['bits'] for i in range(4)],['11111111']*4)
    def test_empty_material_compositions_are_unknown(self):
        self.seed()
        for k,v in self.store.descriptors().items():
            if k!='shaep.lake':
                self.assertEqual(v['composition_status'],'UNKNOWN_NOT_INFERRED')
                self.assertIsNone(v['rune_model'])
    def test_visual_colors_not_chemistry(self):
        self.seed()
        for entry in self.store.descriptors().values():
            self.assertEqual(entry['appearance']['source'],'ART_DIRECTION_NOT_PHYSICAL_SPECTRUM')
    def test_sparse_export_stable(self):
        self.seed();doc=self.store.export(self.export_path)
        self.assertEqual(doc['schema'],SCHEMA)
        self.assertEqual(doc['voxel_count'],3604)
        self.assertEqual(len(doc['spans']),248)
        self.assertEqual(doc['classification'],STATUS)
        reconstructed={(x,y,z,m,s) for x,y,z0,z1,m,s in doc['spans'] for z in range(z0,z1+1)}
        actual={(v.x,v.y,v.z,v.material,v.shaep) for v in self.store.spatial.read_voxels()}
        self.assertEqual(reconstructed,actual)
        self.assertEqual(json.loads(self.export_path.read_text())['binding_sha256'],doc['binding_sha256'])
    def test_persistence_restart(self):
        self.seed();before=self.store.descriptors();self.store.close();self.store=RuneSceneStore(self.path)
        self.assertEqual(before,self.store.descriptors())
        self.assertEqual(self.store.export(self.export_path)['voxel_count'],3604)
    def test_scene_not_overwritten(self):
        self.seed()
        with self.assertRaises(RuntimeError):self.store.install()
    def test_descriptor_update_blocked(self):
        self.seed()
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.db.execute("UPDATE rune_scene_descriptors SET scene_group='fake' WHERE scene_group='shaep.lake'")
    def test_descriptor_delete_blocked(self):
        self.seed()
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.db.execute("DELETE FROM rune_scene_descriptors WHERE scene_group='shaep.lake'")
    def test_descriptor_corruption_detected(self):
        self.seed()
        self.store.db.execute('DROP TRIGGER no_descriptor_update')
        self.store.db.execute("UPDATE rune_scene_descriptors SET descriptor_json='{}' WHERE scene_group='shaep.lake'")
        with self.assertRaises(RuntimeError):self.store.descriptors()
    def test_view_culls_distant(self):
        self.seed()
        v=self.store.view((1,0,-100),12.,yaw=0.,pitch=0.)
        self.assertEqual(v['cells'],[])
    def test_view_filters_to_camera(self):
        self.seed()
        v=self.store.view((-6,2,-10),20.,yaw=0.,pitch=-.1)
        self.assertGreater(v['count'],0)
        self.assertLess(v['count'],3604)
    def test_view_does_not_advance_or_write(self):
        self.seed()
        self.store.db.execute('PRAGMA data_version')
        before=self.path.stat().st_size
        first=self.store.view((-6,2,-10),20.,tick=10,pitch=-.1)
        second=self.store.view((-6,2,-10),20.,tick=500,pitch=-.1)
        self.assertEqual(first['cells'],second['cells'])
        self.assertEqual(before,self.path.stat().st_size)
    def test_rion_sites_spherical(self):
        sites=list(spherical_coil_sites(8,.2,(1,2,3)))
        self.assertEqual(len(set(sites)),8)
        for x,y,z in sites:
            self.assertAlmostEqual((x-1)**2+(y-2)**2+(z-3)**2,.04,places=10)
    def test_ring_sites_have_depth(self):
        sites=list(spherical_coil_sites(8,.2,(0,0,0)))
        self.assertGreater(len({round(p[2],5) for p in sites}),4)
    def test_rion_bits_rotate_but_sites_stay_fixed(self):
        self.seed();d=self.store.descriptors()['shaep.lake']
        a=rune_rion_points(d,(0,0,0),0)
        b=rune_rion_points(d,(0,0,0),1)
        self.assertEqual([x['pos'] for x in a],[x['pos'] for x in b])
        self.assertNotEqual([x['bit'] for x in a],[x['bit'] for x in b])
        self.assertEqual(len(a),20)  # H4 + H4 + O4 + O8
    def test_unknown_material_has_no_rion_geometry(self):
        self.seed();d=self.store.descriptors()['shaep.path']
        self.assertEqual(rune_rion_points(d,(0,0,0),0),())
    def test_invalid_direction_not_forgiven(self):
        with self.assertRaises(ValueError):list(spherical_coil_sites(0,.2,(0,0,0)))
    def test_not_a_trained_llm(self):
        self.seed();d=self.store.export(self.export_path)
        self.assertIn('NOT_CHEMISTRY_OR_TRAINED_LLM',d['classification'])
        self.assertIn('NOT_VERIFIED_AS_CHEMISTRY',d['shaep_bindings']['shaep.lake']['rune_model']['physical_status'])

if __name__=='__main__':unittest.main()