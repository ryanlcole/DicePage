#!/usr/bin/env python3
"""Versioned project evidence for the code graph, private exports, and AWS storage.

This is a data importer, not a canon compiler or permission evaluator. It never
executes imported source, modifies user worlds, or grants access.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sqlite3

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS = ROOT / 'knowledge/project/public.json'
DEFAULT_DATABASE = ROOT / '.code-index/code_graph.sqlite3'
PROJECT_PARTITION = 'PROJECT#shaelvien'
TRUTH_DOMAINS = {'FACT', 'HYPOTHESIS', 'FICTION', 'UNKNOWN'}
VISIBILITIES = {'public-existing-source', 'private-project'}
ID = re.compile(r'^[A-Za-z0-9._:-]{1,160}$')


def canonical(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def sha(value: str) -> str:
    return hashlib.sha256(value.encode('utf-8')).hexdigest()


def validate(data: dict) -> dict:
    if data.get('schema_version') != 1 or data.get('dataset_id') != 'shaelvien-project-knowledge':
        raise ValueError('Unsupported project knowledge dataset')
    sources = {}
    records = set()
    for source in data['sources']:
        sid = source['source_id']
        if not ID.fullmatch(sid) or sid in sources:
            raise ValueError('Invalid or duplicate source identity')
        if source['sha256'] != sha(source['content']):
            raise ValueError('Source content hash mismatch: ' + sid)
        if source['visibility'] not in VISIBILITIES:
            raise ValueError('Unknown source visibility')
        sources[sid] = source
    for record in data['records']:
        rid = record['record_id']
        if not ID.fullmatch(rid) or rid in records:
            raise ValueError('Invalid or duplicate record identity')
        records.add(rid)
        if record['truth_domain'] not in TRUTH_DOMAINS or record['visibility'] not in VISIBILITIES:
            raise ValueError('Unknown truth domain or visibility')
        if not all(isinstance(record.get(k), str) and record[k].strip() for k in ('title', 'text', 'status', 'scope', 'category', 'source_locator')):
            raise ValueError('Missing evidence metadata: ' + rid)
        if not record['source_ids'] or any(sid not in sources for sid in record['source_ids']):
            raise ValueError('Dangling source reference: ' + rid)
        if record['visibility'] == 'public-existing-source' and any(sources[s]['visibility'] != 'public-existing-source' for s in record['source_ids']):
            raise ValueError('Private evidence cannot be exported as public')
        p = record['provenance']
        if p.get('origin') != 'OUTSIDER_AI' or p.get('zone') != 'RED' or p.get('canon_promotion') is not False:
            raise ValueError('Imported AI-organized knowledge must preserve RED provenance')
    for edge in data.get('relationships', []):
        if edge['from_id'] not in records or edge['to_id'] not in records:
            raise ValueError('Dangling relationship')
    return data


def load_corpus(path: Path = DEFAULT_CORPUS) -> dict:
    return validate(json.loads(path.read_text(encoding='utf-8')))


def normalized(data: dict):
    validate(data)
    source_rows = [(s, sha(canonical(s))) for s in data['sources']]
    versions = {s['source_id']: rev for s, rev in source_rows}
    record_rows = []
    for record in data['records']:
        resolved = dict(record, source_revisions={sid: versions[sid] for sid in record['source_ids']})
        record_rows.append((resolved, sha(canonical(resolved))))
    return source_rows, record_rows, sha(canonical(data))


def schema(db: sqlite3.Connection):
    statements = [
        'CREATE TABLE IF NOT EXISTS project_sources (source_id TEXT, revision TEXT, title TEXT NOT NULL, content TEXT NOT NULL, visibility TEXT NOT NULL, payload_json TEXT NOT NULL, PRIMARY KEY(source_id,revision))',
        'CREATE TABLE IF NOT EXISTS project_records (record_id TEXT, revision TEXT, title TEXT NOT NULL, text TEXT NOT NULL, category TEXT NOT NULL, truth_domain TEXT NOT NULL, status TEXT NOT NULL, visibility TEXT NOT NULL, payload_json TEXT NOT NULL, PRIMARY KEY(record_id,revision))',
        'CREATE TABLE IF NOT EXISTS project_record_sources (record_id TEXT, record_revision TEXT, source_id TEXT, source_revision TEXT, PRIMARY KEY(record_id,record_revision,source_id), FOREIGN KEY(record_id,record_revision) REFERENCES project_records(record_id,revision), FOREIGN KEY(source_id,source_revision) REFERENCES project_sources(source_id,revision))',
        'CREATE TABLE IF NOT EXISTS project_imports (import_id TEXT PRIMARY KEY, snapshot_date TEXT NOT NULL, source_count INTEGER NOT NULL, record_count INTEGER NOT NULL, metadata_json TEXT NOT NULL)',
        'CREATE TABLE IF NOT EXISTS project_import_records (import_id TEXT, record_id TEXT, record_revision TEXT, PRIMARY KEY(import_id,record_id), FOREIGN KEY(import_id) REFERENCES project_imports(import_id), FOREIGN KEY(record_id,record_revision) REFERENCES project_records(record_id,revision))',
        'CREATE TABLE IF NOT EXISTS project_relationships (import_id TEXT, from_id TEXT, to_id TEXT, relation TEXT, evidence TEXT, PRIMARY KEY(import_id,from_id,to_id,relation))',
        'CREATE INDEX IF NOT EXISTS idx_project_category ON project_records(category,truth_domain)',
        'CREATE VIRTUAL TABLE IF NOT EXISTS project_search USING fts5(record_id UNINDEXED, revision UNINDEXED, title, text, category, status)',
    ]
    for statement in statements:
        db.execute(statement)


def install(db: sqlite3.Connection, data: dict) -> dict:
    """Append immutable source/record versions; preserve all unrelated graph rows."""
    sources, records, import_id = normalized(data)
    db.execute('SAVEPOINT project_knowledge_import')
    try:
        schema(db)
        metadata = {k: v for k, v in data.items() if k not in ('sources', 'records', 'relationships')}
        db.execute('INSERT OR IGNORE INTO project_imports VALUES (?,?,?,?,?)',
                   (import_id, data['snapshot_date'], len(sources), len(records), canonical(metadata)))
        for source, rev in sources:
            db.execute('INSERT OR IGNORE INTO project_sources VALUES (?,?,?,?,?,?)',
                       (source['source_id'], rev, source['title'], source['content'], source['visibility'], canonical(source)))
        for record, rev in records:
            rid = record['record_id']
            inserted = db.execute('INSERT OR IGNORE INTO project_records VALUES (?,?,?,?,?,?,?,?,?)',
                                  (rid, rev, record['title'], record['text'], record['category'], record['truth_domain'], record['status'], record['visibility'], canonical(record))).rowcount
            if inserted:
                db.execute('INSERT INTO project_search VALUES (?,?,?,?,?,?)',
                           (rid, rev, record['title'], record['text'], record['category'], record['status']))
            for sid, source_rev in record['source_revisions'].items():
                db.execute('INSERT OR IGNORE INTO project_record_sources VALUES (?,?,?,?)', (rid, rev, sid, source_rev))
            db.execute('INSERT OR IGNORE INTO project_import_records VALUES (?,?,?)', (import_id, rid, rev))
        for edge in data.get('relationships', []):
            db.execute('INSERT OR IGNORE INTO project_relationships VALUES (?,?,?,?,?)',
                       (import_id, edge['from_id'], edge['to_id'], edge['relation'], edge['evidence']))
        count = db.execute('SELECT count(*) FROM project_import_records WHERE import_id=?', (import_id,)).fetchone()[0]
        if count != len(records):
            raise ValueError('Database import count mismatch')
        db.execute('RELEASE SAVEPOINT project_knowledge_import')
    except Exception:
        db.execute('ROLLBACK TO SAVEPOINT project_knowledge_import')
        db.execute('RELEASE SAVEPOINT project_knowledge_import')
        raise
    return {'project_import_id': import_id, 'project_sources': len(sources), 'project_records': len(records)}


HISTORY_TABLES = ('project_sources', 'project_records', 'project_imports',
                  'project_record_sources', 'project_import_records', 'project_relationships')


def preserve_history(db: sqlite3.Connection) -> dict:
    present = {row[0] for row in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    return {table: db.execute('SELECT * FROM ' + table + ' ORDER BY rowid').fetchall()
            for table in HISTORY_TABLES if table in present}


def restore_history(db: sqlite3.Connection, history: dict):
    schema(db)
    for table in HISTORY_TABLES:
        rows = history.get(table, [])
        if rows:
            marks = ','.join('?' for _ in rows[0])
            db.executemany('INSERT OR IGNORE INTO ' + table + ' VALUES (' + marks + ')', rows)
    db.execute('''INSERT INTO project_search (record_id,revision,title,text,category,status)
        SELECT r.record_id,r.revision,r.title,r.text,r.category,r.status FROM project_records r
        WHERE NOT EXISTS (SELECT 1 FROM project_search s WHERE s.record_id=r.record_id AND s.revision=r.revision)''')


def search(db: sqlite3.Connection, term: str, import_id: str | None = None, limit: int = 25) -> list[dict]:
    if import_id is None:
        latest = db.execute('SELECT import_id FROM project_imports ORDER BY rowid DESC LIMIT 1').fetchone()
        if not latest:
            return []
        import_id = latest[0]
    terms = re.findall(r'[\w-]+', term, flags=re.UNICODE)[:20]
    if not terms:
        return []
    query = ' OR '.join('"' + word.replace('"', '""') + '"' for word in terms)
    rows = db.execute('''SELECT r.payload_json FROM project_search s
        JOIN project_records r ON r.record_id=s.record_id AND r.revision=s.revision
        JOIN project_import_records i ON i.record_id=r.record_id AND i.record_revision=r.revision
        WHERE project_search MATCH ? AND i.import_id=? ORDER BY rank LIMIT ?''',
                      (query, import_id, min(max(int(limit), 1), 100))).fetchall()
    return [json.loads(row[0]) for row in rows]


def markdown(data: dict) -> str:
    validate(data)
    sources = {s['source_id']: s for s in data['sources']}
    out = ['# Shaelvien Project Knowledge', '',
           'Snapshot: ' + data['snapshot_date'] + '. ' + str(len(data['records'])) + ' records; ' + str(len(sources)) + ' sources.', '',
           'This is a source-backed project reference. It is not proof of current deployment, a permission grant, or automatic canon promotion.', '',
           'All extraction and organization is OUTSIDER_AI / RED. Source authorship is not inferred from who uploaded a file. Preserve source dates, truth domains, historical status, and unresolved conflicts.', '',
           'Current repository documents and historical material are explicitly labeled. Some current repository contracts disagree; see source-conflicts. Private planning figures are not current public offers.', '']
    for category in sorted({r['category'] for r in data['records']}):
        out += ['## ' + category, '']
        for r in (r for r in data['records'] if r['category'] == category):
            out += ['### ' + r['title'], '', '`' + r['record_id'] + '`', '',
                    '**Status:** ' + r['status'] + ' · **Domain:** ' + r['truth_domain'] + ' · **Scope:** ' + r['scope'], '',
                    '**Source date:** ' + str(r.get('effective_date') or 'not established; observed ' + data['snapshot_date']), '',
                    '**Sources:** ' + '; '.join(sources[s]['title'] + ' (' + sources[s]['uri'] + ')' for s in r['source_ids']), '',
                    '**Locator:** ' + r['source_locator'], '']
            if r['category'] == 'prototype-source':
                fence = '`' * max(4, max((len(x) for x in re.findall(r'`+', r['text'])), default=0) + 1)
                out += [fence + 'text', r['text'], fence, '']
            else:
                out += [r['text'], '']
    out += ['## Source inventory', '', '| Source | Kind | Status | SHA-256 |', '|---|---|---|---|']
    for s in data['sources']:
        out.append('| ' + ' | '.join(str(s[k]).replace('|', '\\|').replace('\n', ' ') for k in ('title', 'kind', 'status', 'sha256')) + ' |')
    return '\n'.join(out) + '\n'


def dynamo_items(data: dict) -> tuple[list[dict], dict]:
    sources, records, import_id = normalized(data)
    items = []
    for kind, rows, identity in [('SOURCE', sources, 'source_id'), ('RECORD', records, 'record_id')]:
        for payload, revision in rows:
            item = {'pk': PROJECT_PARTITION, 'sk': kind + '#' + payload[identity] + '#' + revision,
                    'kind': 'project-knowledge-' + kind.lower(), 'schemaVersion': 1,
                    'contentSha256': revision, 'payload': canonical(payload)}
            if len(canonical(item).encode('utf-8')) > 350000:
                raise ValueError('Project evidence item exceeds safe DynamoDB size')
            items.append(item)
    manifest_payload = {'importId': import_id, 'snapshotDate': data['snapshot_date'],
                        'sourceCount': len(sources), 'recordCount': len(records),
                        'sourceKeys': [x['sk'] for x in items if x['kind'].endswith('source')],
                        'recordKeys': [x['sk'] for x in items if x['kind'].endswith('record')],
                        'relationships': data.get('relationships', [])}
    manifest = {'pk': PROJECT_PARTITION, 'sk': 'SNAPSHOT#' + import_id,
                'kind': 'project-knowledge-snapshot', 'schemaVersion': 1,
                'contentSha256': sha(canonical(manifest_payload)), 'payload': canonical(manifest_payload)}
    if len(canonical(manifest).encode('utf-8')) > 350000:
        raise ValueError('Project snapshot manifest requires chunking')
    return items, manifest


def import_aws(data: dict, region: str = 'us-east-1') -> dict:
    import boto3
    from botocore.exceptions import ClientError
    items, manifest = dynamo_items(data)
    stack = boto3.client('cloudformation', region_name=region).describe_stacks(StackName='rist-platform')['Stacks'][0]
    outputs = {x['OutputKey']: x['OutputValue'] for x in stack['Outputs']}
    table_name = outputs['WorldStateTableName']
    if not table_name.startswith('rist-platform-WorldStateTable-'):
        raise ValueError('Refusing an unexpected AWS database target')
    table = boto3.resource('dynamodb', region_name=region).Table(table_name)
    expected_schema = {('pk', 'HASH'), ('sk', 'RANGE')}
    if {(x['AttributeName'], x['KeyType']) for x in table.key_schema} != expected_schema:
        raise ValueError('Unexpected database key schema')
    current_key = {'pk': PROJECT_PARTITION, 'sk': 'KNOWLEDGE-MANIFEST'}
    current = table.get_item(Key=current_key, ConsistentRead=True).get('Item')
    if current and (current.get('kind') != 'project-knowledge-current' or current.get('schemaVersion') != 1):
        raise ValueError('Existing project namespace belongs to another schema')
    created = unchanged = 0
    for item in items + [manifest]:
        try:
            table.put_item(Item=item, ConditionExpression='attribute_not_exists(pk)')
            created += 1
        except ClientError as exc:
            if exc.response['Error']['Code'] != 'ConditionalCheckFailedException':
                raise
            unchanged += 1
        saved = table.get_item(Key={'pk': item['pk'], 'sk': item['sk']}, ConsistentRead=True).get('Item')
        if saved != item:
            raise ValueError('Immutable project record collision or verification failure')
    pointer = {**current_key, 'kind': 'project-knowledge-current', 'schemaVersion': 1,
               'snapshotKey': manifest['sk'], 'recordCount': len(data['records']),
               'sourceCount': len(data['sources'])}
    if current != pointer:
        kwargs = {'Item': pointer, 'ConditionExpression': 'attribute_not_exists(pk)'}
        if current:
            kwargs.update(ConditionExpression='#s = :previous',
                          ExpressionAttributeNames={'#s': 'snapshotKey'},
                          ExpressionAttributeValues={':previous': current['snapshotKey']})
        table.put_item(**kwargs)
    if table.get_item(Key=current_key, ConsistentRead=True).get('Item') != pointer:
        raise ValueError('Current project snapshot verification failed')
    return {'table': table_name, 'partition': PROJECT_PARTITION, 'created': created,
            'unchanged': unchanged, 'records_verified': len(data['records']),
            'sources_verified': len(data['sources']), 'snapshot': manifest['sk']}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('command', choices=['validate', 'install', 'find', 'export', 'import-aws'])
    p.add_argument('term', nargs='?', default='')
    p.add_argument('--corpus', type=Path, default=DEFAULT_CORPUS)
    p.add_argument('--db', type=Path, default=DEFAULT_DATABASE)
    p.add_argument('--output', type=Path)
    args = p.parse_args()
    if args.command == 'find':
        db = sqlite3.connect('file:' + args.db.resolve().as_posix() + '?mode=ro', uri=True)
        try:
            print(json.dumps(search(db, args.term), ensure_ascii=False, indent=2))
        finally:
            db.close()
        return
    data = load_corpus(args.corpus)
    if args.command == 'validate':
        dynamo_items(data)
        print(json.dumps({'sources': len(data['sources']), 'records': len(data['records']),
                          'categories': dict(Counter(r['category'] for r in data['records']))}, sort_keys=True))
    elif args.command == 'install':
        args.db.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(args.db) as db:
            db.execute('PRAGMA foreign_keys=ON')
            print(json.dumps(install(db, data), sort_keys=True))
    elif args.command == 'export':
        if not args.output:
            p.error('export requires --output')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(markdown(data), encoding='utf-8')
        print(str(args.output))
    elif args.command == 'import-aws':
        print(json.dumps(import_aws(data), sort_keys=True))


if __name__ == '__main__':
    main()
