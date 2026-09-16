# Error Database and Repetition Detection

Errors are first-class records in the Shaelvien Code Database. They are not disposable console text.

## Tables

`error_signatures` stores the normalized identity of a failure:

- `error_id` — stable error handle such as `err.4e91...`.
- `fingerprint` — normalized SHA-256 identity.
- `language` — C#, Python, JavaScript, TypeScript, HTML, CSS, or unknown.
- `error_code` — compiler/runtime code when present, such as `CS0103`.
- `normalized_message` — volatile timestamps, GUIDs, memory addresses, and large changing numbers removed.
- `first_seen`, `last_seen`.
- `occurrence_count`.
- `repeat_flag` — true when the configured repetition threshold is reached.
- `resolution_state`.
- `regression_flag` — true when a previously resolved signature reappears.

`error_events` stores each concrete occurrence and links it to:

- source log and line;
- detected language;
- source code path and line;
- persistent code-record ID;
- nearest CHID when resolvable.

`error_resolutions` records how a known error was resolved, along with optional commit/code/CHID context.

## Why normalize

These two raw failures should normally be recognized as the same error:

```text
2026-09-16T12:00:01Z Foo.cs(83): error CS0103: name 'x' does not exist
2026-09-16T12:09:44Z Foo.cs(83): error CS0103: name 'x' does not exist
```

The timestamp is incidental. The language, compiler code, and normalized failure are the identity evidence.

## Repetition behavior

Default behavior is:

```text
occurrence 1 -> NEW
occurrence 2 -> REPEATED
resolved then seen again -> REGRESSION
```

The threshold is configurable in `.code-index/error_sources.json`.

The intended warning path is therefore stronger than a normal log message:

```text
REPEATED ERROR csharp err.abc123... CS0103
linked code id: 002914.csharp.CharacterCreate.line83.code
linked symbol: chid.000042 characterName
```

That warning tells an editor or LLM to inspect the previous occurrences and resolution before proposing another fix.

## Persistent sources

The database ingests configured error sources, including:

- `KNOWN_ERRORS.md` when present;
- repository log files;
- verification logs;
- `.code-index/runtime_errors.jsonl` for explicitly recorded failures.

`python tools/code_database.py record-error "<message>"` records a failure and immediately reports whether the normalized signature is new, repeated, or a regression against the current database.

## Generation rule

Before creating replacement code for a failing area, tooling should query both:

1. the CHID/symbol graph to determine whether a suitable implementation already exists; and
2. the error graph to determine whether this failure or attempted repair has happened before.

This means the system can eventually answer not only “where is `characterName`?” but also “which errors have repeatedly involved `characterName`, which implementations attempted to fix them, and which fix actually remained stable?”
