# Scorpio engine — DataFusion compatibility notes

This document is for **operators and contributors**. Public product copy should say **Scorpio**; wire formats and session keys may still use **`ballista.*`** / protobuf paths for upstream compatibility (see [engine/README.md](../engine/README.md) *Legal*).

## Version alignment (pin together)

| Layer | Location | Typical pin |
|-------|----------|-------------|
| **Engine workspace** | `engine/Cargo.toml` `[workspace.dependencies]` | `datafusion = "53"`, `arrow = "58"`, `object_store = "0.13"`, matching `prost` / `tonic` |
| **`scorpio-core`** | `engine/scorpio/core` (package `scorpio-core`) | `datafusion` **major.minor** must match the rest of `engine/` |

**Rule of thumb:** When you bump DataFusion in one place, bump it across the **whole** `engine/` workspace in the same release train, then run **`cargo test --workspace --locked`**.

## Where boundaries matter

1. **In-process SQL (`scorpio-core`, if present)**  
   Uses DataFusion `SessionContext` directly. Does **not** prove distributed scheduler/executor behavior.

2. **Distributed execution path**  
   Plans cross process boundaries via **serialization** (e.g. `datafusion-proto`, Ballista-derived protos). Custom physical nodes must round-trip.

3. **Arrow / Flight**  
   Keep **arrow** / **arrow-flight** aligned across scheduler, executor, and clients sharing IPC.

4. **Object stores**  
   Keep **`object_store`** versions aligned so URLs and auth behave the same on scheduler and executors. **`CustomObjectStoreRegistry`** (in `scorpio-core`, `build-binary`) resolves **`gs://`**, **`abfs`/`abfss`/`az`/`azure`/`adl`**, **`https://`…`blob.core.windows.net` / `dfs.core.windows.net`** (and Fabric hosts), plus **`s3`**, **`http`**, and **`file`**, and supports **`register_store`** / **`deregister_store`** for explicit bucket registration. **S3 regression:** ignored-by-default MinIO integration test — `scorpio/core/tests/s3_minio_integration.rs` (CI runs with `--ignored`; see [../engine/README.md](../engine/README.md)).

## Practical caveats

- **Workspace tests are necessary, not sufficient** for production: add integration tests against Compose or k8s for multi-executor paths.
- **Proto / Substrait:** Changing definitions requires coordinated client and server bumps.
- **Feature flags:** Different DataFusion `default-features` between crates can change the SQL surface.

## Smoke and CI

- **With `scorpio-core` in `[workspace].members`:** [scripts/run-smoke-sql.sh](../scripts/run-smoke-sql.sh) / [run-smoke-sql.ps1](../scripts/run-smoke-sql.ps1) run `cargo test -p scorpio-core smoke_`.
- **Otherwise:** use **`cd engine && cargo test --workspace --locked`** as the SQL/engine smoke habit; CI runs the same in [`.github/workflows/scorpio-engine-multi-os.yml`](../.github/workflows/scorpio-engine-multi-os.yml) (Ubuntu, Windows, macOS). Optional MinIO S3 integration: [`.github/workflows/scorpio-engine.yml`](../.github/workflows/scorpio-engine.yml).

## Related

- Fork trim and remotes: [scorpio-engine-fork.md](scorpio-engine-fork.md)
- Engine build notes: [../engine/README.md](../engine/README.md)
- Object store credentials (S3 / GCS / ADLS): [object-store-credentials.md](object-store-credentials.md)
- Databases & SFTP strategy: [data-sources-databases-sftp.md](data-sources-databases-sftp.md)
- Hive / Iceberg / Delta scope: [table-formats-metastore-scope.md](table-formats-metastore-scope.md)
