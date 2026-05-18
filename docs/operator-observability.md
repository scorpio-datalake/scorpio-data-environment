# Operator roadmap — observability and debugging (Epic 10)

**Today:** Rust scheduler **optional Prometheus** scrape (`Planning/Phase2-OSS.md` **P2‑E1‑S3** overlaps); Scorpio **`scorpio-python-api`** attaches **`User-Agent`** and **`X-Scorpio-Tenant-Id`** consistent with **`docs/python-session.md`**.

**Epic 10 target:** operator-grade dashboards and searchable logs:

- **Correlation IDs**: propagate from Python wrapper/UI through coordinator REST into executor task logs where feasible.
- **Job lineage**: expose job id + session id consistently in coordinator responses (**OpenAPI** job objects).
- **UI**: Scorpio **`web/`** scaffold may later link “job logs / metrics drill-down” placeholders (Epic 7 + 10 alignment).

Defer heavy packaged SIEM or vendor dashboard programs until OSS adoption clears; incremental logging hooks are welcome without blocking **`Planning/Phase1.md`** milestones.
