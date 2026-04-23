# Scorpio engine (Rust)

Workspace root for the **Scorpio** distributed engine (`scorpio-cli`, `scorpio/client`, `scorpio/core`, `scorpio/executor`, `scorpio/scheduler`). Upstream lineage is Apache DataFusion **Ballista** (see *Legal*). Use **Scorpio** in user-facing text.

## Scorpio naming target (Epic 0 **R0**)

Authoritative mapping for renaming **Scorpio-owned** crates, paths, and binaries. **Do not** rename crates.io dependency keys in `Cargo.toml` (`datafusion`, `arrow`, `object_store`, …) or their `use …` paths in Rust — those stay the upstream names.

| Current path (under `engine/`) | Target path | Cargo package name | Binary / `lib` |
|-------------------------------|-------------|---------------------|----------------|
| `scorpio-cli/` (R1 **done**) | *(same)* | `scorpio-cli` | Binary **`scorpio-cli`** |
| `scorpio/core/` (R5 **done**) | *(same)* | `scorpio-core` | Library **`scorpio_core`** (`use scorpio_core::…`) |
| `scorpio/executor/` | *(same)* | `scorpio-executor` | Binary **`scorpio-executor`** |
| `scorpio/scheduler/` | *(same)* | `scorpio-scheduler` | Binary **`scorpio-scheduler`** |
| `scorpio/client/` (R2 **done**) | *(same)* | **`scorpio`** | Library **`scorpio`** (`use scorpio::…`) |

**R0 itself** is documentation-only: **no `cargo` build** is required to land it. For **R1–R5**, **build and test only the crate you touch** (from `engine/`); do not use `cargo test --workspace` until **R6**:

| Story | Scope | Validate |
|-------|--------|----------|
| R1 | `scorpio-cli` only | `cargo test -p scorpio-cli --locked` |
| R2 | `scorpio` (client) only | `cargo test -p scorpio --locked` |
| R3 | `scorpio-executor` only | `cargo test -p scorpio-executor --locked` |
| R4 | `scorpio-scheduler` only | `cargo test -p scorpio-scheduler --locked` |
| R5 | `scorpio-core` only | `cargo test -p scorpio-core --locked` and, for object store integration tests, add `--features build-binary` (see below) |

