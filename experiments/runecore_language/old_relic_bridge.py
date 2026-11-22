"""Optional Old ReLiC-style local evidence ledger for RuneCore/1 experiments.

Distinct from the legacy ReLiC authority repository and the ReLiC MCP service.
No project authority is inferred from a stored entry. No automatic canon promotion.
Times: occurred_at = event valid time (may be UNKNOWN), recorded_at = UTC write time.
"""
from __future__ import annotations
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import json
import sqlite3
from runecore_language import parse, frame

GENESIS = '0' * 64
TYPES = frozenset({'HYPOTHESIS', 'OBSERVATION', 'TEST', 'RESULT', 'ERROR', 'CORRECTION', 'WORLD_SEED', 'CHECKPOINT'})

def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)

class ReLiCEvidence:
    """Append-only experiment ledger; content hashes detect drift, not establish truth."""
    def __init__(self, path):
        self.path = Path(path)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS events (
            seq INTEGER PRIMARY KEY, event_id TEXT NOT NULL UNIQUE,
            kind TEXT NOT NULL, occurred_at TEXT NOT NULL,
            recorded_at TEXT NOT NULL, subject TEXT NOT NULL,
            refs TEXT NOT NULL, payload TEXT NOT NULL,
            previous_hash TEXT NOT NULL, digest TEXT NOT NULL UNIQUE
          );
          CREATE TRIGGER IF NOT EXISTS immutable_event_update
            BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'append-only evidence'); END;
          CREATE TRIGGER IF NOT EXISTS immutable_event_delete
            BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'append-only evidence'); END;
        ''')
    def close(self): self.db.close()
    def append(self, kind, subject, payload, occurred_at='UNKNOWN', refs=()):
        if kind not in TYPES: raise ValueError('unsupported evidence class')
        if not isinstance(payload, dict) or not isinstance(subject, str) or not subject.strip():
            raise ValueError('subject and structured payload required')
        if not refs or any(not isinstance(r,str) or not r for r in refs):
            raise ValueError('at least one source reference required')
        if occurred_at != 'UNKNOWN':
            datetime.fromisoformat(occurred_at.replace('Z','+00:00'))
        ts = datetime.now(timezone.utc).isoformat()
        self.db.execute('BEGIN IMMEDIATE')
        try:
            last=self.db.execute('SELECT seq,digest FROM events ORDER BY seq DESC LIMIT 1').fetchone()
            seq=(last['seq']+1) if last else 1
            prev=last['digest'] if last else GENESIS
            record={'seq':seq,'event_id':f'EXPERIMENT-{seq:08d}','kind':kind,
                    'occurred_at':occurred_at,'recorded_at':ts,'subject':subject,
                    'refs':list(refs),'payload':payload,'previous_hash':prev}
            digest=sha256(canonical(record).encode('utf-8')).hexdigest()
            self.db.execute('INSERT INTO events VALUES (?,?,?,?,?,?,?,?,?,?)',
                (seq,record['event_id'],kind,occurred_at,ts,subject,canonical(list(refs)),canonical(payload),prev,digest))
            self.db.commit()
            return {'event_id':record['event_id'],'digest':digest,'recorded_at':ts,'status':'OBSERVATION_NOT_CANON'}
        except Exception:
            self.db.rollback()
            raise
    def events(self):
        return [dict(row) for row in self.db.execute('SELECT * FROM events ORDER BY seq')]
    def verify(self):
        prior=GENESIS
        for expected,row in enumerate(self.events(),1):
            if row['seq']!=expected or row['event_id']!=f'EXPERIMENT-{expected:08d}' or row['previous_hash']!=prior:
                return False
            record={k:row[k] for k in ('seq','event_id','kind','occurred_at','recorded_at','subject','previous_hash')}
            try:
                record['refs']=json.loads(row['refs']);record['payload']=json.loads(row['payload'])
            except (ValueError,TypeError):return False
            if sha256(canonical(record).encode('utf-8')).hexdigest()!=row['digest']:return False
            prior=row['digest']
        return True
    def install_world(self, source, refs, occurred_at='UNKNOWN'):
        if self.db.execute("SELECT 1 FROM events WHERE kind='WORLD_SEED' LIMIT 1").fetchone():
            raise RuntimeError('world seed exists; corrections require an added event, not replacement')
        parse(source) # validated before committing
        return self.append('WORLD_SEED','RuneCore world seed',
            {'source':source,'sha256':sha256(source.encode()).hexdigest(),
             'status':'EXPERIMENTAL_WORLD_NOT_CANON'},occurred_at,refs)
    def world(self):
        row=self.db.execute("SELECT payload FROM events WHERE kind='WORLD_SEED' ORDER BY seq LIMIT 1").fetchone()
        if not row:raise LookupError('world seed not installed')
        payload=json.loads(row['payload'])
        if sha256(payload['source'].encode()).hexdigest()!=payload['sha256']:
            raise ValueError('world payload corrupt')
        return parse(payload['source'])
    def checkpoint(self, tick, refs, occurred_at='UNKNOWN'):
        if not isinstance(tick,int) or tick<0:raise ValueError('invalid tick')
        self.world() # needs a world seed
        row=self.db.execute("SELECT payload FROM events WHERE kind='CHECKPOINT' ORDER BY seq DESC LIMIT 1").fetchone()
        if row and tick<=json.loads(row['payload'])['tick']:
            raise ValueError('checkpoint must advance monotonically')
        return self.append('CHECKPOINT','Logical ring clock checkpoint',
                           {'tick':tick,'note':'phase derived from immutable seeds; not proof of continuous CPU execution'},
                           occurred_at,refs)
    def current_tick(self):
        row=self.db.execute("SELECT payload FROM events WHERE kind='CHECKPOINT' ORDER BY seq DESC LIMIT 1").fetchone()
        return json.loads(row['payload'])['tick'] if row else 0
    def viewer(self,viewport,tick=None):
        """Only compute visible atoms. A viewer read never advances or writes clock."""
        if not self.verify():raise RuntimeError('experiment evidence chain invalid')
        return frame(self.world(),self.current_tick() if tick is None else tick,viewport)
