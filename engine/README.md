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

`cargo build` and `cargo test` use the workspace **`[profile.dev]`** in `Cargo.toml` (incremental compilation, no LTO, `codegen-units = 256`). Run them from **`engine/`** so Cargo picks up **`engine/.cargo/config.toml`**.

**rust-analyzer / IDE:** Prefer **no** `RUSTFLAGS` in your shell for this repo. If you must set `RUSTFLAGS`, use the **same** value in rust-analyzer (e.g. `rust-analyzer.cargo.extraEnv` / `RUSTFLAGS` in the IDE) so the build cache matches the terminal.

**Release / CI:** `cargo build --release` uses the `release` profile. `cargo test --release` builds tests with optimizations (slower iteration). CI can use `--profile ci` (see `Cargo.toml`) for reproducible, non-incremental runs.

### S3 / MinIO integration test

[MinIO](https://min.io/) is an **S3-compatible object store** used as a **local (or CI) stand-in for AWS S3**: same signing and bucket/object APIs, usually run in Docker on `localhost`. It is **not** a substitute for testing real IAM/IRSA, but it validates `CustomObjectStoreRegistry` + `object_store` against a real HTTP S3 endpoint.

- **Default:** `cargo test --workspace` does **not** run the MinIO test (it is `#[ignore]` so laptops without Docker still pass).
- **CI:** [`.github/workflows/scorpio-engine.yml`](../.github/workflows/scorpio-engine.yml) starts MinIO, creates bucket `scorpio-it`, then runs  
  `cargo test -p ballista-core --features build-binary --test s3_minio_integration -- --ignored`.
- **Local (Docker required):** from `engine/`, start MinIO (example):

  ```bash
  docker run -d --name scorpio-minio -p 9000:9000 \
    -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin \
    quay.io/minio/minio server /data
  docker run --rm --network host quay.io/minio/mc \
    sh -c "mc alias set sc http://127.0.0.1:9000 minioadmin minioadmin && mc mb -p sc/scorpio-it"
  export AWS_ACCESS_KEY_ID=minioadmin AWS_SECRET_ACCESS_KEY=minioadmin AWS_DEFAULT_REGION=us-east-1
  export AWS_ENDPOINT_URL_S3=http://127.0.0.1:9000 AWS_ALLOW_HTTP=true AWS_EC2_METADATA_DISABLED=true
  cargo test -p ballista-core --features build-binary --test s3_minio_integration --locked -- --ignored --nocapture
  ```

  Override the bucket with `SCORPIO_MINIO_BUCKET` if you use a different name.

## Environment variables

Operator-facing contract (Compose, Kubernetes secrets → env, workload identity): [../docs/object-store-credentials.md](../docs/object-store-credentials.md).

- **S3 / AWS:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` / `AWS_DEFAULT_REGION`, STS / IRSA variables as needed; optional Ballista SQL `s3.*` keys override env **only when both** access key and secret are set (see `ballista/core` `object_store.rs`).
- **GCS (`gs://`):** Application Default Credentials or `GOOGLE_APPLICATION_CREDENTIALS` (see [object_store GCP](https://docs.rs/object_store/latest/object_store/gcp/index.html)).
- **Azure (`abfs`/`abfss`/`az`/`azure`/`adl` or `https://*.blob.core.windows.net`):** `AZURE_STORAGE_*`, managed identity, SAS, etc., per [object_store Azure](https://docs.rs/object_store/latest/object_store/azure/index.html).

## Reference clone

A read-only clone under `vendor/datafusion-ballista` (gitignored) is optional for comparison only.

## Git remotes

[REPOSITORY_SETUP.md](REPOSITORY_SETUP.md), [../docs/scorpio-engine-fork.md](../docs/scorpio-engine-fork.md).

## Legal

[LICENSE](LICENSE), [NOTICE](NOTICE). Derived from Apache DataFusion Ballista; retain upstream notices when shipping.
