# Scorpio engine (Rust)

Committed **Scorpio** workspace (`Cargo.toml` at this level). Public naming in APIs and docs should stay **Scorpio**; third-party library names appear only where required by dependencies and attribution.

## Contents

| Crate | Role |
|-------|------|
| `crates/scorpio-core` | `ScorpioObjectStoreRegistry` — `file`, `http(s)`, `s3`, `gs`/`gcs`, Azure (`az`, `abfs`, `abfss`, `azure`, `adl`); dynamic `register_store` / `deregister_store`; in-process SQL smoke via DataFusion |

## Build / test

Requires **Rust 1.88** (see `rust-toolchain.toml`).

```bash
cd engine
cargo test -p scorpio-core --locked
```

From repo root: `.\scripts\run-smoke-sql.ps1` or `./scripts/run-smoke-sql.sh` runs all `smoke_*` tests (defaults `SCORPIO_ENGINE_ROOT` to `engine/`).

## Environment variables

- **S3 / AWS:** `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, etc. (see `AmazonS3Builder::from_env`).
- **GCS:** Application Default Credentials or `GOOGLE_APPLICATION_CREDENTIALS` (see `GoogleCloudStorageBuilder::from_env`).
- **Azure:** `AZURE_STORAGE_ACCOUNT`, keys or workload identity as supported by `MicrosoftAzureBuilder::from_env` and `with_url`.

## Reference clone

A read-only clone under `vendor/datafusion-ballista` (gitignored) is optional for comparison only—not the Scorpio codebase.

## Git remotes

See [REPOSITORY_SETUP.md](REPOSITORY_SETUP.md). Use **your** org as `origin` for Scorpio; do not treat third-party repos as the primary remote.

## Legal

Scorpio-authored code in this workspace is under **Apache License 2.0** ([LICENSE](LICENSE)). [NOTICE](NOTICE) summarizes third-party components and attribution; keep it updated as dependencies change and retain upstream NOTICE content where Ballista-derived code ships.

Fork/trim/remotes checklist: [REPOSITORY_SETUP.md](REPOSITORY_SETUP.md). Full policy notes: [license-and-notice.txt](../license-and-notice.txt).

## Roadmap (not in this crate yet)

Scheduler, executor, and Docker build scripts from a historical distributed query stack are **separate, large** porting tasks—track them in `Planning/Phase1.md`.
