# Coordinator plan formats (Epic 3 spike)

This note records **versioning and format choices** for moving work between clients and the Scorpio engine. It is not an implementation spec for a single release.

## MVP (today)

- **SQL text** — `POST /v1/sql` and `POST /v1/jobs` carry a UTF-8 `sql` string. The engine parses with DataFusion. **Versioning** is implicit in the **Scorpio engine image tag** (scheduler + executors + planner version).
- **JSON envelopes** — Job lifecycle (`SubmitJobRequest`, `JobStatusResponse`, …) are defined in [docs/openapi/coordinator-v1.json](openapi/coordinator-v1.json) and mirrored in Rust tests under `engine/scorpio/client/tests/job_contract_serde.rs`.

## Optional serialized plans (v1 OpenAPI, coordinator-dependent)

| Field | Meaning |
|-------|---------|
| `plan_encoding` | `"substrait"` — Substrait protobuf bytes; `"opaque"` — fork-specific blob (document server-side). |
| `plan_ir_version` | Opaque string tying bytes to a planner / fork revision (not semver-enforced in the spec). |
| `plan_bytes` | Base64-encoded blob; **omit** for SQL-only MVP submit. |

Clients **must** keep sending `sql` today for compatibility; coordinators that only understand SQL may ignore `plan_*` keys until they implement IR ingest.

## Results: HTTP pagination vs Flight

- **`GET /v1/jobs/{job_id}/result`** — Query params `offset` / `limit`; response may include **`X-Scorpio-Has-More`** and **`X-Scorpio-Next-Offset`** so drivers need not infer continuation from row counts alone.
- **Apache Arrow Flight** — preferred bulk path when the deployment exposes it; REST IPC pages remain the portable fallback (see [epic3-parity-matrix.md](epic3-parity-matrix.md)).

## Future (Epic 3+ extensions)

- **`POST /v1/sql`** accepting optional plan bytes (same `plan_*` fields as jobs) once synchronous path needs IR.
- Explicit **Substrait semantic version** negotiation if multiple encodings must coexist.

## Compatibility rule

When the coordinator adds fields, prefer **additive** JSON and **ignore-unknown** parsing on clients until a semver bump is declared for breaking wire changes.
