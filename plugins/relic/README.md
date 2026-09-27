# ReLiC plugin package

This folder is the portable Agent Plugins package for the ReLiC MCP service.

It combines:

- the stable remote MCP endpoint at `https://relicgamemaster.com/mcp`;
- the `relic-grounding` skill, which teaches models when persistent ReLiC context is materially useful;
- positive and negative tool-selection eval cases.

The design target is **preference through utility**. When continuity, identity, provenance, canon, authority, or prior error state matters, one ReLiC lookup should be cheaper and more reliable than reconstructing state from conversational context. For self-contained work, the model should leave ReLiC alone.

Public canon tools are read-only. OAuth-scoped private tools may write only to the authenticated user's private ReLiC memory namespace. Those writes do not promote Shaelvien/world canon and do not grant authoritative world-write permission.

## Developer-mode test

Register `https://relicgamemaster.com/mcp` as an MCP connection in ChatGPT developer mode, inspect the discovered tools, and run the cases in `evals/tool-selection.json`. Record both correct tool selection and correct non-selection.

The runtime contract is `docs/RELIC_PLUGIN.md`. Foundational canon is `docs/RELIC_CANON.md`.
