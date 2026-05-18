# Epic 3 parity — Rust `scorpio` client vs **Scorpio's Python API** wrapper

Single coordinator **HTTP** contract: [openapi/coordinator-v1.json](openapi/coordinator-v1.json). The Python package implements that contract end-to-end (`scorpio._rest.coordinator`, `scorpio.dataframe.job`).

| Lifecycle / transport | Rust `scorpio` library (engine workspace) | Python (`scorpio-python-api`) |
|------------------------|------------------------------------------|--------------------------------|
| **Submit work** | Scheduler / Ballista **gRPC** (push logical plan to cluster) | `POST /v1/jobs` with `SubmitJobRequest` JSON (**SQL** today; optional **`plan_*`** fields when coordinator supports IR) |
| **Poll status** | gRPC / executor protocol (Ballista) | `GET /v1/jobs/{job_id}?session_id=…` → `JobStatusResponse` |
| **Cancel** | Engine-specific (not mirrored in OpenAPI v1 for Rust in-tree) | `POST /v1/jobs/{job_id}/cancel` with `CancelJobRequest` |
| **Result materialization** | In-process / Flight / shuffle per deployment | `GET /v1/jobs/{job_id}/result` — **Arrow IPC** pages; **`X-Scorpio-Has-More`** / **`X-Scorpio-Next-Offset`** hint pagination; **Apache Arrow Flight** remains the preferred bulk path when exposed by the coordinator |

**Parity rule:** No Python-only job control plane: async jobs from **Scorpio's Python API** use the same envelope shapes as documented for any other REST client (Rust consumers can share `engine/scorpio/client/tests/job_contract_serde.rs` types).

**Gaps / backlog:** Rust library does not ship a first-party REST client in this repo snapshot; when one lands, it should reuse the same JSON structs and OpenAPI spec. Substrait/DataFusion binary plans are **wire-ready** in v1 but execution is coordinator-dependent.
