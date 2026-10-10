# ReLiC Independent Host

Status: **prototype implementation; not yet production-verified**.

This service moves ReLiC continuity out of ChatGPT memory. ChatGPT, other AIs, Shaelvien, RIST, and future clients may query ReLiC, but none becomes ReLiC's persistence authority merely by connecting to it.

## Boundary

- ReLiC owns durable continuity storage.
- Storage is append-only at the event API: prior records are not overwritten.
- Representation is not truth. A stored claim is evidence/history, not automatic proof of current repository/runtime state.
- ReLiC is observer-first and does not gain Shaelvien/RIST mutation authority.
- Proposed governed changes are blocked unless **necessity is PROVEN**, **accuracy is PROVEN**, and **approval is APPROVED**.
- Omission must be represented as a proposed change whenever it changes governed meaning.
- Verification after an authorized external mutation is a separate event; authorization is not verification.

## Run locally

```bash
docker build -t relic-host services/relic-host
docker volume create relic-data
docker run --rm -p 8080:8080 -v relic-data:/data -e RELIC_WRITE_TOKEN='replace-me' relic-host
```

Read endpoints require no write token. Write endpoints require `Authorization: Bearer <RELIC_WRITE_TOKEN>`.

## API

- `GET /health`
- `GET /v1/events?subject=...`
- `POST /v1/events`
- `POST /v1/proposals`
- `POST /v1/proposals/{id}/gates/necessity`
- `POST /v1/proposals/{id}/gates/accuracy`
- `POST /v1/proposals/{id}/gates/approval`
- `GET /v1/proposals/{id}`

The proposal API returns `mutation_allowed: true` only when all three gates are satisfied. It does **not** itself mutate another system.

## Production work still required

A production deployment still needs a durable managed data volume/database, TLS and network policy, secret storage, identity/authorization stronger than the prototype bearer token, backups, restore tests, audit/export tooling, retention policy implementation, availability monitoring, and verified client adapters. Do not label the service production-ready until those controls and deployment tests exist.
