import unittest
from runecore_language import Ring, Rune, Glyph, Shaep, Atom, GLYPH_TABLE, parse, frame, EXAMPLE
from ring_contacts import assign, shaeps_from_links

class CorrectedTerms(unittest.TestCase):
    def setUp(self):self.runes=parse(EXAMPLE)
    def test_binary_rions(self):self.assertEqual(set(self.runes[0].rings[0].seed),{'0','1'})
    def test_rotating_ring(self):self.assertEqual(self.runes[2].rings[1].at(1),'11011101')
    def test_rune_element(self):
        self.assertIsInstance(self.runes[0],Rune)
        self.assertIs(Atom,Rune)
    def test_glyph_h(self):self.assertEqual(self.runes[0].glyph(),Glyph(1,'H'))
    def test_glyph_o(self):self.assertEqual(self.runes[2].glyph(),Glyph(8,'O'))
    def test_118_periodic_glyphs(self):
        self.assertEqual(len(GLYPH_TABLE),118)
        self.assertEqual(GLYPH_TABLE['Nh'].atomic_number,113)
        self.assertEqual(GLYPH_TABLE['Og'].atomic_number,118)
    def test_glyph_not_pattern_signature(self):
        self.assertNotEqual(self.runes[0].glyph().symbol,self.runes[0].pattern_signature())
        self.assertEqual(self.runes[0].pattern_signature(),self.runes[1].pattern_signature())
    def test_same_pattern_not_same_element(self):
        other=Rune('X','O',0.,0.,(Ring(1,'CW','1000'),))
        self.assertEqual(other.pattern_signature(),self.runes[0].pattern_signature())
        self.assertNotEqual(other.glyph(),self.runes[0].glyph())
    def test_unknown_label_not_periodic(self):
        other=parse('RUNE R Q 0 0\nRING 1 CW 100\nENDRUNE')
        self.assertIsNone(other[0].glyph())
        self.assertEqual(frame(other,0,(-1,-1,1,1))['runes'][0]['glyph']['classification'],'UNKNOWN_NOT_PERIODIC_GLYPH')
    def test_shaep_composition(self):
        forms=shaeps_from_links(self.runes,assign(self.runes))
        self.assertEqual(len(forms),1)
        self.assertEqual(forms[0].members,('RAM1','RAM2','RAM3'))
        self.assertEqual(forms[0].composition(self.runes),{'H':2,'O':1})
        self.assertEqual(forms[0].status(),'EXPERIMENTAL_ASSEMBLY_NOT_CHEMISTRY')
    def test_no_faroff_member(self):
        forms=shaeps_from_links(self.runes,assign(self.runes))
        self.assertNotIn('RAM4',forms[0].members)
    def test_invalid_shaep(self):
        with self.assertRaises(ValueError):Shaep(('RAM1','RAM1'))
        with self.assertRaises(ValueError):Shaep(('RAM1','RAM2'),(('RAM1','RAM3',0),))
    def test_legacy_text_alias(self):
        self.assertEqual(parse('ATOM A H 0 0\nRING 1 CW 1000\nENDATOM')[0].glyph().symbol,'H')
    def test_no_mixed_end_markers(self):
        with self.assertRaises(ValueError):parse('RUNE A H 0 0\nRING 1 CW 1000\nENDATOM')
    def test_rune_frame(self):
        v=frame(self.runes,2,(-3,-3,3,3))
        self.assertEqual(len(v['runes']),3)
        self.assertEqual(len(v['atoms']),3)
        self.assertEqual(v['runes'][2]['rings'][1]['bits'],'10111011')
        self.assertEqual(v['runes'][2]['glyph']['atomic_number'],8)
    def test_catalog_not_seed(self):self.assertNotIn('rings',GLYPH_TABLE['C'].as_dict())

if __name__=='__main__':unittest.main()
