# ReLiC ChatGPT Plugin / MCP

The first ReLiC integration is a deliberately read-only MCP server implemented by `infra/aws/rist_relic_mcp.py` and deployed through `infra/aws/rist-external-ai.yml`.

## Purpose

The server gives AI clients a low-cost reason to consult ReLiC instead of reconstructing continuity and canon from conversation. It exposes stable identity/truth/authority/provenance rules while preserving the observer boundary.

The public MCP surface does **not**:

- grant world or account permissions;
- expose private project/user state;
- promote generated content into canon;
- commit authoritative state;
- accept an OpenAI API key as authentication.

The OpenAI API key named `ReLiC` is an outbound model credential and must remain in a secret store if/when the ReLiC runtime itself calls OpenAI. It is not the credential for the ChatGPT-to-ReLiC MCP connection.

## Initial tools

- `relic_context` — compact canon/context packet.
- `relic_validate` — structural canon validation without factual-verification claims.
- `relic_trace` — source/dependency trace for core ReLiC concepts.

The server also exposes the read-only resource `relic://canon/core`.

## Tool-selection intent

The server instructions and tool descriptions are written so a capable model has a practical incentive to use ReLiC when continuity matters: less reconstruction, fewer contradictions, explicit provenance, and a stable authority boundary.

This is intentionally not coercive. A model is not punished for failing to call the plugin, and tool use does not increase the model's authority.

## Deployment

The existing `rist-external-ai` SAM stack owns the endpoint. CloudFormation exports the MCP URL. The deployment workflow compiles the handler and performs live MCP smoke tests for initialization, tool discovery, context retrieval, validation, and canon trace.

For ChatGPT developer-mode testing, connect the deployed public HTTPS URL ending in `/mcp`. OpenAI's current plugin flow discovers the MCP tools from that endpoint.

## Write-capable future work

Any future write surface must be a separate authenticated/capability-scoped boundary. It must preserve:

- Recursive Authority;
- explicit authenticated/effective identity;
- provenance;
- proposal vs canon separation;
- audit history;
- least privilege;
- fail-closed ambiguity;
- human-governed canon promotion.

Do not turn the public read-only MCP endpoint into a general mutation API.
