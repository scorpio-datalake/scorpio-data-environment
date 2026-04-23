# Scorpio engine — test coverage inventory (Epic 0 audit)

This document satisfies the Phase 1 **Engine test coverage audit**: what the retained Rust workspace exercises today, and known gaps. Update it when you add suites or close gaps.

**Same-PR test updates:** When closing gaps or changing behavior, extend tests in the **same PR** as the code (see [`.github/pull_request_template.md`](../.github/pull_request_template.md) and [engine/README.md](../engine/README.md) § *Pull requests — tests with behavior changes*).

## Workspace members (`engine/Cargo.toml`)

| Crate / path | Automated tests (summary) | Typical command |
|--------------|---------------------------|-----------------|
| `scorpio-core` | Unit tests in-tree; shuffle / object-store code behind `build-binary`; MinIO S3 integration (`tests/s3_minio_integration.rs`, `#[ignore]` unless CI) | `cargo test -p scorpio-core --locked` / `--features build-binary` |
| `scorpio-scheduler` | Planner, AQE, execution graph, gRPC, **distributed plan invariants** (`distributed_plan_invariants_tests`) | `cargo test -p scorpio-scheduler --locked` |
| `scorpio-executor` | Executor loop, Flight, metrics | `cargo test -p scorpio-executor --locked` |
| `scorpio` (client) | `tests/context_checks`, `tests/sort_shuffle` (need `standalone` feature) | `cargo test -p scorpio --features standalone --locked --test context_checks` |
| `scorpio-cli` | CLI / REPL tests as present in crate | `cargo test -p scorpio-cli --locked` |
| Full workspace | CI-style | `cargo test --workspace --locked` |

## Gap tracker (explicit)

Planning: extended integration work for these gaps lives under **Epic 12** in [Planning/Phase1.md](../Planning/Phase1.md) (*Multi-cloud freeware deployment smoke*).

| Area | Coverage today | Gap / follow-up |
|------|----------------|-----------------|
| **Multi-executor processes** | Single executor in default client remote tests | Compose/k8s or dedicated multi-process job |
| **GCS / ADLS live reads** | Registry + URL keys; not live cloud in default CI | Optional smoke with real credentials |
| **Failure / cancel / straggler** | Some scheduler/executor tests | Broader integration |
| **Python lazy DataFrame** | N/A in engine workspace | Epic 2 (`python/scorpio`) |
| **Credentials** | Env contract documented; object-store unit tests with `build-binary` | End-to-end per cloud |

## Related

- [engine-distributed-dataframe-verification.md](engine-distributed-dataframe-verification.md) — distributed SQL/DataFrame semantics and where joins/aggregations are verified.
- [engine/README.md](../engine/README.md) — toolchain, MinIO, iterating locally.
