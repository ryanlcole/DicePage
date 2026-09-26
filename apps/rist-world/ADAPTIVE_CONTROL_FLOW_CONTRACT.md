# Shaelvien Adaptive Control Flow Contract

Status: owner-directed active interaction contract
Date: 2026-09-26

## Purpose

World Builder, Region Definer, and Local Definer expose the same underlying world truth through an adaptive, flowchart-like control surface intended to be understandable by new users age 10+ while remaining fully usable through assistive technologies.

Accessibility is not a separate simplified world model. Touch, mouse, keyboard, switch scanning, speech/voice-control labels, screen readers, braille-oriented semantic navigation, and exact-value inputs must reach the same authoritative state and permission checks.

## Five primary flow nodes

The normal control surface exposes only:

1. VIEW — camera, zoom, fit, tilt, selection focus.
2. BUILD — add image, tile, sprite, label, or drawing content.
3. EDIT — contextual actions for the currently selected object.
4. LAYERS — visibility, appearance order, opacity, spatial depth, locks, and permissions.
5. MORE — technical/advanced tools such as exact tier/layer, Pixels, lighting, CAD, stylus, relationships, metadata, and accessibility display preferences.

Claim creation is a temporary guided SELECT flow and may replace the five primary nodes only while the user is actively defining a new Region footprint.

## Contextual Edit flow

Selecting an editable object opens EDIT and fits the selected object into the usable viewer area without placing it behind the control surface.

EDIT begins with result-oriented choices rather than implementation vocabulary:

- MOVE
- SIZE
- APPEARANCE
- DEPTH
- UNDERLAY
- ADVANCED
- DELETE
- DONE
- UNDO when an undoable change exists

Subflows reveal only actions relevant to the current decision. Technical keyboards remain available through ADVANCED / MORE.

## Flow semantics

- BACK returns to the previous decision level and does not reverse authored state.
- UNDO reverses the most recent supported edit for the current selection.
- DONE finishes the current object, clears selection, and restores the pre-selection camera.
- Errors and prerequisites are explicit. A disabled action explains the required prior state, such as CUT APART requiring transparent background first.
- The interface may predict and reveal the next sensible actions, but it must never execute an authored change merely because it is predicted.

## Selection focus and underlay

When an object is selected:

- Auto Focus is on by default and fits the selected object into the usable viewer area.
- The camera move is immediate; reduced-motion users are not forced through animation.
- The directly underlying visual layer may be previewed only inside the selected object's screen footprint.
- Underlay is on by default but can be hidden.
- Auto Focus and Underlay preferences are user-controllable and persistent.
- Leaving selection restores the pre-selection camera.

The underlay is a viewing aid only. It must never mutate layer identity, depth, visibility, permissions, or authored content.

## Input independence

No essential action may require drag, hover, multi-touch, device tilt, simultaneous key chords, or timed interaction.

Where dragging exists, an equivalent button, arrow, numeric field, or semantic command path must exist.

Primary targets should be at least approximately 44 by 44 CSS pixels. Layer-list controls must reflow on narrow screens rather than relying on tiny controls or undiscoverable horizontal scrolling.

## Semantic and sensory accessibility

- Controls use result-oriented accessible names.
- Focus is visible.
- Selection, lock, visibility, errors, and state are not communicated by color alone.
- Important state changes are announced through the existing live-region mechanism.
- High-contrast and large-control preferences are available without changing world truth.
- The five-node surface intentionally reduces switch-scan stops.
- No important information depends on sound.
- Screen-reader and semantic interfaces must describe the same selected object, world relationships, and permissions as visual interfaces.
- The separate Accessibility Shell remains a first-class nonvisual interface into the same authoritative state.

## Layer model

Ordinary users see DEPTH and LAYER concepts in result-oriented language. Advanced controls may expose the exact Shaelvien Tier / Layer values.

Layer appearance order and recursive spatial depth remain distinct. UI simplification must not collapse them into one value or rewrite canonical topology.

## Safety and authority

Adaptive and accessibility transports must never bypass recursive permissions, ownership, claim scope, or other canonical authority checks. Presentation changes do not grant editing authority.

## Preservation rule

Working advanced controls remain available while the adaptive surface replaces their discoverability burden. Refactoring presentation must not delete working authoring mechanisms merely because they are hidden behind MORE or ADVANCED.


## Creator-shell hierarchy — 2026-09-26

The five-node VIEW / BUILD / EDIT / LAYERS / MORE surface remains a working contextual canvas control model and compatibility layer. It is **not** the entire creator-facing information architecture.

At the broader creator/workbench level, Shaelvien uses a stable spatial grammar:

- left = instrument/tool selection
- center = current authored work
- right = material, asset, draft, or alternative selection
- bottom = contextual actions
- top = persistent modifiers and assistance state

CREATE / WORLD / PLAY are the major creator-facing destinations. Specialized studios remain available as instruments instead of requiring a new GM to understand the whole internal tool taxonomy before making useful content.

The Creative Workplace Contract governs assistance, drafts, creative fit, progressive depth, and promotion from private work into production.
