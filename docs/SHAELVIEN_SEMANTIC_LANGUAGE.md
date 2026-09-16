# Shaelvien Semantic Language Reference

Status: **EXPERIMENTAL / AUTHORITATIVE DISCOVERY CONTRACT**  
Specification version: `0.1.1-alpha`

This document defines the shared semantic vocabulary that Shaelvien/RIST code, tools, humans, and AI assistants should use while the compact language and runtime are being developed. It does not replace existing executable source yet. Existing C#, Razor, JavaScript, Python, data files, and validated runtime contracts remain executable truth until a compiler/runtime migration is explicitly promoted.

## 1. Foundational rules

- **Identity is not representation.** A stable semantic identity may have many surface forms.
- **Representation is not truth.** A browser, image, source spelling, pixel, token, or wire encoding is a view/representation of underlying state.
- **The server stores authoritative truth; the viewer produces perception.** Hidden or unauthorized truth must not be sent merely because the UI promises not to show it.
- **Errors become law.** Repeated failures should be normalized, related to the semantic/code identities that caused them, and prevented from silently returning.
- **Unknown meaning is never guessed.** Unknown semantic IDs, opcodes, authority paths, truth states, or provenance remain unresolved/rejected until defined.

## 2. Semantic identities

### Rune

A **Rune** is an atomic semantic identity or operation. A Rune names meaning, not a particular spelling or byte value.

Example concept:

```text
rune.retrieve
```

`SELECT`, `get`, an integer opcode, a visual control, or another form may implement/represent that Rune under declared conditions. The representation does not become the identity.

### Glyph

A **Glyph** is contextual or compound meaning assembled from Runes and/or other Glyphs. Control patterns, resolved capabilities, and compound behaviors belong here.

Example concept:

```text
glyph.counted_loop
```

A C-style `for` and an expanded `while` may represent that Glyph only when their control-flow behavior is actually equivalent. Surface similarity never proves semantic equivalence.

### SHAEP

A **SHAEP** is the persistent Shaelvien/RIST **Spatial Hot Preservation Object** defined by `apps/rist-world/SHAEP_FORMAT.md`.

Current authoritative format is SHAEP v2. A `.shaep` is the hot archive representation produced from supported source media while `ShaepId` remains persistent identity. Native source truth and provenance remain preserved. Concrete world placement remains separate from reusable SHAEP identity.

The semantic/authority system may associate an identity Rune, permission context, or other verified metadata with a SHAEP or SHAEP-related record. That does not redefine the media/archive contract and does not make secrecy-by-container a security mechanism.

### CHID

A **CHID** (Code Handle ID) is persistent semantic identity for a code symbol. File path, source spelling, line number, target language, and UI representation may change without requiring the concept to become a new CHID.

Readable names are presentation. CHID is the stable code handle.

### CCTV

**CCTV** currently names the trusted context translation/verification boundary being designed for semantic authority resolution. The long-form expansion is **not yet canon** and must not be invented by tooling.

Conceptually:

```text
identity + protected context + resource + authority path + intent
                         |
                         v
                       CCTV
                         |
                         v
               contextual capability Glyph
                         |
                         v
                 allowed Rune stream
```

CCTV must authenticate/verify trusted inputs, resolve Recursive Authority, preserve provenance, reject ambiguous permission paths, and expose capability without exposing the credential that created it.

## 3. Truth and provenance

Truth domain and provenance are separate dimensions.

Truth domains:

```text
FACT
HYPOTHESIS
FICTION
UNKNOWN
```

Provenance domains:

```text
HUMAN
OUTSIDER_AI
SHAELVIEN_EI
```

`FICTION` can be fully authoritative world canon without becoming a real-world FACT. `UNKNOWN` is not FALSE. `HYPOTHESIS` must not silently mutate FACT. AI-derived material retains ancestry instead of silently becoming purely HUMAN.

The related human-readable epistemic source rules live in `docs/HUMANS_LANGUAGE.md`.

