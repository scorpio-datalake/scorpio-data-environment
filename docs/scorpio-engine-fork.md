# Scorpio engine fork — trim and git remotes

This doc implements **Epic 0** planning items for creating a maintainable **Ballista-derived** engine tree: trim the default Cargo workspace and ensure **`origin`** is your org, not Apache.

For legal and NOTICE reminders, see [license-and-notice.txt](../license-and-notice.txt) and [engine/REPOSITORY_SETUP.md](../engine/REPOSITORY_SETUP.md).

## 1. Create the git remote layout

Follow **§1** in [engine/REPOSITORY_SETUP.md](../engine/REPOSITORY_SETUP.md) (`origin` → your fork; optional `upstream` → Apache).

Verify from **scorpio-data-environment** (or CI) after you set `SCORPIO_ENGINE_ROOT` to the fork or reference clone:

```bash
chmod +x scripts/verify-engine-git-remotes.sh
./scripts/verify-engine-git-remotes.sh
```

```powershell
.\scripts\verify-engine-git-remotes.ps1
```

The script fails if `origin` still points at **`apache/datafusion-ballista`**. It skips gracefully when the engine path is not a Git checkout (e.g. only the monorepo `engine/` crate tree is used).

## 2. Trim the Ballista workspace (upstream layout)

**Where this applies:** the **Ballista fork** (or `vendor/datafusion-ballista`), i.e. a tree that already contains `ballista/core`, `scorpio-cli`, etc. **Do not** list workspace **members** for paths that are missing on disk: e.g. do not list `scorpio-cli` until that folder exists, and do not list `crates/scorpio-core` unless you have added that crate. Mismatches produce “failed to read … Cargo.toml”.

The following matches **apache/datafusion-ballista** as of a workspace whose root `Cargo.toml` includes `benchmarks` and `examples` in `[workspace].members` (see your snapshot under `vendor/datafusion-ballista` if you keep a local reference).

**Replace** the `members` / `exclude` block with:

```toml
[workspace]
exclude = ["benchmarks", "dev/msrvcheck", "examples", "python"]
members = [
    "scorpio-cli",
    "scorpio/client",
    "ballista/core",
    "ballista/executor",
    "ballista/scheduler",
]
resolver = "3"
```

Keep the rest of the file (workspace dependencies, profiles) unchanged unless you are intentionally upgrading Arrow/DataFusion.

Then from the **engine repository root** (the fork):

```bash
cargo check --workspace --locked
cargo test --workspace --locked
```

If you drop **`scorpio-cli`**, remove it from `members` as well and confirm nothing in your deploy path depends on it.

## 3. Smoke SQL suite (optional `scorpio-core` crate)

If you add **`engine/crates/scorpio-core`** to `[workspace].members`, in-process SQL smoke tests can live there and track the **DataFusion** version you pin in that crate (keep it aligned with Ballista’s `workspace.dependencies`).

From the repo root:

```bash
./scripts/run-smoke-sql.sh
```

```powershell
.\scripts\run-smoke-sql.ps1
```

Those scripts run every test named `smoke_*` in `scorpio-core`. If **`scorpio-core` is not in the workspace**, rely on **`cargo test --workspace`** under `engine/` (Ballista’s own tests) after **`protoc`** is installed ([engine/README.md](../engine/README.md)).

## 4. CI habit

This repository runs **`cargo fmt`**, **`clippy`**, and **`cargo test --locked`** for `engine/` on push/PR via `.github/workflows/scorpio-engine.yml`. Mirror the same jobs on your **standalone** Scorpio engine fork once it exists.

DataFusion ↔ Ballista version notes: [scorpio-engine-compatibility.md](scorpio-engine-compatibility.md).
