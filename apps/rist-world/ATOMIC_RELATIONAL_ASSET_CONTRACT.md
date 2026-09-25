# Atomic Relational Asset Contract

Status: **LOCKED — architectural authority**

## End state

Shaelvien stores a thing once, then stores what happened to it.

The asset system is relational and recursive:

- **Rune** — the smallest immutable data fact: content bytes, a content hash, a coordinate, a scalar property, or another atomic machine value.
- **Glyph** — a relationship between runes or states: derived-from, changed-pixels, crop, transform, metadata assignment, provenance, permission, containment, or another relation.
- **Shaep** — the persistent identity/shape formed by those relations. A Shaep owns a lineage of revisions; it is not a duplicate file.

## Identity law

Identity is independent from presentation.

Renaming an image, moving it to another folder, changing metadata, changing ownership/access, or rendering it differently does not create another physical image.

If exact payload bytes already exist in the database, reuse those bytes. Do not store a second copy because another user uploaded them or supplied different metadata.

If pixels or other content change, store only the new revision content needed to represent that change and link it to the existing lineage. A modification is a new state of the same Shaep unless an explicit creation operation establishes a new independent identity.

## Version law

A version records change; it does not duplicate identity.

A revision may reference:

- parent revision
- content fingerprint
- changed data or replacement payload
- transformation/provenance relation
- metadata state
- creation actor/time

A representation/cache may be regenerated and discarded. Lineage and revision truth persist.

## Permission law

Permissions separate views of truth; they do not separate storage.

A principal may have View, Edit, Public, or Deny against a Shaep or a specific revision. Two users can therefore see different metadata or revisions without requiring duplicate content.

Permission inheritance follows the existing recursive authority system. Removing access removes the relationship, not necessarily the underlying shared payload.

## Storage law

1. Exact content match -> one physical payload.
2. Metadata-only change -> relation/revision metadata only.
3. Content modification -> new revision linked to its parent.
4. Derived representation -> disposable unless explicitly promoted to persistent truth.
5. Physical payload deletion -> only when no retained lineage/revision references it and retention/provenance rules allow collection.
6. Filename, folder, account, UI location, and display label are never identity authorities.

## Recursive language goal

The same model must scale upward without introducing a new programming system:

`Rune -> Glyph -> Shaep -> larger Shaep`

Images are the first enforcement surface, not a special case. The same relational identity model is intended to describe maps, objects, characters, rules, worlds, and other Shaelvien structures.

## Regression rule

Repository assets must not contain exact duplicate image payloads under multiple tracked paths. Historical imports retain provenance through Git history and metadata references rather than copied bytes.

Near-identical content is not automatically merged by visual similarity alone. The database's edit/provenance relationship establishes revision lineage; exact byte equality may be deduplicated deterministically.