## 4. Boolean semantics

The semantic layer uses typed boolean values:

```text
TRUE
FALSE
UNKNOWN        # when the schema/domain permits epistemic uncertainty
```

Do **not** assign universal semantic meaning to numeric `0`, `1`, or `-1`. Different machine languages and APIs encode truth differently. A wire or target representation may explicitly map a numeric value to TRUE/FALSE, but that mapping belongs to that representation schema, not to Rune/Glyph truth itself.

This prevents a decoder or AI assistant from importing accidental truthiness rules from C, JavaScript, SQL, shell languages, legacy APIs, or another target.

## 5. Compact streams are representations

A compact form such as:

```text
i3r20
```

may be useful as a human demonstration of a small semantic instruction stream, but it is not by itself a production grammar. Multi-digit values, negative numbers, strings, references, blocks, versions, and operand boundaries must be unambiguous.

Production encodings should resolve to stable semantic identities and typed operands, for example conceptually:

```text
[format-version]
[registry-version/hash]
[opcode-or-unit-id]
[typed operand count/length]
[typed operands...]
```

ASCII aliases and numeric opcodes are encodings of semantic identities. Their visible token/number may change through a versioned migration; an existing semantic ID's meaning must never silently change.

Unknown opcodes are rejected or represented as UNKNOWN. They are never assigned a plausible meaning by guesswork.

## 6. Browser decoder = perception boundary

The repository currently contains `apps/rist-world/wwwroot/worldbuilder-rune-decoder.js`, a prototype fixed-width numeric decoder. Its contract states that world/rule code decides Rune meaning and the module only applies already-authorized presentation instructions.

The intended direction remains:

```text
authoritative state
      -> semantic identities / Runes / Glyphs / CHIDs
      -> compact, versioned instruction/result stream
      -> browser perception decoder
      -> DOM / Canvas / WebGL / accessibility representation
```

The browser decoder is not an authority engine and must not be able to promote hidden state into truth.

## 7. Recursive Authority and contextual capabilities

`apps/rist-world/AUTHORITY_SYSTEM.md` is the permission authority. Credentials establish authenticated identity; permissions determine what that identity may do. Delegation retains both authenticated actor and effective identity.

A user identity may be represented by a Rune/reference and associated with a trusted SHAEP/context envelope. CCTV then resolves the actual permission-bearing path and produces only the contextual capability Glyph/Rune operations allowed for that request.

A capability should be bindable to relevant constraints such as:

```text
subject identity
effective identity / delegation
resource or SHAEP
authority containment path
operation/capability
session
time/expiry
nonce/replay policy
provenance
```

The client does not need the master permission table or authentication credential in order to invoke an already-authorized presentation capability.

## 8. Map/perception requests

A compact request can identify actor, character, world location, and intent without sending hidden truth.

Human-readable conceptual example:

```text
H52|C1|X23|Y42|Z74|T1|L9|I
```

Meaning:

```text
Human identity 52
Character identity 1
X 23
Y 42
Z 74
Tier 1
Layer 9
Intent: Inspect
```

The exact production grammar/opcodes are **not yet frozen** by this example.

Trusted resolution should follow this direction:

```text
identity
  -> character
  -> coordinate/tier/layer resource lookup
  -> SHAEP/world-object resolution
  -> Recursive Authority
  -> character metadata/perception rules
  -> authoritative roll/check resolution when required
  -> contextual Glyph
  -> revealed Rune/value stream
```

A hidden trap, secret-door DC, GM note, unrevealed object, or other protected fact must not be sent to the browser before the server-side context says it is revealable. Hiding it in CSS/DOM state is not security.

For example, the server may know:

```text
trap.exists = TRUE
trap.visible = FALSE
trap.reveal.minimum = 15
```

A character result of 23 may cause the trusted resolver to emit a reveal capability/result. The browser should receive the revealed result, not the unrevealed threshold merely to compare it locally.

