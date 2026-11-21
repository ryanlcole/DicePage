import unittest
from runecore_language import Ring, parse, frame, EXAMPLE

class LanguageTests(unittest.TestCase):
    def setUp(self):self.atoms=parse(EXAMPLE)
    def test_slots_fixed(self):self.assertEqual([a.slot for a in self.atoms],['RAM1','RAM2','RAM3','RAM4'])
    def test_hydrogen_cycle(self):self.assertEqual([self.atoms[0].rings[0].at(i) for i in range(5)],['1000','0100','0010','0001','1000'])
    def test_oxygen_outer_cycle(self):self.assertEqual([self.atoms[2].rings[1].at(i) for i in range(5)],['11101110','11011101','10111011','01110111','11101110'])
    def test_oxygen_inner_cycle(self):self.assertEqual([self.atoms[2].rings[0].at(i) for i in range(4)],['1010','0101','1010','0101'])
    def test_repeat(self):self.assertEqual([a.repeat() for a in self.atoms[:3]],[4,4,4])
    def test_no_offscreen_atoms(self):self.assertEqual(len(frame(self.atoms,0,(-4,-3,4,3))['atoms']),3)
    def test_pan_filters(self):self.assertEqual([a['slot'] for a in frame(self.atoms,0,(99,99,101,101))['atoms']],['RAM4'])
    def test_empty_view(self):self.assertEqual(frame(self.atoms,0,(50,50,60,60))['atoms'],[])
    def test_glyph_stable_after_rotation(self):
        from runecore_language import Atom
        a=self.atoms[0]
        rotated=Atom('DIFFERENT','X',99.,99.,(Ring(1,'CW','0100'),))
        self.assertEqual(a.glyph(),rotated.glyph())
    def test_glyph_not_atom_identity(self):self.assertEqual(self.atoms[0].glyph(),self.atoms[1].glyph())
    def test_bad_direction(self):
        with self.assertRaises(ValueError):parse('ATOM R1 H 0 0\nRING 1 CCW 1000\nENDATOM')
    def test_bad_ring_order(self):
        with self.assertRaises(ValueError):parse('ATOM R1 H 0 0\nRING 2 CCW 1000\nENDATOM')
    def test_missing_end(self):
        with self.assertRaises(ValueError):parse('ATOM R1 H 0 0\nRING 1 CW 1000')
    def test_duplicate_slot(self):
        with self.assertRaises(ValueError):parse('ATOM R1 H 0 0\nRING 1 CW 1000\nENDATOM\nATOM R1 H 1 1\nRING 1 CW 1000\nENDATOM')
    def test_frame_not_mutating_atoms(self):
        before=repr(self.atoms);[frame(self.atoms,i,(-4,-3,4,3)) for i in range(100)];self.assertEqual(before,repr(self.atoms))
    def test_negative_tick(self):
        with self.assertRaises(ValueError):frame(self.atoms,-1,(-4,-3,4,3))
    def test_negative_view(self):
        with self.assertRaises(ValueError):frame(self.atoms,0,(4,3,-4,-3))
    def test_no_pretend_training(self):self.assertNotIn('trained',frame(self.atoms,0,(-4,-3,4,3))['status'].lower())

if __name__=='__main__':unittest.main()
