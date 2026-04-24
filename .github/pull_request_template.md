## Summary

<!-- What does this PR change and why? -->

## Tests aligned with behavior changes (engine)

CI runs `cargo fmt`, `clippy`, and `cargo test --workspace --locked` on Ubuntu, Windows, and macOS (`.github/workflows/scorpio-engine-multi-os.yml`). That does **not** replace updating the suites your change can break.

## Tests — Python (`python/`)

- [ ] **No Python behavior change** — packaging only, deps, or docs.
- [ ] **Python behavior changed** — I **added or updated `pytest`** (or equivalent) in this PR for the code I touched (session / catalog / coordinator REST under `python/scorpio/src/scorpio/`, lazy DataFrame under `python/scorpio/src/scorpio/dataframe/`, etc.).

Please check **one** (engine):

- [ ] **No engine behavior change** — docs, workflow-only, comments, or refactors that preserve semantics.
- [ ] **Engine behavior changed** — I **added or updated automated tests in this PR** for the areas I touched (same PR, not a follow-up ticket). Examples:
  - **Object store / S3 / `CustomObjectStoreRegistry`** → `engine/scorpio/core` (`object_store.rs`, `--features build-binary`, MinIO integration when relevant).
  - **Scheduler / stages / shuffle planning** → `engine/scorpio/scheduler` (including `distributed_plan_invariants_*` when stage boundaries change).
  - **Executor / shuffle / Flight** → `engine/scorpio/executor`; client SQL / Parquet paths → `engine/scorpio/client/tests/`.
  - **Proto / plan serialization / gRPC** → relevant `serde`, scheduler, or client tests.

## Notes for reviewers

<!-- Risk, rollout, links to issues, etc. -->