## 9. Pixels and UI properties

A pixel or screen coordinate is representation, not semantic identity.

Do not define a Login button permanently as “pixel 1.” Responsive layout, zoom, localization, accessibility, and alternate input would break that identity.

Use the relationship:

```text
pixel/screen position
      -> current representation node / hit target
      -> CHID or semantic UI identity
      -> permitted Rune/Glyph action
```

Thus a pixel may locate an interactive representation at this instant, while an illustrative `chid.login.button` identifies the concept across visual layouts. Keyboard, voice, switch input, touch, screen reader, and pointer can all resolve to the same semantic action without sharing the same pixel.

No essential action may depend on one sense or one input method alone.

## 10. Security requirements

Compactness and obscurity are not security.

Security comes from:

- authenticated principals;
- server-side Recursive Authority checks;
- explicit semantic allowlists;
- typed operand/schema validation;
- immutable/versioned semantic meanings;
- integrity/signature checks where appropriate;
- scoped and expiring capabilities where appropriate;
- replay protection where required;
- least privilege;
- provenance boundaries;
- durable audit/error relationships;
- refusal to execute unknown semantic IDs.

The language may be inspectable/public while protected operations remain unavailable without authority.

## 11. Relationship vocabulary

Semantic/code relationships should be explicit rather than collapsed into `==`.

Useful relation types include:

```text
exact_identity
alias
implements_intent
implements_behavior
contextual_semantic_equivalence
behavioral_equivalence
representation_equivalence
payload_representation
subset
superset
transforms_to
calls
reads
writes
binds_to
serializes
implements
depends_on
causes_error
resolved_by
```

Every equivalence relation may carry conditions and truth status. Two forms that look similar are not automatically interchangeable.

## 12. Error relationships

The code database/error graph should connect normalized failures to the language and semantic identities involved:

```text
error signature
  -> source code ID / CHID
  -> Rune/Glyph/SHAEP/form
  -> decoder/compiler/runtime target
  -> resolution
```

A repeat means the same normalized failure has appeared before. A regression means a failure marked resolved has reappeared. These are different warnings.

## 13. Assistant / ChatGPT operating contract

When a new ChatGPT conversation or coding agent can access this repository or deployed reference, it should load this specification before editing Shaelvien semantic-language code.

The assistant must:

1. search for an existing CHID/Rune/Glyph/SHAEP/form before creating a duplicate;
2. preserve current canonical contracts such as SHAEP v2 and Recursive Authority;
3. distinguish semantic identity from aliases, numeric opcodes, pixels, paths, and source spelling;
4. never infer an unknown opcode/ID meaning from surrounding syntax alone;
5. never move hidden server truth into a client packet merely for convenience;
6. preserve truth-domain and provenance distinctions;
7. treat CCTV as a trusted verification/translation boundary whose long-form name remains unspecified until canonized;
8. version any semantic-breaking change and provide migration/compatibility information;
9. prefer safe additive experiments and maintain existing executable behavior until replacement is validated;
10. report specification/implementation conflicts rather than silently rewriting one to match the other.

A fresh ChatGPT chat does not automatically inherit this document merely because it exists. `AGENTS.md`, the `.well-known` manifest, and the hidden page are discovery surfaces so a repo-aware, connected, or explicitly directed session can retrieve the same authoritative rules instead of reconstructing them from memory.

## 14. Discovery surfaces

Repository agent entry point:

```text
AGENTS.md
```

Repository discovery pointer:

```text
SHAELVIEN_LANGUAGE.md
```

Canonical repository specification:

```text
docs/SHAELVIEN_SEMANTIC_LANGUAGE.md
```

Machine-readable deployed manifest:

```text
/Game/.well-known/shaelvien-language.json
```

Intentionally unlisted human/assistant reference:

```text
/Game/_shaelvien-language.html
```

The hidden page is `noindex` and absent from normal navigation. It is not a security boundary and must contain no secrets.
