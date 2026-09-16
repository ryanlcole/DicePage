# Shaelvien Code Database Architecture

## Purpose

The code index identifies source. The **Code Database** understands relationships.

The long-term rule is:

> Define a concept once. Give it a persistent Code Handle ID (CHID). Everything else references that identity.

A variable such as `characterName` should not become a fresh concept every time a page, serializer, validator, network message, or renderer needs it. The original declaration receives a CHID. Other code becomes references, aliases, reads, writes, calls, bindings, or transformations connected to that CHID.

This turns the repository into a queryable graph before it becomes a new programming language.

## CHID

**CHID = Code Handle ID.**

A CHID is a persistent identity for a semantic code symbol. It is separate from:

- the symbol's current spelling;
- its current file;
- its current line number;
- the language used to implement it;
- the UI screen that exposes it.

Example conceptually:

```text
chid.000042
  kind: variable
  canonical_name: characterName
  declared_at: CharacterCreate.razor:118
  type: string
```

Relationships might include:

```text
CharacterCreate.nameInput  --binds-to--> chid.000042
CharacterStore.Save        --reads-----> chid.000042
CharacterDto.Name          --serializes-> chid.000042
CharacterHeader.Render     --reads-----> chid.000042
```

Renaming `characterName` to `displayName` changes a label/alias. It does not create a new CHID unless the concept itself changed.

## Database model

The generated SQLite database lives at:

```text
.code-index/code_graph.sqlite3
```

It contains these principal relations:

- `files` — tracked files, language, classification, hash.
- `code_records` — line/comment identities inherited from the code index.
- `symbols` — variables, fields, parameters, functions, methods, classes, imports, properties, components, IDs, and other named concepts.
- `symbol_aliases` — historical/current names for a CHID.
- `references` — reads, writes, calls, imports, bindings, and unresolved named references.
- `edges` — normalized graph relationships between symbols/code records/files.
- `duplicate_groups` — exact duplicate evidence from the index.
- `epistemic_nodes` — fact/hypothesis/fiction/unknown declarations used by Shaelvien's higher-level language.

The generated graph views live at:

```text
.code-index/relationships.mmd
.code-index/relationships.dot
```

The Mermaid view is intended for humans and repository documentation. SQLite is the query authority.

## Source is still executable truth

The database does **not** make ordinary C#, Python, JavaScript, or Razor magically execute from SQLite. Those languages still compile from source.

Instead, the database becomes the semantic authority used by generation and editing tools:

1. Search the graph for an existing concept.
2. Reuse its CHID when it already exists.
3. Create a new CHID only when the concept is genuinely new.
4. Generate or update source from the graph.
5. Re-index and verify that source and graph agree.

This prevents the common failure mode where a new feature quietly invents a second `characterName`, second inventory service, second camera state, or fifth "final" helper.

## Relationship confidence

Not all languages are parsed equally on day one. Every relationship therefore carries a confidence value and evidence type.

- `1.0 parser` — derived from a real parser/AST.
- `0.8 structured` — derived from language-specific structured syntax.
- `0.5 heuristic` — derived from conservative lexical matching.
- `0.0 unresolved` — name seen but target is not known yet.

A heuristic relationship may help navigation, but it must never silently become authority over a parser-confirmed relation.

## Duplicate prevention rule

Before generating a new declaration, tools should query by:

- normalized name and aliases;
- symbol kind;
- type when known;
- containing component/class/module;
- semantic signature;
- callers/references;
- nearby comments and code purpose.

If a compatible CHID exists, update or reference it. If two CHIDs appear to represent one concept, flag them for consolidation rather than automatically choosing one.

## Database-first editing

A later Shaelvien source layer can express edits against identities instead of raw files:

```text
Update chid.000042 Name "displayName"
Update chid.000042 Type Text
Add Reference CharacterHeader.Render -> chid.000042
```

The compiler/generator resolves those operations into the implementation language and validates the resulting graph.

This is intentionally different from treating the SQLite database as a runtime key/value store. It is a **semantic code model**: source identity, relationships, provenance, and transformation instructions live together.

## Truth domains

Code and generated reasoning must distinguish at least:

- `FACT` — asserted true in a declared real/system scope and backed by evidence/provenance.
- `HYPOTHESIS` — a possibility being explored; cannot silently mutate FACT state.
- `FICTION` — deliberately invented/world-canon material; may be true inside a declared fictional world without claiming real-world truth.
- `UNKNOWN` — unresolved or insufficiently supported.

The truth domain is independent of confidence. Something may be `FICTION` with confidence 1.0 because we are completely certain it is canon fiction.

This distinction is foundational for the Humans language and for AI-assisted code generation.
