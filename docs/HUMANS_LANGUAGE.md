# Humans Language — Epistemic Control Flow

`Humans` is a proposed Shaelvien source layer designed to be readable by people and unambiguous to machines and language models.

Its first unusual feature is not alternate spelling. It is **epistemic control flow**: the program distinguishes what is established, what is hypothetical, what is fictional, and what is unknown.

## Familiar control words

Traditional control flow remains recognizable:

```text
If
Then
Else
Elseif
Do
While
Until
Go
Return
Case
```

Humans adds:

```text
Whatif
Maybe
Maybeif
Dont
Because
```

These are not synonyms. They carry different semantics.

## Truth domains

Every epistemic statement executes inside one of these domains:

```text
Fact
Hypothesis
Fiction
Unknown
```

### Fact

`Fact` means the program is asserting a value as established **inside a named scope**. A Fact should carry provenance or be derived from deterministic program state.

```text
Fact character.exists = true
Because database.character.chid.000042
```

`Fact` does not mean "universally true forever." Its scope and provenance matter.

### Hypothesis

`Hypothesis` is explicitly non-committal. It can be evaluated, simulated, scored, or rejected, but it may not silently overwrite Fact state.

```text
Whatif character.class = Wizard
Then Hypothesis mana.required = true
```

### Fiction

`Fiction` is intentional invented/canon state. It can be perfectly authoritative inside a fictional world without being presented as a real-world fact.

```text
Fiction world.Geonaph.hasBlackDragon = true
Because canon.event.blackDragonMonthly
```

### Unknown

`Unknown` means insufficiently resolved. It is not false and it is not random.

```text
Maybe character.alive
```

This evaluates to an UNKNOWN truth value until evidence resolves it.

## Three-valued conditions

Ordinary `If` requires a condition that resolves TRUE or FALSE. UNKNOWN is an error unless the programmer handles it.

```text
If account.hasPermission
Then Open Worldbuilder
Else Deny
```

`Maybeif` is the explicit UNKNOWN-aware branch:

```text
Maybeif account.hasPermission
Then Ask Authority
Else Continue
```

A compiler can therefore prevent accidental conversion of "we do not know" into "false."

## Whatif

`Whatif` opens a hypothesis branch. Mutations inside it are sandboxed unless explicitly promoted through a rule that requires evidence/authority.

```text
Whatif inventory.weight > character.capacity
Then Hypothesis movement.speed = reduced
Because rules.encumbrance.chid.000311
```

The result may be inspected or compared without changing authoritative state.

## Maybe

`Maybe` introduces or propagates UNKNOWN.

```text
Maybe target.visible
```

It must not mean `random()`.

If probability is desired, it is explicit:

```text
Chance 0.25 Then Spawn Rain
```

Separating uncertainty from randomness is essential. "We do not know whether it is raining" is different from "generate rain with 25% probability."

## Dont

`Dont` is a negative constraint, not merely `if (!condition)`.

```text
Dont outsiderAI.write HumanMade
Because provenance.boundary
```

A compiler may treat `Dont` as a policy invariant that can be statically checked, dynamically enforced, or both.

## Because

`Because` attaches provenance, justification, rule authority, or dependency evidence.

```text
Fact character.maxHealth = 12
Because chid.004201
```

`Because` does **not** itself prove causal truth. It records why the statement is asserted so a validator can inspect the referenced evidence.

## Elseif and Maybeif

`Elseif` branches on another known TRUE/FALSE condition.

`Maybeif` handles uncertainty explicitly.

```text
If perception.seesTarget
Then Attack
Elseif perception.hearsTarget
Then Search
Maybeif perception.detectsSomething
Then Investigate
Else Wait
```

## Suggested surface grammar

```text
Statement       := FactStatement
                 | FictionStatement
                 | HypothesisStatement
                 | IfStatement
                 | WhatifStatement
                 | MaybeStatement
                 | DontStatement
                 | Action

IfStatement     := "If" Expression "Then" Block
                   { "Elseif" Expression "Then" Block }
                   [ "Maybeif" Expression "Then" Block ]
                   [ "Else" Block ]

WhatifStatement := "Whatif" Expression "Then" Block
MaybeStatement  := "Maybe" Expression
DontStatement   := "Dont" Expression [ "Because" Reference ]

TruthStatement  := ("Fact" | "Hypothesis" | "Fiction" | "Unknown") Assignment
                   [ "Because" Reference ]
```

## CHID-native code

Humans should be able to bind readable names to persistent code identities:

```text
Use CharacterName = chid.000042

If CharacterName is Empty
Then Dont Character.Save
Because validation.characterName.required
```

The compiler resolves the CHID through the Code Database. The readable alias is presentation. The CHID is identity.

This permits controlled source transformations:

```text
Update chid.000042 Name displayName
```

All database relationships still point to the same concept.

## LLM rule

An LLM may propose Humans code, but it must not infer that an unsupported statement is `Fact` merely because it sounds plausible.

When evidence is insufficient, generated code must use `Hypothesis` or `Unknown`. When content belongs to the game world, it must use `Fiction` unless it is describing the software/system itself.

This makes epistemic status part of syntax rather than a conversational convention that can drift.
