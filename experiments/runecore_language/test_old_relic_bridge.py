import sqlite3
import tempfile
from pathlib import Path
import unittest
from old_relic_bridge import ReLiCEvidence
from runecore_language import parse,EXAMPLE
from ring_contacts import candidates,assign,composite

class TestLegacyEvidence(unittest.TestCase):
    def setUp(self):
        self.t=tempfile.TemporaryDirectory();self.path=Path(self.t.name)/'experiment.sqlite3'
        self.log=ReLiCEvidence(self.path)
    def tearDown(self):self.log.close();self.t.cleanup()
    def installed(self):
        return self.log.install_world(EXAMPLE,refs=['https://github.com/ryanlcole/DicePage/pull/58'])
    def test_append_readback(self):
        r=self.installed();self.assertTrue(r['event_id']);self.assertTrue(self.log.verify());self.assertEqual(len(self.log.events()),1)
    def test_temporal_distinction(self):
        r=self.log.append('HYPOTHESIS','historic concept',{},'2026-01-01T00:00:00Z',['archive'])
        event=self.log.events()[0];self.assertEqual(event['occurred_at'],'2026-01-01T00:00:00Z');self.assertNotEqual(event['occurred_at'],event['recorded_at'])
    def test_unknown_event_time(self):
        self.log.append('OBSERVATION','unknown time',{},refs=['archive']);self.assertEqual(self.log.events()[0]['occurred_at'],'UNKNOWN')
    def test_chain_multiple(self):
        self.installed();self.log.append('TEST','one',{'ok':True},refs=['test']);self.assertTrue(self.log.verify());self.assertNotEqual(self.log.events()[0]['digest'],self.log.events()[1]['digest'])
    def test_immutable_update(self):
        self.installed()
        with self.assertRaises(sqlite3.IntegrityError):self.log.db.execute("UPDATE events SET subject='forged' WHERE seq=1")
    def test_immutable_delete(self):
        self.installed()
        with self.assertRaises(sqlite3.IntegrityError):self.log.db.execute('DELETE FROM events WHERE seq=1')
    def test_no_seed_overwrite(self):
        self.installed()
        with self.assertRaises(RuntimeError):self.installed()
    def test_bad_seed_rejected(self):
        with self.assertRaises(ValueError):self.log.install_world('ATOM x H 0 0\nENDATOM',['archive'])
    def test_checkpoint_monotonic(self):
        self.installed();self.log.checkpoint(8,['test'])
        with self.assertRaises(ValueError):self.log.checkpoint(8,['test'])
        self.assertEqual(self.log.current_tick(),8)
    def test_view_does_not_write(self):
        self.installed();self.log.checkpoint(1,['test']);before=len(self.log.events())
        view=self.log.viewer((-3,-3,3,3));self.assertEqual(len(view['atoms']),3);self.assertEqual(before,len(self.log.events()))
    def test_offscreen_excluded(self):
        self.installed();view=self.log.viewer((90,90,105,105));self.assertEqual([a['slot'] for a in view['atoms']],['RAM4'])
    def test_restart(self):
        self.installed();self.log.checkpoint(9,['test']);self.log.close();self.log=ReLiCEvidence(self.path)
        self.assertEqual(self.log.current_tick(),9);self.assertTrue(self.log.verify())
    def test_reject_authority_promotion(self):
        with self.assertRaises(ValueError):self.log.append('CANON','not allowed',{},refs=['test'])
    def test_bad_source(self):
        with self.assertRaises(ValueError):self.log.append('TEST','no refs',{})
    def test_chain_detects_untrusted_edit(self):
        self.installed();self.log.db.execute('DROP TRIGGER immutable_event_update')
        self.log.db.execute("UPDATE events SET subject='forged' WHERE seq=1")
        self.assertFalse(self.log.verify())
    def test_view_fails_closed(self):
        self.installed();self.log.db.execute('DROP TRIGGER immutable_event_update');self.log.db.execute("UPDATE events SET subject='forged' WHERE seq=1")
        with self.assertRaises(RuntimeError):self.log.viewer((-3,-3,3,3))

class TestGenericContacts(unittest.TestCase):
    def setUp(self):self.atoms=parse(EXAMPLE)
    def test_exact_two_links(self):
        self.assertEqual({(v.acceptor,v.sector) for v in assign(self.atoms)}, {('RAM3',0),('RAM3',1)})
        self.assertEqual({v.donor for v in assign(self.atoms)}, {'RAM1','RAM2'})
    def test_full_ring_contact_all_phases(self):
        links=assign(self.atoms)
        expected=['11101110','11011101','10111011','01110111']
        for t in range(4):
            o=composite(self.atoms[2],self.atoms,links,t)
            self.assertEqual(o['exposure'],expected[t]);self.assertEqual(o['contact'],'11111111')
    def test_no_radius_matches(self):self.assertEqual(assign(self.atoms,radius=0.1),())
    def test_label_blind(self):
        a=parse('''ATOM A Q -2 0\nRING 1 CW 1000\nENDATOM\nATOM B Q 2 0\nRING 1 CW 1000\nENDATOM\nATOM C Z 0 0\nRING 1 CW 1010\nRING 2 CCW 11101110\nENDATOM''')
        self.assertEqual(len(assign(a)),2)
    def test_six_bit_example(self):
        a=parse('''ATOM D X -1 0\nRING 1 CW 100\nENDATOM\nATOM E Y 1 0\nRING 1 CW 110\nRING 2 CCW 110110\nENDATOM''')
        self.assertEqual([(v.donor,v.acceptor,v.sector) for v in assign(a)],[('D','E',0)])
    def test_mismatch(self):
        a=parse('''ATOM A H 0 0\nRING 1 CW 1100\nENDATOM\nATOM O O 1 0\nRING 1 CW 1010\nRING 2 CCW 11101110\nENDATOM''')
        self.assertEqual(assign(a),())
    def test_no_duplicate_donors(self):self.assertEqual(len({x.donor for x in assign(self.atoms)}),len(assign(self.atoms)))
    def test_no_duplicate_sectors(self):self.assertEqual(len({(x.acceptor,x.sector) for x in assign(self.atoms)}),len(assign(self.atoms)))
    def test_zero_radius_rejected(self):
        with self.assertRaises(ValueError):assign(self.atoms,0)

if __name__=='__main__':unittest.main()
