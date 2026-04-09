# Scorpio engine — DataFusion ↔ Ballista compatibility

This document is for **operators and contributors**. User-facing Scorpio product copy should say **Scorpio** only where you control branding; internal crates may still use Ballista names.

## Version alignment (pin together)

| Layer | Location | Typical pin |
|-------|----------|-------------|
| **Ballista workspace** | `engine/Cargo.toml` `[workspace.dependencies]` | `datafusion = "53"`, `arrow = "58"`, `object_store = "0.13"`, matching `prost` / `tonic` |
| **`scorpio-core`** (optional monorepo crate) | `engine/crates/scorpio-core/Cargo.toml` when present | `datafusion` **major.minor** must match the Ballista workspace |

**Rule of thumb:** When you bump DataFusion in one place, bump it across the **whole** `engine/` workspace in the same release train, then run **`cargo test --workspace --locked`**.

## Where boundaries matter

1. **In-process SQL (`scorpio-core`, if present)**  
   Uses DataFusion `SessionContext` directly. Does **not** prove distributed scheduler/executor behavior.

2. **Distributed Ballista path**  
   Plans cross process boundaries via **serialization** (e.g. `datafusion-proto`, Ballista protos). Custom physical nodes must round-trip.

3. **Arrow / Flight**  
   Keep **arrow** / **arrow-flight** aligned across scheduler, executor, and clients sharing IPC.

4. **Object stores**  
   Keep **`object_store`** versions aligned so URLs and auth behave the same on scheduler and executors. The Ballista **`CustomObjectStoreRegistry`** (in `ballista-core`, `build-binary`) resolves **`gs://`**, **`abfs`/`abfss`/`az`/`azure`/`adl`**, **`https://`…`blob.core.windows.net` / `dfs.core.windows.net`** (and Fabric hosts), plus **`s3`**, **`http`**, and **`file`**, and supports **`register_store`** / **`deregister_store`** for explicit bucket registration.

## Practical caveats

- **Workspace tests are necessary, not sufficient** for production: add integration tests against Compose or k8s for multi-executor paths.
- **Proto / Substrait:** Changing definitions requires coordinated client and server bumps.
- **Feature flags:** Different DataFusion `default-features` between crates can change the SQL surface.

## Smoke and CI

- **With `scorpio-core` in `[workspace].members`:** [scripts/run-smoke-sql.sh](../scripts/run-smoke-sql.sh) / [run-smoke-sql.ps1](../scripts/run-smoke-sql.ps1) run `cargo test -p scorpio-core smoke_`.
- **Ballista-only workspace (current default):** use **`cd engine && cargo test --workspace --locked`** as the SQL/engine smoke habit; CI runs the same in [`.github/workflows/scorpio-engine.yml`](../.github/workflows/scorpio-engine.yml).

## Related

- Fork trim and remotes: [scorpio-engine-fork.md](scorpio-engine-fork.md)
- Engine build notes: [../engine/README.md](../engine/README.md)
