# Scorpio — optional `scorpio.compat` and migration ergonomics (Epic 11)

The primary surface for Scorpio workloads is **`scorpio`**: **`Session`**, **`DataFrame`**, jobs, catalog registration—each delegating to the Rust coordinator/engine. Use **[`docs/python-session.md`](python-session.md)** and **`docs/python-dataframe.md`** (when present) for the authoritative API.

The **`scorpio.compat`** package is an **explicitly optional** home for thin aliases (`from scorpio.compat import …`) when product demand justifies ergonomics tweaks for teams moving generic “cluster driver” workloads to Scorpio. It is **not** a substitute for **Rust ↔ Python parity** tracked in **`Planning/Phase1.md` Epic 3** and OSS phase docs.

- Add **aliases** behind **small PRs** with **neutral naming** — avoid trademarks of third-party ecosystems in module or function names surfaced to users.
- Prefer **patterns** docs (this file + examples) before expanding `compat`; keep the stable API in the root `scorpio` namespace.
