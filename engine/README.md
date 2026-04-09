# Scorpio engine (Rust)

Workspace root for the **Ballista-derived** distributed engine (`ballista-cli`, `ballista/client`, `ballista/core`, `ballista/executor`, `ballista/scheduler`). Public product naming should stay **Scorpio** where you control user-facing text.

## Prerequisites

- **Rust:** **1.91.1** (see `rust-toolchain.toml`; Ballista and AWS SDK crates in the graph declare this MSRV).
- **`protoc`:** `ballista-core` runs `prost-build` over `.proto` files. Cargo reads **`PROTOC`** (full path to `protoc.exe`) if set; otherwise `protoc` on `PATH`. From repo root on Windows: `. .\scripts\set-protoc-for-cargo.ps1` then build.

## Contents

| Path | Role |
|------|------|
| `ballista-cli` | CLI binary **`ballista-cli`** |
| `ballista/core` | Core types, protos, shared logic |
| `ballista/scheduler` | Scheduler service |
| `ballista/executor` | Executor service |
| `ballista/client` | Client library (`ballista` crate) |

## Build / test

```bash
cd engine
cargo build -p ballista-cli --locked
cargo test --workspace --locked
```

## Environment variables

- **S3 / AWS:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, etc. (and Ballista `s3.*` SQL options when using `CustomObjectStoreRegistry`).
- **GCS (`gs://`):** Application Default Credentials or `GOOGLE_APPLICATION_CREDENTIALS` (see [object_store GCP](https://docs.rs/object_store/latest/object_store/gcp/index.html)).
- **Azure (`abfs`/`abfss`/`az`/`azure`/`adl` or `https://*.blob.core.windows.net`):** `AZURE_STORAGE_ACCOUNT`, `AZURE_STORAGE_ACCESS_KEY`, managed identity / CLI / SAS as supported by [object_store Azure](https://docs.rs/object_store/latest/object_store/azure/index.html).

## Reference clone

A read-only clone under `vendor/datafusion-ballista` (gitignored) is optional for comparison only.

## Git remotes

[REPOSITORY_SETUP.md](REPOSITORY_SETUP.md), [../docs/scorpio-engine-fork.md](../docs/scorpio-engine-fork.md).

## Legal

[LICENSE](LICENSE), [NOTICE](NOTICE). Derived from Apache DataFusion Ballista; retain upstream notices when shipping.
