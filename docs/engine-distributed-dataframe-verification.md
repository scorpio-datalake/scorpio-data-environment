# Scorpio engine — distributed execution & “DataFrame” verification

This document implements Epic 0 items **distributed DataFrame (engine)** and **engine test coverage audit** from the Phase 1 plan: what is verified in Rust today, what “distributed” means here, and what remains for production hardening.

## Terminology

| Term | Meaning in this repo |
|------|----------------------|
| **Python DataFrame** | Epic 2 (lazy API in `python/scorpio`). **Not** what this page exercises. |
| **Engine distributed execution** | SQL / DataFusion `DataFrame` plans executed via the Scorpio stack: **scheduler**, **executor(s)**, **stage boundaries**, **shuffle** (hash or sort-based), **Arrow** batches. |
| **Standalone mode** | `SessionContext::standalone()` — in-process scheduler + executor (still uses distributed *plans* and shuffle when the optimizer inserts exchanges). |
| **Remote mode** | `SessionContext::remote("df://…")` — gRPC to a real scheduler; tests start **one** scheduler + **one** executor process (`scorpio/client/tests/common/mod.rs`). |
| **Task parallelism** | `ballista.standalone.parallelism` — concurrent tasks per executor (see `BALLISTA_STANDALONE_PARALLELISM` in `scorpio/core`). |
| **Multi-executor** | **Multiple executor processes** (e.g. several pods). The default integration tests use **one** executor process; scaling out is validated operationally (Compose/k8s) rather than in every `cargo test`. |

## What we assert today (joins, aggregations, shuffle)

0. **Unit tests (`scorpio-scheduler`)**  
   - Module: `engine/scorpio/scheduler/src/distributed_plan_invariants_tests.rs` (compiled only under `cfg(test)`).  
   - Builds the same synthetic graphs as `test_utils` (`test_aggregation_plan`, `test_join_plan`, `test_two_aggregations_plan`) and asserts **at least two stages** and presence of **shuffle-related** operators (`ShuffleWriterExec`, `SortShuffleWriterExec`, or `UnresolvedShuffleExec`) in staged physical plans.  
   - Command (scoped): `cargo test -p scorpio-scheduler --locked distributed_plan_invariants` (from `engine/`); or full crate tests without the filter.

1. **Integration (`scorpio` client, `standalone` feature)**  
   - File: `engine/scorpio/client/tests/context_checks.rs` (module `supported`).  
   - **Remote + standalone** parameterized tests (`#[case::standalone]`, `#[case::remote]`) run the same SQL against Parquet (`testdata/alltypes_plain.parquet`).  
   - Covers **filters**, **aggregates** (`GROUP BY`, `HAVING`-style patterns elsewhere), **sort-merge join** (`should_support_sort_merge_join`), **shuffle-related settings** (e.g. remote Flight read), and **`should_execute_join_and_aggregate_standalone_and_remote`** — **inner hash join + `GROUP BY` + `ORDER BY`** (partitioned Parquet scan + shuffle stages as the planner emits them).  
   - Commands (from `engine/`):  
     `cargo test -p scorpio --features standalone --locked --test context_checks`  
     Filter one test:  
     `cargo test -p scorpio --features standalone --locked --test context_checks should_execute_join_and_aggregate_standalone_and_remote`

2. **Sort-based shuffle**  
   - File: `engine/scorpio/client/tests/sort_shuffle.rs` (requires `standalone` + sort-shuffle config).  
   - Exercises **GROUP BY**, **aggregates**, **UNION ALL**, etc., with local vs Flight remote shuffle read.

3. **Unit / module tests (shuffle & plan boundaries)**  
   - `scorpio/core`: `shuffle_reader.rs`, `shuffle_writer.rs`, `distributed_query.rs`, sort-shuffle modules — serialization and shuffle mechanics.  
   - `scorpio/scheduler`: AQE / `plan_to_stages`, `execution_graph`, `join_selection`, etc.  
   - `scorpio/executor`: executor loop, Flight, metrics.

4. **Object store**  
   - `engine/scorpio/core/src/object_store.rs` — URL schemes and `register_store`.  
   - `engine/scorpio/core/tests/s3_minio_integration.rs` — optional MinIO (ignored by default; see `engine/README.md`).

## Gaps (explicit)

| Area | Status |
|------|--------|
| **Multiple executor processes in one test** | Not a default automated test; use Compose/k8s (Epic 12) or a dedicated integration job. |
| **GCS / ADLS live reads** | Scheme + registry covered; **live** cloud integration is optional smoke / manual. |
| **Failure, cancel, straggler** | Limited coverage; track as follow-up tests. |
| **Python lazy DataFrame** | Epic 2 — builds on the engine behavior documented here. |

## If something fails

1. Run `cargo test -p scorpio --features standalone --locked --test context_checks` from `engine/` (requires `protoc`, Rust version in `engine/README.md` / `rust-toolchain.toml` if present).  
2. Confirm `engine/scorpio/client/testdata` or `EXAMPLES_TEST_DATA` points at `alltypes_plain.parquet`.  
3. For shuffle-only issues, add `--test sort_shuffle` and enable sort-shuffle flags as in `sort_shuffle.rs`.  
4. Open an issue with **failing test name**, **standalone vs remote**, and **EXPLAIN** output if SQL-level.

## Related

- [scorpio-engine-compatibility.md](scorpio-engine-compatibility.md)  
- [object-store-credentials.md](object-store-credentials.md)  
- [engine/README.md](../engine/README.md)
