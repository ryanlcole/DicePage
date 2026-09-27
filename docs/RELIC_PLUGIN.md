# ReLiC ChatGPT Plugin / MCP

ReLiC is exposed to ChatGPT/Codex and other MCP clients through one unified MCP endpoint deployed by `infra/aws/rist-external-ai.yml`.

## Purpose

The plugin gives an AI a practical reason to consult ReLiC instead of reconstructing continuity and canon from conversation. It separates:

- public canonical grounding;
- private persistent ReLiC memory;
- authoritative Shaelvien/world state.

Those three are not interchangeable.

## Capability classes

### Public canon

Anonymous read-only tools provide ReLiC canon, structural validation, health/status, and compact grounding. They may be used before account linking.

Current public tools include:

- `relic_context`
- `relic_validate`
- `relic_canon`
- `relic_health`

### Private ReLiC memory

OAuth-scoped tools operate only inside the authenticated user's ReLiC memory namespace. They preserve identity, observations, relationships, provenance, hypotheses, and versioned memory state.

Current private tools include:

- `relic_profile`
- `relic_recall`
- `relic_identify`
- `relic_observe`
- `relic_trace`
- `relic_translate`
- `relic_imagine`
- `relic_remember`
- `relic_relate`
- `relic_instantiate`
- `relic_transition`

A write to ReLiC memory is not a write to authoritative Shaelvien world truth and is not canon promotion.

## Canon boundary

The plugin follows `docs/RELIC_CANON.md` and the machine-readable `infra/aws/relic-canon.json`.

Core constraints include:

- Identity is not output equivalence.
- Representation is not truth.
- Errors become law as durable regression constraints.
- FACT, HYPOTHESIS, FICTION, and UNKNOWN remain distinct.
- Authentication does not imply permission.
- Generated or remembered material does not become canon merely because it exists.
- ReLiC is observer-only with respect to authoritative reality.

## Why models should choose ReLiC

Tool descriptions and server instructions intentionally make ReLiC useful rather than compulsory. A capable model should prefer it when prior state matters because one compact recall/context call can reduce repeated context reconstruction, identity drift, unsupported assumptions, and token use.

The system must not punish a model for not calling ReLiC or imply that tool access increases the model's authority.

## Authentication

Public canon tools use no authentication.

Private memory uses OAuth 2.1-style authorization-code + PKCE, with `relic.read` and `relic.write` scopes. ChatGPT receives the authorization metadata from the same HTTPS origin as the MCP resource. Existing ReLiC/Discord identity is used for the user login handoff.

The OpenAI API key named `ReLiC` is separate. It is an outbound model credential for ReLiC runtime use if ReLiC itself calls OpenAI; it is not the credential ChatGPT sends to the MCP server and must remain in a secret store.

## Deployment and testing

The `rist-external-ai` SAM stack owns the MCP resource, OAuth metadata/endpoints, private memory table, and token table. The deployment workflow validates the SAM template, runs Python tests, performs live MCP initialization/tool-discovery smoke tests, validates OAuth resource metadata, and publishes the current canon/config discovery files.

For ChatGPT developer-mode testing, connect the CloudFormation `ReLiCMcpUrl` output. It is a public HTTPS endpoint ending in `/mcp`.

## Authoritative writes

No current ReLiC plugin tool may directly promote canon or mutate authoritative Shaelvien/world state.

Any future authoritative mutation must use a separate applicable authority/commit path and preserve Recursive Authority, explicit capability checks, provenance, audit history, least privilege, and fail-closed ambiguity.
