# Shaelvien project knowledge

The source-controlled public corpus is `knowledge/project/public.json`. Its first
snapshot contains 294 records from 29 previously public sources at repository
commit `6dadd9f8232a4b9c22ff435617ce7801c8d8a362` (observed 2026-09-18).
It covers architecture, semantic language, SHAEP, authority, WorldBuilder,
policies, historical teaching capsules, the existing IP ledger, and unresolved
contract conflicts. It is a dated snapshot, not an assertion that all source
documents still match today's branch or production.

The owner's separate private corpus additionally includes uploaded historical
source, known errors, configuration, project lore, requirements, and planning.
It must not be published into this public repository. It can be merged into an
authorized local developer database using the same importer.

## Authority and provenance

All AI extraction/organization retains OUTSIDER_AI/RED provenance. Unknown source
authorship is not relabeled HUMAN just because a human uploaded it. Source
classification, confidence/currentness, truth domain, and canon authority remain
separate. Policy excerpts describe project documents, not independent legal
advice. Historical capsules retain their original classifications as reported
claims, not fresh verification of the underlying books or running services.

The first snapshot explicitly flags disagreement about kilometre versus authored
measurement profiles, supported layers versus mid-air placement, and the distinct
historical Shaep stabilization and current SHAEP v2 media/archive meanings.

## Developer database

`python tools/code_database.py build` adds this evidence to the existing code
graph. It is reconstructed from the corpus on every rebuild; it does not replace
symbols, references, error history, or semantic-unit identities.

```bash
python tools/project_knowledge.py validate
python tools/project_knowledge.py install
python tools/project_knowledge.py find "SHAEP provenance"
python tools/project_knowledge.py export --output .code-index/Shaelvien_Project_Source.md
```

For a private corpus, supply `--corpus /authorized/path/Shaelvien_Project_Knowledge.json`.
To build a standalone project database, add `--db /authorized/path/project.sqlite3`.
The latest installed snapshot is the default search scope; old revisions remain
queryable by their import ID using the Python search API. Code graph rebuilds
preserve existing project history, including private imports, before adding the
public corpus. Keep the private source corpus as a recoverable backup.

## Existing AWS website database

The importer resolves the existing `rist-platform` CloudFormation output
`WorldStateTableName` and verifies the `pk`/`sk` schema. It uses only partition
`PROJECT#shaelvien`, outside player/world/account partitions.

Source and record versions use conditional insert-only writes. Every item is
read back consistently and compared before the snapshot is published. A current
snapshot pointer is updated with a comparison against its prior value. Old
snapshots are retained. A partial or unauthorized import never publishes a new
current snapshot. There are no deletes, scans of player data, public APIs, new
tables, or IAM mutations in this importer.

```bash
python tools/project_knowledge.py import-aws --corpus /authorized/path/Shaelvien_Project_Knowledge.json
```

The Project Knowledge Database workflow builds the public-source database and
ChatGPT reference on relevant pushes. It reports actual AWS readiness. The
optional workflow-dispatch `import_to_aws` input imports only the public corpus
and requires existing approved data access. A successful build/readiness job is
not evidence that an AWS import occurred: read the `importPerformed` field and
the explicit import/readback step.

On 2026-09-18, the existing GitHub deployment role successfully authenticated and
described `rist-platform-WorldStateTable-K41GRHU2G6X7`, but AWS denied
`dynamodb:GetItem`. The first import stopped before writing any record. The
preflight emits a proposed policy scoped to the project partition and the actual
table encryption key; it does not attach that policy or change IAM. An authorized
AWS administrator must resolve data access before the import can complete.

## ChatGPT source access

Connected, repository-aware ChatGPT/Codex sessions can fetch this document and
`knowledge/project/public.json` on `live-alpha-rist-blazor-world` through the
existing GitHub connection. Do not assume default-branch search covers this
active branch. Fetch the explicit branch/path when the source is not found.

The generated Markdown export is a plain-text, citable source snapshot for
ChatGPT; the private export includes the owner's additional material. Saving or
uploading that export does not create a live database connection and does not
automatically add it to every ChatGPT project or future conversation.

A live custom connection requires an authenticated MCP server with read-only
`search` and `fetch`, access limited to authorized project knowledge, and a
user-created ChatGPT connection. No private database endpoint was opened by this
change. Official setup: https://developers.openai.com/api/docs/mcp and
https://developers.openai.com/plugins/deploy/connect-chatgpt .
