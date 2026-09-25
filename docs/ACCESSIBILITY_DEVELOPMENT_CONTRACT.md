# Accessibility Development Contract

Status: project-wide development rule

## Core rule

Every future Shaelvien/RIST change is both normal development and accessibility development.

A user-facing capability is not complete when only its default visual/pointer representation works. The same authoritative state, identity, permissions, and game rules must be reachable through accessible representation and input paths appropriate to the capability.

Accessibility is not a fork, simplified world, optional afterthought, or separate source of truth. It is another authorized representation of the same semantic system.

## Required equivalence

For every new or materially changed user-facing capability:

1. Preserve one semantic identity and one authoritative state model across default and accessible representations.
2. Provide keyboard access for every essential action.
3. Do not require drag, hover, precise pointer motion, color perception, hearing, speech, animation tolerance, or vision as the only way to understand or perform an essential action.
4. Provide names, roles, state, relationships, coordinates, and descriptions in machine-readable/assistive form when those facts are visually represented.
5. Preserve visible focus and logical focus order.
6. Announce meaningful asynchronous state changes through appropriate live/status semantics without flooding assistive technology.
7. Respect reduced-motion preferences and provide non-motion equivalents when motion carries information.
8. Provide text/caption/transcript equivalents for essential audio and meaningful audio alternatives for essential visual information when applicable.
9. Keep text scalable and interfaces operable under zoom/reflow.
10. Never use color alone as identity, status, permission, targeting, selection, danger, ownership, or game-state information.
11. Keep touch targets and alternate-input paths usable on mobile, keyboard, switch, speech, and assistive technologies where the platform supports them.
12. Accessibility helpers and AI assistants may invoke only the same authorized semantic actions available to the user; they do not receive extra game, account, moderation, or administrative authority.

## Architecture

The preferred flow is:

```text
authoritative state / CHID / SHAEP / Recursive Authority
    -> semantic capability/action
    -> default visual representation
    -> accessibility representation(s)
    -> equivalent authorized result
```

Pixels, audio, animation, gestures, speech, braille, captions, text commands, and AI assistance are representations or input methods. They do not create a second world truth.

The existing Accessibility Shell is a first-class semantic client of WorldSession. New systems should expose reusable semantic actions/state to it rather than duplicate gameplay logic inside the shell.

## Development completion rule

A change that introduces or changes an essential user-facing action is incomplete until its accessibility impact has been considered and the necessary equivalent path is implemented or the capability remains explicitly unavailable/experimental without displacing an existing accessible path.

Normal development reviews and accessibility reviews are the same development process.

## Automated and human verification

Automated checks should cover, where applicable:

- semantic names/roles/states;
- keyboard reachability and keyboard traps;
- focus visibility/order;
- form labels/errors;
- contrast and non-color state;
- reduced motion;
- zoom/reflow;
- accessibility-tree exposure;
- captions/transcripts/text alternatives;
- pointer-independent operation;
- touch target behavior.

Browser/accessibility-tree automation and MCP-based accessibility tools may assist testing, but automated scans are evidence, not proof of complete accessibility. Human assistive-technology testing remains required for behaviors automation cannot establish.

## Failure behavior

Accessibility may never be bypassed merely to ship faster. If an equivalent path cannot yet be made safe and correct, preserve the prior accessible behavior, narrow the feature, or mark the new capability incomplete rather than silently creating an inaccessible-only authority path.
