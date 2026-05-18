# Control plane (Epic 8) — coordinator HTTP and OpenAPI

The **canonical contract** for Scorpio coordinator REST (**session, synchronous SQL, async jobs**) is **`docs/openapi/coordinator-v1.json`**.

Implementation of the Rust (or curated FastAPI) server that honours this spec belongs to **OSS Phase 2** — **`Planning/Phase2-OSS.md` P2‑E1**, including **P2‑E1‑S5** ADR and **LICENSE**/`NOTICE` review (**P2‑E1‑S6**) when net-new deps land.

Consumers today:

| Consumer | Role |
|----------|------|
| **`python/scorpio`** | Production-facing **`Session`**, **`CoordinatorClient`**, job handles |
| **`web/`** (Epic 7) | Browser `fetch()` client keyed by **`VITE_SCORPIO_*`** env vars (CORS-aware deployments) |

See also **[`coordinator-plan-formats.md`](coordinator-plan-formats.md)** for plan-byte fields alongside SQL snapshots.
