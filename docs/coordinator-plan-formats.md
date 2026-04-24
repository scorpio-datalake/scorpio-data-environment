# Coordinator plan formats (Epic 3 spike)

This note records **versioning and format choices** for moving work between clients and the Scorpio engine. It is not an implementation spec for a single release.

## MVP (today)

- **SQL text** — `POST /v1/sql` and `POST /v1/jobs` carry a UTF-8 `sql` string. The engine parses with DataFusion. **Versioning** is implicit in the **Scorpio engine image tag** (scheduler + executors + planner version).
- **JSON envelopes** — Job lifecycle (`SubmitJobRequest`, `JobStatusResponse`, …) are defined in [docs/openapi/coordinator-v1.json](openapi/coordinator-v1.json) and mirrored in Rust tests under `engine/scorpio/client/tests/job_contract_serde.rs`.

## Future (Epic 3+)

- **Substrait** (or DataFusion `LogicalPlan` protobuf) — optional plan bytes on `POST /v1/jobs` / `POST /v1/sql` with explicit **plan_version** or **substrait_version** field once the coordinator accepts non-SQL plans.
- **Apache Arrow Flight** — preferred bulk result path per Phase 1; HTTP paged Arrow IPC remains a fallback for small clients.

## Compatibility rule

When the coordinator adds fields, prefer **additive** JSON and **ignore-unknown** parsing on clients until a semver bump is declared for breaking wire changes.
