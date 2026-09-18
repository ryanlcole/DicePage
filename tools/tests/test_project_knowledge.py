import copy
from pathlib import Path
import sqlite3
import sys
import types
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import project_knowledge as knowledge


def corpus():
    data = copy.deepcopy(knowledge.load_corpus())
    record = data['records'][0]
    data['records'] = [record]
    data['sources'] = [s for s in data['sources'] if s['source_id'] in record['source_ids']]
    data['relationships'] = []
    return data


class StorageTests(unittest.TestCase):
    def test_retry_preserves_graph_and_does_not_duplicate(self):
        db = sqlite3.connect(':memory:')
        db.execute('CREATE TABLE symbols(chid TEXT PRIMARY KEY)')
        db.execute("INSERT INTO symbols VALUES ('existing.identity')")
        data = corpus()
        knowledge.install(db, data)
        knowledge.install(db, data)
        self.assertEqual(db.execute('SELECT count(*) FROM project_records').fetchone()[0], 1)
        self.assertEqual(db.execute('SELECT count(*) FROM project_search').fetchone()[0], 1)
        self.assertEqual(db.execute('SELECT * FROM symbols').fetchone()[0], 'existing.identity')

    def test_changed_evidence_keeps_old_version_and_searches_selected_snapshot(self):
        db = sqlite3.connect(':memory:')
        data = corpus()
        data['records'][0]['text'] = 'Oldamber source claim'
        old = knowledge.install(db, data)['project_import_id']
        data['records'][0]['text'] = 'Newcobalt revised claim'
        knowledge.install(db, data)
        self.assertEqual(db.execute('SELECT count(*) FROM project_records').fetchone()[0], 2)
        self.assertEqual(len(knowledge.search(db, 'Newcobalt')), 1)
        self.assertEqual(knowledge.search(db, 'Oldamber'), [])
        self.assertEqual(len(knowledge.search(db, 'Oldamber', old)), 1)
        self.assertEqual(knowledge.search(db, '" *'), [])

    def test_bad_hash_does_not_change_database(self):
        db = sqlite3.connect(':memory:')
        data = corpus()
        knowledge.install(db, data)
        data['sources'][0]['content'] += 'tampered'
        with self.assertRaises(ValueError): knowledge.install(db, data)
        self.assertEqual(db.execute('SELECT count(*) FROM project_imports').fetchone()[0], 1)

    def test_duplicate_identity_rejected(self):
        data = corpus()
        data['records'].append(copy.deepcopy(data['records'][0]))
        with self.assertRaises(ValueError): knowledge.validate(data)

    def test_private_evidence_cannot_become_public(self):
        data = corpus()
        data['sources'][0]['visibility'] = 'private-project'
        with self.assertRaises(ValueError): knowledge.validate(data)

    def test_ai_origin_cannot_become_human(self):
        data = corpus()
        data['records'][0]['provenance']['origin'] = 'HUMAN'
        with self.assertRaises(ValueError): knowledge.validate(data)

    def test_graph_rebuild_keeps_private_history(self):
        import code_database
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / 'graph.sqlite3'
            with patch.object(code_database, 'DATABASE_PATH', target), patch.object(code_database, 'ERROR_SOURCES_PATH', Path(temp) / 'missing.json'):
                first = code_database.build_database([], [], [], {'entries': {}})
                self.assertGreater(first['project_records'], 1)
                private = corpus()
                private['records'][0]['text'] = 'Privatecobalt preserved source history'
                private['records'][0]['visibility'] = 'private-project'
                with sqlite3.connect(target) as db:
                    import_id = knowledge.install(db, private)['project_import_id']
                code_database.build_database([], [], [], {'entries': {}})
                with sqlite3.connect(target) as db:
                    self.assertEqual(len(knowledge.search(db, 'Privatecobalt', import_id)), 1)
                    self.assertEqual(db.execute('pragma integrity_check').fetchone()[0], 'ok')


class ClientError(Exception):
    def __init__(self, code): self.response = {'Error': {'Code': code}}


class FakeTable:
    key_schema = [{'AttributeName': 'pk', 'KeyType': 'HASH'}, {'AttributeName': 'sk', 'KeyType': 'RANGE'}]
    def __init__(self):
        self.items = {('WORLD#existing', 'ENTITY#tile'): {'player_data': 'unchanged'}}
        self.fail_after = None
    def get_item(self, Key, ConsistentRead):
        assert ConsistentRead
        return {'Item': copy.deepcopy(self.items.get((Key['pk'], Key['sk'])))}
    def put_item(self, Item, ConditionExpression, **kwargs):
        if self.fail_after is not None and len(self.items) >= self.fail_after:
            raise ClientError('AccessDeniedException')
        key = (Item['pk'], Item['sk'])
        existing = self.items.get(key)
        if ConditionExpression == 'attribute_not_exists(pk)' and existing:
            raise ClientError('ConditionalCheckFailedException')
        if ConditionExpression == '#s = :previous' and existing['snapshotKey'] != kwargs['ExpressionAttributeValues'][':previous']:
            raise ClientError('ConditionalCheckFailedException')
        self.items[key] = copy.deepcopy(Item)


class AwsTests(unittest.TestCase):
    def setUp(self):
        self.table = FakeTable()
        table = self.table
        cfn = types.SimpleNamespace(describe_stacks=lambda **k: {'Stacks': [{'Outputs': [
            {'OutputKey': 'WorldStateTableName', 'OutputValue': 'rist-platform-WorldStateTable-fixture'}]}]})
        self.modules = patch.dict(sys.modules, {
            'boto3': types.SimpleNamespace(client=lambda *a, **k: cfn,
                resource=lambda *a, **k: types.SimpleNamespace(Table=lambda n: table)),
            'botocore': types.ModuleType('botocore'),
            'botocore.exceptions': types.SimpleNamespace(ClientError=ClientError)})
        self.modules.start()
    def tearDown(self): self.modules.stop()
    def test_retry_preserves_world_data(self):
        data = corpus()
        first = knowledge.import_aws(data)
        again = knowledge.import_aws(data)
        self.assertEqual(first['created'], 3)
        self.assertEqual(again['created'], 0)
        self.assertEqual(again['unchanged'], 3)
        self.assertEqual(self.table.items[('WORLD#existing', 'ENTITY#tile')], {'player_data': 'unchanged'})
    def test_partial_failure_never_publishes_snapshot(self):
        self.table.fail_after = 2
        with self.assertRaises(ClientError): knowledge.import_aws(corpus())
        self.assertNotIn((knowledge.PROJECT_PARTITION, 'KNOWLEDGE-MANIFEST'), self.table.items)
    def test_immutable_collision_refused(self):
        data = corpus()
        knowledge.import_aws(data)
        item = next(v for k, v in self.table.items.items() if k[1].startswith('SOURCE#'))
        item['payload'] = 'different evidence'
        with self.assertRaises(ValueError): knowledge.import_aws(data)


if __name__ == '__main__': unittest.main()