Workspace packages use Scorpio names (`scorpio-core`, `scorpio-scheduler`, `scorpio-executor`, …). Use the [aliases](#iterating-locally-scoped-builds) in `.cargo/config.toml` and the *Iterating locally* table. The CLI is **`scorpio-cli`** and the client library is **`scorpio`**.

## Prerequisites

- **Rust:** **1.91.1** (see `rust-toolchain.toml`; the engine workspace and AWS SDK crates in the graph declare this MSRV).
- **`protoc`:** `scorpio-core` runs `prost-build` over `.proto` files. Cargo reads **`PROTOC`** (full path to `protoc.exe`) if set; otherwise `protoc` on `PATH`. From repo root on Windows: `. .\scripts\set-protoc-for-cargo.ps1` then build.

## Contents

| Path | Role |
|------|------|
| `scorpio-cli` | CLI binary **`scorpio-cli`** |
| `scorpio/core` | Core types, protos, shared logic |
| `scorpio/scheduler` | Scheduler service |
| `scorpio/executor` | Executor service |
| `scorpio/client` | Client library (`scorpio` crate) |

## Build / test

```bash
cd engine
cargo build -p scorpio-cli --locked
cargo test --workspace --locked
```

`cargo build` and `cargo test` use the workspace **`[profile.dev]`** in `Cargo.toml` (incremental compilation, no LTO, `codegen-units = 256`). Run them from **`engine/`** so Cargo picks up **`engine/.cargo/config.toml`**.

### Iterating locally (scoped builds)

Cargo **reuses** `engine/target/` incrementally: after a first compile, a change in one crate usually rebuilds only that crate and its dependents. To keep feedback small on a modest machine, **default to the smallest package that contains your change**, not `cargo test --workspace` every time.

**Dependency direction:** `scorpio-core` is the foundation. Edits under `scorpio/core` force rebuilds of scheduler, executor, client, and CLI until their APIs stabilize. Edits only under `scorpio/scheduler` do not recompile `scorpio-core` if its sources are unchanged.

| If you are changing… | Package (`-p`) | Typical commands |
|----------------------|----------------|------------------|
| Protos, object store registry, shared plans | `scorpio-core` | `cargo test-core` or `cargo check-core-tests` (compile tests, no run) |
| Scheduler / stage scheduling | `scorpio-scheduler` | `cargo test-scheduler` |
| Executor / shuffle / Flight | `scorpio-executor` | `cargo test-executor` |
| Client library | `scorpio` | `cargo test-client` |
| CLI | `scorpio-cli` | `cargo test-cli` |
| Pre-merge / CI parity | — | `cargo test-ws` (= `cargo test --workspace --locked`) |

**Scripts (same defaults, filters, `--build-binary` for core object-store tests):**

- Windows: [`../scripts/run-engine-tests.ps1`](../scripts/run-engine-tests.ps1) (default `-p scorpio-core`)
- Unix: [`../scripts/run-engine-tests.sh`](../scripts/run-engine-tests.sh)

Examples: `.\scripts\run-engine-tests.ps1 -p scorpio-scheduler`; `./scripts/run-engine-tests.sh --workspace` before a PR.

### Pull requests — tests with behavior changes

If this PR changes **runtime behavior** (object store / S3, scheduler stages, executor or shuffle / Flight, proto or plan wire formats, etc.), add or update **`#[test]` / integration tests in the same PR**. The default [pull request template](../.github/pull_request_template.md) asks contributors to confirm; workspace CI is a gate, not a substitute for area-specific coverage.

**CI parity from `engine/`:** `cargo fmt-check`, `cargo clippy-ws`, then `cargo test-ws`. GitHub Actions: [`.github/workflows/scorpio-engine-multi-os.yml`](../.github/workflows/scorpio-engine-multi-os.yml) runs those steps on **Ubuntu, Windows, and macOS** (no Docker). Optional **MinIO** S3 integration (Linux only, `docker run` for MinIO — not Scorpio image builds): [`.github/workflows/scorpio-engine.yml`](../.github/workflows/scorpio-engine.yml).

**Object store / `register_store` tests** need `--features build-binary` on `scorpio-core` (the script: `-BuildBinary` / `--build-binary`). There is no separate Cargo alias for that pair; use the script or  
`cargo test -p scorpio-core --features build-binary --locked`.

**rust-analyzer / IDE:** Prefer **no** `RUSTFLAGS` in your shell for this repo. If you must set `RUSTFLAGS`, use the **same** value in rust-analyzer (e.g. `rust-analyzer.cargo.extraEnv` / `RUSTFLAGS` in the IDE) so the build cache matches the terminal.

**Release / CI:** `cargo build --release` uses the `release` profile. `cargo test --release` builds tests with optimizations (slower iteration). CI can use `--profile ci` (see `Cargo.toml`) for reproducible, non-incremental runs.

### S3 / MinIO integration test

[MinIO](https://min.io/) is an **S3-compatible object store** used as a **local (or CI) stand-in for AWS S3**: same signing and bucket/object APIs, usually run in Docker on `localhost`. It is **not** a substitute for testing real IAM/IRSA, but it validates `CustomObjectStoreRegistry` + `object_store` against a real HTTP S3 endpoint.

- **Default:** `cargo test --workspace` does **not** run the MinIO test (it is `#[ignore]` so laptops without Docker still pass).
- **CI:** [`.github/workflows/scorpio-engine.yml`](../.github/workflows/scorpio-engine.yml) (Linux only) starts MinIO, creates bucket `scorpio-it`, then runs  
  `cargo test -p scorpio-core --features build-binary --test s3_minio_integration -- --ignored`.
- **Local (Docker required):** from `engine/`, start MinIO (example):

  ```bash
  docker run -d --name scorpio-minio -p 9000:9000 \
    -e MINIO_ROOT_USER=minioadmin -e MINIO_ROOT_PASSWORD=minioadmin \
    quay.io/minio/minio server /data
  docker run --rm --network host --entrypoint /bin/sh quay.io/minio/mc -c \
    "mc alias set sc http://127.0.0.1:9000 minioadmin minioadmin && mc mb -p sc/scorpio-it"
  export AWS_ACCESS_KEY_ID=minioadmin AWS_SECRET_ACCESS_KEY=minioadmin AWS_DEFAULT_REGION=us-east-1
  export AWS_ENDPOINT_URL_S3=http://127.0.0.1:9000 AWS_ALLOW_HTTP=true AWS_EC2_METADATA_DISABLED=true
  cargo test -p scorpio-core --features build-binary --test s3_minio_integration --locked -- --ignored --nocapture
  ```

  Override the bucket with `SCORPIO_MINIO_BUCKET` if you use a different name.

## Environment variables

Operator-facing contract (Compose, Kubernetes secrets → env, workload identity): [../docs/object-store-credentials.md](../docs/object-store-credentials.md).

- **S3 / AWS:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION` / `AWS_DEFAULT_REGION`, STS / IRSA variables as needed; optional SQL `SET` keys (`s3.*`) override env **only when both** access key and secret are set (see `scorpio/core` `object_store.rs`).
- **GCS (`gs://`):** Application Default Credentials or `GOOGLE_APPLICATION_CREDENTIALS` (see [object_store GCP](https://docs.rs/object_store/latest/object_store/gcp/index.html)).
- **Azure (`abfs`/`abfss`/`az`/`azure`/`adl` or `https://*.blob.core.windows.net`):** `AZURE_STORAGE_*`, managed identity, SAS, etc., per [object_store Azure](https://docs.rs/object_store/latest/object_store/azure/index.html).

## Reference clone

A read-only clone under `vendor/datafusion-ballista` (gitignored) is optional for comparison only.

## Git remotes

[REPOSITORY_SETUP.md](REPOSITORY_SETUP.md), [../docs/scorpio-engine-fork.md](../docs/scorpio-engine-fork.md).

## Legal

[LICENSE](LICENSE), [NOTICE](NOTICE). Derived from Apache DataFusion Ballista; retain upstream notices when shipping.
